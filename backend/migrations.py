import os
import sys
import logging

logger = logging.getLogger(__name__)

def _check_safety_guard():
    """Check if ALLOW_DANGEROUS_MIGRATIONS is set."""
    if os.getenv('ALLOW_DANGEROUS_MIGRATIONS') != 'true':
        logger.error(
            "Dangerous operation blocked. Set ALLOW_DANGEROUS_MIGRATIONS=true to proceed."
        )
        sys.exit(1)

def init_migrations():
    """Initialize migrations directory."""
    _check_safety_guard()
    try:
        from app import app, db
        from flask_migrate import Migrate, init
        migrate = Migrate(app, db)
        with app.app_context():
            init()
            logger.info("Migrations directory initialized.")
    except Exception as e:
        logger.exception("Failed to initialize migrations")
        sys.exit(1)

def create_migration(message="Auto-generated migration"):
    """Create a new migration with the given message."""
    _check_safety_guard()
    try:
        from app import app, db
        from flask_migrate import Migrate, migrate as migrate_cmd
        migrate = Migrate(app, db)
        with app.app_context():
            migrate_cmd(message)
            logger.info("Migration created: %s", message)
    except Exception as e:
        logger.exception("Failed to create migration")
        sys.exit(1)

def upgrade_db():
    """Apply pending migrations."""
    _check_safety_guard()
    try:
        from app import app, db
        from flask_migrate import Migrate, upgrade
        migrate = Migrate(app, db)
        with app.app_context():
            upgrade()
            logger.info("Database migrations applied successfully!")
    except Exception as e:
        logger.exception("Failed to apply migrations")
        sys.exit(1)

# CLI interface
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Database migration management')
    parser.add_argument('action', choices=['init', 'create', 'upgrade'], help='Migration action')
    parser.add_argument('--message', default='Auto-generated migration', help='Migration message for create action')

    args = parser.parse_args()

    if args.action == 'init':
        init_migrations()
    elif args.action == 'create':
        create_migration(args.message)
    elif args.action == 'upgrade':
        upgrade_db()
