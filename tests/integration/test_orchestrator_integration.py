#!/usr/bin/env python
"""Test GitHub client directly without needing Flask app context"""

from backend.retrieval.github_client import search_github
from backend.utils import map_domain_to_external_category

print('Testing search_github() with query variations...')
print('=' * 70)

# Test case 1: Original problematic query that now works
print('\nTest 1: "Browser extension for assisting Cognitive disabled people"')
print('Domain: "cognitive_accessibility"')
print('Expected: Should try key terms + domain, then original, then domain only')
print('          and return results from the domain-only variation')
print()
results = search_github(
    'Browser extension for assisting Cognitive disabled people',
    'cognitive_accessibility',
    max_results=5
)
print(f'✓ Retrieved {len(results)} GitHub results')
if results:
    print('\n  Results returned:')
    for r in results[:3]:
        title = r.get('title', 'N/A')
        summary = r.get('summary', '')[:60]
        print(f'    • {title}: {summary}')
else:
    print('  ✗ No results returned')

# Test case 2: Query that should work on first variation
print('\n' + '=' * 70)
print('\nTest 2: "Accessible web application framework"')
print('Domain: "web_accessibility"')
print('Expected: Should return results on first variation (key terms + domain)')
print()
results2 = search_github(
    'Accessible web application framework',
    'web_accessibility',
    max_results=5
)
print(f'✓ Retrieved {len(results2)} GitHub results')
if results2:
    print('\n  Results returned:')
    for r in results2[:3]:
        title = r.get('title', 'N/A')
        summary = r.get('summary', '')[:60]
        print(f'    • {title}: {summary}')
else:
    print('  ✗ No results returned')

# Test case 3: Simple query with security domain
print('\n' + '=' * 70)
print('\nTest 3: "Authentication library"')
print('Domain: "security"')
print()
results3 = search_github(
    'Authentication library',
    'security',
    max_results=5
)
print(f'✓ Retrieved {len(results3)} GitHub results')
if results3:
    print('\n  Results returned:')
    for r in results3[:3]:
        title = r.get('title', 'N/A')
        summary = r.get('summary', '')[:60]
        print(f'    • {title}: {summary}')
else:
    print('  ✗ No results returned')

print('\n' + '=' * 70)
print('✓ Direct GitHub client test completed successfully!')
print('\nSummary:')
print(f'  • Test 1: {len(results)} results')
print(f'  • Test 2: {len(results2)} results')
print(f'  • Test 3: {len(results3)} results')
print(f'  • Total: {len(results) + len(results2) + len(results3)} results found')
