"""Generate the Microsoft Forms version of the researcher interest survey.

Writes two Word documents:

  Researcher_Interest_Survey_MSForms.docx            clean - questions and answer
                                                     options only, ready for Forms'
                                                     Quick Import
  Researcher_Interest_Survey_MSForms_annotated.docx  same, plus a note under each
                                                     question giving its Forms type,
                                                     whether it is required, and any
                                                     branching

The master (Google Forms) version lives in Researcher_Interest_Survey.md. Edit the
content below and re-run to regenerate.

No third-party packages: the .docx is written as raw OOXML into a zip, so this runs
on any Python 3.

    python make_survey_docx.py
"""
import os
import zipfile
from xml.sax.saxutils import escape

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Survey content
# ---------------------------------------------------------------------------
# Roles used throughout: Proposer (brings the idea and milestones), Project Lead
# (plans and orchestrates the team), Collaborator (contributes to someone else's).
# A proposer can also be the lead, which is why the project-type question is split
# by role rather than forced into a single-choice Likert row.

SECTIONS = [
    {
        "title": "Introduction & consent",
        "desc": [
            "We are setting up a Collaboration Hub for AI Deployment in Healthcare "
            "Research at KCL: a single place where researchers list their expertise, "
            "propose projects, find collaborators and project leads, and share what "
            "came out of the work. Projects run at three scales — from multi-day "
            "hackathons to funded, long-term grants — so people can contribute at "
            "whatever level fits their workload.",
            "This survey tells us whether there is real appetite for it, and what it "
            "needs to offer to be worth your time. It takes about 7 minutes.",
            "Your data. The survey is anonymous. We don't ask for your name, email, "
            "department or position until the last page, and then only if you'd like to "
            "register for the first phase — you can answer everything else and leave "
            "those blank. Responses are used to design the hub and to report aggregate "
            "findings to [sponsor/committee]; contact details are stored separately and "
            "never appear in any report. [Add your privacy notice link.]",
        ],
        "questions": [
            {
                "q": "I have read the above and am happy to take part.",
                "type": "Choice · single answer · REQUIRED",
                "opts": ["Yes, continue", "No — exit"],
                "note": "Branching: \"No\" → End of form.",
            },
        ],
    },
    {
        "title": "Your research and AI expertise",
        "desc": [],
        "questions": [
            {
                "q": "In two or three sentences, what is your main research focus at "
                     "the moment?",
                "type": "Text · long answer · REQUIRED",
                "opts": [],
            },
            {
                "q": "Which of the hub's workstreams are closest to your work? "
                     "(choose up to 3)",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Clinical NLP & Language Models",
                    "Medical Imaging AI",
                    "Predictive Modelling & Risk",
                    "Federated & Privacy-Preserving ML",
                    "AI Governance & Safety",
                    "Deployment & MLOps",
                    "Human-Centred AI",
                    "None of these / my angle is different",
                ],
                "note": "Turn on \"Other\" so people can describe a different angle.",
            },
            {
                "q": "How would you rate your own expertise in AI/machine learning?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "1 — None: I don't work with AI/ML",
                    "2 — Aware: I follow it and use off-the-shelf tools, but don't "
                    "build anything",
                    "3 — Applied: I apply existing models/libraries to my own data",
                    "4 — Advanced: I build, train and validate models as a core part "
                    "of my work",
                    "5 — Expert: I develop methods and publish in AI/ML venues",
                ],
            },
            {
                "q": "What would you bring to a collaboration?",
                "type": "Choice · multiple answers",
                "opts": [
                    "Clinical question / unmet need",
                    "Access to a dataset",
                    "Data engineering / curation",
                    "ML modelling",
                    "Statistics / study design",
                    "Software engineering & deployment",
                    "Information governance / ethics expertise",
                    "Qualitative / human-factors research",
                    "Funding or existing grant budget",
                    "Compute resources (e.g. CREATE, GPU access)",
                    "Time, mainly — happy to be assigned",
                ],
            },
            {
                "q": "Do you hold a clinical or NHS-facing role (e.g. GSTT, KCH, SLaM)?",
                "type": "Choice · single answer",
                "opts": [
                    "Yes, clinically active",
                    "Yes, honorary/affiliated but not clinically active",
                    "No",
                ],
            },
            {
                "q": "Do you already have any of the following available for a "
                     "collaborative project? Answer for each of: suitable data; "
                     "ethics/IG approval in place; compute; funded staff time.",
                "type": "Likert · statements: Suitable data / Ethics or IG approval "
                        "in place / Compute / Funded staff time",
                "opts": ["Yes, ready now", "Could be arranged", "No", "Not sure"],
                "note": "If Quick Import turns this into a single-choice question, "
                        "change the type to Likert and add the four statements above "
                        "as rows. Mirrors the panel's data-readiness and resources "
                        "criteria, so proposals arrive pre-triaged.",
            },
            {
                "q": "Would you want any of this from the hub?",
                "type": "Choice · multiple answers",
                "opts": [
                    "Training in AI/ML for my team or me",
                    "To deliver a seminar, training session or data club",
                    "Neither",
                ],
            },
        ],
    },
    {
        "title": "How you collaborate today",
        "desc": [],
        "questions": [
            {
                "q": "How satisfied are you with the level of research collaboration "
                     "within your own department/faculty?",
                "type": "Rating · 5 levels · REQUIRED · labels: Very "
                        "dissatisfied → Very satisfied",
                "opts": [
                    "1 — Very dissatisfied", "2", "3", "4",
                    "5 — Very satisfied",
                ],
            },
            {
                "q": "And with collaboration across KCL as a whole (outside your "
                     "department)?",
                "type": "Rating · 5 levels · REQUIRED · same labels",
                "opts": [
                    "1 — Very dissatisfied", "2", "3", "4",
                    "5 — Very satisfied",
                ],
            },
            {
                "q": "And with collaboration with clinical/NHS partners?",
                "type": "Rating · 5 levels · same labels",
                "opts": [
                    "1 — Very dissatisfied", "2", "3", "4",
                    "5 — Very satisfied",
                ],
            },
            {
                "q": "How do you currently find collaborators?",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Personal network / word of mouth",
                    "Seminars and internal events",
                    "Mailing lists or Teams channels",
                    "Introduced by a manager or mentor",
                    "Publications / KCL Pure profiles",
                    "Cold outreach",
                    "I don't actively look",
                ],
                "note": "Your baseline. Re-ask in 12 months to show whether the hub "
                        "displaced any of these.",
            },
            {
                "q": "What most gets in the way of collaborating more? (choose up to 3)",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "I don't know who else at KCL works on what",
                    "No spare time / competing deadlines",
                    "Data access, IG or ethics friction",
                    "No funding for the work",
                    "No clear route to a project lead or sponsor",
                    "Unclear authorship/IP expectations",
                    "Collaborations start well but fizzle out",
                    "Nothing — I'm happy as things are",
                ],
                "note": "Turn on \"Other\". Satisfaction scores say whether there's a "
                        "problem; this says which one — and whether a directory even "
                        "addresses it.",
            },
        ],
    },
    {
        "title": "The hub itself",
        "desc": [
            "How it would work. Anyone can propose a project. A monthly "
            "multidisciplinary panel reviews proposals on clinical impact, data "
            "readiness, resources and AI feasibility. Approved projects appear as Open, "
            "researchers request to join, and once a project lead takes it on the "
            "project launches and runs to an agreed end date, when outcomes are "
            "published on the platform. Profiles list expertise, availability and "
            "current projects, so people can be found rather than having to be known.",
        ],
        "questions": [
            {
                "q": "Overall, would a hub like this be an advantage for your research?",
                "type": "Rating · 5 levels · REQUIRED · labels: No real "
                        "advantage → Substantial advantage",
                "opts": [
                    "1 — No real advantage", "2", "3", "4",
                    "5 — Substantial advantage",
                ],
            },
            {
                "q": "Which parts would be most valuable to you? (choose up to 3)",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Searchable directory of people and their expertise",
                    "Seeing all open projects in one place",
                    "Finding a project lead for an idea I have",
                    "Finding collaborators with skills I lack",
                    "Finding students/juniors to work on a project",
                    "Panel review giving projects credibility",
                    "Shared roadmaps and progress tracking",
                    "Events calendar (seminars, training, data clubs)",
                    "Showcase of completed projects and their impact",
                    "None of these",
                ],
                "note": "Prioritises the build — stops you polishing the Impact page "
                        "when everyone wanted the people directory.",
            },
            {
                "q": "What would stop you from using it, or what's missing from the "
                     "description above?",
                "type": "Text · long answer",
                "opts": [],
                "note": "The most informative free-text field in the form — it "
                        "surfaces objections you can't anticipate.",
            },
        ],
    },
    {
        "title": "Your participation",
        "desc": [
            "Three ways to take part. Proposer — you bring the idea. You define the "
            "problem, the intended outcome and the milestones, but you don't necessarily "
            "set the timeline or organise the team. Project lead — you lead the "
            "planning and orchestrate the team to deliver against those milestones: "
            "timelines, who does what, keeping it moving. Collaborator — you "
            "contribute to a project someone else proposed or leads.",
            "These aren't exclusive — proposers are often the lead as well. Say yes "
            "to both if that's you.",
        ],
        "questions": [
            {
                "q": "How would you describe your seniority?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Junior — early career, working under supervision",
                    "Intermediate — running your own workstream within someone "
                    "else's project",
                    "Senior — leading projects and supervising others",
                    "Principal — leading a group, holding grants, setting research "
                    "direction",
                ],
            },
            {
                "q": "Grant projects need a formally eligible Principal Investigator to "
                     "hold the funding. Do you hold PI status at KCL?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes, I currently hold or have held PI status",
                    "I am eligible but have not yet acted as PI",
                    "Not eligible",
                    "Not sure",
                ],
                "note": "Deliberately separate from the \"would you lead\" question "
                        "below: that one asks whether someone is willing, this asks "
                        "whether they are allowed to hold grant funding. Long-term "
                        "projects stall on the second.",
            },
            {
                "q": "Which kinds of project would you PROPOSE — bring the idea and "
                     "define the milestones?",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Hackathon — short-term, days to about 2 weeks",
                    "Proof of Concept — medium-term, a few months",
                    "Product Development — medium-term, building a deployable tool",
                    "Grant — long-term funded programme",
                    "None — I wouldn't propose projects",
                ],
                "note": "These three questions replace the checkbox grid in the Google "
                        "version (MS Forms has none). Splitting by role rather than "
                        "using a Likert row keeps the fact that one person can be both "
                        "proposer and lead.",
            },
            {
                "q": "Which kinds of project would you LEAD — plan the work and "
                     "orchestrate the team to deliver it?",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Hackathon — short-term, days to about 2 weeks",
                    "Proof of Concept — medium-term, a few months",
                    "Product Development — medium-term, building a deployable tool",
                    "Grant — long-term funded programme",
                    "None — I wouldn't lead a project",
                ],
            },
            {
                "q": "Which kinds of project would you JOIN as a collaborator — "
                     "contribute to someone else's?",
                "type": "Choice · multiple answers · REQUIRED",
                "opts": [
                    "Hackathon — short-term, days to about 2 weeks",
                    "Proof of Concept — medium-term, a few months",
                    "Product Development — medium-term, building a deployable tool",
                    "Grant — long-term funded programme",
                    "None — I wouldn't join as a collaborator",
                ],
            },
            {
                "q": "Realistically, how much time could you give per month, across all "
                     "hub projects?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "None right now",
                    "Up to 2 hours",
                    "2–5 hours",
                    "5–10 hours (about half a day a week)",
                    "10–20 hours",
                    "20+ hours (about a day a week or more)",
                ],
                "note": "Per month, not per week or % FTE — monthly bands are the "
                        "least optimistic and the easiest to answer honestly.",
            },
            {
                "q": "And over what period could you sustain that?",
                "type": "Choice · single answer",
                "opts": [
                    "A one-off burst (a hackathon)",
                    "Up to 3 months",
                    "3–12 months",
                    "More than a year",
                    "Depends entirely on the project",
                ],
            },
            {
                "q": "When in the year do you have most capacity? (teaching and clinical "
                     "loads are seasonal)",
                "type": "Choice · multiple answers",
                "opts": [
                    "Sept–Dec", "Jan–Mar", "Apr–Jun", "Jul–Aug",
                    "No strong pattern",
                ],
            },
            {
                "q": "Which site(s) are you usually based at?",
                "type": "Choice · multiple answers",
                "opts": [
                    "Denmark Hill", "Guy's", "St Thomas'", "Strand", "Waterloo",
                    "Mostly remote",
                ],
            },
            {
                "q": "Which best describes your availability right now?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Active — already have capacity committed",
                    "Keen — actively looking to join something",
                    "Busy — interested, but not for a few months",
                    "Unavailable — not at the moment",
                ],
            },
            {
                "q": "Do you already have a project idea you'd propose to the panel?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes, ready to write it up",
                    "Yes, but it needs shaping",
                    "Not yet",
                ],
                "note": "Turns the survey into a pipeline — you finish with candidate "
                        "projects for the first panel, not just a sentiment score.",
            },
            {
                "q": "If yes, tell us about it in a sentence or two.",
                "type": "Text · long answer",
                "opts": [],
            },
            {
                "q": "Do you line-manage, supervise or lead a team of researchers or "
                     "students?",
                "type": "Choice · single answer · REQUIRED",
                "opts": ["Yes", "No"],
                "note": "Branching: \"No\" → skip the \"Your team\" section and go to "
                        "\"Sharing outcomes\".",
            },
        ],
    },
    {
        "title": "Your team",
        "desc": [
            "Only shown to people who supervise or lead a team.",
        ],
        "questions": [
            {
                "q": "Would you be willing for members of your team to take part in hub "
                     "projects?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes, and I'd actively encourage it",
                    "Yes, case by case with my sign-off",
                    "Only if it clearly serves their own project",
                    "No",
                ],
            },
            {
                "q": "Roughly how many of your team could realistically take part in the "
                     "next 12 months?",
                "type": "Choice · single answer",
                "opts": ["1", "2–3", "4–5", "More than 5"],
            },
            {
                "q": "Which of them?",
                "type": "Choice · multiple answers",
                "opts": [
                    "PhD students", "Postdocs", "Research assistants",
                    "Clinical fellows", "Technical staff (RSE/data)",
                ],
            },
            {
                "q": "What conditions would you attach?",
                "type": "Choice · multiple answers",
                "opts": [
                    "The work must align with their existing project",
                    "I must be named on outputs / kept informed",
                    "A cap on their hours",
                    "They must not be in write-up or a critical phase",
                    "Written agreement on authorship up front",
                    "None",
                ],
            },
            {
                "q": "Would you need approval from anyone above you (Head of Department, "
                     "funder) to allow it?",
                "type": "Choice · single answer",
                "opts": ["No", "Yes", "Not sure"],
                "note": "\"Yes\" from a group leader often means \"yes, if my HoD agrees\" "
                        "— capture the caveats now, not at kick-off.",
            },
        ],
    },
    {
        "title": "Sharing outcomes",
        "desc": [],
        "questions": [
            {
                "q": "Projects publish their outcomes on the hub when they complete. "
                     "Would you be comfortable sharing yours at a high level — what "
                     "the project was, who was involved and what came of it, without "
                     "methodological or unpublished detail?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes, publicly on the hub",
                    "Yes, but visible to KCL members only",
                    "Yes, but only after I review the wording",
                    "Only once the work is published elsewhere",
                    "No",
                ],
            },
            {
                "q": "Which specifics would you be happy to share?",
                "type": "Choice · multiple answers",
                "opts": [
                    "Project title and plain-English summary",
                    "Names of collaborators",
                    "Publications and DOIs",
                    "Code repositories",
                    "Names of datasets used (not the data)",
                    "Grants or funding won as a result",
                    "Preliminary/unpublished results",
                    "Negative results and lessons learned",
                ],
                "note": "\"I'll share outcomes\" and \"I'll share unpublished results\" "
                        "are very different commitments; the gap is where trust is lost.",
            },
            {
                "q": "Any concerns about sharing — IP, commercial partners, "
                     "pre-publication risk, patient data?",
                "type": "Text · long answer",
                "opts": [],
            },
            {
                "q": "If you joined, would you be happy for your profile (name, "
                     "department, expertise, current projects) to be visible to other hub "
                     "members?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes",
                    "Yes, but hide my availability/hours",
                    "KCL sign-in only",
                    "No",
                ],
                "note": "The directory is the core feature — better to learn now if a "
                        "third of people won't be listed in it.",
            },
        ],
    },
    {
        "title": "Registering your interest",
        "desc": [
            "Last page. Everything so far has been anonymous. We're now building the "
            "first phase of the hub with a small group of founding members, who get "
            "early access, help shape how it works, and are first in line when projects "
            "open.",
        ],
        "questions": [
            {
                "q": "Would you like to register your interest in taking part in "
                     "phase one?",
                "type": "Choice · single answer · REQUIRED",
                "opts": [
                    "Yes — register me as an interested member",
                    "Keep me informed — send me updates, but I'm not committing yet",
                    "No — I'd rather not be contacted",
                ],
            },
            {
                "q": "Position",
                "type": "Choice · single answer · drop-down",
                "opts": [
                    "Research Assistant", "PhD Student", "Postdoctoral Researcher",
                    "Research Fellow", "Academic / Lecturer", "Senior Lecturer",
                    "Professor", "Clinician", "Data Scientist", "Software Engineer",
                    "Other",
                ],
            },
            {
                "q": "Department",
                "type": "Choice · single answer · drop-down",
                "opts": [
                    "Biomedical Engineering & Imaging Sciences",
                    "Informatics",
                    "School of Cardiovascular & Metabolic Medicine",
                    "Population Health Sciences",
                    "Cancer & Pharmaceutical Sciences",
                    "Neuroscience",
                    "Nursing, Midwifery & Palliative Care",
                    "Life Sciences & Medicine",
                    "Other",
                ],
                "note": "Ask this and Faculty of everyone, not just registrants — "
                        "they're the only non-identifying fields you can break results "
                        "down by. Subtitle: \"Even if you answered No above, this helps "
                        "us report back by department.\"",
            },
            {
                "q": "Faculty",
                "type": "Choice · single answer · drop-down",
                "opts": [
                    "Faculty of Life Sciences & Medicine",
                    "Institute of Psychiatry, Psychology & Neuroscience (IoPPN)",
                    "Faculty of Natural, Mathematical & Engineering Sciences",
                    "Florence Nightingale Faculty of Nursing, Midwifery & Palliative Care",
                    "Faculty of Dentistry, Oral & Craniofacial Sciences",
                    "King's Business School / Social Science & Public Policy / Arts & "
                    "Humanities / Law",
                    "Other",
                ],
            },
            {
                "q": "If you joined, which role would you expect to hold most often?",
                "type": "Choice · single answer",
                "opts": [
                    "Proposer — I'd bring ideas",
                    "Project lead — I'd plan and orchestrate the team",
                    "Collaborator — I'd contribute to other people's projects",
                    "A mix, depending on the project",
                ],
            },
            {
                "q": "Name (only needed if you registered above)",
                "type": "Text · short answer",
                "opts": [],
            },
            {
                "q": "KCL email (only needed if you registered above — this is the "
                     "only way we can reach you)",
                "type": "Text · short answer · restriction: contains @kcl.ac.uk",
                "opts": [],
            },
            {
                "q": "Beyond joining projects, would you be willing to…",
                "type": "Choice · multiple answers",
                "opts": [
                    "Sit on the monthly review panel",
                    "Lead or co-lead a workstream",
                    "Be interviewed for 20 minutes about your needs",
                    "Help run an event or training session",
                    "None of these",
                ],
                "note": "You need panel members and workstream leads from day one — "
                        "the cheapest place to recruit them.",
            },
            {
                "q": "Anything else we should know, or anything we've missed?",
                "type": "Text · long answer",
                "opts": [],
            },
        ],
    },
]

