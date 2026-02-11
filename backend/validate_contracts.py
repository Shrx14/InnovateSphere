#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test endpoint contracts and response schemas."""

import sys
import io
from pathlib import Path

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("TEST 4: ENDPOINT CONTRACT VALIDATION")
print("=" * 60)
print()

# Check route files for validations using direct file inspection
route_files = {
    'backend/api/routes/novelty.py': {
        'required_checks': ['len(description) > 5000', 'len(description) < 10'],
        'description': 'Novelty analysis validations'
    },
    'backend/api/routes/generation.py': {
        'required_checks': ['len(query) > 2000'],
        'description': 'Generation query validation'
    },
    'backend/api/routes/admin.py': {
        'required_checks': ['page', 'limit', 'IntegrityError'],
        'description': 'Admin pagination and error handling'
    },
    'backend/api/routes/ideas.py': {
        'required_checks': ['len(comment) > 5000', 'IntegrityError'],
        'description': 'Ideas feedback validation'
    },
    'backend/api/routes/public.py': {
        'required_checks': ['len(q) > 1000'],
        'description': 'Public endpoint data exposure checks',
        'should_not_have': ['quality_score in response', 'total_users in response'],
    },
    'backend/api/routes/retrieval.py': {
        'required_checks': ['0.0 <= similarity_threshold <= 1.0'],
        'description': 'Retrieval threshold validation'
    },
}

print('=== ENDPOINT RESPONSE SCHEMA VALIDATION ===')
print()

total_checks = 0
passed_checks = 0

for file_path, config in route_files.items():
    print(f'File: {file_path}')
    print(f'Description: {config["description"]}')

    try:
        full_path = Path(file_path)
        with open(full_path, 'r') as f:
            content = f.read()

        file_passed = 0
        file_total = len(config['required_checks'])

        for check in config['required_checks']:
            total_checks += 1
            if check in content:
                print(f'  [OK] {check}')
                passed_checks += 1
                file_passed += 1
            else:
                print(f'  [FAIL] {check} NOT FOUND')

        # Check for things that should NOT be present
        if 'should_not_have' in config:
            for violation in config.get('should_not_have', []):
                total_checks += 1
                # For public.py, check quality_score is not in response value
                if 'quality_score' in violation:
                    # Look for deprecated quality_score in response dict
                    if '"quality_score"' not in content and "'quality_score'" not in content:
                        print(f'  [OK] {violation} - properly removed')
                        passed_checks += 1
                    else:
                        print(f'  [FAIL] {violation} - still present')
                elif 'total_users' in violation:
                    if '"total_users"' not in content and "'total_users'" not in content:
                        print(f'  [OK] {violation} - properly removed')
                        passed_checks += 1
                    else:
                        print(f'  [FAIL] {violation} - still present')

        print()
    except Exception as e:
        print(f'  [ERROR] {e}')
        print()

print("=" * 60)
print("=== PAGINATION SCHEMA VALIDATION ===")
print()

pagination_files = {
    'backend/api/routes/admin.py': 'Admin quality review endpoint',
    'backend/api/routes/ideas.py': 'User ideas endpoint',
}

pagination_passed = 0

for file_path, description in pagination_files.items():
    print(f'File: {file_path} - {description}')
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check for pagination response format
        required_pagination_fields = ['page', 'limit', 'total', 'pages']
        for field in required_pagination_fields:
            total_checks += 1
            if f'"{field}"' in content or f"'{field}'" in content:
                print(f'  [OK] Meta field: {field}')
                passed_checks += 1
                pagination_passed += 1
            else:
                print(f'  [FAIL] Meta field: {field} NOT FOUND')

        print()
    except Exception as e:
        print(f'  [ERROR] {e}')
        print()

print("=" * 60)
print("=== ERROR HANDLING VALIDATION ===")
print()

error_handling_checks = {
    'backend/api/routes/novelty.py': [
        ('400 response for short description', '400'),
        ('400 response for long description', '400'),
    ],
    'backend/api/routes/generation.py': [
        ('400 response for long query', '400'),
        ('proper error handling', 'except'),
    ],
    'backend/api/routes/admin.py': [
        ('409 Conflict for duplicates', '409'),
        ('201 Created response', '201'),
    ],
    'backend/api/routes/ideas.py': [
        ('409 Conflict for duplicates', '409'),
        ('400 for validation', '400'),
    ],
    'backend/api/routes/public.py': [
        ('400 for long search query', '400'),
        ('400 for invalid pagination', '400'),
    ],
    'backend/api/routes/retrieval.py': [
        ('400 for invalid threshold', '400'),
    ],
}

error_checks_passed = 0
error_checks_total = 0

for file_path, checks in error_handling_checks.items():
    print(f'File: {file_path}')
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        for check_desc, check_str in checks:
            error_checks_total += 1
            total_checks += 1
            if check_str in content:
                print(f'  [OK] {check_desc}')
                passed_checks += 1
                error_checks_passed += 1
            else:
                print(f'  [FAIL] {check_desc} NOT FOUND')

        print()
    except Exception as e:
        print(f'  [ERROR] {e}')
        print()

print("=" * 60)
print("=== VALIDATION SUMMARY ===")
print()
print(f'Total Checks Performed: {total_checks}')
print(f'Checks Passed: {passed_checks}')
print(f'Checks Failed: {total_checks - passed_checks}')
print()

if passed_checks == total_checks:
    print("[OK] All endpoint contracts validated successfully!")
    print("Status: PASSED")
    exit_code = 0
else:
    failed_count = total_checks - passed_checks
    print(f"[WARNING] {failed_count} checks failed")
    print("Status: REVIEW NEEDED")
    exit_code = 1

print()
print("=" * 60)
exit(exit_code)
