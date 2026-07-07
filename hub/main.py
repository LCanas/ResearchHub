"""Main application routes: projects, profiles, directory, join flow."""
import os
import uuid
from datetime import datetime, date

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from .extensions import db
from .models import (
    User, Project, Milestone, Collaboration, JoinRequest,
    NewsPost, Event, EventAttendance,
)
from .config import (
    STAGE_NAMES, PROJECT_TYPE_NAMES, WORKSTREAM_NAMES, WORKSTREAM_BY_SLUG,
    EVENT_TYPES,
)

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_date(value, default=None):
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return default


def _parse_dt(value, default=None):
    """Parse an HTML datetime-local value (YYYY-MM-DDTHH:MM)."""
    if not value:
        return default
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return default


def can_manage(project):
    """A project can be managed by its proposer, its PI, or an admin."""
    if not current_user.is_authenticated:
        return False
    return (
        current_user.is_admin
        or project.proposer_id == current_user.id
        or project.pi_id == current_user.id
    )


def build_gantt(project):
    """Turn a project's milestones into positioned bars for the CSS Gantt.

    Returns (rows, month_labels). Each row carries offset/width percentages
    relative to the full project window so the template just drops them in.
    """
    milestones = project.milestones
    if not milestones:
        return [], []

    starts = [m.start_date for m in milestones]
    ends = [m.end_date for m in milestones]
    if project.start_date:
        starts.append(project.start_date)
    if project.end_date:
        ends.append(project.end_date)

    window_start = min(starts)
    window_end = max(ends)
    total_days = max((window_end - window_start).days, 1)

    rows = []
    for m in milestones:
        offset = (m.start_date - window_start).days
        width = max((m.end_date - m.start_date).days, 1)
        rows.append({
            "milestone": m,
            "offset_pct": round(offset / total_days * 100, 2),
            "width_pct": round(width / total_days * 100, 2),
        })

    # Build month tick labels across the window.
    labels = []
    cur = date(window_start.year, window_start.month, 1)
    while cur <= window_end:
        offset = max((cur - window_start).days, 0)
        labels.append({
            "text": cur.strftime("%b %y"),
            "offset_pct": round(offset / total_days * 100, 2),
        })
        # advance one month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)

    return rows, labels


def save_photo(file_storage):
    """Persist an uploaded profile photo, returning the stored filename."""
    if not file_storage or file_storage.filename == "":
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        flash("Unsupported image type. Use PNG, JPG, GIF or WEBP.", "warning")
        return None
    fname = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], fname))
    return fname


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------
@main_bp.route("/")
@login_required
def index():
    stats = {
        "projects": Project.query.count(),
        "open": Project.query.filter_by(status="Open").count(),
        "ongoing": Project.query.filter_by(status="Ongoing").count(),
        "completed": Project.query.filter_by(status="Completed").count(),
        "researchers": User.query.count(),
    }
    latest_news = NewsPost.query.order_by(
        NewsPost.pinned.desc(), NewsPost.created_at.desc()
    ).limit(4).all()
    upcoming_events = Event.query.filter(Event.start_at >= datetime.utcnow()) \
        .order_by(Event.start_at).limit(4).all()
    # A few open projects to feature as calls for collaborators.
    featured = Project.query.filter_by(status="Open") \
        .order_by(Project.created_at.desc()).limit(3).all()
    if len(featured) < 3:
        extra = Project.query.filter(Project.status != "Open") \
            .order_by(Project.created_at.desc()).limit(3 - len(featured)).all()
        featured = featured + extra

    return render_template(
        "home.html", stats=stats, latest_news=latest_news,
        upcoming_events=upcoming_events, featured=featured,
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@main_bp.route("/projects")
@login_required
def projects():
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()
    dept = request.args.get("department", "").strip()
    ptype = request.args.get("type", "").strip()
    ws_slug = request.args.get("workstream", "").strip()
    ws_name = WORKSTREAM_BY_SLUG.get(ws_slug, {}).get("name", "")

    query = Project.query
    if status and status in STAGE_NAMES:
        query = query.filter(Project.status == status)
    if ptype and ptype in PROJECT_TYPE_NAMES:
        query = query.filter(Project.project_type == ptype)
    if ws_name:
        query = query.filter(Project.workstream == ws_name)
    if dept:
        query = query.filter(Project.department == dept)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Project.title.ilike(like),
            Project.summary.ilike(like),
            Project.keywords.ilike(like),
            Project.description.ilike(like),
        ))

    project_list = query.order_by(Project.created_at.desc()).all()

    stage_counts = {s: Project.query.filter_by(status=s).count()
                    for s in STAGE_NAMES}
    stats = {
        "projects": Project.query.count(),
        "open": Project.query.filter_by(status="Open").count(),
        "ongoing": Project.query.filter_by(status="Ongoing").count(),
        "researchers": User.query.count(),
    }

    return render_template(
        "projects.html", projects=project_list, stage_counts=stage_counts,
        stats=stats, active_status=status, q=q, active_dept=dept,
        active_type=ptype, active_workstream=ws_slug,
    )


