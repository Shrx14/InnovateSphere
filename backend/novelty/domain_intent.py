# Domains that are suspended and should not be detected as primary intent
# All ideas will be routed to the software analyzer instead
SUSPENDED_DOMAINS = {
    "Business & Productivity Tools",  # Business model suspended
    "Healthcare & Biotech",           # Social model suspended
    "Education & E-Learning",         # Social model suspended
}

DOMAIN_PROFILES = {
    "AI & Machine Learning": {
        "ai", "ml", "machine learning", "neural network", "deep learning",
        "nlp", "natural language", "computer vision", "reinforcement learning",
        "generative", "llm", "transformer", "embedding", "model", "gpt",
        "classification", "regression", "clustering", "prediction"
    },
    "Web & Mobile Development": {
        "web", "app", "frontend", "backend", "react", "vue", "angular",
        "nodejs", "python", "javascript", "typescript", "api", "rest",
        "graphql", "mobile", "ios", "android", "pwa", "progressive web",
        "responsive", "ui", "ux", "database", "framework", "server"
    },
    "Data Science & Analytics": {
        "data", "analytics", "bi", "business intelligence", "tableau",
        "power bi", "datawarehouse", "etl", "statistics", "sql",
        "pandas", "numpy", "visualization", "insights", "metrics",
        "dashboard", "reporting", "big data", "data mining", "analysis"
    },
    "Cybersecurity & Privacy": {
        "security", "privacy", "encryption", "authentication", "firewall",
        "penetration", "vulnerability", "threat", "compliance", "gdpr",
        "oauth", "jwt", "ssl", "tls", "https", "secure", "breach",
        "password", "audit", "monitoring", "detection", "defense"
    },
    "Cloud & DevOps": {
        "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "devops",
        "ci/cd", "cicd", "deployment", "infrastructure", "terraform",
        "ansible", "jenkins", "gitlab", "github", "container", "orchestration",
        "monitoring", "logging", "scalability", "microservices", "service mesh"
    },
    "Blockchain & Web3": {
        "blockchain", "crypto", "cryptocurrency", "bitcoin", "ethereum",
        "smart contract", "solidity", "defi", "nft", "web3", "dapp",
        "consensus", "blockchain", "decentralized", "token", "blockchain",
        "mining", "stake", "transaction", "ledger", "distributed"
    },
    "IoT & Hardware": {
        "iot", "internet of things", "hardware", "sensor", "device",
        "embedded", "microcontroller", "arduino", "raspberry pi", "iot",
        "robotics", "automation", "actuator", "wireless", "5g",
        "edge computing", "iot platform", "connected devices", "smart home"
    },
    "Healthcare & Biotech": {
        "healthcare", "health", "medical", "biotech", "biology", "dna",
        "genomics", "telemedicine", "telehealth", "hospital", "therapy",
        "drug", "disease", "diagnosis", "patient", "clinician",
        "fitbit", "health monitoring", "wellness", "bioinformatics"
    },
    "Education & E-Learning": {
        "education", "learning", "elearning", "course", "training",
        "student", "teacher", "school", "university", "tutoring",
        "lms", "skill", "assessment", "certification", "online",
        "interactive", "gamification", "adaptive learning", "collaboration"
    },
    "Business & Productivity Tools": {
        "business", "crm", "erp", "project management", "productivity",
        "collaboration", "team", "workflow", "automation", "saas",
        "b2b", "enterprise", "startup", "scaling", "revenue",
        "market", "customer", "sales", "invoice", "accounting"
    }
}


# Problem-class keywords for detecting optimization, scheduling, etc.
PROBLEM_CLASS_KEYWORDS = {
    "optimization": {
        "keywords": ["optimal", "maximize", "minimize", "efficient", "efficiency",
                    "resource", "allocation", "layout", "arrangement", "placement",
                    "optimize", "routing", "path", "scheduler", "scheduling",
                    "constraint", "trade-off", "design", "improve performance"],
        "exclude_domains": ["robotics", "sensors", "autonomous driving", "trajectory"]
    },
    "classification": {
        "keywords": ["classify", "categorize", "predict", "label", "tag", "detect",
                    "identify", "recognition", "segmentation", "clustering", "type",
                    "category", "class", "determine", "distinguish"],
        "exclude_domains": ["robotics"]
    },
    "simulation": {
        "keywords": ["simulate", "model", "emulate", "behavior", "dynamics",
                    "forecast", "predict", "virtual", "digital twin", "engine",
                    "physics", "environment", "agent-based"],
        "exclude_domains": []
    },
    "scheduling": {
        "keywords": ["schedule", "plan", "allocate", "assign", "timetable", "time",
                    "booking", "slot", "resource management", "availability",
                    "calendar", "timeline", "event management"],
        "exclude_domains": []
    },
    "anomaly_detection": {
        "keywords": ["anomaly", "outlier", "abnormal", "detect error", "detect fault",
                    "unusual", "deviation", "fraud", "suspicious", "threat",
                    "detection", "monitoring", "alert"],
        "exclude_domains": []
    },
    "ranking": {
        "keywords": ["rank", "ranking", "score", "relevance", "priority", "order",
                    "sort", "recommend", "recommendation", "recommend", "top-k",
                    "leaderboard", "reputation"],
        "exclude_domains": []
    },
    "nlp": {
        "keywords": ["nlp", "natural language", "text", "language model", "llm",
                    "parsing", "extraction", "sentiment", "summarization", "translation",
                    "embedding", "tokenization", "linguistic", "semantic"],
        "exclude_domains": []
    },
    "general": {
        "keywords": [],
        "exclude_domains": []
    }
}


