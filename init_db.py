"""Initialise the database on boot.

Creates the tables and, **only if the database is empty**, seeds the demo data.
Safe to run on every startup — it never wipes existing data.

This is used in the production startup command so a freshly-deployed app comes
up already populated with the demo content and login:

    python init_db.py && gunicorn --bind=0.0.0.0 --timeout 600 --workers 1 wsgi:app
"""
from hub import create_app
from hub.extensions import db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        from hub.models import User
        already_populated = User.query.count() > 0

    if already_populated:
        print("Database already populated — skipping seed.")
    else:
        print("Empty database — seeding demo data…")
        from seed import run
        run()


if __name__ == "__main__":
    main()
