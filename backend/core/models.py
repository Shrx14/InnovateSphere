from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.core.db import db


def _utcnow():
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


# ⚠️ LEGACY KNOWLEDGE TABLE — deprecated
class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1024), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    vector = db.relationship("ProjectVector", back_populates="project", uselist=False)


class ProjectVector(db.Model):
    __tablename__ = "project_vectors"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, unique=True
    )
    embedding = db.Column(db.JSON)

    project = db.relationship("Project", back_populates="vector")


class Domain(db.Model):
    __tablename__ = "domains"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    categories = db.relationship("DomainCategory", backref="domain", lazy=True)
    project_ideas = db.relationship("ProjectIdea", back_populates="domain", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "categories": [
                {"id": c.id, "name": c.name} for c in self.categories
            ],
        }


class DomainCategory(db.Model):
    __tablename__ = "domain_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("domain_id", "name", name="unique_domain_category_name"),
        db.Index("idx_domain_categories_domain_id", "domain_id"),
    )


class AiPipelineVersion(db.Model):
    __tablename__ = "ai_pipeline_versions"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


class BiasProfile(db.Model):
    __tablename__ = "bias_profiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    version = db.Column(db.String(50), nullable=False)
    rules = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        db.Index("idx_bias_profiles_version", "version"),
        db.Index("idx_bias_profiles_active", "is_active"),
    )


class PromptVersion(db.Model):
    __tablename__ = "prompt_versions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prompts_json = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


# ----------------------------
# Analytics + HITL Core
# ----------------------------

class ProjectIdea(db.Model):
    __tablename__ = "project_ideas"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

    problem_statement = db.Column(db.Text, nullable=False)
    problem_statement_json = db.Column(db.JSON, nullable=False)

    tech_stack = db.Column(db.Text, nullable=False)
    tech_stack_json = db.Column(db.JSON, nullable=False)

    domain_id = db.Column(db.Integer, db.ForeignKey("domains.id"))
    ai_pipeline_version = db.Column(db.String(50), nullable=False)

    is_ai_generated = db.Column(db.Boolean, nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    is_human_verified = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    # view_count added manually in Neon (no migration)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    quality_score_cached = db.Column(db.Integer)
    novelty_score_cached = db.Column(db.Integer)
    novelty_context = db.Column(db.JSON)
    idea_embedding = db.Column(db.JSON, nullable=True)

    # Relationships
    domain = db.relationship("Domain", back_populates="project_ideas")
    requests = db.relationship("IdeaRequest", back_populates="idea", lazy=True)
    sources = db.relationship(
        "IdeaSource", back_populates="idea", lazy=True, cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "IdeaReview", back_populates="idea", lazy=True, cascade="all, delete-orphan"
    )

    feedbacks = db.relationship(
        "IdeaFeedback",
        back_populates="idea",
        lazy=True,
        cascade="all, delete-orphan",
    )

    admin_verdict = db.relationship(
        "AdminVerdict",
        back_populates="idea",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("idx_project_ideas_domain_id", "domain_id"),
        db.Index("idx_project_ideas_created_at", "created_at"),
        db.Index("idx_project_ideas_is_public", "is_public"),
        db.Index("idx_project_ideas_is_validated", "is_validated"),
    )

    # ----------------------------
    # HITL Metrics
    # ----------------------------

    @property
    def quality_score(self):
        base = 50

        weights = {
            "high_quality": 15,
            "factual_error": -20,
            "hallucinated_source": -25,
            "weak_novelty": -15,
            "poor_justification": -10,
            "unclear_scope": -10,
        }

        counts = {}
        for fb in self.feedbacks:
            counts[fb.feedback_type] = counts.get(fb.feedback_type, 0) + 1

        raw_feedback_impact = sum(
            min(count, 3) * weights.get(ftype, 0)
            for ftype, count in counts.items()
        )

        feedback_impact = max(raw_feedback_impact, -40)

        evidence_bonus = min(len(self.sources) * 2, 20)

        avg_rating = (
            sum(r.rating for r in self.reviews) / len(self.reviews)
            if self.reviews else 3
        )
        rating_bonus = (avg_rating - 3) * 2

        verdict_multiplier = 1.0
        if self.admin_verdict:
            verdict_multiplier = {
                "validated": 1.2,
                "downgraded": 0.8,
                "rejected": 0.5,
            }.get(self.admin_verdict.verdict, 1.0)

        score = (
            base + feedback_impact + evidence_bonus + rating_bonus
        ) * verdict_multiplier

        return max(0, min(100, int(score)))

    @property
    def hallucination_risk_level(self):
        count = sum(
            1 for fb in self.feedbacks if fb.feedback_type == "hallucinated_source"
        )
        if count >= 3:
            return "high"
        if count >= 1 or len(self.sources) < 3:
            return "medium"
        return "low"

    @property
    def evidence_strength(self):
        types = {s.source_type for s in self.sources}
        factual_errors = sum(
            1 for fb in self.feedbacks if fb.feedback_type == "factual_error"
        )

        if len(self.sources) >= 5 and len(types) >= 3 and factual_errors == 0:
            return "high"
        if len(self.sources) >= 3 and len(types) >= 2 and factual_errors <= 1:
            return "medium"
        return "low"

    @property
    def novelty_confidence(self):
        weak = sum(1 for fb in self.feedbacks if fb.feedback_type == "weak_novelty")
        good = sum(1 for fb in self.feedbacks if fb.feedback_type == "high_quality")

        if weak >= 2:
            return "low"
        if good >= 1 and weak == 0:
            return "high"
        return "medium"


class IdeaRequest(db.Model):
    __tablename__ = "idea_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)
    requested_at = db.Column(db.DateTime, default=_utcnow)

    idea = db.relationship("ProjectIdea", back_populates="requests")

    __table_args__ = (
        db.Index("idx_idea_requests_user_id", "user_id"),
        db.Index("idx_idea_requests_idea_id", "idea_id"),
    )


class IdeaSource(db.Model):
    __tablename__ = "idea_sources"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)

    source_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1024), nullable=False)
    summary = db.Column(db.Text)
    published_date = db.Column(db.Date)
    is_hallucinated = db.Column(db.Boolean, default=False, nullable=False)

    idea = db.relationship("ProjectIdea", back_populates="sources")

    __table_args__ = (
        db.Index("idx_idea_sources_idea_id", "idea_id"),
        db.UniqueConstraint("idea_id", "url", name="unique_idea_source_url"),
    )


