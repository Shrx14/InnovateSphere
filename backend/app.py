# app.py - Main Flask Application
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import bcrypt
import os
import re
import logging
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.engine.url import make_url
from backend.db import db
from backend.auth import create_access_token, jwt_required
from backend.models import Domain, DomainCategory, ProjectIdea, IdeaRequest, IdeaReview, IdeaSource
from backend.ai_registry import get_active_ai_pipeline_version
from backend.retrieval.orchestrator import retrieve_sources
import jwt

# Load environment variables
load_dotenv()

try:
    from backend.config import Config
except ImportError:
    from backend.config import Config

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(
    level=Config.LOG_LEVEL if hasattr(Config, "LOG_LEVEL") else os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    Config.DATABASE_URL or os.getenv('DATABASE_URL')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Config.SECRET_KEY
# Ensure a default schema is selected when connecting to cloud Postgres (e.g. Neon)
# Some managed Postgres instances present an empty search_path by default which
# causes errors like: "no schema has been selected to create in". Setting the
# `options` connect arg ensures connections use the `public` schema.
database_url = Config.DATABASE_URL
engine_opts = {}

if database_url:
    try:
        url = make_url(database_url)

        if url.drivername.startswith("postgresql"):
            host = url.host or ""

            # Neon pooled connections do NOT support startup options
            is_neon_pooler = "neon.tech" in host and "pooler" in host

            if not is_neon_pooler:
                engine_opts = {
                    "pool_pre_ping": True,
                    "connect_args": {
                        "options": "-c statement_timeout=5000"
                    }
                }
            else:
                engine_opts = {
                    "pool_pre_ping": True
                }

    except Exception:
        engine_opts = {}

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

# Initialize extensions
db.init_app(app)
CORS(
    app,
    origins=Config.get_cors_origins(),
    supports_credentials=True,
)
logger.info(
    "CORS configured for origins: %s",
    ", ".join(Config.get_cors_origins())
)

Config.log_config_startup()

# Register blueprints
# ingest_bp removed - legacy deprecated

# Embedding model loading is now centralized in backend/embeddings.py



# User Model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    
    # Profile fields for InnovateSphere
    preferred_domains = db.Column(db.JSON, default=list)  # ['AI/ML', 'Web Dev', etc.]
    skill_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, expert
    saved_ideas = db.Column(db.JSON, default=list)  # List of saved project idea IDs

    # Domain taxonomy (Segment 0.1) - nullable FK to domains.id
    preferred_domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'preferred_domains': self.preferred_domains,
            'skill_level': self.skill_level
        }

# Validation functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""

