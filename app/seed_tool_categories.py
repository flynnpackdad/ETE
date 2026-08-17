"""
Seed script: Create default tool categories for budget projection.

Run this once to populate initial categories:
    python -m app.seed_tool_categories
"""
from app import create_app, db
from app.models import ToolCategory


def seed():
    app = create_app()
    with app.app_context():
        categories = [
            {"name": "Hardware", "description": "Physical equipment (servers, switches, laptops)", "sort_order": 1},
            {"name": "Software", "description": "Licensing, subscriptions, SaaS", "sort_order": 2},
            {"name": "Network Circuit", "description": "WAN, MPLS, internet circuits, dark fiber", "sort_order": 3},
            {"name": "Cloud", "description": "Cloud infrastructure (AWS, Azure, GCP)", "sort_order": 4},
            {"name": "Professional Services", "description": "Consulting, implementation, migration", "sort_order": 5},
            {"name": "Support & Maintenance", "description": "Annual support contracts (ASC)", "sort_order": 6},
        ]

        for cat in categories:
            existing = ToolCategory.query.filter_by(name=cat["name"]).first()
            if not existing:
                db.session.add(ToolCategory(
                    name=cat["name"],
                    description=cat["description"],
                    sort_order=cat["sort_order"],
                ))
                print(f"Created category: {cat['name']}")
            else:
                print(f"Skipped (exists): {cat['name']}")

        db.session.commit()
        print("\n✅ Seed complete.")


if __name__ == "__main__":
    seed()