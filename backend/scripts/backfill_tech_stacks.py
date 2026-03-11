#!/usr/bin/env python3
"""
Backfill script: Update tech_stack_json for existing ideas that have
vague/generic tech stack entries (e.g., "AI", "NLP", "Cloud Services")
to use specific libraries, frameworks, and tools.

Uses the Gemini LLM (via the app's existing llm_client) to re-recommend
tech stacks based on each idea's problem statement, domain, and modules.

Usage:
    python backend/scripts/backfill_tech_stacks.py              # Full run
    python backend/scripts/backfill_tech_stacks.py --dry-run     # Preview only
    python backend/scripts/backfill_tech_stacks.py --limit 5     # Process 5 ideas

Requirements:
    - DATABASE_URL pointing to the database
    - GEMINI_API_KEY or Ollama running locally
"""

import os
import sys
import json
import logging
import argparse
import time

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['SKIP_STARTUP_CHECKS'] = '1'

# Monkeypatch startup checks
import backend.utils.health_checks as _hc
_hc.run_startup_checks = lambda: None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('backfill_tech')

from backend.core.db import db
from backend.core.app import create_app
from backend.core.models import ProjectIdea, Domain

# Known vague/generic tech names that should be replaced with specific tools
VAGUE_TECH_NAMES = {
    'ai', 'ml', 'nlp', 'machine learning', 'deep learning',
    'cloud services', 'cloud computing', 'cloud', 'big data',
    'big data analytics', 'data analytics', 'analytics',
    'iot', 'blockchain', 'ar/vr', 'ar (augmented reality)',
    'vr (virtual reality)', 'vr/ar', 'web development',
    'mobile app', 'apis', 'wearable tech', 'biosensors',
    'nanotechnology', 'genomics', 'biometrics', 'high-performance computing',
    'real-time sync', 'calendar integration', 'synthetic biology',
    'ai & ml',
}


def is_vague_tech_stack(tech_stack_json):
    """Check if the tech_stack_json contains mostly vague category names."""
    if not tech_stack_json or not isinstance(tech_stack_json, list):
        return True
    
    vague_count = 0
    total = 0
    
    for item in tech_stack_json:
        if not isinstance(item, dict):
            continue
        # Check "name" key (seed data format)
        name = item.get('name', '').strip()
        if name:
            total += 1
            if name.lower() in VAGUE_TECH_NAMES:
                vague_count += 1
        # Check "technologies" key (hybrid/demo format)
        techs = item.get('technologies', [])
        if isinstance(techs, list):
            for t in techs:
                if isinstance(t, str):
                    total += 1
                    if t.lower() in VAGUE_TECH_NAMES:
                        vague_count += 1
    
    if total == 0:
        return True
    
    # If >50% of tech names are vague, flag for update
    return vague_count / total > 0.5


def build_recommender_prompt(idea):
    """Build a prompt to get specific tech recommendations for an idea."""
    domain_name = idea.domain.name if idea.domain else "General"
    modules_str = ""
    if idea.tech_stack_json and isinstance(idea.tech_stack_json, list):
        # Show existing categories so the LLM knows what areas to cover
        categories = []
        for item in idea.tech_stack_json:
            if isinstance(item, dict):
                categories.append(item.get('name', item.get('component', '')))
        if categories:
            modules_str = f"\nExisting categories to cover: {', '.join(categories)}"
    
    return f"""Given the following project idea, recommend SPECIFIC technologies for each component category.

Title: {idea.title}
Domain: {domain_name}
Problem: {idea.problem_statement or 'Not specified'}
{modules_str}

Return a JSON object with a single key "tech_stack" containing an array. Each element must have:
- "component": The technical category (e.g. "Backend", "Frontend", "ML/AI Pipeline", "Database", "DevOps")
- "technologies": An array of SPECIFIC named software — languages, frameworks, libraries, databases, tools.
  Examples: "Python", "FastAPI", "React", "PostgreSQL", "PyTorch", "Docker", "Redis", "scikit-learn", "Kafka"
  NEVER use vague categories like "AI", "ML", "Cloud", "NLP", "Big Data", "Analytics", "IoT".
- "rationale": One sentence explaining why these specific tools suit this project.

Example format:
{{"tech_stack": [{{"component": "Backend", "technologies": ["Python", "FastAPI"], "rationale": "..."}}]}}

Return ONLY the JSON object, no markdown, no explanation. Cover 3-6 component categories.
"""


