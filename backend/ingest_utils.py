"""
Shared ingestion utilities for both ArXiv and Admin ingestion.
Ensures identical behavior for embedding generation, text preprocessing, and vector storage.
"""
import logging
from backend.app import db
from backend.models import Project, ProjectVector
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def ingest_projects(items, model):
    """
    Shared ingestion function for projects.
    Handles duplicate checking (by title), embedding generation, and storage.
    Text formatting: "Title: {title}. Description: {description or ''}"

    Args:
        items: List of dicts with keys: 'source', 'title', 'description', 'url'
        model: SentenceTransformer model instance

    Returns:
        dict: {'added': int, 'skipped': int, 'failed': int}
    """
    added = 0
    skipped = 0
    failed = 0

    for item in items:
        title = item.get('title', '').strip()
        description = item.get('description', '').strip()
        source = item.get('source', '')
        url = item.get('url', '')

        if not title:
            failed += 1
            logger.warning("Skipping item with empty title")
            continue

        # Check for duplicate by title (unified check for both sources)
        existing = Project.query.filter_by(title=title).first()
        if existing:
            skipped += 1
            continue

        try:
            # Create project
            project = Project(source=source, title=title, description=description, url=url)
            db.session.add(project)
            db.session.flush()

            # Generate embedding with identical text formatting
            text = f"Title: {title}. Description: {description or ''}"
            embedding = model.encode(text)

            # Create project vector
            project_vector = ProjectVector(project_id=project.id, embedding=embedding.tolist())
            db.session.add(project_vector)

            db.session.commit()
            added += 1

        except IntegrityError:
            db.session.rollback()
            skipped += 1
        except Exception as e:
            db.session.rollback()
            failed += 1
            logger.error("Failed to ingest project '%s': %s", title, e)

    logger.info("Ingestion completed: added=%d, skipped=%d, failed=%d", added, skipped, failed)
    return {'added': added, 'skipped': skipped, 'failed': failed}
