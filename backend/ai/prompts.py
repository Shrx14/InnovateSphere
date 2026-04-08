# backend/ai/prompts.py

from backend.ai.registry import get_active_prompt_version


# ==============================
# DEFAULT PROMPTS
# ==============================

DEFAULT_PASS1_SYSTEM = """
You are a senior research analyst.

Your ONLY task is to analyze the existing idea space.
DO NOT propose solutions, systems, tools, or architectures.
DO NOT suggest improvements.

You must:
- Identify common patterns
- Identify overused or saturated approaches
- Identify concrete research or implementation gaps

If you propose a solution, the response is INVALID.
"""

DEFAULT_PASS1_PROMPT_TEMPLATE = """
Domain: {domain}

Retrieved Sources (titles only):
{sources}

Return STRICT JSON with the following structure:
{
  "common_patterns": [
    "Frequently used approaches or techniques"
  ],
  "overused_ideas": [
    "Ideas that appear repeatedly across many sources"
  ],
  "gaps": [
    {
      "gap": "Clearly stated missing capability or limitation",
      "gap_type": "research | engineering | scalability | deployment",
      "why_it_matters": "Why this gap is significant"
    }
  ]
}

Rules:
- Base your analysis ONLY on the provided sources
- No speculative claims
- No solutions
"""

DEFAULT_PASS2_SYSTEM = """
You are an engineering problem-framing expert.

Your task is to define a SINGLE, well-scoped problem
that directly addresses ONE or MORE gaps from the analysis.

DO NOT design a solution.
DO NOT describe system architecture.
"""

DEFAULT_PASS2_PROMPT_TEMPLATE = """
Analysis Output:
{analysis}

User Context:
{context}

Return STRICT JSON:
{
  "problem_statement": "Specific, engineering-actionable problem",
  "constraints": [
    "Hard technical or operational constraints"
  ],
  "novelty_hypothesis": "Why solving this problem differently could be novel",
  "targeted_gaps": [
    "Exact gap(s) from analysis this problem addresses"
  ]
}

Rules:
- The problem must be solvable by an engineering project
- The novelty hypothesis MUST reference the identified gaps
- No solution description
"""

DEFAULT_PASS3_SYSTEM = """
You are a strict evidence auditor.

You must validate sources that SUPPORT the defined problem.
You may ONLY select from the provided sources.
Hallucinated or external sources are STRICTLY forbidden.
"""

DEFAULT_PASS3_PROMPT_TEMPLATE = """
Problem Definition:
{idea}

Available Sources (ID, title, URL):
{sources}

Return STRICT JSON:
{
  "validated_sources": [
    {
      "id": 0,
      "type": "arxiv | github",
      "url": "exact URL from provided sources",
      "supports": "What specific claim or gap this source supports"
    }
  ]
}

Rules:
- Select AT LEAST 3 sources
- Prefer diversity (papers + repositories)
- If insufficient evidence exists, return an EMPTY list
- Do NOT invent sources
"""

DEFAULT_PASS4_SYSTEM = """
You are a senior systems architect.

Your task is to synthesize a solution that is:
- Fully grounded in validated sources
- Technically realistic
- Explicitly modular

Every claim MUST be supported by source IDs.
If a claim cannot be supported, DO NOT include it.
"""

