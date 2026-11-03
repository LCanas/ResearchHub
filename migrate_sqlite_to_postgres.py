"""Copy everything from a SQLite hub.db into the database in DATABASE_URL
(PostgreSQL). Run it once, when moving an existing hub onto Postgres.

With Docker Compose, from the folder with docker-compose.yml:

    docker compose cp hub.db web:/tmp/hub.db
    docker compose exec web python migrate_sqlite_to_postgres.py /tmp/hub.db

The target must not have any members yet. Anything else in it (e.g. the
starter announcements created on first boot) is replaced by the copy.
"""
import argparse
import sys

import sqlalchemy as sa

from hub import create_app, _add_missing_columns
from hub.extensions import db


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sqlite_file", help="path to the old hub.db")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        target = db.engine
        if target.dialect.name == "sqlite":
            sys.exit("DATABASE_URL points at SQLite: set it to the Postgres database.")

        source = sa.create_engine(f"sqlite:///{args.sqlite_file}")
        src_insp = sa.inspect(source)
        if not src_insp.has_table("users"):
            sys.exit(f"{args.sqlite_file} doesn't look like a hub database.")

        tables = db.metadata.sorted_tables          # parents before children
        with target.connect() as conn:
            if conn.execute(sa.text("SELECT count(*) FROM users")).scalar():
                sys.exit("The Postgres database already has members: refusing to "
                         "overwrite it.")

        with target.begin() as conn:
            # Clear whatever first boot created, children first.
            for table in reversed(tables):
                conn.execute(table.delete())

            for table in tables:
                if not src_insp.has_table(table.name):
                    print(f"  {table.name}: not in the old database, skipped")
                    continue
                # Older databases may lack newer columns; copy what exists and
                # let the rest take their defaults.
                src_cols = {c["name"] for c in src_insp.get_columns(table.name)}
                cols = [c for c in table.columns if c.name in src_cols]
                with source.connect() as src:
                    rows = [dict(r._mapping) for r in
                            src.execute(sa.select(*cols))]
                for row in rows:
                    for c in table.columns:
                        if c.name not in row and c.default is not None and c.default.is_scalar:
                            row[c.name] = c.default.arg
                if rows:
                    conn.execute(table.insert(), rows)
                print(f"  {table.name}: {len(rows)} row(s)")

            # Postgres hands out ids from sequences; move them past the copied ids.
            for table in tables:
                if "id" in table.columns:
                    conn.execute(sa.text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {table.name}), 1), "
                        f"(SELECT MAX(id) FROM {table.name}) IS NOT NULL)"))
        _add_missing_columns()
    print("Done. Everything from the SQLite file is now in Postgres.")


if __name__ == "__main__":
    main()
