"""Detailed inspection of tech_stack_json and novelty_context."""
import os
import sys
import psycopg2
import json

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    print("ERROR: DATABASE_URL environment variable is required.")
    print("Set it before running: $env:DATABASE_URL='postgresql://...'")
    sys.exit(1)

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

print("=" * 80)
print("TECH_STACK_JSON samples (first 5 ideas)")
print("=" * 80)
cur.execute("SELECT id, title, tech_stack_json, problem_statement, problem_statement_json FROM project_ideas ORDER BY id LIMIT 5")
for r in cur.fetchall():
    print(f"\nID={r[0]} | TITLE: {r[1]}")
    print(f"  tech_stack_json: {json.dumps(r[2], indent=2)[:500]}")
    print(f"  problem_statement: {r[3][:200] if r[3] else 'NULL'}")
    print(f"  problem_statement_json type: {type(r[4]).__name__}")

print("\n")
print("=" * 80)
print("TECH_STACK_JSON samples (IDs 10-15, different batch)")
print("=" * 80)
cur.execute("SELECT id, title, tech_stack_json FROM project_ideas WHERE id BETWEEN 10 AND 15 ORDER BY id")
for r in cur.fetchall():
    print(f"\nID={r[0]} | TITLE: {r[1]}")
    print(f"  tech_stack_json: {json.dumps(r[2], indent=2)[:500]}")

print("\n")
print("=" * 80)
print("NOVELTY_CONTEXT samples (old format - ID 10)")
print("=" * 80)
cur.execute("SELECT id, novelty_context FROM project_ideas WHERE id = 10")
r = cur.fetchone()
print(f"ID={r[0]}: {json.dumps(r[1], indent=2)[:800]}")

print("\n")
print("=" * 80)
print("NOVELTY_CONTEXT samples (new format - ID 1)")
print("=" * 80)
cur.execute("SELECT id, novelty_context FROM project_ideas WHERE id = 1")
r = cur.fetchone()
print(f"ID={r[0]}: {json.dumps(r[1], indent=2)[:1000]}")

print("\n")
print("=" * 80)
print("DUPLICATE TITLES CHECK")
print("=" * 80)
cur.execute("""
    SELECT title, COUNT(*) as cnt 
    FROM project_ideas 
    GROUP BY title 
    HAVING COUNT(*) > 1 
    ORDER BY cnt DESC
""")
for r in cur.fetchall():
    print(f"  '{r[0]}' appears {r[1]} times")

conn.close()
print("\nDone!")
