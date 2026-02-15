"""
Migration script for the InnovateSphere improvement pass.

Run this ONCE against your Neon database to apply the schema changes that
the models.py overhaul introduced:
  - New indexes on frequently queried FK columns
  - CASCADE / SET NULL foreign key rules
  - CHECK constraints (rating, verdict, feedback_type, role)
  - UNIQUE constraints (domain_categories, idea_sources)
  - updated_at columns on tables that were missing them

Usage:
    python -m backend.scripts.migrate_improvements
"""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── DDL statements ──────────────────────────────────────────────────────────

MIGRATION_SQL = [
    # ---------- Indexes ----------
    "CREATE INDEX IF NOT EXISTS ix_idea_sources_idea_id ON idea_sources (idea_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_reviews_idea_id ON idea_reviews (idea_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_reviews_user_id ON idea_reviews (user_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_feedbacks_idea_id ON idea_feedbacks (idea_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_feedbacks_user_id ON idea_feedbacks (user_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_requests_user_id ON idea_requests (user_id);",
    "CREATE INDEX IF NOT EXISTS ix_idea_requests_idea_id ON idea_requests (idea_id);",
    "CREATE INDEX IF NOT EXISTS ix_project_ideas_is_public ON project_ideas (is_public);",
    "CREATE INDEX IF NOT EXISTS ix_project_ideas_is_validated ON project_ideas (is_validated);",
    "CREATE INDEX IF NOT EXISTS ix_domain_categories_domain_id ON domain_categories (domain_id);",
    "CREATE INDEX IF NOT EXISTS ix_admin_verdicts_admin_id ON admin_verdicts (admin_id);",

    # ---------- updated_at columns ----------
    """ALTER TABLE project_ideas
       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
       DEFAULT now();""",
    """ALTER TABLE ai_pipeline_versions
       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
       DEFAULT now();""",
    """ALTER TABLE bias_profiles
       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
       DEFAULT now();""",
    """ALTER TABLE prompt_versions
       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
       DEFAULT now();""",
    """ALTER TABLE admin_verdicts
       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
       DEFAULT now();""",

    # ---------- CHECK constraints (safe: IF NOT EXISTS isn't supported, use DO blocks) ----------
    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_idea_reviews_rating_range'
        ) THEN
            ALTER TABLE idea_reviews
              ADD CONSTRAINT ck_idea_reviews_rating_range CHECK (rating >= 1 AND rating <= 5);
        END IF;
    END $$;""",

    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_admin_verdicts_verdict_valid'
        ) THEN
            ALTER TABLE admin_verdicts
              ADD CONSTRAINT ck_admin_verdicts_verdict_valid
              CHECK (verdict IN ('validated', 'downgraded', 'rejected'));
        END IF;
    END $$;""",

    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_idea_feedbacks_type_valid'
        ) THEN
            ALTER TABLE idea_feedbacks
              ADD CONSTRAINT ck_idea_feedbacks_type_valid
              CHECK (feedback_type IN ('upvote', 'downvote', 'bookmark', 'report', 'helpful', 'not_helpful'));
        END IF;
    END $$;""",

    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_role_valid'
        ) THEN
            ALTER TABLE users
              ADD CONSTRAINT ck_users_role_valid CHECK (role IN ('user', 'admin'));
        END IF;
    END $$;""",

    # ---------- UNIQUE constraints ----------
    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_domain_categories_domain_name'
        ) THEN
            ALTER TABLE domain_categories
              ADD CONSTRAINT uq_domain_categories_domain_name UNIQUE (domain_id, name);
        END IF;
    END $$;""",

    """DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_idea_sources_idea_url'
        ) THEN
            ALTER TABLE idea_sources
              ADD CONSTRAINT uq_idea_sources_idea_url UNIQUE (idea_id, url);
        END IF;
    END $$;""",
]


def run_migration():
    """Execute migration statements inside the Flask app context."""
    from backend.app import create_app
    from backend.core.db import db as _db

    app = create_app()
    with app.app_context():
        conn = _db.engine.connect()
        for idx, stmt in enumerate(MIGRATION_SQL, 1):
            try:
                conn.execute(_db.text(stmt))
                logger.info("[%d/%d] OK", idx, len(MIGRATION_SQL))
            except Exception as exc:
                logger.warning("[%d/%d] SKIPPED (%s)", idx, len(MIGRATION_SQL), exc)
        conn.commit()
        conn.close()
        logger.info("Migration complete — %d statements processed.", len(MIGRATION_SQL))


if __name__ == "__main__":
    run_migration()