def backfill(dry_run=False, limit=None, force=False):
    """Main backfill logic."""
    app = create_app()
    
    with app.app_context():
        query = ProjectIdea.query.order_by(ProjectIdea.id)
        ideas = query.all()
        
        if force:
            candidates = list(ideas)
            log.info(f"Force mode: will process ALL {len(candidates)} ideas")
        else:
            candidates = []
            for idea in ideas:
                if is_vague_tech_stack(idea.tech_stack_json):
                    candidates.append(idea)
            log.info(f"Found {len(candidates)} ideas with vague tech stacks (out of {len(ideas)} total)")
        
        if limit:
            candidates = candidates[:limit]
        
        if not candidates:
            log.info("Nothing to backfill!")
            return
        
        if dry_run:
            for idea in candidates:
                ts = idea.tech_stack_json
                names = []
                if isinstance(ts, list):
                    for item in ts:
                        if isinstance(item, dict):
                            names.append(item.get('name', item.get('component', '?')))
                log.info(f"  [DRY] ID {idea.id}: {idea.title[:60]} — current tech: {', '.join(names)}")
            log.info(f"  [DRY] Would update {len(candidates)} ideas")
            return
        
        # Import LLM client
        try:
            from backend.ai.llm_client import generate_json
            log.info("Using app LLM client (generate_json)")
        except ImportError:
            log.error("Cannot import LLM client. Make sure the app is properly configured.")
            return
        
        updated = 0
        failed = 0
        
        for i, idea in enumerate(candidates):
            log.info(f"  [{i+1}/{len(candidates)}] Processing: {idea.title[:60]}...")
            
            prompt = build_recommender_prompt(idea)
            
            try:
                result = generate_json(
                    prompt,
                    max_tokens=800,
                    temperature=0.2,
                )
                
                # Extract tech_stack array from the dict response
                parsed = result.get('tech_stack', [])
                
                if not isinstance(parsed, list) or len(parsed) == 0:
                    log.warning(f"    ✗ Invalid response format (no tech_stack array), skipping")
                    failed += 1
                    continue
                
                # Validate structure
                valid_items = []
                for item in parsed:
                    if isinstance(item, dict) and 'component' in item and 'technologies' in item:
                        valid_items.append(item)
                
                if not valid_items:
                    log.warning(f"    ✗ No valid tech stack items, skipping")
                    failed += 1
                    continue
                
                # Update the idea
                idea.tech_stack_json = valid_items
                
                # Build descriptive text
                parts = []
                for item in valid_items:
                    techs = item.get('technologies', [])
                    if isinstance(techs, list) and techs:
                        parts.append(f"{item['component']}: {', '.join(str(t) for t in techs)}")
                    else:
                        parts.append(item['component'])
                idea.tech_stack = ' | '.join(parts)[:500]
                
                db.session.commit()
                updated += 1
                
                tech_summary = ' | '.join(
                    f"{item['component']}: {', '.join(item.get('technologies', [])[:2])}"
                    for item in valid_items[:3]
                )
                log.info(f"    ✓ Updated: {tech_summary}")
                
                # Rate limiting
                time.sleep(0.5)
                
            except json.JSONDecodeError as e:
                log.warning(f"    ✗ JSON parse error: {e}")
                failed += 1
                db.session.rollback()
            except Exception as e:
                log.error(f"    ✗ Error: {e}")
                failed += 1
                db.session.rollback()
        
        log.info(f"\n  Done! Updated: {updated}, Failed: {failed}, Skipped: {len(candidates) - updated - failed}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill vague tech stacks with specific technologies')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no changes')
    parser.add_argument('--limit', type=int, help='Max number of ideas to process')
    parser.add_argument('--force', action='store_true', help='Process ALL ideas, not just vague ones')
    args = parser.parse_args()
    
    backfill(dry_run=args.dry_run, limit=args.limit, force=args.force)
