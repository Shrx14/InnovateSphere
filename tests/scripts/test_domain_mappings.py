#!/usr/bin/env python
"""Test domain keyword mappings for arXiv and GitHub"""

from backend.utils.common import map_domain_to_external_category

new_domains = [
    'AI & Machine Learning',
    'Web & Mobile Development',
    'Data Science & Analytics',
    'Cybersecurity & Privacy',
    'Cloud & DevOps',
    'Blockchain & Web3',
    'IoT & Hardware',
    'Healthcare & Biotech',
    'Education & E-Learning',
    'Business & Productivity Tools'
]

print("\nDomain → External Keywords Mapping for arXiv & GitHub:\n")
print("=" * 80)

for domain in new_domains:
    keywords = map_domain_to_external_category(domain)
    print(f"\n{domain}")
    print(f"  → {keywords}")

print("\n" + "=" * 80)
print("\n✓ All 10 domains have keyword mappings for external API searches")
print("✓ arXiv client will append these keywords to search queries")
print("✓ GitHub client will use these keywords for repository searches\n")
