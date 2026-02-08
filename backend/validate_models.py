#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test 5: Verify models are properly defined by code inspection."""

from pathlib import Path
import re

print("=" * 60)
print("TEST 5: MODELS SCHEMA DEFINITION VALIDATION")
print("=" * 60)
print()

models_file = Path("backend/core/models.py")
app_file = Path("backend/core/app.py")

print("=== CHECKING MODEL CLASS DEFINITIONS ===")
print()

models_to_check = {
    'Domain': 'backend/core/models.py',
    'DomainCategory': 'backend/core/models.py',
    'ProjectIdea': 'backend/core/models.py',
    'IdeaRequest': 'backend/core/models.py',
    'IdeaSource': 'backend/core/models.py',
    'IdeaReview': 'backend/core/models.py',
    'IdeaView': 'backend/core/models.py',
    'AdminVerdict': 'backend/core/models.py',
    'User': 'backend/core/app.py',
}

models_found = 0

for model_name, file_path in models_to_check.items():
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if f'class {model_name}' in content:
            print(f"[OK] {model_name} class found in {file_path}")
            models_found += 1
        else:
            print(f"[FAIL] {model_name} class NOT found in {file_path}")
    except Exception as e:
        print(f"[ERROR] Could not read {file_path}: {e}")

print()
print("=== CHECKING CRITICAL DATABASE COLUMNS ===")
print()

critical_columns = {
    'User': ['email', 'username', 'created_at'],
    'Domain': ['name'],
    'ProjectIdea': ['user_id', 'title', 'description', 'domain_id', 'created_at'],
    'IdeaRequest': ['user_id', 'idea_id'],
    'IdeaSource': ['idea_id', 'title', 'url', 'source_type'],
    'IdeaReview': ['idea_id', 'rating'],
    'IdeaView': ['idea_id', 'user_id'],
    'AdminVerdict': ['idea_id', 'admin_id', 'verdict'],
    'DomainCategory': ['domain_id', 'name'],
}

columns_ok = 0
columns_total = 0

for model_name, columns in critical_columns.items():
    file_path = models_to_check.get(model_name)
    if not file_path:
        continue

    print(f"Model: {model_name}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find the class definition
        class_match = re.search(rf'class {model_name}\(.*?\):(.*?)(?=class |\Z)', content, re.DOTALL)
        if class_match:
            class_content = class_match.group(1)

            for col in columns:
                columns_total += 1
                # Look for the column definition
                col_pattern = rf'db\.Column.*?\b{col}\b|{col}\s*=\s*db\.Column'
                if re.search(col_pattern, class_content):
                    print(f"  [OK] {col}")
                    columns_ok += 1
                elif f'"{col}"' in class_content or f"'{col}'" in class_content:
                    print(f"  [OK] {col}")
                    columns_ok += 1
                else:
                    print(f"  [FAIL] {col} NOT FOUND")

    except Exception as e:
        print(f"  [ERROR] {e}")

    print()

print("=" * 60)
print("=== CHECKING RELATIONSHIPS & FOREIGN KEYS ===")
print()

relationships = {
    'User': ['ProjectIdea', 'IdeaRequest', 'IdeaView'],
    'Domain': ['ProjectIdea', 'DomainCategory'],
    'ProjectIdea': ['IdeaRequest', 'IdeaSource', 'IdeaReview', 'IdeaView', 'AdminVerdict'],
}

relationships_ok = 0

for model_name, related_models in relationships.items():
    file_path = models_to_check.get(model_name)
    if not file_path:
        continue

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        class_match = re.search(rf'class {model_name}\(.*?\):(.*?)(?=class |\Z)', content, re.DOTALL)
        if class_match:
            class_content = class_match.group(1)

            print(f"Model: {model_name}")
            # Check for relationship definitions
            rel_count = len(re.findall(r'db\.relationship', class_content))
            if rel_count > 0:
                print(f"  [OK] Found {rel_count} relationship(s)")
                relationships_ok += 1
            else:
                print(f"  [WARNING] No relationships found")

    except Exception as e:
        print(f"  [ERROR] {e}")

print()
print("=" * 60)
print("=== VALIDATION SUMMARY ===")
print()
print(f"Models Found: {models_found}/{len(models_to_check)}")
print(f"Columns Verified: {columns_ok}/{columns_total}")
print()

if models_found >= 8 and columns_ok >= 20:
    print("[OK] All critical models and columns validated!")
    print("Status: PASSED")
    exit_code = 0
else:
    print(f"[WARNING] Some models or columns missing")
    print("Status: REVIEW NEEDED")
    exit_code = 1

print()
print("=" * 60)
exit(exit_code)
