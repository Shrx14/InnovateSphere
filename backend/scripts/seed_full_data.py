#!/usr/bin/env python3
"""
InnovateSphere — Comprehensive Database Seeder
===============================================
Populates the Neon ai-refactor branch with LLM-generated ideas across all 10
domains, plus reviews, feedback, verdicts, generation traces, view events,
search queries, novelty breakdowns, daily domain metrics, idea relationships,
and missing config records (BiasProfile, PromptVersion).

Usage:
    python backend/scripts/seed_full_data.py              # Full run
    python backend/scripts/seed_full_data.py --dry-run     # Preview counts only

Requirements:
    - Ollama running locally with qwen2.5:7b loaded
    - DATABASE_URL pointing to Neon ai-refactor branch
    - SKIP_STARTUP_CHECKS=1 set automatically

All LLM calls use generous timeouts and retries. No placeholder/dummy data.
"""

import os
import sys
import json
import uuid
import random
import logging
import argparse
import time
import math
import requests
from datetime import datetime, timedelta, timezone, date

# ── Path & env setup ──────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['SKIP_STARTUP_CHECKS'] = '1'

# Monkeypatch startup checks to avoid slow network calls during seeding
import backend.utils.health_checks as _hc
_hc.run_startup_checks = lambda: None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('seed_full')

from werkzeug.security import generate_password_hash
from backend.core.db import db
from backend.core.app import create_app
from backend.core.models import (
    Domain, DomainCategory, User, ProjectIdea, IdeaSource, IdeaReview,
    IdeaFeedback, IdeaRequest, IdeaView, AdminVerdict, GenerationTrace,
    ViewEvent, SearchQuery, AbuseEvent, BiasProfile, PromptVersion,
    AiPipelineVersion,
)

# ── Constants ─────────────────────────────────────────────────────

# Ollama direct call settings (bypass the app's llm_client for simplicity)
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('LLM_MODEL_NAME', 'qwen2.5:7b')
OLLAMA_TIMEOUT = 180          # seconds — generous for 7b model
OLLAMA_MAX_RETRIES = 3
OLLAMA_BACKOFF_BASE = 2.0     # seconds

# How many ideas per domain (domain 6 already has 5, so we add fewer there)
IDEAS_PER_DOMAIN = 6

# Date range for temporal spread (30 days back from "today")
NOW = datetime.now(timezone.utc)
SEED_START = NOW - timedelta(days=30)

# Existing IDs from DB inspection
EXISTING_IDEA_IDS = [1, 2, 3, 4, 5]
ADMIN_USER_IDS = [1, 7]       # user IDs with role=admin
ALL_USER_IDS = [1, 2, 3, 4, 5, 6, 7, 8]  # "real" users (skip test artifacts 12-28)
DOMAIN_ID_RANGE = range(6, 16)  # domain IDs 6-15

# ── Helpers ───────────────────────────────────────────────────────

def _utcnow():
    return datetime.now(timezone.utc)


def _random_datetime_between(start: datetime, end: datetime) -> datetime:
    """Random datetime uniformly distributed between start and end."""
    delta = (end - start).total_seconds()
    offset = random.random() * delta
    return start + timedelta(seconds=offset)


def _distribute_dates(n: int, start: datetime, end: datetime) -> list:
    """Return n datetimes spread roughly evenly across [start, end] with jitter."""
    if n <= 0:
        return []
    span = (end - start).total_seconds()
    step = span / n
    dates = []
    for i in range(n):
        base_offset = step * i + step * 0.5
        jitter = random.uniform(-step * 0.35, step * 0.35)
        offset = max(0, min(span, base_offset + jitter))
        dates.append(start + timedelta(seconds=offset))
    random.shuffle(dates)
    return dates


def _novelty_score_from_bucket() -> int:
    """Weighted random novelty score: 10% elite, 30% solid, 40% moderate, 20% low."""
    r = random.random()
    if r < 0.10:
        return random.randint(80, 95)
    elif r < 0.40:
        return random.randint(60, 79)
    elif r < 0.80:
        return random.randint(40, 59)
    else:
        return random.randint(20, 39)


def _view_count_power_law() -> int:
    """Power-law-ish distribution: mostly low views, a few viral."""
    r = random.random()
    if r < 0.05:
        return random.randint(200, 500)
    elif r < 0.20:
        return random.randint(80, 200)
    elif r < 0.60:
        return random.randint(20, 80)
    else:
        return random.randint(2, 20)


def _rating_weighted() -> int:
    """Skewed-positive rating distribution: mean ~3.6."""
    r = random.random()
    if r < 0.10:
        return 1
    elif r < 0.25:
        return 2
    elif r < 0.50:
        return 3
    elif r < 0.80:
        return 4
    else:
        return 5


def _safe_commit():
    """Commit with retry on connection drop (Neon pooler can disconnect idle sessions)."""
    for attempt in range(3):
        try:
            db.session.commit()
            return
        except Exception as e:
            log.warning(f"  [DB] commit failed (attempt {attempt+1}): {type(e).__name__}: {str(e)[:200]}")
            try:
                db.session.rollback()
            except Exception:
                pass
            if attempt < 2:
                time.sleep(2 + attempt * 2)
            else:
                log.error("  [DB] commit failed after 3 attempts, continuing…")
                # Don't raise — just log and continue. Lost data will be retried on next run.


def _safe_rollback():
    """Safe rollback that doesn't raise."""
    try:
        db.session.rollback()
    except Exception:
        try:
            db.session.close()
        except Exception:
            pass


# ── Ollama direct caller ─────────────────────────────────────────

