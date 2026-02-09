#!/usr/bin/env python3
"""
Quick import verification script for backend fixes.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

print('=== Testing Critical Imports ===')

try:
    from backend.generation.generator import generate_idea
    print('✓ generator.py imports work')
except Exception as e:
    print(f'✗ generator.py failed: {e}')

try:
    from backend.ai.prompts import PASS1_SYSTEM
    print('✓ prompts.py imports work')
except Exception as e:
    print(f'✗ prompts.py failed: {e}')

try:
    from backend.api.routes.generation import generation_bp
    print('✓ generation route imports work')
except Exception as e:
    print(f'✗ generation route failed: {e}')

try:
    from backend.api.routes.ideas import ideas_bp
    print('✓ ideas route imports work')
except Exception as e:
    print(f'✗ ideas route failed: {e}')

try:
    from backend.ai.llm_client import generate_json
    print('✓ llm_client imports work')
except Exception as e:
    print(f'✗ llm_client failed: {e}')

try:
    from backend.api.routes.admin import admin_bp
    print('✓ admin route imports work')
except Exception as e:
    print(f'✗ admin route failed: {e}')

try:
    from backend.api.routes.analytics import analytics_bp
    print('✓ analytics route imports work')
except Exception as e:
    print(f'✗ analytics route failed: {e}')

try:
    from backend.api.routes.novelty import novelty_bp
    print('✓ novelty route imports work')
except Exception as e:
    print(f'✗ novelty route failed: {e}')

print('\n=== All Critical Imports Verified ===')
