"""Application configuration and shared constants."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hub.db"))
    # Render / Heroku hand out postgres:// URLs; SQLAlchemy wants the driver named.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    # An empty SECRET_KEY (e.g. a blank line in .env) counts as unset.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-me-in-production-kcl-hub"
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Uploaded profile photos land here.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "hub", "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB profile photos
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


# ---------------------------------------------------------------------------
# Launch & hackathon. Exact dates are still to be confirmed: update these
# labels once they are fixed and they change everywhere on the site.
# ---------------------------------------------------------------------------
# Dates are YYYY-MM-DD; leave "" while unknown. On the hackathon page's timeline
# a step turns red once its date has passed (or, with only a month known, once
# that month is over); steps without a date stay grey.
LAUNCH = {
    "when": "January 2027",
    "date_confirmed": False,
    "month_start": "2027-01-01",
    "date": "",                       # exact launch day, once fixed
    "venue": "",                      # e.g. "Guy's Campus, London"; "" shows "to be announced"
}

# The Launch Day page (/launch). The programme is to be announced: while this
# list is empty the page says so. Once it's fixed, add sessions as
#   ("09:30", "Registration & coffee", "Short description"),
LAUNCH_PROGRAMME = []

# Who is registering for launch day (registration form).
ATTENDEE_TYPES = ["Clinician", "Researcher / academic", "PhD student", "Postdoc",
                  "Data scientist / engineer", "NHS staff", "Industry", "Other"]

# Hackathon registration: how people want to take part.
HACKATHON_ROLES = ["Participant (join a team)", "Challenge owner", "Mentor / expert",
                   "Not sure yet"]

# Pages a news post can link to (news form), as (label, endpoint).
NEWS_LINK_PAGES = [
    ("Launch day", "main.launch"),
    ("Register for launch day", "main.launch_register"),
    ("Hackathon", "main.hackathon"),
    ("Call for speakers", "main.call_for_speakers"),
    ("Code of Conduct", "main.code_of_conduct"),
    ("Create your profile", "auth.register"),
    ("Projects", "main.projects"),
    ("Events", "main.events"),
    ("Workstreams", "main.workstreams"),
]

# Confirmed speakers, shown on the launch page. Add them as they confirm:
#   {"name": "...", "role": "...", "affiliation": "...", "talk": "..."}
LAUNCH_SPEAKERS = []

# Session formats offered on the call-for-speakers form.
SPEAKER_SESSION_TYPES = ["Keynote", "Talk (15–20 min)", "Lightning talk (5 min)",
                         "Panel discussion", "Demo", "Poster", "Workshop / training"]
SPEAKER_PROPOSAL_STATUSES = ["New", "Shortlisted", "Accepted", "Declined"]

HACKATHON = {
    "name": "AI in Healthcare Hackathon",
    "when": "May 2027",
    "submissions_open": "2026-11-02",
    "submissions_close": "to be confirmed",
    "submissions_close_date": "",     # e.g. "2027-03-31"
    # Countdown on the hackathon page. Until the exact start is known it counts
    # (approximately) to the first of the month; set "start" to e.g.
    # "2027-05-12T09:00" for a live days/hours/minutes countdown.
    "month_start": "2027-05-01",
    "start": "",
    "end": "",                        # last day of the hackathon, e.g. "2027-05-14"
    # Participant registration. While empty (or in the future) the "Register to
    # take part" button is shown greyed out; from this date it opens.
    "registration_opens": "",         # e.g. "2027-02-01"
}

# Home-page hero illustration: "network" (original), "match" (clinicians ×
# AI experts pairing up) or "live" (workstream graph built from real sign-ups).
# Preview any of them with /?hero=match etc.
HERO_ART = "network"

# External event calendars imported into the Events page and kept in sync.
# Each must be a WordPress site running "The Events Calendar" plugin (it
# publishes events at /wp-json/tribe/events/v1/events).
EVENT_FEEDS = [
    {"key": "folsm-ai-portal", "name": "FoLSM AI Portal",
     "url": "https://folsmaiportal.sites.er.kcl.ac.uk",
     "events_page": "https://folsmaiportal.sites.er.kcl.ac.uk/events/"},
]
EVENT_SYNC_MINUTES = 60      # refresh at most this often while people browse
EVENT_SYNC_PAST_DAYS = 180   # also import recent past events

# The "Learn" page: guides and resources on the FoLSM AI Portal. Links go
# straight to the portal; edit titles, text or links here.
_P = "https://folsmaiportal.sites.er.kcl.ac.uk"
PORTAL = {"name": "FoLSM AI Portal", "url": _P + "/",
          "tagline": "A space for everyone in the Faculty to learn about AI and how to use it responsibly."}
PORTAL_RESOURCES = [
    {"key": "education", "title": "AI in Education",
     "desc": "A curated guide to the research literature on how AI is reshaping teaching, "
             "learning and assessment in higher education.",
     "url": _P + "/ai-in-education/",
     "items": [
         ("Policy and sector overview", _P + "/policy-and-sector-overview/"),
         ("Assessment and academic integrity", _P + "/assessment-and-academic-integrity/"),
         ("Feedback and evaluation", _P + "/feedback-and-evaluation/"),
         ("Knowledge, judgement and learning", _P + "/knowledge-judgement-and-learning/"),
         ("Health professions and medical education", _P + "/health-professions-and-medical-education/"),
         ("Ethics, relationships and academic writing", _P + "/ethics-relationships-and-academic-writing/"),
         ("Data, analytics and research", _P + "/data-analytics-and-research/"),
         ("Conclusions and getting involved", _P + "/conclusions-and-getting-involved/"),
     ]},
    {"key": "reviews", "title": "AI for systematic reviews",
     "desc": "Where AI tools can help at each stage of evidence synthesis, where they can't, "
             "and how to use them responsibly.",
     "url": _P + "/the-review-process/",
     "items": [
         ("The systematic review process", _P + "/the-review-process/"),
         ("Question formulation and search strategy", _P + "/question-formulation-and-the-search-strategy/"),
         ("Screening papers", _P + "/screening-papers/"),
         ("Data extraction", _P + "/data-extraction/"),
         ("Quality assessment", _P + "/quality-assessment/"),
         ("Synthesis", _P + "/synthesis/"),
         ("Responsible AI use", _P + "/responsible-ai-use/"),
     ]},
    {"key": "skills", "title": "Skills: the Prompt Library",
     "desc": "The FoLSM AI Prompt Library: a shared collection of ready-to-use prompts for "
             "everyday research, teaching and admin tasks.",
     "url": _P + "/skills/", "items": []},
]

CODE_OF_CONDUCT_VERSION = "1.0"

# Always admin, on any machine, once they register / sign in. More admins and
# committee members can be added from the Members page, manage.py, or the
# HUB_ADMIN_EMAILS / HUB_COMMITTEE_EMAILS environment variables.
DEFAULT_ADMIN_EMAILS = ["k1778298@kcl.ac.uk"]

# Contact & social links. Leave a value empty to hide it on the site: fill
# these in once the mailbox / pages actually exist.
CONTACT_EMAIL = "k1778298@kcl.ac.uk"  # for now; swap for a shared hub mailbox when there is one
SOCIAL_LINKS = {
    "LinkedIn": "",
    "GitHub": "",           # e.g. the hub's GitHub organisation / repo
    "X": "",
}

# ---------------------------------------------------------------------------
# Controlled vocabularies used across forms, filters and templates.
# ---------------------------------------------------------------------------

# Review of submitted projects before they go live on the hub.
REVIEW_STATUSES = ["Pending review", "Approved", "Changes requested", "Declined"]
REVIEW_STATUS_CSS = {
    "Pending review": "stage-waiting",
    "Approved": "stage-ongoing",
    "Changes requested": "stage-launched",
    "Declined": "stage-completed",
}

# Project lifecycle stages (requirement 10). Order matters: it drives the
# timeline widget and status ordering.
PROJECT_STAGES = [
    ("Open", "The project is seeking collaborators and PIs. Researchers are "
             "invited to express their interest in joining."),
    ("Waiting for PI", "Moved to the backlog due to a lack of interest from "
                        "senior researchers to coordinate. It reopens only if "
                        "a senior researcher shows interest."),
    ("Launched", "Joining is closed. An initial meeting with the proposers is "
                 "scheduled and the project is launched and expected to start."),
    ("Ongoing", "Actively managed by the PI and proposer without panel "
                "oversight. All collaborators are expected to be contributing."),
    ("Completed", "The agreed period has ended. The PI updates the panel on "
                  "progress and outcomes, which are shared on the platform."),
]
STAGE_NAMES = [s[0] for s in PROJECT_STAGES]
STAGE_DESCRIPTIONS = dict(PROJECT_STAGES)

# A CSS accent class per stage, wired up in style.css.
STAGE_CSS = {
    "Open": "stage-open",
    "Waiting for PI": "stage-waiting",
    "Launched": "stage-launched",
    "Ongoing": "stage-ongoing",
    "Completed": "stage-completed",
}

# Project types grouped by the effort/time band they represent (requirement 4).
PROJECT_TYPES = [
    {"name": "Hackathon", "band": "Short-term", "css": "type-hackathon",
     "icon": "⚡",
     "desc": "A focused sprint (days to a couple of weeks) to prototype an "
             "idea, test a dataset or explore a question at pace."},
    {"name": "Proof of Concept", "band": "Medium-term", "css": "type-poc",
     "icon": "🧪",
     "desc": "A few months to validate technical and clinical feasibility "
             "before committing to a larger build."},
    {"name": "Product Development", "band": "Medium-term", "css": "type-product",
     "icon": "🛠️",
     "desc": "Building and hardening a deployable tool or product for real "
             "clinical or research use."},
    {"name": "Grant", "band": "Long-term", "css": "type-grant",
     "icon": "🎓",
     "desc": "A funded, long-term research programme with formal milestones, "
             "outputs and reporting."},
]
PROJECT_TYPE_NAMES = [t["name"] for t in PROJECT_TYPES]
PROJECT_TYPE_CSS = {t["name"]: t["css"] for t in PROJECT_TYPES}
PROJECT_TYPE_BAND = {t["name"]: t["band"] for t in PROJECT_TYPES}

# ---------------------------------------------------------------------------
# Research workstreams / themes: the top-level way projects and people are
# organised (mirrors how KCL research hubs structure their work).
# ---------------------------------------------------------------------------
WORKSTREAMS = [
    {"slug": "clinical-nlp", "short": "Clinical NLP", "name": "Clinical NLP & Language Models",
     "icon": "💬", "css": "ws-1",
     "desc": "Applying large language models and natural-language processing to "
             "clinical text: documentation, coding, summarisation and "
             "information extraction."},
    {"slug": "medical-imaging", "short": "Imaging", "name": "Medical Imaging AI",
     "icon": "🩻", "css": "ws-2",
     "desc": "Computer vision for radiology, pathology and other imaging: "
             "detection, triage, segmentation and quantification."},
    {"slug": "predictive-risk", "short": "Risk models", "name": "Predictive Modelling & Risk",
     "icon": "📈", "css": "ws-3",
     "desc": "Risk prediction and early-warning models from structured clinical "
             "data, with a focus on calibration, fairness and clinical utility."},
    {"slug": "federated-privacy", "short": "Federated ML", "name": "Federated & Privacy-Preserving ML",
     "icon": "🔐", "css": "ws-4",
     "desc": "Training models across sites without moving patient data: "
             "federated learning, privacy, and secure computation."},
    {"slug": "governance-safety", "short": "Governance", "name": "AI Governance & Safety",
     "icon": "⚖️", "css": "ws-5",
     "desc": "Evaluation, equity and fairness auditing, safety and the "
             "governance needed to deploy AI responsibly in healthcare."},
    {"slug": "deployment-mlops", "short": "MLOps", "name": "Deployment & MLOps",
     "icon": "🚀", "css": "ws-6",
     "desc": "Integrating models into clinical workflows and building the "
             "infrastructure and monitoring that keep them running safely."},
    {"slug": "human-centred", "short": "Human-centred", "name": "Human-Centred AI",
     "icon": "🧑‍⚕️", "css": "ws-7",
     "desc": "Explainability, human factors and communicating AI-assisted "
             "decisions to clinicians and patients."},
]
WORKSTREAM_NAMES = [w["name"] for w in WORKSTREAMS]
WORKSTREAM_BY_SLUG = {w["slug"]: w for w in WORKSTREAMS}
WORKSTREAM_BY_NAME = {w["name"]: w for w in WORKSTREAMS}
# name -> slug and name -> css, handy in templates
WORKSTREAM_SLUG = {w["name"]: w["slug"] for w in WORKSTREAMS}
WORKSTREAM_CSS = {w["name"]: w["css"] for w in WORKSTREAMS}

CONTRACT_TYPES = [
    "Research Assistant",
    "PhD Student",
    "Postdoctoral Researcher",
    "Research Fellow",
    "Academic / Lecturer",
    "Senior Lecturer",
    "Professor",
    "Clinician",
    "Data Scientist",
    "Software Engineer",
    "Other",
]

SENIORITY_LEVELS = [
    "Junior",
    "Intermediate",
    "Senior",
    "Principal",
]

WORK_STATUSES = ["Active", "Keen", "Busy", "Unavailable"]

DB_ROLES = ["Collaborator", "PI"]

MILESTONE_STATUSES = ["Planned", "In Progress", "Done"]

# Event categories for the engagement calendar.
EVENT_TYPES = [
    "Seminar",
    "Training",
    "Data Club",
    "Workshop",
    "Journal Club",
    "Other",
]
EVENT_TYPE_ICONS = {
    "Seminar": "🎤",
    "Training": "🎓",
    "Data Club": "📊",
    "Workshop": "🛠️",
    "Journal Club": "📚",
    "Other": "📅",
}

# King's schools: chosen from this list on profiles and projects, and used for
# filtering. A person's department within their school is free text.
SCHOOLS = ["Basic & Medical Biosciences",
           "Biomedical Engineering & Imaging Sciences",
           "Cancer & Pharmaceutical Sciences",
           "Cardiovascular and Metabolic Medicine & Sciences",
           "Immunology & Microbial Sciences",
           "Life Course & Population Health Sciences",
           "Other",
]

# Earlier "department" values that were really schools, moved into the school
# field when an existing database is upgraded (see init_db.py).
LEGACY_SCHOOL_NAMES = {
    "School of Cardiovascular & Metabolic Medicine":
        "Cardiovascular and Metabolic Medicine & Sciences",
    "Population Health Sciences": "Life Course & Population Health Sciences",
}

# External KCL school pages, linked from the About page.
SCHOOL_KCL_URLS = {
    "Biomedical Engineering & Imaging Sciences": "https://www.kcl.ac.uk/bmeis",
    "Basic & Medical Biosciences": "https://www.kcl.ac.uk/bmb",
    "Cardiovascular and Metabolic Medicine & Sciences":
        "https://www.kcl.ac.uk/scmms",
    "Immunology & Microbial Sciences": "https://www.kcl.ac.uk/sims",
    "Life Course & Population Health Sciences": "https://www.kcl.ac.uk/slcps",
    "Cancer & Pharmaceutical Sciences":
        "https://www.kcl.ac.uk/scps",
    "Other": "https://www.kcl.ac.uk",
}

# The multidisciplinary review panel (from the project brief). It meets monthly
# to evaluate proposals on clinical impact, data readiness, resources and AI
# feasibility. Fill in "name" / "affiliation" once members are confirmed: the
# page shows "To be announced" until then.
PANEL_MEMBERS = [
    {"role": "Panel Chair", "name": "", "affiliation": "",
     "desc": "Chairs the monthly panel, sets priorities and has the final say "
             "on whether a proposal enters the Hub."},
    {"role": "Clinical Chair", "name": "", "affiliation": "",
     "desc": "Ensures each project answers a genuine clinical need and assesses "
             "clinical impact and data readiness."},
    {"role": "Technical / AI Chair", "name": "", "affiliation": "",
     "desc": "Reviews the AI approach and engineering feasibility, and helps "
             "match projects to the right technical collaborators."},
    {"role": "Governance & IG Chair", "name": "", "affiliation": "",
     "desc": "Owns information governance, ethics and data-protection sign-off "
             "before a project can launch."},
    {"role": "PI Representative", "name": "", "affiliation": "",
     "desc": "Represents Principal Investigators, helping connect proposals with "
             "senior researchers willing to coordinate them."},
    {"role": "ECR Representative", "name": "", "affiliation": "",
     "desc": "Represents Early Career Researchers, ensuring their perspectives "
     "are considered in the review process."},
]

# What the panel weighs up when reviewing a submission (from the brief).
REVIEW_CRITERIA = [
    ("Clinical impact", "Does the project address a real, valuable clinical or "
                        "research need?"),
    ("Data readiness", "Is suitable, well-governed data available and usable?"),
    ("Resources needed", "What people, compute and time would the project take?"),
    ("AI feasibility", "Is the proposed AI approach technically realistic?"),
]
