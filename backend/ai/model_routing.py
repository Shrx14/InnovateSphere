from __future__ import annotations

from backend.core.config import Config


def resolve_model_for_task(*, task_type: str | None = None, model_override: str | None = None) -> str:
    """Resolve the effective model for an LLM call.

    Priority:
    1. Explicit model_override
    2. Task-based routing (when ENABLE_HETEROGENEOUS_MODELS=true)
    3. Default LLM model
    """
    if model_override:
        return model_override

    if not getattr(Config, "ENABLE_HETEROGENEOUS_MODELS", False):
        return Config.LLM_MODEL_NAME

    task = (task_type or "").strip().lower()
    fast_tasks = getattr(Config, "LLM_FAST_TASK_TYPES", set()) or set()

    if task and task in fast_tasks:
        return getattr(Config, "LLM_FAST_MODEL_NAME", Config.LLM_MODEL_NAME)

    return getattr(Config, "LLM_QUALITY_MODEL_NAME", Config.LLM_MODEL_NAME)


def is_task_routed_to_fast_model(task_type: str | None) -> bool:
    task = (task_type or "").strip().lower()
    return bool(
        getattr(Config, "ENABLE_HETEROGENEOUS_MODELS", False)
        and task
        and task in (getattr(Config, "LLM_FAST_TASK_TYPES", set()) or set())
    )
