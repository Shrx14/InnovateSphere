"""
Idea generation endpoints
"""
from functools import wraps
import logging
import threading
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from backend.core.app import limiter
from backend.utils import require_admin, get_current_user_id
from backend.generation.job_queue import get_job_queue


generation_bp = Blueprint("generation", __name__)

# Global list to track all active background threads for graceful shutdown
_active_threads = []
_threads_lock = threading.Lock()


def _register_thread(thread: threading.Thread):
    """Register a background thread for graceful shutdown tracking."""
    with _threads_lock:
        _active_threads.append(thread)


def _unregister_thread(thread: threading.Thread):
    """Unregister a background thread after it completes."""
    with _threads_lock:
        if thread in _active_threads:
            _active_threads.remove(thread)


def wait_for_active_threads(timeout_seconds: int = 300):
    """
    Wait for all active background threads to complete.
    Called during graceful shutdown to ensure jobs are not interrupted.
    
    Args:
        timeout_seconds: Maximum time to wait for all threads to complete
    """
    logger = logging.getLogger(__name__)
    logger.info(f"[Shutdown] Waiting for {len(_active_threads)} background thread(s) to complete (timeout: {timeout_seconds}s)")
    
    with _threads_lock:
        threads_to_wait = _active_threads.copy()
    
    for thread in threads_to_wait:
        try:
            thread.join(timeout=timeout_seconds)
            if thread.is_alive():
                logger.warning(f"[Shutdown] Thread {thread.name} did not complete within {timeout_seconds}s")
            else:
                logger.info(f"[Shutdown] Thread {thread.name} completed")
        except Exception as e:
            logger.exception(f"[Shutdown] Error waiting for thread {thread.name}: {e}")
    
    logger.info("[Shutdown] All background threads processed")


def admin_bypass_limit(limit_str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            # Log incoming request details to help diagnose validation errors
            try:
                body = request.get_data(as_text=True)
            except Exception:
                body = "<unreadable>"
            headers = dict(list(request.headers)[:10])
            logger.debug("admin_bypass_limit invoked for path=%s method=%s headers=%s body=%s", request.path, request.method, headers, (body[:2000] if body else ""))

            if require_admin():
                logger.debug("Admin user detected - bypassing rate limit")
                return func(*args, **kwargs)

            wrapped = limiter.limit(limit_str)(func)
            logger.debug("Calling wrapped function via limiter: %s", getattr(wrapped, '__name__', str(wrapped)))
            return wrapped(*args, **kwargs)
        return wrapper
    return decorator


def _generate_idea_background(app, job_id: str, query: str, domain_id, user_id: int):
    """
    Background worker function to run idea generation asynchronously.
    Updates job queue with progress and results.
    Runs in a non-daemon thread so it completes before app shutdown.
    
    Args:
        app: Flask application instance
        job_id: Unique job identifier
        query: The idea generation query/subject
        domain_id: Domain constraint for generation
        user_id: User ID for the request
    """
    current_thread = threading.current_thread()
    logger = logging.getLogger(__name__)
    
    try:
        # Establish Flask application context for database access in background thread
        with app.app_context():
            job_queue = get_job_queue()
            
            try:
                job_queue.update_job_status(job_id, "running", 0, 5)
                
                from backend.generation.generator import generate_idea as do_generate
                
                # Run the main generation (this will call generate_idea with job_id parameter)
                result = do_generate(query, domain_id, user_id, job_id=job_id)
                
                # Check if generation succeeded
                if isinstance(result, dict) and 'error' in result:
                    error_msg = result.get('error', 'Unknown error')
                    job_queue.set_job_error(job_id, error_msg)
                    logger.error(f"[Job {job_id}] Generation failed: {error_msg}")
                else:
                    # Success - store final result
                    job_queue.set_final_result(job_id, result)
                    logger.info(f"[Job {job_id}] Generation completed successfully")
            
            except Exception as e:
                import traceback
                error_msg = str(e)
                trace = traceback.format_exc()
                job_queue.set_job_error(job_id, error_msg, trace)
                logger.exception(f"[Job {job_id}] Unhandled exception in background generation")
    
    finally:
        # Unregister thread after completion
        _unregister_thread(current_thread)


@generation_bp.route("/api/ideas/generate", methods=["POST"])
@jwt_required()
@admin_bypass_limit("20/hour")
def generate_idea():
    """
    Asynchronously generate ideas.
    Returns 202 Accepted with job_id immediately, processing happens in background.
    Poll /api/ideas/generate/{job_id} to check status and get results.
    """
    logger = logging.getLogger(__name__)
    try:
        raw = request.get_data(as_text=True)
    except Exception:
        raw = "<unreadable>"
    headers = dict(list(request.headers)[:20])
    logger.debug("ENTER generate_idea path=%s method=%s headers=%s body=%s", request.path, request.method, headers, raw[:5000])

    # Try to parse JSON silently so we can log raw body if parsing fails
    data = request.get_json(silent=True)
    logger.debug("Parsed JSON (silent): %s", data)

    # Determine subject (accept 'subject' or 'query')
    subject = None
    if isinstance(data, dict):
        if 'subject' in data:
            subject = data.get('subject')
        elif 'query' in data:
            subject = data.get('query')

    logger.debug("Determined subject type=%s value=%r", type(subject).__name__ if subject is not None else None, subject)

    # Validate manually to capture detailed log if invalid
    if not isinstance(subject, str) or not subject.strip():
        logger.error("Subject validation failed. raw=%r parsed=%r", raw, data)
        return jsonify({"msg": "Subject must be a string - received: " + str(type(subject))}), 422

    domain_id = data.get('domain_id') if isinstance(data, dict) else None
    user_id = get_current_user_id()
    logger.debug("Calling generation: subject(len=%d) domain_id=%r user_id=%r", len(subject), domain_id, user_id)

    try:
        # Create job entry
        job_queue = get_job_queue()
        job_id = job_queue.create_job(subject, domain_id, user_id)
        
        # Start background worker thread (non-daemon to allow graceful shutdown)
        thread = threading.Thread(
            target=_generate_idea_background,
            args=(current_app._get_current_object(), job_id, subject, domain_id, user_id),
            daemon=False,
            name=f"generation-{job_id[:8]}"
        )
        _register_thread(thread)
        thread.start()
        
        logger.info(f"[Job {job_id}] Started async generation in background thread")
        
        # Return 202 Accepted with job_id immediately
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Idea generation started. Poll /api/ideas/generate/{job_id} for status and results.",
            "poll_url": f"/api/ideas/generate/{job_id}"
        }), 202
    
    except Exception as e:
        logger.exception("Unhandled exception in generation request handler")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@generation_bp.route("/api/ideas/generate/<job_id>", methods=["GET"])
