# Collaboration Hub for AI Deployment in Healthcare Research

A web database for King's College London to coordinate researchers and projects
working on the deployment of AI in healthcare. Researchers create profiles,
browse projects, request to join them, and track roadmaps, contributions and
outcomes across a defined project lifecycle.

Built with **Python / Flask**, **SQLAlchemy** (SQLite) and server-rendered
**Jinja** templates, styled in a modern KCL palette (crimson, navy, greys and
white, with round profile photos).

## Features

| # | Requirement | Where |
|---|-------------|-------|
| 1 | User profiles assigned to projects | `Collaboration` link model |
| 2 | Log in, browse projects, send join requests | `auth.py`, `project_join` |
| 3 | Project pages with status + members | `project_detail.html` |
| 4 | Profiles show projects, hours/days, status | `profile.html` |
| 5 | Expertise, keywords, bio, seniority, contract, links, department, PI | `User` model, `edit_profile.html` |
| 6 | Project status, title, roadmap/Gantt, outcomes, GitHub, collaborators, PI | `project_detail.html` |
| 7 | Status labels; completed projects show outcomes, not expected outcomes | `project_detail.html` |
| 8 | Directory: contact, status, availability filter, skills, department, line manager, role | `directory.html` |
| 9 | Named "Collaboration Hub for AI Deployment in Healthcare Research" | throughout |
| 10 | Lifecycle: Open → Waiting for PI → Launched → Ongoing → Completed | `config.py` `PROJECT_STAGES` |

## Pages

- **Home** (`/`) – landing page with the hub banner, quick links, latest news and
  upcoming events.
- **Projects** (`/projects`) – browse/filter all projects (by stage, **type**, **workstream**, department, search).
- **Workstreams** – the research themes that organise all work; each has a page
  listing its projects and researchers. Projects belong to one workstream;
  people can belong to several.
- **People** – researcher directory with availability/skill/role/workstream filters.
- **Events** – seminars, training, data clubs and workshops (upcoming + past),
  with one-click **sign-up** and attendee lists.
- **News** – hub announcements/updates (pinnable), surfaced on the home page.
- **Impact** – showcase of completed projects and the outcomes they delivered.
- **About** – mission, how the hub works (4-step model), research workstreams,
  project types, and departments (each linking to its collaborators and KCL page).
- **Review panel** (`/panel`) – the monthly multidisciplinary panel: review
  criteria and named members.
- **Requests** – your outgoing join requests and incoming ones for projects you manage.

## Project types (effort bands)

Projects are tagged with a type so people can contribute at the scale that fits:

- **Hackathon** — *short-term*, days to weeks.
- **Proof of Concept** / **Product Development** — *medium-term*, months.
- **Grant** — *long-term*, funded programme.

## Project lifecycle stages

- **Open** – Seeking collaborators and PIs; researchers express interest to join.
- **Waiting for PI** – Backlogged for lack of a senior lead; reopens only if a
  senior researcher shows interest.
- **Launched** – Joining is closed; kick-off scheduled and the project starts.
- **Ongoing** – Managed by the PI and proposer without panel oversight.
- **Completed** – Agreed period ended; the PI reports outcomes, shared on the platform.

## Running locally

The project uses the **`researchHub`** conda environment.

```bash
# 1. Activate the environment and install dependencies
conda activate researchHub
pip install -r requirements.txt

# 2. Create and populate the database with demo data
python seed.py

# 3. Start the app
python run.py
```

Then open <http://127.0.0.1:5000>.

## Deploying online (Azure)

See **[DEPLOY_AZURE.md](DEPLOY_AZURE.md)** for a step-by-step guide to hosting the
app on Azure App Service (via the Azure CLI or the VS Code extension), so it can
be shared with a presenter on a public `https://…azurewebsites.net` URL. The app
is production-ready — `wsgi.py` (gunicorn entry), `init_db.py` (auto-seeds an
empty database), a `Dockerfile`, and env-based `SECRET_KEY` / `DATABASE_URL`.

### Demo accounts

The demo researchers are cast from *The Big Bang Theory*, mapped to roles that
fit each character's canonical status. All share the password **`password123`**.

| Email | Character / role |
|-------|------------------|
| `s.cooper@kcl.ac.uk` | Sheldon Cooper — Professor, admin / PI (imaging) |
| `a.fowler@kcl.ac.uk` | Amy Farrah Fowler — neuroscientist, PI |
| `l.hofstadter@kcl.ac.uk` | Leonard Hofstadter — Senior Lecturer, PI |
| `h.wolowitz@kcl.ac.uk` | Howard Wolowitz — engineer (no PhD), collaborator |
| `b.rostenkowski@kcl.ac.uk` | Bernadette — microbiologist / pharma, PI |
| `p.hofstadter@kcl.ac.uk` | Penny — pharma liaison, collaborator |
| `s.bloom@kcl.ac.uk` | Stuart Bloom — ever-available research assistant |

New users can also register from the sign-in page.

## Project structure

```
ResearchNetwork/
├── run.py                 # entry point
├── seed.py                # demo data
├── requirements.txt
└── hub/
    ├── __init__.py        # app factory
    ├── config.py          # settings + controlled vocabularies (stages, etc.)
    ├── extensions.py      # db + login manager
    ├── models.py          # User, Project, Milestone, Collaboration, JoinRequest
    ├── auth.py            # register / login / logout
    ├── main.py            # projects, profiles, directory, join flow
    ├── static/            # style.css (KCL theme), main.js, uploaded photos
    └── templates/         # Jinja templates
```

## Notes

- The Gantt/roadmap chart is rendered in pure CSS from each project's
  milestones — no external libraries, works fully offline.
- Profile photos are uploaded to `hub/static/uploads/` and displayed as round
  avatars; users without a photo get an initials avatar.
- Permissions: a project's **proposer**, its **PI**, or an **admin** can edit it,
  manage milestones, and accept/decline join requests.
- `SECRET_KEY` and `DATABASE_URL` can be overridden via environment variables
  for a production deployment (use a real WSGI server, not the dev server).