TITLE = "Collaboration Hub for AI in Healthcare — Researcher Interest Survey"

# Letters used to label answer options: A. B. C. ...
LETTERS = [chr(ord("A") + i) for i in range(26)]

# ---------------------------------------------------------------------------
# Minimal OOXML writer
# ---------------------------------------------------------------------------
CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package'
    '.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd'
    '.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
    '2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)

DOC_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships"/>'
)

SECT_PR = (
    '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
    'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
)


def run(text, *, bold=False, italic=False, size=22, color=None):
    """One text run. `size` is in half-points, so 22 = 11pt."""
    props = ['<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>']
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append('<w:color w:val="%s"/>' % color)
    props.append('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size))
    return (
        "<w:r><w:rPr>%s</w:rPr><w:t xml:space=\"preserve\">%s</w:t></w:r>"
        % ("".join(props), escape(text))
    )


def para(runs, *, before=0, after=80, indent=0, keep_next=False):
    props = ['<w:spacing w:before="%d" w:after="%d"/>' % (before, after)]
    if indent:
        props.append('<w:ind w:left="%d"/>' % indent)
    if keep_next:
        props.append("<w:keepNext/>")
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % ("".join(props), "".join(runs))


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def build_body(annotated):
    """Return the list of paragraph XML strings for one variant of the document."""
    out = [
        para([run(TITLE, bold=True, size=32)], after=160),
    ]
    if annotated:
        out.append(
            para(
                [
                    run(
                        "Annotated build copy. Each » line gives the Microsoft Forms "
                        "question type, whether the question should be marked required, "
                        "and any branching or setup note. Delete these lines if you "
                        "import this file rather than the clean one.",
                        italic=True,
                        size=18,
                        color="777777",
                    )
                ],
                after=200,
            )
        )

    number = 0
    for index, section in enumerate(SECTIONS):
        if index:
            out.append(page_break())
        out.append(
            para(
                [run("Section %d — %s" % (index + 1, section["title"]),
                     bold=True, size=26)],
                before=120, after=100, keep_next=True,
            )
        )
        for paragraph in section["desc"]:
            out.append(para([run(paragraph, size=20)], after=100))

        for question in section["questions"]:
            number += 1
            out.append(
                para(
                    [run("%d. %s" % (number, question["q"]), bold=True)],
                    before=160, after=40, keep_next=True,
                )
            )
            if annotated:
                note = "» " + question["type"]
                if question.get("note"):
                    note += "  |  " + question["note"]
                out.append(
                    para([run(note, italic=True, size=18, color="777777")],
                         after=40, indent=283)
                )
            for letter, option in zip(LETTERS, question["opts"]):
                out.append(
                    para([run("%s. %s" % (letter, option))], after=20, indent=283)
                )

    return out


def write_docx(path, annotated):
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
        '2006/main"><w:body>%s%s</w:body></w:document>'
        % ("".join(build_body(annotated)), SECT_PR)
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("word/_rels/document.xml.rels", DOC_RELS)
        archive.writestr("word/document.xml", document)
    return path


def main():
    total = sum(len(section["questions"]) for section in SECTIONS)
    for suffix, annotated in (("", False), ("_annotated", True)):
        path = os.path.join(
            BASE_DIR, "Researcher_Interest_Survey_MSForms%s.docx" % suffix
        )
        write_docx(path, annotated)
        print("wrote %s" % os.path.basename(path))
    print("%d questions across %d sections" % (total, len(SECTIONS)))


if __name__ == "__main__":
    main()
