# Backend Architecture Cleanup TODO

## Files to Delete
- [x] backend/scripts/test_mock.py - Temporary test script
- [x] backend/services/novelty_service.py - Thin wrapper to consolidate


## Files to Move/Consolidate
- [x] Move backend/health/checks.py → backend/utils/health_checks.py
- [x] Move backend/services/novelty_service.py → backend/novelty/service.py


## Files to Update
- [x] backend/api/routes/public.py - Remove duplicate serialize_public_idea()
- [x] backend/api/routes/health.py - No changes needed (simple endpoint)
- [x] backend/utils/__init__.py - Add health check exports
- [x] backend/novelty/__init__.py - Add service exports


## Verification
- [x] Test imports work correctly
- [x] No broken references


## Summary

### Deleted Files:
1. `backend/scripts/test_mock.py` - Temporary test script
2. `backend/services/novelty_service.py` - Consolidated into novelty module
3. `backend/health/checks.py` - Moved to utils

### Deleted Directories:
1. `backend/services/` - Empty after consolidation
2. `backend/health/` - Empty after move

### New Files:
1. `backend/utils/health_checks.py` - Consolidated health check utilities
2. `backend/novelty/service.py` - Novelty analysis service

### Updated Files:
1. `backend/api/routes/public.py` - Now imports from shared serializer
2. `backend/utils/__init__.py` - Exports health check functions
3. `backend/novelty/__init__.py` - Exports service functions

### Final Directory Structure:
```
backend/
├── ai/                      # AI/LLM clients
├── api/routes/              # API endpoints
├── core/                    # Core app components
├── generation/              # Idea generation
├── novelty/                 # Novelty analysis
│   ├── service.py          # (NEW) Consolidated service
│   └── ...
├── retrieval/              # External source retrieval
├── scripts/                # Database scripts (cleaned)
├── semantic/               # Semantic/embedding utilities
├── tests/                  # Test suite
└── utils/                  # Shared utilities (consolidated)
    ├── health_checks.py    # (NEW) From health/
    └── ...
```
