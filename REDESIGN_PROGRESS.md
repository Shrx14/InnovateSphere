# InnovateSphere Redesign Progress

Last updated: 2026-04-08
Source plan: Technical Audit & Redesign.md

## Summary

This tracker records implementation progress against the Technical Audit & Redesign plan.
Status values:
- Completed: Implemented in code
- In progress: Partially implemented
- Not started: Not yet implemented

## Completed Items

### Quick Wins

1. Fix dual retrieval (pass preloaded sources to novelty scorer) - Completed
- Novelty analysis now accepts preloaded sources from generation flow.
- Duplicate retrieval calls for novelty scoring were removed from generation path.
- Key files:
  - backend/novelty/service.py
  - backend/novelty/analyzer.py
  - backend/generation/generator.py

2. Score novelty on generated idea (generation path) while preserving query scoring for standalone novelty checks - Completed
- Generation flow now performs:
  - Query-based novelty precheck for gating
  - Final idea-grounded novelty scoring using generated idea text
- Standalone novelty page endpoint remains query-scored.
- Key files:
  - backend/generation/generator.py
  - backend/api/routes/novelty.py
  - backend/api/routes/admin.py

3. Remove light mode toggle completely - Completed
- Theme toggle control removed from footer UI.
- Theme context now exposes fixed dark theme value only.
- Key files:
  - frontend/src/features/shared/layout/Footer.jsx
  - frontend/src/context/ThemeContext.jsx

4. Switch semantic filter to singleton embedder - Completed
- Semantic filtering now uses shared embedder instance from get_embedder().
- Key file:
  - backend/semantic/filter.py

5. Implement self-critique loop (Approach 1 shape) - Completed
- Hybrid prompts updated to enforce structured decomposition and self_critique output.
- Hybrid schema extended to validate self_critique block.
- Generator fallback and pass handling updated for revised analysis shape.
- Key files:
  - backend/ai/prompts.py
  - backend/generation/schemas.py
  - backend/generation/generator.py

### Medium Complexity

6. Redesigned novelty scoring (distributional + idea-grounded) - Completed
- Added distribution-aware novelty scoring signals.
- Added token-level novelty signal and cross-domain spread signal.
- Preserved HITL/admin/commodity/reuse adjustments and evidence calibration for stability.
- Key file:
  - backend/novelty/analyzer.py

7. ONNX embedding optimization - Completed (with safe fallback)
- Added optional ONNX embedding backend configuration.
- Added fallback to sentence-transformers when ONNX model or runtime is unavailable.
- Added required dependencies.
- Key files:
  - backend/semantic/embedder.py
  - backend/core/config.py
  - backend/requirements.txt

8. Persist job queue to PostgreSQL - Completed
- Added durable JobState model.
- JobQueue now persists and reloads job snapshots from DB.
- In-memory behavior retained as fallback.
- Key files:
  - backend/core/models.py
  - backend/generation/job_queue.py
  - backend/novelty/service.py

9. Replace position-length heuristic with TF-IDF keyword extraction - Completed
- Introduced shared TF-IDF-style extractor.
- Wired arXiv and GitHub retrieval clients to use it for fallback term extraction.
- Key files:
  - backend/retrieval/keyword_extractor.py
  - backend/retrieval/arxiv_client.py
  - backend/retrieval/github_client.py

## Plan Items In Progress

### Advanced / Research-Level

10. Generator-Critic-Refiner pipeline (Approach 2) - Not started
11. Evaluation framework with FAISS reference index (INS/IDS/CS/RR pipeline) - In progress
- Added evaluation package with:
  - FAISS index wrapper/load/save/build helpers
  - INS/IDS/CS/RR metric functions
  - Batch evaluation service
- Added optional generation integration to compute INS/CS when a reference index is configured.
- Added index build script for JSONL corpora.
- Key files:
  - backend/evaluation/faiss_index.py
  - backend/evaluation/metrics.py
  - backend/evaluation/service.py
  - backend/scripts/build_faiss_reference_index.py
  - backend/generation/generator.py
  - backend/core/config.py

12. Contrastive similarity approach/domain separation pipeline - In progress
- Added contrastive novelty signal to analyzer using approach-vs-domain term separation.
- Added configurable weighting and minimum domain similarity guard.
- Integrated signal into novelty base score and detailed breakdown/debug payload.
- Key files:
  - backend/novelty/analyzer.py
  - backend/core/config.py

13. Heterogeneous model pipeline routing by task (fast model + quality model) - In progress
- Added task-aware model router with override support.
- Extended generate_json() to accept model_override and task_type.
- Wired retrieval keyword extraction, query summarization, problem-class detection, and generation passes to task tags.
- Key files:
  - backend/ai/model_routing.py
  - backend/ai/llm_client.py
  - backend/retrieval/arxiv_client.py
  - backend/retrieval/github_client.py
  - backend/retrieval/orchestrator.py
  - backend/novelty/domain_intent.py
  - backend/generation/generator.py

## Verification and Operational Follow-ups

- Targeted runtime tests were prepared but not executed in the session where these changes were applied.
- Recommended next validation:
  - Run backend tests for job queue, novelty service, and novelty endpoint.
  - Run end-to-end generation smoke test.
  - Run novelty page smoke test.
- Database note:
  - JobState model was added in ORM and will be created with db.create_all() where enabled.
  - If migration-managed environments are used, add a formal migration for job_states.

## Change Log

- 2026-04-08: Initial progress tracker created with completed redesign implementation items.
- 2026-04-08: Started implementation for advanced items 11-13 (evaluation framework, contrastive novelty, heterogeneous model routing).