@main_bp.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = db.session.get(Project, project_id) or abort(404)
    gantt_rows, gantt_labels = build_gantt(project)

    my_request = JoinRequest.query.filter_by(
        user_id=current_user.id, project_id=project.id
    ).order_by(JoinRequest.created_at.desc()).first()
    is_collaborator = Collaboration.query.filter_by(
        user_id=current_user.id, project_id=project.id
    ).first() is not None

    pending_requests = []
    if can_manage(project):
        pending_requests = [r for r in project.join_requests
                            if r.status == "Pending"]

    return render_template(
        "project_detail.html", project=project, gantt_rows=gantt_rows,
        gantt_labels=gantt_labels, my_request=my_request,
        is_collaborator=is_collaborator, can_manage=can_manage(project),
        pending_requests=pending_requests,
    )


@main_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        project = Project(
            title=request.form.get("title", "").strip(),
            summary=request.form.get("summary", "").strip(),
            description=request.form.get("description", "").strip(),
            status=request.form.get("status", "Open"),
            project_type=request.form.get("project_type", "").strip(),
            workstream=request.form.get("workstream", "").strip(),
            expected_outcomes=request.form.get("expected_outcomes", "").strip(),
            actual_outcomes=request.form.get("actual_outcomes", "").strip(),
            github_url=request.form.get("github_url", "").strip(),
            department=request.form.get("department", "").strip(),
            keywords=request.form.get("keywords", "").strip(),
            start_date=_parse_date(request.form.get("start_date"), date.today()),
            end_date=_parse_date(request.form.get("end_date")),
            proposer_id=current_user.id,
        )
        pi_id = request.form.get("pi_id")
        if pi_id:
            project.pi_id = int(pi_id)

        if not project.title:
            flash("A project needs a title.", "danger")
            return render_template("project_form.html", project=project,
                                   users=User.query.order_by(User.full_name).all())

        db.session.add(project)
        db.session.commit()
        flash("Project created.", "success")
        return redirect(url_for("main.project_detail", project_id=project.id))

    return render_template(
        "project_form.html", project=None,
        users=User.query.order_by(User.full_name).all(),
    )


@main_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id):
    project = db.session.get(Project, project_id) or abort(404)
    if not can_manage(project):
        abort(403)

    if request.method == "POST":
        project.title = request.form.get("title", "").strip()
        project.summary = request.form.get("summary", "").strip()
        project.description = request.form.get("description", "").strip()
        project.status = request.form.get("status", project.status)
        project.project_type = request.form.get("project_type", "").strip()
        project.workstream = request.form.get("workstream", "").strip()
        project.expected_outcomes = request.form.get("expected_outcomes", "").strip()
        project.actual_outcomes = request.form.get("actual_outcomes", "").strip()
        project.github_url = request.form.get("github_url", "").strip()
        project.department = request.form.get("department", "").strip()
        project.keywords = request.form.get("keywords", "").strip()
        project.start_date = _parse_date(request.form.get("start_date"),
                                         project.start_date)
        project.end_date = _parse_date(request.form.get("end_date"),
                                       project.end_date)
        pi_id = request.form.get("pi_id")
        project.pi_id = int(pi_id) if pi_id else None
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("main.project_detail", project_id=project.id))

    return render_template(
        "project_form.html", project=project,
        users=User.query.order_by(User.full_name).all(),
    )


@main_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def project_delete(project_id):
    project = db.session.get(Project, project_id) or abort(404)
    if not can_manage(project):
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("main.index"))


# --- Milestones (roadmap / Gantt) ------------------------------------------
@main_bp.route("/projects/<int:project_id>/milestones/add", methods=["POST"])
@login_required
def milestone_add(project_id):
    project = db.session.get(Project, project_id) or abort(404)
    if not can_manage(project):
        abort(403)
    name = request.form.get("name", "").strip()
    if name:
        m = Milestone(
            project_id=project.id, name=name,
            start_date=_parse_date(request.form.get("start_date"), date.today()),
            end_date=_parse_date(request.form.get("end_date"), date.today()),
            status=request.form.get("status", "Planned"),
        )
        db.session.add(m)
        db.session.commit()
        flash("Milestone added to the roadmap.", "success")
    return redirect(url_for("main.project_detail", project_id=project.id))


