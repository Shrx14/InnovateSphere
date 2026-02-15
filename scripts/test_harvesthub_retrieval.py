#!/usr/bin/env python
"""
Test script to evaluate the improved retrieval system on HarvestHub query.
Compares keyword extraction and source retrieval with 50-source limit.
"""
import sys
sys.path.insert(0, 'd:\\Work\\InnovateSphere')

import json
import logging
from datetime import datetime

# Set up logging to see detailed retrieval info
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

from backend.retrieval.arxiv_client import _extract_academic_keywords_with_llm
from backend.retrieval.github_client import _extract_semantic_keywords_with_llm
from backend.retrieval.orchestrator import retrieve_sources

# HarvestHub query
description = """A Local Artisan Market Management & Discovery Platform
The solution is a two-sided platform, called HarvestHub, with both a web application for organizers and a mobile application for vendors and community members.
Solution Components:
Organizer Web Portal:
Event Creation & Management: Organizers can easily list event details, set up booth types and pricing, and manage vendor applications.
Automated Booth Allocation: An AI-powered layout optimizer suggests efficient booth arrangements based on vendor category, size requirements, and power needs, which organizers can then manually adjust.
Payment & Reporting: Integrated payment processing for vendor fees and a dashboard for financial reporting and analytics.
Vendor Mobile App:
Event Discovery & Application: Vendors can find upcoming markets, view available booth options, and apply directly through the app.
Market-Specific Inventory Management: A simple inventory system allowing vendors to track which items are allocated to which market and manage stock levels in real-time during the event.
Customer Engagement: A feature for vendors to showcase their products, offer limited-time "market deals," and allow customers to pre-order items for pickup at the event."""

domain = "Web & Mobile Development"

print("=" * 80)
print("HarvestHub Retrieval Test")
print("=" * 80)
print(f"\nQuery Length: {len(description)} characters")
print(f"Domain: {domain}\n")

# Test arXiv keyword extraction
print("\n" + "=" * 80)
print("Testing arXiv Keyword Extraction")
print("=" * 80)
try:
    arxiv_keywords = _extract_academic_keywords_with_llm(description, domain)
    print(f"✓ Compound terms: {arxiv_keywords.get('compound_terms', [])}")
    print(f"✓ Simple terms: {arxiv_keywords.get('simple_terms', [])}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test GitHub keyword extraction
print("\n" + "=" * 80)
print("Testing GitHub Keyword Extraction")
print("=" * 80)
try:
    github_keywords = _extract_semantic_keywords_with_llm(description, domain)
    print(f"✓ Simple terms: {github_keywords.get('simple_terms', [])}")
    print(f"✓ Compound terms: {github_keywords.get('compound_terms', [])}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test source retrieval
print("\n" + "=" * 80)
print("Testing Source Retrieval (limit=50)")
print("=" * 80)
try:
    result = retrieve_sources(
        query=description,
        domain=domain,
        limit=50,
        semantic_filter=False
    )
    
    sources = result.get("sources", [])
    print(f"\n✓ Retrieved {len(sources)} sources")
    
    # Breakdown by source type
    arxiv_sources = [s for s in sources if s.get("source_type") == "arxiv"]
    github_sources = [s for s in sources if s.get("source_type") == "github"]
    
    print(f"  - arXiv papers: {len(arxiv_sources)}")
    print(f"  - GitHub repos: {len(github_sources)}")
    
    # Display sample sources
    print("\n" + "-" * 80)
    print("Sample Retrieved Sources (first 10):")
    print("-" * 80)
    
    for i, source in enumerate(sources[:10], 1):
        title = source.get("title") or source.get("name") or ""
        source_type = source.get("source_type")
        confidence = source.get("confidence", 0)
        url = source.get("url", "")
        
        print(f"\n{i}. [{source_type.upper()}] {title[:70]}")
        print(f"   URL: {url[:70]}")
        print(f"   Confidence: {confidence:.3f}")
    
    # Save results to file for further analysis
    output_file = "D:\\Work\\InnovateSphere\\scripts\\harvesthub_retrieval_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "query": description[:100],
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "total_sources": len(sources),
            "arxiv_count": len(arxiv_sources),
            "github_count": len(github_sources),
            "sample_sources": [
                {
                    "title": s.get("title") or s.get("name", ""),
                    "source_type": s.get("source_type"),
                    "url": s.get("url"),
                    "confidence": s.get("confidence")
                }
                for s in sources[:20]
            ]
        }, f, indent=2)
    print(f"\n✓ Results saved to {output_file}")
    
except Exception as e:
    print(f"✗ Error during retrieval: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
