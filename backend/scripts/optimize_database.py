#!/usr/bin/env python
"""
Database schema optimization script.
Adds missing indexes and constraints for performance and data integrity.

Usage:
    python backend/scripts/optimize_database.py
"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv("backend/.env")
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("Error: DATABASE_URL not set in .env")
    exit(1)

engine = create_engine(db_url)

def get_existing_indexes(table_name):
    """Get existing indexes for a table."""
    inspector = inspect(engine)
    indexes = inspector.get_indexes(table_name)
    return {idx['name'] for idx in indexes}

def get_existing_constraints(table_name):
    """Get existing constraints for a table."""
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints(table_name)
    return {c['name'] for c in constraints}

# SQL statements to add missing indexes
index_optimizations = [
    ("idea_requests", "idx_idea_requests_user_id", "CREATE INDEX IF NOT EXISTS idx_idea_requests_user_id ON idea_requests(user_id)"),
    ("idea_requests", "idx_idea_requests_idea_id", "CREATE INDEX IF NOT EXISTS idx_idea_requests_idea_id ON idea_requests(idea_id)"),
    ("idea_reviews", "idx_idea_reviews_rating", "CREATE INDEX IF NOT EXISTS idx_idea_reviews_rating ON idea_reviews(rating)"),
    ("project_ideas", "idx_project_ideas_is_public", "CREATE INDEX IF NOT EXISTS idx_project_ideas_is_public ON project_ideas(is_public)"),
    ("project_ideas", "idx_project_ideas_is_validated", "CREATE INDEX IF NOT EXISTS idx_project_ideas_is_validated ON project_ideas(is_validated)"),
    ("domain_categories", "idx_domain_categories_domain_id", "CREATE INDEX IF NOT EXISTS idx_domain_categories_domain_id ON domain_categories(domain_id)"),
    ("admin_verdicts", "idx_admin_verdicts_admin_id", "CREATE INDEX IF NOT EXISTS idx_admin_verdicts_admin_id ON admin_verdicts(admin_id)"),
]

def run_optimizations():
    """Run database optimizations."""
    print("Starting database optimizations...\n")

    with engine.connect() as conn:
        successful = 0
        failed = 0
        skipped = 0

        # Add indexes
        print("=== Adding Indexes ===")
        for table, idx_name, sql in index_optimizations:
            try:
                exist_idxs = get_existing_indexes(table)
                if idx_name in exist_idxs:
                    print(f"[SKIP] {table}.{idx_name} (already exists)")
                    skipped += 1
                else:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"[OK] {table}.{idx_name}")
                    successful += 1
            except Exception as e:
                print(f"[ERROR] {table}.{idx_name}: {str(e)[:80]}")
                conn.rollback()
                failed += 1

        print(f"\n=== Unique Constraints (Informational) ===")
        print("Note: The following constraints may need manual addition if duplicates exist:")
        print("  1. idea_requests(user_id, idea_id)")
        print("  2. idea_sources(idea_id, url)")
        print("  3. domain_categories(domain_id, name)")
        print("  4. admin_verdicts(idea_id)")

        print(f"\n=== Performance Summary ===")
        print(f"Indexes Added: {successful}")
        print(f"Indexes Failed: {failed}")
        print(f"Indexes Skipped: {skipped}")

        if successful > 0:
            print(f"\nDatabase now has improved indexes for:")
            print(f"  - Faster lookups on foreign keys (user_id, idea_id)")
            print(f"  - Faster filtering (is_public, is_validated)")
            print(f"  - Faster rating aggregations")

        if failed > 0:
            print(f"\nNote: {failed} index(es) failed. Check permissions.")

if __name__ == "__main__":
    run_optimizations()
