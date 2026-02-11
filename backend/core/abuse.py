from datetime import datetime, timedelta
from typing import Optional

from backend.core.db import db
from backend.core.models import AbuseEvent
from backend.core.config import Config


def record_abuse_event(user_id: Optional[int], event_type: str, metadata: dict = None):
    try:
        # If the user id doesn't exist in `users` table (tests use arbitrary ids),
        # avoid violating the FK by storing `NULL` instead.
        user_fk = None
        if user_id is not None:
            try:
                from backend.core.app import User
                if User.query.get(user_id):
                    user_fk = user_id
                else:
                    # Preserve the original provided user_id in details so we can
                    # attribute events even when the users table has no corresponding row.
                    metadata = metadata or {}
                    metadata["_anon_user_id"] = user_id
            except Exception:
                user_fk = None
                metadata = metadata or {}
                metadata["_anon_user_id"] = user_id

        ev = AbuseEvent(user_id=user_fk, event_type=event_type, details=metadata or {})
        db.session.add(ev)
        db.session.commit()
        return ev
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("record_abuse_event: initial insert failed: %s", e)
        db.session.rollback()
        # If the table wasn't created (e.g., running tests against a fresh DB),
        # attempt to create all tables and retry once.
        try:
            from sqlalchemy.exc import ProgrammingError, OperationalError, IntegrityError
            if isinstance(e, (ProgrammingError, OperationalError, IntegrityError)) or "does not exist" in str(e):
                logger.info("Attempting db.create_all() and retrying abuse event insert")
                db.create_all()
                user_fk = None
                if user_id is not None:
                    try:
                        from backend.core.app import User
                        if User.query.get(user_id):
                            user_fk = user_id
                    except Exception:
                        user_fk = None
                ev = AbuseEvent(user_id=user_fk, event_type=event_type, details=metadata or {})
                db.session.add(ev)
                db.session.commit()
                return ev
        except Exception as e2:
            logger.exception("record_abuse_event: retry insert failed: %s", e2)
            db.session.rollback()
        return None


def count_recent_events(user_id: Optional[int], event_type: str, window_seconds: int = None) -> int:
    window_seconds = window_seconds or Config.ABUSE_WINDOW_SECONDS
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    q = AbuseEvent.query.filter(AbuseEvent.event_type == event_type, AbuseEvent.created_at >= cutoff)
    if user_id is not None:
        # Some events for non-existing users are stored with `user_id` NULL and
        # the supplied id preserved in details['_anon_user_id']. We therefore
        # fetch a superset and count in Python to support both cases.
        events = q.all()
        cnt = 0
        for ev in events:
            if ev.user_id == user_id:
                cnt += 1
            elif isinstance(ev.details, dict) and ev.details.get("_anon_user_id") == user_id:
                cnt += 1
        return cnt
    return q.count()


def check_generation_rate(user_id: Optional[int]) -> bool:
    """Returns True if the user exceeds the configured generation rate threshold."""
    cnt = count_recent_events(user_id, "generation_attempt")
    return cnt >= Config.MAX_GENERATION_REQUESTS_PER_MIN