def validate_username(username):
    if not 6 <= len(username) <= 16:
        return False, "Username must be between 6 and 16 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def get_current_user_id():
    """Get current user ID from JWT token if present, else None"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGO],
        )
        return int(payload.get("sub"))
    except jwt.InvalidTokenError:
        return None

def serialize_public_idea(idea):
    """Serialize idea data for public/anonymous access"""
    domain_name = idea.domain.name if idea.domain else None
    return {
        'id': idea.id,
        'title': idea.title,
        'problem_statement': idea.problem_statement,
        'tech_stack': idea.tech_stack,
        'domain': domain_name
    }

def serialize_full_idea(idea):
    """Serialize complete idea data for authenticated users"""
    public_data = serialize_public_idea(idea)
    public_data.update({
        'description': idea.problem_statement,  # Using problem_statement as description
        'ai_pipeline_version': idea.ai_pipeline_version,
        'is_ai_generated': idea.is_ai_generated,
        'is_public': idea.is_public,
        'created_at': idea.created_at.isoformat(),
        'sources': [
            {
                'source_type': source.source_type,
                'title': source.title,
                'url': source.url,
                'published_date': source.published_date.isoformat() if source.published_date else None,
                'summary': source.summary
            }
            for source in idea.sources
        ],
        'reviews': [
            {
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat()
            }
            for review in idea.reviews
        ],
        'average_rating': round(sum(r.rating for r in idea.reviews) / len(idea.reviews), 1) if idea.reviews else None,
        'requested_count': len(idea.requests)
    })
    return public_data

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'InnovateSphere API is running'}), 200

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'error': 'Email, username, and password are required'}), 400

        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password
        is_valid_password, password_error = validate_password(data['password'])
        if not is_valid_password:
            return jsonify({'error': password_error}), 400

        # Validate username
        is_valid_username, username_error = validate_username(data['username'])
        if not is_valid_username:
            return jsonify({'error': username_error}), 400

        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == data['email']) | (User.username == data['username'])
        ).first()

        if existing_user:
            if existing_user.email == data['email']:
                return jsonify({
                    'error': 'Email already registered',
                    'type': 'EXISTING_EMAIL'
                }), 409
            else:
                return jsonify({'error': 'Username already taken'}), 409

        # Hash password
        password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Create new user
        new_user = User(
            email=data['email'],
            username=data['username'],
            password_hash=password_hash,
            preferred_domains=data.get('preferred_domains', []),
            skill_level=data.get('skill_level', 'beginner')
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    """Change user password endpoint"""
    try:
        data = request.get_json()

        # Validate required fields
        if not all(key in data for key in ['email', 'current_password', 'new_password']):
            return jsonify({'error': 'Current password and new password are required'}), 400

        # Find user by email
        user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify current password
        if not bcrypt.checkpw(
            data['current_password'].encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            return jsonify({'error': 'Current password is incorrect'}), 401

        # Hash and update new password
        new_password_hash = bcrypt.hashpw(
            data['new_password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user.password_hash = new_password_hash
        db.session.commit()

        return jsonify({
            'message': 'Password updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Password change failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        # Find user by email
        user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Verify password
        if not bcrypt.checkpw(
            data['password'].encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Determine role based on config
        role = "admin" if user.username in Config.ADMIN_USERNAMES else "user"

        # Generate JWT token
        token = create_access_token(user_id=user.id, role=role, username=user.username, email=user.email)

        return jsonify({
            'message': 'Login successful',
            'access_token': token
        }), 200

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@app.route('/api/check_novelty', methods=['POST'])
def check_novelty():
    return jsonify({
        "error": "Legacy novelty scoring deprecated"
    }), 410











@app.route('/api/generate-idea', methods=['POST'])
def handle_generate_idea():
    return jsonify({
        "error": "Legacy AI pipeline deprecated"
    }), 410


@app.route('/api/ai/pipeline-version', methods=['GET'])
def get_pipeline_version():
    """Get the active AI pipeline version"""
    version = get_active_ai_pipeline_version()
    return jsonify({"version": version}), 200


@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get all domains with their categories"""
    domains = Domain.query.all()
    return jsonify({"domains": [domain.to_dict() for domain in domains]}), 200

@app.route('/api/public/ideas', methods=['GET'])
def get_public_ideas():
    """Get list of public project ideas with optional search and domain filter"""
    query = ProjectIdea.query.filter_by(is_public=True)

    # Keyword search
    q = request.args.get('q')
    if q:
        query = query.filter(
            db.or_(
                ProjectIdea.title.contains(q),
                ProjectIdea.problem_statement.contains(q),
                ProjectIdea.tech_stack.contains(q)
            )
        )

    # Domain filter
    domain_id = request.args.get('domain_id')
    if domain_id:
        query = query.filter_by(domain_id=domain_id)

    ideas = query.all()
    return jsonify({"ideas": [serialize_public_idea(idea) for idea in ideas]}), 200

@app.route('/api/ideas/<int:idea_id>', methods=['GET'])
def get_idea(idea_id):
    """Get idea details - limited for anonymous, full for authenticated"""
    idea = ProjectIdea.query.get_or_404(idea_id)

    user_id = get_current_user_id()
    if user_id:
        # Authenticated: return full details
        return jsonify(serialize_full_idea(idea)), 200
    else:
        # Anonymous: return limited details with login prompt
        public_data = serialize_public_idea(idea)
        public_data['requires_login'] = True
        public_data['message'] = "Sign in to view full details and novelty analysis."
        return jsonify(public_data), 200

