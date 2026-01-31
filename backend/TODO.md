# TODO: Implement AI Pipeline Versioning and Domain Taxonomy (Segment 0.1)

## Completed Tasks
- [x] Analyze codebase and create plan
- [x] Get user approval for plan
- [x] Update config.py: Add DEFAULT_AI_PIPELINE_VERSION and ENABLE_AI_PIPELINES
- [x] Add new models in models.py: ai_pipeline_versions, domains, domain_categories
- [x] Create backend/ai_registry.py: Add get_active_ai_pipeline_version() function
- [x] Update User model in app.py: Add preferred_domain_id FK
- [x] Add new APIs in app.py: GET /api/domains and GET /api/ai/pipeline-version
- [x] Create backend/seed_data.py: Idempotent seed function for domains and AI pipeline version
- [x] Create docs/ai_architecture.md: Documentation for Segment 0.1

## Pending Tasks
- [ ] Run database migrations to create new tables
- [ ] Execute seed script to populate initial data
- [ ] Test new APIs and verify app boots cleanly