class IdeaReview(db.Model):
    __tablename__ = "idea_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)

    idea = db.relationship("ProjectIdea", back_populates="reviews")

    __table_args__ = (
        db.UniqueConstraint("user_id", "idea_id", name="unique_user_idea_review"),
        db.Index("idx_idea_reviews_idea_id", "idea_id"),
        db.Index("idx_idea_reviews_user_id", "user_id"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )


class IdeaFeedback(db.Model):
    __tablename__ = "idea_feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)

    feedback_type = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)

    idea = db.relationship("ProjectIdea", back_populates="feedbacks")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "idea_id", "feedback_type",
            name="unique_user_idea_feedback_type"
        ),
        db.Index("idx_feedback_type", "feedback_type"),
        db.Index("idx_idea_feedbacks_idea_id", "idea_id"),
        db.Index("idx_idea_feedbacks_user_id", "user_id"),
        db.CheckConstraint(
            "feedback_type IN ('upvote', 'downvote', 'bookmark', 'report', 'helpful', 'not_helpful', 'factual_error', 'hallucinated_source', 'weak_novelty', 'poor_justification', 'unclear_scope', 'high_quality')",
            name="ck_idea_feedbacks_type_valid"
        ),
    )


class AdminVerdict(db.Model):
    __tablename__ = "admin_verdicts"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(
        db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    verdict = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    idea = db.relationship("ProjectIdea", back_populates="admin_verdict")

    __table_args__ = (
        db.Index("idx_admin_verdicts_admin_id", "admin_id"),
        db.CheckConstraint(
            "verdict IN ('validated', 'downgraded', 'rejected')",
            name="check_verdict_valid"
        ),
    )


# idea_views table added manually in Neon (no migration)
class IdeaView(db.Model):
    __tablename__ = "idea_views"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    viewed_at = db.Column(db.DateTime, default=_utcnow)

    __table_args__ = (
        db.Index("idx_idea_views_idea_id", "idea_id"),
        db.Index("idx_idea_views_user_id", "user_id"),
        db.Index("idx_idea_views_viewed_at", "viewed_at"),
    )


# ====================================================
# AUDIT & TRACING MODELS (Critical Gap Fixes)
# ====================================================

class GenerationTrace(db.Model):
    """
    Audit trail for idea generation.
    Stores the complete reasoning chain, phases, prompts, and constraints active during generation.
    """
    __tablename__ = "generation_traces"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Input conditioning (Phase 0)
    query = db.Column(db.Text, nullable=False)  # User query
    domain_name = db.Column(db.String(100), nullable=False)
    
    # Pipeline configuration
    ai_pipeline_version = db.Column(db.String(50), nullable=False)
    bias_profile_version = db.Column(db.String(50))
    prompt_version = db.Column(db.String(50))

    # Generation phases
    phase_0_output = db.Column(db.JSON)  # Input conditioning result
    phase_1_output = db.Column(db.JSON)  # Retrieved sources
    phase_2_output = db.Column(db.JSON)  # Idea space analysis (landscape narrative)
    phase_3_output = db.Column(db.JSON)  # Constraint-guided synthesis
    phase_4_output = db.Column(db.JSON)  # Evidence validation

    # Constraint tracking
    constraints_active = db.Column(db.JSON)  # Serialized constraints that were active
    bias_penalties_applied = db.Column(db.JSON)  # Breakdown of bias penalties

    # Timing
    retrieval_time_ms = db.Column(db.Integer)
    analysis_time_ms = db.Column(db.Integer)
    generation_time_ms = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=_utcnow)

    idea = db.relationship("ProjectIdea", foreign_keys=[idea_id])
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.Index("idx_generation_traces_idea_id", "idea_id"),
        db.Index("idx_generation_traces_user_id", "user_id"),
        db.Index("idx_generation_traces_created_at", "created_at"),
    )