@app.route('/api/ideas/<int:idea_id>/request', methods=['POST'])
@jwt_required()
def request_idea(idea_id):
    """Authenticated users can request an idea (track demand)"""
    idea = ProjectIdea.query.get_or_404(idea_id)

    # Check if already requested
    existing_request = IdeaRequest.query.filter_by(user_id=g.current_user_id, idea_id=idea_id).first()
    if existing_request:
        return jsonify({"message": "Idea already requested"}), 200

    # Create new request
    new_request = IdeaRequest(user_id=g.current_user_id, idea_id=idea_id)
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"message": "Idea requested successfully"}), 201

@app.route('/api/ideas/<int:idea_id>/review', methods=['POST'])
@jwt_required()
def review_idea(idea_id):
    """Authenticated users can submit a review (rating + optional comment)"""
    idea = ProjectIdea.query.get_or_404(idea_id)
    data = request.get_json()

    if not data or 'rating' not in data:
        return jsonify({"error": "Rating is required"}), 400

    rating = data['rating']
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

    # Check if already reviewed (enforced by unique constraint, but check for better error)
    existing_review = IdeaReview.query.filter_by(user_id=g.current_user_id, idea_id=idea_id).first()
    if existing_review:
        return jsonify({"error": "You have already reviewed this idea"}), 409

    # Create new review
    new_review = IdeaReview(
        user_id=g.current_user_id,
        idea_id=idea_id,
        rating=rating,
        comment=data.get('comment')
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"message": "Review submitted successfully"}), 201

# Analytics APIs (Segment 1.3)

@app.route('/api/analytics/user/overview', methods=['GET'])
@jwt_required()
def user_overview():
    """Get user's analytics overview"""
    user_id = g.current_user_id

    # Total requests
    total_requests = IdeaRequest.query.filter_by(user_id=user_id).count()

    # Total reviews
    total_reviews = IdeaReview.query.filter_by(user_id=user_id).count()

    # Preferred domain
    user = User.query.get(user_id)
    preferred_domain = None
    if user.preferred_domain_id:
        domain = Domain.query.get(user.preferred_domain_id)
        preferred_domain = domain.name if domain else None

    # Top domain by requests
    top_domain_result = db.session.query(
        Domain.name,
        func.count(IdeaRequest.id).label('request_count')
    ).join(ProjectIdea, Domain.id == ProjectIdea.domain_id)\
     .join(IdeaRequest, ProjectIdea.id == IdeaRequest.idea_id)\
     .filter(IdeaRequest.user_id == user_id)\
     .group_by(Domain.id, Domain.name)\
     .order_by(func.count(IdeaRequest.id).desc())\
     .first()

    top_domain = top_domain_result.name if top_domain_result else None

    return jsonify({
        "total_requests": total_requests,
        "total_reviews": total_reviews,
        "preferred_domain": preferred_domain,
        "top_domain": top_domain
    }), 200

@app.route('/api/analytics/user/top-ideas', methods=['GET'])
@jwt_required()
def user_top_ideas():
    """Get user's top requested ideas"""
    user_id = g.current_user_id

    # Top ideas by request count
    results = db.session.query(
        ProjectIdea.id.label('idea_id'),
        ProjectIdea.title,
        func.count(IdeaRequest.id).label('request_count'),
        Domain.name.label('domain')
    ).join(IdeaRequest, ProjectIdea.id == IdeaRequest.idea_id)\
     .outerjoin(Domain, ProjectIdea.domain_id == Domain.id)\
     .filter(IdeaRequest.user_id == user_id)\
     .group_by(ProjectIdea.id, ProjectIdea.title, Domain.name)\
     .order_by(func.count(IdeaRequest.id).desc())\
     .limit(5)\
     .all()

    top_ideas = [
        {
            "idea_id": r.idea_id,
            "title": r.title,
            "request_count": r.request_count,
            "domain": r.domain
        }
        for r in results
    ]

    return jsonify({"ideas": top_ideas}), 200

