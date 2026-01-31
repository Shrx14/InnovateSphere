from datetime import datetime

def rank_sources(sources):
    def sort_key(source):
        sim = source.get("similarity_score", 0.0)

        recency = 0.0
        pub_date = source.get("metadata", {}).get("published_date")
        if pub_date:
            try:
                recency = datetime.fromisoformat(pub_date).timestamp()
            except Exception:
                pass

        stars = source.get("metadata", {}).get("stars", 0)

        return (-sim, -recency, -stars)

    return sorted(sources, key=sort_key)
