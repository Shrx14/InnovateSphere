# Task 2: Fix Admin Ingestion to Match ArXiv Ingestion Behavior

## Completed
- [x] Created shared ingestion utility (`backend/ingest_utils.py`) for consistent embedding generation and storage
- [x] Updated Admin ingestion (`backend/ingest_api.py`) to use shared utility
- [x] Updated ArXiv ingestion (`backend/ingest.py`) to use shared utility
- [x] Ensured identical text formatting: "Title: {title}. Description: {description or ''}"
- [x] Unified duplicate checking by title for both sources
- [x] Maintained same embedding model, dimensions, and metadata handling

## Verification Steps
- [ ] Test Admin ingestion endpoint with sample data
- [ ] Verify admin-ingested projects appear in novelty scoring
- [ ] Verify admin-ingested projects appear in idea generation sources
- [ ] Confirm no regressions in ArXiv ingestion
- [ ] Check logs for consistent ingestion counts

## Notes
- Admin ingestion now behaves identically to ArXiv ingestion except for source='admin'
- No schema changes, embedding model changes, or RAG logic changes
- Shared utility ensures single source of truth for ingestion logic
- ArXiv ingestion updated to use shared utility, maintaining backward compatibility
