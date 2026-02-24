"""
Novelty Score Parity Verification Script
=========================================
Compares the stored novelty_score_cached in the DB against a fresh
re-computation from the novelty engine for every idea.

Usage:
    python -m scripts.verify_novelty_parity          # dry-run (default)
    python -m scripts.verify_novelty_parity --fix     # update stale scores

Requires:
    DATABASE_URL env var (or .env file)
    Ollama / embedder available for the novelty analyzer
"""
import os, sys, json, logging

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("verify_novelty_parity")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL not set. Export it or add to .env")

TOLERANCE = 5  # points — scores within this delta are considered "matching"


def run(fix: bool = False):
    from backend.app import create_app

    app = create_app()
    with app.app_context():
        from backend.core.db import db
        from backend.core.models import ProjectIdea, Domain
        from backend.novelty.service import analyze_novelty

        ideas = (
            ProjectIdea.query
            .filter(ProjectIdea.is_ai_generated.is_(True))
            .order_by(ProjectIdea.id)
            .all()
        )

        total = len(ideas)
        match = 0
        mismatch = 0
        skipped = 0
        errors = 0
        drifts = []

        print(f"\n{'='*70}")
        print(f"  Novelty Parity Check — {total} AI-generated ideas")
        print(f"  Tolerance: ±{TOLERANCE} points")
        print(f"  Mode: {'FIX (will update DB)' if fix else 'DRY-RUN (read-only)'}")
        print(f"{'='*70}\n")

        for i, idea in enumerate(ideas, 1):
            cached = idea.novelty_score_cached
            domain_name = idea.domain.name if idea.domain else "generic"

            # Reconstruct the input text used during generation
            input_text = None
            if idea.novelty_context and isinstance(idea.novelty_context, dict):
                input_text = idea.novelty_context.get("input_text")
            if not input_text:
                input_text = idea.problem_statement or idea.title

            if not input_text:
                skipped += 1
                continue

            try:
                result = analyze_novelty(input_text, domain_name, bypass_cache=True)
                fresh = round(result.get("novelty_score", 0))
            except Exception as e:
                logger.warning("Idea %d: analysis failed — %s", idea.id, e)
                errors += 1
                continue

            delta = abs((cached or 0) - fresh)

            if delta <= TOLERANCE:
                match += 1
                tag = "OK"
            else:
                mismatch += 1
                tag = "DRIFT"
                drifts.append({
                    "id": idea.id,
                    "title": (idea.title or "")[:60],
                    "domain": domain_name,
                    "cached": cached,
                    "fresh": fresh,
                    "delta": delta,
                })

                if fix:
                    idea.novelty_score_cached = fresh
                    result["input_text"] = input_text
                    idea.novelty_context = result

            if i % 10 == 0 or tag == "DRIFT":
                print(f"  [{i}/{total}] Idea {idea.id:>5}  cached={cached!s:>4}  fresh={fresh:>4}  Δ={delta:>3}  {tag}")

        if fix and mismatch > 0:
            db.session.commit()
            print(f"\n  ✓ Committed {mismatch} score updates to DB")

        # Summary
        print(f"\n{'='*70}")
        print(f"  RESULTS: {match} match | {mismatch} drift | {skipped} skipped | {errors} errors")
        if drifts:
            print(f"\n  Top drifts:")
            for d in sorted(drifts, key=lambda x: x["delta"], reverse=True)[:10]:
                print(f"    ID {d['id']:>5}: cached={d['cached']!s:>4} → fresh={d['fresh']:>4}  (Δ{d['delta']})  [{d['domain']}] {d['title']}")
        print(f"{'='*70}\n")

        return mismatch == 0


if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    success = run(fix=fix_mode)
    sys.exit(0 if success else 1)
