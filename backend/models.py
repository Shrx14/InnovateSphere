from datetime import datetime
from backend.db import db


# ⚠️ LEGACY KNOWLEDGE TABLE — deprecated
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)  # 'github' | 'arxiv' | 'other'
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(1024), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vector = db.relationship('ProjectVector', back_populates='project', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'created_at': self.created_at.isoformat()
        }


class ProjectVector(db.Model):
    __tablename__ = 'project_vectors'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, unique=True)
    # Legacy embedding column, deprecated
    embedding = db.Column(db.JSON)

    project = db.relationship('Project', back_populates='vector')

    def __repr__(self):
        length = None
        try:
            length = len(self.embedding) if self.embedding is not None else 0
        except Exception:
            length = None
        return f"<ProjectVector project_id={self.project_id} len={length}>"


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    categories = db.relationship('DomainCategory', backref='domain', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'categories': [cat.to_dict() for cat in self.categories]
        }


class DomainCategory(db.Model):
    __tablename__ = 'domain_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class AiPipelineVersion(db.Model):
    __tablename__ = 'ai_pipeline_versions'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


# Analytics Models (Segment 1.1) - Analytics-first database schema for tracking project ideas, user requests, popularity, and feedback

class ProjectIdea(db.Model):
    """
    Represents a generated or stored project idea.
    Purpose: Stores ideas shown to users for popularity tracking, novelty baselines, and analytics dashboards.
    """
    __tablename__ = 'project_ideas'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    problem_statement = db.Column(db.Text, nullable=False)
    tech_stack = db.Column(db.Text, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=True)
    ai_pipeline_version = db.Column(db.String(50), nullable=False)
    is_ai_generated = db.Column(db.Boolean, nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    requests = db.relationship('IdeaRequest', back_populates='idea', lazy=True)
    sources = db.relationship('IdeaSource', back_populates='idea', lazy=True)
    reviews = db.relationship('IdeaReview', back_populates='idea', lazy=True)

    # Indexes for analytics queries
    __table_args__ = (
        db.Index('idx_project_ideas_domain_id', 'domain_id'),
        db.Index('idx_project_ideas_created_at', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'problem_statement': self.problem_statement,
            'tech_stack': self.tech_stack,
            'domain_id': self.domain_id,
            'ai_pipeline_version': self.ai_pipeline_version,
            'is_ai_generated': self.is_ai_generated,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat()
        }


class IdeaRequest(db.Model):
    """
    Tracks each time a user requests an idea.
    Purpose: Tracks demand, enables "most recommended ideas", and domain-wise trends over time.
    """
    __tablename__ = 'idea_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey('project_ideas.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='idea_requests', lazy=True)
    idea = db.relationship('ProjectIdea', back_populates='requests', lazy=True)

    # Indexes for analytics queries
    __table_args__ = (
        db.Index('idx_idea_requests_user_id', 'user_id'),
        db.Index('idx_idea_requests_idea_id', 'idea_id'),
        db.Index('idx_idea_requests_requested_at', 'requested_at'),
    )


class IdeaSource(db.Model):
    """
    Stores metadata references used to generate ideas.
    Purpose: Provides transparency, explainability, and inputs for future novelty scoring.
    """
    __tablename__ = 'idea_sources'
    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('project_ideas.id'), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # e.g., "arxiv", "github", "blog"
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1024), nullable=False)
    published_date = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text, nullable=True)

    # Relationships
    idea = db.relationship('ProjectIdea', back_populates='sources', lazy=True)

    # Indexes for analytics queries
    __table_args__ = (
        db.Index('idx_idea_sources_idea_id', 'idea_id'),
    )


class IdeaReview(db.Model):
    """
    Tracks user feedback on ideas.
    Purpose: Provides human-in-the-loop signals for quality ranking and analytics.
    Rules: One review per user per idea (enforced via unique constraint).
    """
    __tablename__ = 'idea_reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id = db.Column(db.Integer, db.ForeignKey('project_ideas.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='idea_reviews', lazy=True)
    idea = db.relationship('ProjectIdea', back_populates='reviews', lazy=True)

    # Unique constraint: one review per user per idea
    __table_args__ = (
        db.UniqueConstraint('user_id', 'idea_id', name='unique_user_idea_review'),
        db.Index('idx_idea_reviews_user_id', 'user_id'),
        db.Index('idx_idea_reviews_idea_id', 'idea_id'),
        db.Index('idx_idea_reviews_created_at', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'idea_id': self.idea_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }
