"""Populate the database with demo data — cast by The Big Bang Theory.

The researchers are BBT characters, mapped to roles that fit their canonical
"status" (Sheldon the professor, Amy the neuroscientist, Howard the no-PhD
engineer, Penny in pharma sales, Stuart the ever-available assistant...). Every
project is still about deploying AI in healthcare.

Run once:   python seed.py
All demo accounts use the password:  password123
Log in with, e.g.,  s.cooper@kcl.ac.uk / password123
"""
from datetime import date, datetime, timedelta

from hub import create_app
from hub.extensions import db
from hub.models import (
    User, Project, Milestone, Collaboration, JoinRequest,
    NewsPost, Event, EventAttendance,
)


def make_user(**kw):
    pw = kw.pop("password", "password123")
    u = User(**kw)
    u.set_password(pw)
    db.session.add(u)
    return u


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---------------- Users (the BBT cast) ----------------
        sheldon = make_user(
            full_name="Sheldon Cooper", email="s.cooper@kcl.ac.uk", is_admin=True,
            expertise="Theoretical foundations of medical imaging AI",
            bio="Theoretical physicist applying first-principles modelling to "
                "medical imaging. Leads the imaging AI group and is quite certain "
                "his approach is optimal.",
            keywords="medical imaging, foundation models, physics, deep learning",
            seniority="Principal", contract_type="Professor",
            department="Biomedical Engineering & Imaging Sciences",
            work_status="Busy", hours_available=4, db_role="PI",
            workstreams="Medical Imaging AI|Deployment & MLOps",
            kcl_url="https://kcl.ac.uk/people/sheldon-cooper", phone="+44 20 7848 0001",
        )
        amy = make_user(
            full_name="Amy Farrah Fowler", email="a.fowler@kcl.ac.uk",
            expertise="Computational neuroscience & human-centred clinical AI",
            bio="Neuroscientist studying how clinicians and patients interact with "
                "AI-assisted decisions, with a focus on trust, safety and equity.",
            keywords="neuroscience, human factors, explainability, evaluation",
            seniority="Senior", contract_type="Academic / Lecturer",
            department="Neuroscience", work_status="Active", hours_available=10,
            db_role="PI", workstreams="Human-Centred AI|AI Governance & Safety",
            linkedin_url="https://linkedin.com/in/amy-farrah-fowler",
            kcl_url="https://kcl.ac.uk/people/amy-farrah-fowler",
        )
        leonard = make_user(
            full_name="Leonard Hofstadter", email="l.hofstadter@kcl.ac.uk",
            expertise="Experimental imaging & clinical translation",
            bio="Experimental physicist turned imaging researcher, translating "
                "models into real radiology workflows.",
            keywords="medical imaging, experimentation, radiology, deployment",
            seniority="Senior", contract_type="Senior Lecturer",
            department="Biomedical Engineering & Imaging Sciences",
            pi="Prof. Sheldon Cooper", line_manager="Prof. Sheldon Cooper",
            work_status="Active", hours_available=8, db_role="PI",
            workstreams="Medical Imaging AI|Clinical NLP & Language Models",
            linkedin_url="https://linkedin.com/in/leonard-hofstadter",
        )
        howard = make_user(
            full_name="Howard Wolowitz", email="h.wolowitz@kcl.ac.uk",
            expertise="Engineering & deployment of clinical AI systems",
            bio="Engineer (MEng) building and integrating ML systems into clinical "
                "infrastructure. No doctorate — but he did go to space.",
            keywords="engineering, MLOps, systems integration, APIs",
            seniority="Intermediate", contract_type="Software Engineer",
            department="Informatics", line_manager="Prof. Sheldon Cooper",
            work_status="Active", hours_available=15, db_role="Collaborator",
            workstreams="Deployment & MLOps|Federated & Privacy-Preserving ML",
        )
        raj = make_user(
            full_name="Rajesh Koothrappali", email="r.koothrappali@kcl.ac.uk",
            expertise="Data-driven risk prediction (ex-astrophysics)",
            bio="Astrophysicist applying large-scale statistical modelling to "
                "clinical risk prediction.",
            keywords="risk prediction, statistics, big data, calibration",
            seniority="Senior", contract_type="Postdoctoral Researcher",
            department="Informatics", pi="Prof. Sheldon Cooper",
            line_manager="Prof. Sheldon Cooper", work_status="Keen",
            hours_available=18, db_role="Collaborator",
            workstreams="Predictive Modelling & Risk|Medical Imaging AI",
            linkedin_url="https://linkedin.com/in/rajesh-koothrappali",
        )
        bernadette = make_user(
            full_name="Bernadette Rostenkowski-Wolowitz", email="b.rostenkowski@kcl.ac.uk",
            expertise="Microbiology & pharmaceutical data science",
            bio="Microbiologist leading pharmaceutical R&D collaborations; "
                "interested in privacy-preserving analysis across industry and "
                "the NHS. Small in stature, large in authority.",
            keywords="microbiology, pharmaceutical, federated learning, trials",
            seniority="Senior", contract_type="Research Fellow",
            department="Cancer & Pharmaceutical Sciences", work_status="Active",
            hours_available=9, db_role="PI",
            workstreams="Federated & Privacy-Preserving ML|Predictive Modelling & Risk",
            kcl_url="https://kcl.ac.uk/people/bernadette-rostenkowski",
        )
        penny = make_user(
            full_name="Penny Hofstadter", email="p.hofstadter@kcl.ac.uk",
            expertise="Clinical liaison & pharmaceutical engagement",
            bio="Pharmaceutical representative and patient-engagement lead — "
                "bridges clinical teams, patients and the research group, and is "
                "unmatched at explaining AI in plain English.",
            keywords="stakeholder engagement, clinical liaison, communication, patient voice",
            seniority="Intermediate", contract_type="Other",
            department="Population Health Sciences",
            line_manager="Dr Bernadette Rostenkowski-Wolowitz",
            work_status="Keen", hours_available=12, db_role="Collaborator",
            workstreams="Human-Centred AI",
            linkedin_url="https://linkedin.com/in/penny-hofstadter",
        )
        stuart = make_user(
            full_name="Stuart Bloom", email="s.bloom@kcl.ac.uk",
            expertise="Research assistant — annotation, evaluation & equity",
            bio="Endlessly available and eager research assistant supporting "
                "annotation, benchmarking and fairness auditing across projects. "
                "Rarely turns anything down.",
            keywords="annotation, benchmarking, fairness, literature review",
            seniority="Junior", contract_type="Research Assistant",
            department="Other", line_manager="Dr Amy Farrah Fowler",
            work_status="Keen", hours_available=30, db_role="Collaborator",
            workstreams="AI Governance & Safety",
        )
        db.session.commit()

        today = date.today()

        # ---------------- Projects ----------------
        # 1) Ongoing — Medical Imaging AI, led by Sheldon
        p1 = Project(
            title="Foundation models for cardiac MRI reporting",
            summary="Deploying and evaluating a foundation model to draft "
                    "structured cardiac MRI reports.",
            description="This project deploys an imaging foundation model to "
                        "pre-draft structured cardiac MRI reports for radiologist "
                        "review. We measure reporting time, report quality and "
                        "clinician trust, with a strong focus on safety and "
                        "governance.\n\nWork packages cover data governance, model "
                        "integration, a shadow-mode pilot and a prospective "
                        "evaluation.",
            status="Ongoing", project_type="Product Development",
            department="Biomedical Engineering & Imaging Sciences",
            keywords="cardiac MRI, foundation models, radiology, evaluation",
            workstream="Medical Imaging AI",
            expected_outcomes="A validated deployment protocol and an evaluation "
                              "report quantifying reporting time saved and quality.",
            github_url="https://github.com/kcl-health-ai/cardiac-mri-fm",
            start_date=today - timedelta(days=120), end_date=today + timedelta(days=120),
            pi_id=sheldon.id, proposer_id=leonard.id,
        )
        db.session.add(p1)
        db.session.flush()
        db.session.add_all([
            Milestone(project_id=p1.id, name="Data governance & IG approval",
                      start_date=today - timedelta(days=120),
                      end_date=today - timedelta(days=70), status="Done"),
            Milestone(project_id=p1.id, name="Model integration & shadow mode",
                      start_date=today - timedelta(days=75),
                      end_date=today - timedelta(days=10), status="Done"),
            Milestone(project_id=p1.id, name="Reader study (pilot)",
                      start_date=today - timedelta(days=15),
                      end_date=today + timedelta(days=45), status="In Progress"),
            Milestone(project_id=p1.id, name="Prospective evaluation & write-up",
                      start_date=today + timedelta(days=45),
                      end_date=today + timedelta(days=120), status="Planned"),
        ])
        db.session.add_all([
            Collaboration(user_id=sheldon.id, project_id=p1.id, role="PI"),
            Collaboration(user_id=leonard.id, project_id=p1.id, role="Lead researcher"),
            Collaboration(user_id=howard.id, project_id=p1.id, role="Engineering"),
            Collaboration(user_id=raj.id, project_id=p1.id, role="Modelling & stats"),
        ])

        # 2) Open — Federated & Privacy-Preserving ML, proposed by Bernadette
        p2 = Project(
            title="Federated learning across pharma and NHS datasets",
            summary="Privacy-preserving models trained across industry and NHS "
                    "sites without moving patient data.",
            description="We aim to build a federated learning framework so that a "
                        "pharmaceutical partner and multiple NHS trusts can jointly "
                        "train models while keeping data local. Seeking "
                        "collaborators with experience in federated learning, "
                        "infrastructure and clinical evaluation.",
            status="Open", project_type="Grant",
            department="Cancer & Pharmaceutical Sciences",
            keywords="federated learning, privacy, pharma, NHS",
            workstream="Federated & Privacy-Preserving ML",
            expected_outcomes="An open-source federated training pipeline and a "
                              "multi-site proof-of-concept.",
            start_date=today - timedelta(days=10), end_date=today + timedelta(days=200),
            proposer_id=bernadette.id, pi_id=None,
        )
        db.session.add(p2)
        db.session.flush()
        db.session.add_all([
            Milestone(project_id=p2.id, name="Scoping & partner recruitment",
                      start_date=today - timedelta(days=10),
                      end_date=today + timedelta(days=40), status="In Progress"),
            Milestone(project_id=p2.id, name="Framework build",
                      start_date=today + timedelta(days=40),
                      end_date=today + timedelta(days=120), status="Planned"),
        ])
        db.session.add(Collaboration(user_id=bernadette.id, project_id=p2.id,
                                     role="Proposer"))

        # 3) Waiting for PI — AI Governance & Safety, proposed by Stuart
        p3 = Project(
            title="Equity audit of deployed diagnostic AI",
            summary="Auditing deployed diagnostic models for performance gaps "
                    "across demographic groups.",
            description="A proposal to systematically audit already-deployed "
                        "diagnostic models for subgroup performance disparities. "
                        "Currently in the backlog awaiting a senior investigator "
                        "to coordinate.",
            status="Waiting for PI", project_type="Proof of Concept",
            department="Population Health Sciences",
            keywords="equity, fairness, auditing, imaging",
            workstream="AI Governance & Safety",
            expected_outcomes="An audit framework and a report on subgroup "
                              "performance across deployed models.",
            start_date=today, end_date=today + timedelta(days=180),
            proposer_id=stuart.id, pi_id=None,
        )
        db.session.add(p3)
        db.session.flush()
        db.session.add(Collaboration(user_id=stuart.id, project_id=p3.id,
                                     role="Proposer"))

        # 4) Launched — Clinical NLP, led by Leonard
        p4 = Project(
            title="Ambient AI scribe for outpatient clinics",
            summary="A launched project integrating an ambient LLM scribe to draft "
                    "clinical letters.",
            description="Kick-off complete; the project is launching an ambient "
                        "speech-to-text plus LLM summarisation pipeline to draft "
                        "outpatient letters for clinician review.",
            status="Launched", project_type="Product Development",
            department="Informatics",
            keywords="LLMs, ambient scribe, clinical documentation, NLP",
            workstream="Clinical NLP & Language Models",
            expected_outcomes="Integrated ambient scribe prototype and a plan for "
                              "a prospective shadow-mode evaluation.",
            github_url="https://github.com/kcl-health-ai/ambient-scribe",
            start_date=today - timedelta(days=15), end_date=today + timedelta(days=160),
            pi_id=leonard.id, proposer_id=raj.id,
        )
        db.session.add(p4)
        db.session.flush()
        db.session.add_all([
            Milestone(project_id=p4.id, name="Kick-off & scoping",
                      start_date=today - timedelta(days=15),
                      end_date=today + timedelta(days=15), status="In Progress"),
            Milestone(project_id=p4.id, name="Workflow integration",
                      start_date=today + timedelta(days=15),
                      end_date=today + timedelta(days=90), status="Planned"),
        ])
        db.session.add_all([
            Collaboration(user_id=leonard.id, project_id=p4.id, role="PI"),
            Collaboration(user_id=raj.id, project_id=p4.id, role="NLP lead"),
            Collaboration(user_id=howard.id, project_id=p4.id, role="Engineering"),
        ])

        # 5) Completed — Predictive Modelling & Risk, led by Bernadette
        p5 = Project(
            title="Sepsis early-warning score validation",
            summary="Completed external validation of an ML sepsis early-warning "
                    "score.",
            description="A retrospective external validation of a machine-learned "
                        "sepsis early-warning score across two years of emergency "
                        "admissions.",
            status="Completed", project_type="Grant",
            department="Cancer & Pharmaceutical Sciences",
            keywords="sepsis, early warning, validation, calibration",
            workstream="Predictive Modelling & Risk",
            expected_outcomes="",
            actual_outcomes="• Externally validated on 48,000 admissions with "
                            "AUROC 0.86 and good calibration after recalibration.\n"
                            "• Identified alert-fatigue trade-offs at different "
                            "thresholds.\n• Published in a peer-reviewed journal and "
                            "the code released openly.\n• Informed a business case "
                            "for a prospective silent trial.",
            github_url="https://github.com/kcl-health-ai/sepsis-validation",
            start_date=today - timedelta(days=400), end_date=today - timedelta(days=40),
            pi_id=bernadette.id, proposer_id=raj.id,
        )
        db.session.add(p5)
        db.session.flush()
        db.session.add_all([
            Milestone(project_id=p5.id, name="Data extraction",
                      start_date=today - timedelta(days=400),
                      end_date=today - timedelta(days=330), status="Done"),
            Milestone(project_id=p5.id, name="Validation & calibration",
                      start_date=today - timedelta(days=330),
                      end_date=today - timedelta(days=180), status="Done"),
            Milestone(project_id=p5.id, name="Write-up & publication",
                      start_date=today - timedelta(days=180),
                      end_date=today - timedelta(days=40), status="Done"),
        ])
        db.session.add_all([
            Collaboration(user_id=bernadette.id, project_id=p5.id, role="PI"),
            Collaboration(user_id=raj.id, project_id=p5.id, role="Lead analyst"),
            Collaboration(user_id=stuart.id, project_id=p5.id, role="Data & annotation"),
        ])

        # 6) Open — Human-Centred AI, led by Amy, proposed by Penny
        p6 = Project(
            title="Patient-facing explanations for AI decisions",
            summary="Designing plain-language explanations for AI-assisted "
                    "clinical decisions.",
            description="Co-designing patient-facing explanations of AI-assisted "
                        "recommendations, evaluated for comprehension and trust. "
                        "Seeking collaborators from HCI, health comms and clinical "
                        "backgrounds.",
            status="Open", project_type="Hackathon",
            department="Neuroscience",
            keywords="explainability, HCI, patient communication, trust",
            workstream="Human-Centred AI",
            expected_outcomes="A validated set of explanation templates and a "
                              "comprehension study report.",
            start_date=today - timedelta(days=5), end_date=today + timedelta(days=150),
            proposer_id=penny.id, pi_id=amy.id,
        )
        db.session.add(p6)
        db.session.flush()
        db.session.add_all([
            Collaboration(user_id=amy.id, project_id=p6.id, role="PI"),
            Collaboration(user_id=penny.id, project_id=p6.id, role="Proposer / patient engagement"),
        ])

        # ---------------- Join requests ----------------
        db.session.add_all([
            JoinRequest(user_id=stuart.id, project_id=p1.id,
                        message="I can help with annotation and benchmarking of "
                                "the generated reports. I'm very available.",
                        status="Pending"),
            JoinRequest(user_id=howard.id, project_id=p2.id,
                        message="Happy to build the federated infrastructure.",
                        status="Pending"),
            JoinRequest(user_id=raj.id, project_id=p2.id,
                        message="Keen to contribute the modelling and calibration.",
                        status="Pending"),
        ])

        # ---------------- News / announcements ----------------
        now = datetime.utcnow()
        db.session.add_all([
            NewsPost(
                title="Welcome to the Collaboration Hub",
                body="The hub is now live! Create your profile, browse projects "
                     "across their lifecycle, and express interest in the work "
                     "that matches your skills. Sheldon strongly recommends "
                     "reading the onboarding guide. Twice.",
                pinned=True, author_id=sheldon.id, workstream="",
                created_at=now - timedelta(days=2),
            ),
            NewsPost(
                title="Ambient scribe project launches in outpatient clinics",
                body="Leonard's ambient AI scribe project has moved into its "
                     "launch phase, with an initial clinic integration planned "
                     "and early clinician feedback being gathered.",
                author_id=raj.id, workstream="Clinical NLP & Language Models",
                created_at=now - timedelta(days=6),
            ),
            NewsPost(
                title="Sepsis early-warning validation study published",
                body="The completed sepsis early-warning validation, led by "
                     "Bernadette, has been published with the code released "
                     "openly. See the Impact page for the headline outcomes.",
                author_id=bernadette.id, workstream="Predictive Modelling & Risk",
                created_at=now - timedelta(days=12),
            ),
            NewsPost(
                title="Call for collaborators: federated learning across sites",
                body="A new open project is seeking collaborators with experience "
                     "in federated learning, infrastructure and clinical "
                     "evaluation. Express your interest from the project page.",
                author_id=bernadette.id,
                workstream="Federated & Privacy-Preserving ML",
                created_at=now - timedelta(days=18),
            ),
        ])

        # ---------------- Events ----------------
        e1 = Event(
            title="Deploying LLMs safely in the NHS",
            description="A seminar on evaluation, governance and guardrails for "
                        "large language models in clinical settings, with lessons "
                        "from the ambient scribe project.",
            event_type="Seminar", is_online=True,
            url="https://teams.microsoft.com/l/meetup-join/llm-seminar",
            location="", workstream="Clinical NLP & Language Models",
            host_id=leonard.id, start_at=now + timedelta(days=7, hours=1),
            end_at=now + timedelta(days=7, hours=2),
        )
        e2 = Event(
            title="Hands-on: intro to federated learning",
            description="A practical training session building a simple federated "
                        "training loop across simulated sites. Bring a laptop.",
            event_type="Training", is_online=False, location="Bush House (S)3.01",
            workstream="Federated & Privacy-Preserving ML",
            host_id=bernadette.id, start_at=now + timedelta(days=14, hours=3),
            end_at=now + timedelta(days=14, hours=5),
        )
        e3 = Event(
            title="Data club: calibration in clinical risk models",
            description="An informal data club discussing calibration, decision "
                        "curves and why they matter for deployment.",
            event_type="Data Club", is_online=False,
            location="Guy's Campus, Lecture Theatre 1",
            workstream="Predictive Modelling & Risk",
            host_id=raj.id, start_at=now + timedelta(days=3, hours=2),
            end_at=now + timedelta(days=3, hours=3),
        )
        e4 = Event(
            title="Workshop: evaluating medical imaging AI",
            description="A workshop on designing reader studies and evaluation "
                        "protocols for imaging models.",
            event_type="Workshop", is_online=False, location="St Thomas' Hospital",
            workstream="Medical Imaging AI",
            host_id=leonard.id, start_at=now + timedelta(days=21, hours=4),
            end_at=now + timedelta(days=21, hours=6),
        )
        e_past = Event(
            title="Foundation models in cardiac imaging",
            description="A past seminar introducing foundation models for cardiac "
                        "imaging and their clinical translation.",
            event_type="Seminar", is_online=True,
            url="https://kcl.ac.uk/events/cardiac-fm",
            workstream="Medical Imaging AI",
            host_id=sheldon.id, start_at=now - timedelta(days=20, hours=-1),
            end_at=now - timedelta(days=20, hours=-2),
        )
        db.session.add_all([e1, e2, e3, e4, e_past])
        db.session.flush()

        db.session.add_all([
            EventAttendance(user_id=raj.id, event_id=e1.id),
            EventAttendance(user_id=howard.id, event_id=e1.id),
            EventAttendance(user_id=stuart.id, event_id=e1.id),
            EventAttendance(user_id=stuart.id, event_id=e3.id),
            EventAttendance(user_id=penny.id, event_id=e3.id),
            EventAttendance(user_id=raj.id, event_id=e4.id),
        ])

        db.session.commit()

        print("Seed complete.")
        print(f"  Users:    {User.query.count()}")
        print(f"  Projects: {Project.query.count()}")
        print("\nDemo login:  s.cooper@kcl.ac.uk  /  password123  (admin/PI)")
        print("Other users use the same password: password123")


if __name__ == "__main__":
    run()
