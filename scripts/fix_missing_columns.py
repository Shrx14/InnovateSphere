"""Add missing columns to the users table via the app's DB connection."""
import os, sys
os.chdir('D:/Work/InnovateSphere')

# Load .env
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from backend.core.app import create_app
from backend.core.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check existing columns
    result = db.session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
    ))
    existing = {r[0] for r in result}
    print(f"Existing user columns: {sorted(existing)}")

    if 'preferred_domain_id' not in existing:
        print("Adding preferred_domain_id...")
        db.session.execute(text("ALTER TABLE users ADD COLUMN preferred_domain_id INTEGER"))
        db.session.commit()
        print("Done.")
    else:
        print("preferred_domain_id already exists.")

    if 'role' not in existing:
        print("Adding role...")
        db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
        db.session.commit()
        print("Done.")
    else:
        print("role already exists.")

    # Promote user 1 to admin
    db.session.execute(text("UPDATE users SET role = 'admin' WHERE id = 1"))
    db.session.commit()
    print("User id=1 promoted to admin.")

    # Show user 1 info
    result = db.session.execute(text("SELECT id, email, username, role FROM users WHERE id = 1"))
    row = result.fetchone()
    print(f"Admin user: id={row[0]}, email={row[1]}, username={row[2]}, role={row[3]}")

    # Verify login would work
    result = db.session.execute(text("SELECT password_hash FROM users WHERE id = 1"))
    pw_hash = result.fetchone()[0]
    print(f"Password hash prefix: {pw_hash[:30]}...")
