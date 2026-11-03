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

# 2. Create the database with the launch announcements (no demo people)
python init_db.py
#    …or, for a demo with the fictional researchers below:  python seed.py

# 3. Start the app
python run.py
```

Then open <http://127.0.0.1:5000>.

### Roles, review and public pages

- **Researchers create their own profiles** and must agree to the Code of Conduct
  (`/code-of-conduct`) when they register.
- **Roles:** *member* (default), *committee* (reviews submissions, posts
  announcements) and *admin* (also manages roles on the **Members** page).
  Every new project or hackathon challenge is **on hold** until the committee
  approves it; committee members can't approve their own.
  - Bootstrap the first admin with `HUB_ADMIN_EMAILS=you@kcl.ac.uk` (applied when
    that person registers or signs in), or from the server:
    `python manage.py role you@kcl.ac.uk admin` (with Docker:
    `docker exec -it <container> python manage.py role …`).
    `python manage.py list` shows who has which role.
  - Admins can also **reset passwords** (a temporary password the person must
    change at next sign-in), **suspend** (block sign-in, keep data) and
    **delete profiles**, on the Members page or with `python manage.py
    reset-password | suspend | unsuspend | delete EMAIL`.
- **Forgot password:** the sign-in page emails a one-time reset link that
  expires after an hour. This needs email (SMTP) configured to reach people.
- **Monthly newsletter:** each member gets open projects matched to their
  profile keywords and workstreams, plus upcoming events, recent news and the
  hackathon. Members opt out on their profile or via the link in the email.
  Admins can preview and send it from **Newsletter** in the account menu. To send
  it automatically on the 1st of each month at 09:00, add a cron job on the
  server (`crontab -e`):

  ```
  0 9 1 * * cd /path/to/ResearchNetwork && docker compose exec -T web python manage.py newsletter >> /var/log/hub-newsletter.log 2>&1
  ```
  `python manage.py newsletter --dry-run` prints them without sending. Nobody
  is sent two within 25 days, so a repeated run never double-sends.
- **Email notifications:** proposer and PI when someone asks to join; the
  committee when something is submitted; the proposer when it's reviewed.
  Configure SMTP with `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`,
  `MAIL_PASSWORD`, `MAIL_FROM` and `SITE_URL` (see `hub/mail.py`). Without
  `MAIL_SERVER` the emails are printed to the log instead of sent.
- **Public pages** (no sign-in): home, about, review panel, workstreams, news,
  events, impact, hackathon and Code of Conduct. Projects, people and profiles
  need an account.
- Launch and hackathon dates live in `LAUNCH` / `HACKATHON` in `hub/config.py`.

## Deploying with Docker + PostgreSQL (the VM)

`docker-compose.yml` runs two containers: **web** (the hub, gunicorn) and **db**
(PostgreSQL 16). Data is kept in Docker volumes (`pgdata` for the database,
`uploads` for profile photos), so it survives rebuilds and restarts.

```bash
# 1. Settings: copy the template and fill in SECRET_KEY, POSTGRES_PASSWORD, SITE_URL
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # run twice, one per secret

# 2. Build and start (the database tables are created on first boot)
docker compose up -d --build
docker compose logs -f web          # watch it start; Ctrl+C to stop watching

# 3. Admin commands run inside the web container
docker compose exec web python manage.py list --all
```

**Updating to a new version of the code:** `git pull && docker compose up -d --build`.
The data is untouched; new database columns are added automatically on boot.

**Moving an existing SQLite `hub.db` into Postgres** (once, on an empty hub):
```bash
docker compose cp hub.db web:/tmp/hub.db
docker compose exec web python migrate_sqlite_to_postgres.py /tmp/hub.db
```

**Backups:** dump the database to a file, e.g. nightly via cron:
```bash
docker compose exec -T db pg_dump -U hub hub > backup_$(date +%F).sql
# restore into an empty database:
docker compose exec -T db psql -U hub hub < backup_2027-01-15.sql
```
Keep copies off the VM. `docker compose down` stops the hub but keeps the
data; **`docker compose down -v` deletes the volumes, and with them all data.**

## Deploying online (Azure)

See **[DEPLOY_AZURE.md](DEPLOY_AZURE.md)** for a step-by-step guide to hosting the
app on Azure App Service (via the Azure CLI or the VS Code extension), so it can
be shared with a presenter on a public `https://…azurewebsites.net` URL. The app
is production-ready — `wsgi.py` (gunicorn entry), `init_db.py` (auto-seeds an
empty database), a `Dockerfile`, and env-based `SECRET_KEY` / `DATABASE_URL`.

### Demo accounts (only with `python seed.py` or `SEED_DEMO=1`)

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
