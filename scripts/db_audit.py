"""Quick DB audit script to inspect data quality."""
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
print("1. PROJECT IDEAS - tech_stack and novelty_score_cached")
print("=" * 80)
cur.execute("""
    SELECT id, title, tech_stack, tech_stack_json, novelty_score_cached, novelty_context, domain_id
    FROM project_ideas 
    ORDER BY id
""")
rows = cur.fetchall()
for r in rows:
    id_, title, ts, ts_json, novelty, novelty_ctx, domain_id = r
    ts_preview = (ts[:150] + "...") if ts and len(ts) > 150 else ts
    print(f"\nID={id_} | DOMAIN_ID={domain_id}")
    print(f"  TITLE: {title}")
    print(f"  TECH_STACK: {ts_preview}")
    print(f"  TECH_STACK_JSON type: {type(ts_json).__name__}, keys: {list(ts_json.keys()) if isinstance(ts_json, dict) else 'N/A'}")
    print(f"  NOVELTY_SCORE_CACHED: {novelty}")
    if isinstance(novelty_ctx, dict):
        print(f"  NOVELTY_CONTEXT keys: {list(novelty_ctx.keys())}")
    else:
        print(f"  NOVELTY_CONTEXT: {novelty_ctx}")

print("\n" + "=" * 80)
print("2. DOMAINS")
print("=" * 80)
cur.execute("SELECT id, name FROM domains ORDER BY id")
for r in cur.fetchall():
    print(f"  ID={r[0]} | NAME={r[1]}")

print("\n" + "=" * 80)
print("3. DOMAIN CATEGORIES")
print("=" * 80)
cur.execute("SELECT id, name, domain_id FROM domain_categories ORDER BY domain_id, id")
for r in cur.fetchall():
    print(f"  ID={r[0]} | NAME={r[1]} | DOMAIN_ID={r[2]}")

print("\n" + "=" * 80)
print("4. IDEA SOURCES (first 20)")
print("=" * 80)
cur.execute("SELECT id, idea_id, source_type, title, url, is_hallucinated FROM idea_sources ORDER BY idea_id LIMIT 20")
for r in cur.fetchall():
    print(f"  ID={r[0]} | IDEA_ID={r[1]} | TYPE={r[2]} | TITLE={r[3][:50]} | HALLUCINATED={r[5]}")

print("\n" + "=" * 80)
print("5. USERS")
print("=" * 80)
cur.execute("SELECT id, username, role FROM users ORDER BY id")
for r in cur.fetchall():
    print(f"  ID={r[0]} | USERNAME={r[1]} | ROLE={r[2]}")

print("\n" + "=" * 80)
print("6. IDEA COUNT BY DOMAIN")
print("=" * 80)
cur.execute("""
    SELECT d.name, COUNT(pi.id) 
    FROM project_ideas pi 
    LEFT JOIN domains d ON pi.domain_id = d.id 
    GROUP BY d.name 
    ORDER BY COUNT(pi.id) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} ideas")

conn.close()
print("\nDone!")
