"""Simple script to inspect `prompt_versions` table in Neon/Postgres.

Usage:
  Set environment variable `NEON_CONN` to your Neon connection string (pg URI),
  then run: python scripts/inspect_prompt_versions.py

This script intentionally reads the connection string from env to avoid
committing credentials into the repo.
"""
import os
import json
import sys
import psycopg2
import psycopg2.extras


def get_conn():
    dsn = os.environ.get("NEON_CONN")
    if not dsn:
        print("NEON_CONN environment variable not set. Export your Neon connection string.")
        sys.exit(2)
    return psycopg2.connect(dsn)


def fetch_prompt_versions(limit=50):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Discover available columns to avoid failing on schema differences
            cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='prompt_versions'"
            )
            cols = {r['column_name'] for r in cur.fetchall()}

            preferred = [
                'id', 'name', 'description', 'prompt_template',
                'prompt_body', 'system_prompt', 'template',
                'created_at', 'updated_at'
            ]
            selected = [c for c in preferred if c in cols]
            if not selected:
                # fallback to select all columns (limited)
                q = f"SELECT * FROM prompt_versions ORDER BY created_at DESC LIMIT %s"
            else:
                q = f"SELECT {', '.join(selected)} FROM prompt_versions ORDER BY created_at DESC LIMIT %s"

            cur.execute(q, (limit,))
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()


def main():
    rows = fetch_prompt_versions(limit=50)
    if not rows:
        print("No rows found in prompt_versions")
        return
    print(json.dumps(rows, default=str, indent=2))


if __name__ == "__main__":
    main()