@app.route('/api/analytics/admin/domains', methods=['GET'])
@jwt_required(required_role="admin")
def admin_domains():
    """Get domain-wise analytics"""
    results = db.session.query(
        Domain.name.label('domain'),
        func.count(ProjectIdea.id).label('idea_count'),
        func.count(IdeaRequest.id).label('request_count'),
        func.avg(IdeaReview.rating).label('average_rating')
    ).outerjoin(ProjectIdea, Domain.id == ProjectIdea.domain_id)\
     .outerjoin(IdeaRequest, ProjectIdea.id == IdeaRequest.idea_id)\
     .outerjoin(IdeaReview, ProjectIdea.id == IdeaReview.idea_id)\
     .group_by(Domain.id, Domain.name)\
     .all()

    domains = [
        {
            "domain": r.domain,
            "idea_count": r.idea_count,
            "request_count": r.request_count,
            "average_rating": round(float(r.average_rating), 1) if r.average_rating else None
        }
        for r in results
    ]

    return jsonify({"domains": domains}), 200

@app.route('/api/analytics/admin/ideas/top', methods=['GET'])
@jwt_required(required_role="admin")
def admin_top_ideas():
    """Get top ideas by demand"""
    results = db.session.query(
        ProjectIdea.id.label('idea_id'),
        ProjectIdea.title,
        Domain.name.label('domain'),
        func.count(IdeaRequest.id).label('request_count'),
        func.avg(IdeaReview.rating).label('average_rating')
    ).outerjoin(Domain, ProjectIdea.domain_id == Domain.id)\
     .outerjoin(IdeaRequest, ProjectIdea.id == IdeaRequest.idea_id)\
     .outerjoin(IdeaReview, ProjectIdea.id == IdeaReview.idea_id)\
     .group_by(ProjectIdea.id, ProjectIdea.title, Domain.name)\
     .order_by(func.count(IdeaRequest.id).desc())\
     .limit(10)\
     .all()

    top_ideas = [
        {
            "idea_id": r.idea_id,
            "title": r.title,
            "domain": r.domain,
            "request_count": r.request_count,
            "average_rating": round(float(r.average_rating), 1) if r.average_rating else None
        }
        for r in results
    ]

    return jsonify({"ideas": top_ideas}), 200

@app.route('/api/analytics/admin/time-trends', methods=['GET'])
@jwt_required(required_role="admin")
def admin_time_trends():
    """Get request volume grouped by date and domain"""
    results = db.session.query(
        func.date(IdeaRequest.requested_at).label('date'),
        Domain.name.label('domain'),
        func.count(IdeaRequest.id).label('request_count')
    ).join(ProjectIdea, IdeaRequest.idea_id == ProjectIdea.id)\
     .outerjoin(Domain, ProjectIdea.domain_id == Domain.id)\
     .group_by(func.date(IdeaRequest.requested_at), Domain.name)\
     .order_by(func.date(IdeaRequest.requested_at), Domain.name)\
     .all()

    trends = [
        {
            "date": str(r.date),
            "domain": r.domain,
            "request_count": r.request_count
        }
        for r in results
    ]

    return jsonify({"trends": trends}), 200

@app.route('/api/retrieval/sources', methods=['POST'])
@jwt_required()
def retrieve_sources_endpoint():
    """Retrieve sources from external APIs (arXiv, GitHub) with optional semantic filtering"""
    data = request.get_json()

    if not data or 'query' not in data or 'domain_id' not in data:
        return jsonify({"error": "query and domain_id are required"}), 400

    query = data['query']
    domain_id = data['domain_id']
    semantic_filter = data.get('semantic_filter', False)
    similarity_threshold = data.get('similarity_threshold', 0.6)

    # Validate similarity_threshold
    if not isinstance(similarity_threshold, (int, float)) or not 0 <= similarity_threshold <= 1:
        return jsonify({"error": "similarity_threshold must be a float between 0 and 1"}), 400

    # Fetch domain name from database
    domain = Domain.query.get(domain_id)
    if not domain:
        return jsonify({"error": "Invalid domain_id"}), 400

    domain_name = domain.name

    # Call retrieval function with semantic options
    result = retrieve_sources(
        query=query,
        domain=domain_name,
        semantic_filter=semantic_filter,
        similarity_threshold=similarity_threshold
    )

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
