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
