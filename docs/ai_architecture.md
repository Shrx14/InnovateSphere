# AI Architecture Documentation

## 1. Overview

InnovateSphere uses a **provider-agnostic LLM integration** with no dependency on LangChain or similar orchestration frameworks. All LLM interaction goes through a single `generate_json()` function that abstracts provider differences and guarantees structured JSON output.

**Active Configuration:**
- **Provider:** Ollama (local) with optional OpenAI fallback
- **Model:** qwen2.5:7b (default)
- **Embeddings:** all-MiniLM-L6-v2 (384-dim, sentence-transformers)
- **Active Mode:** Hybrid (2-pass) — the default for daily usage
- **Vector Storage:** PostgreSQL + pgvector

---

## 2. LLM Client Architecture

### Provider-Agnostic Interface

```
generate_json(prompt, system_prompt, max_tokens, temperature)
    ├── Config.LLM_PROVIDER == "ollama"  → _generate_ollama()
    ├── Config.LLM_PROVIDER == "openai"  → _generate_openai()
    └── On TransientLLMError + fallback enabled → retry with fallback provider
```

**Key design decisions:**
- Returns parsed Python `dict` — never raw text
- Robust JSON extraction from mixed LLM output (handles markdown fences, trailing text)
- Exponential backoff with jitter on transient failures
- Thread-safe Ollama health cache (30s TTL) and OpenAI client singleton
- Custom `TransientLLMError` exception with optional `trace_id` for audit trail

### Configuration (backend/.env)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `ollama` | Primary provider |
| `LLM_MODEL_NAME` | `qwen2.5:7b` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `LLM_TIMEOUT_SECONDS` | `60` | Request timeout |
| `LLM_MAX_RETRIES` | `4` | Retry count |
| `LLM_FALLBACK_ENABLED` | `false` | Enable provider fallback |
| `LLM_FALLBACK_PROVIDER` | `openai` | Fallback provider |

---

## 3. Generation Pipeline

### Three Operating Modes

| Mode | Passes | Retrieval | Novelty | Status |
|------|--------|-----------|---------|--------|
| Demo | 1-pass | Minimal | Skipped | Available |
| **Hybrid** | **2-pass** | **Live arXiv + GitHub** | **Skipped** | **Active default** |
| Production | 4-pass | Full + validation | Full analysis | Theoretical |

Mode is determined by `Config.get_active_mode()` which checks `DEMO_MODE` and `HYBRID_MODE` flags.

### Hybrid Mode Pipeline (Active)

```
User Input (problem_statement + domain)
    │
    ├── Phase 0: Input Conditioning
    │   └── Sanitize, validate, extract keywords
    │
    ├── Phase 1: Retrieval
    │   ├── arXiv API → academic papers
    │   ├── GitHub API → repositories
    │   └── Semantic filtering with threshold fallback
    │
    ├── Phase 2: LLM Pass 1 — Landscape + Problem Formulation
    │   └── PASS1_PROMPT_TEMPLATE → structured analysis
    │
    ├── Phase 3: LLM Pass 2 — Constraint Synthesis + Output
    │   └── PASS2_PROMPT_TEMPLATE → final idea JSON
    │
    └── Phase 4: Scoring + Persistence
        ├── Quality score computation
        ├── Hallucination risk assessment
        ├── Evidence strength calculation
        └── Save to ProjectIdea + IdeaSource + GenerationTrace
```

### Prompt Architecture

All prompts are stored in `backend/ai/prompts.py` with database-backed versioning via `PromptVersion` model. The system falls back to hardcoded defaults if no DB version exists.

**Prompt sets:**
- `PASS1_SYSTEM` / `PASS1_PROMPT_TEMPLATE` — Hybrid pass 1
- `PASS2_SYSTEM` / `PASS2_PROMPT_TEMPLATE` — Hybrid pass 2
- `PASS3_SYSTEM` / `PASS4_SYSTEM` — Production passes 3-4 (theoretical)
- `DIRECT_SYSTEM` / `DIRECT_PROMPT_TEMPLATE` — Demo mode single pass

---

## 4. Retrieval Pipeline

### Source Retrieval Orchestrator

```
retrieve_sources(query, domain)
    ├── arXiv API → search by relevance
    ├── GitHub API → search repositories
    └── Combined + deduplicated → raw_sources[]
```

### Semantic Filtering

