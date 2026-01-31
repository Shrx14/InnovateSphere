import uuid
import logging

logger = logging.getLogger("novelty.trace")


def log_trace(payload: dict) -> str:
    trace_id = str(uuid.uuid4())
    payload["trace_id"] = trace_id
    logger.info(payload)
    return trace_id
