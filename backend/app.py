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

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://innovate_admin:innovate_pass_2025@localhost:5432/innovatesphere_dev')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)



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
    db.create_all()

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











if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)