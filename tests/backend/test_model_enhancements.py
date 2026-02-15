"""Tests for model enhancements: new fields, User relocation, TokenBlocklist."""
import pytest


class TestModelFields:
    """Verify new model fields exist."""

    def test_project_idea_has_is_human_verified(self):
        """ProjectIdea should have is_human_verified field."""
        from backend.core.models import ProjectIdea
        assert hasattr(ProjectIdea, "is_human_verified")
        col = ProjectIdea.__table__.columns["is_human_verified"]
        assert col.default.arg is False

    def test_idea_source_has_is_hallucinated(self):
        """IdeaSource should have is_hallucinated field."""
        from backend.core.models import IdeaSource
        assert hasattr(IdeaSource, "is_hallucinated")
        col = IdeaSource.__table__.columns["is_hallucinated"]
        assert col.default.arg is False

    def test_user_model_in_models_py(self):
        """User should be importable from models.py."""
        from backend.core.models import User
        assert hasattr(User, "email")
        assert hasattr(User, "role")
        assert hasattr(User, "set_password")
        assert hasattr(User, "check_password")

    def test_user_backward_compat_from_app(self):
        """User should still be importable from app.py for backward compat."""
        from backend.core.app import User
        assert hasattr(User, "email")

    def test_token_blocklist_model(self):
        """TokenBlocklist should exist with jti field."""
        from backend.core.models import TokenBlocklist
        assert hasattr(TokenBlocklist, "jti")
        assert hasattr(TokenBlocklist, "created_at")


class TestConfigEnhancements:
    """Verify config changes."""

    def test_min_evidence_required(self):
        from backend.core.config import Config
        assert Config.MIN_EVIDENCE_REQUIRED >= 3

    def test_min_novelty_score(self):
        from backend.core.config import Config
        assert Config.MIN_NOVELTY_SCORE >= 25

    def test_jwt_refresh_exp(self):
        from backend.core.config import Config
        assert Config.JWT_REFRESH_EXP_SECONDS > 0

    def test_jwt_access_token_expires_configured(self):
        from backend.core.config import Config
        assert Config.JWT_EXP_SECONDS > 0


class TestSchemaValidators:
    """Tests for Pydantic schema enum validators."""

    def test_evidence_source_valid_relevance_tier(self):
        """Valid relevance_tier values should pass validation."""
        from backend.generation.schemas import EvidenceSource
        for tier in ("supporting", "contextual", "peripheral"):
            src = EvidenceSource(
                source_id="1", title="Test", url="https://example.com",
                source_type="arxiv", relevance_tier=tier,
                used_for="evidence", problem_type_match="direct"
            )
            assert src.relevance_tier == tier

    def test_evidence_source_invalid_relevance_tier(self):
        """Invalid relevance_tier should be coerced to 'contextual' default."""
        from backend.generation.schemas import EvidenceSource
        src = EvidenceSource(
            source_id="1", title="Test", url="https://example.com",
            source_type="arxiv", relevance_tier="invalid",
            used_for="evidence", problem_type_match="direct"
        )
        assert src.relevance_tier == "contextual"  # coerced to safe default

    def test_evidence_source_valid_problem_type_match(self):
        """Valid problem_type_match values should pass."""
        from backend.generation.schemas import EvidenceSource
        for ptm in ("direct", "indirect", "tangential"):
            src = EvidenceSource(
                source_id="1", title="Test", url="https://example.com",
                source_type="arxiv", relevance_tier="supporting",
                used_for="evidence", problem_type_match=ptm
            )
            assert src.problem_type_match == ptm
