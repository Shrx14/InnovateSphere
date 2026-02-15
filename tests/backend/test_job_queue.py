"""Unit tests for backend.generation.job_queue module."""
import pytest
from datetime import datetime, timedelta
from backend.generation.job_queue import JobQueue


class TestJobQueue:
    """Tests for the in-memory JobQueue."""

    def setup_method(self):
        self.queue = JobQueue(max_age_minutes=60)

    def test_create_job_returns_uuid(self):
        job_id = self.queue.create_job("AI search engine", domain_id=1, user_id=42)
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID length

    def test_get_job_status_returns_created_job(self):
        job_id = self.queue.create_job("AI search engine", domain_id=1, user_id=42)
        job = self.queue.get_job_status(job_id)
        assert job is not None
        assert job["query"] == "AI search engine"
        assert job["domain_id"] == 1
        assert job["user_id"] == 42
        assert job["status"] == "queued"
        assert job["progress"] == 0

    def test_get_nonexistent_job_returns_none(self):
        job = self.queue.get_job_status("nonexistent-id")
        assert job is None

    def test_update_job_status(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        result = self.queue.update_job_status(job_id, status="running", phase=1, progress=25)
        assert result is True
        job = self.queue.get_job_status(job_id)
        assert job["status"] == "running"
        assert job["phase"] == 1
        assert job["progress"] == 25
        assert job["started_at"] is not None

    def test_update_nonexistent_returns_false(self):
        result = self.queue.update_job_status("bad-id", status="running", phase=0, progress=0)
        assert result is False

    def test_set_final_result_completes_job(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        self.queue.update_job_status(job_id, status="running", phase=3, progress=80)
        result = self.queue.set_final_result(job_id, {"idea_id": 99})
        assert result is True
        job = self.queue.get_job_status(job_id)
        assert job["status"] == "completed"
        assert job["final_result"]["idea_id"] == 99
        assert job["completed_at"] is not None
        assert job["progress"] == 100
        assert job["phase"] == 4

    def test_set_job_error_marks_failed(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        result = self.queue.set_job_error(job_id, error="LLM timeout", trace="traceback...")
        assert result is True
        job = self.queue.get_job_status(job_id)
        assert job["status"] == "failed"
        assert job["error"] == "LLM timeout"
        assert job["error_trace"] == "traceback..."

    def test_set_intermediate_result(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        result = self.queue.set_intermediate_result(job_id, "sources", [{"url": "http://example.com"}])
        assert result is True
        job = self.queue.get_job_status(job_id)
        assert job["intermediate_results"]["sources"] == [{"url": "http://example.com"}]

    def test_set_intermediate_result_invalid_key(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        result = self.queue.set_intermediate_result(job_id, "invalid_key", "data")
        assert result is False

    def test_multiple_jobs_independent(self):
        id1 = self.queue.create_job("q1", domain_id=1, user_id=1)
        id2 = self.queue.create_job("q2", domain_id=2, user_id=2)
        assert id1 != id2
        assert self.queue.get_job_status(id1)["query"] == "q1"
        assert self.queue.get_job_status(id2)["query"] == "q2"

    def test_job_has_phase_names(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        job = self.queue.get_job_status(job_id)
        assert "phase_names" in job
        assert job["phase_names"][0] == "Retrieving sources"
        assert job["phase_names"][4] == "Complete"

    def test_set_phase_names_override(self):
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        custom_names = {0: "Step A", 1: "Step B", 2: "Step C"}
        result = self.queue.set_phase_names(job_id, custom_names)
        assert result is True
        job = self.queue.get_job_status(job_id)
        assert job["phase_names"][0] == "Step A"

    def test_get_job_status_returns_copy(self):
        """Modifying returned dict should not affect internal state."""
        job_id = self.queue.create_job("test", domain_id=None, user_id=1)
        job = self.queue.get_job_status(job_id)
        job["status"] = "tampered"
        # Internal state should be untouched
        assert self.queue.get_job_status(job_id)["status"] == "queued"


class TestJobQueueCleanup:
    """Tests for job queue cleanup behavior."""

    def test_cleanup_old_jobs(self):
        queue = JobQueue(max_age_minutes=0)  # Everything is stale immediately
        job_id = queue.create_job("old job", domain_id=None, user_id=1)
        # Artificially age the job so it's strictly older than cutoff
        queue._jobs[job_id]["created_at"] = (datetime.utcnow() - timedelta(seconds=2)).isoformat()
        removed = queue.cleanup_old_jobs()
        assert removed >= 1

    def test_cleanup_preserves_recent_jobs(self):
        queue = JobQueue(max_age_minutes=9999)
        job_id = queue.create_job("recent job", domain_id=None, user_id=1)
        removed = queue.cleanup_old_jobs()
        assert removed == 0
        assert queue.get_job_status(job_id) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
