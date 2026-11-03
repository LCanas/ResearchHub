"""Match open projects to a member's interests.

Used by the "declined" email and the monthly newsletter. Scoring is simple and
explainable:
  +3  project is in one of the member's workstreams
  +2  for each project keyword that matches one of the member's keywords
  +1  for each member keyword found in the project's title / summary / description
  +1  same department
Only projects scoring above zero count as a match.
"""
import re

from .models import Project, Collaboration, JoinRequest


def _terms(text):
    return {t.strip().lower() for t in re.split(r"[,|;]", text or "") if t.strip()}


def score(project, user):
    my_keywords = _terms(user.keywords)
    s = 0
    if project.workstream and project.workstream in user.workstream_list:
        s += 3
    s += 2 * len(my_keywords & _terms(project.keywords))
    blob = " ".join([project.title or "", project.summary or "",
                     project.description or ""]).lower()
    s += sum(1 for k in my_keywords if len(k) > 2 and k in blob)
    if user.department and project.department == user.department:
        s += 1
    return s


def matching_projects(user, limit=5, exclude_ids=(), since=None):
    """Live, open projects this member isn't already part of, best match first.
    ``since`` keeps only projects published after that time (for the newsletter)."""
    involved = {c.project_id for c in Collaboration.query.filter_by(user_id=user.id)}
    involved |= {r.project_id for r in JoinRequest.query.filter_by(user_id=user.id)}
    involved |= set(exclude_ids)

    query = Project.query.filter(Project.review_status == "Approved",
                                 Project.status == "Open")
    if since:
        query = query.filter(Project.reviewed_at >= since)
    candidates = [p for p in query.all()
                  if p.id not in involved and user.id not in (p.proposer_id, p.pi_id)]
    scored = [(score(p, user), p) for p in candidates]
    scored = [(s, p) for s, p in scored if s > 0]
    scored.sort(key=lambda sp: (sp[0], sp[1].created_at), reverse=True)
    return [p for _, p in scored[:limit]]


def has_interests(user):
    return bool(_terms(user.keywords) or user.workstream_list)
