from datetime import datetime

def rank_sources(sources):
    def sort_key(source):
        sim = source.get("similarity_score", 0.0)

        rejected = source.get("admin_rejected_count", 0)
        validated = source.get("admin_validated_count", 0)

        admin_penalty = rejected * 0.15
        admin_bonus = validated * 0.1

        recency = 0.0
        pub_date = source.get("metadata", {}).get("published_date")
        if pub_date:
            try:
                recency = datetime.fromisoformat(pub_date).timestamp()
            except Exception:
                pass

        stars = source.get("metadata", {}).get("stars", 0)

        return (
            -(sim + admin_bonus - admin_penalty),
            -recency,
            -stars,
        )

    return sorted(sources, key=sort_key)
