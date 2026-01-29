from datetime import datetime
from app import db
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app import db
from pgvector.sqlalchemy import Vector


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
    # Use pgvector Vector type for fast similarity search in Postgres
    embedding = db.Column(Vector(384))

    project = db.relationship('Project', back_populates='vector')

    def __repr__(self):
        length = None
        try:
            length = len(self.embedding) if self.embedding is not None else 0
        except Exception:
            length = None
        return f"<ProjectVector project_id={self.project_id} len={length}>"
