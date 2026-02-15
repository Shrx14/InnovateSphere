"""Reset admin user password to use Werkzeug-compatible hash."""
import os, sys
os.chdir('D:/Work/InnovateSphere')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from werkzeug.security import generate_password_hash
from backend.core.app import create_app
from backend.core.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    new_hash = generate_password_hash("AdminPass123")
    db.session.execute(
        text("UPDATE users SET password_hash = :h WHERE id = 1"),
        {"h": new_hash}
    )
    db.session.commit()
    print(f"Password updated for user 1 (test@example.com, admin)")
    print(f"New hash prefix: {new_hash[:30]}")

    # Verify it works
    from werkzeug.security import check_password_hash
    result = db.session.execute(text("SELECT password_hash FROM users WHERE id = 1"))
    stored = result.fetchone()[0]
    ok = check_password_hash(stored, "AdminPass123")
    print(f"Verification: {ok}")
