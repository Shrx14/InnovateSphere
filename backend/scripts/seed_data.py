"""
Seed Data Module (Segment 0.1)

Provides idempotent seeding of initial domain taxonomy and AI pipeline versions.
Safe to run multiple times without creating duplicates.
"""

from backend.core.db import db
from backend.core.models import Domain, DomainCategory, AiPipelineVersion


def seed_initial_data():
    """
    Seeds initial domains, categories, and AI pipeline versions.
    Idempotent - safe to run multiple times.
    """
    try:
        # Seed domains with subcategories
        domains_data = [
            {
                'name': 'AI & Machine Learning',
                'categories': ['Natural Language Processing', 'Computer Vision', 'Reinforcement Learning', 'Generative AI', 'AI Tools']
            },
            {
                'name': 'Web & Mobile Development',
                'categories': ['Frontend', 'Backend', 'Full Stack', 'Progressive Web Apps', 'Mobile Apps']
            },
            {
                'name': 'Data Science & Analytics',
                'categories': ['Business Intelligence', 'Data Engineering', 'Predictive Analytics', 'Data Visualization', 'Statistical Analysis']
            },
            {
                'name': 'Cybersecurity & Privacy',
                'categories': ['Application Security', 'Network Security', 'Privacy Engineering', 'Threat Detection', 'Compliance']
            },
            {
                'name': 'Cloud & DevOps',
                'categories': ['Cloud Infrastructure', 'Containerization', 'CI/CD Pipelines', 'Infrastructure as Code', 'Monitoring']
            },
            {
                'name': 'Blockchain & Web3',
                'categories': ['Smart Contracts', 'DeFi', 'NFTs', 'Cryptocurrency', 'Consensus Mechanisms']
            },
            {
                'name': 'IoT & Hardware',
                'categories': ['Embedded Systems', 'Sensor Networks', 'Smart Devices', 'Robotics', 'Microcontrollers']
            },
            {
                'name': 'Healthcare & Biotech',
                'categories': ['Medical Devices', 'Telemedicine', 'Bioinformatics', 'Drug Discovery', 'Health Tech']
            },
            {
                'name': 'Education & E-Learning',
                'categories': ['Online Learning Platforms', 'Adaptive Learning', 'Skill Assessment', 'Collaborative Tools', 'Gamification']
            },
            {
                'name': 'Business & Productivity Tools',
                'categories': ['Project Management', 'CRM Systems', 'Automation', 'Analytics Platforms', 'Collaboration Tools']
            }
        ]

        for domain_data in domains_data:
            existing = Domain.query.filter_by(name=domain_data['name']).first()
            if not existing:
                domain = Domain(name=domain_data['name'])
                db.session.add(domain)
                print(f"Added domain: {domain_data['name']}")
                
                # Add categories for this domain after the domain is added
                for category_name in domain_data['categories']:
                    category = DomainCategory(domain=domain, name=category_name)
                    db.session.add(category)
                    print(f"  └─ Added category: {category_name}")

        # Commit domains first to get IDs
        db.session.commit()

        # Seed AI pipeline version
        existing_version = AiPipelineVersion.query.filter_by(version='v2').first()
        if not existing_version:
            ai_version = AiPipelineVersion(
                version='v2',
                is_active=True
            )
            db.session.add(ai_version)
            print("Added AI pipeline version: v2")

        # Commit all changes
        db.session.commit()
        print("Seed data completed successfully")

    except Exception as e:
        db.session.rollback()
        print(f"Error during seeding: {e}")
        raise


if __name__ == '__main__':
    # Allow running as standalone script
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from backend.core.app import create_app
    app = create_app()
    with app.app_context():
        seed_initial_data()
