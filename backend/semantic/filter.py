import numpy as np
import logging
from backend.semantic.embedder import get_embedder


logger = logging.getLogger(__name__)


# Problem-type keywords for relevance classification
PROBLEM_TYPE_KEYWORDS = {
    "optimization": {
        "matching": ["optimization", "maximize", "minimize", "efficient", "resource", "allocation", 
                    "layout", "placement", "arrangement", "routing", "scheduler", "constraint"],
        "noise": ["robot", "trajectory", "autonomous", "driving", "sensor network", "charge"]
    },
    "classification": {
        "matching": ["classify", "classify", "category", "predict", "label", "detect", "identify",
                    "recognition", "tag", "type", "segmentation", "clustering"],
        "noise": ["robot", "autonomous", "sensor", "trajectory"]
    },
    "scheduling": {
        "matching": ["schedule", "plan", "allocate", "assign", "timetable", "booking", "resource",
                    "availability", "calendar", "event", "time management", "slot"],
        "noise": ["robot", "autonomous", "charge"]
    },
    "simulation": {
        "matching": ["simulate", "model", "emulate", "behavior", "dynamics", "forecast", "predict",
                    "virtual", "agent-based", "environment"],
        "noise": []
    },
    "anomaly_detection": {
        "matching": ["anomaly", "outlier", "abnormal", "detect", "error", "fault", "unusual",
                    "deviation", "fraud", "threat", "suspicious", "monitoring", "alert"],
        "noise": []
    },
    "ranking": {
        "matching": ["rank", "ranking", "score", "relevance", "priority", "order", "sort",
                    "recommend", "recommendation", "leaderboard", "reputation"],
        "noise": []
    },
    "nlp": {
        "matching": ["nlp", "natural language", "text", "language model", "llm", "parsing",
                    "extraction", "sentiment", "summarization", "translation", "embedding",
                    "semantic", "linguistic"],
        "noise": []
    }
}


def classify_source_relevance(source, problem_class):
    """
    Classify a source as 'direct', 'indirect', or 'noise' based on problem type.
    
    Args:
        source: Source dictionary with title, summary, url
        problem_class: Problem class (optimization, classification, etc.)
        
    Returns:
        tuple: (relevance_class, match_count, noise_count)
        - relevance_class: 'direct' (high match), 'indirect' (mixed), 'noise' (problematic)
        - match_count: Number of matching keywords found
        - noise_count: Number of noise keywords found
    """
    if problem_class == "general" or problem_class not in PROBLEM_TYPE_KEYWORDS:
        return "direct", 0, 0  # Default to direct when no specific classification
    
    # Combine title + summary for analysis
    text = (source.get("title", "") + " " + source.get("summary", "")).lower()
    
    problem_keywords = PROBLEM_TYPE_KEYWORDS[problem_class]
    matching_keywords = problem_keywords.get("matching", [])
    noise_keywords = problem_keywords.get("noise", [])
    
    # Count matches
    match_count = sum(1 for kw in matching_keywords if kw in text)
    noise_count = sum(1 for kw in noise_keywords if kw in text)
    
    # Classify
    if noise_count > 0 and match_count == 0:
        return "noise", match_count, noise_count
    elif noise_count > 0 and match_count > 0:
        return "indirect", match_count, noise_count
    elif match_count > 0:
        return "direct", match_count, noise_count
    else:
        return "indirect", match_count, noise_count  # Default neutral if no keywords match


def _cosine_similarity(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / den) if den else 0.0


def filter_by_semantic_similarity(query_text, sources, threshold, problem_class="general"):
    """
    Filter sources by semantic similarity to the query using fresh embeddings.
    Also applies problem-type relevance classification and penalties.

    Returns the subset of `sources` whose similarity_score >= threshold and
    populates `similarity_score` and `relevance_class` on each source.
    
    Similarity score adjustments based on relevance_class:
    - 'direct': 1.0x (no penalty)
    - 'indirect': 0.7x (mild penalty)
    - 'noise': 0.4x (heavy penalty)
    """
    try:
        embedder = get_embedder()

        query_emb = embedder.encode([query_text], normalize_embeddings=True)[0]

        texts = [s.get("summary") or s.get("title") or "" for s in sources]
        source_embs = embedder.encode(texts, normalize_embeddings=True)

        for src, emb in zip(sources, source_embs):
            sim = _cosine_similarity(query_emb, emb)
            src["similarity_score"] = float(sim)
            
            # Classify relevance and apply penalty
            relevance_class, match_count, noise_count = classify_source_relevance(src, problem_class)
            src["relevance_class"] = relevance_class
            src["relevance_match_count"] = match_count
            src["relevance_noise_count"] = noise_count
            
            # Apply penalty multiplier based on relevance class
            penalty_multiplier = {
                "direct": 1.0,
                "indirect": 0.7,
                "noise": 0.4
            }.get(relevance_class, 1.0)
            
            src["similarity_score_adjusted"] = src["similarity_score"] * penalty_multiplier
            
            if penalty_multiplier < 1.0:
                logger.debug("[Semantic] Source '%s' is %s (match=%d, noise=%d); penalty=%.1fx",
                           src.get("title", "")[:50], relevance_class, match_count, noise_count, penalty_multiplier)

        # Filter by adjusted similarity score
        filtered = [src for src in sources if src.get("similarity_score_adjusted", 0.0) >= threshold]
        return filtered
    except Exception as e:
        logger.warning("Semantic filter skipped: %s", str(e))
        return sources
