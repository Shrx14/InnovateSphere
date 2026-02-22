#!/usr/bin/env python3
"""
Quick fix script — re-runs only the feedback and traces steps
that failed during the main seeder run.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['SKIP_STARTUP_CHECKS'] = '1'

import backend.utils.health_checks as _hc
_hc.run_startup_checks = lambda: None

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)-8s  %(message)s', datefmt='%H:%M:%S')

from backend.core.app import create_app
from backend.core.db import db

# Import seed functions from main script
from backend.scripts.seed_full_data import seed_feedback, seed_traces

app = create_app()

with app.app_context():
    print("=== Re-running failed seed steps ===\n")

    print("Step 1: Fixing feedbacks (correct types)...")
    seed_feedback(dry_run=False)

    print("\nStep 2: Fixing traces (all ideas)...")
    seed_traces([], dry_run=False)

    # Final counts
    from backend.core.models import IdeaFeedback, GenerationTrace
    fb_count = IdeaFeedback.query.count()
    tr_count = db.session.query(GenerationTrace).count()
    print(f"\n=== Results ===")
    print(f"  idea_feedbacks:    {fb_count}")
    print(f"  generation_traces: {tr_count}")
    print("Done!")
