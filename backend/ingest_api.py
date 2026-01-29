from flask import Blueprint, request, jsonify
from backend.auth import jwt_required
from backend.config import Config
from backend.embeddings import get_embedding_model
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models import Project, ProjectVector
    from backend.app import db


logger = logging.getLogger(__name__)

ingest_bp = Blueprint('ingest', __name__, url_prefix='/api/admin')

@ingest_bp.route('/ingest', methods=['POST'])
@jwt_required(required_role="admin")
def ingest_projects():
    """
    Admin-only endpoint to ingest new project data and generate embeddings.
    """
    data = request.get_json() or {}

    # Validate payload
    projects = data.get('projects', [])
    if not projects or not isinstance(projects, list):
        return jsonify({'error': 'projects must be a non-empty list'}), 400

    if len(projects) > Config.INGEST_MAX_PROJECTS:
        return jsonify({'error': f'Maximum {Config.INGEST_MAX_PROJECTS} projects per request'}), 400

    inserted = 0
    skipped = 0
    failed = 0
    errors = []

    for proj_data in projects:
        title = proj_data.get('title', '').strip()
        description = proj_data.get('description', '').strip()
        domain = proj_data.get('domain', '').strip()

        if not title or not description:
            failed += 1
            errors.append(f"Missing title or description for project: {title or 'Unknown'}")
            continue

        # Check for duplicate title
        existing = Project.query.filter_by(title=title).first()
        if existing:
            skipped += 1
            continue

        # Start transaction for this project
        try:
            # Create project
            project = Project(
                source='admin',
                title=title,
                description=description,
                url=f"admin://{title.replace(' ', '_')}"  # Placeholder URL
            )
            db.session.add(project)
            db.session.flush()  # Get project.id

            # Generate embedding
            model = get_embedding_model()
            if model is None:
                raise Exception("Embedding model unavailable")

            embedding = model.encode(f"{title} {description}")
            if len(embedding) != Config.EMBEDDING_DIM:
                raise Exception(f"Embedding dimension mismatch: {len(embedding)} != {Config.EMBEDDING_DIM}")

            # Create project vector
            project_vector = ProjectVector(
                project_id=project.id,
                embedding=list(map(float, embedding))
            )
            db.session.add(project_vector)

            db.session.commit()
            inserted += 1

        except Exception as e:
            db.session.rollback()
            failed += 1
            errors.append(f"Failed to ingest project '{title}': {str(e)}")
            logger.error("Ingestion failed for project '%s': %s", title, e)

    logger.info("Ingestion completed: inserted=%d, skipped=%d, failed=%d", inserted, skipped, failed)

    return jsonify({
        'inserted': inserted,
        'skipped': skipped,
        'failed': failed,
        'errors': errors
    }), 200
