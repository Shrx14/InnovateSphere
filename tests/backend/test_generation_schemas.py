"""Unit tests for backend.generation.schemas module."""
import pytest
from backend.generation.schemas import (
    ProblemFormulation,
    EvidenceSource,
    GeneratedIdea,
    validate_generated_idea,
    HybridGeneratedIdea,
    validate_hybrid_idea,
    NoveltyPositioning,
    Module,
    SystemDesign,
    TechnologyChoice,
    RelatedWorkSynthesis,
    ProposedContribution,
)
from pydantic import ValidationError


# ========== Helpers ==========

def _make_source(sid="S1", stype="arxiv"):
    return {
        "source_id": sid,
        "title": f"Source {sid}",
        "url": f"http://example.com/{sid}",
        "source_type": stype,
        "used_for": "grounding",
    }


def _make_full_idea(**overrides):
    """Build a valid GeneratedIdea dict."""
    sources = [
        _make_source("S1", "arxiv"),
        _make_source("S2", "github"),
        _make_source("S3", "arxiv"),
        _make_source("S4", "github"),
    ]
    base = {
        "title": "Test Idea",
        "problem_formulation": {
            "context": "Problem context",
            "why_this_problem_matters": "It matters because...",
            "evidence_basis": ["S1", "S2"],
        },
        "related_work_synthesis": {
            "common_approaches": "Approaches...",
            "observed_limitations": "Limits...",
            "evidence_basis": ["S1"],
        },
        "proposed_contribution": {
            "core_idea": "Core idea",
            "what_is_new": "Novelty",
            "why_it_is_plausible": "Plausibility",
            "evidence_basis": ["S2", "S3"],
        },
        "system_or_project_design": {
            "modules": [{"name": "Core", "responsibility": "Main logic", "justification": "Needed"}]
        },
        "technology_choices": [
            {"technology": "Python", "role": "Backend", "justification": "Widely used"}
        ],
        "novelty_positioning": {
            "novelty_score": 72.0,
            "interpretation": "Moderately novel",
            "tradeoffs": "Some risks",
        },
        "limitations_and_risks": ["Risk 1"],
        "evidence_sources": sources,
    }
    base.update(overrides)
    return base


# ========== Evidence Source Tests ==========

class TestEvidenceSource:
    def test_valid_source(self):
        s = EvidenceSource(**_make_source("S1", "arxiv"))
        assert s.source_id == "S1"
        assert s.source_type == "arxiv"

    def test_invalid_source_type_rejected(self):
        with pytest.raises(ValidationError, match="Invalid source_type"):
            EvidenceSource(**_make_source("S1", "wikipedia"))

    def test_relevance_tier_defaults_to_contextual(self):
        s = EvidenceSource(**_make_source())
        assert s.relevance_tier == "contextual"

    def test_invalid_relevance_tier_fallback(self):
        data = _make_source()
        data["relevance_tier"] = "invalid"
        s = EvidenceSource(**data)
        assert s.relevance_tier == "contextual"


# ========== Problem Formulation Tests ==========

class TestProblemFormulation:
    def test_empty_evidence_rejected(self):
        with pytest.raises(ValidationError, match="evidence"):
            ProblemFormulation(
                context="ctx",
                why_this_problem_matters="why",
                evidence_basis=[]
            )

    def test_valid_formulation(self):
        pf = ProblemFormulation(
            context="ctx",
            why_this_problem_matters="why",
            evidence_basis=["S1"]
        )
        assert pf.evidence_basis == ["S1"]


# ========== Novelty Positioning Tests ==========

class TestNoveltyPositioning:
    def test_score_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            NoveltyPositioning(novelty_score=150, interpretation="x", tradeoffs="y")

    def test_valid_score(self):
        n = NoveltyPositioning(novelty_score=50, interpretation="x", tradeoffs="y")
        assert n.novelty_score == 50


# ========== Full Generated Idea Tests ==========

class TestGeneratedIdea:
    def test_valid_idea_passes(self):
        idea = validate_generated_idea(_make_full_idea())
        assert idea.title == "Test Idea"

    def test_too_few_sources_rejected(self):
        data = _make_full_idea()
        data["evidence_sources"] = [_make_source("S1", "arxiv")]
        data["problem_formulation"]["evidence_basis"] = ["S1"]
        data["related_work_synthesis"]["evidence_basis"] = ["S1"]
        data["proposed_contribution"]["evidence_basis"] = ["S1"]
        with pytest.raises(ValidationError, match="4 evidence sources"):
            validate_generated_idea(data)

    def test_single_source_type_rejected(self):
        """At least 2 distinct source types required."""
        data = _make_full_idea()
        data["evidence_sources"] = [
            _make_source("S1", "arxiv"),
            _make_source("S2", "arxiv"),
            _make_source("S3", "arxiv"),
            _make_source("S4", "arxiv"),
        ]
        with pytest.raises(ValidationError, match="2 distinct source types"):
            validate_generated_idea(data)

    def test_invalid_evidence_reference_rejected(self):
        data = _make_full_idea()
        data["problem_formulation"]["evidence_basis"] = ["NONEXISTENT"]
        with pytest.raises(ValidationError, match="Invalid evidence reference"):
            validate_generated_idea(data)

    def test_evidence_breakdown_populated(self):
        idea = validate_generated_idea(_make_full_idea())
        assert isinstance(idea.evidence_breakdown, dict)


# ========== Hybrid Schema Tests ==========

class TestHybridGeneratedIdea:
    def test_valid_hybrid_idea(self):
        data = {
            "title": "Hybrid Test Idea",
            "problem_statement": "A real problem that needs solving",
            "modules": [{"name": "Core Module", "responsibility": "Main logic"}],
        }
        idea = validate_hybrid_idea(data)
        assert idea.title == "Hybrid Test Idea"
        assert idea.implementation_complexity == "medium"

    def test_title_too_short_rejected(self):
        with pytest.raises(ValidationError):
            validate_hybrid_idea({
                "title": "Hi",
                "problem_statement": "A real problem",
                "modules": [{"name": "M", "responsibility": "Logic stuff"}],
            })

    def test_complexity_normalized(self):
        data = {
            "title": "Valid Title Here",
            "problem_statement": "A real problem statement",
            "modules": [{"name": "Core", "responsibility": "Main logic"}],
            "implementation_complexity": "HIGH",
        }
        idea = validate_hybrid_idea(data)
        assert idea.implementation_complexity == "high"

    def test_invalid_complexity_defaults_medium(self):
        data = {
            "title": "Valid Title Here",
            "problem_statement": "A real problem statement",
            "modules": [{"name": "Core", "responsibility": "Main logic"}],
            "implementation_complexity": "extreme",
        }
        idea = validate_hybrid_idea(data)
        assert idea.implementation_complexity == "medium"

    def test_empty_modules_rejected(self):
        with pytest.raises(ValidationError):
            validate_hybrid_idea({
                "title": "Valid Title Here",
                "problem_statement": "A real problem statement",
                "modules": [],
            })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
