#!/usr/bin/env python3
"""
InnovateSphere Test Data Setup Script
Creates test users and generates sample ideas for testing purposes
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Disable health checks to avoid module issues
os.environ['SKIP_STARTUP_CHECKS'] = '1'

from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json

# Import without running startup checks
import logging
logging.getLogger('backend.utils.health_checks').setLevel(logging.CRITICAL)

from backend.core.db import db
from backend.core.app import User, create_app
from backend.core.models import ProjectIdea, Domain, IdeaSource

def main():
    """Create test data"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("InnovateSphere Test Data Setup")
        print("=" * 60)

        # Step 1: Create test users
        print("\n[1/3] Creating test users...")

        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            _admin_pw = os.getenv("TEST_ADMIN_PASSWORD", "admin123")
            admin = User(
                email='admin@example.com',
                username='admin',
                password_hash=generate_password_hash(_admin_pw),
                role='admin',
                skill_level='advanced'
            )
            db.session.add(admin)
            print("  ✓ Created admin@example.com")
        else:
            print("  ✓ admin@example.com already exists")

        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            _user_pw = os.getenv("TEST_USER_PASSWORD", "password123")
            user = User(
                email='user@example.com',
                username='testuser',
                password_hash=generate_password_hash(_user_pw),
                skill_level='beginner'
            )
            db.session.add(user)
            print("  ✓ Created user@example.com")
        else:
            print("  ✓ user@example.com already exists")

        db.session.commit()

        # Step 2: Get domains
        print("\n[2/3] Creating sample ideas...")
        domains = Domain.query.all()
        print(f"  Found {len(domains)} domains: {', '.join([d.name for d in domains])}")

        # Create sample ideas (if none exist)
        existing_ideas = ProjectIdea.query.count()
        if existing_ideas == 0:
            sample_ideas = [
                {
                    'title': 'AI-Powered Healthcare Diagnostic Assistant',
                    'domain': 'AI & Machine Learning',
                    'problem_statement': 'Medical professionals spend significant time analyzing patient symptoms and medical records. An AI assistant could help by analyzing patterns in patient data and suggesting potential diagnoses based on current medical research.',
                    'tech_stack': 'Python, TensorFlow, FastAPI, PostgreSQL, Redis'
                },
                {
                    'title': 'Real-Time Cyberattack Detection System',
                    'domain': 'Cybersecurity & Privacy',
                    'problem_statement': 'Current intrusion detection systems are often reactive and miss zero-day attacks. A machine learning-based system could detect anomalous network patterns in real-time and alert security teams before damage occurs.',
                    'tech_stack': 'Go, Rust, Kubernetes, Prometheus, ELK Stack'
                },
                {
                    'title': 'Blockchain Supply Chain Transparency Platform',
                    'domain': 'Blockchain & Web3',
                    'problem_statement': 'Supply chain opacity leads to counterfeiting and ethical sourcing issues. A blockchain-based platform could provide immutable tracking of products from manufacture to consumer, ensuring authenticity and ethical practices.',
                    'tech_stack': 'Solidity, Web3.js, React, Ethereum, IPFS'
                },
                {
                    'title': 'Predictive Maintenance for IoT Devices',
                    'domain': 'IoT & Hardware',
                    'problem_statement': 'Industrial IoT devices fail unexpectedly, causing costly downtime. Predictive analytics could analyze sensor data to forecast failures before they occur, enabling proactive maintenance.',
                    'tech_stack': 'C++, MQTT, InfluxDB, Grafana, TensorFlow Lite'
                },
                {
                    'title': 'Automated Data Quality Improvement Framework',
                    'domain': 'Data Science & Analytics',
                    'problem_statement': 'Data scientists spend 80% of time on data cleaning. An automated framework could detect and fix common data quality issues, validation rules, and outliers automatically.',
                    'tech_stack': 'Python, Pandas, Great Expectations, PySpark, Airflow'
                }
            ]

            for i, idea_data in enumerate(sample_ideas):
                domain = Domain.query.filter_by(name=idea_data['domain']).first()
                if domain:
                    idea = ProjectIdea(
                        title=idea_data['title'],
                        problem_statement=idea_data['problem_statement'],
                        problem_statement_json=json.loads('{"content":"' + idea_data['problem_statement'].replace('"', '\\"') + '"}') if isinstance(idea_data['problem_statement'], str) else {},
                        tech_stack=idea_data['tech_stack'],
                        tech_stack_json={'tools': idea_data['tech_stack'].split(', ')},
                        domain_id=domain.id,
                        ai_pipeline_version='v2',
                        is_ai_generated=True,
                        is_public=True,
                        is_validated=False,
                        created_at=datetime.utcnow() - timedelta(days=len(sample_ideas)-i),
                        quality_score_cached=70 + (i * 3),
                        novelty_score_cached=65 + (i * 4),
                        novelty_context={'explanation': f'Novel approach combining multiple techniques for {idea_data["domain"]}'}
                    )
                    db.session.add(idea)
                    print(f"  ✓ Created: {idea_data['title']}")

            db.session.commit()
            print(f"  ✓ Added 5 sample ideas")
        else:
            print(f"  ℹ {existing_ideas} ideas already exist")

        # Step 3: Summary
        print("\n[3/3] Database Summary:")
        user_count = User.query.count()
        domain_count = Domain.query.count()
        idea_count = ProjectIdea.query.count()

        print(f"  Users: {user_count}")
        print(f"  Domains: {domain_count}")
        print(f"  Ideas: {idea_count}")

        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print("\nTest Credentials:")
        print("  Admin:  admin@example.com / admin123")
        print("  User:   user@example.com / password123")
        print("\nYou can now:")
        print("  1. Test login with these credentials")
        print("  2. Generate more ideas")
        print("  3. Test admin features")
        print("=" * 60)

if __name__ == '__main__':
    main()
