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


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        from hub.models import User
        already_populated = User.query.count() > 0

    if already_populated:
        print("Database already has users — skipping demo seed.")
    elif os.environ.get("SEED_DEMO", "0") == "1":
        print("Empty database — SEED_DEMO=1, seeding demo data…")
        from seed import run
        run()

    with app.app_context():
        from launch_content import seed_launch_content
        added = seed_launch_content()
        if added:
            print(f"Added {added} launch announcements.")


if __name__ == "__main__":
    main()
