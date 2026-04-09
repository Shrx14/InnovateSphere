"""
Novelty analysis endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from backend.novelty.router import route_engine
from backend.novelty.normalization import normalize_score
from backend.novelty.utils.calibration import compute_evidence_score, apply_evidence_constraints


novelty_bp = Blueprint("novelty", __name__)


@novelty_bp.route("/api/novelty/analyze", methods=["POST"])
@jwt_required()
def analyze_novelty():
    payload = request.get_json() or {}

    description = payload.get("description", "").strip()
    domain = payload.get("domain", "generic")

    if not description:
        return jsonify({"error": "Description required"}), 400

    if len(description) > 5000:
        return jsonify({"error": "Description too long (maximum 5000 characters)"}), 400

    engine, intent, intent_confidence, problem_class, problem_class_confidence = route_engine(description, override_domain=domain)

    result = engine.analyze(
        description,
        domain,
        problem_class=problem_class,
        query_text=description,
    )

    # Pass sources to evidence score computation for relevance-tier weighting
    evidence = compute_evidence_score(result.get("debug", {}), intent_confidence, sources=result.get("sources", []))

    # Pass sources to constraint enforcement for domain-only fallback penalty
    result = apply_evidence_constraints(result, evidence, sources=result.get("sources", []))

    normalized_score = normalize_score(result["novelty_score"], result.get("engine", "generic"))
    normalized_score = min(normalized_score, result["novelty_score"])

    return jsonify({
        "novelty_score": normalized_score,
        "novelty_level": result["novelty_level"],
        "confidence": result["confidence"],
        "speculative": result.get("speculative"),
        "evidence_score": result.get("evidence_score"),
        "evidence_breakdown": result.get("evidence_breakdown", {"supporting": 0, "contextual": 0, "peripheral": 0}),

        "similar_projects": result.get("similar_projects", []),

        "engine": result["engine"],
        "domain_intent": intent,
        "intent_confidence": intent_confidence,
        "problem_class": problem_class,
        "problem_class_confidence": problem_class_confidence,

        "trace_id": result.get("trace_id"),
        "insights": result.get("insights", {}),
        "sources": result.get("sources", []),
        "debug": result.get("debug"),
    }), 200


# Legacy /api/check_novelty alias is handled by platform_bp in platform.py