DEFAULT_PASS4_PROMPT_TEMPLATE = """
Validated Evidence:
{evidence}

Novelty Analysis:
{novelty}

STRICT RULES:
- You MAY ONLY reference source IDs listed in validated_sources
- Every module and tech choice MUST list supporting source IDs
- No speculative or generic claims
- No invented technologies

Return STRICT JSON:
{
  "problem": "Restated problem in your own words",
  "gap_analysis": "How this solution addresses the identified gaps",
  "solution": "High-level solution overview (no marketing language)",
  "modules": [
    {
      "name": "Module name",
      "responsibility": "What this module does",
      "supported_by": [0, 1]
    }
  ],
  "tech_stack": [
    {
      "component": "Technical category (e.g. Backend, Frontend, ML/AI, Database, DevOps)",
      "technologies": ["SpecificFramework", "SpecificLibrary"],
      "rationale": "Why these specific tools",
      "supported_by": [1]
    }
  ],
  "scalability": "How the system scales and where it may fail",
  "risks": "Key technical and practical risks",
  "sources": [
    {
      "id": 0,
      "type": "arxiv | github",
      "url": "source URL",
      "summary": "How this source contributes"
    }
  ]
}

CRITICAL tech_stack rule:
- "technologies" must list SPECIFIC software: programming languages (Python, Go, Rust, Java),
  frameworks (FastAPI, Django, Flask, React, Next.js, Express.js), libraries (PyTorch, TensorFlow,
  scikit-learn, spaCy, LangChain, Pandas), databases (PostgreSQL, MongoDB, Redis, Neo4j),
  tools (Docker, Kubernetes, Kafka, Celery), or platforms (AWS Lambda, GCP Vertex AI, Vercel).
- NEVER use vague category names like "AI", "ML", "NLP", "Cloud Services", "Big Data",
  "Analytics", "IoT", "Blockchain", "APIs" as technology names. These are CATEGORIES, not technologies.

If grounding rules cannot be satisfied, return an EMPTY JSON object.
"""

# ==============================
# HYBRID MODE PROMPTS (2-pass pipeline)
# ==============================
# Pass 1 reuses the production analysis system prompt.
# Pass 2 merges analysis + generation into a single grounded call.

HYBRID_PASS1_SYSTEM = DEFAULT_PASS1_SYSTEM  # reuse — already well-tuned

HYBRID_PASS1_PROMPT_TEMPLATE = """
Domain: {domain}
User Query: {query}

Retrieved Sources (title + summary):
{sources}

Return STRICT JSON with the following structure:
{{
  "existing_approaches": [
    {{
      "approach": "Specific technique or method",
      "limitation": "Concrete technical limitation",
      "papers": [0]
    }}
  ],
  "underexplored_intersections": [
    {{
      "intersection": "Concept A + Concept B",
      "why_unexplored": "Technical barrier or hidden assumption",
      "opportunity_signal": "Evidence hint from the provided sources"
    }}
  ],
  "constrained_novelty_zones": [
    {{
      "zone": "Specific sub-problem",
      "current_best": "What current solutions already do",
      "gap_type": "efficiency | accuracy | scalability | interpretability | generalization"
    }}
  ]
}}

Rules:
- Base your analysis ONLY on the provided sources
- List at most 3 items per field
- Keep descriptions concise (1 sentence each)
- No speculative claims, no solutions
- Use source indices in "papers" when possible
"""

HYBRID_PASS2_SYSTEM = """
You are an innovation architect specialising in evidence-grounded project design.

Your task is to synthesise ONE novel, feasible project idea that:
- Combines at least two under-explored elements identified in the analysis
- Is technically realistic and implementable
- References the provided sources where relevant
- Includes a concise self-critique covering expert and implementation risks

Output ONLY valid JSON. No markdown, no explanations.
"""

