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

    if not description or len(description) < 10:
        return jsonify({"error": "Description too short (minimum 10 characters)"}), 400

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
        "speculative": result["speculative"],
        "evidence_score": result["evidence_score"],

        "engine": result["engine"],
        "domain_intent": intent,
        "intent_confidence": intent_confidence,

        "trace_id": result.get("trace_id"),
        "insights": {},
        "debug": result.get("debug"),
    }), 200
