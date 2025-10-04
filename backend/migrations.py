from app import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Initialize migrations directory if it doesn't exist
        from flask_migrate import init, migrate as migrate_cmd, upgrade
        try:
            init()
            print("Migrations directory initialized.")
        except:
            print("Migrations directory already exists.")
        
        # Generate migration for current schema changes
        migrate_cmd("Added 2FA fields")
        
        # Apply migrations
        upgrade()
        print("Database migrations applied successfully!")