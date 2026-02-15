#!/usr/bin/env python3
"""
Quick test script to verify the improved keyword extraction and query handling.
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.retrieval.github_client import (

    _extract_semantic_keywords_with_llm,
    _generate_query_variations,
    _extract_key_terms
)

def test_heuristic_extraction():
    """Test the heuristic key term extraction (fallback)."""
    print("=" * 60)
    print("TEST 1: Heuristic Key Term Extraction")
    print("=" * 60)
    
    query = "A personalized fitness tracking system that helps users monitor their health"
    result = _extract_key_terms(query, max_terms=5)
    print(f"Query: {query}")
    print(f"Extracted terms: {result}")
    print(f"Expected: 5 terms including 'personalized', 'fitness', 'tracking', etc.")
    print()

def test_query_variations_short():
    """Test query variations for a short query."""
    print("=" * 60)
    print("TEST 2: Query Variations (Short Query)")
    print("=" * 60)
    
    query = "resume analyzer with nlp"
    domain = "Software"
    variations = _generate_query_variations(query, domain)
    
    print(f"Query: {query}")
    print(f"Domain: {domain}")
    print(f"Generated {len(variations)} variations:")
    for i, (var_query, desc) in enumerate(variations, 1):
        print(f"  {i}. [{desc}] {var_query[:60]}{'...' if len(var_query) > 60 else ''}")
    print()

def test_query_variations_long():
    """Test query variations for a long query (should trigger LLM extraction)."""
    print("=" * 60)
    print("TEST 3: Query Variations (Long Query - Resume Analyzer)")
    print("=" * 60)
    
    query = "A comprehensive resume analysis platform that uses natural language processing to help job seekers improve their resumes and prepare for interviews with machine learning powered interview simulation"
    domain = "Software"
    
    print(f"Query: {query[:80]}...")
    print(f"Domain: {domain}")
    print(f"Query length: {len(query)} chars")
    print()
    
    # This will test the new mixed keyword extraction
    try:
        variations = _generate_query_variations(query, domain)
        print(f"Generated {len(variations)} variations:")
        for i, (var_query, desc) in enumerate(variations, 1):
            marker = " ✓" if "LLM-summarized" in desc else ""
            print(f"  {i}. [{desc}]{marker} {var_query[:60]}{'...' if len(var_query) > 60 else ''}")
        print()
    except Exception as e:
        print(f"Error (expected if LLM not available): {e}")
        print()

def test_oversized_query():
    """Test handling of oversized query (>200 chars)."""
    print("=" * 60)
    print("TEST 4: Oversized Query Handling (>200 chars)")
    print("=" * 60)
    
    query = "A very long and detailed description of a machine learning platform that does many things including natural language processing and computer vision and deep learning and neural networks and data analysis"
    domain = "Software"
    
    print(f"Query length: {len(query)} chars")
    print(f"Should trigger LLM summarization for queries > 200 chars")
    print()
    
    try:
        variations = _generate_query_variations(query, domain)
        has_llm_summary = any("LLM-summarized" in desc for _, desc in variations)
        print(f"Has LLM-summarized variation: {has_llm_summary}")
        
        for var_query, desc in variations:
            if "LLM-summarized" in desc:
                print(f"  LLM Summary: {var_query}")
                print(f"  Summary length: {len(var_query)} chars")
        print()
    except Exception as e:
        print(f"Error (expected if LLM not available): {e}")
        print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("KEY TERMS EXTRACTION & QUERY HANDLING TESTS")
    print("=" * 60 + "\n")
    
    test_heuristic_extraction()
    test_query_variations_short()
    test_query_variations_long()
    test_oversized_query()
    
    print("=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)
    print("\nNote: LLM-dependent tests may fail if LLM is not configured.")
    print("The implementation includes fallback to heuristic extraction.")
