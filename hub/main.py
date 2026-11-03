"""Main application routes: projects, profiles, directory, join flow."""
import math
import os
import uuid
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from .extensions import db
from .accounts import reset_password, delete_user, is_last_admin, set_suspended
from .mail import send_mail, absolute_url
from .newsletter import (build as build_newsletter, send_all as send_newsletters,
                         recipients as newsletter_recipients,
                         user_from_unsubscribe_token)
from .recommend import matching_projects
from .models import (
    User, Project, Milestone, Collaboration, JoinRequest,
    NewsPost, Event, EventAttendance, USER_ROLES,
)
from .config import (
    STAGE_NAMES, PROJECT_TYPE_NAMES, WORKSTREAM_NAMES, WORKSTREAM_BY_SLUG,
    EVENT_TYPES, REVIEW_STATUSES, WORKSTREAMS, HERO_ART, HACKATHON,
)

main_bp = Blueprint("main", __name__)

# Pages anyone can read without signing in (their routes omit @login_required).
# Everything else needs an account.
PUBLIC_ENDPOINTS = {
    "main.index", "main.about", "main.panel", "main.impact",
    "main.workstreams", "main.workstream_detail", "main.news",
    "main.news_detail", "main.events", "main.event_detail",
    "main.code_of_conduct", "main.hackathon", "main.newsletter_unsubscribe",
}

# Endpoints a signed-in user can still reach before agreeing to the Code of
# Conduct (so they can read it, agree, or leave).
_COC_EXEMPT = PUBLIC_ENDPOINTS | {"main.code_of_conduct_accept", "auth.logout",
                                  "main.change_password", "static"}


@main_bp.before_app_request
def require_password_change():
    """After an admin reset, the temporary password must be replaced first."""
    if (current_user.is_authenticated and current_user.must_change_password
            and request.endpoint not in ("main.change_password", "auth.logout",
                                         "static")):
        flash("Please choose a new password to continue.", "info")
        return redirect(url_for("main.change_password"))


@main_bp.before_app_request
def require_code_of_conduct():
    """Accounts created before the Code of Conduct existed must agree to it."""
    if (current_user.is_authenticated and not current_user.coc_accepted_at
            and request.endpoint not in _COC_EXEMPT):
        flash("Please read and agree to the Code of Conduct to continue.", "info")
        return redirect(url_for("main.code_of_conduct", next=request.path))


@main_bp.app_context_processor
def inject_review_count():
    count = 0
    if current_user.is_authenticated and current_user.can_review:
        count = Project.query.filter_by(review_status="Pending review").count()
    return {"review_queue_count": count}


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


def active_users():
    """Members who aren't suspended — the only ones shown around the hub."""
    return User.query.filter(User.is_suspended.isnot(True))


def live_projects():
    """Projects approved by a reviewer — the only ones listed on the hub."""
    return Project.query.filter(Project.review_status == "Approved")


def can_view(project):
    """Live projects are visible to members; submissions only to their own
    team and to reviewers."""
    return project.is_live or can_manage(project) or (
        current_user.is_authenticated and current_user.can_review)


def committee_emails():
    return [u.email for u in active_users().filter(
        or_(User.is_reviewer.is_(True), User.is_admin.is_(True))).all()]


def project_leads(project):
    """Proposer and PI — the people who handle join requests."""
    return [u for u in (project.proposer, project.pi_user) if u]


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


