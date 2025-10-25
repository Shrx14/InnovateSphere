"""Recompute and restore missing pgvector embeddings for ProjectVector rows.

This script loads the embedding model (same as ingest.py), finds ProjectVector
rows where the new pgvector `embedding` is NULL, recomputes the embedding from
the associated Project title+description, and writes the vector back as a
Python list (pgvector adapter will accept this).

Run from the `backend` folder with the project's virtualenv active:
    python restore_embeddings.py

This is safe to run multiple times; rows that already have embeddings are skipped.
"""
import os
from sentence_transformers import SentenceTransformer

from app import app, db
from models import Project, ProjectVector

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')


def main():
    print('Loading embedding model:', EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)
    print('Model loaded.')

    updated = 0
    skipped = 0
    with app.app_context():
        # find vectors where embedding is NULL
        rows = ProjectVector.query.join(Project).filter(ProjectVector.embedding == None).all()
        total = len(rows)
        print(f'Found {total} project vectors with missing embeddings.')

        for pv in rows:
            proj = pv.project
            if not proj:
                print(f'Warning: no project for vector id={pv.id}, skipping')
                skipped += 1
                continue

            text = f"Title: {proj.title}. Description: {proj.description or ''}"
            try:
                emb = model.encode(text)
                # ensure native Python floats (tolist() does that)
                pv.embedding = emb.tolist()
                db.session.add(pv)
                db.session.commit()
                updated += 1
                if updated % 25 == 0:
                    print(f'Updated {updated}/{total} embeddings...')
            except Exception as e:
                db.session.rollback()
                print(f'Failed to update project_id={pv.project_id}:', e)
                skipped += 1

    print(f'Done. Updated: {updated}, Skipped/Failed: {skipped}, Total missing: {total}')


if __name__ == '__main__':
    main()
