"""Command-line admin for the Collaboration Hub: run it where the app runs
(your laptop, or on the VM / inside the container) so it uses the same database.

    python manage.py list                          # everyone with a role
    python manage.py list --all                    # every member
    python manage.py role you@kcl.ac.uk admin      # member | committee | admin
    python manage.py role them@kcl.ac.uk committee
    python manage.py reset-password them@kcl.ac.uk # prints a temporary password
    python manage.py delete them@kcl.ac.uk         # asks for confirmation
    python manage.py suspend them@kcl.ac.uk        # block sign-in, keep data
    python manage.py unsuspend them@kcl.ac.uk
    python manage.py newsletter --dry-run          # print this month's newsletters
    python manage.py newsletter                    # send them (monthly, via cron)
    python manage.py sync-events                   # import events from the FoLSM AI Portal now

On the VM with Docker:
    docker exec -it <container> python manage.py role you@kcl.ac.uk admin

The person must have registered first. The web equivalent is the Members page
(admins only).
"""
import argparse
import sys

from hub import create_app
from hub.accounts import reset_password, delete_user, is_last_admin, set_suspended
from hub.extensions import db
from hub.models import User, USER_ROLES


def cmd_list(args):
    query = User.query
    if not args.all:
        query = query.filter((User.is_admin.is_(True)) | (User.is_reviewer.is_(True)))
    users = query.order_by(User.is_admin.desc(), User.is_reviewer.desc(),
                           User.full_name).all()
    if not users:
        print("No one yet." if args.all else "No committee members or admins yet.")
    for u in users:
        flag = "  [suspended]" if u.is_suspended else ""
        print(f"{u.role:<10} {u.email:<35} {u.full_name}{flag}")


def _find(email):
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        sys.exit(f"No account for {email}.")
    return user


def cmd_reset_password(args):
    user = _find(args.email)
    temp = reset_password(user, args.password)
    print(f"Temporary password for {user.full_name} <{user.email}>: {temp}")
    print("They'll be asked to choose a new one when they sign in.")


def cmd_delete(args):
    user = _find(args.email)
    if is_last_admin(user):
        sys.exit(f"{user.email} is the only admin: make someone else admin first.")
    if not args.yes:
        answer = input(f"Permanently delete {user.full_name} <{user.email}>? Type 'delete': ")
        if answer.strip().lower() != "delete":
            sys.exit("Cancelled.")
    name = user.full_name
    delete_user(user)
    print(f"Deleted {name}.")


def cmd_suspend(args):
    user = _find(args.email)
    if args.cmd == "suspend" and is_last_admin(user):
        sys.exit(f"{user.email} is the only admin: make someone else admin first.")
    set_suspended(user, args.cmd == "suspend")
    print(f"{user.full_name} <{user.email}> is now "
          f"{'suspended' if user.is_suspended else 'active'}.")


def cmd_newsletter(args):
    import os
    from hub.newsletter import send_all
    result = send_all(force=args.force, only_email=args.to, dry_run=args.dry_run)
    verb = "Would send" if args.dry_run else "Sent"
    count = len(result["recipients"]) if args.dry_run else result["sent"]
    print(f"{verb} {count} newsletter(s); skipped {result['skipped_recent']} "
          f"sent recently, {result['nothing_to_send']} with nothing to send.")
    if not os.environ.get("SITE_URL"):
        print("Note: SITE_URL is not set, so links point to http://127.0.0.1:5000.")


def cmd_sync_events(args):
    from hub.event_sync import sync_all
    for name, result in sync_all().items():
        print(f"{name}: {result}")


def cmd_role(args):
    user = User.query.filter_by(email=args.email.strip().lower()).first()
    if not user:
        sys.exit(f"No account for {args.email}: they need to register first.")
    if user.is_admin and args.role != "admin" \
            and User.query.filter_by(is_admin=True).count() == 1:
        sys.exit(f"{user.email} is the only admin: make someone else admin first.")
    user.set_role(args.role)
    db.session.commit()
    print(f"{user.full_name} <{user.email}> is now {args.role}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list", help="show committee members and admins")
    p_list.add_argument("--all", action="store_true", help="include every member")
    p_role = sub.add_parser("role", help="set someone's role")
    p_role.add_argument("email")
    p_role.add_argument("role", choices=USER_ROLES)
    p_reset = sub.add_parser("reset-password", help="give someone a temporary password")
    p_reset.add_argument("email")
    p_reset.add_argument("--password", help="use this instead of a random one")
    p_del = sub.add_parser("delete", help="delete someone's profile")
    p_del.add_argument("email")
    p_del.add_argument("--yes", action="store_true", help="skip the confirmation")
    for name, text in (("suspend", "block someone from signing in (data kept)"),
                       ("unsuspend", "let a suspended person sign in again")):
        sub.add_parser(name, help=text).add_argument("email")
    p_news = sub.add_parser("newsletter", help="send the monthly newsletter")
    p_news.add_argument("--dry-run", action="store_true", help="print instead of sending")
    p_news.add_argument("--to", help="only this member (for testing)")
    p_news.add_argument("--force", action="store_true",
                        help="send even to people who got one in the last 25 days")
    args = parser.parse_args()

    sub.add_parser("sync-events", help="import events from the external calendars now")
    commands = {"sync-events": cmd_sync_events, "newsletter": cmd_newsletter, "list": cmd_list, "role": cmd_role,
                "reset-password": cmd_reset_password, "delete": cmd_delete,
                "suspend": cmd_suspend, "unsuspend": cmd_suspend}
    import os
    app = create_app()
    # A request context lets emails build full links to the site.
    with app.test_request_context(base_url=os.environ.get("SITE_URL") or "http://127.0.0.1:5000"):
        commands[args.cmd](args)


if __name__ == "__main__":
    main()
