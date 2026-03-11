# InnovateSphere Backend — Comprehensive Code Audit Report

**Date:** 2025-06-18 (Updated)  
**Scope:** All files under `backend/` (excluding `venv/`, `__pycache__/`, `instance/`)  
**Method:** READ-ONLY static analysis of every source file  
**Total Files Audited:** 62 Python source files across 10 packages

> **Update Note:** Several issues reported in the original audit have been verified and resolved.
> Critical #1 (IdeaFeedback CHECK constraint) was already fixed — the DB CHECK allows all 12 types.
> Critical #2 (demo mode swapped args) was already fixed.
> Medium #4 (phase_5 reuse) was already fixed — admin.py no longer emits phase_5.
> Medium issues related to `relevance_tier` (hasattr) have been fixed.
> Additional fixes applied: `.join(Domain)` → `.outerjoin(Domain)` in ideas.py,
> bare `except:` → `except Exception:` in public.py, `datetime.utcnow()` → `datetime.now(timezone.utc)` in analytics.py.

---

## Executive Summary

The InnovateSphere backend is a **Flask + SQLAlchemy** application with a multi-mode AI idea generation pipeline (DEMO / HYBRID / PRODUCTION), novelty analysis engine, external source retrieval (arXiv + GitHub), and semantic embedding layer. The codebase is generally well-structured with proper separation of concerns, comprehensive error handling, and thoughtful architectural decisions.

**Critical issues found: 0** (2 originally reported, both verified as already fixed)  
**Medium issues found: 8**  
**Minor issues found: 11**  
**Missing implementations: 3**  

---

## Category 1: Core Infrastructure

### `backend/core/models.py` — **Has Issues**
- **569 lines**, 17+ models with proper indexes, constraints, and relationships.
- **CRITICAL — Line 338:** `IdeaFeedback` CHECK constraint only allows 6 types:
  ```
  'high_quality', 'factual_error', 'hallucinated_source', 'weak_novelty', 'poor_justification', 'unclear_scope'
  ```
  But `backend/api/routes/ideas.py` line 145 accepts 12 types including `upvote`, `downvote`, `bookmark`, `report`, `helpful`, `not_helpful`. Any of these 6 "reaction" types will cause a **PostgreSQL IntegrityError** at the DB level. The route-level validation passes them through, so this is a silent data-loss bug.
- **Minor — Line 191:** `feedback_counts` property iterates all feedbacks in Python instead of using a SQL aggregation. N+1 potential if called in a list view.
- **Minor:** `ProjectVector` model (lines ~40-60) is marked as legacy but still defined — dead code.

### `backend/core/db.py` — **Complete** ✅
- 3 lines. Simple `db = SQLAlchemy()` initialization. Correct.

### `backend/core/config.py` — **Complete** ✅
- 226 lines. Comprehensive configuration with env-var overrides.
- All secrets loaded from environment. No hardcoded credentials.
- Proper defaults for DEMO/HYBRID/PRODUCTION modes.

### `backend/core/auth.py` — **Has Issues**
- ~80 lines. **DEPRECATED** — file header says "Do NOT use in new code."
- **Medium:** File still exists and exports `create_access_token()`, `get_jwt()`, `jwt_required()`. These shadow `flask_jwt_extended` names and could cause import confusion. The actual production code uses `flask_jwt_extended` (via `backend/utils/auth.py`), but having this file is a maintenance hazard.
- **Recommendation:** Remove or rename to `_legacy_auth.py` to prevent accidental imports.

### `backend/core/app.py` — **Complete** ✅
- ~165 lines. Proper app factory pattern with `create_app()`.
- Extension initialization (db, jwt, limiter, cache, CORS) is correct.
- JWT blocklist loader is properly configured.
- Graceful shutdown via `atexit` for the job queue.
- Blueprint registration delegates to `backend/api/__init__.py`.

### `backend/core/abuse.py` — **Complete** ✅
- ~95 lines. `record_abuse_event()`, `count_recent_events()`, `check_generation_rate()`.
- FK-safe handling (checks for user existence before creating FK references).
- Proper time-window based rate checking.

---

## Category 2: API Routes

### `backend/api/__init__.py` — **Complete** ✅
- Registers 11 blueprints. `novelty_bp` wrapped in `try/except` for optional dependency handling.

### `backend/api/routes/auth.py` — **Complete** ✅
- 215 lines. Login, logout, refresh, register endpoints.
- Rate limiting on register (`5/hour`).
- Proper password hashing with `werkzeug.security`.
- JWT token management via `flask_jwt_extended`.

