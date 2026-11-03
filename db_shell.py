"""Interactive database shell for the Collaboration Hub.

Opens the app + database and drops you into a Python prompt with the ORM ready,
so you can read and change data without writing SQL by hand.

Run:   python db_shell.py

Examples once inside:
    User.query.count()
    [u.full_name for u in User.query.all()]
    Project.query.filter_by(status="Open").all()
    User.query.filter(User.hours_available >= 10).all()

    # change something and save it:
    u = User.query.filter_by(email="s.cooper@kcl.ac.uk").first()
    u.hours_available = 6
    db.session.commit()

Exit with Ctrl-Z then Enter (Windows) or Ctrl-D.
"""
import code

from hub import create_app
from hub.extensions import db
from hub.models import (
    User, Project, Milestone, Collaboration, JoinRequest,
    NewsPost, Event, EventAttendance,
)

app = create_app()
app.app_context().push()

banner = (
    "\nCollaboration Hub: database shell (SQLite file: hub.db)\n"
    "Ready: db, User, Project, Milestone, Collaboration, JoinRequest, "
    "NewsPost, Event, EventAttendance\n"
    "Try:  User.query.count()\n"
)
code.interact(banner=banner, local=dict(
    db=db, User=User, Project=Project, Milestone=Milestone,
    Collaboration=Collaboration, JoinRequest=JoinRequest,
    NewsPost=NewsPost, Event=Event, EventAttendance=EventAttendance,
))
