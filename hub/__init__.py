"""Application factory for the Collaboration Hub for AI Deployment in
Healthcare Research (King's College London)."""
import os

from flask import Flask

from .config import (
    Config, STAGE_NAMES, STAGE_DESCRIPTIONS, STAGE_CSS, CONTRACT_TYPES,
    SENIORITY_LEVELS, WORK_STATUSES, DB_ROLES, MILESTONE_STATUSES, DEPARTMENTS,
    PROJECT_TYPES, PROJECT_TYPE_NAMES, PROJECT_TYPE_CSS, PROJECT_TYPE_BAND,
    DEPARTMENT_KCL_URLS, PANEL_MEMBERS, REVIEW_CRITERIA,
    WORKSTREAMS, WORKSTREAM_NAMES, WORKSTREAM_SLUG, WORKSTREAM_CSS,
    EVENT_TYPES, EVENT_TYPE_ICONS,
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
        return db.session.get(User, int(user_id))

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
        DEPARTMENTS=DEPARTMENTS,
        PROJECT_TYPES=PROJECT_TYPES,
        PROJECT_TYPE_NAMES=PROJECT_TYPE_NAMES,
        PROJECT_TYPE_CSS=PROJECT_TYPE_CSS,
        PROJECT_TYPE_BAND=PROJECT_TYPE_BAND,
        DEPARTMENT_KCL_URLS=DEPARTMENT_KCL_URLS,
        PANEL_MEMBERS=PANEL_MEMBERS,
        REVIEW_CRITERIA=REVIEW_CRITERIA,
        WORKSTREAMS=WORKSTREAMS,
        WORKSTREAM_NAMES=WORKSTREAM_NAMES,
        WORKSTREAM_SLUG=WORKSTREAM_SLUG,
        WORKSTREAM_CSS=WORKSTREAM_CSS,
        EVENT_TYPES=EVENT_TYPES,
        EVENT_TYPE_ICONS=EVENT_TYPE_ICONS,
        APP_NAME="Collaboration Hub",
        APP_SUBTITLE="AI Deployment in Healthcare Research",
    )

    with app.app_context():
        db.create_all()

    return app