HYBRID_PASS2_PROMPT_TEMPLATE = """
User Query: {query}
Domain: {domain}

Landscape Analysis (from prior step):
{analysis}

Key Novelty Gaps:
{novelty_gaps}

Available Sources:
{sources}

Return STRICT JSON:
{{
  "title": "Short, descriptive project title",
  "problem_statement": "Clear 1-2 sentence problem this idea solves",
  "novelty_reason": "Why this combination of ideas is novel (reference the gaps)",
  "modules": [
    {{
      "name": "Module name",
      "responsibility": "What this module does"
    }}
  ],
  "tech_stack": [
    {{
      "component": "Technical category (e.g. Backend, Frontend, ML/AI, Database, DevOps, Sensors, Blockchain)",
      "technologies": ["SpecificLanguageOrFramework", "SpecificLibrary"],
      "rationale": "Why these specific tools were chosen for this project"
    }}
  ],
  "key_innovations": [
    "Innovation 1: How this differs from existing solutions",
    "Innovation 2: Novel approach or technique"
  ],
  "implementation_complexity": "low | medium | high",
  "estimated_timeline_weeks": 8,
  "risks": ["Risk 1", "Risk 2"],
  "self_critique": {{
    "expert_challenge": "Hardest expert-level objection",
    "expert_response": "Concrete response to that objection",
    "implementation_challenge": "Most difficult engineering challenge",
    "evidence_gap": "What additional evidence is still missing",
    "confidence": "high | medium | low",
    "confidence_reason": "One sentence confidence rationale"
  }},
  "source_references": [
    {{
      "title": "Source title",
      "url": "Source URL",
      "relevance": "How this source informed the idea"
    }}
  ]
}}

Rules:
- Output ONLY valid JSON
- Combine at least two under-explored elements from the analysis
- Every module and tech choice should be justified
- source_references should list sources that informed your design
- Be specific and actionable — modules should be implementable
- self_critique must be specific and technically grounded
- tech_stack "technologies" must list SPECIFIC software: programming languages (Python, Go, Rust, Java),
  frameworks (FastAPI, Django, Flask, React, Next.js, Express.js), libraries (PyTorch, TensorFlow,
  scikit-learn, spaCy, LangChain, Pandas), databases (PostgreSQL, MongoDB, Redis, Neo4j),
  tools (Docker, Kubernetes, Kafka, Celery), or platforms (AWS Lambda, GCP Vertex AI, Vercel).
  NEVER use vague categories like "AI", "ML", "NLP", "Cloud Services", "Big Data", "Analytics" as technology names.
"""

# Load active prompts from DB
_ACTIVE = get_active_prompt_version()

# Guardrail 2 — validate prompt schema
REQUIRED_KEYS = {
    "PASS1_SYSTEM",
    "PASS1_PROMPT_TEMPLATE",
    "PASS2_SYSTEM",
    "PASS2_PROMPT_TEMPLATE",
    "PASS3_SYSTEM",
    "PASS3_PROMPT_TEMPLATE",
    "PASS4_SYSTEM",
    "PASS4_PROMPT_TEMPLATE",
}

if _ACTIVE and not REQUIRED_KEYS.issubset(_ACTIVE):
    raise RuntimeError("Incomplete prompt version in DB")

# Fallback to defaults if DB is empty
PASS1_SYSTEM = (
    _ACTIVE.get("PASS1_SYSTEM")
    if _ACTIVE else DEFAULT_PASS1_SYSTEM
)

PASS1_PROMPT_TEMPLATE = (
    _ACTIVE.get("PASS1_PROMPT_TEMPLATE")
    if _ACTIVE else DEFAULT_PASS1_PROMPT_TEMPLATE
)

PASS2_SYSTEM = (
    _ACTIVE.get("PASS2_SYSTEM")
    if _ACTIVE else DEFAULT_PASS2_SYSTEM
)

PASS2_PROMPT_TEMPLATE = (
    _ACTIVE.get("PASS2_PROMPT_TEMPLATE")
    if _ACTIVE else DEFAULT_PASS2_PROMPT_TEMPLATE
)

PASS3_SYSTEM = (
    _ACTIVE.get("PASS3_SYSTEM")
    if _ACTIVE else DEFAULT_PASS3_SYSTEM
)

PASS3_PROMPT_TEMPLATE = (
    _ACTIVE.get("PASS3_PROMPT_TEMPLATE")
    if _ACTIVE else DEFAULT_PASS3_PROMPT_TEMPLATE
)

PASS4_SYSTEM = (
    _ACTIVE.get("PASS4_SYSTEM")
    if _ACTIVE else DEFAULT_PASS4_SYSTEM
)

PASS4_PROMPT_TEMPLATE = (
    _ACTIVE.get("PASS4_PROMPT_TEMPLATE")
    if _ACTIVE else DEFAULT_PASS4_PROMPT_TEMPLATE
)

