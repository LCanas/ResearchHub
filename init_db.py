"""Initialise the database on boot.

Creates the tables and, **only if the database is empty**, adds the starter
launch & hackathon announcements (no fake people — researchers create their own
profiles). Safe to run on every startup — it never wipes existing data.

This is used in the production startup command:

    python init_db.py && gunicorn --bind=0.0.0.0 --timeout 600 --workers 1 wsgi:app

Set SEED_DEMO=1 to fill an empty database with the old Big Bang Theory demo
data instead (handy for demos; never use it on the live hub).
"""
import os

from hub import create_app
from hub.extensions import db


def move_departments_to_schools(models):
    """Earlier versions stored the school in the "department" field. Move those
    values into "school" and keep anything else as the department."""
    from hub.config import SCHOOLS, LEGACY_SCHOOL_NAMES
    moved = 0
    for model in models:
        for row in model.query.filter((model.school == "") | (model.school.is_(None))):
            name = LEGACY_SCHOOL_NAMES.get(row.department, row.department)
            if name in SCHOOLS:
                row.school, row.department = name, ""
                moved += 1
    db.session.commit()
    return moved


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        from hub.models import User, Project
        already_populated = User.query.count() > 0
        # Only when the school columns have just been added (an upgrade).
        added = app.config.get("COLUMNS_ADDED", [])
        upgrade = [m for m, t in ((User, "users"), (Project, "projects"))
                   if (t, "school") in added]
        if upgrade:
            print(f"Moved {move_departments_to_schools(upgrade)} department value(s) "
                  f"into the new school field.")

    if already_populated:
        print("Database already has users — skipping demo seed.")
    elif os.environ.get("SEED_DEMO", "0") == "1":
        print("Empty database — SEED_DEMO=1, seeding demo data…")
        from seed import run
        run()
        with app.app_context():
            move_departments_to_schools([User, Project])

    with app.app_context():
        from hub.event_sync import sync_all
        for name, result in sync_all().items():
            print(f"Events from {name}: {result}")
        from launch_content import seed_launch_content, backfill_links
        added = seed_launch_content()
        if added:
            print(f"Added {added} launch announcements.")
        linked = backfill_links()
        if linked:
            print(f"Added page buttons to {linked} announcement(s).")


if __name__ == "__main__":
    main()
