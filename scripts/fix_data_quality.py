"""
Database data quality fix script for InnovateSphere.

Fixes:
1. Regenerate tech_stack text from tech_stack_json
2. Normalize novelty_context to consistent schema
3. Remove duplicate ideas (keep higher novelty score)
4. Remove automated test users

Usage:
    python scripts/fix_data_quality.py --dry-run   # Preview changes
    python scripts/fix_data_quality.py              # Apply changes
"""
import sys
import json
import psycopg2

DB_URL = "postgresql://innovate_admin:npg_VmnriYj0lk4y@ep-green-bird-a1xliwfl-pooler.ap-southeast-1.aws.neon.tech/innovatesphere_dev?sslmode=require"

DRY_RUN = "--dry-run" in sys.argv


def connect():
    return psycopg2.connect(DB_URL)


# =========================================================================
# 1. FIX TECH_STACK TEXT FIELD
# =========================================================================

def build_tech_stack_text(ts_json):
    """
    Build a descriptive tech_stack string from tech_stack_json.
    Handles two schemas:
      - Schema A (IDs 1-5): { component, technologies[], rationale }
      - Schema B (IDs 10+): { name, role, justification }
    """
    if not ts_json or not isinstance(ts_json, list):
        return None

    parts = []
    for item in ts_json:
        if not isinstance(item, dict):
            continue

        # Schema A: component + technologies + rationale
        if "component" in item:
            name = item["component"]
            techs = item.get("technologies", [])
            rationale = item.get("rationale", "")
            tech_str = ", ".join(techs) if techs else ""
            if tech_str and rationale:
                parts.append(f"{name} ({tech_str}): {rationale}")
            elif tech_str:
                parts.append(f"{name}: {tech_str}")
            elif rationale:
                parts.append(f"{name}: {rationale}")
            else:
                parts.append(name)

        # Schema B: name + role + justification
        elif "name" in item:
            name = item["name"]
            role = item.get("role", "")
            justification = item.get("justification", "")
            if role and justification:
                parts.append(f"{name} — {role} ({justification})")
            elif role:
                parts.append(f"{name} — {role}")
            else:
                parts.append(name)

    return "; ".join(parts) if parts else None


def fix_tech_stack(conn):
    """Regenerate tech_stack from tech_stack_json for all ideas."""
    print("\n" + "=" * 70)
    print("1. FIXING TECH_STACK TEXT FIELD")
    print("=" * 70)

    cur = conn.cursor()
    cur.execute("SELECT id, title, tech_stack, tech_stack_json FROM project_ideas ORDER BY id")
    rows = cur.fetchall()

    updated = 0
    for id_, title, old_ts, ts_json in rows:
        new_ts = build_tech_stack_text(ts_json)
        if new_ts and new_ts != old_ts:
            print(f"\n  ID={id_} | {title}")
            print(f"    OLD: {old_ts[:100]}...")
            print(f"    NEW: {new_ts[:100]}...")
            if not DRY_RUN:
                cur.execute("UPDATE project_ideas SET tech_stack = %s WHERE id = %s", (new_ts, id_))
            updated += 1

    print(f"\n  >> {updated} ideas {'would be' if DRY_RUN else ''} updated")
    return updated


# =========================================================================
# 2. NORMALIZE NOVELTY_CONTEXT
# =========================================================================

def normalize_novelty_context(ctx):
    """
    Upgrade old-format novelty_context to the new format.
    Old format: { engine, confidence, explanation, evidence_score, domain_maturity, sources_analyzed }
    New format: adds debug, routing, sources, insights, trace_id, speculative,
                explanations, evidence_note, novelty_level, novelty_score,
                signal_breakdown, evidence_breakdown, detailed_explanation
    """
    if not isinstance(ctx, dict):
        return None

    # Already new format (has 'routing' key)
    if "routing" in ctx or "debug" in ctx:
        return None  # No change needed

    # Old format — upgrade
    confidence_str = ctx.get("confidence", "Medium")
    confidence_val = {"High": 0.85, "Medium": 0.6, "Low": 0.35}.get(confidence_str, 0.6)
    evidence_score = ctx.get("evidence_score", 0.5)
    explanation = ctx.get("explanation", "")
    engine = ctx.get("engine", "hybrid_v2")
    domain_maturity = ctx.get("domain_maturity", "unknown")
    sources_analyzed = ctx.get("sources_analyzed", 0)

    # Map old confidence to novelty level
    novelty_level = "moderate"
    if confidence_str == "High" and evidence_score > 0.7:
        novelty_level = "high"
    elif confidence_str == "Low" or evidence_score < 0.3:
        novelty_level = "low"

    return {
        "engine": engine,
        "confidence": confidence_str,
        "speculative": evidence_score < 0.4,
        "novelty_level": novelty_level,
        "novelty_score": None,  # Will be derived from cached score
        "evidence_score": evidence_score,
        "evidence_note": f"Based on analysis of {sources_analyzed} sources in a {domain_maturity} domain.",
        "evidence_breakdown": {
            "supporting": max(1, int(sources_analyzed * evidence_score)),
            "contextual": max(0, sources_analyzed - int(sources_analyzed * evidence_score)),
            "peripheral": 0,
        },
        "signal_breakdown": {
            "signals": {
                "domain_maturity": 0.0 if domain_maturity == "mature" else 5.0,
                "evidence_quality": round((evidence_score - 0.5) * 20, 1),
            }
        },
        "explanations": {
            "summary": explanation,
            "full_narrative": explanation,
        },
        "detailed_explanation": explanation,
        "routing": {
            "detected_domain": "unknown",
            "domain_confidence": 0.5,
            "problem_class": "general",
            "problem_class_confidence": 0.0,
        },
        "sources": [],
        "insights": {
            "domain_maturity": domain_maturity,
            "sources_analyzed": sources_analyzed,
        },
        "debug": {
            "migrated_from_v1": True,
            "original_format": "legacy_6_key",
        },
        "trace_id": None,
    }


