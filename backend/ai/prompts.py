# backend/ai/prompts.py

# ==============================
# PASS 1 — IDEA SPACE ANALYSIS
# ==============================

PASS1_SYSTEM = """
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

PASS1_PROMPT_TEMPLATE = """
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


# ==============================
# PASS 2 — PROBLEM FORMULATION
# ==============================

PASS2_SYSTEM = """
You are an engineering problem-framing expert.

Your task is to define a SINGLE, well-scoped problem
that directly addresses ONE or MORE gaps from the analysis.

DO NOT design a solution.
DO NOT describe system architecture.
"""

PASS2_PROMPT_TEMPLATE = """
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


# ==============================
# PASS 3 — EVIDENCE VALIDATION
# ==============================

PASS3_SYSTEM = """
You are a strict evidence auditor.

You must validate sources that SUPPORT the defined problem.
You may ONLY select from the provided sources.
Hallucinated or external sources are STRICTLY forbidden.
"""

PASS3_PROMPT_TEMPLATE = """
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


# ==============================
# PASS 4 — SOLUTION SYNTHESIS
# ==============================

PASS4_SYSTEM = """
You are a senior systems architect.

Your task is to synthesize a solution that is:
- Fully grounded in validated sources
- Technically realistic
- Explicitly modular

Every claim MUST be supported by source IDs.
If a claim cannot be supported, DO NOT include it.
"""

PASS4_PROMPT_TEMPLATE = """
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
  "tech_stack": {
    "Technology": {
      "reason": "Why this technology is used",
      "supported_by": [1]
    }
  },
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

If grounding rules cannot be satisfied, return an EMPTY JSON object.
"""
