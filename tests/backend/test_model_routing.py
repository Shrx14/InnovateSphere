from unittest.mock import patch

from backend.ai.model_routing import resolve_model_for_task


@patch("backend.ai.model_routing.Config")
def test_override_has_priority(mock_config):
    mock_config.ENABLE_HETEROGENEOUS_MODELS = True
    mock_config.LLM_MODEL_NAME = "default-model"
    mock_config.LLM_FAST_MODEL_NAME = "fast-model"
    mock_config.LLM_QUALITY_MODEL_NAME = "quality-model"
    mock_config.LLM_FAST_TASK_TYPES = {"retrieval_keywords"}

    result = resolve_model_for_task(task_type="retrieval_keywords", model_override="forced-model")
    assert result == "forced-model"


@patch("backend.ai.model_routing.Config")
def test_fast_task_routed_to_fast_model(mock_config):
    mock_config.ENABLE_HETEROGENEOUS_MODELS = True
    mock_config.LLM_MODEL_NAME = "default-model"
    mock_config.LLM_FAST_MODEL_NAME = "fast-model"
    mock_config.LLM_QUALITY_MODEL_NAME = "quality-model"
    mock_config.LLM_FAST_TASK_TYPES = {"retrieval_keywords", "query_summarization"}

    result = resolve_model_for_task(task_type="retrieval_keywords", model_override=None)
    assert result == "fast-model"


@patch("backend.ai.model_routing.Config")
def test_generation_task_uses_quality_model(mock_config):
    mock_config.ENABLE_HETEROGENEOUS_MODELS = True
    mock_config.LLM_MODEL_NAME = "default-model"
    mock_config.LLM_FAST_MODEL_NAME = "fast-model"
    mock_config.LLM_QUALITY_MODEL_NAME = "quality-model"
    mock_config.LLM_FAST_TASK_TYPES = {"retrieval_keywords"}

    result = resolve_model_for_task(task_type="generation_synthesis", model_override=None)
    assert result == "quality-model"


@patch("backend.ai.model_routing.Config")
def test_disabled_routes_to_default(mock_config):
    mock_config.ENABLE_HETEROGENEOUS_MODELS = False
    mock_config.LLM_MODEL_NAME = "default-model"
    mock_config.LLM_FAST_MODEL_NAME = "fast-model"
    mock_config.LLM_QUALITY_MODEL_NAME = "quality-model"
    mock_config.LLM_FAST_TASK_TYPES = {"retrieval_keywords"}

    result = resolve_model_for_task(task_type="retrieval_keywords", model_override=None)
    assert result == "default-model"
