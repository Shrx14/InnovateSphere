"""
In-memory job queue for async idea generation.
Tracks job status, intermediate results, and completion state.
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class JobQueue:
    """In-memory job queue with status tracking for async generation."""
    
    def __init__(self, max_age_minutes: int = 120):
        """
        Initialize job queue.
        
        Args:
            max_age_minutes: Jobs older than this are removed during cleanup (default 2 hours)
        """
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.max_age_minutes = max_age_minutes
        self._persistence_enabled = True
        self._db_failure_logged = False

    def _persist_job_snapshot(self, job_id: str) -> None:
        """Persist the latest in-memory snapshot for a job to PostgreSQL."""
        if not self._persistence_enabled:
            return

        try:
            from backend.core.db import db
            from backend.core.models import JobState

            payload = self._jobs.get(job_id)
            if payload is None:
                return

            state = JobState.query.get(job_id)
            if state is None:
                db.session.add(JobState(job_id=job_id, payload=payload))
            else:
                state.payload = payload
            db.session.commit()
        except Exception as exc:
            try:
                from backend.core.db import db
                db.session.rollback()
            except Exception:
                pass

            if not self._db_failure_logged:
                logger.warning("[Job Queue] PostgreSQL persistence unavailable, using memory fallback: %s", exc)
                self._db_failure_logged = True

    def _load_job_snapshot(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job snapshot from PostgreSQL when it is missing in process memory."""
        if not self._persistence_enabled:
            return None

        try:
            from backend.core.models import JobState

            state = JobState.query.get(job_id)
            if not state or not isinstance(state.payload, dict):
                return None
            return dict(state.payload)
        except Exception:
            return None

    def _delete_job_snapshot(self, job_id: str) -> None:
        if not self._persistence_enabled:
            return

        try:
            from backend.core.db import db
            from backend.core.models import JobState

            state = JobState.query.get(job_id)
            if state is not None:
                db.session.delete(state)
                db.session.commit()
        except Exception:
            try:
                from backend.core.db import db
                db.session.rollback()
            except Exception:
                pass

    def count_running_jobs(self) -> int:
        """Count running jobs across memory and persisted snapshots."""
        with self._lock:
            local_running = sum(1 for j in self._jobs.values() if j.get("status") == "running")

        if local_running > 0:
            return local_running

        if not self._persistence_enabled:
            return 0

        try:
            from backend.core.models import JobState

            persisted_running = JobState.query.all()
            return sum(1 for state in persisted_running if isinstance(state.payload, dict) and state.payload.get("status") == "running")
        except Exception:
            return 0
    
    def create_job(self, query: str, domain_id: Optional[int], user_id: int) -> str:
        """
        Create a new generation job.
        Auto-cleans old jobs every 10th creation to prevent memory leaks.
        
        Args:
            query: The idea query/subject
            domain_id: Optional domain ID
            user_id: User requesting the generation
            
        Returns:
            job_id (UUID string)
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        with self._lock:
            # Auto-cleanup every 10 jobs to prevent unbounded growth
            if len(self._jobs) % 10 == 0 and len(self._jobs) > 0:
                cutoff = now - timedelta(minutes=self.max_age_minutes)
                to_remove = [jid for jid, j in self._jobs.items()
                             if datetime.fromisoformat(j["created_at"]) < cutoff]
                for jid in to_remove:
                    del self._jobs[jid]
                if to_remove:
                    logger.info(f"[Job Queue] Auto-cleaned {len(to_remove)} stale jobs")

            self._jobs[job_id] = {
                "job_id": job_id,
                "query": query,
                "domain_id": domain_id,
                "user_id": user_id,
                "status": "queued",  # queued -> running -> completed/failed
                "phase": 0,  # 0=retrieval, 1=novelty, 2=locking, 3=generation, 4=complete
                "phase_names": {
                    0: "Retrieving sources",
                    1: "Analyzing novelty",
                    2: "Checking constraints",
                    3: "Generating with LLM",
                    4: "Complete"
                },
                "progress": 0,  # 0-100
                "created_at": now.isoformat(),
                "started_at": None,
                "completed_at": None,
                "intermediate_results": {
                    "sources": None,
                    "novelty": None,
                    "constraints": None,
                    "trace_id": None
                },
                "final_result": None,
                "error": None,
                "error_trace": None
            }

            self._persist_job_snapshot(job_id)
        
        logger.info(f"[Job Queue] Created job {job_id} for user={user_id} query='{query[:50]}...'")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full job status and progress.
        
        Args:
            job_id: Job UUID
            
        Returns:
            Job status dict, or None if not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                loaded = self._load_job_snapshot(job_id)
                if loaded is not None:
                    self._jobs[job_id] = loaded
                    job = loaded
                else:
                    return None
            # Return a copy to avoid external mutations
            return dict(job)
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        phase: int,
        progress: int,
        error: Optional[str] = None
    ) -> bool:
        """
        Update job status and progress.
        
        Args:
            job_id: Job UUID
            status: "queued", "running", "completed", "failed"
            phase: Current phase (0-4)
            progress: Progress percentage (0-100)
            error: Optional error message if failed
            
        Returns:
            True if job updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            job["status"] = status
            job["phase"] = phase
            job["progress"] = progress
            
            if status == "running" and not job["started_at"]:
                job["started_at"] = datetime.utcnow().isoformat()
            
            if status in ("completed", "failed"):
                job["completed_at"] = datetime.utcnow().isoformat()
            
            if error:
                job["error"] = error

            self._persist_job_snapshot(job_id)
            
            logger.debug(f"[Job Queue] Updated job {job_id}: status={status} phase={phase} progress={progress}%")
            return True
    
    def set_intermediate_result(
        self,
        job_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Store intermediate results (sources, novelty, constraints, trace_id).
        
        Args:
            job_id: Job UUID
            key: "sources", "novelty", "constraints", or "trace_id"
            value: Result data
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            if key in job["intermediate_results"]:
                job["intermediate_results"][key] = value
                self._persist_job_snapshot(job_id)
                logger.debug(f"[Job Queue] Stored intermediate {key} for job {job_id}")
                return True
            
            return False
    
    def set_final_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """
        Store final generation result.
        
        Args:
            job_id: Job UUID
            result: Final generated idea result
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            job["final_result"] = result
            job["status"] = "completed"
            job["phase"] = 4
            job["progress"] = 100
            job["completed_at"] = datetime.utcnow().isoformat()

            self._persist_job_snapshot(job_id)
            
            logger.info(f"[Job Queue] Job {job_id} completed successfully")
            return True
    
    def set_job_error(self, job_id: str, error: str, trace: Optional[str] = None) -> bool:
        """
        Mark job as failed with error details.
        
        Args:
            job_id: Job UUID
            error: Error message
            trace: Optional stack trace
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            job["status"] = "failed"
            job["error"] = error
            job["error_trace"] = trace
            job["completed_at"] = datetime.utcnow().isoformat()

            self._persist_job_snapshot(job_id)
            
            logger.error(f"[Job Queue] Job {job_id} failed: {error}")
            return True

    def set_phase_names(self, job_id: str, phase_names: Dict[int, str]) -> bool:
        """
        Override the default phase names for a job (e.g. hybrid mode phases).

        Args:
            job_id: Job UUID
            phase_names: Mapping of phase int -> display label

        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["phase_names"] = phase_names
            self._persist_job_snapshot(job_id)
            return True
    
    def cleanup_old_jobs(self) -> int:
        """
        Remove jobs older than max_age_minutes.
        
        Returns:
            Number of jobs removed
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=self.max_age_minutes)
            
            to_remove = []
            for job_id, job in self._jobs.items():
                created_at = datetime.fromisoformat(job["created_at"])
                if created_at < cutoff:
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del self._jobs[job_id]
                self._delete_job_snapshot(job_id)
            
            if to_remove:
                logger.info(f"[Job Queue] Cleaned up {len(to_remove)} jobs older than {self.max_age_minutes} minutes")
            
            return len(to_remove)


# Global job queue instance
_global_job_queue = None


def get_job_queue() -> JobQueue:
    """Get or create the global job queue instance."""
    global _global_job_queue
    if _global_job_queue is None:
        _global_job_queue = JobQueue()
    return _global_job_queue
