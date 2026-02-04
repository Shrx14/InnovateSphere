from datetime import datetime
from backend.db import db


# ⚠️ LEGACY KNOWLEDGE TABLE — deprecated
class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1024), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    domain_id = db.Column(db.Integer, db.ForeignKey("domains.id"), nullable=False)


class AiPipelineVersion(db.Model):
    __tablename__ = "ai_pipeline_versions"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PromptVersion(db.Model):
    __tablename__ = "prompt_versions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prompts_json = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id"), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    idea = db.relationship("ProjectIdea", back_populates="requests")


class IdeaSource(db.Model):
    __tablename__ = "idea_sources"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id"), nullable=False)

    source_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1024), nullable=False)
    summary = db.Column(db.Text)
    published_date = db.Column(db.Date)

    idea = db.relationship("ProjectIdea", back_populates="sources")


class IdeaReview(db.Model):
    __tablename__ = "idea_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    idea = db.relationship("ProjectIdea", back_populates="reviews")

    __table_args__ = (
        db.UniqueConstraint("user_id", "idea_id", name="unique_user_idea_review"),
    )


class IdeaFeedback(db.Model):
    __tablename__ = "idea_feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id"), nullable=False)

    feedback_type = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    idea = db.relationship("ProjectIdea", back_populates="feedbacks")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "idea_id", "feedback_type",
            name="unique_user_idea_feedback_type"
        ),
        db.Index("idx_feedback_type", "feedback_type"),
    )


class AdminVerdict(db.Model):
    __tablename__ = "admin_verdicts"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(
        db.Integer, db.ForeignKey("project_ideas.id"), nullable=False, unique=True
    )
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    verdict = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    idea = db.relationship("ProjectIdea", back_populates="admin_verdict")


# idea_views table added manually in Neon (no migration)
class IdeaView(db.Model):
    __tablename__ = "idea_views"

    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey("project_ideas.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