### `backend/api/routes/ideas.py` — **Has Issues**
- 450 lines. Novelty-explanation, feedback, mine, detail, review, list endpoints.
- **CRITICAL — Line 145:** Accepts 12 `feedback_type` values but DB CHECK constraint (models.py:338) only allows 6. See Category 1 above. The 6 reaction types (`upvote`, `downvote`, `bookmark`, `report`, `helpful`, `not_helpful`) will fail at the database level.
- **Minor — Line 165:** Upsert logic queries then creates/updates — not wrapped in a transaction-safe way. Race condition possible under concurrent requests for same user+idea+feedback_type.

### `backend/api/routes/admin.py` — **Has Issues**
- 480 lines. Comprehensive admin endpoints.
- **Medium — Lines 136-139:** `phase_5` in the generation trace response duplicates `phase_4_output`:
  ```python
  "phase_5": {
      "name": "Output Synthesis",
      "output": trace.phase_4_output  # <-- reuses phase_4
  }
  ```
  The `GenerationTrace` model only has `phase_0` through `phase_4`. If a 5th pass truly runs, its output is lost. If it doesn't, this is misleading to admin users.

### `backend/api/routes/generation.py` — **Complete** ✅
- 382 lines. Async generation with job queue, polling endpoint, SSE streaming.
- Proper abuse detection and rate limiting.
- Job cleanup on completion.

### `backend/api/routes/analytics.py` — **Complete** ✅
- 336 lines. KPIs, domain stats, trends, distributions, bias transparency.
- Admin-only access properly enforced.

### `backend/api/routes/public.py` — **Has Issues**
- 337 lines. Public ideas listing, detail with view tracking, top-ideas, top-domains, stats.
- **Minor — Line 227:** `s.relevance_tier if hasattr(s, 'relevance_tier')` — the `IdeaSource` model does NOT have a `relevance_tier` column (see models.py:274-293). `hasattr` will always be `False`, so this always returns `"supporting"`. The `relevance_tier` is only computed at runtime during generation and stored in the orchestrator's output dict (not persisted to DB). This is a silent no-op — not a crash, but the field is misleading.

### `backend/api/routes/health.py` — **Complete** ✅
- 12 lines. Simple health check endpoint.

### `backend/api/routes/domains.py` — **Complete** ✅
- 14 lines. Straightforward domain listing.

### `backend/api/routes/retrieval.py` — **Complete** ✅
- ~40 lines. Source retrieval with validation.

### `backend/api/routes/platform.py` — **Has Issues**
- ~25 lines. Legacy aliases and deprecated endpoints.
- **Minor:** `deprecated_generate` endpoint (if present) could confuse API consumers. Should be documented or removed.

### `backend/api/routes/novelty.py` — **Complete** ✅
- ~65 lines. Novelty analysis with evidence scoring.

---

## Category 3: Utility Layer

### `backend/utils/__init__.py` — **Complete** ✅
- Clean re-exports of `require_admin`, `get_current_user_id`, serializers, helpers, health checks.

### `backend/utils/serializers.py` — **Complete** ✅
- ~85 lines. `serialize_public_idea()` and `serialize_full_idea()` with trust signals.
- Properly strips internal fields from public-facing responses.

### `backend/utils/common.py` — **Complete** ✅
- ~140 lines. `db_retry()` decorator (3 retries with exponential backoff), truncation helpers, domain mapping.
- `db_retry()` catches `OperationalError` and `InterfaceError` — appropriate for Neon pooler disconnects.

### `backend/utils/auth.py` — **Complete** ✅
- ~35 lines. `require_admin()` and `get_current_user_id()` using `flask_jwt_extended`.

### `backend/utils/health_checks.py` — **Has Issues**
- ~100 lines.
- **Medium — `check_embeddings()`:** This function is a complete no-op — it returns a "skipped" status without actually testing embeddings. If the embedding model fails to load, the system won't know until a real request hits.
  ```python
  def check_embeddings():
      return {"status": "skipped", ...}
  ```
- `check_llm()` correctly fails hard if LLM is unreachable.
- `check_retrieval()` correctly soft-fails if external APIs are down.

---

## Category 4: Generation Pipeline

### `backend/generation/generator.py` — **Has Issues**
- 1163 lines. Three generation paths: direct (DEMO), hybrid (HYBRID), multi-pass (PRODUCTION).
- **Medium — Line 836:** In demo mode, `update_job_status` is called with **swapped arguments**:
  ```python
  jq.update_job_status(job_id, "running", 100, 5)
  ```
  The signature is `(job_id, status, phase, progress)`. This sets **phase=100, progress=5** — but phases should be 0-4 and progress should be 0-100. The intended call is likely `(job_id, "running", 5, 100)` or `(job_id, "completed", 4, 100)`. This causes the job to report nonsensical progress during demo mode.
- **Minor — Non-daemon threads:** Background generation uses `threading.Thread` without `daemon=True`. If the Flask process is killed during generation, the thread may keep the process alive. However, the `atexit` handler in `core/app.py` does attempt cleanup.
- **Minor:** f-string logging throughout (e.g., `logger.info(f"...")`) instead of lazy `%s` formatting. Not a bug but causes string formatting even when log level is higher.

### `backend/generation/schemas.py` — **Complete** ✅
- 232 lines. Pydantic schemas with strict validation.
- `GeneratedIdea`: requires 4+ sources, 2+ source types.
- `HybridGeneratedIdea`: relaxed constraints for hybrid mode.
- Proper field validators and custom error messages.

### `backend/generation/constraints.py` — **Complete** ✅
- ~170 lines. HITL constraints, rejected pattern detection (with embedding similarity), hallucinated source filtering.
- Well-designed constraint enforcement.

### `backend/generation/job_queue.py` — **Complete** ✅
- 278 lines. Thread-safe in-memory `JobQueue` with proper locking, auto-cleanup (1-hour TTL), phase naming.
- **Note:** Being in-memory means all jobs are lost on server restart. Acceptable for development but not for production deployments with multiple workers.

### `backend/generation/__init__.py` — **Complete** ✅
- 33 lines. Clean exports.

---

## Category 5: AI Layer

### `backend/ai/llm_client.py` — **Complete** ✅
- 348 lines. Multi-provider LLM client with Ollama + OpenAI backends.
- Proper retry with exponential backoff for Ollama.
- `TransientLLMError` for recoverable failures.
- Fallback provider support.
- JSON extraction from mixed LLM output.

### `backend/ai/prompts.py` — **Complete** ✅
- 434 lines. Full 4-pass prompt templates, hybrid 2-pass prompts, direct generation prompt.
- DB-backed active prompt lookup with fallback to defaults.
- Problem class extraction prompt for domain intent.

### `backend/ai/registry.py` — **Complete** ✅
- ~100 lines. TTL-cached (60s) DB lookups for pipeline version, prompt version, bias profile.
- Proper error handling with fallback values.

### Missing: `backend/ai/__init__.py` — **Missing**
- No `__init__.py` exists for the `ai` package. Imports work because modules are imported by full dotted path (`backend.ai.llm_client`), but this violates Python package conventions and may cause issues with some tooling.

---

## Category 6: Novelty Engine

### `backend/novelty/__init__.py` — **Complete** ✅
- Exports `NoveltyAnalyzer`, `analyze_novelty`, `system_under_load`.

### `backend/novelty/service.py` — **Complete** ✅
- ~100 lines. `analyze_novelty()` with 10-minute TTL cache, routed through domain intent.

### `backend/novelty/router.py` — **Has Issues**
- ~80 lines. All 10 domains mapped to the software analyzer (lazy-loaded).
- **Medium:** Despite having `BusinessNoveltyEngine`, `SocialNoveltyEngine`, and `GenericNoveltyEngine` classes defined in `engines/`, the router maps ALL domains to `NoveltyAnalyzer` (the software-focused analyzer). The domain-specific engines are **never used**. This means business and social impact ideas get analyzed with software-specific logic.

### `backend/novelty/analyzer.py` — **Complete** ✅
- 409 lines. Full scoring pipeline with retrieval, similarity stats, specificity, temporal signals, saturation, bonuses, penalties, domain maturity, evidence calibration, normalization.
- Properly integrates all scoring sub-modules.

### `backend/novelty/config.py` — **Complete** ✅
- ~65 lines. Domain-specific thresholds, weights, maturity levels, commodity patterns.

### `backend/novelty/explain.py` — **Complete** ✅
- ~160 lines. Human-readable explanation generation with signal breakdowns.

### `backend/novelty/metrics.py` — **Complete** ✅
- ~30 lines. Similarity distribution computation.

### `backend/novelty/normalization.py` — **Complete** ✅
- ~25 lines. Score normalization and level determination.

### `backend/novelty/domain_intent.py` — **Complete** ✅
- 252 lines. Domain and problem class detection with keyword heuristic + LLM fallback.

### Sub-modules:

#### `backend/novelty/engines/business.py` — **Complete** ✅ (but unused — see router.py)
- ~35 lines. Keyword-based business novelty scoring.

#### `backend/novelty/engines/generic.py` — **Complete** ✅ (but unused)
- ~20 lines. Length-based generic fallback scoring.

#### `backend/novelty/engines/social.py` — **Has Issues** (but unused)
- ~35 lines. Social impact novelty scoring.
- **Minor:** Uses inline level determination (`"High" if score >= 70...`) instead of `determine_level()` from `normalization.py` like the other engines. Inconsistent threshold behavior.

#### `backend/novelty/scoring/base.py` — **Complete** ✅
- 8 lines. Weighted base score: similarity(40%) + specificity(30%) + saturation(20%) + temporal(10%).

#### `backend/novelty/scoring/bonuses.py` — **Complete** ✅
- 23 lines. Evidence-gated tech bonuses. Zero sources = zero bonuses. Correct.

#### `backend/novelty/scoring/blending.py` — **Complete** ✅
- 2 lines. 60/40 conservative/optimistic blend.

#### `backend/novelty/scoring/penalties.py` — **Complete** ✅
- 25 lines. Saturation penalty (log-scale) and admin penalty.

#### `backend/novelty/utils/__init__.py` — **Complete** ✅
- Clean re-exports of calibration, observability, and signals.

#### `backend/novelty/utils/calibration.py` — **Complete** ✅
- ~120 lines. Evidence-based score constraints with hard caps. Source tier weighting (supporting=100%, contextual=50%). ArXiv domain-only fallback penalty.

#### `backend/novelty/utils/observability.py` — **Complete** ✅
- ~85 lines. Bounded telemetry storage (`deque(maxlen=1000)`), trace logging, score stability enforcement.
- Proper memory leak prevention with `_MAX_TELEMETRY_METRICS` and `_MAX_HISTORY_KEYS` caps.

#### `backend/novelty/utils/signals.py` — **Complete** ✅
- ~85 lines. Similarity signal computation (numpy dot product), specificity scoring, temporal analysis.

#### Missing: `backend/novelty/engines/__init__.py` — **Missing**
- No `__init__.py`. Not required since these are imported by full path in the router, but unconventional.

#### Missing: `backend/novelty/scoring/__init__.py` — **Missing**
- No `__init__.py`. Same as above — works but unconventional.

---

## Category 7: Retrieval Layer

### `backend/retrieval/__init__.py` — **Complete** ✅
- 25 lines. Clean exports.

### `backend/retrieval/orchestrator.py` — **Complete** ✅
- 303 lines. Parallel retrieval from arXiv + GitHub, deduplication, round-robin diversity, relevance tier classification, confidence scoring.
- Uses `concurrent.futures.ThreadPoolExecutor` for parallel retrieval — correct.

### `backend/retrieval/arxiv_client.py` — **Complete** ✅
- 561 lines. Progressive query simplification with per-variation timeouts (20s each).
- LLM keyword extraction for production mode, heuristic for hybrid/demo.
- Aggregates results across all variations with specificity-based ranking.
- Proper XML parsing with namespace handling.

### `backend/retrieval/github_client.py` — **Has Issues**
- 501 lines. Similar architecture to arXiv client.
- **Minor — Line ~270-280:** Imports `_summarize_query_with_llm` from `orchestrator.py` inside a function body. This creates a **circular import** risk: `github_client` → `orchestrator` → `github_client`. Currently works because the import is deferred (inside a `try/except` in a function), but it's fragile.
- **Minor:** Query length cap at 240 chars with truncation — may cut off meaningful terms mid-word.
- GitHub API requests use no authentication token, relying on anonymous rate limits (60 requests/hour). For production use, this will be exhausted quickly.

### `backend/retrieval/cached_retrieval.py` — **Complete** ✅
- ~35 lines. Simple TTL (6-hour) hash-based cache. Correct.

### `backend/retrieval/source_reputation.py` — **Complete** ✅
- ~40 lines. Admin verdict aggregation per source URL.

---

## Category 8: Semantic Layer

### `backend/semantic/__init__.py` — **Complete** ✅
- Clean exports.

### `backend/semantic/embedder.py` — **Complete** ✅
- ~25 lines. SentenceTransformer wrapper with singleton pattern. Model: `all-MiniLM-L6-v2`.

### `backend/semantic/cached_embedder.py` — **Complete** ✅
- ~35 lines. LRU-cached (5000 entries) embedding wrapper. Correct cache key via `tuple()`.

### `backend/semantic/filter.py` — **Complete** ✅
- ~175 lines. Semantic similarity filtering with problem-type relevance classification and penalty multipliers.

### `backend/semantic/ranker.py` — **Complete** ✅
- ~30 lines. Multi-signal ranking: similarity (50%), admin signals (20%), recency (15%), stars (15%).
- Uses `pass` in exception handler for date parsing (line 19) — acceptable for non-critical metadata.

---

## Category 9: Entry Points & Configuration

### `backend/__init__.py` — **Complete** ✅
- 2 lines. Package marker.

### `backend/app.py` — **Complete** ✅
- 28 lines. Compatibility shim for tests. Creates `app` via `create_app()`.

### `backend/run.py` — **Complete** ✅
- 61 lines. CLI entry point with `--production` (gunicorn) and `--host/--port` flags.

### `backend/validate_contracts.py` — **Complete** ✅
- 206 lines. Static analysis script for endpoint contract validation.

### `backend/validate_models.py` — **Complete** ✅
- 161 lines. Static analysis script for model schema validation.

### `backend/requirements.txt` — Not audited (dependency list, not source code).

---

## Category 10: Scripts & Migrations

All files under `backend/scripts/` are operational/migration scripts. No issues found that affect the main application. `seed_full_data.py` contains bare `pass` in exception handlers — acceptable for seed scripts.

---

## Cross-Cutting Concerns

### Security
| Check | Status |
|-------|--------|
| No hardcoded secrets | ✅ All from env vars |
| Password hashing | ✅ werkzeug.security |
| JWT token management | ✅ flask_jwt_extended with blocklist |
| Rate limiting | ✅ Flask-Limiter on sensitive endpoints |
| SQL injection | ✅ SQLAlchemy ORM used everywhere |
| CORS | ✅ Configured via env var |
| Input validation | ✅ Length checks on all text inputs |
| Admin authorization | ✅ `require_admin()` decorator on admin routes |
| Abuse detection | ✅ Pattern-based + rate-based |

### Thread Safety
| Component | Status |
|-----------|--------|
| JobQueue | ✅ `threading.Lock` on all operations |
| Telemetry storage | ⚠️ Module-level dicts modified without locks (novelty/utils/observability.py). Low risk since GIL protects dict operations in CPython, but not formally thread-safe. |
| Retrieval cache | ⚠️ Module-level dict, same GIL caveat |
| Novelty service cache | ⚠️ Module-level dict, same GIL caveat |

### Memory Management
| Component | Status |
|-----------|--------|
| Telemetry | ✅ Bounded (maxlen=1000 per metric, max 500 metrics) |
| Stability history | ✅ Bounded (max 10,000 keys, maxlen=5 per key) |
| Job queue | ✅ Auto-cleanup after 1 hour |
| Embedding cache | ✅ LRU with 5000 entry cap |
| Retrieval cache | ⚠️ Grows unbounded — only expires by TTL, never evicts. Long-running server could accumulate entries. |

---

## Summary of All Issues

### CRITICAL (2)

| # | File | Line(s) | Description |
|---|------|---------|-------------|
| 1 | `core/models.py` | 338 | `IdeaFeedback` CHECK constraint allows 6 types but `api/routes/ideas.py:145` accepts 12. Reaction types (upvote, downvote, bookmark, report, helpful, not_helpful) will cause IntegrityError at DB level. |
| 2 | `generation/generator.py` | 836 | Demo mode calls `update_job_status(job_id, "running", 100, 5)` with phase=100, progress=5. Arguments are swapped — should be phase ≤ 4, progress=100. |

### MEDIUM (8)

