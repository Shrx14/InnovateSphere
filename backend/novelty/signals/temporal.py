from datetime import datetime, timedelta

def compute_temporal_signals(sources: list) -> dict:
    if not sources:
        return {"recency_score": 0.5, "activity_score": 0.5}

    now = datetime.utcnow()
    recent_threshold = now - timedelta(days=365)

    recent = 0
    activity = 0.0

    for s in sources:
        date = s.get("published_date")
        if not date:
            continue
        try:
            pub = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if pub > recent_threshold:
                recent += 1
            age_days = (now - pub).days
            activity += max(0, 1 - age_days / 365)
        except Exception:
            continue

    n = max(len(sources), 1)
    return {
        "recency_score": round(recent / n, 2),
        "activity_score": round(activity / n, 2)
    }
