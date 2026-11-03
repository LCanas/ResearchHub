"""Monthly member newsletter: open projects matched to each person's keywords
and workstreams, plus upcoming events, recent news and the hackathon.

Sent by `python manage.py newsletter` (run monthly by cron on the server) or the
admin Newsletter page. Members can opt out from their profile or the one-click
link at the bottom of every newsletter.
"""
from datetime import datetime, timedelta

from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer

from .config import HACKATHON
from .extensions import db
from .mail import send_mail, absolute_url
from .models import User, Project, Event, NewsPost
from .recommend import matching_projects, has_interests

# Don't send to the same person twice within this window, even if the job is
# run again by hand.
MIN_DAYS_BETWEEN = 25


def _unsubscribe_serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="newsletter-unsubscribe")


def unsubscribe_token(user):
    return _unsubscribe_serializer().dumps(user.id)


def user_from_unsubscribe_token(token):
    try:
        return db.session.get(User, _unsubscribe_serializer().loads(token))
    except BadSignature:
        return None


def recipients():
    """Members who want the newsletter."""
    return User.query.filter(User.is_suspended.isnot(True),
                             User.newsletter_opt_in.is_(True)) \
        .order_by(User.full_name).all()


def build(user, now=None):
    """Return (subject, body) for this member, or None if there's nothing
    worth sending."""
    now = now or datetime.utcnow()
    since = user.newsletter_last_sent or (now - timedelta(days=31))
    month = now.strftime("%B %Y")

    matched_new = matching_projects(user, limit=5, since=since)
    matched_all = matching_projects(user, limit=5)
    # Prefer projects published since the last newsletter; top up with older
    # matches that are still open.
    projects = matched_new + [p for p in matched_all if p not in matched_new]
    projects = projects[:5]
    personalised = bool(projects)
    if not projects:
        projects = Project.query.filter_by(review_status="Approved", status="Open") \
            .order_by(Project.reviewed_at.desc()).limit(3).all()

    events = Event.query.filter(Event.start_at >= now,
                                Event.start_at <= now + timedelta(days=42)) \
        .order_by(Event.start_at).limit(5).all()
    news = NewsPost.query.filter(NewsPost.created_at >= since) \
        .order_by(NewsPost.pinned.desc(), NewsPost.created_at.desc()).limit(4).all()

    if not (projects or events or news):
        return None

    lines = [f"Hello {user.full_name.split()[0]},", "",
             f"Here's what's happening on the Collaboration Hub this month.", ""]

    if projects:
        lines.append("OPEN PROJECTS FOR YOU" if personalised else "OPEN PROJECTS")
        lines.append("-" * 40)
        if not personalised:
            lines.append("Add keywords and workstreams to your profile to get "
                         "projects matched to your interests.")
        for p in projects:
            tag = " (new)" if p in matched_new else ""
            lines.append(f"* {p.title}{tag}")
            details = " · ".join(x for x in (p.project_type, p.workstream) if x)
            if details:
                lines.append(f"  {details}")
            if p.summary:
                lines.append(f"  {p.summary}")
            lines.append(f"  {absolute_url('main.project_detail', project_id=p.id)}")
        lines += ["", f"All open projects: {absolute_url('main.projects', status='Open')}", ""]

    if events:
        lines += ["UPCOMING EVENTS", "-" * 40]
        for e in events:
            where = "Online" if e.is_online else (e.location or "Venue TBC")
            lines.append(f"* {e.start_at.strftime('%a %d %b, %H:%M')}: {e.title} ({where})")
            lines.append(f"  {absolute_url('main.event_detail', event_id=e.id)}")
        lines.append("")

    if news:
        lines += ["NEWS", "-" * 40]
        for n in news:
            lines.append(f"* {n.title}")
            lines.append(f"  {absolute_url('main.news_detail', post_id=n.id)}")
        lines.append("")

    lines += [f"{HACKATHON['name'].upper()} · {HACKATHON['when'].upper()}", "-" * 40,
              "Got a problem AI could help with? Submit a challenge:",
              absolute_url("main.hackathon"), ""]

    if not has_interests(user):
        lines += ["Tip: add keywords and workstreams to your profile so we can "
                  "match projects to you:", absolute_url("main.edit_profile"), ""]

    lines += ["", "You're receiving this monthly update as a member of the "
              "Collaboration Hub.",
              "Unsubscribe: " + absolute_url("main.newsletter_unsubscribe",
                                             token=unsubscribe_token(user))]
    return f"Your {month} update", "\n".join(lines) + "\n"


def send_all(force=False, only_email=None, dry_run=False):
    """Send the newsletter to every subscriber. Returns a summary dict."""
    now = datetime.utcnow()
    summary = {"sent": 0, "skipped_recent": 0, "nothing_to_send": 0, "recipients": []}
    people = recipients()
    if only_email:
        people = [u for u in people if u.email == only_email.strip().lower()]
    for user in people:
        if (not force and user.newsletter_last_sent
                and now - user.newsletter_last_sent < timedelta(days=MIN_DAYS_BETWEEN)):
            summary["skipped_recent"] += 1
            continue
        built = build(user, now)
        if not built:
            summary["nothing_to_send"] += 1
            continue
        subject, body = built
        summary["recipients"].append(user.email)
        if dry_run:
            print(f"\n===== {user.email}: {subject} =====\n{body}")
            continue
        send_mail([user.email], subject, body, wait=True)
        user.newsletter_last_sent = now
        db.session.commit()
        summary["sent"] += 1
    return summary