```
filter_by_semantic_similarity(query, sources, threshold)
    ├── Embed query + source summaries → 384-dim vectors
    ├── Cosine similarity scoring
    ├── Progressive threshold fallback (threshold → threshold/2 → 0.1)
    └── Falls back to all raw sources if no filter passes
```

### Source Reputation

Each source gets a reputation weight based on provider (arXiv, GitHub) and metadata quality (citation count, stars, recency). Used in evidence strength calculation.

---

## 5. Embeddings & Semantic Search

### Embedding Model

- **Model:** `all-MiniLM-L6-v2` from sentence-transformers
- **Dimension:** 384
- **Storage:** PostgreSQL with pgvector extension
- **Caching:** Thread-safe LRU cache (max 5000 embeddings)

### Semantic Operations

| Operation | Module | Purpose |
|-----------|--------|---------|
| `get_embedding(text)` | `semantic/embeddings.py` | Text → 384-dim vector |
| `cosine_similarity(a, b)` | `semantic/similarity.py` | Vector comparison |
| `filter_by_semantic_similarity()` | `semantic/filter.py` | Source relevance filtering |
| `rank_sources()` | `semantic/ranker.py` | Multi-signal source ranking |

---

## 6. Novelty Scoring Engine

### Architecture

```
analyze_novelty(description, domain)
    ├── Cache check (SHA-256 key, 10-min TTL)
    ├── Domain intent routing → problem_class detection
    ├── NoveltyAnalyzer (lazy singleton)
    │   ├── Similarity signal (vs existing ideas in DB)
    │   ├── Specificity signal (description depth)
    │   ├── Temporal signal (recency of related work)
    │   └── Saturation signal (domain crowding)
    ├── Signal fusion → weighted score
    ├── Stabilization + normalization
    └── Persist to NoveltyBreakdown model
```

### Scoring Signals

| Signal | Weight | Source |
|--------|--------|--------|
| Similarity | Dynamic | Cosine distance to existing ideas |
| Specificity | Dynamic | Description length + technical depth |
| Temporal | Dynamic | Age of related work |
| Saturation | Dynamic | Domain idea density |

Results are persisted in the `NoveltyBreakdown` model with all intermediate scores for transparency.

---

## 7. AI Pipeline Versioning

### Database-Backed Versioning

The `AiPipelineVersion` model tracks pipeline configuration:
- Version identifier (e.g., `v2`)
- Generation mode mappings
- Active/inactive status
- Created/updated timestamps

The `BiasProfile` model stores versioned bias rules:
- Domain-specific scoring adjustments
- Source penalty weights
- HITL constraint overrides

Active versions are resolved by `get_active_ai_pipeline_version()` and `get_active_bias_profile()` from the AI registry.

---

## 8. Quality & Hallucination Assessment

### Quality Score Computation

Quality scores are computed during generation based on:
- Evidence strength (source count, relevance, reputation)
- Response completeness (all required fields present)
- Technical depth (specificity of tech stack, problem statement)
- Source-claim alignment

### Hallucination Risk Levels

| Level | Criteria |
|-------|----------|
| Low | 3+ high-relevance sources, strong evidence alignment |
| Medium | 1-2 sources or moderate alignment |
| High | No sources or weak alignment, generic responses |

---

## 9. HITL (Human-in-the-Loop) Integration

Admin verdicts cascade through the scoring system:
- **Validated:** Boosts quality score of similar ideas
- **Downgraded:** Applies penalty to similar ideas
- **Rejected:** Flags pattern for future generation constraints

The `GenerationTrace` model provides full audit trail of all pipeline phases (0-4), constraints applied, bias penalties, and timing for admin review.

---

## 10. Public vs Authenticated Content Access

### Access Rules

**Anonymous Users (No Auth):**
- View public idea listings via `GET /api/public/ideas`
- Search by keyword and domain
- View limited idea details (id, title, problem_statement, tech_stack, domain)
- Cannot see sources, reviews, scores, or submit feedback

**Authenticated Users (JWT Required):**
- Full idea details including sources and reviews
- Submit reviews (1-5 rating + comment, one per user per idea)
- Submit idea requests (demand tracking)
- Submit structured feedback (12 types)
- Generate new ideas

### Response Shaping

- `serialize_public_idea()` — limited fields + `requires_login: true`
- `serialize_full_idea()` — all fields including computed metrics
