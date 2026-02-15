-- ============================================================
-- DDL: Add missing columns to existing tables in Neon
-- Run against the Neon PostgreSQL database manually or via psql.
-- These columns were added to SQLAlchemy models but db.create_all()
-- only creates missing TABLES, not missing COLUMNS on existing tables.
-- ============================================================

-- 1. project_ideas.is_human_verified  (Boolean, default false)
--    Used by admin HITL workflow to mark ideas as human-verified.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'project_ideas' AND column_name = 'is_human_verified'
    ) THEN
        ALTER TABLE project_ideas ADD COLUMN is_human_verified BOOLEAN NOT NULL DEFAULT FALSE;
        RAISE NOTICE 'Added project_ideas.is_human_verified';
    ELSE
        RAISE NOTICE 'project_ideas.is_human_verified already exists';
    END IF;
END $$;

-- 2. idea_sources.is_hallucinated  (Boolean, default false)
--    Used by admin hallucination flagging to mark sources as hallucinated.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'idea_sources' AND column_name = 'is_hallucinated'
    ) THEN
        ALTER TABLE idea_sources ADD COLUMN is_hallucinated BOOLEAN NOT NULL DEFAULT FALSE;
        RAISE NOTICE 'Added idea_sources.is_hallucinated';
    ELSE
        RAISE NOTICE 'idea_sources.is_hallucinated already exists';
    END IF;
END $$;
