from backend.evaluation.metrics import compute_cs, compute_ids, compute_rr


def test_compute_ids_for_distinct_texts_is_positive():
    score = compute_ids(["graph neural networks", "event scheduling optimization"])
    assert 0.0 <= score <= 1.0


def test_compute_rr_is_zero_for_single_item():
    assert compute_rr(["only one idea"]) == 0.0


def test_compute_cs_handles_hybrid_payload_shape():
    payload = {
        "title": "Adaptive Scheduler",
        "problem_statement": "Allocate booths under spatial constraints",
        "proposed_method": "Constraint programming with local search",
        "tech_stack": [
            {"component": "Backend", "technologies": ["FastAPI", "PostgreSQL"]},
            {"component": "Optimization", "technologies": ["OR-Tools"]},
        ],
    }
    score = compute_cs(payload)
    assert 0.0 <= score <= 1.0
