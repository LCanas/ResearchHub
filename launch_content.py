"""Starter content for the live hub: launch and hackathon announcements.

No fake people — posts are authored by "Collaboration Hub team" (no author).
Dates come from LAUNCH / HACKATHON in hub/config.py, so update them there.

Run on its own (inside an app context) or via init_db.py:
    python launch_content.py
"""
from hub import create_app
from hub.config import LAUNCH, HACKATHON, CONTACT_EMAIL
from hub.extensions import db
from hub.models import NewsPost


def announcements():
    launch, hack = LAUNCH["when"], HACKATHON["when"]
    # Without a confirmed mailbox, point people at the hub itself.
    contact = (f"email {CONTACT_EMAIL}" if CONTACT_EMAIL
               else "get in touch with the hub team (contact details coming soon)")
    return [
        dict(
            title=f"The Collaboration Hub launches in {launch}",
            pinned=True,
            body=f"""We're delighted to announce that the Collaboration Hub for AI Deployment in Healthcare Research will officially launch in {launch}. The exact launch day is still to be confirmed, and we'll share the date, venue and programme here and by email as soon as they're fixed.

The hub is a matchmaking platform for King's researchers. It brings together people with clinical questions and people with AI expertise, and helps them turn ideas into collaborative, deployable projects.

What you can do now:
• Create your profile, adding your expertise, workstreams and availability, so collaborators can find you from day one.
• Propose a project, or submit a challenge for the {hack} hackathon.
• Read our Code of Conduct, which explains how teams agree IP, authorship and publications up front.

Launch day will include an introduction to the hub and its review panel, short talks from researchers deploying AI in healthcare, a showcase of the first hackathon challenges, and time to meet potential collaborators.

Questions, or ideas for the launch? Please {contact}.""",
        ),
        dict(
            title=f"Hackathon {hack}: challenge submissions are open",
            pinned=True,
            body=f"""Our first {HACKATHON['name']} will take place in {hack}. Exact dates and venue are to be confirmed. We're now inviting challenges: real clinical or research problems that a small team could make progress on in a few days.

How to submit:
1. Create your profile (or sign in).
2. Go to "Propose a project" and choose the type "Hackathon".
3. Describe the problem, the data that could be used (open, synthetic or already approved; never upload patient data to the hub) and what a useful result would look like.
4. Fill in the collaboration agreement covering IP, code licence, authorship and how publications will be approved.

Every submission stays on hold until the committee has checked it against the panel criteria (clinical impact, data readiness, resources and AI feasibility). The committee may approve it, ask for changes or decline it, and you'll be emailed the decision, with any note from the committee. Approved challenges are listed on the Hackathon page for participants to join.

The closing date for submissions will be announced soon. Submitting early gives you time to refine your challenge with the committee's feedback.""",
        ),
        dict(
            title="Introducing our Code of Conduct: agree before you start",
            body="""Good collaborations start with clear expectations. Every hub member agrees to our Code of Conduct, which is built around two principles:

• Agree a priori. Before work starts, both parties agree how intellectual property, software licences, data use and authorship will be handled. Each project records this on its page, and collaborators accept it when they ask to join.
• Approve together. Publications, presentations, code releases and other outcomes need the written approval of both parties before they are shared.

The Code works alongside King's College London policies and formal agreements, not instead of them. You can read it in full from the link in the site footer.""",
        ),
        dict(
            title="Create your profile: help us map AI expertise across the Faculty",
            body="""The hub works best when it knows who's out there. Whether you're a clinician with a question, a PhD student with machine-learning skills or a PI looking for a team, create your profile and tell us:
• your expertise and keywords
• the research workstreams that interest you
• your availability (hours per week), and whether you'd be open to leading a project as a PI

Profiles are only visible to signed-in members of the hub.""",
        ),
        dict(
            title="Call for seminar speakers, trainers and data club hosts",
            body=f"""We're building the events programme for the hub's launch in {launch} and beyond. Get in touch if you'd like to:
• give a short seminar on deploying AI in healthcare, including what didn't work
• host a data club introducing a dataset that others could use
• run a training session, e.g. LLMs for clinical text, federated learning, model evaluation, or information governance for AI projects

To offer a session, fill in the Call for speakers form on the hub (link in the site footer). It only takes a few minutes, and you don't need an account.""",
        ),
    ]


def seed_launch_content():
    """Add the starter announcements if there are no announcements yet.
    Call inside an app context."""
    if NewsPost.query.count():
        return 0
    posts = announcements()
    for p in posts:
        db.session.add(NewsPost(**p))
    db.session.commit()
    return len(posts)


if __name__ == "__main__":
    with create_app().app_context():
        n = seed_launch_content()
        print(f"Added {n} announcements." if n else "Announcements already exist — nothing added.")
