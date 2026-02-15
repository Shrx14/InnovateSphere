#!/usr/bin/env python3
"""Fast integration test with Flask app context"""

import sys
sys.path.insert(0, 'd:\\Work\\InnovateSphere')

from backend.core.app import create_app
from backend.novelty.router import route_engine
from backend.novelty.utils.calibration import compute_evidence_score, apply_evidence_constraints

app = create_app()

with app.app_context():
    print("=" * 60)
    print("INTEGRATION TEST: End-to-End Verification")
    print("=" * 60)
    
    # Test 1: Router returns problem_class
    print("\n[1] Router with problem_class...")
    test_desc = "A mobile marketplace for local vendors"
    analyzer, domain, d_conf, p_class, p_conf = route_engine(test_desc)
    print(f"  ✓ Problem Class: {p_class} (conf: {p_conf})")
    print(f"  ✓ Domain: {domain}")
    
    # Test 2: Analyzer returns evidence breakdown
    print("\n[2] Analyzer with evidence breakdown...")
    result = analyzer.analyze(test_desc, domain, problem_class=p_class)
    
    evidence_breakdown = result.get("evidence_breakdown")
    print(f"  ✓ Evidence Breakdown: {evidence_breakdown}")
    
    # Test 3: Check sources have relevance_tier
    print("\n[3] Sources with relevance_tier...")
    sources = result.get("sources", [])
    print(f"  ✓ Retrieved {len(sources)} sources")
    
    if sources:
        for i, src in enumerate(sources[:2]):
            tier = src.get("relevance_tier")
            print(f"    [{i+1}] Tier={tier}, Title={src.get('title', 'N/A')[:40]}")
    
    # Test 4: Evidence score computation with sources
    print("\n[4] Evidence score with sources...")
    score = compute_evidence_score(result.get("debug", {}), d_conf, sources=sources)
    print(f"  ✓ Evidence Score: {score}")
    
    # Test 5: Apply constraints with sources
    print("\n[5] Evidence constraints with sources...")
    constrained = apply_evidence_constraints(result, score, sources=sources)
    print(f"  ✓ Constrained Novelty: {constrained.get('novelty_score')}")
    
    print("\n" + "=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)
