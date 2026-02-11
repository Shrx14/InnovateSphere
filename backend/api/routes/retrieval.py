"""
Retrieval endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.core.models import Domain
from backend.retrieval.orchestrator import retrieve_sources

retrieval_bp = Blueprint("retrieval", __name__)


@retrieval_bp.route("/api/retrieval/sources", methods=["POST"])
@jwt_required()
def retrieval():
    data = request.get_json() or {}
    query = data.get("query")
    domain_id = data.get("domain_id")

    if not query or not domain_id:
        return jsonify({"error": "query and domain_id required"}), 400

    domain = Domain.query.get(domain_id)
    if not domain:
        return jsonify({"error": "Invalid domain_id"}), 400

    try:
        similarity_threshold = float(data.get("similarity_threshold", 0.6))
        if not (0.0 <= similarity_threshold <= 1.0):
            return jsonify({"error": "similarity_threshold must be between 0.0 and 1.0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "similarity_threshold must be a valid number"}), 400

    result = retrieve_sources(
        query=query,
        domain=domain.name,
        semantic_filter=data.get("semantic_filter", False),
        similarity_threshold=similarity_threshold,
    )
    return jsonify(result), 200