def fix_novelty_context(conn):
    """Normalize all novelty_context entries to the new schema."""
    print("\n" + "=" * 70)
    print("2. NORMALIZING NOVELTY_CONTEXT SCHEMA")
    print("=" * 70)

    cur = conn.cursor()
    cur.execute("SELECT id, title, novelty_context, novelty_score_cached FROM project_ideas ORDER BY id")
    rows = cur.fetchall()

    updated = 0
    for id_, title, ctx, cached_score in rows:
        new_ctx = normalize_novelty_context(ctx)
        if new_ctx is not None:
            # Fill in the novelty_score from cached
            new_ctx["novelty_score"] = cached_score
            print(f"  ID={id_} | {title[:50]} — upgrading from legacy format")
            if not DRY_RUN:
                cur.execute(
                    "UPDATE project_ideas SET novelty_context = %s WHERE id = %s",
                    (json.dumps(new_ctx), id_),
                )
            updated += 1

    print(f"\n  >> {updated} ideas {'would be' if DRY_RUN else ''} updated")
    return updated


# =========================================================================
# 3. REMOVE DUPLICATE IDEAS
# =========================================================================

def fix_duplicates(conn):
    """Remove duplicate ideas, keeping the one with the higher novelty score."""
    print("\n" + "=" * 70)
    print("3. REMOVING DUPLICATE IDEAS")
    print("=" * 70)

    cur = conn.cursor()
    cur.execute("""
        SELECT title, array_agg(id ORDER BY novelty_score_cached DESC NULLS LAST), COUNT(*)
        FROM project_ideas
        GROUP BY title
        HAVING COUNT(*) > 1
    """)
    rows = cur.fetchall()

    removed = 0
    for title, ids, cnt in rows:
        keep_id = ids[0]
        remove_ids = ids[1:]
        print(f"  '{title}' — keeping ID={keep_id}, removing IDs={remove_ids}")
        if not DRY_RUN:
            for rid in remove_ids:
                # Delete dependent rows first (cascades should handle most, but be safe)
                cur.execute("DELETE FROM idea_sources WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM idea_requests WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM idea_feedbacks WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM idea_reviews WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM admin_verdicts WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM generation_traces WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM view_events WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM idea_views WHERE idea_id = %s", (rid,))
                cur.execute("DELETE FROM project_ideas WHERE id = %s", (rid,))
                removed += 1

    print(f"\n  >> {removed} duplicate ideas {'would be' if DRY_RUN else ''} removed")
    return removed


# =========================================================================
# 4. CLEAN UP TEST USERS
# =========================================================================

def fix_test_users(conn):
    """Remove automated test users."""
    print("\n" + "=" * 70)
    print("4. CLEANING UP TEST USERS")
    print("=" * 70)

    cur = conn.cursor()
    cur.execute("""
        SELECT id, username FROM users
        WHERE username LIKE 'routetest%%'
           OR username LIKE 'gentest%%'
           OR username LIKE 'novtest%%'
           OR username = 'smoketest'
           OR username LIKE 'testuser_%%'
        ORDER BY id
    """)
    rows = cur.fetchall()

    for id_, username in rows:
        print(f"  Removing user ID={id_} username={username}")
        if not DRY_RUN:
            # Clean up dependent rows
            cur.execute("DELETE FROM idea_requests WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM idea_feedbacks WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM idea_reviews WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM admin_verdicts WHERE admin_id = %s", (id_,))
            cur.execute("DELETE FROM generation_traces WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM view_events WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM idea_views WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM search_queries WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM abuse_events WHERE user_id = %s", (id_,))
            cur.execute("DELETE FROM token_blocklist WHERE id IN (SELECT id FROM token_blocklist LIMIT 0)")  # no FK, skip
            cur.execute("DELETE FROM users WHERE id = %s", (id_,))

    print(f"\n  >> {len(rows)} test users {'would be' if DRY_RUN else ''} removed")
    return len(rows)


# =========================================================================
# MAIN
# =========================================================================

def main():
    mode = "DRY RUN" if DRY_RUN else "LIVE"
    print(f"\n{'#' * 70}")
    print(f"  InnovateSphere Data Quality Fix — {mode}")
    print(f"{'#' * 70}")

    conn = connect()
    try:
        n1 = fix_tech_stack(conn)
        n2 = fix_novelty_context(conn)
        n3 = fix_duplicates(conn)
        n4 = fix_test_users(conn)

        if DRY_RUN:
            print(f"\n{'=' * 70}")
            print(f"DRY RUN COMPLETE — no changes written.")
            print(f"  Would update {n1} tech_stack, {n2} novelty_context")
            print(f"  Would remove {n3} duplicates, {n4} test users")
            print(f"Run without --dry-run to apply.")
            conn.rollback()
        else:
            conn.commit()
            print(f"\n{'=' * 70}")
            print(f"ALL CHANGES COMMITTED!")
            print(f"  Updated {n1} tech_stack, {n2} novelty_context")
            print(f"  Removed {n3} duplicates, {n4} test users")
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
