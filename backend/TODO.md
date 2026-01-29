# TODO: Admin Ingestion & Re-Embedding API

## Steps to Complete

- [ ] Add INGEST_MAX_PROJECTS to backend/config.py (default 50)
- [ ] Create backend/ingest_api.py with Flask Blueprint for POST /api/admin/ingest
  - [ ] Implement jwt_required("admin") protection
  - [ ] Validate payload: non-empty projects list, max INGEST_MAX_PROJECTS, each with title and description
  - [ ] For each project: deduplication by title, insert Project (source='admin'), generate embedding, validate dimension, insert ProjectVector
  - [ ] Use one transaction per project with rollback on failure
  - [ ] Return response with inserted, skipped, failed counts and errors list
  - [ ] Structured logging for counts
- [ ] Edit backend/app.py to import and register the ingest_api blueprint
- [ ] Test endpoint: 401 no token, 403 non-admin, success with admin token, verify data affects novelty and idea generation