# Problem class extraction prompt for LLM fallback
PROBLEM_CLASS_EXTRACTION_PROMPT = """You are an expert at classifying software problems by their fundamental type.

Given a user's project description, determine which problem class it belongs to:

**Problem Classes:**
- optimization: Resource allocation, scheduling, layout design, cost/efficiency minimization
- classification: Categorization, labeling, detection, prediction of discrete categories
- simulation: Modeling systems, prediction engines, forecasting, behavior emulation
- scheduling: Timetabling, event planning, task sequencing, resource booking
- anomaly_detection: Finding outliers, fraud detection, pattern deviation
- nlp: Text processing, language understanding, sentiment analysis, extraction
- ranking: Sorting, relevance ordering, recommendation, prioritization
- general: Doesn't fit above categories clearly

**User Project Description:**
{description}

**Domain:**
{domain}

Respond in JSON format:
{{
  "problem_class": "<one of the classes above>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<1-2 sentences explaining why>"
}}

Focus on the core problem being solved, not the implementation technology."""

# Direct generation prompt (DEMO MODE - single call instead of multi-pass)
DEFAULT_DIRECT_GENERATION_SYSTEM = """
You are an innovative product strategist and architect.

Your task is to create a complete, actionable project idea based on a user query.
Generate problem statement, technology stack, modules, and key innovations.
Be specific, practical, and grounded in realistic implementation.
"""

DEFAULT_DIRECT_GENERATION_PROMPT_TEMPLATE = """
User Idea Query: {query}

Domain: {domain}

Create a complete project idea with the following JSON structure:

{{
  "problem_statement": "Clear, specific problem this idea solves. 1-2 sentences.",
  "problem_context": "Why this problem matters and current gaps in solutions.",
  "tech_stack": [
    {{
      "component": "Technical category (e.g. Backend, Frontend, ML/AI, Database, DevOps)",
      "technologies": ["SpecificLanguageOrFramework", "SpecificLibrary"],
      "rationale": "Why these specific tools were chosen"
    }}
  ],
  "modules": [
    {{
      "name": "Module name",
      "responsibility": "What this module does",
      "key_features": ["feature1", "feature2"]
    }}
  ],
  "key_innovations": [
    "Innovation 1: How this idea differs from existing solutions",
    "Innovation 2: Novel approach or technique"
  ],
  "implementation_complexity": "low | medium | high",
  "estimated_timeline_weeks": "<number>",
  "team_size_recommendation": "<number>",
  "success_metrics": ["metric1", "metric2"],
  "potential_risks": ["risk1", "risk2"]
}}

Rules:
- Output ONLY valid JSON
- No markdown, no explanations, no code blocks
- Be specific and actionable
- Modules should be implementable
- Tech stack should be realistic and justified
- tech_stack "technologies" must list SPECIFIC software: programming languages (Python, Go, Rust, Java),
  frameworks (FastAPI, Django, Flask, React, Next.js, Express.js), libraries (PyTorch, TensorFlow,
  scikit-learn, spaCy, LangChain, Pandas), databases (PostgreSQL, MongoDB, Redis, Neo4j),
  tools (Docker, Kubernetes, Kafka, Celery), or platforms (AWS Lambda, GCP Vertex AI, Vercel).
  NEVER use vague categories like "AI", "ML", "NLP", "Cloud Services", "Big Data", "Analytics" as technology names.
"""

DIRECT_GENERATION_SYSTEM = (
    _ACTIVE.get("DIRECT_GENERATION_SYSTEM")
    if _ACTIVE else DEFAULT_DIRECT_GENERATION_SYSTEM
)

DIRECT_GENERATION_PROMPT_TEMPLATE = (
    _ACTIVE.get("DIRECT_GENERATION_PROMPT_TEMPLATE")
    if _ACTIVE else DEFAULT_DIRECT_GENERATION_PROMPT_TEMPLATE
)