@main_bp.route("/milestones/<int:milestone_id>/delete", methods=["POST"])
@login_required
def milestone_delete(milestone_id):
    m = db.session.get(Milestone, milestone_id) or abort(404)
    project_id = m.project_id
    if not can_manage(m.project):
        abort(403)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("main.project_detail", project_id=project_id))


# --- Join requests ----------------------------------------------------------
@main_bp.route("/projects/<int:project_id>/join", methods=["POST"])
@login_required
def project_join(project_id):
    project = db.session.get(Project, project_id) or abort(404)

    already = Collaboration.query.filter_by(
        user_id=current_user.id, project_id=project.id).first()
    if already:
        flash("You are already a collaborator on this project.", "info")
        return redirect(url_for("main.project_detail", project_id=project.id))

    existing = JoinRequest.query.filter_by(
        user_id=current_user.id, project_id=project.id, status="Pending").first()
    if existing:
        flash("You already have a pending request for this project.", "info")
        return redirect(url_for("main.project_detail", project_id=project.id))

    req = JoinRequest(
        user_id=current_user.id, project_id=project.id,
        message=request.form.get("message", "").strip(),
    )
    db.session.add(req)
    db.session.commit()
    flash("Your request to join has been sent.", "success")
    return redirect(url_for("main.project_detail", project_id=project.id))


@main_bp.route("/requests/<int:request_id>/<action>", methods=["POST"])
@login_required
def request_action(request_id, action):
    req = db.session.get(JoinRequest, request_id) or abort(404)
    if not can_manage(req.project):
        abort(403)

    if action == "accept":
        req.status = "Accepted"
        # Create the collaboration if it doesn't exist yet.
        exists = Collaboration.query.filter_by(
            user_id=req.user_id, project_id=req.project_id).first()
        if not exists:
            db.session.add(Collaboration(
                user_id=req.user_id, project_id=req.project_id,
                role="Collaborator",
            ))
        flash(f"{req.user.full_name} added to the project.", "success")
    elif action == "reject":
        req.status = "Rejected"
        flash("Request declined.", "info")
    else:
        abort(400)
    db.session.commit()
    return redirect(request.referrer
                    or url_for("main.project_detail", project_id=req.project_id))


@main_bp.route("/requests")
@login_required
def my_requests():
    outgoing = JoinRequest.query.filter_by(user_id=current_user.id) \
        .order_by(JoinRequest.created_at.desc()).all()
    # Incoming: requests on projects I manage.
    managed_ids = [p.id for p in Project.query.all() if can_manage(p)]
    incoming = JoinRequest.query.filter(
        JoinRequest.project_id.in_(managed_ids or [-1]),
        JoinRequest.status == "Pending",
    ).order_by(JoinRequest.created_at.desc()).all()
    return render_template("requests.html", outgoing=outgoing, incoming=incoming)


# --- Collaborator management (role) -----------------------------------------
@main_bp.route("/collaborations/<int:collab_id>/update", methods=["POST"])
@login_required
def collaboration_update(collab_id):
    collab = db.session.get(Collaboration, collab_id) or abort(404)
    if not can_manage(collab.project):
        abort(403)
    collab.role = request.form.get("role", collab.role).strip() or collab.role
    db.session.commit()
    flash("Collaborator role updated.", "success")
    return redirect(url_for("main.project_detail", project_id=collab.project_id))


@main_bp.route("/collaborations/<int:collab_id>/remove", methods=["POST"])
@login_required
def collaboration_remove(collab_id):
    collab = db.session.get(Collaboration, collab_id) or abort(404)
    if not can_manage(collab.project):
        abort(403)
    project_id = collab.project_id
    db.session.delete(collab)
    db.session.commit()
    flash("Collaborator removed.", "info")
    return redirect(url_for("main.project_detail", project_id=project_id))


