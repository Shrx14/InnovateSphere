# app.py - Main Flask Application
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import bcrypt
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from backend.config import Config
except ImportError:
    from config import Config

# Initialize Flask app
app = Flask(__name__)

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
DATABASE_URL = app.config.get('SQLALCHEMY_DATABASE_URI', '')

# Neon pooler rejects startup `options` containing `search_path`. Only add
# the `-csearch_path` connect arg for servers that support it (e.g., local
# Postgres or non-pooled connections).
engine_opts = {}
if DATABASE_URL and 'neon.tech' not in DATABASE_URL:
    engine_opts = {
        'connect_args': {'options': '-csearch_path=public'}
    }

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_opts

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

Config.log_config_startup()

# --- Embedding model (loaded on startup) ---
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    # load lazily below to avoid startup noise if package missing
    _EMBED_MODEL_NAME = Config.EMBEDDING_MODEL
    print('Embedding model configured:', _EMBED_MODEL_NAME)
    _embedding_model = None
except Exception:
    _embedding_model = None



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



# Create tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Don't crash the app on DB init failure — print a helpful warning and continue.
        print(f"⚠️ Warning: could not initialize database (will continue without DB): {e}")
        print("If this persists, check DATABASE_URL and your Postgres credentials.")

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

        # In a production app, you'd generate a JWT token here
        # For now, we'll just return user data
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


# Novelty checking endpoint (uses sentence-transformers model to embed input
# and compares against stored embeddings for projects).
@app.route('/api/check_novelty', methods=['POST'])
def check_novelty():
    data = request.get_json() or {}
    text = data.get('description') or data.get('text') or ''
    if not text or not text.strip():
        return jsonify({'error': 'description is required'}), 400

    # lazy-load model
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'))
        except Exception as e:
            print('Failed to load embedding model:', e)
            return jsonify({'error': 'Embedding model unavailable on server'}), 500

    try:
        # create embedding for user text
        idea_emb = _embedding_model.encode(text)

        # import models here to avoid circular imports when app starts
        from models import Project, ProjectVector
        # Attempt DB-level similarity using pgvector (fast path)
        try:
            idea_list = list(map(float, idea_emb))
            # Query DB for top-5 closest by cosine distance
            q = db.session.query(
                Project,
                ProjectVector.embedding.cosine_distance(idea_list).label('distance')
            ).join(ProjectVector, Project.id == ProjectVector.project_id).order_by('distance').limit(5)

            rows = q.all()
            if not rows:
                return jsonify({'novelty_score': 100.0, 'similar_projects': []}), 200

            # rows: list of (Project, distance)
            closest_distance = rows[0][1]
            # Map distance (cosine distance) to novelty score: 0 -> 0 novelty, 1 -> 100
            novelty_score = round(min(max(float(closest_distance) * 100.0, 0.0), 100.0), 2)

            similar_projects = []
            for proj, dist in rows:
                similarity_percent = max(0.0, 100.0 - (float(dist) * 100.0))
                similar_projects.append({
                    'id': proj.id,
                    'title': proj.title,
                    'url': proj.url,
                    'description': proj.description,
                    'similarity_percent': round(similarity_percent, 2)
                })

            return jsonify({'novelty_score': novelty_score, 'similar_projects': similar_projects}), 200

        except Exception as db_exc:
            # Fallback to in-Python similarity if DB-level query fails
            print('DB-level pgvector similarity failed, falling back to in-Python compute:', db_exc)

            vectors = ProjectVector.query.join(Project).all()
            if not vectors:
                return jsonify({'novelty_score': 100.0, 'similar_projects': []})

            sims = []
            idea_arr = np.array(idea_emb, dtype=float)
            idea_norm = np.linalg.norm(idea_arr)
            for pv in vectors:
                if not pv.embedding:
                    continue
                emb = np.array(pv.embedding, dtype=float)
                denom = (np.linalg.norm(emb) * idea_norm)
                if denom == 0:
                    cos = 0.0
                else:
                    cos = float(np.dot(idea_arr, emb) / denom)
                sims.append((pv.project, cos))

            sims.sort(key=lambda x: x[1], reverse=True)
            top_n = sims[:5]
            most_sim = top_n[0][1] if top_n else 0.0
            novelty_score = round(max(0.0, (1.0 - most_sim)) * 100.0, 2)
            similar_projects = []
            for proj, cos in top_n:
                similar_projects.append({
                    'id': proj.id,
                    'title': proj.title,
                    'url': proj.url,
                    'description': proj.description,
                    'similarity_percent': round(cos * 100.0, 2)
                })

            return jsonify({'novelty_score': novelty_score, 'similar_projects': similar_projects}), 200

    except Exception as e:
        print('Error in novelty endpoint:', e)
        return jsonify({'error': 'Failed to process novelty request'}), 500











@app.route('/api/generate-idea', methods=['POST'])
def handle_generate_idea():
    """
    Handles a request to generate a new project idea using the RAG chain.
    """
    data = request.get_json()
    user_query = data.get('query') # Get the user's raw query

    if not user_query:
        return jsonify({'error': 'A query is required.'}), 400

    # --- THIS IS THE FIX ---
    # We "wrap" the user's topic in a clear instruction for the RAG chain.
    # You can customize this prompt to be more specific.
    rag_query = f"Generate a creative and novel project idea for a student about: {user_query}"
    # --- END OF FIX ---

    try:
        # Import RAG chain lazily so the server can start even if ML deps are missing
        try:
            from rag_chain import generate_idea
        except Exception as import_err:
            print(f"RAG chain unavailable: {import_err}")
            return jsonify({'error': 'Idea generation is currently unavailable.'}), 503

        # Call the RAG chain with the new, improved query
        result = generate_idea(rag_query)

        # Extract relevant info to send to frontend
        # Build response including clickable source URLs where available.
        source_documents = []
        for doc in result.get('source_documents', []):
            meta = getattr(doc, 'metadata', {}) or {}
            title = meta.get('title') or meta.get('paper_title') or 'Unknown Title'
            # Determine URL: prefer explicit url, then arxiv id, then source
            url = meta.get('url') or meta.get('source') or None
            # If an arXiv id is present, build a canonical arXiv URL
            arxiv_id = meta.get('arxiv_id') or meta.get('arxiv')
            if not url and arxiv_id:
                url = f"https://arxiv.org/abs/{arxiv_id}"

            summary = ''
            try:
                summary = (doc.page_content or '')[:250]
                if len(doc.page_content or '') > 250:
                    summary += '...'
            except Exception:
                summary = ''

            source_documents.append({
                'title': title,
                'summary': summary,
                'url': url,
                'raw_metadata': meta
            })

        response_data = {
            "generated_text": result.get('result'),
            "source_documents": source_documents
        }
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error during idea generation: {e}")
        return jsonify({'error': 'Failed to generate idea.'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)