def detect_problem_class(description: str, confidence_threshold: float = 0.5) -> tuple[str, float]:
    """
    Detect the problem classification of an idea.
    Returns a tuple of (problem_class, confidence).
    
    Problem classes:
    - optimization: Finding best solution under constraints
    - classification: Assigning inputs to categories
    - simulation: Modeling system behavior
    - scheduling: Time/resource allocation
    - anomaly_detection: Finding outliers/abnormal patterns
    - ranking: Ordering items by relevance
    - nlp: Natural language processing/understanding
    - general: Doesn't fit above categories
    
    Uses hybrid approach: keyword heuristic first, LLM fallback for edge cases.
    """
    text_lower = description.lower()
    
    # Keyword-based scoring
    scores = {}
    for problem_class, info in PROBLEM_CLASS_KEYWORDS.items():
        if problem_class == "general":
            continue
        
        keyword_matches = sum(1 for kw in info.get("keywords", []) if kw in text_lower)
        scores[problem_class] = keyword_matches
    
    # Find best match from keyword heuristic
    if scores:
        best_class = max(scores, key=scores.get)
        if scores[best_class] > 0:
            # Confidence: matches relative to total keywords searched
            total_keywords_in_set = sum(len(PROBLEM_CLASS_KEYWORDS[cls].get("keywords", [])) 
                                       for cls in scores.keys())
            confidence = scores[best_class] / total_keywords_in_set if total_keywords_in_set > 0 else 0.0
            
            if confidence >= confidence_threshold:
                return best_class, min(confidence, 1.0)
    
    # If no strong match via keywords, try LLM fallback (skip in hybrid/demo mode)
    from backend.core.config import Config
    if Config.HYBRID_MODE or Config.DEMO_MODE:
        # Hybrid/demo: skip LLM, return best keyword match or general
        if scores:
            best_class = max(scores, key=scores.get)
            if scores[best_class] > 0:
                total_keywords_in_set = sum(len(PROBLEM_CLASS_KEYWORDS[cls].get("keywords", []))
                                           for cls in scores.keys())
                confidence = scores[best_class] / total_keywords_in_set if total_keywords_in_set > 0 else 0.0
                return best_class, min(confidence, 1.0)
        return "general", 0.3

    try:
        from backend.ai.llm_client import generate_json
        
        prompt = f"""Classify this project idea into ONE of these problem classes:

Problem Classes:
- "optimization": Finding best solution(s) under constraints (e.g., booth allocation, resource planning)
- "classification": Assigning inputs to predefined categories (e.g., spam detection, product categorization)
- "simulation": Modeling system behavior over time (e.g., traffic flow, market dynamics)
- "scheduling": Time/resource allocation under constraints (e.g., event scheduling, shift planning)
- "anomaly_detection": Finding outliers or abnormal patterns (e.g., fraud detection, system monitoring)
- "ranking": Ordering items by relevance/importance (e.g., search rankings, recommendation systems)
- "nlp": Natural language processing/generation (e.g., text analysis, chatbots, summarization)
- "general": Doesn't fit the above categories

Project Description:
{description}

Return JSON:
{{"problem_class": "one_of_above", "confidence": 0.0_to_1.0, "reasoning": "brief reason"}}"""
        
        response = generate_json(prompt, max_tokens=150, temperature=0.1)
        if isinstance(response, dict):
            problem_class = response.get("problem_class", "general")
            confidence = float(response.get("confidence", 0.0))
            
            if problem_class in PROBLEM_CLASS_KEYWORDS:
                return problem_class, min(confidence, 1.0)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("Problem-class LLM detection failed: %s", str(e))
    
    # Default: general
    return "general", 0.3


def detect_domain_intent(description: str) -> tuple[str, float, str, float]:
    """
    Detect both domain and problem-class intent from a description.
    Returns tuple: (domain, domain_confidence, problem_class, problem_class_confidence)
    
    Note: Suspended domains (Business, Social, Generic) are excluded from detection.
    If only suspended domains match, defaults to the best match from remaining active domains.
    """
    text = description.lower()

    # Domain detection with suspension filtering
    domain_scores = {
        domain: sum(1 for k in keywords if k in text)
        for domain, keywords in DOMAIN_PROFILES.items()
    }

    # Filter out suspended domains and find best active domain
    active_domain_scores = {
        domain: score for domain, score in domain_scores.items()
        if domain not in SUSPENDED_DOMAINS
    }
    
    # If there are active domains with scores, use them
    if active_domain_scores:
        best_domain = max(active_domain_scores, key=active_domain_scores.get)
        total = sum(active_domain_scores.values())
        domain_confidence = active_domain_scores[best_domain] / total if total else 0.0
    else:
        # Fallback: use best domain from all domains if nothing matches active ones
        best_domain = max(domain_scores, key=domain_scores.get)
        total = sum(domain_scores.values())
        domain_confidence = domain_scores[best_domain] / total if total else 0.0

    # Problem-class detection (new)
    problem_class, problem_class_confidence = detect_problem_class(description)

    return best_domain, round(domain_confidence, 2), problem_class, round(problem_class_confidence, 2)