# ---------------------------------------------------------------------------
# People directory & profiles
# ---------------------------------------------------------------------------
@main_bp.route("/directory")
@login_required
def directory():
    q = request.args.get("q", "").strip()
    dept = request.args.get("department", "").strip()
    work_status = request.args.get("work_status", "").strip()
    db_role = request.args.get("db_role", "").strip()
    min_hours = request.args.get("min_hours", "").strip()
    ws_slug = request.args.get("workstream", "").strip()
    ws_name = WORKSTREAM_BY_SLUG.get(ws_slug, {}).get("name", "")

    query = User.query
    if dept:
        query = query.filter(User.department == dept)
    if work_status:
        query = query.filter(User.work_status == work_status)
    if db_role:
        query = query.filter(User.db_role == db_role)
    if ws_name:
        query = query.filter(User.workstreams.ilike(f"%{ws_name}%"))
    if min_hours.isdigit():
        query = query.filter(User.hours_available >= int(min_hours))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            User.full_name.ilike(like),
            User.keywords.ilike(like),
            User.expertise.ilike(like),
            User.bio.ilike(like),
        ))

    people = query.order_by(User.full_name).all()
    return render_template(
        "directory.html", people=people, q=q, active_dept=dept,
        active_work_status=work_status, active_db_role=db_role,
        min_hours=min_hours, active_workstream=ws_slug,
    )


@main_bp.route("/users/<int:user_id>")
@login_required
def profile(user_id):
    user = db.session.get(User, user_id) or abort(404)
    return render_template("profile.html", user=user)


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = current_user
    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.bio = request.form.get("bio", "").strip()
        user.expertise = request.form.get("expertise", "").strip()
        user.keywords = request.form.get("keywords", "").strip()
        # Workstreams come in as multiple checkbox values; store pipe-separated.
        chosen_ws = [w for w in request.form.getlist("workstreams")
                     if w in WORKSTREAM_NAMES]
        user.workstreams = "|".join(chosen_ws)
        user.seniority = request.form.get("seniority", "").strip()
        user.contract_type = request.form.get("contract_type", "").strip()
        user.department = request.form.get("department", "").strip()
        user.pi = request.form.get("pi", "").strip()
        user.line_manager = request.form.get("line_manager", "").strip()
        user.linkedin_url = request.form.get("linkedin_url", "").strip()
        user.teams_url = request.form.get("teams_url", "").strip()
        user.kcl_url = request.form.get("kcl_url", "").strip()
        user.work_status = request.form.get("work_status", "Active")
        user.db_role = request.form.get("db_role", "Collaborator")
        user.phone = request.form.get("phone", "").strip()
        hours = request.form.get("hours_available", "").strip()
        user.hours_available = int(hours) if hours.isdigit() else 0

        photo = request.files.get("photo")
        saved = save_photo(photo)
        if saved:
            user.photo = saved

        db.session.commit()
        flash("Profile saved.", "success")
        return redirect(url_for("main.profile", user_id=user.id))

    return render_template("edit_profile.html", user=user)


# ---------------------------------------------------------------------------
# Research workstreams / themes
# ---------------------------------------------------------------------------
@main_bp.route("/workstreams")
@login_required
def workstreams():
    # Per-theme counts for projects and people.
    counts = {}
    for name in WORKSTREAM_NAMES:
        counts[name] = {
            "projects": Project.query.filter_by(workstream=name).count(),
            "people": User.query.filter(User.workstreams.ilike(f"%{name}%")).count(),
        }
    return render_template("workstreams.html", counts=counts)


@main_bp.route("/workstreams/<slug>")
@login_required
def workstream_detail(slug):
    ws = WORKSTREAM_BY_SLUG.get(slug) or abort(404)
    name = ws["name"]
    projects = Project.query.filter_by(workstream=name) \
        .order_by(Project.created_at.desc()).all()
    people = User.query.filter(User.workstreams.ilike(f"%{name}%")) \
        .order_by(User.full_name).all()
    return render_template(
        "workstream_detail.html", ws=ws, projects=projects, people=people,
    )


# ---------------------------------------------------------------------------
# News / announcements
# ---------------------------------------------------------------------------
@main_bp.route("/news")
@login_required
def news():
    posts = NewsPost.query.order_by(
        NewsPost.pinned.desc(), NewsPost.created_at.desc()
    ).all()
    return render_template("news.html", posts=posts)


