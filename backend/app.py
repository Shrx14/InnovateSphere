# app.py - Main Flask Application
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import bcrypt
import os
import re
import pyotp
import phonenumbers
from twilio.rest import Client
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

# Initialize Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Test mode configuration
TEST_MODE = True  # Force test mode for development
if TEST_MODE:
    # Use Twilio's official test credentials
    TWILIO_TEST_ACCOUNT_SID = 'ACb6e8ff482ade7c1ff7e5dbe733232d65'  # Twilio test Account SID
    TWILIO_TEST_AUTH_TOKEN = '745db77752dd7802c37b1432d2755a24'   # Twilio test Auth Token
    TWILIO_TEST_NUMBER = '+15005550006'  # Twilio's magic test number

def get_twilio_client():
    """Get a new Twilio client instance"""
    try:
        if TEST_MODE:
            return Client(TWILIO_TEST_ACCOUNT_SID, TWILIO_TEST_AUTH_TOKEN)
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"Error creating Twilio client: {str(e)}")
        return None

def get_twilio_number():
    """Get the appropriate Twilio phone number"""
    return TWILIO_TEST_NUMBER if TEST_MODE else TWILIO_PHONE_NUMBER

# User Model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 2FA fields
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    phone_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
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
            'skill_level': self.skill_level,
            'phone_number': self.phone_number,
            'phone_verified': self.phone_verified,
            'two_factor_enabled': self.two_factor_enabled
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

def validate_phone_number(phone_number):
    try:
        parsed = phonenumbers.parse(phone_number)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False

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

@app.route('/api/setup-phone', methods=['POST'])
def setup_phone():
    """Setup phone number for 2FA"""
    try:
        print("Handling setup-phone request")
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data.get('email') or not data.get('phone_number'):
            return jsonify({'error': 'Email and phone number are required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Validate phone number format
        if not validate_phone_number(data['phone_number']):
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Check if phone number is already in use
        existing_phone = User.query.filter_by(phone_number=data['phone_number']).first()
        if existing_phone and existing_phone.id != user.id:
            return jsonify({'error': 'Phone number is already in use'}), 409

        # Generate verification code
        verification_code = pyotp.random_base32()[:6]
        
        # Send verification code via SMS
        client = get_twilio_client()
        if not client:
            return jsonify({'error': 'SMS service not configured'}), 503

        try:
            # Log the attempt (in development only)
            if app.debug:
                print(f"Attempting to send SMS to {data['phone_number']} with code {verification_code}")
                print(f"Using Twilio number: {TWILIO_PHONE_NUMBER}")

            # In test mode, only allow Twilio test numbers
            if TEST_MODE and not data['phone_number'] in ['+15005550006', '+15005550009']:
                return jsonify({
                    'error': 'In test mode, only Twilio test numbers are allowed. Use +15005550009 for testing.'
                }), 400

            message = client.messages.create(
                body=f'Your InnovateSphere verification code is: {verification_code}',
                from_=get_twilio_number(),
                to=data['phone_number']
            )

            # Log success (in development only)
            if app.debug:
                print(f"SMS sent successfully! Message SID: {message.sid}")

        except Exception as e:
            # Log the error (in development only)
            if app.debug:
                print(f"Twilio error: {str(e)}")
            error_msg = str(e)
            if 'not a valid phone number' in error_msg.lower():
                return jsonify({'error': 'Invalid phone number format'}), 400
            return jsonify({'error': f'Failed to send verification code: {error_msg}'}), 500

        # Store verification code temporarily (in production, use Redis or similar)
        user.phone_verification_code = verification_code
        user.phone_number = data['phone_number']
        db.session.commit()

        return jsonify({
            'message': 'Verification code sent successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-phone', methods=['POST'])
def verify_phone():
    """Verify phone number with code"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['email', 'code']):
            return jsonify({'error': 'Email and verification code are required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.phone_verification_code or user.phone_verification_code != data['code']:
            return jsonify({'error': 'Invalid verification code'}), 400

        user.phone_verified = True
        user.phone_verification_code = None  # Clear the code after successful verification
        db.session.commit()

        return jsonify({
            'message': 'Phone number verified successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/setup-2fa', methods=['POST'])
def setup_2fa():
    """Enable 2FA for a user"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.phone_verified:
            return jsonify({'error': 'Phone number must be verified before enabling 2FA'}), 400

        # Generate new TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Send initial code via SMS
        try:
            code = totp.now()
            client = get_twilio_client()
            if not client:
                return jsonify({'error': 'SMS service not configured'}), 503
                
            # In test mode, only allow Twilio test numbers
            if TEST_MODE and not user.phone_number in ['+15005550006', '+15005550009']:
                return jsonify({
                    'error': 'In test mode, only Twilio test numbers are allowed. Use +15005550009 for testing.'
                }), 400

            message = client.messages.create(
                body=f'Your InnovateSphere 2FA setup code is: {code}',
                from_=get_twilio_number(),
                to=user.phone_number
            )
        except Exception as e:
            return jsonify({'error': 'Failed to send 2FA setup code'}), 500

        user.two_factor_secret = secret
        db.session.commit()

        return jsonify({
            'message': '2FA setup initiated. Please verify with the code sent to your phone.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-2fa', methods=['POST'])
def verify_2fa():
    """Verify 2FA setup with code"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['email', 'code']):
            return jsonify({'error': 'Email and verification code are required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.two_factor_secret:
            return jsonify({'error': '2FA setup not initiated'}), 400

        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(data['code']):
            return jsonify({'error': 'Invalid verification code'}), 400

        user.two_factor_enabled = True
        db.session.commit()

        return jsonify({
            'message': '2FA enabled successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/disable-2fa', methods=['POST'])
def disable_2fa():
    """Disable 2FA for a user"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.two_factor_enabled = False
        user.two_factor_secret = None
        db.session.commit()

        return jsonify({
            'message': '2FA disabled successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)