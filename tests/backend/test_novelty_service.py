"""Tests for novelty analysis service and caching."""
import pytest
from unittest.mock import patch, MagicMock


class TestNoveltyCache:
    """Tests for novelty result caching in service.py"""

    def test_cache_returns_cached_result(self):
        """Calling analyze_novelty twice with same input should use cache."""
        from backend.novelty import service
        # Clear cache
        service._novelty_cache.clear()

        mock_result = {
            "novelty_score": 75,
            "novelty_level": "moderate",
            "confidence": "medium",
            "engine": "generic",
        }

        with patch.object(service, "_get_analyzer") as mock_analyzer:
            analyzer_instance = MagicMock()
            analyzer_instance.analyze.return_value = mock_result
            mock_analyzer.return_value = analyzer_instance

            with patch("backend.novelty.router.route_engine", side_effect=Exception("skip router")):
                # First call — should compute
                result1 = service.analyze_novelty("test idea", "ai")
                assert result1["novelty_score"] == 75
                assert analyzer_instance.analyze.call_count == 1

                # Second call — should hit cache
                result2 = service.analyze_novelty("test idea", "ai")
                assert result2["novelty_score"] == 75
                assert analyzer_instance.analyze.call_count == 1  # NOT incremented

    def test_bypass_cache(self):
        """bypass_cache=True should force fresh computation."""
        from backend.novelty import service
        service._novelty_cache.clear()

        mock_result = {
            "novelty_score": 75,
            "novelty_level": "moderate",
            "confidence": "medium",
            "engine": "generic",
        }

        with patch.object(service, "_get_analyzer") as mock_analyzer:
            analyzer_instance = MagicMock()
            analyzer_instance.analyze.return_value = mock_result
            mock_analyzer.return_value = analyzer_instance

            with patch("backend.novelty.router.route_engine", side_effect=Exception("skip router")):
                service.analyze_novelty("test idea", "ai")
                service.analyze_novelty("test idea", "ai", bypass_cache=True)
                assert analyzer_instance.analyze.call_count == 2


class TestSystemUnderLoad:
    """Tests for system_under_load detection."""

    def test_under_load_returns_true_when_busy(self):
        """Should return True when >=5 jobs are running."""
        from backend.novelty.service import system_under_load
        from backend.generation.job_queue import get_job_queue

        jq = get_job_queue()
        # Fill with running jobs
        for i in range(6):
            jid = jq.create_job(f"query_{i}", None, 1)
            jq.update_job_status(jid, "running", 0, 10)

        assert system_under_load() is True

        # Cleanup
        jq._jobs.clear()

    def test_under_load_returns_false_when_idle(self):
        """Should return False when <5 jobs are running."""
        from backend.novelty.service import system_under_load
        from backend.generation.job_queue import get_job_queue

        jq = get_job_queue()
        jq._jobs.clear()
        assert system_under_load() is False


class TestConstraints:
    """Tests for constraints.py pattern rejection."""

    def test_exact_title_match_rejects(self):
        """Exact rejected title match should abort."""
        from backend.generation.constraints import is_rejected_pattern

        constraints = {"pattern_penalties": ["bad idea"]}
        candidate = {"title": "Bad Idea"}
        result = is_rejected_pattern(candidate, constraints)
        assert result is not None
        assert result["reason"] == "historically_rejected_pattern"

    def test_non_matching_title_passes(self):
        """Non-matching title should return None."""
        from backend.generation.constraints import is_rejected_pattern

        constraints = {"pattern_penalties": ["bad idea"]}
        candidate = {"title": "Great Innovation"}
        result = is_rejected_pattern(candidate, constraints)
        assert result is None

    def test_filter_hallucinated_sources(self):
        """filter_hallucinated_sources should be importable."""
        from backend.generation.constraints import filter_hallucinated_sources
        # Without DB context, should return sources unchanged
        sources = [{"url": "https://example.com", "title": "Test"}]
        # This will fail to query DB but should handle gracefully
        result = filter_hallucinated_sources(sources)
        assert len(result) == len(sources)
