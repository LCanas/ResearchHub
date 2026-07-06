"""Application configuration and shared constants."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-kcl-hub")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hub.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Uploaded profile photos land here.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "hub", "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB profile photos
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


# ---------------------------------------------------------------------------
# Controlled vocabularies used across forms, filters and templates.
# ---------------------------------------------------------------------------

# Project lifecycle stages (requirement 10). Order matters — it drives the
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
     "desc": "A focused sprint — days to a couple of weeks — to prototype an "
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
# Research workstreams / themes — the top-level way projects and people are
# organised (mirrors how KCL research hubs structure their work).
# ---------------------------------------------------------------------------
WORKSTREAMS = [
    {"slug": "clinical-nlp", "name": "Clinical NLP & Language Models",
     "icon": "💬", "css": "ws-1",
     "desc": "Applying large language models and natural-language processing to "
             "clinical text — documentation, coding, summarisation and "
             "information extraction."},
    {"slug": "medical-imaging", "name": "Medical Imaging AI",
     "icon": "🩻", "css": "ws-2",
     "desc": "Computer vision for radiology, pathology and other imaging — "
             "detection, triage, segmentation and quantification."},
    {"slug": "predictive-risk", "name": "Predictive Modelling & Risk",
     "icon": "📈", "css": "ws-3",
     "desc": "Risk prediction and early-warning models from structured clinical "
             "data, with a focus on calibration, fairness and clinical utility."},
    {"slug": "federated-privacy", "name": "Federated & Privacy-Preserving ML",
     "icon": "🔐", "css": "ws-4",
     "desc": "Training models across sites without moving patient data — "
             "federated learning, privacy, and secure computation."},
    {"slug": "governance-safety", "name": "AI Governance & Safety",
     "icon": "⚖️", "css": "ws-5",
     "desc": "Evaluation, equity and fairness auditing, safety and the "
             "governance needed to deploy AI responsibly in healthcare."},
    {"slug": "deployment-mlops", "name": "Deployment & MLOps",
     "icon": "🚀", "css": "ws-6",
     "desc": "Integrating models into clinical workflows and building the "
             "infrastructure and monitoring that keep them running safely."},
    {"slug": "human-centred", "name": "Human-Centred AI",
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

DEPARTMENTS = [
    "Biomedical Engineering & Imaging Sciences",
    "Informatics",
    "School of Cardiovascular & Metabolic Medicine",
    "Population Health Sciences",
    "Cancer & Pharmaceutical Sciences",
    "Neuroscience",
    "Nursing, Midwifery & Palliative Care",
    "Life Sciences & Medicine",
    "Other",
]

# External KCL department pages, linked from the About page.
DEPARTMENT_KCL_URLS = {
    "Biomedical Engineering & Imaging Sciences": "https://www.kcl.ac.uk/bmeis",
    "Informatics": "https://www.kcl.ac.uk/informatics",
    "School of Cardiovascular & Metabolic Medicine":
        "https://www.kcl.ac.uk/cardiovascular-metabolic-medicine-sciences",
    "Population Health Sciences": "https://www.kcl.ac.uk/population-health",
    "Cancer & Pharmaceutical Sciences":
        "https://www.kcl.ac.uk/cancer-pharmaceutical-sciences",
    "Neuroscience": "https://www.kcl.ac.uk/ioppn",
    "Nursing, Midwifery & Palliative Care": "https://www.kcl.ac.uk/nmpc",
    "Life Sciences & Medicine": "https://www.kcl.ac.uk/lsm",
    "Other": "https://www.kcl.ac.uk",
}

# The multidisciplinary review panel (from the project brief). It meets monthly
# to evaluate proposals on clinical impact, data readiness, resources and AI
# feasibility. Names below are illustrative demo members.
PANEL_MEMBERS = [
    {"role": "Panel Chair", "name": "Prof. Sheldon Cooper",
     "affiliation": "Biomedical Engineering & Imaging Sciences",
     "desc": "Chairs the monthly panel, sets priorities and has the final say "
             "on whether a proposal enters the pipeline."},
    {"role": "Clinical Lead", "name": "Dr Bernadette Rostenkowski-Wolowitz",
     "affiliation": "Cancer & Pharmaceutical Sciences",
     "desc": "Ensures each project answers a genuine clinical need and assesses "
             "clinical impact and data readiness."},
    {"role": "Technical / AI Lead", "name": "Dr Leonard Hofstadter",
     "affiliation": "Biomedical Engineering & Imaging Sciences",
     "desc": "Reviews the AI approach and engineering feasibility, and helps "
             "match projects to the right technical collaborators."},
    {"role": "Governance & IG Lead", "name": "Dr Amy Farrah Fowler",
     "affiliation": "Neuroscience",
     "desc": "Owns information governance, ethics and data-protection sign-off "
             "before a project can launch."},
    {"role": "PI Representative", "name": "Dr Rajesh Koothrappali",
     "affiliation": "Informatics",
     "desc": "Represents Principal Investigators, helping connect proposals with "
             "senior researchers willing to coordinate them."},
    {"role": "Panel Coordinator", "name": "Stuart Bloom",
     "affiliation": "Research Support",
     "desc": "Keeps the pipeline moving — contacts proposers, schedules launch "
             "meetings and tracks the backlog."},
]

# What the panel weighs up when reviewing a submission (from the brief).
REVIEW_CRITERIA = [
    ("Clinical impact", "Does the project address a real, valuable clinical or "
                        "research need?"),
    ("Data readiness", "Is suitable, well-governed data available and usable?"),
    ("Resources needed", "What people, compute and time would the project take?"),
    ("AI feasibility", "Is the proposed AI approach technically realistic?"),
]
