from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime, timedelta

from backend.core.config import Config
from backend.core.db import db
from backend.core.models import (
    ProjectIdea,
    IdeaRequest,
    IdeaSource,
    Domain,
    GenerationTrace,
)
from backend.generation.job_queue import get_job_queue

logger = logging.getLogger(__name__)

from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.filter import filter_by_semantic_similarity
from backend.evaluation.service import get_reference_eval_index


def _get_domain_threshold(domain_name: str, cap: float = 0.4) -> float:
    """Get the similarity threshold for a domain, capped at `cap`."""
    from backend.novelty.config import SIMILARITY_THRESHOLDS
    return min(SIMILARITY_THRESHOLDS.get(domain_name.lower(), 0.6), cap)


def _filter_with_fallback(
    query: str,
    raw_sources: list,
    threshold: float,
    min_required: int | None = None,
) -> list:
    """Apply semantic filtering with progressive fallback.

    Tries the given *threshold* first, then halves it repeatedly (down to 0.1)
    until at least *min_required* sources survive filtering.  Falls back to the
    full *raw_sources* list if all thresholds fail.
    """
    if min_required is None:
        min_required = getattr(Config, "MIN_EVIDENCE_REQUIRED", 2)

    filtered = filter_by_semantic_similarity(query, raw_sources, threshold)

    fallback_thresholds = [max(0.2, threshold / 2), 0.2, 0.1]
    for fb in fallback_thresholds:
        if len(filtered) >= min_required or len(raw_sources) < min_required:
            break
        logger.info(
            "Progressive fallback: %d/%d sources, retrying at threshold=%.2f",
            len(filtered), len(raw_sources), fb,
        )
        filtered = filter_by_semantic_similarity(query, raw_sources, fb)

    if not filtered:
        logger.warning(
            "Semantic filter exhausted all fallbacks — using all %d raw sources",
            len(raw_sources),
        )
        filtered = raw_sources

    return filtered

from backend.semantic.ranker import rank_sources

# Novelty analysis - required dependency
from backend.novelty.service import analyze_novelty


from backend.ai.registry import get_active_ai_pipeline_version
from backend.ai.registry import get_active_bias_profile

from backend.ai.llm_client import generate_json, TransientLLMError
from backend.ai.prompts import (
    PASS1_SYSTEM,
    PASS1_PROMPT_TEMPLATE,
    PASS2_SYSTEM,
    PASS2_PROMPT_TEMPLATE,
    PASS3_SYSTEM,
    PASS3_PROMPT_TEMPLATE,
    PASS4_SYSTEM,
    PASS4_PROMPT_TEMPLATE,
    DIRECT_GENERATION_SYSTEM,
    DIRECT_GENERATION_PROMPT_TEMPLATE,
    HYBRID_PASS1_SYSTEM,
    HYBRID_PASS1_PROMPT_TEMPLATE,
    HYBRID_PASS2_SYSTEM,
    HYBRID_PASS2_PROMPT_TEMPLATE,
    GCR_GENERATOR_SYSTEM,
    GCR_GENERATOR_PROMPT_TEMPLATE,
    GCR_CRITIC_SYSTEM,
    GCR_CRITIC_PROMPT_TEMPLATE,
    GCR_REFINER_SYSTEM,
    GCR_REFINER_PROMPT_TEMPLATE,
)
from .schemas import validate_generated_idea, validate_hybrid_idea
from .constraints import build_hitl_constraints, is_rejected_pattern, filter_hallucinated_sources


def _build_tech_stack_text(tech_list: List[Dict[str, Any]]) -> str:
    """Build a human-readable tech stack string from structured JSON.
    
    Handles both schema formats:
      - {component, technologies, rationale}  (hybrid/demo format)
      - {name, role, justification}           (seed data format)
    
    Returns strings like:
      "Backend: FastAPI, PostgreSQL | ML/AI: PyTorch, scikit-learn"
    """
    if not tech_list or not isinstance(tech_list, list):
        return "Not specified"
    
    parts = []
    for t in tech_list:
        if not isinstance(t, dict):
            continue
        
        # Hybrid/demo format: {component, technologies, rationale}
        if "component" in t and "technologies" in t:
            techs = t.get("technologies", [])
            if isinstance(techs, list) and techs:
                parts.append(f"{t['component']}: {', '.join(str(x) for x in techs)}")
            else:
                parts.append(t["component"])
        # Seed/legacy format: {name, role, justification}
        elif "name" in t:
            name = t.get("name", "")
            role = t.get("role", "")
            if role:
                parts.append(f"{name} — {role}")
            else:
                parts.append(name)
        # Multi-pass technology_choices format: {technology, role, justification}
        elif "technology" in t:
            tech = t.get("technology", "")
            role = t.get("role", "")
            if role:
                parts.append(f"{tech} — {role}")
            else:
                parts.append(tech)
    
    return (" | ".join(parts))[:500] if parts else "Not specified"


# Module-level feasibility estimator (used to populate Phase 0 bounds)
def estimate_feasibility_module(query: str, domain: str, sources: List[Dict[str, Any]], novelty: Dict[str, Any]) -> Dict[str, Any]:
    source_count = max(0, len(sources))
    novelty_score = float(novelty.get("novelty_score", 0)) if novelty else 0.0

    base = 50
    source_bonus = (source_count - 3) * 5
    novelty_penalty = (70 - novelty_score) * 0.5

    feasibility_score = int(max(0, min(100, base + source_bonus + novelty_penalty)))

    if feasibility_score > 75:
        complexity = "low"
    elif feasibility_score > 45:
        complexity = "medium"
    else:
        complexity = "high"

    estimated_time_weeks = round(max(1.0, (100 - feasibility_score) / 10.0 + (0.5 if complexity == "low" else 1.5 if complexity == "medium" else 3.0)), 1)

    if feasibility_score > 80:
        team_size = 1
    elif feasibility_score > 60:
        team_size = 2
    elif feasibility_score > 40:
        team_size = 3
    else:
        team_size = 5

    uncertainty = round(max(0.05, min(0.95, 1.0 - min(1.0, source_count / 10.0) * 0.7)), 2)

    return {
        "feasibility_score": feasibility_score,
        "complexity": complexity,
        "estimated_time_weeks": estimated_time_weeks,
        "recommended_team_size": team_size,
        "uncertainty": uncertainty,
        "source_count": source_count,
        "novelty_score": novelty_score,
    }


# Evidence sufficiency gate (cheap, pre-LLM)
def check_evidence_sufficiency(
    sources: List[Dict[str, Any]], novelty_score: float
) -> Optional[str]:
    if len(sources) < Config.MIN_EVIDENCE_REQUIRED:
        return "evidence_insufficient_count"

    # Novelty score threshold: reject ideas that are too derivative
    # Only enforced in non-demo modes (demo bypasses the gate entirely)
    if novelty_score < Config.MIN_NOVELTY_SCORE:
        return "novelty_below_threshold"

    return None


def _select_novelty_text_for_idea(idea_payload: Dict[str, Any], fallback_query: str) -> str:
    """Pick the best text span for idea-grounded novelty scoring."""
    if not isinstance(idea_payload, dict):
        return fallback_query

    candidates = [
        idea_payload.get("problem_statement"),
        idea_payload.get("novelty_reason"),
        idea_payload.get("title"),
    ]
    merged = "\n".join(str(c).strip() for c in candidates if c and str(c).strip())
    return merged if merged else fallback_query


