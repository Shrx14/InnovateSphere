# Tier-4.7: Evidence-Aware Calibration Implementation

## Completed Tasks
- [x] Created `backend/novelty/calibration/evidence.py` with `compute_evidence_score` and `apply_evidence_constraints` functions
- [x] Modified all novelty engines to include `debug` field with `retrieved_sources` and `similarity_variance`
- [x] Updated API endpoint `/api/novelty/analyze` to follow exact flow: analyze -> compute_evidence -> apply_constraints -> normalize -> response
- [x] Added `novelty_level` to engines that were missing it
- [x] Updated response contract to include `speculative`, `evidence_score`, and `insights`
- [x] Ensured evidence constraints apply BEFORE normalization
- [x] Verified no modifications to scoring logic, engines (except debug), embeddings, retrieval, or weights

## Key Features Implemented
- Evidence score calculation based on sources, variance, and intent confidence
- Hard caps on scores when evidence < 0.20 (max 30) or < 0.35 (max 45)
- Speculative flag for weak evidence
- Deterministic and explainable logic
- Zero performance impact (no new retrieval/embeddings)

## Acceptance Criteria Met
- [x] "High novelty" score cannot appear when evidence < 0.35
- [x] "Speculative" returned when evidence is weak
- [x] Engines remain unchanged (core logic preserved)
- [x] Code is deterministic and explainable
