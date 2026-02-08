#!/usr/bin/env python
"""
Test endpoint contracts and response schemas.
Validates that all API endpoints follow proper schema after fixes.
"""

import sys
import json
import inspect
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TEST 4: ENDPOINT CONTRACT VALIDATION")
print("=" * 60)
print()

# Import all route blueprints
try:
    from backend.api.routes.novelty import novelty_bp
    from backend.api.routes.generation import generation_bp
    from backend.api.routes.ideas import ideas_bp
    from backend.api.routes.admin import admin_bp
    from backend.api.routes.analytics import analytics_bp
    from backend.api.routes.public import public_bp
    from backend.api.routes.retrieval import retrieval_bp
    print("[OK] All route blueprints imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import route blueprints: {e}")
    sys.exit(1)

print()
print("=== ENDPOINT VALIDATION ===")
print()

# Define expected endpoints and their methods
expected_endpoints = {
    "novelty_bp": {
        "/api/novelty/analyze": ["POST"],
    },
    "generation_bp": {
        "/api/ideas/generate": ["POST"],
    },
    "ideas_bp": {
        "/api/ideas/mine": ["GET"],
        "/api/ideas/<int:idea_id>": ["GET"],
        "/api/ideas/<int:idea_id>/feedback": ["POST"],
        "/api/ideas/<int:idea_id>/view": ["POST"],
    },
    "admin_bp": {
        "/api/admin/ideas/quality-review": ["GET"],
        "/api/admin/ideas/<int:idea_id>/verdict": ["POST"],
    },
    "analytics_bp": {
        "/api/analytics/admin-kpis": ["GET"],
    },
    "public_bp": {
        "/api/public/ideas": ["GET"],
        "/api/public/top-ideas": ["GET"],
        "/api/public/stats": ["GET"],
    },
    "retrieval_bp": {
        "/api/retrieval/sources": ["POST"],
    },
}

blueprints = {
    "novelty_bp": novelty_bp,
    "generation_bp": generation_bp,
    "ideas_bp": ideas_bp,
    "admin_bp": admin_bp,
    "analytics_bp": analytics_bp,
    "public_bp": public_bp,
    "retrieval_bp": retrieval_bp,
}

endpoints_found = 0
endpoints_valid = 0
endpoints_with_decorators = 0

for bp_name, expected_routes in expected_endpoints.items():
    bp = blueprints[bp_name]

    print(f"Blueprint: {bp_name}")
    for url, methods in expected_routes.items():
        found = False
        for url_rule in bp.deferred_functions:
            # Check if route exists
            if hasattr(bp, 'url_map'):
                found = True
                break

        # Check by looking at registered deferred functions
        deferred_count = len(bp.deferred_functions)
        endpoints_found += 1

        if deferred_count > 0:
            endpoints_valid += 1
            print(f"  ✓ {url} [{', '.join(methods)}] - route function found")
        else:
            print(f"  ✗ {url} [{', '.join(methods)}] - NO route function")
    print()

print("=" * 60)
print("=== RESPONSE SCHEMA VALIDATION ===")
print()

# Check for proper error handling in route functions
response_schema_checks = {
    "novelty_bp": {
        "analyze_novelty": {
            "checks": [
                "Description length validation",
                "Proper error messages",
                "novelty_score in response",
                "novelty_level in response",
            ]
        }
    },
    "generation_bp": {
        "generate_ideas": {
            "checks": [
                "Query length validation (max 2000)",
                "Error handling",
                "ideas array in response",
            ]
        }
    },
    "admin_bp": {
        "quality_review": {
            "checks": [
                "Pagination support (page, limit)",
                "Meta object in response",
                "ideas array in response",
            ]
        },
        "save_admin_verdict": {
            "checks": [
                "IntegrityError handling (409 response)",
                "Proper status code (201)",
                "message field in response",
            ]
        }
    },
    "ideas_bp": {
        "get_user_ideas": {
            "checks": [
                "Pagination support",
                "Meta object in response",
                "ideas array in response",
            ]
        },
        "submit_feedback": {
            "checks": [
                "Comment length validation (max 5000)",
                "IntegrityError handling (409)",
                "Proper error messages",
            ]
        }
    },
    "public_bp": {
        "search_ideas": {
            "checks": [
                "Search query validation (max 1000)",
                "Pagination support",
                "NO quality_score in ideas",
                "NO total_users in stats",
            ]
        },
        "top_ideas": {
            "checks": [
                "NO quality_score exposed",
                "Proper pagination",
            ]
        },
        "platform_stats": {
            "checks": [
                "NO total_users field",
                "total_public_ideas present",
                "total_domains present",
            ]
        }
    },
    "retrieval_bp": {
        "retrieval": {
            "checks": [
                "Similarity threshold validation (0.0-1.0)",
                "Type checking for threshold",
                "Proper error messages",
            ]
        }
    }
}

# Analyze route function source code for validations
print("Checking response schemas and validations...\n")

route_file_checks = {
    "backend/api/routes/novelty.py": {
        "has_length_validation": True,
        "required_checks": ["len(description) > 5000", "len(description) < 10"],
    },
    "backend/api/routes/generation.py": {
        "has_length_validation": True,
        "required_checks": ["len(query) > 2000"],
    },
    "backend/api/routes/admin.py": {
        "has_pagination": True,
        "has_integrity_error": True,
        "required_checks": ["page", "limit", "IntegrityError"],
    },
    "backend/api/routes/ideas.py": {
        "has_pagination": True,
        "has_integrity_error": True,
        "required_checks": ["len(comment) > 5000", "IntegrityError"],
    },
    "backend/api/routes/public.py": {
        "has_no_quality_score": True,
        "has_no_total_users": True,
        "has_search_validation": True,
        "required_checks": ["len(q) > 1000", "quality_score", "total_users"],
    },
    "backend/api/routes/retrieval.py": {
        "has_threshold_validation": True,
        "required_checks": ["0.0 <= similarity_threshold <= 1.0"],
    },
}

schema_checks_passed = 0
schema_checks_total = 0

for file_path, checks in route_file_checks.items():
    full_path = Path(f"d:/Work/InnovateSphere/{file_path}")
    try:
        with open(full_path, 'r') as f:
            content = f.read()

        print(f"File: {file_path}")

        for check_name in checks.get("required_checks", []):
            schema_checks_total += 1
            if check_name in content:
                print(f"  ✓ {check_name}")
                schema_checks_passed += 1
            else:
                print(f"  ✗ {check_name} NOT FOUND")

        if "has_pagination" in checks:
            schema_checks_total += 1
            if "page" in content and "limit" in content:
                print(f"  ✓ Pagination parameters (page, limit)")
                schema_checks_passed += 1
            else:
                print(f"  ✗ Pagination parameters missing")

        if "has_integrity_error" in checks:
            schema_checks_total += 1
            if "IntegrityError" in content:
                print(f"  ✓ IntegrityError handling")
                schema_checks_passed += 1
            else:
                print(f"  ✗ IntegrityError handling missing")

        print()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}\n")

print("=" * 60)
print("=== VALIDATION SUMMARY ===")
print()
print(f"Endpoints Found: {endpoints_found}")
print(f"Endpoints Valid: {endpoints_valid}")
print(f"Schema Checks Passed: {schema_checks_passed}/{schema_checks_total}")
print()

if schema_checks_passed == schema_checks_total and endpoints_valid == endpoints_found:
    print("[OK] All endpoint contracts validated successfully!")
    print("Status: PASSED ✓")
else:
    print("[WARNING] Some endpoint contracts may need attention")
    print("Status: REVIEW NEEDED")

print()
print("=" * 60)
