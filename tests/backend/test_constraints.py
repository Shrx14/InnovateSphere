"""Unit tests for backend.generation.constraints module."""
import pytest
from unittest.mock import patch, MagicMock
from backend.generation.constraints import (
    build_hitl_constraints,
    is_rejected_pattern,
    filter_hallucinated_sources,
    _cosine_similarity,
)


class TestCosineSimiliarity:
    """Tests for the cosine similarity helper."""

    def test_identical_vectors(self):
        assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert _cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert _cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert _cosine_similarity([0, 0], [1, 2]) == 0.0

    def test_partial_similarity(self):
        result = _cosine_similarity([1, 1], [1, 0])
        assert 0.0 < result < 1.0


class TestIsRejectedPattern:
    """Tests for pattern matching against historically rejected ideas."""

    def test_exact_title_match_rejects(self):
        constraints = {"pattern_penalties": ["blockchain voting system"]}
        candidate = {"title": "Blockchain Voting System"}
        result = is_rejected_pattern(candidate, constraints)
        assert result is not None
        assert result["error"] == "generation_aborted"
        assert result["reason"] == "historically_rejected_pattern"

    def test_no_match_returns_none(self):
        constraints = {"pattern_penalties": ["blockchain voting"]}
        candidate = {"title": "Quantum Key Distribution"}
        result = is_rejected_pattern(candidate, constraints)
        assert result is None

    def test_empty_constraints_returns_none(self):
        constraints = {"pattern_penalties": []}
        candidate = {"title": "Some Idea"}
        result = is_rejected_pattern(candidate, constraints)
        assert result is None

    @patch("backend.semantic.embedder.get_embedder")
    def test_embedding_similarity_check(self, mock_get_embedder):
        """High embedding similarity should reject."""
        mock_embedder = MagicMock()
        # Return identical embeddings for high similarity
        mock_embedder.encode.return_value = [1.0, 0.0, 0.0]
        mock_get_embedder.return_value = mock_embedder

        constraints = {"pattern_penalties": ["ai powered search"]}
        candidate = {"title": "AI Powered Search Engine"}  # Different text, same embedding
        result = is_rejected_pattern(candidate, constraints)
        # With identical embeddings, similarity = 1.0 > 0.85 threshold
        assert result is not None
        assert result["reason"] == "embedding_similar_to_rejected"


class TestFilterHallucinatedSources:
    """Tests for hallucinated source filtering."""

    @patch("backend.core.models.IdeaSource")
    def test_filters_flagged_urls(self, mock_model):
        mock_query = MagicMock()
        mock_model.query.filter_by.return_value = mock_query
        mock_row = MagicMock()
        mock_row.url = "http://fake.com/paper"
        mock_query.with_entities.return_value.all.return_value = [mock_row]

        sources = [
            {"url": "http://fake.com/paper", "title": "Fake"},
            {"url": "http://real.com/paper", "title": "Real"},
        ]
        result = filter_hallucinated_sources(sources)
        assert len(result) == 1
        assert result[0]["url"] == "http://real.com/paper"

    @patch("backend.core.models.IdeaSource")
    def test_no_flagged_returns_all(self, mock_model):
        mock_query = MagicMock()
        mock_model.query.filter_by.return_value = mock_query
        mock_query.with_entities.return_value.all.return_value = []

        sources = [
            {"url": "http://a.com", "title": "A"},
            {"url": "http://b.com", "title": "B"},
        ]
        result = filter_hallucinated_sources(sources)
        assert len(result) == 2

    @patch("backend.core.models.IdeaSource")
    def test_db_error_returns_all_sources(self, mock_model):
        """If DB query fails, don't block generation."""
        mock_model.query.filter_by.side_effect = Exception("DB error")

        sources = [{"url": "http://a.com", "title": "A"}]
        result = filter_hallucinated_sources(sources)
        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
