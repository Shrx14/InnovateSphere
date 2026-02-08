"""
Platform-level endpoints (pipeline version, legacy routes)
"""
from flask import Blueprint, jsonify
from backend.ai.registry import get_active_ai_pipeline_version
from backend.api.routes.novelty import analyze_novelty

platform_bp = Blueprint("platform", __name__)


@platform_bp.route("/api/check_novelty", methods=["POST"])
def legacy_novelty():
    # Forward legacy route to the new novelty analyze endpoint for backward compatibility
    return analyze_novelty()


@platform_bp.route("/api/generate-idea", methods=["POST"])
def legacy_generation():
    return jsonify({"error": "Legacy AI pipeline deprecated"}), 410


@platform_bp.route("/api/ai/pipeline-version", methods=["GET"])
def pipeline_version():
    return jsonify({"version": get_active_ai_pipeline_version()}), 200
