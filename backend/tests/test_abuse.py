from backend.core.abuse import record_abuse_event, count_recent_events, check_generation_rate
from backend.core.config import Config
from backend.app import app


def test_abuse_record_and_count():
    # Ensure clean start by recording unique user
    user_id = 999999
    with app.app_context():
        # Record one generation attempt
        ev = record_abuse_event(user_id, 'generation_attempt', {'note': 'test'})
        assert ev is not None
        cnt = count_recent_events(user_id, 'generation_attempt', window_seconds=Config.ABUSE_WINDOW_SECONDS)
        assert cnt >= 1


def test_generation_rate_threshold():
    user_id = 888888
    with app.app_context():
        # Record up to threshold
        for _ in range(Config.MAX_GENERATION_REQUESTS_PER_MIN):
            record_abuse_event(user_id, 'generation_attempt')
        # Now check should report True (>= threshold)
        assert check_generation_rate(user_id) is True
