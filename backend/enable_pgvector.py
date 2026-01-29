"""Run once to enable the pgvector extension in the connected Postgres database.

This script uses SQLAlchemy engine from the Flask app to execute the
CREATE EXTENSION command. Run it after your Postgres container is up and
before you run migrations or start using pgvector columns.
"""
from backend.app import app, db
try:
    from backend.config import Config
except ImportError:
    from config import Config
from sqlalchemy import text


def enable_extension():
    with app.app_context():
        try:
            # execute raw SQL to create extension
            db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            db.session.commit()
            print('pgvector extension enabled (or already present).')
        except Exception as e:
            print('Failed to enable pgvector extension:', e)

if __name__ == '__main__':
    enable_extension()
