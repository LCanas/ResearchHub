"""Database models for the Collaboration Hub.

The schema mirrors the requirements:
  * User        -> researcher profiles (expertise, seniority, contract, links...)
  * Project     -> collaborative projects with a lifecycle stage + roadmap
  * Milestone   -> roadmap / Gantt rows attached to a project
  * Collaboration-> user <-> project link storing hours/days dedicated + role
  * JoinRequest -> a user's request to join a project (pending/accepted/rejected)
"""
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile (requirement 5)
    bio = db.Column(db.Text, default="")
    expertise = db.Column(db.String(255), default="")          # short headline
    keywords = db.Column(db.String(255), default="")           # comma separated skills
    workstreams = db.Column(db.String(400), default="")        # pipe-separated themes
    seniority = db.Column(db.String(60), default="")
    contract_type = db.Column(db.String(80), default="")
    department = db.Column(db.String(120), default="")
    pi = db.Column(db.String(120), default="")                 # research supervisor / PI
    line_manager = db.Column(db.String(120), default="")

    # Links (requirement 5)
    linkedin_url = db.Column(db.String(255), default="")
    teams_url = db.Column(db.String(255), default="")
    kcl_url = db.Column(db.String(255), default="")

    # Availability / directory metadata (requirement 8)
    work_status = db.Column(db.String(40), default="Active")   # Active / Keen / ...
    hours_available = db.Column(db.Integer, default=0)         # hours per week
    db_role = db.Column(db.String(40), default="Collaborator")  # Collaborator / PI
    phone = db.Column(db.String(60), default="")

    photo = db.Column(db.String(255), default="")              # uploaded filename
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    collaborations = db.relationship(
        "Collaboration", back_populates="user", cascade="all, delete-orphan"
    )
    join_requests = db.relationship(
        "JoinRequest", back_populates="user", cascade="all, delete-orphan"
    )
    led_projects = db.relationship(
        "Project", foreign_keys="Project.pi_id", back_populates="pi_user"
    )
    proposed_projects = db.relationship(
        "Project", foreign_keys="Project.proposer_id", back_populates="proposer"
    )

    # -- helpers -----------------------------------------------------------
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def keyword_list(self):
        return [k.strip() for k in (self.keywords or "").split(",") if k.strip()]

    @property
    def workstream_list(self):
        return [w.strip() for w in (self.workstreams or "").split("|") if w.strip()]

    @property
    def initials(self):
        parts = self.full_name.split()
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def total_hours(self):
        return sum(c.hours_dedicated or 0 for c in self.collaborations)

    @property
    def active_project_count(self):
        return sum(
            1 for c in self.collaborations
            if c.project and c.project.status not in ("Completed",)
        )

    def __repr__(self):
        return f"<User {self.full_name}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(300), default="")            # one-line pitch
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="Open", index=True)
    project_type = db.Column(db.String(60), default="")        # Hackathon/PoC/... (req 4)
    workstream = db.Column(db.String(80), default="")          # research theme

    expected_outcomes = db.Column(db.Text, default="")
    actual_outcomes = db.Column(db.Text, default="")           # shown when Completed
    github_url = db.Column(db.String(255), default="")
    department = db.Column(db.String(120), default="")
    keywords = db.Column(db.String(255), default="")

    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date)

    pi_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pi_user = db.relationship(
        "User", foreign_keys=[pi_id], back_populates="led_projects"
    )
    proposer = db.relationship(
        "User", foreign_keys=[proposer_id], back_populates="proposed_projects"
    )
    milestones = db.relationship(
        "Milestone", back_populates="project",
        cascade="all, delete-orphan", order_by="Milestone.start_date",
    )
    collaborations = db.relationship(
        "Collaboration", back_populates="project", cascade="all, delete-orphan"
    )
    join_requests = db.relationship(
        "JoinRequest", back_populates="project", cascade="all, delete-orphan"
    )

    @property
    def keyword_list(self):
        return [k.strip() for k in (self.keywords or "").split(",") if k.strip()]

    @property
    def is_completed(self):
        return self.status == "Completed"

    @property
    def is_open(self):
        return self.status == "Open"

    @property
    def collaborators(self):
        return [c.user for c in self.collaborations]

    @property
    def total_hours(self):
        return sum(c.hours_dedicated or 0 for c in self.collaborations)

    def __repr__(self):
        return f"<Project {self.title}>"


class Milestone(db.Model):
    """A roadmap row rendered into the Gantt chart on the project page."""
    __tablename__ = "milestones"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(40), default="Planned")

    project = db.relationship("Project", back_populates="milestones")

    @property
    def duration_days(self):
        return max((self.end_date - self.start_date).days, 1)

    def __repr__(self):
        return f"<Milestone {self.name}>"


class Collaboration(db.Model):
    """Link table: a user's involvement in a project (requirement 4)."""
    __tablename__ = "collaborations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    role = db.Column(db.String(80), default="Collaborator")
    hours_dedicated = db.Column(db.Integer, default=0)
    days_dedicated = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="collaborations")
    project = db.relationship("Project", back_populates="collaborations")

    __table_args__ = (
        db.UniqueConstraint("user_id", "project_id", name="uq_user_project"),
    )


class NewsPost(db.Model):
    """A hub announcement / news item."""
    __tablename__ = "news_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, default="")
    workstream = db.Column(db.String(80), default="")
    pinned = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User")

    def __repr__(self):
        return f"<NewsPost {self.title}>"


class Event(db.Model):
    """A seminar, training session, data club or workshop."""
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    event_type = db.Column(db.String(60), default="Seminar")
    start_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_at = db.Column(db.DateTime)
    location = db.Column(db.String(200), default="")
    is_online = db.Column(db.Boolean, default=False)
    url = db.Column(db.String(255), default="")          # join / sign-up link
    workstream = db.Column(db.String(80), default="")
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    host = db.relationship("User")
    attendances = db.relationship(
        "EventAttendance", back_populates="event", cascade="all, delete-orphan"
    )

    @property
    def is_past(self):
        return (self.end_at or self.start_at) < datetime.utcnow()

    @property
    def attendee_count(self):
        return len(self.attendances)

    @property
    def attendees(self):
        return [a.user for a in self.attendances]

    def __repr__(self):
        return f"<Event {self.title}>"


class EventAttendance(db.Model):
    """A user's sign-up for an event."""
    __tablename__ = "event_attendances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    event = db.relationship("Event", back_populates="attendances")

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )


class JoinRequest(db.Model):
    """A user's request to join a project (requirement 2)."""
    __tablename__ = "join_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="Pending")       # Pending/Accepted/Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="join_requests")
    project = db.relationship("Project", back_populates="join_requests")
