"""
Quality Score Parity Verification Script
==========================================
Compares the stored quality_score_cached in the DB against the live
computed quality_score property for every idea.

Unlike novelty, quality_score is a pure DB-computed property (no external
services), so this is fast and deterministic.

Usage:
    python -m scripts.verify_quality_parity          # dry-run
    python -m scripts.verify_quality_parity --fix     # update stale caches
"""
import os, sys, logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.WARNING)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL not set. Export it or add to .env")


def run(fix: bool = False):
    from backend.app import create_app

    app = create_app()
    with app.app_context():
        from backend.core.db import db
        from backend.core.models import ProjectIdea

        ideas = ProjectIdea.query.order_by(ProjectIdea.id).all()

        total = len(ideas)
        match = 0
        mismatch = 0
        drifts = []

        print(f"\n{'='*70}")
        print(f"  Quality Score Parity Check — {total} ideas")
        print(f"  Mode: {'FIX (will update DB)' if fix else 'DRY-RUN (read-only)'}")
        print(f"{'='*70}\n")

        for idea in ideas:
            cached = idea.quality_score_cached
            live = idea.quality_score  # computed property

            if cached == live:
                match += 1
            else:
                mismatch += 1
                drifts.append({
                    "id": idea.id,
                    "title": (idea.title or "")[:60],
                    "cached": cached,
                    "live": live,
                    "delta": abs((cached or 0) - live),
                })
                if fix:
                    idea.refresh_quality_cache()

        if fix and mismatch > 0:
            db.session.commit()
            print(f"  ✓ Committed {mismatch} quality cache updates")

        print(f"\n{'='*70}")
        print(f"  RESULTS: {match} match | {mismatch} drift (out of {total})")
        if drifts:
            print(f"\n  Drifted ideas:")
            for d in sorted(drifts, key=lambda x: x["delta"], reverse=True)[:20]:
                print(f"    ID {d['id']:>5}: cached={d['cached']!s:>4} → live={d['live']:>4}  (Δ{d['delta']})")
        print(f"{'='*70}\n")

        return mismatch == 0


if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    success = run(fix=fix_mode)
    sys.exit(0 if success else 1)