@main_bp.route("/news/new", methods=["GET", "POST"])
@login_required
def news_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("An announcement needs a title.", "danger")
            return render_template("news_form.html", post=None)
        post = NewsPost(
            title=title,
            body=request.form.get("body", "").strip(),
            workstream=request.form.get("workstream", "").strip(),
            pinned=bool(request.form.get("pinned")),
            author_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash("Announcement published.", "success")
        return redirect(url_for("main.news_detail", post_id=post.id))
    return render_template("news_form.html", post=None)


@main_bp.route("/news/<int:post_id>")
@login_required
def news_detail(post_id):
    post = db.session.get(NewsPost, post_id) or abort(404)
    return render_template("news_detail.html", post=post)


@main_bp.route("/news/<int:post_id>/delete", methods=["POST"])
@login_required
def news_delete(post_id):
    post = db.session.get(NewsPost, post_id) or abort(404)
    if not (current_user.is_admin or post.author_id == current_user.id):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Announcement deleted.", "info")
    return redirect(url_for("main.news"))


# ---------------------------------------------------------------------------
# Events & seminars
# ---------------------------------------------------------------------------
@main_bp.route("/events")
@login_required
def events():
    now = datetime.utcnow()
    upcoming = Event.query.filter(Event.start_at >= now) \
        .order_by(Event.start_at).all()
    past = Event.query.filter(Event.start_at < now) \
        .order_by(Event.start_at.desc()).all()
    my_ids = {a.event_id for a in EventAttendance.query
              .filter_by(user_id=current_user.id).all()}
    return render_template("events.html", upcoming=upcoming, past=past,
                           my_ids=my_ids)


@main_bp.route("/events/new", methods=["GET", "POST"])
@login_required
def event_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        start_at = _parse_dt(request.form.get("start_at"))
        if not title or not start_at:
            flash("An event needs a title and a start date/time.", "danger")
            return render_template("event_form.html", event=None)
        ev = Event(
            title=title,
            description=request.form.get("description", "").strip(),
            event_type=request.form.get("event_type", "Seminar"),
            start_at=start_at,
            end_at=_parse_dt(request.form.get("end_at")),
            location=request.form.get("location", "").strip(),
            is_online=bool(request.form.get("is_online")),
            url=request.form.get("url", "").strip(),
            workstream=request.form.get("workstream", "").strip(),
            host_id=current_user.id,
        )
        db.session.add(ev)
        db.session.commit()
        flash("Event created.", "success")
        return redirect(url_for("main.event_detail", event_id=ev.id))
    return render_template("event_form.html", event=None)


@main_bp.route("/events/<int:event_id>")
@login_required
def event_detail(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    is_registered = EventAttendance.query.filter_by(
        user_id=current_user.id, event_id=ev.id).first() is not None
    can_manage_event = current_user.is_admin or ev.host_id == current_user.id
    return render_template("event_detail.html", event=ev,
                           is_registered=is_registered,
                           can_manage_event=can_manage_event)


@main_bp.route("/events/<int:event_id>/register", methods=["POST"])
@login_required
def event_register(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    exists = EventAttendance.query.filter_by(
        user_id=current_user.id, event_id=ev.id).first()
    if not exists:
        db.session.add(EventAttendance(user_id=current_user.id, event_id=ev.id))
        db.session.commit()
        flash("You're signed up for this event.", "success")
    return redirect(url_for("main.event_detail", event_id=ev.id))


@main_bp.route("/events/<int:event_id>/unregister", methods=["POST"])
@login_required
def event_unregister(event_id):
    att = EventAttendance.query.filter_by(
        user_id=current_user.id, event_id=event_id).first()
    if att:
        db.session.delete(att)
        db.session.commit()
        flash("You've cancelled your sign-up.", "info")
    return redirect(url_for("main.event_detail", event_id=event_id))


@main_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    if not (current_user.is_admin or ev.host_id == current_user.id):
        abort(403)
    db.session.delete(ev)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("main.events"))


# ---------------------------------------------------------------------------
# About & Impact
# ---------------------------------------------------------------------------
@main_bp.route("/about")
@login_required
def about():
    stats = {
        "projects": Project.query.count(),
        "researchers": User.query.count(),
        "completed": Project.query.filter_by(status="Completed").count(),
        "departments": db.session.query(User.department)
            .filter(User.department != "").distinct().count(),
    }
    return render_template("about.html", stats=stats)


@main_bp.route("/panel")
@login_required
def panel():
    return render_template("panel.html")


@main_bp.route("/impact")
@login_required
def impact():
    completed = Project.query.filter_by(status="Completed") \
        .order_by(Project.end_date.desc()).all()
    # Headline numbers for the impact hero.
    totals = {
        "completed": len(completed),
        "collaborators": len({c.user_id for p in completed
                              for c in p.collaborations}),
    }
    return render_template("impact.html", completed=completed, totals=totals)
