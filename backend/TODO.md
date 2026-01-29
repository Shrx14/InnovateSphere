# TODO: Remove Runtime Schema Creation and Enforce Migrations

## Tasks
- [x] Remove db.create_all() from backend/app.py startup block
- [x] Update backend/ingest.py to check for required tables and fail gracefully if missing
- [x] Refactor backend/migrations.py to expose explicit functions with safety guard
- [x] Verify app startup performs no schema writes
- [x] Verify ingest fails safely with clear error if schema missing
- [x] Verify migrations import does nothing
- [x] Verify explicit migration commands work with safety guard

## Summary
Successfully removed runtime schema creation and enforced migration-driven schema management:

1. **app.py**: Removed `db.create_all()` from startup - app no longer creates schema automatically
2. **ingest.py**: Replaced `db.create_all()` with explicit table existence check - fails gracefully with clear error if required tables (projects, project_vectors) are missing
3. **migrations.py**: Refactored to expose explicit functions (`init_migrations()`, `create_migration()`, `upgrade_db()`) with safety guard requiring `ALLOW_DANGEROUS_MIGRATIONS=true` - no execution on import

All changes are minimal, production-safe, and maintain existing behavior while preventing accidental schema mutations on Neon PostgreSQL.
