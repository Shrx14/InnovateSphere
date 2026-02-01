"""
Evidence-anchored idea generator (Segment 3.1)

Research-grade pipeline with epistemic controls.
"""

from typing import Dict, Any, Optional
import json
import logging

from backend.db import db
from backend.models import ProjectIdea, IdeaRequest, IdeaSource, Domain
from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.filter import filter_sources
from backend.semantic.ranker import rank_sources
from backend.services.novelty_service import analyze_novelty
from backend.ai_registry import get_active_ai_pipeline_version
from .prompt_builder import build_generation_prompt
from .schemas import validate_generated_idea

logger = logging.getLogger(__name__)


# ----------------------------
# Evidence Gate
# ----------------------------

def check_evidence_sufficiency(sources: list, novelty_score: float) -> Optional[str]:
    if len(sources) < 4:
        return "evidence_insufficient_count"
    source_types = {s.get("source_type") for s in sources if s.get("source_type")}
    if len(source_types) < 2:
        return "evidence_insufficient_diversity"
    if novelty_score < 45:
        return "novelty_below_threshold"
    return None


# ----------------------------
# Deterministic Mock LLM
# ----------------------------

def mock_llm_generate(prompt: str) -> str:
    """
    Deterministic, schema-valid mock output.
    Replace with real LLM (temp ≤ 0.4) in Segment 3.2+.
    """
    return json.dumps({
        "title": "AI-Powered Code Review Assistant",
        "problem_formulation": {
            "context": "Manual code reviews are time-consuming and error-prone.",
            "why_this_problem_matters": "Automation can improve code quality and developer efficiency.",
            "evidence_basis": ["S1", "S3"]
        },
        "related_work_synthesis": {
            "common_approaches": "Static analysis tools and human reviews.",
            "observed_limitations": "Limited contextual understanding and scalability.",
            "evidence_basis": ["S1", "S2"]
        },
        "proposed_contribution": {
            "core_idea": "A learning-based assistant for contextual code review.",
            "what_is_new": "Combines static analysis with NLP-driven reasoning.",
            "why_it_is_plausible": "ML has proven effective in code understanding tasks.",
            "evidence_basis": ["S2", "S3"]
        },
        "system_or_project_design": {
            "modules": [
                {
                    "name": "Code Parser",
                    "responsibility": "Extract syntactic and semantic features.",
                    "justification": "AST-based parsing is standard in code analysis."
                }
            ]
        },
        "technology_choices": [
            {
                "technology": "Python",
                "role": "Core language",
                "justification": "Strong ML and static analysis ecosystem."
            }
        ],
        "novelty_positioning": {
            "novelty_score": 67.2,
            "interpretation": "Moderate novelty through integration of methods.",
            "tradeoffs": "Does not guarantee perfect review accuracy."
        },
        "limitations_and_risks": [
            "False positives",
            "Bias toward common coding patterns"
        ],
        "evidence_sources": [
            {
                "source_id": "S1",
                "title": "Challenges in Code Review",
                "url": "https://arxiv.org/abs/xxxx",
                "source_type": "arxiv",
                "used_for": "Problem context"
            },
            {
                "source_id": "S2",
                "title": "Automated Code Analysis Tools",
                "url": "https://github.com/example/repo",
                "source_type": "github",
                "used_for": "Existing methods"
            },
            {
                "source_id": "S3",
                "title": "ML for Software Engineering",
                "url": "https://arxiv.org/abs/yyyy",
                "source_type": "arxiv",
                "used_for": "Feasibility"
            },
            {
                "source_id": "S4",
                "title": "NLP for Code Understanding",
                "url": "https://example.com/nlp-code",
                "source_type": "web",
                "used_for": "Supporting evidence"
            }
        ]
    })


# ----------------------------
# Main Pipeline
# ----------------------------

def generate_idea(query: str, domain_id: int, user_id: int) -> Dict[str, Any]:
    domain = Domain.query.get(domain_id)
    if not domain:
        return {"error": "Invalid domain_id"}

    retrieved = retrieve_sources(query=query, domain=domain.name)
    sources = retrieved.get("sources", [])[:20]  # early cap
    if not sources:
        return {"error": "No sources retrieved", "failure_stage": "retrieval"}

    filtered = filter_sources(sources, query)
    ranked = rank_sources(filtered, query)[:10]

    novelty_input = "\n".join(
        f"[{s['source_type']}] {s['title']}: {s.get('summary','')}"
        for s in ranked
    )
    novelty_result = analyze_novelty(novelty_input, domain.name)
    novelty_score = novelty_result.get("novelty_score", 0)

    gate_error = check_evidence_sufficiency(ranked, novelty_score)
    if gate_error:
        persist_generation_attempt(user_id, domain_id, gate_error, None)
        return {"error": gate_error, "failure_stage": "pre_generation"}

    prompt = build_generation_prompt(
        query, domain.name, ranked, novelty_result
    )

    for attempt in range(2):
        try:
            raw = mock_llm_generate(prompt)
            parsed = json.loads(raw)
            validated = validate_generated_idea(parsed)
            break
        except Exception as e:
            if attempt == 1:
                persist_generation_attempt(user_id, domain_id, "schema_validation", str(e))
                return {"error": "Schema validation failed", "failure_stage": "schema"}
            prompt += "\nSTRICT MODE: Output valid JSON only."

    data = validated.dict()
    ai_version = get_active_ai_pipeline_version()

    problem_summary = (
        f"{data['problem_formulation']['context']} "
        f"This matters because {data['problem_formulation']['why_this_problem_matters']}."
    )[:300]

    tech_summary = ", ".join(
        t["technology"] for t in data["technology_choices"]
    )[:150]

    idea = ProjectIdea(
        title=data["title"],
        problem_statement=problem_summary,
        problem_statement_json=data["problem_formulation"],
        tech_stack=tech_summary,
        tech_stack_json=data["technology_choices"],
        domain_id=domain_id,
        ai_pipeline_version=ai_version,
        is_ai_generated=True,
        is_public=True,
        is_validated=True,
    )
    db.session.add(idea)
    db.session.flush()

    for src in data["evidence_sources"]:
        db.session.add(IdeaSource(
            idea_id=idea.id,
            source_type=src["source_type"],
            title=src["title"],
            url=src["url"],
            summary=src["used_for"],
        ))

    db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))
    db.session.commit()

    return {
        "idea": data,
        "novelty_score": novelty_score,
        "evidence_summary": {
            "source_count": len(ranked),
            "source_types": sorted({s["source_type"] for s in ranked}),
        },
    }


def persist_generation_attempt(user_id: int, domain_id: int, stage: str, details: Optional[str]):
    logger.warning(
        "Generation failed | user=%s domain=%s stage=%s details=%s",
        user_id, domain_id, stage, details
    )