def call_ollama(prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> dict:
    """
    Call Ollama directly (not through the app's llm_client) with generous
    timeout and retries.  Returns parsed JSON dict or raises RuntimeError.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": (
            "You are a JSON generator. Return ONLY valid JSON with no markdown, "
            "no explanation, no extra text.\n\n" + prompt
        ),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": 4096,
        },
    }

    for attempt in range(OLLAMA_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")

            # Try to parse JSON from response
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("LLM returned non-object JSON")

        except json.JSONDecodeError:
            # Try to extract JSON from mixed text
            import re
            match = re.search(r'\{[\s\S]*\}', raw)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            log.warning(f"  [Ollama] attempt {attempt+1}: could not parse JSON")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            log.warning(f"  [Ollama] attempt {attempt+1}: {type(e).__name__}")

        except Exception as e:
            log.warning(f"  [Ollama] attempt {attempt+1}: {e}")

        if attempt < OLLAMA_MAX_RETRIES:
            backoff = OLLAMA_BACKOFF_BASE * (2 ** attempt)
            log.info(f"  [Ollama] retrying in {backoff:.1f}s …")
            time.sleep(backoff)

    raise RuntimeError("Ollama failed after all retries")


# ── LLM prompt builders ──────────────────────────────────────────

def _build_idea_prompt(domain_name: str, category_name: str, idx: int) -> str:
    """Build a prompt for generating one unique project idea."""
    return f"""Generate a unique, innovative project idea in the domain "{domain_name}", 
specifically in the sub-area "{category_name}".

This is idea #{idx} for this domain — make it substantially different from typical projects.
Focus on a real-world problem that hasn't been solved well yet.

Return a JSON object with EXACTLY these keys:
{{
  "title": "A concise, creative project title (5-12 words)",
  "problem_statement": "A detailed description of the real-world problem this solves. Explain why current solutions are inadequate and what impact solving this would have. 3-5 sentences.",
  "problem_statement_json": {{
    "core_problem": "One sentence stating the core problem",
    "impact": "Who is affected and how",
    "current_gaps": "What existing solutions miss",
    "constraints": ["constraint1", "constraint2", "constraint3"]
  }},
  "tech_stack": "Comma-separated list of 4-6 specific technologies (e.g. Python, FastAPI, React, PostgreSQL, TensorFlow — NOT vague categories like AI, ML, Cloud)",
  "tech_stack_json": [
    {{"name": "SpecificLanguageOrFramework", "role": "What it does in the project", "justification": "Why this specific tool was chosen over alternatives"}},
    {{"name": "AnotherSpecificLibrary", "role": "What it does", "justification": "Why chosen"}}
  ],
  "user_query": "A short 5-10 word search query a user might type to discover this idea"
}}"""


def _build_source_prompt(idea_title: str, domain_name: str, tech_stack: str, count: int) -> str:
    """Build a prompt for generating realistic evidence sources for an idea."""
    return f"""Generate {count} realistic academic and open-source evidence sources that would support
a research project titled "{idea_title}" in the domain "{domain_name}" using: {tech_stack}.

For each source, generate a plausible:
- Academic paper (arXiv-style) OR GitHub repository
- With a realistic title, URL, summary, and publication date

Return a JSON object:
{{
  "sources": [
    {{
      "source_type": "arxiv" or "github",
      "title": "Realistic paper or repo title",
      "url": "https://arxiv.org/abs/24XX.XXXXX or https://github.com/org/repo",
      "summary": "2-3 sentence summary of what this source contributes",
      "published_date": "YYYY-MM-DD (within last 2 years)"
    }}
  ]
}}

Make approximately 60% arxiv papers and 40% github repos. Ensure URLs are unique and realistic.
Generate EXACTLY {count} sources."""


def _build_review_comment_prompt(idea_title: str, rating: int) -> str:
    """Build a prompt to generate a natural review comment for an idea."""
    sentiment = {1: "very negative", 2: "negative", 3: "neutral/mixed", 4: "positive", 5: "very positive"}
    return f"""Write a short, natural-sounding review comment (1-2 sentences) for a research project idea titled "{idea_title}".
The reviewer gave it {rating}/5 stars, so the tone should be {sentiment.get(rating, 'neutral')}.

Return JSON: {{"comment": "Your review comment here"}}"""


def _build_search_queries_prompt(domains: list) -> str:
    """Build a prompt for generating diverse search queries."""
    domain_list = ", ".join(domains)
    return f"""Generate 80 diverse search queries that users would type when looking for innovative project ideas
across these domains: {domain_list}.

Each query should be 3-8 words, realistic, and span different aspects of each domain.
Mix technical and non-technical queries.

Return JSON: {{
  "queries": [
    {{"query": "the search text", "domain": "closest matching domain name from the list"}}
  ]
}}

Generate EXACTLY 80 queries spread across all domains."""


# ══════════════════════════════════════════════════════════════════
#  SEED FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def seed_config(dry_run: bool):
    """Seed BiasProfile and PromptVersion if missing."""
    log.info("── seed_config ──")

    # BiasProfile
    existing_bp = BiasProfile.query.filter_by(name='default_v1').first()
    if not existing_bp:
        if dry_run:
            log.info("  [DRY] Would create BiasProfile 'default_v1'")
        else:
            bp = BiasProfile(
                name='default_v1',
                version='v1',
                is_active=True,
                rules={
                    "domain_strictness_defaults": {
                        "AI & Machine Learning": 1.2,
                        "Web & Mobile Development": 1.0,
                        "Data Science & Analytics": 1.1,
                        "Cybersecurity & Privacy": 1.3,
                        "Cloud & DevOps": 1.0,
                        "Blockchain & Web3": 1.1,
                        "IoT & Hardware": 1.0,
                        "Healthcare & Biotech": 1.3,
                        "Education & E-Learning": 0.9,
                        "Business & Productivity Tools": 0.9,
                    },
                    "source_penalty_weights": {
                        "hallucinated": -0.25,
                        "rejected": -0.15,
                        "low_reputation": -0.10,
                    },
                    "novelty_floor": 25,
                    "evidence_minimum_sources": 3,
                },
            )
            db.session.add(bp)
            db.session.flush()
            log.info("  ✓ Created BiasProfile 'default_v1'")
    else:
        log.info("  ✓ BiasProfile 'default_v1' already exists")

    # PromptVersion
    existing_pv = PromptVersion.query.filter_by(name='default').first()
    if not existing_pv:
        if dry_run:
            log.info("  [DRY] Would create PromptVersion 'default'")
        else:
            pv = PromptVersion(
                name='default',
                is_active=True,
                prompts_json={
                    "SYSTEM_PASS1": "You are a senior research analyst ...",
                    "USER_PASS1": "Analyze the existing idea space for: {query} in {domain}",
                    "SYSTEM_PASS2": "You are an engineering problem-framing expert ...",
                    "USER_PASS2": "Define a well-scoped problem addressing gaps from analysis",
                    "SYSTEM_PASS3": "You are a strict evidence auditor ...",
                    "USER_PASS3": "Validate sources supporting the problem",
                    "SYSTEM_PASS4": "You are a senior systems architect ...",
                    "USER_PASS4": "Synthesize a modular solution grounded in validated sources",
                },
            )
            db.session.add(pv)
            db.session.flush()
            log.info("  ✓ Created PromptVersion 'default'")
    else:
        log.info("  ✓ PromptVersion 'default' already exists")

    if not dry_run:
        _safe_commit()


def update_existing_users(dry_run: bool):
    """Spread preferred_domain_id and skill_levels across existing users."""
    log.info("── update_existing_users ──")

    users = User.query.order_by(User.id).all()
    domain_ids = list(DOMAIN_ID_RANGE)
    skill_levels = ['beginner', 'intermediate', 'advanced', 'expert']
    updated = 0

    for i, user in enumerate(users):
        changes = False
        target_domain = domain_ids[i % len(domain_ids)]
        if user.preferred_domain_id != target_domain:
            user.preferred_domain_id = target_domain
            changes = True
        # Set preferred_domains JSON (2-3 domains)
        pref_domains = [target_domain]
        secondary = domain_ids[(i + 3) % len(domain_ids)]
        if secondary != target_domain:
            pref_domains.append(secondary)
        if i % 3 == 0:
            tertiary = domain_ids[(i + 7) % len(domain_ids)]
            if tertiary not in pref_domains:
                pref_domains.append(tertiary)
        user.preferred_domains = pref_domains

        # Diversify skill levels
        target_skill = skill_levels[i % len(skill_levels)]
        if user.skill_level != target_skill:
            user.skill_level = target_skill
            changes = True

        if changes:
            updated += 1

    if dry_run:
        log.info(f"  [DRY] Would update {updated} users with domain prefs & skill levels")
    else:
        _safe_commit()
        log.info(f"  ✓ Updated {updated} users with domain prefs & skill levels")


def seed_ideas(dry_run: bool):
    """Generate ideas via Ollama across all 10 domains."""
    log.info("── seed_ideas ──")

    domains = Domain.query.order_by(Domain.id).all()
    domain_map = {d.id: d for d in domains}

    # Check existing idea counts per domain
    existing_counts = {}
    for d in domains:
        count = ProjectIdea.query.filter_by(domain_id=d.id).count()
        existing_counts[d.id] = count

    total_to_generate = 0
    plan = []
    for d in domains:
        needed = max(0, IDEAS_PER_DOMAIN - existing_counts[d.id])
        if needed > 0:
            categories = DomainCategory.query.filter_by(domain_id=d.id).all()
            cat_names = [c.name for c in categories]
            plan.append((d, needed, cat_names))
            total_to_generate += needed

    if total_to_generate == 0:
        log.info("  ✓ All domains already have enough ideas")
        return []

    log.info(f"  Generating {total_to_generate} ideas across {len(plan)} domains")

    if dry_run:
        log.info(f"  [DRY] Would generate {total_to_generate} ideas via Ollama")
        return []

    # Distribute dates across 30-day window
    all_dates = _distribute_dates(total_to_generate, SEED_START, NOW - timedelta(hours=1))
    date_idx = 0

    new_ideas = []
    users_for_assignment = ALL_USER_IDS.copy()

    for domain, needed_count, cat_names in plan:
        log.info(f"  Domain: {domain.name} — generating {needed_count} ideas")
        for i in range(needed_count):
            cat = cat_names[i % len(cat_names)]
            attempt = 0
            max_idea_retries = 3
            idea_data = None

            while attempt < max_idea_retries:
                try:
                    prompt = _build_idea_prompt(domain.name, cat, i + 1)
                    idea_data = call_ollama(prompt, max_tokens=2000, temperature=0.8)
                    # Validate required keys
                    required = ['title', 'problem_statement', 'tech_stack']
                    if all(k in idea_data and idea_data[k] for k in required):
                        break
                    log.warning(f"    LLM output missing keys, retrying ({attempt+1})")
                    idea_data = None
                except Exception as e:
                    log.warning(f"    LLM error on attempt {attempt+1}: {e}")
                attempt += 1

            if not idea_data:
                log.error(f"    ✗ Failed to generate idea for {domain.name}/{cat} after {max_idea_retries} attempts — SKIPPING")
                date_idx += 1
                continue

            # Build problem_statement_json if LLM didn't return valid structure
            ps_json = idea_data.get('problem_statement_json')
            if not isinstance(ps_json, dict):
                ps_json = {"content": idea_data['problem_statement']}

            # Build tech_stack_json
            ts_json = idea_data.get('tech_stack_json')
            if not isinstance(ts_json, list):
                techs = [t.strip() for t in idea_data['tech_stack'].split(',')]
                ts_json = [{"name": t, "role": "Core component", "justification": "Industry standard"} for t in techs]

            created_at = all_dates[date_idx] if date_idx < len(all_dates) else _random_datetime_between(SEED_START, NOW)
            date_idx += 1

            novelty = _novelty_score_from_bucket()
            views = _view_count_power_law()
            user_id = users_for_assignment[len(new_ideas) % len(users_for_assignment)]

            # Extract or synthesize user_query for traces
            user_query = idea_data.get('user_query', f"innovative {cat.lower()} project")

            idea = ProjectIdea(
                title=idea_data['title'][:255],
                problem_statement=idea_data['problem_statement'],
                problem_statement_json=ps_json,
                tech_stack=idea_data['tech_stack'],
                tech_stack_json=ts_json,
                domain_id=domain.id,
                ai_pipeline_version='v2',
                is_ai_generated=True,
                is_public=True,
                is_validated=False,
                is_human_verified=False,
                created_at=created_at,
                view_count=views,
                novelty_score_cached=novelty,
                quality_score_cached=50,  # will be recomputed later
                novelty_context={
                    "engine": "hybrid_v2",
                    "domain_maturity": random.choice(["emerging", "growing", "mature"]),
                    "confidence": random.choice(["High", "Medium", "Low"]),
                    "evidence_score": round(random.uniform(0.4, 0.92), 2),
                    "sources_analyzed": random.randint(6, 30),
                    "explanation": f"Novel approach in {cat} within {domain.name}",
                },
            )
            db.session.add(idea)
            db.session.flush()  # get idea.id

            # IdeaRequest
            req = IdeaRequest(
                user_id=user_id,
                idea_id=idea.id,
                requested_at=created_at,
            )
            db.session.add(req)

            new_ideas.append({
                'idea': idea,
                'user_id': user_id,
                'user_query': user_query,
                'domain_name': domain.name,
                'cat_name': cat,
            })
            log.info(f"    ✓ [{len(new_ideas)}/{total_to_generate}] {idea_data['title'][:60]}")

            # Commit every 3 ideas to avoid losing progress
            if len(new_ideas) % 3 == 0:
                _safe_commit()
                log.info(f"    [checkpoint] committed {len(new_ideas)} ideas")

    _safe_commit()
    log.info(f"  ✓ Generated {len(new_ideas)} new ideas total")
    return new_ideas


def seed_sources(new_ideas: list, dry_run: bool):
    """Generate IdeaSource records via LLM for ideas without sources.
    Also deliberately give ~8 ideas < 3 sources (thin evidence)."""
    log.info("── seed_sources ──")

    # Build list of ideas that need sources (skip ideas that already have some)
    existing_source_idea_ids = set(
        r[0] for r in db.session.query(IdeaSource.idea_id).distinct().all()
    )

    # If new_ideas is empty (e.g., resuming after crash), query all ideas
    if not new_ideas:
        all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
        new_ideas = []
        for idea in all_ideas:
            if idea.id not in existing_source_idea_ids:
                domain_name = idea.domain.name if idea.domain else 'Unknown'
                new_ideas.append({
                    'idea': idea,
                    'user_id': idea.requests[0].user_id if idea.requests else 1,
                    'user_query': idea.title,
                    'domain_name': domain_name,
                    'cat_name': domain_name,
                })
    else:
        # Filter out ideas that already got sources from a previous partial run
        new_ideas = [m for m in new_ideas if m['idea'].id not in existing_source_idea_ids]

    if not new_ideas:
        log.info("  ✓ All ideas already have sources")
        return

    if dry_run:
        log.info(f"  [DRY] Would generate sources for {len(new_ideas)} ideas")
        return

    thin_evidence_indices = set(random.sample(range(len(new_ideas)), min(8, len(new_ideas))))
    hallucinate_indices = set(random.sample(range(len(new_ideas)), min(3, len(new_ideas))))

    for idx, meta in enumerate(new_ideas):
        idea = meta['idea']
        # Cache scalar attributes before any DB operations that could detach the object
        idea_id = idea.id
        idea_title = idea.title
        idea_tech_stack = idea.tech_stack
        domain_name = meta['domain_name']

        # Decide source count: thin evidence ideas get 1-2, rest get 4-8
        if idx in thin_evidence_indices:
            target_count = random.randint(1, 2)
        else:
            target_count = random.randint(4, 8)

        try:
            prompt = _build_source_prompt(
                idea_title, domain_name, idea_tech_stack, target_count
            )
            result = call_ollama(prompt, max_tokens=3000, temperature=0.6)
            sources = result.get('sources', [])

            if not isinstance(sources, list) or len(sources) == 0:
                log.warning(f"  ✗ No sources returned for idea {idea_id} — retrying")
                result = call_ollama(prompt, max_tokens=3000, temperature=0.7)
                sources = result.get('sources', [])

        except Exception as e:
            log.error(f"  ✗ Source generation failed for idea {idea_id}: {e}")
            _safe_rollback()
            continue

        seen_urls = set()
        added = 0
        for s in sources[:target_count]:
            if not isinstance(s, dict):
                continue
            url = s.get('url', f"https://arxiv.org/abs/{random.randint(2400, 2599)}.{random.randint(10000, 99999)}")
            if url in seen_urls:
                url += f"?v={random.randint(2,9)}"
            seen_urls.add(url)

            # Parse published_date
            pub_date = None
            pd_str = s.get('published_date', '')
            try:
                pub_date = datetime.strptime(pd_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pub_date = (NOW - timedelta(days=random.randint(30, 700))).date()

            is_hall = False
            if idx in hallucinate_indices and added == 0:
                is_hall = True  # flag first source of hallucinate-target ideas

            source = IdeaSource(
                idea_id=idea_id,
                source_type=s.get('source_type', 'arxiv')[:50],
                title=s.get('title', 'Untitled Source')[:255],
                url=url[:1024],
                summary=s.get('summary', ''),
                published_date=pub_date,
                is_hallucinated=is_hall,
            )
            db.session.add(source)
            added += 1

        if added > 0:
            log.info(f"  ✓ Idea {idea_id}: {added} sources" + (" [thin]" if idx in thin_evidence_indices else "") + (" [hallucinated]" if idx in hallucinate_indices else ""))

        # Commit after each idea's sources to minimize data loss on Neon connection drops
        if added > 0:
            _safe_commit()

    _safe_commit()
    log.info(f"  ✓ Sources seeded for {len(new_ideas)} ideas")


def seed_reviews(dry_run: bool):
    """Create ~180 IdeaReview records with LLM-generated comments."""
    log.info("── seed_reviews ──")

    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    all_users = User.query.order_by(User.id).all()
    user_ids = [u.id for u in all_users]

    # Get existing reviews to avoid constraint violations
    existing_reviews = set()
    for r in IdeaReview.query.all():
        existing_reviews.add((r.user_id, r.idea_id))

    # Plan: popular ideas get more reviews
    review_plan = []
    for idea in all_ideas:
        # Weight by view count
        if idea.view_count > 100:
            n_reviews = random.randint(6, 10)
        elif idea.view_count > 30:
            n_reviews = random.randint(3, 6)
        else:
            n_reviews = random.randint(1, 4)

        available_users = [uid for uid in user_ids if (uid, idea.id) not in existing_reviews]
        random.shuffle(available_users)
        for uid in available_users[:n_reviews]:
            rating = _rating_weighted()
            review_plan.append((uid, idea.id, idea.title, rating))
            existing_reviews.add((uid, idea.id))

    target = min(len(review_plan), 200)
    random.shuffle(review_plan)
    review_plan = review_plan[:target]

    if dry_run:
        log.info(f"  [DRY] Would create {len(review_plan)} reviews")
        return

    log.info(f"  Generating {len(review_plan)} reviews (some with LLM comments)…")

    # Generate LLM comments for ~40% of reviews in batches
    comment_indices = set(random.sample(range(len(review_plan)), int(len(review_plan) * 0.4)))

    # Spread created_at across 30 days
    review_dates = _distribute_dates(len(review_plan), SEED_START, NOW)

    for i, (uid, idea_id, idea_title, rating) in enumerate(review_plan):
        comment = None
        if i in comment_indices:
            try:
                prompt = _build_review_comment_prompt(idea_title, rating)
                result = call_ollama(prompt, max_tokens=200, temperature=0.8)
                comment = result.get('comment', '')
                if comment:
                    comment = comment[:1000]
            except Exception:
                comment = None  # skip comment, still insert review

        review = IdeaReview(
            user_id=uid,
            idea_id=idea_id,
            rating=rating,
            comment=comment,
            created_at=review_dates[i] if i < len(review_dates) else _utcnow(),
        )
        db.session.add(review)

        if (i + 1) % 20 == 0:
            _safe_commit()
            log.info(f"    [checkpoint] {i+1}/{len(review_plan)} reviews")

    _safe_commit()
    log.info(f"  ✓ Created {len(review_plan)} reviews")


def seed_feedback(dry_run: bool):
    """Create ~150 IdeaFeedback records respecting UNIQUE(user_id, idea_id, feedback_type)."""
    log.info("── seed_feedback ──")

    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    user_ids = [u.id for u in User.query.order_by(User.id).all()]

    existing_fb = set()
    for fb in IdeaFeedback.query.all():
        existing_fb.add((fb.user_id, fb.idea_id, fb.feedback_type))

    # DB check constraint only allows these types:
    feedback_types = ['upvote', 'downvote', 'bookmark', 'report', 'helpful', 'not_helpful']

    # Target distribution
    type_weights = {
        'upvote': 40,
        'downvote': 15,
        'bookmark': 30,
        'report': 5,
        'helpful': 35,
        'not_helpful': 25,
    }

    # Build pool of possible feedbacks
    pool = []
    for idea in all_ideas:
        for ftype in feedback_types:
            # Allocate feedback types logically
            if ftype == 'upvote' and (idea.novelty_score_cached or 50) < 40:
                continue  # low novelty ideas rarely get upvoted
            if ftype == 'report' and random.random() > 0.3:
                continue  # reports are rare
            available_users = [uid for uid in user_ids if (uid, idea.id, ftype) not in existing_fb]
            if available_users:
                uid = random.choice(available_users)
                pool.append((uid, idea.id, ftype))

    # Sample 150 from pool respecting type distribution
    target_total = 150
    random.shuffle(pool)

    # Group by type
    by_type = {t: [] for t in feedback_types}
    for item in pool:
        by_type[item[2]].append(item)

    selected = []
    total_weight = sum(type_weights.values())
    for ftype, weight in type_weights.items():
        n = int(target_total * weight / total_weight)
        candidates = by_type[ftype][:n + 5]
        selected.extend(candidates[:n])

    # Trim to 150
    selected = selected[:target_total]

    if dry_run:
        log.info(f"  [DRY] Would create {len(selected)} feedbacks")
        return

    feedback_dates = _distribute_dates(len(selected), SEED_START, NOW)

    for i, (uid, idea_id, ftype) in enumerate(selected):
        fb = IdeaFeedback(
            user_id=uid,
            idea_id=idea_id,
            feedback_type=ftype,
            comment=None,
            created_at=feedback_dates[i] if i < len(feedback_dates) else _utcnow(),
        )
        db.session.add(fb)

    _safe_commit()
    log.info(f"  ✓ Created {len(selected)} feedbacks")

    # Log distribution
    dist = {}
    for _, _, ft in selected:
        dist[ft] = dist.get(ft, 0) + 1
    log.info(f"    Distribution: {dist}")


def seed_verdicts(dry_run: bool):
    """Create ~24 AdminVerdict records for ~40% of ideas."""
    log.info("── seed_verdicts ──")

    existing_verdict_ideas = set(
        v.idea_id for v in AdminVerdict.query.all()
    )

    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    candidates = [i for i in all_ideas if i.id not in existing_verdict_ideas]

    target = min(24, len(candidates))
    selected = random.sample(candidates, target)

    # Distribution: 50% validated, 29% downgraded, 21% rejected
    validated_n = int(target * 0.50)
    downgraded_n = int(target * 0.29)
    rejected_n = target - validated_n - downgraded_n

    verdict_plan = []
    for idea in selected[:validated_n]:
        verdict_plan.append((idea, 'validated'))
    for idea in selected[validated_n:validated_n + downgraded_n]:
        verdict_plan.append((idea, 'downgraded'))
    for idea in selected[validated_n + downgraded_n:]:
        verdict_plan.append((idea, 'rejected'))

    # LLM-generate reasons
    reason_prompts = {
        'validated': "This idea demonstrates strong evidence grounding and novel approach.",
        'downgraded': None,  # will use LLM
        'rejected': None,    # will use LLM
    }

    if dry_run:
        log.info(f"  [DRY] Would create {len(verdict_plan)} verdicts (V:{validated_n} D:{downgraded_n} R:{rejected_n})")
        return

    verdict_dates = _distribute_dates(len(verdict_plan), SEED_START + timedelta(days=3), NOW)

    for i, (idea, verdict_type) in enumerate(verdict_plan):
        admin_id = random.choice(ADMIN_USER_IDS)

        if verdict_type == 'validated':
            reason = "Solid evidence grounding with novel approach. Sources verified and problem statement well-scoped."
        else:
            # Generate reason via LLM
            try:
                rprompt = f"""Write a short admin review reason (1-2 sentences) for why a project idea titled
"{idea.title}" was {verdict_type}. Be specific and professional.
Return JSON: {{"reason": "your reason here"}}"""
                result = call_ollama(rprompt, max_tokens=200, temperature=0.7)
                reason = result.get('reason', f"Idea {verdict_type} based on quality review.")
            except Exception:
                reason = f"Idea {verdict_type} during quality review — evidence or novelty concerns."

        v = AdminVerdict(
            idea_id=idea.id,
            admin_id=admin_id,
            verdict=verdict_type,
            reason=reason[:2000],
            created_at=verdict_dates[i] if i < len(verdict_dates) else _utcnow(),
        )
        db.session.add(v)

        # Update idea flags
        if verdict_type == 'validated':
            idea.is_validated = True
            if random.random() < 0.5:
                idea.is_human_verified = True

    _safe_commit()
    log.info(f"  ✓ Created {len(verdict_plan)} verdicts")


def seed_traces(new_ideas: list, dry_run: bool):
    """Create GenerationTrace for ALL ideas missing traces, and fix timing on existing."""
    log.info("── seed_traces ──")

    # Fix existing traces (null timing fields)
    # NOTE: GenerationTrace has a column named 'query' which shadows db.Model.query,
    # so we must use db.session.query() instead of GenerationTrace.query
    existing_traces = db.session.query(GenerationTrace).filter(
        GenerationTrace.retrieval_time_ms == None  # noqa: E711 — SQLAlchemy IS NULL
    ).all()

    if dry_run:
        log.info(f"  [DRY] Would fix {len(existing_traces)} existing traces")
        return

    for trace in existing_traces:
        trace.retrieval_time_ms = random.randint(300, 1500)
        trace.analysis_time_ms = random.randint(500, 2500)
        trace.generation_time_ms = random.randint(3000, 12000)
        if not trace.bias_profile_version:
            trace.bias_profile_version = 'v1'
        if not trace.prompt_version:
            trace.prompt_version = 'default'

    if existing_traces:
        _safe_commit()
        log.info(f"  ✓ Fixed timing on {len(existing_traces)} existing traces")

    # Create traces for ALL ideas that don't have one yet
    existing_trace_idea_ids = set(
        t.idea_id for t in db.session.query(GenerationTrace).all()
    )

    # Get all ideas + their request info
    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    user_ids = [u.id for u in User.query.all()]

    created = 0
    for idea in all_ideas:
        if idea.id in existing_trace_idea_ids:
            continue

        # Try to get original request info
        req = IdeaRequest.query.filter_by(idea_id=idea.id).first()
        trace_user_id = req.user_id if req else random.choice(user_ids)
        trace_query = f"Generate innovative {idea.domain.name if idea.domain else 'general'} project idea"
        trace_domain = idea.domain.name if idea.domain else 'Unknown'

        trace = GenerationTrace(
            idea_id=idea.id,
            user_id=trace_user_id,
            query=trace_query,
            domain_name=trace_domain,
            ai_pipeline_version='v2',
            bias_profile_version='v1',
            prompt_version='default',
            phase_0_output={
                "sources_retrieved": random.randint(8, 25),
                "arxiv": random.randint(4, 15),
                "github": random.randint(3, 12),
                "deduplication": {"before": random.randint(15, 30), "after": random.randint(8, 20)},
            },
            phase_1_output={
                "novelty_score": idea.novelty_score_cached,
                "confidence": random.choice(["High", "Medium", "Low"]),
                "evidence_gate_passed": True,
                "signals": {
                    "similarity": round(random.uniform(0.2, 0.7), 3),
                    "specificity": round(random.uniform(0.4, 0.9), 3),
                    "temporal": round(random.uniform(0.3, 0.8), 3),
                },
            },
            phase_2_output={
                "landscape_analysis": {
                    "gaps_identified": random.randint(2, 5),
                    "overused_patterns": random.randint(1, 3),
                    "emerging_trends": random.randint(1, 4),
                },
            },
            phase_3_output={
                "problem_framing": {
                    "scope": "well-defined",
                    "constraints_count": random.randint(2, 5),
                    "evidence_anchored": True,
                },
            },
            phase_4_output={
                "final_synthesis": {
                    "modules_count": random.randint(3, 6),
                    "grounding_score": round(random.uniform(0.6, 0.95), 2),
                    "cross_references": random.randint(2, 8),
                },
            },
            constraints_active={
                "domain_strictness": round(random.uniform(0.9, 1.4), 2),
                "source_penalties_count": random.randint(0, 3),
                "pattern_penalties_count": random.randint(0, 2),
                "evidence_minimum": 3,
            },
            bias_penalties_applied={
                "hitl_penalty": round(random.uniform(0, 0.15), 3),
                "commodity_penalty": round(random.uniform(0, 0.1), 3),
                "saturation_penalty": round(random.uniform(0, 0.2), 3),
                "internal_reuse_penalty": round(random.uniform(0, 0.05), 3),
            },
            retrieval_time_ms=random.randint(300, 1800),
            analysis_time_ms=random.randint(500, 3000),
            generation_time_ms=random.randint(3000, 15000),
            created_at=idea.created_at,
        )
        db.session.add(trace)
        created += 1

        # Commit every 10 to avoid losing progress
        if created % 10 == 0:
            _safe_commit()

    _safe_commit()
    log.info(f"  ✓ Created {created} new traces")


def seed_view_events(dry_run: bool):
    """Create ~250 ViewEvent and ~100 IdeaView records."""
    log.info("── seed_view_events ──")

    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    user_ids = [u.id for u in User.query.order_by(User.id).all()]

    existing_idea_views = set()
    for iv in IdeaView.query.all():
        existing_idea_views.add((iv.idea_id, iv.user_id))

    referrers = ['explore', 'search', 'direct', 'landing', 'shared_link']
    referrer_weights = [0.35, 0.25, 0.20, 0.12, 0.08]
    event_types = ['view', 'detail_view']

    view_events_plan = []
    idea_views_plan = []

    for idea in all_ideas:
        # Number of view events proportional to view_count
        n_events = max(1, int(idea.view_count * 0.5))
        n_events = min(n_events, 15)  # cap per idea

        for _ in range(n_events):
            uid = random.choice(user_ids) if random.random() > 0.3 else None
            ref = random.choices(referrers, referrer_weights)[0]
            evt = random.choice(event_types)
            duration = int(random.lognormvariate(3.5, 1.0))  # median ~33s
            duration = max(3, min(600, duration))
            created_at = _random_datetime_between(SEED_START, NOW)

            view_events_plan.append({
                'idea_id': idea.id,
                'user_id': uid,
                'event_type': evt,
                'view_duration_seconds': duration,
                'referrer': ref,
                'search_query': None,
                'created_at': created_at,
            })

            # IdeaView (unique per user+idea)
            if uid and (idea.id, uid) not in existing_idea_views:
                idea_views_plan.append({
                    'idea_id': idea.id,
                    'user_id': uid,
                    'viewed_at': created_at,
                })
                existing_idea_views.add((idea.id, uid))

    # Limit totals
    random.shuffle(view_events_plan)
    view_events_plan = view_events_plan[:280]
    idea_views_plan = idea_views_plan[:120]

    if dry_run:
        log.info(f"  [DRY] Would create {len(view_events_plan)} view events + {len(idea_views_plan)} idea views")
        return

    for ve in view_events_plan:
        db.session.add(ViewEvent(**ve))
    for iv in idea_views_plan:
        db.session.add(IdeaView(**iv))

    _safe_commit()
    log.info(f"  ✓ Created {len(view_events_plan)} view events + {len(idea_views_plan)} idea views")


def seed_search_queries(dry_run: bool):
    """Generate ~80 search queries via LLM."""
    log.info("── seed_search_queries ──")

    domains = Domain.query.order_by(Domain.id).all()
    domain_names = [d.name for d in domains]
    domain_name_to_id = {d.name: d.id for d in domains}
    user_ids = [u.id for u in User.query.order_by(User.id).all()]
    all_idea_ids = [i.id for i in ProjectIdea.query.all()]

    if dry_run:
        log.info("  [DRY] Would generate 80 search queries via LLM")
        return

    try:
        prompt = _build_search_queries_prompt(domain_names)
        result = call_ollama(prompt, max_tokens=4000, temperature=0.8)
        queries = result.get('queries', [])
        if not isinstance(queries, list):
            raise ValueError("Expected list of queries")
    except Exception as e:
        log.error(f"  ✗ Failed to generate search queries: {e}")
        return

    queries = queries[:80]

    actions = ['search', 'clicked_idea', 'refined_query', 'abandoned']
    action_weights = [0.35, 0.40, 0.15, 0.10]

    # Group into sessions (2-4 queries per session)
    sessions = []
    i = 0
    while i < len(queries):
        session_size = random.randint(2, 4)
        session_id = str(uuid.uuid4())
        sessions.append((session_id, queries[i:i + session_size]))
        i += session_size

    query_dates = _distribute_dates(len(queries), SEED_START, NOW)
    q_idx = 0

    for session_id, session_queries in sessions:
        for sq in session_queries:
            if not isinstance(sq, dict):
                continue
            query_text = sq.get('query', '')
            domain_name = sq.get('domain', '')
            domain_id = domain_name_to_id.get(domain_name)

            action = random.choices(actions, action_weights)[0]
            clicked_id = None
            if action == 'clicked_idea' and all_idea_ids:
                clicked_id = random.choice(all_idea_ids)

            uid = random.choice(user_ids) if random.random() > 0.3 else None

            search_q = SearchQuery(
                user_id=uid,
                query_text=query_text[:500],
                domain_id=domain_id,
                result_count=random.randint(2, 20),
                user_action=action,
                clicked_idea_id=clicked_id,
                session_id=session_id,
                created_at=query_dates[q_idx] if q_idx < len(query_dates) else _utcnow(),
            )
            db.session.add(search_q)
            q_idx += 1

    _safe_commit()
    log.info(f"  ✓ Created {q_idx} search queries in {len(sessions)} sessions")


def seed_novelty_breakdowns(dry_run: bool):
    """Fill novelty_breakdowns table for all ideas."""
    log.info("── seed_novelty_breakdowns ──")

    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()

    # Check existing (raw SQL since no model)
    existing = set()
    try:
        rows = db.session.execute(db.text("SELECT idea_id FROM novelty_breakdowns")).fetchall()
        existing = set(r[0] for r in rows)
    except Exception:
        pass

    to_insert = [idea for idea in all_ideas if idea.id not in existing]

    if dry_run:
        log.info(f"  [DRY] Would create {len(to_insert)} novelty breakdowns")
        return

    for idea in to_insert:
        novelty = idea.novelty_score_cached or 50
        # Inverse correlation: high novelty = low mean similarity
        mean_sim = round(max(0.1, min(0.85, 1.0 - (novelty / 120.0) + random.uniform(-0.1, 0.1))), 4)
        specificity = round(random.uniform(0.35, 0.92), 4)
        temporal = round(random.uniform(0.25, 0.85), 4)
        saturation = round(random.uniform(0.0, 0.30), 4)
        base_score = round(novelty * 0.7 + random.uniform(-5, 5), 2)
        bonus = round(random.uniform(0, 10), 2)
        weighted = round(base_score + bonus - saturation * 10, 2)
        stabilized = round(weighted * random.uniform(0.9, 1.05), 2)

        src_count = len(idea.sources) if idea.sources else 0
        domain_name = idea.domain.name if idea.domain else 'Unknown'

        db.session.execute(db.text("""
            INSERT INTO novelty_breakdowns
            (idea_id, mean_similarity, similarity_variance, specificity_score,
             temporal_score, saturation_penalty, base_score, bonus_score,
             weighted_score, stabilized_score, retrieved_sources_count,
             referenced_ideas_count, domain, engine, algorithm_version, created_at)
            VALUES (:idea_id, :mean_sim, :sim_var, :spec, :temp, :sat, :base,
                    :bonus, :weighted, :stab, :src_count, :ref_count, :domain,
                    :engine, :algo, :created)
        """), {
            'idea_id': idea.id,
            'mean_sim': mean_sim,
            'sim_var': round(random.uniform(0.01, 0.15), 4),
            'spec': specificity,
            'temp': temporal,
            'sat': saturation,
            'base': base_score,
            'bonus': bonus,
            'weighted': weighted,
            'stab': stabilized,
            'src_count': src_count,
            'ref_count': random.randint(0, 5),
            'domain': domain_name,
            'engine': 'hybrid_v2',
            'algo': '2.1',
            'created': idea.created_at or _utcnow(),
        })

    _safe_commit()
    log.info(f"  ✓ Created {len(to_insert)} novelty breakdowns")


def seed_daily_domain_metrics(dry_run: bool):
    """Fill daily_domain_metrics for 30 days × 10 domains."""
    log.info("── seed_daily_domain_metrics ──")

    domains = Domain.query.order_by(Domain.id).all()
    all_ideas = ProjectIdea.query.order_by(ProjectIdea.created_at).all()

    # Build actual counts per (domain_id, date)
    idea_counts = {}
    novelty_by_day_domain = {}
    for idea in all_ideas:
        if not idea.created_at:
            continue
        d = idea.created_at.date()
        key = (idea.domain_id, d)
        idea_counts[key] = idea_counts.get(key, 0) + 1
        if key not in novelty_by_day_domain:
            novelty_by_day_domain[key] = []
        novelty_by_day_domain[key].append(idea.novelty_score_cached or 50)

    # Check existing
    existing = set()
    try:
        rows = db.session.execute(db.text("SELECT domain_id, date FROM daily_domain_metrics")).fetchall()
        existing = set((r[0], r[1]) for r in rows)
    except Exception:
        pass

    to_insert = []
    for day_offset in range(31):
        d = (SEED_START + timedelta(days=day_offset)).date()
        for domain in domains:
            key = (domain.id, d)
            if key in existing:
                continue
            count = idea_counts.get(key, 0)
            avg_novelty = None
            if key in novelty_by_day_domain:
                scores = novelty_by_day_domain[key]
                avg_novelty = sum(scores) / len(scores)
            total_views = random.randint(0, 20) if count > 0 else random.randint(0, 5)
            to_insert.append({
                'domain_id': domain.id,
                'date': d,
                'ideas_generated': count,
                'avg_novelty_score': avg_novelty,
                'total_views': total_views,
            })

    if dry_run:
        log.info(f"  [DRY] Would create {len(to_insert)} daily domain metrics rows")
        return

    for row in to_insert:
        db.session.execute(db.text("""
            INSERT INTO daily_domain_metrics (domain_id, date, ideas_generated, avg_novelty_score, total_views)
            VALUES (:domain_id, :date, :ideas_generated, :avg_novelty_score, :total_views)
        """), row)

    _safe_commit()
    log.info(f"  ✓ Created {len(to_insert)} daily domain metrics rows")


def seed_idea_relationships(dry_run: bool):
    """Create ~30 idea relationship records between ideas in the same domain."""
    log.info("── seed_idea_relationships ──")

    # Group ideas by domain
    all_ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()
    by_domain = {}
    for idea in all_ideas:
        by_domain.setdefault(idea.domain_id, []).append(idea)

    existing = set()
    try:
        rows = db.session.execute(db.text("SELECT source_idea_id, related_idea_id FROM idea_relationships")).fetchall()
        existing = set((r[0], r[1]) for r in rows)
    except Exception:
        pass

    relation_types = ['similar', 'similar', 'similar', 'evolution', 'complementary']
    candidates = []

    for domain_id, ideas in by_domain.items():
        if len(ideas) < 2:
            continue
        for i in range(len(ideas)):
            for j in range(i + 1, len(ideas)):
                pair = (ideas[i].id, ideas[j].id)
                if pair not in existing and (pair[1], pair[0]) not in existing:
                    candidates.append(pair)

    target = min(30, len(candidates))
    selected = random.sample(candidates, target)

    if dry_run:
        log.info(f"  [DRY] Would create {len(selected)} idea relationships")
        return

    for src_id, rel_id in selected:
        rtype = random.choice(relation_types)
        sim_score = round(random.uniform(0.5, 0.92) if rtype == 'similar' else random.uniform(0.3, 0.7), 4)

        db.session.execute(db.text("""
            INSERT INTO idea_relationships (source_idea_id, related_idea_id, relation_type, similarity_score)
            VALUES (:src, :rel, :rtype, :score)
        """), {'src': src_id, 'rel': rel_id, 'rtype': rtype, 'score': sim_score})

    _safe_commit()
    log.info(f"  ✓ Created {len(selected)} idea relationships")


def seed_abuse_events_diversity(dry_run: bool):
    """Add diverse abuse event types beyond the 112 existing generation_attempt events."""
    log.info("── seed_abuse_events_diversity ──")

    user_ids = [u.id for u in User.query.order_by(User.id).all()]

    new_events = [
        ('rate_limit_exceeded', 5, {"endpoint": "/api/ideas/generate", "limit": "20/hour", "current_count": random.randint(21, 35)}),
        ('generation_spam', 5, {"rapid_requests": random.randint(5, 15), "window_seconds": 60}),
        ('auto_blocked', 3, {"reason": "Exceeded rate limits 3 times in 24h", "block_duration_hours": 24}),
        ('suspicious_pattern', 2, {"pattern": "Repeated identical queries", "query_count": random.randint(10, 30)}),
    ]

    plan = []
    dates = _distribute_dates(15, SEED_START, NOW)
    d_idx = 0
    for event_type, count, details_template in new_events:
        for _ in range(count):
            # Refresh random details per event
            details = dict(details_template)
            if event_type == 'rate_limit_exceeded':
                details['current_count'] = random.randint(21, 35)
            elif event_type == 'generation_spam':
                details['rapid_requests'] = random.randint(5, 15)
            elif event_type == 'suspicious_pattern':
                details['query_count'] = random.randint(10, 30)

            plan.append({
                'user_id': random.choice(user_ids),
                'event_type': event_type,
                'details': details,
                'created_at': dates[d_idx] if d_idx < len(dates) else _utcnow(),
            })
            d_idx += 1

    if dry_run:
        log.info(f"  [DRY] Would create {len(plan)} new abuse events")
        return

    for evt in plan:
        db.session.add(AbuseEvent(
            user_id=evt['user_id'],
            event_type=evt['event_type'],
            details=evt['details'],
            created_at=evt['created_at'],
        ))

    _safe_commit()
    log.info(f"  ✓ Created {len(plan)} new diverse abuse events")


def update_cached_scores(dry_run: bool):
    """Recompute quality_score_cached for all ideas using the actual @property formula."""
    log.info("── update_cached_scores ──")

    all_ideas = ProjectIdea.query.options(
        db.joinedload(ProjectIdea.feedbacks),
        db.joinedload(ProjectIdea.reviews),
        db.joinedload(ProjectIdea.sources),
        db.joinedload(ProjectIdea.admin_verdict),
    ).all()

    if dry_run:
        log.info(f"  [DRY] Would recompute scores for {len(all_ideas)} ideas")
        return

    updated = 0
    for idea in all_ideas:
        new_quality = idea.quality_score  # triggers the @property
        if idea.quality_score_cached != new_quality:
            idea.quality_score_cached = new_quality
            updated += 1

        # Ensure novelty_context exists
        if not idea.novelty_context:
            idea.novelty_context = {
                "engine": "hybrid_v2",
                "domain_maturity": "growing",
                "confidence": "Medium",
                "evidence_score": 0.65,
                "sources_analyzed": len(idea.sources) * 2,
                "explanation": f"Novelty analysis for {idea.title}",
            }

    _safe_commit()
    log.info(f"  ✓ Updated quality_score_cached for {updated}/{len(all_ideas)} ideas")

    # Log distribution
    scores = [i.quality_score_cached for i in all_ideas if i.quality_score_cached is not None]
    if scores:
        log.info(f"    Quality score range: {min(scores)}-{max(scores)}, avg: {sum(scores)/len(scores):.1f}")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='InnovateSphere comprehensive database seeder')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be created without writing')
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        log.info("=" * 64)
        log.info("InnovateSphere — Comprehensive Database Seeder")
        log.info(f"  Mode:      {'DRY RUN' if args.dry_run else 'LIVE'}")
        log.info(f"  Ollama:    {OLLAMA_URL} ({OLLAMA_MODEL})")
        log.info(f"  Timeout:   {OLLAMA_TIMEOUT}s per call, {OLLAMA_MAX_RETRIES} retries")
        log.info("=" * 64)

        if not args.dry_run:
            # Verify Ollama is reachable before starting
            log.info("  Checking Ollama connectivity…")
            try:
                resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
                resp.raise_for_status()
                models = [m.get('name', '') for m in resp.json().get('models', [])]
                if any(OLLAMA_MODEL.split(':')[0] in m for m in models):
                    log.info(f"  ✓ Ollama reachable, model '{OLLAMA_MODEL}' available")
                else:
                    log.warning(f"  ⚠ Ollama reachable but model '{OLLAMA_MODEL}' not found in: {models}")
                    log.warning(f"    Available models: {models}")
                    log.warning(f"    Will attempt to use it anyway (Ollama may pull on demand)")
            except Exception as e:
                log.error(f"  ✗ Cannot reach Ollama at {OLLAMA_URL}: {e}")
                log.error("  Start Ollama first: ollama serve")
                sys.exit(1)

        # ── Step 1: Config tables ──
        seed_config(args.dry_run)

        # ── Step 2: Update existing users ──
        update_existing_users(args.dry_run)

        # ── Step 3: Generate ideas via LLM ──
        new_ideas = seed_ideas(args.dry_run)

        # ── Step 4: Generate sources via LLM ──
        seed_sources(new_ideas, args.dry_run)

        # ── Step 5: Reviews (with LLM comments) ──
        seed_reviews(args.dry_run)

        # ── Step 6: Feedback ──
        seed_feedback(args.dry_run)

        # ── Step 7: Admin verdicts ──
        seed_verdicts(args.dry_run)

        # ── Step 8: Generation traces ──
        seed_traces(new_ideas if new_ideas else [], args.dry_run)

        # ── Step 9: View events + idea views ──
        seed_view_events(args.dry_run)

        # ── Step 10: Search queries ──
        seed_search_queries(args.dry_run)

        # ── Step 11: Novelty breakdowns ──
        seed_novelty_breakdowns(args.dry_run)

        # ── Step 12: Daily domain metrics ──
        seed_daily_domain_metrics(args.dry_run)

        # ── Step 13: Idea relationships ──
        seed_idea_relationships(args.dry_run)

        # ── Step 14: Diverse abuse events ──
        seed_abuse_events_diversity(args.dry_run)

        # ── Step 15: Recompute cached scores ──
        update_cached_scores(args.dry_run)

        # ── Final summary ──
        log.info("")
        log.info("=" * 64)
        if args.dry_run:
            log.info("DRY RUN COMPLETE — no data was written")
        else:
            log.info("SEEDING COMPLETE — Final Database State:")
            tables = [
                ('users', User.query.count()),
                ('project_ideas', ProjectIdea.query.count()),
                ('idea_sources', IdeaSource.query.count()),
                ('idea_reviews', IdeaReview.query.count()),
                ('idea_feedbacks', IdeaFeedback.query.count()),
                ('admin_verdicts', AdminVerdict.query.count()),
                ('generation_traces', db.session.query(GenerationTrace).count()),
                ('view_events', ViewEvent.query.count()),
                ('idea_views', IdeaView.query.count()),
                ('search_queries', SearchQuery.query.count()),
                ('abuse_events', AbuseEvent.query.count()),
                ('bias_profiles', BiasProfile.query.count()),
                ('prompt_versions', PromptVersion.query.count()),
            ]
            for name, count in tables:
                log.info(f"  {name:24s} {count:>6}")
        log.info("=" * 64)


if __name__ == '__main__':
    main()