@jwt_required()
def get_generation_status(job_id: str):
    """
    Poll the status of an async idea generation job.
    
    Returns:
        - 200 with job status if job found
        - 202 if job still running
        - 400 if job failed
        - 404 if job not found
    """
    logger = logging.getLogger(__name__)
    job_queue = get_job_queue()
    
    job_status = job_queue.get_job_status(job_id)
    
    if not job_status:
        logger.warning(f"[Job {job_id}] Status requested but job not found")
        return jsonify({"error": "Job not found", "job_id": job_id}), 404
    
    # Log status check
    logger.debug(f"[Job {job_id}] Status check: status={job_status['status']} phase={job_status['phase']} progress={job_status['progress']}%")
    
    # Prepare response
    response = {
        "job_id": job_id,
        "status": job_status["status"],
        "phase": job_status["phase"],
        "phase_name": job_status["phase_names"].get(job_status["phase"], "Unknown"),
        "progress": job_status["progress"],
        "created_at": job_status["created_at"],
        "started_at": job_status["started_at"],
        "completed_at": job_status["completed_at"],
    }
    
    # Add intermediate results if available
    if job_status["intermediate_results"]["sources"]:
        response["sources_count"] = len(job_status["intermediate_results"]["sources"])
    
    if job_status["intermediate_results"]["novelty"]:
        response["novelty_score"] = job_status["intermediate_results"]["novelty"].get("novelty_score")
    
    if job_status["intermediate_results"]["trace_id"]:
        response["trace_id"] = job_status["intermediate_results"]["trace_id"]
    
    # Job still running
    if job_status["status"] == "running":
        response["message"] = "Generation in progress..."
        logger.debug(f"[Job {job_id}] Returning 202 - still processing")
        return jsonify(response), 202
    
    # Job completed successfully
    if job_status["status"] == "completed" and job_status["final_result"]:
        response["result"] = job_status["final_result"]
        logger.info(f"[Job {job_id}] Returning completed result")
        return jsonify(response), 200
    
    # Job failed
    if job_status["status"] == "failed":
        response["error"] = job_status["error"]
        if job_status["error_trace"]:
            response["error_trace"] = job_status["error_trace"]
        logger.warning(f"[Job {job_id}] Returning failed status with error: {job_status['error']}")
        return jsonify(response), 400
    
    # Queued (waiting to start)
    if job_status["status"] == "queued":
        response["message"] = "Waiting to start..."
        logger.debug(f"[Job {job_id}] Still queued")
        return jsonify(response), 202
    
    # Unknown state
    logger.warning(f"[Job {job_id}] Unknown status: {job_status['status']}")
    return jsonify(response), 200