def build_hub_graph(sample=False):
    """Layout for the "live" hero: one node per workstream, sized by how many
    researchers chose it, with a dot orbiting it per person (new sign-ups in
    crimson) and links weighted by people who share two workstreams.

    ``sample`` fills in made-up numbers so the design can be previewed on an
    empty database (debug mode only — never shown on the live site)."""
    cx, cy, ring = 280, 240, 172
    users = [] if sample else active_users().all()
    week_ago = datetime.utcnow() - timedelta(days=7)

    members = {w["name"]: [] for w in WORKSTREAMS}
    for u in users:
        for name in u.workstream_list:
            if name in members:
                members[name].append(u)
    if sample:
        for (name, _), n in zip(members.items(), [12, 9, 7, 5, 8, 4, 6]):
            members[name] = [None] * n

    nodes = []
    for i, w in enumerate(WORKSTREAMS):
        angle = -math.pi / 2 + 2 * math.pi * i / len(WORKSTREAMS)
        people = members[w["name"]]
        r = 16 + min(22, 5 * math.sqrt(len(people)))
        x, y = cx + ring * math.cos(angle), cy + ring * math.sin(angle)
        dots = []
        for k, u in enumerate(people[:10]):
            is_new = (k < 2) if sample else bool(u.created_at and u.created_at >= week_ago)
            orbit = r + 7 + (k % 2) * 6
            a = 2 * math.pi * k / min(len(people), 10)
            dots.append({
                "x": round(x + orbit * math.cos(a), 1),
                "y": round(y + orbit * math.sin(a), 1),
                "dur": 16 + (k * 7) % 11,
                "new": is_new,
            })
        nodes.append({"ws": w, "x": round(x, 1), "y": round(y, 1), "r": round(r, 1),
                      "count": len(people), "dots": dots,
                      "label_y": round(y + r + 15, 1) if y >= cy - 1 else round(y - r - 9, 1)})

    links = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = WORKSTREAMS[i]["name"], WORKSTREAMS[j]["name"]
            shared = (len({id(u) for u in members[a] if u} & {id(u) for u in members[b] if u})
                      if not sample else (3 if (i + j) % 3 == 0 else 0))
            if shared:
                links.append({"a": nodes[i], "b": nodes[j], "w": min(1 + shared, 6)})

    return {"cx": cx, "cy": cy, "nodes": nodes, "links": links,
            "people": len(users) if not sample else 38,
            "new_this_week": sum(1 for u in users if u.created_at and u.created_at >= week_ago)
            if not sample else 5}


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
def index():
    stats = {
        "projects": live_projects().count(),
        "open": live_projects().filter_by(status="Open").count(),
        "ongoing": live_projects().filter_by(status="Ongoing").count(),
        "completed": live_projects().filter_by(status="Completed").count(),
        "researchers": active_users().count(),
    }
    latest_news = NewsPost.query.order_by(
        NewsPost.pinned.desc(), NewsPost.created_at.desc()
    ).limit(4).all()
    upcoming_events = Event.query.filter(Event.start_at >= datetime.utcnow()) \
        .order_by(Event.start_at).limit(4).all()
    # A few open projects to feature as calls for collaborators.
    featured = live_projects().filter_by(status="Open") \
        .order_by(Project.created_at.desc()).limit(3).all()
    if len(featured) < 3:
        extra = live_projects().filter(Project.status != "Open") \
            .order_by(Project.created_at.desc()).limit(3 - len(featured)).all()
        featured = featured + extra

    # /?hero=match|live|network previews the other hero illustrations.
    hero_art = request.args.get("hero", HERO_ART)
    if hero_art not in ("network", "match", "live"):
        hero_art = HERO_ART
    hub_graph = None
    if hero_art == "live":
        sample = request.args.get("sample") == "1" and current_app.debug
        hub_graph = build_hub_graph(sample=sample)

    return render_template(
        "home.html", stats=stats, latest_news=latest_news,
        upcoming_events=upcoming_events, featured=featured,
        hero_art=hero_art, hub_graph=hub_graph,
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

    query = live_projects()
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

    stage_counts = {s: live_projects().filter_by(status=s).count()
                    for s in STAGE_NAMES}
    stats = {
        "projects": live_projects().count(),
        "open": live_projects().filter_by(status="Open").count(),
        "ongoing": live_projects().filter_by(status="Ongoing").count(),
        "researchers": active_users().count(),
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
    if not can_view(project):
        abort(404)
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
            ip_agreement=request.form.get("ip_agreement", "").strip(),
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

        errors = []
        if not project.title:
            errors.append("A project needs a title.")
        if not project.ip_agreement:
            errors.append("Please set out how IP, authorship and publications "
                          "will be agreed (see the Code of Conduct).")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("project_form.html", project=project,
                                   is_new=True,
                                   users=active_users().order_by(User.full_name).all())

        # Every submission — committee members' included — waits on hold
        # until the committee approves it.
        project.review_status = "Pending review"
        db.session.add(project)
        db.session.commit()

        send_mail(
            committee_emails(),
            f"New submission to review: {project.title}",
            f"{current_user.full_name} has submitted a "
            f"{(project.project_type or 'project').lower()} for review:\n\n"
            f"  {project.title}\n  {project.summary}\n\n"
            f"Review it here: {absolute_url('main.project_detail', project_id=project.id)}\n"
            f"Review queue: {absolute_url('main.review_queue')}\n",
        )
        # Receipt to the proposer, and a heads-up to anyone named as PI.
        link = absolute_url("main.project_detail", project_id=project.id)
        send_mail(
            [current_user.email], f"Submission received: {project.title}",
            f"Hello {current_user.full_name},\n\nThank you for submitting "
            f"“{project.title}”. It is on hold until the committee reviews "
            f"it against the panel criteria (clinical impact, data readiness, "
            f"resources and AI feasibility). We'll email you the decision.\n\n"
            f"You can follow its status here: {link}\n",
        )
        if project.pi_user and project.pi_id != current_user.id:
            send_mail(
                [project.pi_user.email], f"You've been named as PI: {project.title}",
                f"Hello {project.pi_user.full_name},\n\n{current_user.full_name} has "
                f"submitted “{project.title}” to the Collaboration Hub and "
                f"named you as Principal Investigator. It is on hold until the "
                f"committee reviews it.\n\nIf this isn't right, please let them know.\n\n"
                f"{link}\n",
            )
        flash("Thanks! Your project is on hold until the committee reviews it. "
              "It will appear on the hub once approved.", "success")
        return redirect(url_for("main.project_detail", project_id=project.id))

    # Pre-select a project type, e.g. /projects/new?type=Hackathon
    preset_type = request.args.get("type", "")
    return render_template(
        "project_form.html", project=None, is_new=True,
        preset_type=preset_type if preset_type in PROJECT_TYPE_NAMES else "",
        users=active_users().order_by(User.full_name).all(),
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
        project.ip_agreement = request.form.get("ip_agreement", "").strip()
        project.github_url = request.form.get("github_url", "").strip()
        project.department = request.form.get("department", "").strip()
        project.keywords = request.form.get("keywords", "").strip()
        project.start_date = _parse_date(request.form.get("start_date"),
                                         project.start_date)
        project.end_date = _parse_date(request.form.get("end_date"),
                                       project.end_date)
        pi_id = request.form.get("pi_id")
        project.pi_id = int(pi_id) if pi_id else None
        # Editing after the committee asked for changes puts it back in the queue.
        if project.review_status == "Changes requested" and not current_user.can_review:
            project.review_status = "Pending review"
            send_mail(committee_emails(), f"Resubmitted for review: {project.title}",
                      f"{current_user.full_name} has updated \u201c{project.title}\u201d "
                      f"after changes were requested.\n\n"
                      f"{absolute_url('main.project_detail', project_id=project.id)}\n")
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("main.project_detail", project_id=project.id))

    return render_template(
        "project_form.html", project=project,
        users=active_users().order_by(User.full_name).all(),
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


# --- Review: submissions are approved before they go live -------------------
@main_bp.route("/review")
@login_required
def review_queue():
    if not current_user.can_review:
        abort(403)
    pending = Project.query.filter(Project.review_status.in_(
        ["Pending review", "Changes requested"])) \
        .order_by(Project.created_at).all()
    recent = Project.query.filter(
        Project.review_status.in_(["Approved", "Declined"]),
        Project.reviewed_at.isnot(None),
    ).order_by(Project.reviewed_at.desc()).limit(10).all()
    return render_template("review_queue.html", pending=pending, recent=recent)


@main_bp.route("/projects/<int:project_id>/review", methods=["POST"])
@login_required
def project_review(project_id):
    if not current_user.can_review:
        abort(403)
    project = db.session.get(Project, project_id) or abort(404)
    decision = request.form.get("decision", "")
    if decision not in REVIEW_STATUSES or decision == "Pending review":
        abort(400)
    note = request.form.get("note", "").strip()
    if decision != "Approved" and not note:
        flash("Please add a note telling the proposer why.", "danger")
        return redirect(url_for("main.project_detail", project_id=project.id))
    # Committee members can't approve their own projects; another member (or
    # an admin) must.
    own = current_user.id in (project.proposer_id, project.pi_id)
    if own and decision == "Approved" and not current_user.is_admin:
        flash("You can't approve your own project — another committee member "
              "needs to review it.", "warning")
        return redirect(url_for("main.project_detail", project_id=project.id))
    project.review_status = decision
    project.review_note = note
    project.reviewed_by_id = current_user.id
    project.reviewed_at = datetime.utcnow()
    db.session.commit()

    outcome = {
        "Approved": "has been approved and is now live on the hub",
        "Changes requested": "needs some changes before it can go live",
        "Declined": "has not been approved",
    }[decision]
    send_mail(
        [u.email for u in project_leads(project)],
        f"{decision}: {project.title}",
        f"Your submission \u201c{project.title}\u201d {outcome}.\n\n"
        + (f"Note from the committee:\n{note}\n\n" if note else "")
        + f"{absolute_url('main.project_detail', project_id=project.id)}\n",
    )
    flash(f"\u201c{project.title}\u201d marked as {decision.lower()}.", "success")
    return redirect(url_for("main.review_queue"))


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
    if not project.is_live:
        abort(404)
    if not request.form.get("agree_terms"):
        flash("Please confirm you agree to this project's IP and publication "
              "terms before requesting to join.", "danger")
        return redirect(url_for("main.project_detail", project_id=project.id))

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

    leads = [u for u in project_leads(project) if u.id != current_user.id]
    send_mail(
        [u.email for u in leads],
        f"{current_user.full_name} would like to join {project.title}",
        f"{current_user.full_name}"
        f"{' (' + current_user.department + ')' if current_user.department else ''} "
        f"has asked to join \u201c{project.title}\u201d and has accepted the project's "
        f"IP and publication terms.\n\n"
        + (f"Their message:\n{req.message}\n\n" if req.message else "")
        + f"Their profile: {absolute_url('main.profile', user_id=current_user.id)}\n"
        f"Accept or decline: {absolute_url('main.project_detail', project_id=project.id)}\n",
    )
    flash("Your request to join has been sent to the project team.", "success")
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
        # A decline must always carry a personal message from the team.
        note = request.form.get("note", "").strip()
        if len(note) < 10:
            flash("Please write a short message to the person explaining the "
                  "decision — it's sent to them by email.", "danger")
            return redirect(request.referrer
                            or url_for("main.project_detail", project_id=req.project_id))
        req.status = "Rejected"
        req.response_note = note
        flash("Request declined and your message sent.", "info")
    else:
        abort(400)
    db.session.commit()

    project = req.project
    link = absolute_url("main.project_detail", project_id=project.id)
    if req.status == "Accepted":
        send_mail(
            [req.user.email], f"You've joined {project.title}",
            f"Hello {req.user.full_name},\n\n{current_user.full_name} has accepted "
            f"your request to join “{project.title}”. Welcome to the team!\n\n"
            f"As agreed when you asked to join, the project's IP, authorship and "
            f"publication terms apply, and outcomes need the approval of both "
            f"parties before they're shared.\n\n{link}\n",
        )
    else:
        send_mail(
            [req.user.email], f"Your request to join {project.title}",
            f"Hello {req.user.full_name},\n\nYour request to join "
            f"“{project.title}” hasn't been accepted this time. "
            f"{current_user.full_name} wrote:\n\n{req.response_note}\n\n"
            f"Thank you for your interest."
            + _suggestions_text(req.user, exclude_ids=[project.id]),
        )
    return redirect(request.referrer
                    or url_for("main.project_detail", project_id=req.project_id))


def _suggestions_text(user, exclude_ids=()):
    """Open projects matching someone's keywords/workstreams, for an email."""
    matches = matching_projects(user, limit=3, exclude_ids=exclude_ids)
    all_open = absolute_url("main.projects", status="Open")
    if not matches:
        return f" Other open projects: {all_open}\n"
    lines = ["\n\nOpen projects that match your interests:"]
    for p in matches:
        lines.append(f"* {p.title}\n  {absolute_url('main.project_detail', project_id=p.id)}")
    lines.append(f"\nAll open projects: {all_open}\n")
    return "\n".join(lines)


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

    query = active_users()
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
    if user.is_suspended and not current_user.is_admin:
        abort(404)
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
        user.newsletter_opt_in = bool(request.form.get("newsletter_opt_in"))

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
def workstreams():
    # Per-theme counts for projects and people.
    counts = {}
    for name in WORKSTREAM_NAMES:
        counts[name] = {
            "projects": live_projects().filter_by(workstream=name).count(),
            "people": active_users().filter(User.workstreams.ilike(f"%{name}%")).count(),
        }
    return render_template("workstreams.html", counts=counts)


@main_bp.route("/workstreams/<slug>")
def workstream_detail(slug):
    ws = WORKSTREAM_BY_SLUG.get(slug) or abort(404)
    name = ws["name"]
    projects = live_projects().filter_by(workstream=name) \
        .order_by(Project.created_at.desc()).all()
    people = active_users().filter(User.workstreams.ilike(f"%{name}%")) \
        .order_by(User.full_name).all()
    return render_template(
        "workstream_detail.html", ws=ws, projects=projects, people=people,
    )


# ---------------------------------------------------------------------------
# News / announcements
# ---------------------------------------------------------------------------
@main_bp.route("/news")
def news():
    posts = NewsPost.query.order_by(
        NewsPost.pinned.desc(), NewsPost.created_at.desc()
    ).all()
    return render_template("news.html", posts=posts)


@main_bp.route("/news/new", methods=["GET", "POST"])
@login_required
def news_new():
    if not current_user.can_review:
        abort(403)
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
def events():
    now = datetime.utcnow()
    upcoming = Event.query.filter(Event.start_at >= now) \
        .order_by(Event.start_at).all()
    past = Event.query.filter(Event.start_at < now) \
        .order_by(Event.start_at.desc()).all()
    my_ids = set()
    if current_user.is_authenticated:
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
def event_detail(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    is_registered = can_manage_event = False
    if current_user.is_authenticated:
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
def about():
    stats = {
        "projects": live_projects().count(),
        "researchers": active_users().count(),
        "completed": live_projects().filter_by(status="Completed").count(),
        "departments": db.session.query(User.department)
            .filter(User.department != "").distinct().count(),
    }
    return render_template("about.html", stats=stats)


@main_bp.route("/panel")
def panel():
    return render_template("panel.html")


@main_bp.route("/impact")
def impact():
    completed = live_projects().filter_by(status="Completed") \
        .order_by(Project.end_date.desc()).all()
    # Headline numbers for the impact hero.
    totals = {
        "completed": len(completed),
        "collaborators": len({c.user_id for p in completed
                              for c in p.collaborations}),
    }
    return render_template("impact.html", completed=completed, totals=totals)


# ---------------------------------------------------------------------------
# Code of Conduct & Hackathon
# ---------------------------------------------------------------------------
@main_bp.route("/code-of-conduct")
def code_of_conduct():
    return render_template("code_of_conduct.html",
                           next_url=request.args.get("next", ""))


@main_bp.route("/code-of-conduct/accept", methods=["POST"])
@login_required
def code_of_conduct_accept():
    if not request.form.get("agree_coc"):
        flash("Tick the box to confirm you agree.", "danger")
        return redirect(url_for("main.code_of_conduct"))
    current_user.coc_accepted_at = datetime.utcnow()
    db.session.commit()
    flash("Thank you — you've agreed to the Code of Conduct.", "success")
    next_url = request.form.get("next", "")
    # Only follow local paths.
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.index")
    return redirect(next_url)


@main_bp.route("/hackathon")
def hackathon():
    challenges = live_projects().filter_by(project_type="Hackathon") \
        .order_by(Project.created_at.desc()).all()
    # Countdown target: the exact start if known, else the first of the month.
    exact = bool(HACKATHON.get("start"))
    target = HACKATHON["start"] if exact else HACKATHON["month_start"]
    try:
        days_left = (datetime.fromisoformat(target) - datetime.utcnow()).days
    except ValueError:
        days_left = None
    return render_template("hackathon.html", challenges=challenges,
                           countdown_target=target, countdown_exact=exact,
                           days_left=days_left)


# ---------------------------------------------------------------------------
# Admin: members & roles
# ---------------------------------------------------------------------------
@main_bp.route("/admin/members")
@login_required
def admin_members():
    if not current_user.is_admin:
        abort(403)
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    members = query.order_by(User.is_admin.desc(), User.is_reviewer.desc(),
                             User.full_name).all()
    return render_template("admin_members.html", members=members, q=q,
                           roles=USER_ROLES)


@main_bp.route("/admin/members/<int:user_id>/role", methods=["POST"])
@login_required
def admin_set_role(user_id):
    if not current_user.is_admin:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    role = request.form.get("role", "")
    if role not in USER_ROLES:
        abort(400)
    if user.id == current_user.id and role != "admin" \
            and User.query.filter_by(is_admin=True).count() == 1:
        flash("You're the only admin — make someone else admin first.", "warning")
        return redirect(url_for("main.admin_members"))
    user.set_role(role)
    db.session.commit()
    flash(f"{user.full_name} is now {role}.", "success")
    return redirect(url_for("main.admin_members", q=request.form.get("q", "")))


@main_bp.route("/admin/members/<int:user_id>/reset-password", methods=["POST"])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    temp = reset_password(user)
    send_mail(
        [user.email], "Your password has been reset",
        f"Hello {user.full_name},\n\nAn administrator has reset your Collaboration "
        f"Hub password. Your temporary password is:\n\n    {temp}\n\n"
        f"Sign in at {absolute_url('auth.login')} and you'll be asked to choose a "
        f"new one.\n",
    )
    # Shown once to the admin, as email may not be configured yet.
    flash(f"Temporary password for {user.full_name} ({user.email}): {temp} — "
          f"pass it on securely; they must change it when they sign in.", "warning")
    return redirect(url_for("main.admin_members", q=request.form.get("q", "")))


@main_bp.route("/admin/members/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_member(user_id):
    if not current_user.is_admin:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id:
        flash("You can't delete your own account from here.", "warning")
        return redirect(url_for("main.admin_members"))
    if is_last_admin(user):
        flash("That's the only admin — make someone else admin first.", "warning")
        return redirect(url_for("main.admin_members"))
    name = user.full_name
    delete_user(user)
    flash(f"{name}'s profile has been deleted.", "success")
    return redirect(url_for("main.admin_members", q=request.form.get("q", "")))


# ---------------------------------------------------------------------------
# Account: change own password
# ---------------------------------------------------------------------------
@main_bp.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current", "")
        new = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        errors = []
        if not current_user.check_password(current):
            errors.append("Your current password is incorrect.")
        if len(new) < 6:
            errors.append("The new password must be at least 6 characters.")
        if new != confirm:
            errors.append("The new passwords do not match.")
        if new and new == current:
            errors.append("Choose a password different from the current one.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("change_password.html")
        current_user.set_password(new)
        current_user.must_change_password = False
        db.session.commit()
        flash("Your password has been changed.", "success")
        return redirect(url_for("main.index"))
    return render_template("change_password.html")


@main_bp.route("/admin/members/<int:user_id>/suspend", methods=["POST"])
@login_required
def admin_suspend_member(user_id):
    """Block (or unblock) someone from signing in, keeping all their data."""
    if not current_user.is_admin:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    suspend = request.form.get("suspend") == "1"
    if suspend and user.id == current_user.id:
        flash("You can't suspend your own account.", "warning")
    elif suspend and is_last_admin(user):
        flash("That's the only admin — make someone else admin first.", "warning")
    else:
        set_suspended(user, suspend)
        flash(f"{user.full_name} has been {'suspended' if suspend else 'reactivated'}.",
              "success")
    return redirect(url_for("main.admin_members", q=request.form.get("q", "")))


# ---------------------------------------------------------------------------
# Monthly newsletter
# ---------------------------------------------------------------------------
@main_bp.route("/newsletter/unsubscribe/<token>", methods=["GET", "POST"])
def newsletter_unsubscribe(token):
    # GET only shows a button, so email link-scanners can't unsubscribe people.
    user = user_from_unsubscribe_token(token) or abort(404)
    done = False
    if request.method == "POST":
        user.newsletter_opt_in = False
        db.session.commit()
        done = True
    return render_template("newsletter_unsubscribe.html", user=user, done=done)


@main_bp.route("/admin/newsletter", methods=["GET", "POST"])
@login_required
def admin_newsletter():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        result = send_newsletters(force=bool(request.form.get("force")))
        flash(f"Newsletter sent to {result['sent']} member(s). "
              f"Skipped {result['skipped_recent']} who received one in the last "
              f"few weeks and {result['nothing_to_send']} with nothing to send.",
              "success")
        return redirect(url_for("main.admin_newsletter"))

    subscribers = newsletter_recipients()
    preview_for = db.session.get(User, request.args.get("preview", type=int) or 0) \
        or current_user
    preview = build_newsletter(preview_for)
    last_sent = max((u.newsletter_last_sent for u in subscribers
                     if u.newsletter_last_sent), default=None)
    return render_template("admin_newsletter.html", subscribers=subscribers,
                           preview_for=preview_for, preview=preview,
                           last_sent=last_sent,
                           members=active_users().order_by(User.full_name).all())
