"""Authentication: register, login, logout (requirement 2)."""
import os
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
)
from flask_login import login_user, logout_user, login_required, current_user

from .accounts import RESET_LINK_HOURS, make_reset_token, user_from_reset_token
from .config import DEFAULT_ADMIN_EMAILS
from .extensions import db
from .mail import send_mail, absolute_url
from .models import User

auth_bp = Blueprint("auth", __name__)


def _emails_from_env(name):
    return {e.strip().lower() for e in os.environ.get(name, "").split(",") if e.strip()}


def sync_roles(user):
    """Grant admin / committee rights to the emails listed in HUB_ADMIN_EMAILS
    and HUB_COMMITTEE_EMAILS (comma separated; HUB_REVIEWER_EMAILS is the old
    name). Only grants — never revokes; use the Members page or manage.py."""
    admins = _emails_from_env("HUB_ADMIN_EMAILS") | {e.lower() for e in DEFAULT_ADMIN_EMAILS}
    if user.email in admins:
        user.set_role("admin")
    elif user.email in (_emails_from_env("HUB_COMMITTEE_EMAILS")
                        | _emails_from_env("HUB_REVIEWER_EMAILS")):
        if not user.is_admin:
            user.set_role("committee")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = []
        if not full_name:
            errors.append("Please enter your full name.")
        if not email:
            errors.append("Please enter your email.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")
        if not request.form.get("agree_coc"):
            errors.append("Please read and agree to the Code of Conduct.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form=request.form)

        user = User(
            full_name=full_name,
            email=email,
            department=request.form.get("department", "").strip(),
            contract_type=request.form.get("contract_type", "").strip(),
            db_role=request.form.get("db_role", "Collaborator"),
            coc_accepted_at=datetime.utcnow(),
            newsletter_opt_in=bool(request.form.get("newsletter_opt_in")),
        )
        user.set_password(password)
        sync_roles(user)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to the Collaboration Hub! Complete your profile below.",
              "success")
        return redirect(url_for("main.edit_profile"))

    return render_template("auth/register.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)
        if user.is_suspended:
            flash("This account has been suspended. Please contact the hub "
                  "administrators.", "danger")
            return render_template("auth/login.html", email=email)

        sync_roles(user)
        db.session.commit()
        login_user(user, remember=remember)
        next_page = request.args.get("next", "")
        # Only follow local paths.
        if not next_page.startswith("/") or next_page.startswith("//"):
            next_page = url_for("main.index")
        flash(f"Signed in as {user.full_name}.", "success")
        return redirect(next_page)

    return render_template("auth/login.html", email="")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Forgot password: email a signed link that expires and works only once.
# ---------------------------------------------------------------------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.change_password"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and not user.is_suspended:
            link = absolute_url("auth.reset_password_with_token",
                                token=make_reset_token(user))
            send_mail(
                [user.email], "Reset your password",
                f"Hello {user.full_name},\n\nSomeone (hopefully you) asked to reset "
                f"your Collaboration Hub password. Choose a new one here:\n\n"
                f"    {link}\n\nThe link works once and expires in "
                f"{RESET_LINK_HOURS} hour{'s' if RESET_LINK_HOURS != 1 else ''}. "
                f"If you didn't ask for this, you can ignore this email.\n",
            )
        # Same answer whether or not the account exists, so the form can't be
        # used to find out who is registered.
        flash("If an account exists for that email, we've sent a link to reset "
              "the password. Check your inbox (and junk folder).", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_with_token(token):
    user = user_from_reset_token(token)
    if user is None:
        flash("That reset link is invalid or has expired. Please request a new one.",
              "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user.set_password(password)
            user.must_change_password = False
            db.session.commit()
            flash("Your password has been reset. You can sign in now.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
