from flask import Blueprint, request, jsonify
from backend.auth import jwt_required
from backend.config import Config
from backend.embeddings import get_embedding_model
from backend.ingest_utils import ingest_projects
import logging

logger = logging.getLogger(__name__)

ingest_bp = Blueprint('ingest', __name__, url_prefix='/api/admin')

@ingest_bp.route('/ingest', methods=['POST'])
@jwt_required(required_role="admin")
def ingest_projects_endpoint():
    return jsonify({
        "error": "Legacy ingestion deprecated. Live retrieval will replace this."
    }), 410
