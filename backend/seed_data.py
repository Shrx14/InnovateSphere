"""
Seed Data Module (Segment 0.1)

Provides idempotent seeding of initial domain taxonomy and AI pipeline versions.
Safe to run multiple times without creating duplicates.
"""

from backend.app import db
from backend.models import Domain, DomainCategory, AiPipelineVersion


def seed_initial_data():
    """
    Seeds initial domains, categories, and AI pipeline versions.
    Idempotent - safe to run multiple times.
    """
    try:
        # Seed domains
        domains_data = [
            {'name': 'AI', 'description': 'Artificial Intelligence and Machine Learning'},
            {'name': 'Web Development', 'description': 'Web application development and technologies'},
            {'name': 'Data Science', 'description': 'Data analysis, visualization, and statistical modeling'},
            {'name': 'Cybersecurity', 'description': 'Security, encryption, and threat protection'},
            {'name': 'IoT', 'description': 'Internet of Things and embedded systems'}
        ]

        for domain_data in domains_data:
            existing = Domain.query.filter_by(name=domain_data['name']).first()
            if not existing:
                domain = Domain(
                    name=domain_data['name'],
                    description=domain_data['description'],
                    is_active=True
                )
                db.session.add(domain)
                print(f"Added domain: {domain_data['name']}")

        # Commit domains first to get IDs
        db.session.commit()

        # Seed AI pipeline version
        existing_version = AiPipelineVersion.query.filter_by(version='v2').first()
        if not existing_version:
            ai_version = AiPipelineVersion(
                version='v2',
                description='Initial AI pipeline version for Segment 0.1',
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
    from backend.app import app
    with app.app_context():
        seed_initial_data()
