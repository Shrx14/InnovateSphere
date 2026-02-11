from backend.core.db import db
from backend.core.models import IdeaSource, AdminVerdict



def get_source_reputation():
    """
    Infers source quality from admin verdicts on ideas.
    Returns:
    {
        url: {
            "rejected": int,
            "downgraded": int,
            "validated": int
        }
    }
    """
    rows = (
        db.session.query(
            IdeaSource.url,
            AdminVerdict.verdict,
        )
        .join(AdminVerdict, AdminVerdict.idea_id == IdeaSource.idea_id)
        .all()
    )

    reputation = {}
    for url, verdict in rows:
        reputation.setdefault(url, {"rejected": 0, "downgraded": 0, "validated": 0})

        if verdict == "rejected":
            reputation[url]["rejected"] += 1
        elif verdict == "downgraded":
            reputation[url]["downgraded"] += 1
        elif verdict == "validated":
            reputation[url]["validated"] += 1

    return reputation
