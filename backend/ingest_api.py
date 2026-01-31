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
    """
    Admin-only endpoint to ingest new project data and generate embeddings.
    Now uses shared ingestion utility for consistency with ArXiv ingestion.
    """
    data = request.get_json() or {}

    # Validate payload
    projects = data.get('projects', [])
    if not projects or not isinstance(projects, list):
        return jsonify({'error': 'projects must be a non-empty list'}), 400

    if len(projects) > Config.INGEST_MAX_PROJECTS:
        return jsonify({'error': f'Maximum {Config.INGEST_MAX_PROJECTS} projects per request'}), 400

    # Prepare items for shared utility
    items = []
    errors = []
    for proj_data in projects:
        title = proj_data.get('title', '').strip()
        description = proj_data.get('description', '').strip()

        if not title:
            errors.append(f"Missing title for project: {title or 'Unknown'}")
            continue

        # Use placeholder URL for admin projects
        url = f"admin://{title.replace(' ', '_')}"

        items.append({
            'source': 'admin',
            'title': title,
            'description': description,
            'url': url
        })

    if not items:
        return jsonify({'error': 'No valid projects to ingest', 'errors': errors}), 400

    # Get embedding model
    model = get_embedding_model()
    if model is None:
        return jsonify({'error': 'Embedding model unavailable'}), 500

    # Use shared ingestion utility
    result = ingest_projects(items, model)

    # Map result keys to match original API response
    response = {
        'inserted': result['added'],
        'skipped': result['skipped'],
        'failed': result['failed'] + len(errors),
        'errors': errors
    }

    logger.info("Admin ingestion completed: inserted=%d, skipped=%d, failed=%d", result['added'], result['skipped'], result['failed'])

    return jsonify(response), 200