class ViewEvent(db.Model):
    """
    Tracks user engagement: when users view ideas, for how long, and what they do.
    Used for analytics and understanding user behavior.
    """
    __tablename__ = "view_events"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # nullable for anon views
    
    # Event metadata
    event_type = db.Column(db.String(50), nullable=False)  # 'view', 'share', 'feedback', 'review'
    view_duration_seconds = db.Column(db.Integer)  # How long user spent on idea
    
    # Referral tracking
    referrer = db.Column(db.String(255))  # How user reached this idea (search, browse, share, etc.)
    search_query = db.Column(db.Text)  # If from search, what was the query
    
    created_at = db.Column(db.DateTime, default=_utcnow)

    idea = db.relationship("ProjectIdea", foreign_keys=[idea_id])
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.Index("idx_view_events_idea_id", "idea_id"),
        db.Index("idx_view_events_user_id", "user_id"),
        db.Index("idx_view_events_created_at", "created_at"),
        db.Index("idx_view_events_event_type", "event_type"),
    )


class SearchQuery(db.Model):
    """
    Audit log of search queries for analytics and discovery patterns.
    Helps identify user demand and guide algorithm improvements.
    """
    __tablename__ = "search_queries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # nullable for anon searches
    
    query_text = db.Column(db.Text, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey("domains.id", ondelete="SET NULL"), nullable=True)
    
    # Results
    result_count = db.Column(db.Integer)
    user_action = db.Column(db.String(50))  # 'clicked_idea', 'refined_query', 'abandoned', 'no_results'
    clicked_idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id", ondelete="SET NULL"), nullable=True)
    
    # Session tracking
    session_id = db.Column(db.String(100))  # To group related searches
    
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    domain = db.relationship("Domain", foreign_keys=[domain_id])

    __table_args__ = (
        db.Index("idx_search_queries_user_id", "user_id"),
        db.Index("idx_search_queries_created_at", "created_at"),
        db.Index("idx_search_queries_domain_id", "domain_id"),
        db.Index("idx_search_queries_session_id", "session_id"),
    )


class AbuseEvent(db.Model):
    """
    Records suspicious or rate-limit-related events for users.
    """
    __tablename__ = "abuse_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # e.g., 'generation_attempt'
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=_utcnow)

    __table_args__ = (
        db.Index("idx_abuse_events_user_id", "user_id"),
        db.Index("idx_abuse_events_event_type", "event_type"),
        db.Index("idx_abuse_events_created_at", "created_at"),
    )


# ====================================================
# USER MODEL (moved from core/app.py for proper import ordering)
# ====================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    preferred_domains = db.Column(db.JSON, default=list)
    skill_level = db.Column(db.String(20), default="beginner")
    saved_ideas = db.Column(db.JSON, default=list)

    preferred_domain_id = db.Column(
        db.Integer, db.ForeignKey("domains.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('user', 'admin')",
            name="check_user_role_valid"
        ),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ====================================================
# JWT TOKEN BLOCKLIST (for real logout)
# ====================================================

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