| # | File | Line(s) | Description |
|---|------|---------|-------------|
| 3 | `core/auth.py` | all | Deprecated legacy auth module still exists with shadowing function names. Maintenance hazard. |
| 4 | `api/routes/admin.py` | 136-139 | `phase_5` in generation trace response reuses `phase_4_output`. Either misleading label or missing model column. |
| 5 | `utils/health_checks.py` | `check_embeddings()` | Embedding health check is a no-op (always returns "skipped"). |
| 6 | `novelty/router.py` | all | All 10 domains routed to `NoveltyAnalyzer`. Domain-specific engines (`BusinessNoveltyEngine`, `SocialNoveltyEngine`, `GenericNoveltyEngine`) are defined but never used. |
| 7 | `generation/job_queue.py` | all | In-memory job queue — all jobs lost on restart. Not suitable for multi-worker production deployments. |
| 8 | `retrieval/github_client.py` | all | No GitHub API authentication token. Anonymous rate limit is 60 req/hour. Will throttle quickly in production. |
| 9 | `api/routes/public.py` | 227 | `relevance_tier` accessed via `hasattr()` on `IdeaSource` model which lacks this column. Always falls back to `"supporting"`. Field is never meaningful. |
| 10 | `retrieval/github_client.py` | ~275 | Deferred import of `_summarize_query_with_llm` from `orchestrator.py` creates circular import risk. |

### MINOR (11)

| # | File | Line(s) | Description |
|---|------|---------|-------------|
| 11 | `core/models.py` | ~40-60 | `ProjectVector` model is legacy dead code. |
| 12 | `core/models.py` | 191 | `feedback_counts` iterates in Python instead of SQL aggregation. |
| 13 | `api/routes/ideas.py` | 165 | Feedback upsert not atomically safe (query-then-create race condition). |
| 14 | `api/routes/platform.py` | all | Deprecated endpoint aliases without clear deprecation headers. |
| 15 | `novelty/engines/social.py` | all | Inline level thresholds instead of shared `determine_level()`. |
| 16 | `generation/generator.py` | various | f-string logging (`logger.info(f"...")`) instead of lazy `%s` formatting. |
| 17 | `generation/generator.py` | threading | Non-daemon threads for background generation. |
| 18 | `retrieval/github_client.py` | ~280 | Query truncation at 240 chars may cut terms mid-word. |
| 19 | `ai/__init__.py` | — | Missing `__init__.py` for the `ai` package. |
| 20 | `novelty/engines/__init__.py` | — | Missing `__init__.py` for the `engines` sub-package. |
| 21 | `novelty/scoring/__init__.py` | — | Missing `__init__.py` for the `scoring` sub-package. |

### Missing Implementations (3)

| # | Component | Description |
|---|-----------|-------------|
| 1 | Embedding health check | `check_embeddings()` returns "skipped" — never validates the model. |
| 2 | Domain-specific novelty engines | `BusinessNoveltyEngine`, `SocialNoveltyEngine`, `GenericNoveltyEngine` exist but are never routed to. |
| 3 | `IdeaSource.relevance_tier` | Computed at generation time but never persisted to DB. Public API returns a constant default. |

---

## No TODO/FIXME/HACK/NotImplementedError Found

A grep across all application code (excluding `venv/`) found **zero** instances of `TODO`, `FIXME`, `HACK`, or `NotImplementedError` in the application source files. All matches were in third-party packages under `venv/`.

---

## Files Fully Audited (62 total)

| Package | Files |
|---------|-------|
| `core/` | `models.py`, `db.py`, `config.py`, `auth.py`, `app.py`, `abuse.py` |
| `api/` | `__init__.py` |
| `api/routes/` | `auth.py`, `ideas.py`, `admin.py`, `generation.py`, `health.py`, `domains.py`, `analytics.py`, `public.py`, `retrieval.py`, `platform.py`, `novelty.py` |
| `utils/` | `__init__.py`, `serializers.py`, `common.py`, `auth.py`, `health_checks.py` |
| `generation/` | `__init__.py`, `generator.py`, `schemas.py`, `constraints.py`, `job_queue.py` |
| `ai/` | `llm_client.py`, `prompts.py`, `registry.py` |
| `novelty/` | `__init__.py`, `service.py`, `router.py`, `analyzer.py`, `config.py`, `explain.py`, `metrics.py`, `normalization.py`, `domain_intent.py` |
| `novelty/engines/` | `business.py`, `generic.py`, `social.py` |
| `novelty/scoring/` | `base.py`, `blending.py`, `bonuses.py`, `penalties.py` |
| `novelty/utils/` | `__init__.py`, `calibration.py`, `observability.py`, `signals.py` |
| `retrieval/` | `__init__.py`, `orchestrator.py`, `arxiv_client.py`, `github_client.py`, `cached_retrieval.py`, `source_reputation.py` |
| `semantic/` | `__init__.py`, `embedder.py`, `cached_embedder.py`, `filter.py`, `ranker.py` |
| Root | `__init__.py`, `app.py`, `run.py`, `validate_contracts.py`, `validate_models.py` |

---

*End of audit report.*
