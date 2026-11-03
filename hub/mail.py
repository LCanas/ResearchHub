"""Outgoing email notifications.

Configured entirely by environment variables, so nothing secret lives in code:

    MAIL_SERVER     SMTP host, e.g. smtp.office365.com. Unset = don't send,
                    just print the email to the log (useful locally).
    MAIL_PORT       default 587
    MAIL_USE_TLS    STARTTLS, default "1"
    MAIL_USE_SSL    implicit TLS (usually port 465), default "0"
    MAIL_USERNAME / MAIL_PASSWORD   SMTP login, if the server needs one
    MAIL_FROM       sender address, defaults to MAIL_USERNAME
    SITE_URL        public address used in links, e.g. https://aicollabhub.example.kcl.ac.uk

Emails are sent on a background thread so a slow mail server never delays the
page, and a failure is logged rather than shown to the user.
"""
import logging
import os
import smtplib
import threading
from email.message import EmailMessage

from flask import current_app, url_for

from .config import CONTACT_EMAIL

log = logging.getLogger(__name__)


def _env_flag(name, default):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def absolute_url(endpoint, **values):
    """Link for an email: SITE_URL if set (correct behind a proxy), else the
    address of the current request."""
    site = os.environ.get("SITE_URL", "").rstrip("/")
    if site:
        return site + url_for(endpoint, **values)
    return url_for(endpoint, _external=True, **values)


def absolute_link(path_or_url):
    """Full address for a stored link: a hub path like "/register" gets the
    site's address in front; full web addresses are left as they are."""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    from flask import request
    site = os.environ.get("SITE_URL", "").rstrip("/") or request.host_url.rstrip("/")
    return site + "/" + path_or_url.lstrip("/")


def _deliver(msg):
    host = os.environ.get("MAIL_SERVER", "")
    port = int(os.environ.get("MAIL_PORT", "587"))
    user = os.environ.get("MAIL_USERNAME", "")
    password = os.environ.get("MAIL_PASSWORD", "")
    try:
        if _env_flag("MAIL_USE_SSL", "0"):
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            if _env_flag("MAIL_USE_TLS", "1"):
                server.starttls()
        with server:
            if user:
                server.login(user, password)
            server.send_message(msg)
        log.info("Email sent to %s: %s", msg["To"], msg["Subject"])
    except Exception:  # never let email break the app
        log.exception("Could not send email to %s: %s", msg["To"], msg["Subject"])


def _html_body(body, header_png):
    """The email as HTML: the brand header image on top, then the text with
    its line breaks kept and web addresses clickable. Inline styles only, as
    email programs ignore stylesheets."""
    from markupsafe import escape
    import re
    text = str(escape(body))
    text = re.sub(r"(https?://[^\s<]+[^\s<.,;:!?)\]'\"])",
                  r'<a href="\1" style="color:#B3123A">\1</a>', text)
    text = text.replace("\n", "<br>\n")
    width = 600 if header_png == "banner" else 280
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#EEF0F3">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF0F3">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#FFFFFF">
<tr><td style="padding:{'0' if header_png == 'banner' else '24px 28px 8px'}">
<img src="cid:brand-header" width="{width}" alt="FoLSM AI Collaboration Hub" style="display:block;border:0;max-width:100%;height:auto">
</td></tr>
<tr><td style="padding:20px 28px 28px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#14234A">
{text}
</td></tr>
</table>
</td></tr>
</table>
</body></html>"""


def send_mail(recipients, subject, body, wait=False, banner_png=None):
    """Send an email to a list of addresses (duplicates / blanks removed), as
    plain text plus an HTML version headed by the FoLSM horizontal logo, or by
    ``banner_png`` (the newsletter banner) when given. Without MAIL_SERVER it
    is only logged. ``wait`` sends on the calling thread (for command-line jobs
    that exit straight afterwards)."""
    to = sorted({r.strip() for r in recipients if r and r.strip()})
    if not to:
        return
    sender = os.environ.get("MAIL_FROM") or os.environ.get("MAIL_USERNAME") \
        or "no-reply@localhost"
    msg = EmailMessage()
    msg["Subject"] = f"[FoLSM AI Collaboration Hub] {subject}"
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    # Replies go to the hub contact, even when sent from a no-reply address.
    if CONTACT_EMAIL and CONTACT_EMAIL != sender:
        msg["Reply-To"] = CONTACT_EMAIL
    msg.set_content(body)
    try:
        from .branding import email_logo_png
        header = banner_png or email_logo_png()
        msg.add_alternative(_html_body(body, "banner" if banner_png else "logo"), subtype="html")
        # The image travels inside the email (not linked), so it shows even
        # where the hub isn't reachable and isn't blocked as a remote image.
        msg.get_payload()[1].add_related(header, "image", "png", cid="<brand-header>",
                                         filename="folsm-ai-hub.png")
    except Exception:  # never let branding stop an email going out
        current_app.logger.exception("Couldn't add the brand header; sending plain text")

    if not os.environ.get("MAIL_SERVER"):
        # Print it readably (the raw message wraps long lines, breaking links).
        readable = f"To: {msg['To']}\nSubject: {msg['Subject']}\n\n{body}"
        current_app.logger.info("MAIL_SERVER not set: email not sent:\n%s", readable)
        print(f"\n--- email (not sent: MAIL_SERVER unset) ---\n{readable}\n---\n", flush=True)
        return
    if wait or current_app.testing:
        _deliver(msg)
    else:
        threading.Thread(target=_deliver, args=(msg,), daemon=True).start()