def _compute_evaluation_metrics(idea_payload: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Compute evaluation metrics (INS/CS) when the framework is enabled."""
    if not getattr(Config, "ENABLE_EVALUATION_FRAMEWORK", False):
        return {}
    if not isinstance(idea_payload, dict):
        return {}

    metrics: Dict[str, Any] = {}
    try:
        from backend.evaluation.metrics import compute_cs, compute_ins

        metrics["cs"] = round(compute_cs(idea_payload), 4)

        reference_index = get_reference_eval_index()
        if reference_index is not None:
            eval_text = _select_novelty_text_for_idea(idea_payload, query)
            metrics["ins"] = round(
                compute_ins(
                    eval_text,
                    reference_index,
                    k=max(1, getattr(Config, "EVAL_REFERENCE_NEIGHBORS", 5)),
                ),
                4,
            )
    except Exception as e:
        logger.warning("[EVAL] Evaluation metrics failed: %s", e)
        return {}

    return metrics


# HITL guardrails (domain-level safety)
def check_hitl_guardrails(domain_id: int):
    cutoff = datetime.utcnow() - timedelta(days=30)

    ideas = ProjectIdea.query.filter(
        ProjectIdea.domain_id == domain_id,
        ProjectIdea.created_at >= cutoff,
    ).all()

    if not ideas:
        return None

    bad = sum(
        1
        for idea in ideas
        if idea.evidence_strength == "low"
        or idea.hallucination_risk_level == "high"
        or idea.novelty_confidence == "low"
    )

    if bad / len(ideas) > 0.5:
        return {
            "error": "Idea generation blocked",
            "reason": "Sustained low-quality output in this domain",
        }

    return None


# Grounding enforcement (critical)
def enforce_grounding(final: Dict[str, Any]):
    # Be defensive: ensure expected structure exists and provide clear errors
    sources = final.get("evidence_sources")
    if not isinstance(sources, list):
        raise ValueError("Ungrounded: 'evidence_sources' missing or invalid in LLM output")

    source_ids = {str(s.get("source_id")) for s in sources if isinstance(s, dict) and s.get("source_id") is not None}

    for key in ("problem_formulation", "related_work_synthesis", "proposed_contribution"):
        section = final.get(key)
        if not isinstance(section, dict):
            raise ValueError(f"Ungrounded: LLM output missing required section '{key}'")

        evidence_basis = section.get("evidence_basis")
        if not isinstance(evidence_basis, (list, tuple)):
            raise ValueError(f"Ungrounded: section '{key}' missing 'evidence_basis' list")

        for sid in evidence_basis:
            if str(sid) not in source_ids:
                raise ValueError(f"Ungrounded evidence reference: {sid}")


# Multi-pass LLM pipeline (core)
def multi_pass_llm_generate(
    query: str,
    domain: str,
    sources: List[Dict[str, Any]],
    novelty: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    
    # ------------------
    # Phase 0: Feasibility estimation (uses module-level estimate_feasibility_module)
    # ------------------

    # Apply HITL source penalties (deterministic weighting)
    for src in sources:
        url = src.get("url")
        penalty = constraints["source_penalties"].get(url, 1.0)
        src["_hitl_weight"] = penalty

    # Sort sources by HITL weight descending (higher weight first)
    sources = sorted(sources, key=lambda s: s["_hitl_weight"], reverse=True)

    sources = sources[: Config.MAX_SOURCES_FOR_LLM]

    # ========================================================
    # PRODUCTION MODE: FULL MULTI-PASS PIPELINE
    # ========================================================
    # Note: Demo mode is handled by generate_direct_to_llm() and never reaches here.
    
    # Inject HITL constraints into prompts
    pass1_system = PASS1_SYSTEM
    if constraints["domain_strictness"] > 1.0:
        pass1_system += "\n\nADDITIONAL CONSTRAINTS:\n- Use conservative analysis and avoid speculative gaps.\n- Require stronger evidence for any identified limitations."

    penalized_urls = [url for url, mult in constraints["source_penalties"].items() if mult < 1.0]
    if penalized_urls:
        pass1_system += "\n- Avoid over-reliance on sources that have been previously rejected by reviewers."

    # ========================================================
    # PHASE 2: IDEA SPACE ANALYSIS (Explicit Landscape Study)
    # ========================================================
    # Pass 1 — landscape analysis (identifies patterns, gaps, saturated zones)
    try:
        pass1_body = PASS1_PROMPT_TEMPLATE
        pass1_body = pass1_body.replace("{domain}", domain)
        pass1_body = pass1_body.replace(
            "{sources}",
            "\n".join(f"[{i}] {s['title']} ({s['source_type']})" for i, s in enumerate(sources)),
        )

        analysis = generate_json(
            pass1_system + pass1_body,
            task_type="generation_analysis",
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 1 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 2 - Landscape Analysis): LLM error") from e

    # ========================================================
    # PHASE 3: CONSTRAINT-GUIDED SYNTHESIS
    # ========================================================
    # PASS 2 — problem framing (informed by landscape analysis)
    try:
        pass2_body = PASS2_PROMPT_TEMPLATE
        pass2_body = pass2_body.replace("{analysis}", json.dumps(analysis))
        pass2_body = pass2_body.replace("{context}", query)
        idea = generate_json(
            PASS2_SYSTEM + pass2_body,
            task_type="generation_synthesis",
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 2 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 3 - Problem Framing): LLM error") from e
    # Defensive: ensure idea is a dict
    if not isinstance(idea, dict):
        logger.warning("PASS2 returned unexpected type; coercing to empty dict")
        idea = {}

    # PASS 3 — evidence validation
    try:
        pass3_body = PASS3_PROMPT_TEMPLATE
        pass3_body = pass3_body.replace("{idea}", json.dumps(idea))
        pass3_body = pass3_body.replace(
            "{sources}",
            "\n".join(f"[{i}] {s['title']} — {s['url']}" for i, s in enumerate(sources)),
        )
        evidence = generate_json(
            PASS3_SYSTEM + pass3_body,
            task_type="generation_validation",
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 3 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 3 - Evidence Validation): LLM error") from e
    # Defensive: ensure evidence is a dict and has validated_sources list
    if not isinstance(evidence, dict):
        logger.warning("PASS3 returned unexpected type; coercing to empty evidence dict")
        evidence = {}

    validated_list = [s for s in evidence.get("validated_sources", []) if isinstance(s, dict)]
    if len(validated_list) < Config.MIN_EVIDENCE_REQUIRED:
        raise ValueError("Insufficient validated evidence")

    validated_ids = {str(s.get("id")): s for s in validated_list if s.get("id") is not None}

    # Enforce admin-validated evidence preference
    validated_urls = {s.get("url") for s in validated_list if s.get("url")}
    sources = [
        s for s in sources
        if s["url"] in validated_urls
    ]
    # Preserve HITL weighting order — do not re-sort

    # ========================================================
    # PHASE 4: EVIDENCE-ANCHORED OUTPUT (USED IN BOTH MODES)
    # ========================================================
    # PASS 4 — grounded assembly
    try:
        pass4_body = PASS4_PROMPT_TEMPLATE
        pass4_body = pass4_body.replace("{analysis}", json.dumps(analysis))
        pass4_body = pass4_body.replace("{evidence}", json.dumps(evidence))
        pass4_body = pass4_body.replace("{novelty}", json.dumps(novelty))
        final = generate_json(
            PASS4_SYSTEM + pass4_body,
            task_type="generation_assembly",
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 4 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 4 - Output Synthesis): LLM error") from e
    # Defensive: ensure final is a dict
    if not isinstance(final, dict):
        logger.error("PASS4 returned invalid type; expected JSON object")
        raise ValueError("LLM returned invalid final structure")

    final_sources = [s for s in final.get("evidence_sources", []) if isinstance(s, dict)]
    for src in final_sources:
        if str(src.get("source_id")) not in validated_ids:
            raise ValueError("PASS4 used non-validated source")

    # Enforce grounding (will raise if structure incomplete)
    enforce_grounding(final)
    
    # Return phases for tracing
    return {
        "final": final,
        "phase_0": {"query": query, "domain": domain},
        "phase_1": analysis,  # Landscape analysis
        "phase_2": idea,      # Problem framing
        "phase_3": evidence,  # Evidence validation
    }


# ================================================================
# HYBRID MODE: 2-pass generation (real retrieval + real novelty)
# ================================================================
def generate_hybrid(
    query: str, domain_id: int, user_id: int, job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Hybrid pipeline: real retrieval, real novelty scoring, 2-pass LLM.

    Pass 1 — Landscape Analysis  (identifies patterns, gaps)
    Pass 2 — Grounded Generation (single idea informed by analysis + novelty)

    Total LLM calls: 2  (~30-50s on CPU with 7B model)
    """
    from backend.utils.common import truncate_source_for_prompt, truncate_novelty_gaps

    logger.info("[HYBRID] Starting 2-pass generation: query='%s'", query[:80])
    job_queue = get_job_queue() if job_id else None

    # Set hybrid-specific phase names
    if job_queue:
        job_queue.set_phase_names(job_id, {
            0: "Retrieving sources",
            1: "Analyzing novelty",
            2: "Generating idea with AI",
            3: "Validating & saving",
            4: "Complete",
        })

    # --- Abuse check ---
    try:
        from backend.core.abuse import check_generation_rate, record_abuse_event
        if check_generation_rate(user_id):
            try:
                record_abuse_event(user_id, "generation_blocked", {"query": query[:200]})
            except Exception:
                pass
            return {"error": "rate_limited"}
        try:
            record_abuse_event(user_id, "generation_attempt", {"query": query[:200]})
        except Exception:
            pass
    except Exception:
        logger.exception("Abuse subsystem error; continuing generation")

    # --- Domain lookup ---
    domain = Domain.query.get(domain_id)
    if not domain:
        return {"error": "Invalid domain_id"}

    if job_queue:
        job_queue.update_job_status(job_id, "running", 0, 5)

    guardrail = check_hitl_guardrails(domain_id)
    if guardrail:
        return guardrail

    # =============================================
    # Phase 0  — Retrieve sources  (0-30%)
    # =============================================
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 0, 10)

        retrieved = retrieve_sources(query=query, domain=domain.name)
        raw_sources = retrieved.get("sources", []) if retrieved else []
        # Filter out sources previously flagged as hallucinated
        raw_sources = filter_hallucinated_sources(raw_sources)
        logger.info("[HYBRID] Retrieved %d raw sources (post-hallucination filter)", len(raw_sources))

        if not raw_sources:
            logger.warning("[HYBRID] No sources for query='%s'", query[:60])
            return {"error": "No sources found for topic. Please try a different topic."}

        # Semantic filter with progressive fallback
        threshold = _get_domain_threshold(domain.name, cap=0.4)
        filtered = _filter_with_fallback(query, raw_sources, threshold)

        ranked = rank_sources(filtered)
        if not ranked:
            return {"error": "Could not rank sources. Please try again."}

        if job_queue:
            job_queue.set_intermediate_result(job_id, "sources", ranked)
            job_queue.update_job_status(job_id, "running", 0, 30)

    except Exception as e:
        logger.error("[HYBRID] Retrieval error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, f"Retrieval error: {e}")
        return {"error": f"Retrieval error: {e}"}

    # =============================================
    # Phase 1  — Novelty precheck (query-grounded)  (30-50%)
    # =============================================
    try:
        novelty = analyze_novelty(
            query,
            domain.name,
            preloaded_sources=ranked,
            query_text=query,
        )
        novelty["scoring_mode"] = "query_precheck"
        novelty["input_text"] = query

        if job_queue:
            job_queue.set_intermediate_result(job_id, "novelty", novelty)
            job_queue.update_job_status(job_id, "running", 1, 50)

    except Exception as e:
        logger.error("[HYBRID] Novelty error: %s", e)
        novelty = {"novelty_score": 50, "confidence": "Low", "insights": {}, "sources": []}

    # Evidence gate
    gate_error = check_evidence_sufficiency(ranked, novelty.get("novelty_score", 0))
    if gate_error:
        return {"error": gate_error}

    # =============================================
    # Phase 2  — 2-Pass LLM generation  (50-85%)
    # =============================================
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 2, 55)

        # HITL constraints
        try:
            constraints = build_hitl_constraints(domain.name, ranked)
        except Exception:
            constraints = {"source_penalties": {}, "pattern_penalties": [], "domain_strictness": 1.0}

        # Prepare truncated sources for prompt
        top_sources = ranked[: Config.HYBRID_MAX_SOURCES_FOR_PROMPT]
        source_lines = []
        for i, s in enumerate(top_sources):
            source_lines.append(f"[{i}] ({s.get('source_type','?').upper()}) {truncate_source_for_prompt(s)}")
        sources_text = "\n".join(source_lines)

        # --- Pass 1: Landscape Analysis ---
        pass1_system = HYBRID_PASS1_SYSTEM
        if constraints.get("domain_strictness", 1.0) > 1.0:
            pass1_system += "\n\nADDITIONAL: Use conservative analysis; require stronger evidence."

        pass1_body = (
            HYBRID_PASS1_PROMPT_TEMPLATE
            .replace("{domain}", domain.name)
            .replace("{query}", query)
            .replace("{sources}", sources_text)
        )
        prompt_len = len(pass1_system + pass1_body)
        logger.info("[HYBRID] Pass 1 prompt length: %d chars", prompt_len)

        try:
            analysis = generate_json(
                pass1_system + pass1_body,
                max_tokens=800,
                temperature=0.2,
                task_type="generation_analysis",
            )
        except Exception as e:
            logger.warning("[HYBRID] Pass 1 failed (%s); using novelty insights as fallback", e)
            # Fallback: construct analysis from novelty insights
            insights = novelty.get("insights", {})
            analysis = {
                "existing_approaches": [
                    {
                        "approach": str(insights.get("summary", "common baseline approach"))[:180],
                        "limitation": "Derived from novelty precheck due to pass-1 fallback",
                        "papers": [0],
                    }
                ],
                "underexplored_intersections": [
                    {
                        "intersection": "Cross-domain synthesis",
                        "why_unexplored": "Limited direct evidence across retrieved sources",
                        "opportunity_signal": "Novelty precheck indicates room for differentiation",
                    }
                ],
                "constrained_novelty_zones": [
                    {
                        "zone": g,
                        "current_best": "Existing approaches cluster around similar implementations",
                        "gap_type": "generalization",
                    }
                    for g in truncate_novelty_gaps(novelty.get("gaps", []), max_items=3)
                ],
            }

        if job_queue:
            job_queue.update_job_status(job_id, "running", 2, 70)

        # --- Pass 2: Grounded Generation ---
        # Extract novelty gaps for prompt
        raw_zones = analysis.get("constrained_novelty_zones", [])
        gap_strings = []
        for z in raw_zones[:3]:
            if isinstance(z, dict):
                zone = str(z.get("zone", "")).strip()
                gap_type = str(z.get("gap_type", "")).strip()
                if zone:
                    gap_strings.append(f"{zone} ({gap_type})" if gap_type else zone)

        # Backward compatibility with earlier pass1 schema
        if not gap_strings:
            raw_gaps = analysis.get("gaps", [])
            gap_strings = truncate_novelty_gaps(raw_gaps, max_items=3, max_words=50)
        if not gap_strings:
            # Fallback: use novelty insights
            for k, v in novelty.get("insights", {}).items():
                gap_strings.append(str(v)[:200])
                if len(gap_strings) >= 3:
                    break
        novelty_gaps_text = "\n".join(f"- {g}" for g in gap_strings) if gap_strings else "No specific gaps identified"

        pass2_body = (
            HYBRID_PASS2_PROMPT_TEMPLATE
            .replace("{query}", query)
            .replace("{domain}", domain.name)
            .replace("{analysis}", json.dumps(analysis, default=str))
            .replace("{novelty_gaps}", novelty_gaps_text)
            .replace("{sources}", sources_text)
        )
        prompt_len = len(HYBRID_PASS2_SYSTEM + pass2_body)
        logger.info("[HYBRID] Pass 2 prompt length: %d chars", prompt_len)

        idea_raw = generate_json(
            HYBRID_PASS2_SYSTEM + pass2_body,
            max_tokens=1000,
            temperature=0.3,
            task_type="generation_synthesis",
        )

    except TransientLLMError as e:
        logger.error("[HYBRID] LLM transient error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, str(e) or "LLM transient failure")
        return {"error": str(e) or "LLM transient failure", "transient": True}
    except (RuntimeError, ValueError) as e:
        logger.error("[HYBRID] LLM generation error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, str(e) or "LLM generation failed")
        return {"error": str(e) or "LLM generation failed"}
    except Exception as e:
        logger.exception("[HYBRID] Unexpected LLM error")
        if job_queue:
            import traceback
            job_queue.set_job_error(job_id, f"Generation failed: {e}", traceback.format_exc())
        return {"error": f"Generation failed: {e}"}

    # =============================================
    # Phase 3  — Validate & persist  (85-100%)
    # =============================================
    if job_queue:
        job_queue.update_job_status(job_id, "running", 3, 85)

    # Ensure idea_raw is a dict
    if not isinstance(idea_raw, dict):
        logger.error("[HYBRID] LLM returned non-dict: %s", type(idea_raw))
        return {"error": "LLM returned invalid structure"}

    # Validate via relaxed schema
    try:
        parsed = validate_hybrid_idea(idea_raw)
        parsed_dict = parsed.model_dump()
    except Exception as e:
        logger.warning("[HYBRID] Schema validation partial fail: %s", e)
        # Use raw data with minimal sanity check
        parsed_dict = idea_raw
        if "title" not in parsed_dict:
            parsed_dict["title"] = f"Idea: {query[:80]}"
        if "problem_statement" not in parsed_dict:
            parsed_dict["problem_statement"] = query

    evaluation_metrics: Dict[str, Any] = {}

    # Pattern rejection
    pattern_check = is_rejected_pattern(parsed_dict, constraints)
    if pattern_check:
        return pattern_check

    # Final novelty score for idea generation must be idea-grounded.
    novelty_input = _select_novelty_text_for_idea(parsed_dict, query)
    try:
        novelty = analyze_novelty(
            novelty_input,
            domain.name,
            preloaded_sources=ranked,
            query_text=query,
        )
        novelty["scoring_mode"] = "generated_idea"
        novelty["input_text"] = novelty_input
        novelty["query_text"] = query
    except Exception as e:
        logger.warning("[HYBRID] Idea-grounded novelty failed (%s); using precheck novelty", e)
        novelty["scoring_mode"] = novelty.get("scoring_mode", "query_precheck")

    evaluation_metrics = _compute_evaluation_metrics(parsed_dict, query)

    if job_queue:
        job_queue.set_intermediate_result(job_id, "novelty", novelty)

    # Grounding enforcement for hybrid mode (was previously skipped)
    try:
        # Check that source references in the idea are not fabricated
        source_refs = parsed_dict.get("source_references", [])
        known_urls = {s.get("url") for s in ranked if s.get("url")}
        for ref in source_refs:
            ref_url = ref.get("url", "") if isinstance(ref, dict) else ""
            if ref_url and ref_url not in known_urls:
                logger.warning("[HYBRID] Grounding issue: LLM cited unknown URL %s", ref_url)
    except Exception as e:
        logger.warning("[HYBRID] Grounding check error: %s", e)

    # Feasibility estimation (heuristic, no LLM)
    feasibility = estimate_feasibility_module(query, domain.name, ranked, novelty)

    # Persist to DB
    try:
        title = str(parsed_dict.get("title", "Untitled"))[:255]
        problem_statement = str(parsed_dict.get("problem_statement", query))

        tech_stack_list = parsed_dict.get("tech_stack", [])
        if isinstance(tech_stack_list, list):
            tech_stack_str = _build_tech_stack_text(tech_stack_list)
        else:
            tech_stack_str = str(tech_stack_list)[:500]

        idea = ProjectIdea(
            title=title,
            problem_statement=problem_statement,
            problem_statement_json=parsed_dict,
            tech_stack=tech_stack_str,
            tech_stack_json=tech_stack_list,
            domain_id=domain_id,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            is_ai_generated=True,
            is_public=True,
            is_validated=False,
        )
        db.session.add(idea)
        db.session.flush()

        idea.quality_score_cached = idea.quality_score
        idea.novelty_score_cached = round(novelty.get("novelty_score", 0))
        novelty["input_text"] = novelty_input  # Store for rescore parity
        if evaluation_metrics:
            novelty["evaluation"] = evaluation_metrics
        idea.novelty_context = novelty

        # Persist sources
        for src in ranked:
            if isinstance(src, dict):
                db.session.add(
                    IdeaSource(
                        idea_id=idea.id,
                        source_type=src.get("source_type", "unknown"),
                        title=src.get("title", "Untitled"),
                        url=src.get("url", ""),
                        summary=src.get("summary", src.get("relevance_explanation", "")),
                        relevance_tier=src.get("relevance_tier", "supporting"),
                    )
                )

        db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))

        # Persist novelty breakdown for audit trail
        try:
            from backend.core.models import NoveltyBreakdown
            sig = novelty.get("signal_breakdown", {})
            dbg = novelty.get("debug", {})
            nb = NoveltyBreakdown(
                idea_id=idea.id,
                mean_similarity=novelty.get("routing", {}).get("domain_confidence", 0),
                similarity_variance=dbg.get("similarity_variance", 0),
                specificity_score=sig.get("base_score", 0),
                temporal_score=sig.get("maturity_bonus", 0),
                saturation_penalty=sig.get("commodity_penalty", 0),
                base_score=sig.get("base_score", 0),
                bonus_score=sig.get("bonus", 0),
                weighted_score=novelty.get("novelty_score", 0),
                stabilized_score=novelty.get("novelty_score", 0),
                retrieved_sources_count=dbg.get("retrieved_sources", len(ranked)),
                referenced_ideas_count=0,
                domain=domain.name,
                engine=novelty.get("engine", "software"),
                algorithm_version="hybrid_v2",
            )
            db.session.add(nb)
        except Exception as e:
            logger.warning("Failed to persist NoveltyBreakdown: %s", e)

        # Audit trace (2-phase) with retrieval metadata
        active_bias = get_active_bias_profile()

        # Build retrieval audit metadata for reproducibility
        retrieval_audit = {
            "query": query,
            "domain": domain.name,
            "raw_source_count": len(raw_sources) if 'raw_sources' in dir() else len(ranked),
            "filtered_source_count": len(filtered) if 'filtered' in dir() else len(ranked),
            "ranked_source_count": len(ranked),
            "sources_used": [
                {"url": s.get("url"), "source_type": s.get("source_type"), "relevance_tier": s.get("relevance_tier")}
                for s in ranked[:10]
            ],
        }

        trace = GenerationTrace(
            idea_id=idea.id,
            user_id=user_id,
            query=query,
            domain_name=domain.name,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            bias_profile_version=active_bias.get("version", "default"),
            prompt_version="hybrid-v1",
            phase_0_output={"query": query, "domain": domain.name, "feasibility": feasibility, "retrieval_audit": retrieval_audit},
            phase_1_output=analysis,
            phase_2_output=parsed_dict,
            phase_3_output=None,
            phase_4_output=None,
            constraints_active=constraints,
            bias_penalties_applied={"source_penalties": constraints.get("source_penalties", {})}
        )
        db.session.add(trace)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error("[HYBRID] DB error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, f"Failed to save idea: {e}")
        return {"error": "Failed to save idea. Please try again."}

    # Build result
    result = {
        "id": idea.id,
        "title": title,
        "problem_statement": problem_statement,
        "tech_stack": tech_stack_str,
        "domain": domain.name,
        "domain_id": domain_id,
        "novelty_score": novelty.get("novelty_score", 0),
        "novelty_level": novelty.get("novelty_level", ""),
        "novelty_confidence": novelty.get("confidence", "Low"),
        "quality_score": idea.quality_score_cached,
        "evidence_strength": novelty.get("confidence", "Low"),
        "evidence_sources": [
            {"title": s.get("title"), "url": s.get("url"), "source_type": s.get("source_type"),
             "relevance_tier": s.get("relevance_tier", "contextual"),
             "relevance_explanation": s.get("relevance_explanation", "")}
            for s in ranked[:10]
        ],
        "idea": parsed_dict,
        "feasibility": feasibility,
        "novelty_context": novelty,
        "source_count": len(ranked),
        "generation_metadata": {
            "mode": "hybrid",
            "llm_calls": 2,
            "hitl_influenced": bool(constraints.get("source_penalties")),
            "domain_strictness": constraints.get("domain_strictness", 1.0),
            "evaluation_metrics": evaluation_metrics,
        },
    }

    if job_queue:
        if hasattr(trace, "id"):
            job_queue.set_intermediate_result(job_id, "trace_id", str(trace.id))
        job_queue.set_final_result(job_id, result)

    logger.info("[HYBRID] Generation completed: idea_id=%s novelty=%.1f", idea.id, novelty.get("novelty_score", 0))
    return result


# ================================================================
# GCR MODE: Generate -> Critique -> Refine (3-pass pipeline)
# ================================================================
def generate_gcr(
    query: str, domain_id: int, user_id: int, job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    GCR pipeline: real retrieval + novelty, then 3 LLM passes.

    Pass 1: Generate draft idea
    Pass 2: Critique draft idea
    Pass 3: Refine into final idea
    """
    from backend.utils.common import truncate_source_for_prompt, truncate_novelty_gaps

    logger.info("[GCR] Starting 3-pass generation: query='%s'", query[:80])
    job_queue = get_job_queue() if job_id else None

    if job_queue:
        job_queue.set_phase_names(job_id, {
            0: "Retrieving sources",
            1: "Analyzing novelty",
            2: "Drafting idea",
            3: "Critiquing draft",
            4: "Refining & saving",
        })

    # --- Abuse check ---
    try:
        from backend.core.abuse import check_generation_rate, record_abuse_event
        if check_generation_rate(user_id):
            try:
                record_abuse_event(user_id, "generation_blocked", {"query": query[:200]})
            except Exception:
                pass
            return {"error": "rate_limited"}
        try:
            record_abuse_event(user_id, "generation_attempt", {"query": query[:200]})
        except Exception:
            pass
    except Exception:
        logger.exception("Abuse subsystem error; continuing generation")

    # --- Domain lookup ---
    domain = Domain.query.get(domain_id)
    if not domain:
        return {"error": "Invalid domain_id"}

    if job_queue:
        job_queue.update_job_status(job_id, "running", 0, 5)

    guardrail = check_hitl_guardrails(domain_id)
    if guardrail:
        return guardrail

    # =============================================
    # Phase 0  — Retrieve sources (0-30%)
    # =============================================
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 0, 10)

        retrieved = retrieve_sources(query=query, domain=domain.name)
        raw_sources = retrieved.get("sources", []) if retrieved else []
        raw_sources = filter_hallucinated_sources(raw_sources)
        logger.info("[GCR] Retrieved %d raw sources (post-hallucination filter)", len(raw_sources))

        if not raw_sources:
            logger.warning("[GCR] No sources for query='%s'", query[:60])
            return {"error": "No sources found for topic. Please try a different topic."}

        threshold = _get_domain_threshold(domain.name, cap=0.4)
        filtered = _filter_with_fallback(query, raw_sources, threshold)

        ranked = rank_sources(filtered)
        if not ranked:
            return {"error": "Could not rank sources. Please try again."}

        if job_queue:
            job_queue.set_intermediate_result(job_id, "sources", ranked)
            job_queue.update_job_status(job_id, "running", 0, 30)

    except Exception as e:
        logger.error("[GCR] Retrieval error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, f"Retrieval error: {e}")
        return {"error": f"Retrieval error: {e}"}

    # =============================================
    # Phase 1  — Novelty precheck (30-50%)
    # =============================================
    try:
        novelty = analyze_novelty(
            query,
            domain.name,
            preloaded_sources=ranked,
            query_text=query,
        )
        novelty["scoring_mode"] = "query_precheck"
        novelty["input_text"] = query

        if job_queue:
            job_queue.set_intermediate_result(job_id, "novelty", novelty)
            job_queue.update_job_status(job_id, "running", 1, 50)

    except Exception as e:
        logger.error("[GCR] Novelty error: %s", e)
        novelty = {"novelty_score": 50, "confidence": "Low", "insights": {}, "sources": []}

    gate_error = check_evidence_sufficiency(ranked, novelty.get("novelty_score", 0))
    if gate_error:
        return {"error": gate_error}

    # HITL constraints
    try:
        constraints = build_hitl_constraints(domain.name, ranked)
    except Exception:
        constraints = {"source_penalties": {}, "pattern_penalties": [], "domain_strictness": 1.0}

    # Prepare truncated sources for prompt
    top_sources = ranked[: Config.HYBRID_MAX_SOURCES_FOR_PROMPT]
    source_lines = []
    for i, s in enumerate(top_sources):
        source_lines.append(f"[{i}] ({s.get('source_type','?').upper()}) {truncate_source_for_prompt(s)}")
    sources_text = "\n".join(source_lines)

    raw_gaps = novelty.get("gaps", [])
    gap_strings = truncate_novelty_gaps(raw_gaps, max_items=3, max_words=50)
    if not gap_strings:
        for k, v in novelty.get("insights", {}).items():
            gap_strings.append(str(v)[:200])
            if len(gap_strings) >= 3:
                break
    novelty_gaps_text = "\n".join(f"- {g}" for g in gap_strings) if gap_strings else "No specific gaps identified"

    # =============================================
    # Phase 2  — Draft generation (50-70%)
    # =============================================
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 2, 60)

        draft_body = (
            GCR_GENERATOR_PROMPT_TEMPLATE
            .replace("{query}", query)
            .replace("{domain}", domain.name)
            .replace("{novelty}", json.dumps(novelty, default=str))
            .replace("{novelty_gaps}", novelty_gaps_text)
            .replace("{sources}", sources_text)
        )

        draft_idea = generate_json(
            GCR_GENERATOR_SYSTEM + draft_body,
            max_tokens=1000,
            temperature=0.35,
            task_type="generation_gcr_generate",
        )

    except TransientLLMError as e:
        logger.error("[GCR] LLM transient error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, str(e) or "LLM transient failure")
        return {"error": str(e) or "LLM transient failure", "transient": True}
    except Exception as e:
        logger.error("[GCR] Draft generation failed: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, str(e) or "LLM generation failed")
        return {"error": str(e) or "LLM generation failed"}

    # =============================================
    # Phase 3  — Critique (70-80%)
    # =============================================
    critique = {}
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 3, 72)

        critic_body = (
            GCR_CRITIC_PROMPT_TEMPLATE
            .replace("{idea}", json.dumps(draft_idea, default=str))
            .replace("{novelty}", json.dumps(novelty, default=str))
            .replace("{constraints}", json.dumps(constraints, default=str))
            .replace("{sources}", sources_text)
        )

        critique = generate_json(
            GCR_CRITIC_SYSTEM + critic_body,
            max_tokens=600,
            temperature=0.2,
            task_type="generation_gcr_critic",
        )
    except Exception as e:
        logger.warning("[GCR] Critique failed: %s", e)
        critique = {"blocking_issues": ["Critique failed"], "confidence": "low", "confidence_reason": str(e)[:120]}

    # =============================================
    # Phase 4  — Refine & save (80-100%)
    # =============================================
    try:
        if job_queue:
            job_queue.update_job_status(job_id, "running", 4, 85)

        refine_body = (
            GCR_REFINER_PROMPT_TEMPLATE
            .replace("{idea}", json.dumps(draft_idea, default=str))
            .replace("{critique}", json.dumps(critique, default=str))
            .replace("{novelty}", json.dumps(novelty, default=str))
            .replace("{sources}", sources_text)
        )

        refined_idea = generate_json(
            GCR_REFINER_SYSTEM + refine_body,
            max_tokens=1100,
            temperature=0.25,
            task_type="generation_gcr_refine",
        )

    except Exception as e:
        logger.warning("[GCR] Refiner failed: %s", e)
        refined_idea = draft_idea if isinstance(draft_idea, dict) else {}

    if not isinstance(refined_idea, dict):
        refined_idea = draft_idea if isinstance(draft_idea, dict) else {}

    # Validate via relaxed schema
    try:
        parsed = validate_hybrid_idea(refined_idea)
        parsed_dict = parsed.model_dump()
    except Exception as e:
        logger.warning("[GCR] Schema validation partial fail: %s", e)
        parsed_dict = refined_idea if isinstance(refined_idea, dict) else {}
        if "title" not in parsed_dict:
            parsed_dict["title"] = f"Idea: {query[:80]}"
        if "problem_statement" not in parsed_dict:
            parsed_dict["problem_statement"] = query

    # Pattern rejection
    pattern_check = is_rejected_pattern(parsed_dict, constraints)
    if pattern_check:
        return pattern_check

    # Final novelty score (idea-grounded)
    novelty_input = _select_novelty_text_for_idea(parsed_dict, query)
    try:
        novelty = analyze_novelty(
            novelty_input,
            domain.name,
            preloaded_sources=ranked,
            query_text=query,
        )
        novelty["scoring_mode"] = "generated_idea"
        novelty["input_text"] = novelty_input
        novelty["query_text"] = query
    except Exception as e:
        logger.warning("[GCR] Idea-grounded novelty failed (%s); using precheck novelty", e)
        novelty["scoring_mode"] = novelty.get("scoring_mode", "query_precheck")

    evaluation_metrics = _compute_evaluation_metrics(parsed_dict, query)
    if evaluation_metrics:
        novelty["evaluation"] = evaluation_metrics

    if job_queue:
        job_queue.set_intermediate_result(job_id, "novelty", novelty)

    # Grounding sanity check
    try:
        source_refs = parsed_dict.get("source_references", [])
        known_urls = {s.get("url") for s in ranked if s.get("url")}
        for ref in source_refs:
            ref_url = ref.get("url", "") if isinstance(ref, dict) else ""
            if ref_url and ref_url not in known_urls:
                logger.warning("[GCR] Grounding issue: LLM cited unknown URL %s", ref_url)
    except Exception as e:
        logger.warning("[GCR] Grounding check error: %s", e)

    feasibility = estimate_feasibility_module(query, domain.name, ranked, novelty)

    # Persist to DB
    try:
        title = str(parsed_dict.get("title", "Untitled"))[:255]
        problem_statement = str(parsed_dict.get("problem_statement", query))

        tech_stack_list = parsed_dict.get("tech_stack", [])
        if isinstance(tech_stack_list, list):
            tech_stack_str = _build_tech_stack_text(tech_stack_list)
        else:
            tech_stack_str = str(tech_stack_list)[:500]

        idea = ProjectIdea(
            title=title,
            problem_statement=problem_statement,
            problem_statement_json=parsed_dict,
            tech_stack=tech_stack_str,
            tech_stack_json=tech_stack_list if isinstance(tech_stack_list, list) else [],
            domain_id=domain_id,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            is_ai_generated=True,
            is_public=True,
            is_validated=False,
        )
        db.session.add(idea)
        db.session.flush()

        idea.quality_score_cached = idea.quality_score
        idea.novelty_score_cached = round(novelty.get("novelty_score", 0))
        novelty["input_text"] = novelty_input
        idea.novelty_context = novelty

        for src in ranked:
            if isinstance(src, dict):
                db.session.add(
                    IdeaSource(
                        idea_id=idea.id,
                        source_type=src.get("source_type", "unknown"),
                        title=src.get("title", "Untitled"),
                        url=src.get("url", ""),
                        summary=src.get("summary", src.get("relevance_explanation", "")),
                        relevance_tier=src.get("relevance_tier", "supporting"),
                    )
                )

        db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))

        # Persist novelty breakdown for audit trail
        try:
            from backend.core.models import NoveltyBreakdown
            sig = novelty.get("signal_breakdown", {})
            dbg = novelty.get("debug", {})
            nb = NoveltyBreakdown(
                idea_id=idea.id,
                mean_similarity=novelty.get("routing", {}).get("domain_confidence", 0),
                similarity_variance=dbg.get("similarity_variance", 0),
                specificity_score=sig.get("base_score", 0),
                temporal_score=sig.get("maturity_bonus", 0),
                saturation_penalty=sig.get("commodity_penalty", 0),
                base_score=sig.get("base_score", 0),
                bonus_score=sig.get("bonus", 0),
                weighted_score=novelty.get("novelty_score", 0),
                stabilized_score=novelty.get("novelty_score", 0),
                retrieved_sources_count=dbg.get("retrieved_sources", len(ranked)),
                referenced_ideas_count=0,
                domain=domain.name,
                engine=novelty.get("engine", "software"),
                algorithm_version="gcr_v1",
            )
            db.session.add(nb)
        except Exception as e:
            logger.warning("Failed to persist NoveltyBreakdown: %s", e)

        # Audit trace (GCR) with retrieval metadata
        active_bias = get_active_bias_profile()
        retrieval_audit = {
            "query": query,
            "domain": domain.name,
            "raw_source_count": len(raw_sources) if 'raw_sources' in dir() else len(ranked),
            "filtered_source_count": len(filtered) if 'filtered' in dir() else len(ranked),
            "ranked_source_count": len(ranked),
            "sources_used": [
                {"url": s.get("url"), "source_type": s.get("source_type"), "relevance_tier": s.get("relevance_tier")}
                for s in ranked[:10]
            ],
        }

        trace = GenerationTrace(
            idea_id=idea.id,
            user_id=user_id,
            query=query,
            domain_name=domain.name,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            bias_profile_version=active_bias.get("version", "default"),
            prompt_version="gcr-v1",
            phase_0_output={"query": query, "domain": domain.name, "feasibility": feasibility, "retrieval_audit": retrieval_audit},
            phase_1_output=draft_idea,
            phase_2_output=critique,
            phase_3_output=parsed_dict,
            phase_4_output=None,
            constraints_active=constraints,
            bias_penalties_applied={"source_penalties": constraints.get("source_penalties", {})}
        )
        db.session.add(trace)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error("[GCR] DB error: %s", e)
        if job_queue:
            job_queue.set_job_error(job_id, f"Failed to save idea: {e}")
        return {"error": "Failed to save idea. Please try again."}

    result = {
        "id": idea.id,
        "title": title,
        "problem_statement": problem_statement,
        "tech_stack": tech_stack_str,
        "domain": domain.name,
        "domain_id": domain_id,
        "novelty_score": novelty.get("novelty_score", 0),
        "novelty_level": novelty.get("novelty_level", ""),
        "novelty_confidence": novelty.get("confidence", "Low"),
        "quality_score": idea.quality_score_cached,
        "evidence_strength": novelty.get("confidence", "Low"),
        "evidence_sources": [
            {"title": s.get("title"), "url": s.get("url"), "source_type": s.get("source_type"),
             "relevance_tier": s.get("relevance_tier", "contextual"),
             "relevance_explanation": s.get("relevance_explanation", "")}
            for s in ranked[:10]
        ],
        "idea": parsed_dict,
        "feasibility": feasibility,
        "novelty_context": novelty,
        "source_count": len(ranked),
        "generation_metadata": {
            "mode": "gcr",
            "llm_calls": 3,
            "hitl_influenced": bool(constraints.get("source_penalties")),
            "domain_strictness": constraints.get("domain_strictness", 1.0),
            "evaluation_metrics": evaluation_metrics,
            "critic_confidence": critique.get("confidence") if isinstance(critique, dict) else None,
        },
    }

    if job_queue:
        if hasattr(trace, "id"):
            job_queue.set_intermediate_result(job_id, "trace_id", str(trace.id))
        job_queue.set_final_result(job_id, result)

    logger.info("[GCR] Generation completed: idea_id=%s novelty=%.1f", idea.id, novelty.get("novelty_score", 0))
    return result


# DEMO MODE: Direct LLM generation (no retrieval, no multi-pass)
def generate_direct_to_llm(
    query: str, domain_id: int, user_id: int, job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    DEMO MODE ONLY: Direct idea generation without retrieval or multi-pass pipeline.
    Sends user query directly to LLM for fast idea generation.
    
    Args:
        query: User's idea query
        domain_id: Domain ID
        user_id: User ID
        job_id: Optional job ID for progress tracking
        
    Returns:
        Complete idea dictionary with problem_statement, tech_stack, modules, etc.
    """
    logger.info(f"[DEMO MODE] Generating direct idea without pipeline: query='{query[:50]}...'")
    
    # Get domain name
    domain = None
    if domain_id:
        domain_obj = Domain.query.get(domain_id)
        domain = domain_obj.name if domain_obj else "General"
    else:
        domain = "General"
    
    # Update job status if tracking
    if job_id:
        jq = get_job_queue()
        jq.update_job_status(job_id, "running", 0, 5)
    
    try:
        # Build the prompt (system + user combined, like multi-pass pipeline)
        prompt_combined = DIRECT_GENERATION_SYSTEM + DIRECT_GENERATION_PROMPT_TEMPLATE.format(
            query=query,
            domain=domain
        )
        
        # Call LLM directly (matching the pattern from PASS1-4)
        logger.info(f"[DEMO MODE] Calling LLM with direct generation prompt")
        
        result = generate_json(
            prompt_combined,
            temperature=0.7,
            max_tokens=2000,
            task_type="generation_synthesis",
        )
        
        logger.info(f"[DEMO MODE] LLM returned valid JSON for direct generation")
        
        # Parse the result
        idea_data = result
        
        # Build a mock novelty/evidence object for compatibility
        novelty = {
            "novelty_score": 60.0,  # Fixed demo score
            "novelty_breakdown": {
                "technical_novelty": 65,
                "process_novelty": 60,
                "business_novelty": 55
            }
        }
        
        # Create minimal sources list (empty, since we didn't retrieve)
        sources = []
        
        # Ensure required fields exist
        if "problem_statement" not in idea_data:
            idea_data["problem_statement"] = f"Innovation: {query}"
        if "tech_stack" not in idea_data:
            idea_data["tech_stack"] = []
        if "modules" not in idea_data:
            idea_data["modules"] = []
        if "key_innovations" not in idea_data:
            idea_data["key_innovations"] = ["Direct LLM-generated innovation"]
        
        # Build output structure matching the standard generate_idea response
        output = {
            "id": None,  # Will be generated by DB
            "user_id": user_id,
            "domain_id": domain_id,
            "query": query,
            "status": "completed",
            "problem_statement": idea_data.get("problem_statement"),
            "problem_context": idea_data.get("problem_context", ""),
            "proposed_contribution": {
                "title": idea_data.get("problem_statement", "")[:100],
                "description": idea_data.get("problem_context", ""),
                "evidence_basis": []  # No sources in demo mode
            },
            "tech_stack": idea_data.get("tech_stack", []),
            "modules": idea_data.get("modules", []),
            "key_innovations": idea_data.get("key_innovations", []),
            "implementation_complexity": idea_data.get("implementation_complexity", "medium"),
            "estimated_timeline_weeks": idea_data.get("estimated_timeline_weeks", 12),
            "team_size_recommendation": idea_data.get("team_size_recommendation", 3),
            "success_metrics": idea_data.get("success_metrics", []),
            "potential_risks": idea_data.get("potential_risks", []),
            "novelty_score": novelty["novelty_score"],
            "novelty_breakdown": novelty["novelty_breakdown"],
            "evidence_strength": "demo",  # Mark as demo-generated
            "evidence_sources": [],
            "evidence_gap": "None (demo mode)",
            "hallucination_risk_level": "low",
            "novelty_confidence": "medium",
            "feasibility": {
                "score": 65,
                "complexity": idea_data.get("implementation_complexity", "medium"),
                "estimated_weeks": idea_data.get("estimated_timeline_weeks", 12),
                "team_size": idea_data.get("team_size_recommendation", 3),
                "uncertainty": 0.4
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "source_count": 0
        }
        
        # Update job if tracking - mark complete
        if job_id:
            jq = get_job_queue()
            jq.update_job_status(job_id, "running", 4, 100)
            # Store intermediate novelty for polling
            jq.set_intermediate_result(job_id, "novelty", novelty)
        
        logger.info(f"[DEMO MODE] Direct idea generation completed successfully")
        return output
        
    except TransientLLMError as e:
        logger.error(f"[DEMO MODE] LLM error: {e}")
        error_msg = f"Failed to generate idea: {str(e)}"
        if job_id:
            jq = get_job_queue()
            jq.set_job_error(job_id, error_msg)
        return {"error": error_msg}
    
    except Exception as e:
        logger.exception(f"[DEMO MODE] Unexpected error in direct generation")
        error_msg = f"Generation failed: {str(e)}"
        if job_id:
            jq = get_job_queue()
            jq.set_job_error(job_id, error_msg)
        return {"error": error_msg}


# Main entry: generate_idea
def generate_idea(query: str, domain_id: int, user_id: int, job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an idea based on query, domain, and user.
    Optionally tracks progress in job queue if job_id is provided.
    
    Args:
        query: The idea subject/query
        domain_id: Domain ID to generate for
        user_id: User requesting generation
        job_id: Optional job ID for async tracking
        
    Returns:
        Dict with generated idea or error message
    """
    # DEMO MODE: Skip entire pipeline and use direct LLM generation
    if Config.DEMO_MODE:
        logger.info(f"[DEMO MODE ENABLED] Using direct LLM generation, skipping full pipeline")
        return generate_direct_to_llm(query, domain_id, user_id, job_id)

    # GCR MODE: 3-pass Generate -> Critique -> Refine pipeline
    if Config.GCR_MODE:
        logger.info("[GCR MODE ENABLED] Using 3-pass GCR generation pipeline")
        return generate_gcr(query, domain_id, user_id, job_id)

    # HYBRID MODE: 2-pass pipeline (real retrieval + real novelty + 2 LLM calls)
    if Config.HYBRID_MODE:
        logger.info("[HYBRID MODE ENABLED] Using 2-pass generation pipeline")
        return generate_hybrid(query, domain_id, user_id, job_id)
    
    job_queue = get_job_queue() if job_id else None
    # Basic abuse check: ensure user is not exceeding generation attempts
    try:
        from backend.core.abuse import check_generation_rate, record_abuse_event
        if check_generation_rate(user_id):
            # Record the blocked attempt for auditing
            try:
                record_abuse_event(user_id, "generation_blocked", {"query": query[:200]})
            except Exception:
                pass
            return {"error": "rate_limited"}
        else:
            # Record this attempt
            try:
                record_abuse_event(user_id, "generation_attempt", {"query": query[:200]})
            except Exception:
                pass

    except Exception:
        # If abuse subsystem fails, allow generation but log
        logger.exception("Abuse subsystem error; continuing generation")

    try:
        domain = Domain.query.get(domain_id)
        if not domain:
            return {"error": "Invalid domain_id"}

        # Update job status: domain lookup complete
        if job_queue:
            job_queue.update_job_status(job_id, "running", 1, 10)

        guardrail = check_hitl_guardrails(domain_id)
        if guardrail:
            return guardrail

        retrieved = retrieve_sources(query=query, domain=domain.name)
        
        # Log retrieval results for debugging
        source_count = len(retrieved.get("sources", [])) if retrieved else 0
        logger.info(f"Retrieval complete: {source_count} sources for domain={domain.name}, query='{query[:50]}...'")
        
        # Update job status: retrieval complete
        if job_queue:
            job_queue.set_intermediate_result(job_id, "sources", retrieved.get("sources", []))
            job_queue.update_job_status(job_id, "running", 1, 20)
        # Check for empty sources - must check both missing key and empty list
        if not retrieved or 'sources' not in retrieved or not retrieved.get("sources"):
            logger.warning(f"No sources retrieved for query='{query[:50]}...' domain={domain.name}")
            return {"error": "No sources found for topic. Please try a different topic."}
        
        # Use domain-specific similarity threshold, or fall back to unfiltered sources
        threshold = _get_domain_threshold(domain.name, cap=0.4)
        
        raw_sources = retrieved.get("sources", [])
        # Filter out sources previously flagged as hallucinated
        raw_sources = filter_hallucinated_sources(raw_sources)
        
        # In demo mode, skip semantic filtering for speed
        if Config.DEMO_MODE:
            logger.info(f"[DEMO MODE] Skipping semantic filter, using all {len(raw_sources)} retrieved sources")
            filtered = raw_sources
        else:
            filtered = _filter_with_fallback(query, raw_sources, threshold)

        ranked = rank_sources(filtered)
        logger.info(f"Ranking complete: {len(ranked)} sources ranked")
        
        if not ranked:
            logger.error(f"Ranking returned empty for {len(filtered)} filtered sources")
            return {"error": "Could not rank sources. Please try again."}


        # In demo mode, mock novelty analysis for speed
        if Config.DEMO_MODE:
            logger.info(f"[DEMO MODE] Skipping novelty analysis, using mock novelty score")
            novelty = {
                "novelty_score": 60,
                "novelty_level": "moderate",
                "confidence": "Low",
                "signals": {
                    "similarity": 0.5,
                    "specificity": 0.6,
                    "temporal": 0.3,
                    "saturation": 0.7
                },
                "sources_count": len(ranked),
                "confidence_hint": "Low (mocked for demo)"
            }
        else:
            novelty = analyze_novelty(
                query,
                domain.name,
                preloaded_sources=ranked,
                query_text=query,
            )
            novelty["input_text"] = query
            novelty["scoring_mode"] = "query_precheck"

        # Update job status: novelty analysis complete
        if job_queue:
            job_queue.set_intermediate_result(job_id, "novelty", novelty)
            job_queue.update_job_status(job_id, "running", 2, 30)

        gate_error = check_evidence_sufficiency(ranked, novelty.get("novelty_score", 0))
        if gate_error:
            # In demo mode, skip the gate error for speed
            if Config.DEMO_MODE:
                logger.info(f"[DEMO MODE] Bypassing evidence gate error: {gate_error}")
            else:
                return {"error": gate_error}
    except Exception as e:
        logger.error(f"Error in generate_idea retrieval phase: {e}")
        if job_queue:
            job_queue.set_job_error(job_id, f"Retrieval error: {str(e)}", None)
        return {"error": f"Retrieval error: {str(e)}"}

    # Build HITL constraints
    try:
        constraints = build_hitl_constraints(domain.name, ranked)
    except Exception as e:
        logger.warning(f"HITL constraint building failed: {e}. Using empty constraints.")
        constraints = {"source_penalties": {}, "pattern_penalties": [], "domain_strictness": 1.0}

    # Wrap LLM generation in try-except
    try:
        # Update job status: LLM generation phase starting
        if job_queue:
            job_queue.update_job_status(job_id, "running", 3, 50)
        
        generation_output = multi_pass_llm_generate(query, domain.name, ranked, novelty, constraints)
        final = generation_output["final"]
        phase_0 = generation_output["phase_0"]
        # Augment phase_0 with feasibility bounds
        try:
            phase_0["feasibility"] = estimate_feasibility_module(query, domain.name, ranked, novelty)
        except Exception:
            phase_0["feasibility"] = None
        phase_1 = generation_output["phase_1"]
        phase_2 = generation_output["phase_2"]
        phase_3 = generation_output["phase_3"]
    except TransientLLMError as e:
        logger.error(f"Transient LLM error: {e}")
        if job_queue:
            job_queue.set_job_error(job_id, str(e) if str(e) else "LLM transient failure", None)
        trace_id = getattr(e, "trace_id", None)
        out = {"error": str(e) if str(e) else "LLM transient failure", "transient": True}
        if trace_id:
            out["trace_id"] = trace_id
        return out
    except RuntimeError as e:
        logger.error(f"LLM generation failed: {e}")
        if job_queue:
            job_queue.set_job_error(job_id, str(e) if str(e) else "LLM generation failed", None)
        return {"error": str(e) if str(e) else "LLM generation failed. Please try again."}
    except ValueError as e:
        logger.error(f"LLM validation failed: {e}")
        if job_queue:
            job_queue.set_job_error(job_id, f"Validation error: {str(e)}", None)
        return {"error": f"Validation error: {str(e)}" if str(e) else "Validation failed. Please try again."}
    except Exception as e:
        logger.exception("Unexpected error in LLM generation")
        if job_queue:
            import traceback
            job_queue.set_job_error(job_id, f"Generation failed unexpectedly: {str(e)}", traceback.format_exc())
        return {"error": f"Generation failed unexpectedly: {str(e)}"}

    try:
        parsed = validate_generated_idea(final).model_dump()
    except Exception as e:
        logger.exception("Schema validation failed")
        return {"error": f"Response validation failed: {str(e)}"}

    pattern_check = is_rejected_pattern(parsed, constraints)
    if pattern_check:
        return pattern_check

    novelty_input = _select_novelty_text_for_idea(parsed, query)
    try:
        novelty = analyze_novelty(
            novelty_input,
            domain.name,
            preloaded_sources=ranked,
            query_text=query,
        )
        novelty["input_text"] = novelty_input
        novelty["query_text"] = query
        novelty["scoring_mode"] = "generated_idea"
    except Exception as e:
        logger.warning("Final novelty scoring failed; using precheck score: %s", e)

    evaluation_metrics = _compute_evaluation_metrics(parsed, query)
    if evaluation_metrics:
        novelty["evaluation"] = evaluation_metrics

    # Persist idea + sources (with transaction protection)
    try:
        # Build title safely
        title = parsed.get("title", "Untitled Idea")[:255]
        
        # Build problem statement safely
        problem_form = parsed.get("problem_formulation", {})
        problem_statement = problem_form.get("context", "No problem statement provided")
        
        # Build tech stack safely — Pass 4 now returns array format
        tech_choices = parsed.get("tech_stack", parsed.get("technology_choices", []))
        if isinstance(tech_choices, list):
            tech_stack = _build_tech_stack_text(tech_choices)
            tech_stack_json = tech_choices
        elif isinstance(tech_choices, dict):
            # Legacy dict format: {"Technology": {"reason": ...}}
            tech_stack_json = [
                {"component": "Technology", "technologies": [k], "rationale": v.get("reason", "") if isinstance(v, dict) else str(v)}
                for k, v in tech_choices.items()
            ]
            tech_stack = _build_tech_stack_text(tech_stack_json)
        else:
            tech_stack = "Not specified"
            tech_stack_json = []
        
        idea = ProjectIdea(
            title=title,
            problem_statement=problem_statement,
            problem_statement_json=problem_form,
            tech_stack=tech_stack,
            tech_stack_json=tech_stack_json,
            domain_id=domain_id,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            is_ai_generated=True,
            is_public=True,
            is_validated=False,
        )

        db.session.add(idea)
        db.session.flush()

        idea.quality_score_cached = idea.quality_score
        
        # Keep cache score sourced from novelty analyzer for consistency.
        novelty_pos = parsed.get("novelty_positioning", {})
        fallback_novelty = novelty_pos.get("novelty_score", 0) if isinstance(novelty_pos, dict) else 0
        idea.novelty_score_cached = round(novelty.get("novelty_score", fallback_novelty))

        idea.novelty_context = novelty

        # Add sources
        evidence_sources = parsed.get("evidence_sources", [])
        for src in evidence_sources:
            if isinstance(src, dict):
                db.session.add(
                    IdeaSource(
                        idea_id=idea.id,
                        source_type=src.get("source_type", "unknown"),
                        title=src.get("title", "Untitled"),
                        url=src.get("url", ""),
                        summary=src.get("used_for", ""),
                        relevance_tier=src.get("relevance_tier", "supporting"),
                    )
                )

        db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))

        # Persist novelty breakdown for audit trail
        try:
            from backend.core.models import NoveltyBreakdown
            nb = NoveltyBreakdown(
                idea_id=idea.id,
                mean_similarity=0,
                similarity_variance=0,
                base_score=novelty_pos.get("novelty_score", 0) if isinstance(novelty_pos, dict) else 0,
                bonus_score=0,
                weighted_score=idea.novelty_score_cached or 0,
                stabilized_score=idea.novelty_score_cached or 0,
                retrieved_sources_count=len(ranked),
                referenced_ideas_count=0,
                domain=domain.name,
                engine="software",
                algorithm_version="production_v1",
            )
            db.session.add(nb)
        except Exception as e:
            logger.warning("Failed to persist NoveltyBreakdown: %s", e)
        
        # ================================================================
        # CREATE AUDIT TRACE (Phase 0-4 reasoning documented)
        # ================================================================
        active_bias = get_active_bias_profile()

        trace = GenerationTrace(
            idea_id=idea.id,
            user_id=user_id,
            query=query,
            domain_name=domain.name,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            bias_profile_version=active_bias.get("version", "default"),
            prompt_version="v1",
            phase_0_output=phase_0,
            phase_1_output=phase_1,  # Landscape analysis (ideas space)
            phase_2_output=phase_2,  # Problem framing
            phase_3_output=phase_3,  # Evidence validation
            phase_4_output=final,    # Final synthesis
            constraints_active=constraints,
            bias_penalties_applied={"source_penalties": constraints.get("source_penalties", {})}
        )
        db.session.add(trace)
        
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error persisting idea: {e}")
        if job_queue:
            job_queue.set_job_error(job_id, f"Failed to save idea: {str(e)}", None)
        return {"error": "Failed to save idea. Please try again."}

    # Compute metadata
    penalized_sources_count = len([url for url, mult in constraints.get("source_penalties", {}).items() if mult < 1.0])
    parsed_evidence = parsed.get("evidence_sources", []) if isinstance(parsed, dict) else []
    validated_sources = [s for s in parsed_evidence if s.get("url") in constraints.get("source_penalties", {})]
    validated_source_ratio = len(validated_sources) / len(parsed_evidence) if parsed_evidence else 0.0

    result = {
        "idea": parsed,
        "novelty_score": novelty.get(
            "novelty_score",
            parsed.get("novelty_positioning", {}).get("novelty_score", 0),
        ),
        "generation_metadata": {
            "hitl_influenced": True,
            "penalized_sources_count": penalized_sources_count,
            "domain_strictness": constraints.get("domain_strictness", 1.0),
            "validated_source_ratio": validated_source_ratio,
            "evaluation_metrics": evaluation_metrics,
        }
    }
    
    # Store trace_id and mark job as complete
    if job_queue and hasattr(trace, 'id'):
        job_queue.set_intermediate_result(job_id, "trace_id", str(trace.id))
    
    if job_queue:
        job_queue.set_final_result(job_id, result)
    
    return result
