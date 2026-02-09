"""
Novelty analysis endpoints
"""
from flask import Blueprint, request, jsonify
# novelty endpoints are public-facing (no auth required)

from backend.novelty.router import route_engine
from backend.novelty.normalization import normalize_score
from backend.novelty.utils.calibration import compute_evidence_score, apply_evidence_constraints


novelty_bp = Blueprint("novelty", __name__)


@novelty_bp.route("/api/novelty/analyze", methods=["POST"])
def analyze_novelty():
    payload = request.get_json() or {}

    description = payload.get("description", "").strip()
    domain = payload.get("domain", "generic")

    if not description:
        return jsonify({"error": "Description required"}), 400

    if len(description) > 5000:
        return jsonify({"error": "Description too long (maximum 5000 characters)"}), 400

    engine, intent, intent_confidence = route_engine(description)

    result = engine.analyze(description, domain)

    evidence = compute_evidence_score(result.get("debug", {}), intent_confidence)

    result = apply_evidence_constraints(result, evidence)

    normalized_score = normalize_score(result["novelty_score"], result.get("engine", "generic"))
    normalized_score = min(normalized_score, result["novelty_score"])

    return jsonify({
        "novelty_score": normalized_score,
        "novelty_level": result["novelty_level"],
        "confidence": result["confidence"],
        "speculative": result.get("speculative"),
        "evidence_score": result.get("evidence_score"),

        "similar_projects": result.get("similar_projects", []),

        "engine": result["engine"],
        "domain_intent": intent,
        "intent_confidence": intent_confidence,

        "trace_id": result.get("trace_id"),
        "insights": result.get("insights", {}),
        "sources": result.get("sources", []),
        "debug": result.get("debug"),
    }), 200


# Backwards-compatible alias used by older clients/tests
@novelty_bp.route("/api/check_novelty", methods=["POST"])
def check_novelty_alias():
    # Reuse the analyze_novelty implementation
    return analyze_novelty()
