"""Application factory for the Collaboration Hub for AI Deployment in
Healthcare Research (King's College London)."""
import os
import re

import sqlalchemy as sa
from markupsafe import Markup, escape
from flask import Flask

from .config import (
    Config, STAGE_NAMES, STAGE_DESCRIPTIONS, STAGE_CSS, CONTRACT_TYPES,
    SENIORITY_LEVELS, WORK_STATUSES, DB_ROLES, MILESTONE_STATUSES, SCHOOLS,
    PROJECT_TYPES, PROJECT_TYPE_NAMES, PROJECT_TYPE_CSS, PROJECT_TYPE_BAND,
    SCHOOL_KCL_URLS, PANEL_MEMBERS, REVIEW_CRITERIA,
    WORKSTREAMS, WORKSTREAM_NAMES, WORKSTREAM_SLUG, WORKSTREAM_CSS,
    EVENT_TYPES, EVENT_TYPE_ICONS, LAUNCH, HACKATHON, CODE_OF_CONDUCT_VERSION,
    REVIEW_STATUSES, REVIEW_STATUS_CSS, CONTACT_EMAIL, SOCIAL_LINKS,
    SPEAKER_SESSION_TYPES, SPEAKER_PROPOSAL_STATUSES, ATTENDEE_TYPES, NEWS_LINK_PAGES,
)
from .extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        return None if user is None or user.is_suspended else user

    # Blueprints
    from .auth import auth_bp
    from .main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Make the controlled vocabularies + helpers available in every template.
    # Registered as Jinja *globals* (not a context processor) so that macros
    # imported with `{% from ... import ... %}` can also see them.
    app.jinja_env.globals.update(
        STAGE_NAMES=STAGE_NAMES,
        STAGE_DESCRIPTIONS=STAGE_DESCRIPTIONS,
        STAGE_CSS=STAGE_CSS,
        CONTRACT_TYPES=CONTRACT_TYPES,
        SENIORITY_LEVELS=SENIORITY_LEVELS,
        WORK_STATUSES=WORK_STATUSES,
        DB_ROLES=DB_ROLES,
        MILESTONE_STATUSES=MILESTONE_STATUSES,
        SCHOOLS=SCHOOLS,
        PROJECT_TYPES=PROJECT_TYPES,
        PROJECT_TYPE_NAMES=PROJECT_TYPE_NAMES,
        PROJECT_TYPE_CSS=PROJECT_TYPE_CSS,
        PROJECT_TYPE_BAND=PROJECT_TYPE_BAND,
        SCHOOL_KCL_URLS=SCHOOL_KCL_URLS,
        PANEL_MEMBERS=PANEL_MEMBERS,
        REVIEW_CRITERIA=REVIEW_CRITERIA,
        WORKSTREAMS=WORKSTREAMS,
        WORKSTREAM_NAMES=WORKSTREAM_NAMES,
        WORKSTREAM_SLUG=WORKSTREAM_SLUG,
        WORKSTREAM_CSS=WORKSTREAM_CSS,
        EVENT_TYPES=EVENT_TYPES,
        EVENT_TYPE_ICONS=EVENT_TYPE_ICONS,
        LAUNCH=LAUNCH,
        HACKATHON=HACKATHON,
        CODE_OF_CONDUCT_VERSION=CODE_OF_CONDUCT_VERSION,
        REVIEW_STATUSES=REVIEW_STATUSES,
        REVIEW_STATUS_CSS=REVIEW_STATUS_CSS,
        CONTACT_EMAIL=CONTACT_EMAIL,
        SOCIAL_LINKS=SOCIAL_LINKS,
        SPEAKER_SESSION_TYPES=SPEAKER_SESSION_TYPES,
        SPEAKER_PROPOSAL_STATUSES=SPEAKER_PROPOSAL_STATUSES,
        ATTENDEE_TYPES=ATTENDEE_TYPES,
        NEWS_LINK_PAGES=NEWS_LINK_PAGES,
        APP_NAME="Collaboration Hub",
        APP_SUBTITLE="AI Deployment in Healthcare Research",
    )

    # Turn web addresses in plain text (news posts) into links, safely.
    app.jinja_env.filters["linkify"] = _linkify

    with app.app_context():
        db.create_all()
        # Recorded so init_db.py can run one-off data moves for new columns.
        app.config["COLUMNS_ADDED"] = _add_missing_columns()

    return app


_URL_RE = re.compile(r"(https?://[^\s<]+[^\s<.,;:!?)\]'\"])")


def _linkify(text):
    escaped = str(escape(text or ""))
    return Markup(_URL_RE.sub(
        r'<a href="\1" target="_blank" rel="noopener">\1</a>', escaped))


def _add_missing_columns():
    """db.create_all() never alters existing tables, so add any model columns an
    older database is missing. Additive changes only: no renames or drops."""
    engine = db.engine
    insp = sa.inspect(engine)
    added = []
    with engine.begin() as conn:
        for table in db.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing:
                    continue
                ddl = (f"ALTER TABLE {table.name} ADD COLUMN {col.name} "
                       f"{col.type.compile(dialect=engine.dialect)}")
                if col.default is not None and col.default.is_scalar:
                    literal = sa.literal(col.default.arg, type_=col.type).compile(
                        dialect=engine.dialect,
                        compile_kwargs={"literal_binds": True})
                    ddl += f" DEFAULT {literal}"
                conn.execute(sa.text(ddl))
                added.append((table.name, col.name))
    return added
