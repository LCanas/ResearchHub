"""Admin account operations shared by the Members page and manage.py."""
import os
import secrets

from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .extensions import db
from .models import Project, NewsPost, Event, EventAttendance, User


def reset_password(user, new_password=None):
    """Set a temporary password the person must change at next sign-in.
    Returns the password so it can be passed on to them."""
    temp = new_password or secrets.token_urlsafe(9)
    user.set_password(temp)
    user.must_change_password = True
    db.session.commit()
    return temp


def delete_user(user):
    """Delete a profile. Their projects, announcements and events stay on the
    hub but lose the link to them; their memberships, join requests and event
    sign-ups are removed."""
    uid = user.id
    Project.query.filter_by(proposer_id=uid).update({"proposer_id": None})
    Project.query.filter_by(pi_id=uid).update({"pi_id": None})
    Project.query.filter_by(reviewed_by_id=uid).update({"reviewed_by_id": None})
    NewsPost.query.filter_by(author_id=uid).update({"author_id": None})
    Event.query.filter_by(host_id=uid).update({"host_id": None})
    EventAttendance.query.filter_by(user_id=uid).delete()
    photo = user.photo
    db.session.delete(user)          # collaborations + join requests cascade
    db.session.commit()

    if photo:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo)
        try:
            os.remove(path)
        except OSError:
            pass


RESET_LINK_HOURS = 1


def _reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")


def make_reset_token(user):
    """A signed, expiring token for a "forgot password" link. It embeds a piece
    of the current password hash, so it stops working once it has been used."""
    return _reset_serializer().dumps({"id": user.id, "h": user.password_hash[-16:]})


def user_from_reset_token(token):
    try:
        data = _reset_serializer().loads(token, max_age=RESET_LINK_HOURS * 3600)
    except BadSignature:            # also covers expired tokens
        return None
    user = db.session.get(User, data.get("id"))
    if not user or user.is_suspended or user.password_hash[-16:] != data.get("h"):
        return None
    return user


def set_suspended(user, suspended):
    user.is_suspended = suspended
    db.session.commit()


def is_last_admin(user):
    return user.is_admin and User.query.filter_by(is_admin=True).count() == 1
