"""Generate the Collaboration Hub overview deck as a PowerPoint (.pptx).

KCL palette (navy / crimson / greys), Georgia serif headings, built from the
project brief. Run:  python make_pptx.py   ->  Collaboration_Hub_Overview.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---- palette / fonts -------------------------------------------------------
NAVY   = RGBColor(0x0A, 0x1F, 0x44)
NAVY2  = RGBColor(0x17, 0x30, 0x5E)
CRIMSON = RGBColor(0xC8, 0x10, 0x2E)
INK    = RGBColor(0x14, 0x1D, 0x33)
MUTED  = RGBColor(0x58, 0x60, 0x74)
PANEL  = RGBColor(0xEE, 0xF2, 0xF8)
LINE   = RGBColor(0xDD, 0xE3, 0xEC)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT  = RGBColor(0xCD, 0xD8, 0xEC)
AMBER  = RGBColor(0xB3, 0x64, 0x1B)
TEAL   = RGBColor(0x0F, 0x76, 0x6E)
SERIF  = "Georgia"
SANS   = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
MW = 13.333            # slide width
MARGIN = 0.9
CW = MW - 2 * MARGIN   # content width


# ---- helpers ---------------------------------------------------------------
def add_slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    return s


def shape(s, kind, l, t, w, h, fill=None, line_color=None, line_w=1.0):
    sh = s.shapes.add_shape(kind, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line_color is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line_color; sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    return sh


def rect(s, l, t, w, h, fill, **kw):
    return shape(s, MSO_SHAPE.RECTANGLE, l, t, w, h, fill=fill, **kw)


def rrect(s, l, t, w, h, fill, **kw):
    return shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=fill, **kw)


def para(tf, text, size, color, bold=False, font=SANS, italic=False,
         first=False, sa=6, sb=0, align=PP_ALIGN.LEFT, line=1.05):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(sa); p.space_before = Pt(sb); p.line_spacing = line
    r = p.add_run(); r.text = text
    f = r.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.name = font; f.color.rgb = color
    return p


def textbox(s, l, t, w, h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    return tf


def header(s, kicker, title):
    """White content-slide header: crimson kicker, navy serif title, rule."""
    rect(s, 0, 0, 0.16, 7.5, CRIMSON)                     # left accent bar
    tf = textbox(s, MARGIN, 0.5, CW, 1.5)
    para(tf, kicker.upper(), 12.5, CRIMSON, bold=True, first=True, sa=5)
    para(tf, title, 29, NAVY, bold=True, font=SERIF, sa=0, line=1.0)
    rect(s, MARGIN + 0.02, 1.72, 0.85, 0.05, CRIMSON)     # underline
    footer(s)


def footer(s):
    tf = textbox(s, MARGIN, 7.02, 10, 0.4)
    para(tf, "Collaboration Hub  ·  AI Deployment in Healthcare Research",
         9, MUTED, first=True)


def card(s, l, t, w, h, title, body, accent=CRIMSON, tsize=15, bsize=11.5,
         fill=PANEL):
    box = rrect(s, l, t, w, h, fill, line_color=LINE, line_w=1)
    rect(s, l, t, w, 0.055, accent)                       # top accent
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2); tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.18); tf.margin_bottom = Inches(0.12)
    para(tf, title, tsize, NAVY, bold=True, first=True, sa=5)
    para(tf, body, bsize, MUTED, line=1.1)
    return box


# ===========================================================================
# Slide 1 — Title
# ===========================================================================
s = add_slide(NAVY)
rect(s, 0, 0, MW, 7.5, NAVY)
# subtle band
rect(s, 0, 0, MW, 0.22, CRIMSON)
tf = textbox(s, MARGIN, 1.15, CW, 3.4)
para(tf, "KING'S COLLEGE LONDON  ·  FoLSM × BMEIS", 13, RGBColor(0xFF, 0x9F, 0xAC),
     bold=True, first=True, sa=10)
para(tf, "Collaboration Hub for AI Deployment\nin Healthcare Research",
     40, WHITE, bold=True, font=SERIF, sa=12, line=1.02)
para(tf, "An interactive matchmaking platform that bridges clinical knowledge "
         "and AI expertise — turning clinical ideas into collaborative, "
         "deployable AI projects.", 16, LIGHT, line=1.25)
# aims strip
aims = [("01", "Lower barriers to entry"), ("02", "Connect clinical & technical expertise"),
        ("03", "Accelerate delivery"), ("04", "Educate & upskill")]
aw = (CW - 3 * 0.25) / 4
for i, (n, label) in enumerate(aims):
    x = MARGIN + i * (aw + 0.25)
    b = rrect(s, x, 5.15, aw, 1.05, NAVY2, line_color=RGBColor(0x2A, 0x40, 0x6E), line_w=1)
    tf = b.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.12)
    para(tf, n, 20, WHITE, bold=True, font=SERIF, first=True, sa=2)
    para(tf, label, 11, LIGHT, line=1.05)
tf = textbox(s, MARGIN, 6.55, CW, 0.6)
para(tf, "Inspired by cross-institution research networks across Oxford & "
         "Cambridge, Imperial and UCL.", 11.5, RGBColor(0x9F, 0xB2, 0xD4),
     italic=True, first=True)

# ===========================================================================
# Slide 2 — The idea
# ===========================================================================
s = add_slide(WHITE)
header(s, "The idea", "Turning clinical needs into collaborative AI projects")
tf = textbox(s, MARGIN, 2.25, CW, 3.5)
para(tf, "The hub unlocks the potential of healthcare research and clinical "
         "data across FoLSM and BMEIS by lowering the barriers to AI "
         "innovation. Clinical partners submit ideas; a multidisciplinary panel "
         "reviews them; and approved projects are published so AI researchers — "
         "from PhD students to academic staff — can browse and collaborate.",
     17, INK, first=True, sa=16, line=1.35)
para(tf, "It also supports hackathons, educational days and technical "
         "consultations for grant applications — a structured framework and an "
         "educational launchpad for the wider King's community.",
     13.5, MUTED, line=1.3)

# ===========================================================================
# Slide 3 — Key aims (2x2 cards)
# ===========================================================================
s = add_slide(WHITE)
header(s, "What we're aiming for", "Four key aims")
aims = [
    ("Lower barriers to entry", "Enable clinicians and researchers with no prior AI experience to pitch ideas and access advanced technical resources."),
    ("Foster cross-disciplinary collaboration", "Connect frontline clinical knowledge (FoLSM) with the technical and deployment expertise within BMEIS."),
    ("Accelerate project delivery", "Move ideas from a simple submission to active, fully-staffed research collaborations or hackathons."),
    ("Drive educational engagement", "Identify skill gaps, host workshops, and help early-career researchers build new skills and networks."),
]
cw2 = (CW - 0.4) / 2
ch2 = 1.9
for i, (t, b) in enumerate(aims):
    x = MARGIN + (i % 2) * (cw2 + 0.4)
    y = 2.25 + (i // 2) * (ch2 + 0.35)
    card(s, x, y, cw2, ch2, t, b)

# ===========================================================================
# Slide 4 — How it works (4-step pipeline)
# ===========================================================================
s = add_slide(WHITE)
header(s, "How it works", "From a clinical idea to a launched project")
steps = [
    ("01", "Idea submission", "Partners submit ideas through a form covering data, ethics, resources and timeline."),
    ("02", "Project review", "A panel meets monthly to score clinical impact, data readiness, resources and AI feasibility."),
    ("03", "Publication", "Approved projects are published for researchers, developers and students to browse."),
    ("04", "Match & launch", "A PI is matched, collaborators join, and the project launches — or becomes a hackathon."),
]
cw4 = (CW - 3 * 0.3) / 4
for i, (n, t, b) in enumerate(steps):
    x = MARGIN + i * (cw4 + 0.3)
    box = rrect(s, x, 2.5, cw4, 2.6, PANEL, line_color=LINE, line_w=1)
    rect(s, x, 2.5, cw4, 0.055, CRIMSON)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.2); tf.margin_right = Inches(0.2); tf.margin_top = Inches(0.2)
    para(tf, n, 22, CRIMSON, bold=True, font=SERIF, first=True, sa=4)
    para(tf, t, 15, NAVY, bold=True, sa=5)
    para(tf, b, 11.5, MUTED, line=1.15)
    if i < 3:
        ar = textbox(s, x + cw4 - 0.02, 3.5, 0.34, 0.5)
        para(ar, "›", 22, LINE, bold=True, first=True, align=PP_ALIGN.CENTER)

# ===========================================================================
# Slide 5 — Review panel
# ===========================================================================
s = add_slide(WHITE)
header(s, "Governance", "The multidisciplinary review panel")
tf = textbox(s, MARGIN, 2.2, CW, 1.0)
para(tf, "A panel of BMEIS AI experts meets monthly to evaluate submissions and "
         "connect proposals with the right PIs and collaborators.",
     16, INK, first=True, line=1.3)
crit = ["Clinical impact", "Data readiness", "Resources needed", "AI feasibility"]
cwc = (CW - 3 * 0.3) / 4
for i, c in enumerate(crit):
    x = MARGIN + i * (cwc + 0.3)
    box = rrect(s, x, 3.35, cwc, 1.0, PANEL, line_color=LINE, line_w=1)
    rect(s, x, 3.35, 0.09, 1.0, CRIMSON)
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.25)
    para(tf, c, 14.5, NAVY, bold=True, first=True)
tf = textbox(s, MARGIN, 4.75, CW, 1.4)
para(tf, "PIs are found by direct contact, from senior researchers who signed "
         "up, or by proposer suggestion; the appointed PI approves the final "
         "team. Complex ideas can be routed into hackathons or workshop days.",
     13, MUTED, first=True, line=1.3)

# ===========================================================================
# Slide 6 — Lifecycle
# ===========================================================================
s = add_slide(WHITE)
header(s, "Project lifecycle", "Five clear stages")
stages = [
    ("Open", "Seeking collaborators & a PI"),
    ("Waiting for PI", "Backlogged for lack of a senior lead"),
    ("Launched", "Joining closed; project starts"),
    ("Ongoing", "Run by PI & proposer"),
    ("Completed", "Outcomes reported & shared"),
]
cw5 = (CW - 4 * 0.25) / 5
for i, (t, b) in enumerate(stages):
    x = MARGIN + i * (cw5 + 0.25)
    box = rrect(s, x, 2.6, cw5, 2.3, PANEL, line_color=LINE, line_w=1)
    # numbered dot
    dot = shape(s, MSO_SHAPE.OVAL, x + cw5 / 2 - 0.16, 2.85, 0.32, 0.32, fill=CRIMSON)
    dtf = dot.text_frame; dtf.word_wrap = False
    para(dtf, str(i + 1), 11, WHITE, bold=True, first=True, align=PP_ALIGN.CENTER)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_top = Inches(0.75); tf.margin_left = Inches(0.14); tf.margin_right = Inches(0.14)
    para(tf, t, 13.5, NAVY, bold=True, first=True, sa=5, align=PP_ALIGN.CENTER)
    para(tf, b, 10.5, MUTED, align=PP_ALIGN.CENTER, line=1.15)
tf = textbox(s, MARGIN, 5.35, CW, 0.9)
para(tf, "Indicative timeline: approval in up to 1 month  ·  open for a PI & "
         "team for ~1 month  ·  projects run for 3–6 months before completion.",
     12.5, MUTED, italic=True, first=True, line=1.3)

# ===========================================================================
# Slide 7 — Project hierarchy
# ===========================================================================
s = add_slide(WHITE)
header(s, "A hierarchy of projects", "Contribute at the scale that fits")
tiers = [
    ("Short-term", "Hackathons — days to weeks", AMBER),
    ("Intermediate", "Proof-of-concept — approximately 3 months", TEAL),
    ("Long-term", "Basis for interdisciplinary grant applications", CRIMSON),
]
for i, (t, b, col) in enumerate(tiers):
    y = 2.4 + i * 0.95
    box = rrect(s, MARGIN, y, CW, 0.8, PANEL, line_color=LINE, line_w=1)
    rect(s, MARGIN, y, 0.12, 0.8, col)
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.35)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = t + "   "
    r.font.size = Pt(16); r.font.bold = True; r.font.name = SANS; r.font.color.rgb = NAVY
    r2 = p.add_run(); r2.text = b
    r2.font.size = Pt(13); r2.font.name = SANS; r2.font.color.rgb = MUTED
tf = textbox(s, MARGIN, 5.4, CW, 0.9)
para(tf, "Allocations are triaged by early-career researchers with support from "
         "professional services — e.g. Tom Foulkes and Tamara Al Janabi.",
     13, MUTED, italic=True, first=True, line=1.3)

# ===========================================================================
# Slide 8 — Longer-term vision
# ===========================================================================
s = add_slide(WHITE)
header(s, "Where this is heading", "A living skills database & public platform")
tf = textbox(s, MARGIN, 2.2, CW, 1.7)
para(tf, "Map the AI-engineering skillset across the faculty and design "
         "meaningful search keywords, so the right collaborators are found in "
         "seconds — with notifications when relevant projects appear, and "
         "profiles that showcase each person's projects and outcomes.",
     16, INK, first=True, line=1.35)
box = rrect(s, MARGIN, 4.15, CW, 1.7, NAVY)
tf = box.text_frame; tf.word_wrap = True
tf.margin_left = Inches(0.35); tf.margin_right = Inches(0.35); tf.margin_top = Inches(0.3)
para(tf, "Knowledge  →  a searchable skills database  →  a public-facing website.",
     18, WHITE, bold=True, font=SERIF, first=True, sa=6)
para(tf, "A structured, discoverable map of who can help with what — across "
         "clinical and technical teams.", 13, LIGHT, line=1.25)

# ===========================================================================
# Slide 9 — Impact & accreditation
# ===========================================================================
s = add_slide(WHITE)
header(s, "Making it work", "Impact & accreditation")
tf = textbox(s, MARGIN, 2.2, CW, 0.9)
para(tf, "For the hub to succeed, people must see genuine credit and impact for "
         "their effort — especially where work leads to papers, products or "
         "spin-outs.", 15.5, INK, first=True, line=1.3)
cards3 = [
    ("Papers & authorship", "Clear, fair recognition of research contributions as projects become publications."),
    ("Products & spin-outs", "Accreditation for work that matures into IP, products or ventures — not just academic output."),
    ("Expert support", "Tom Foulkes and IP advisory teams to guide accreditation, IP and the route to impact."),
]
cw3 = (CW - 2 * 0.3) / 3
for i, (t, b) in enumerate(cards3):
    x = MARGIN + i * (cw3 + 0.3)
    card(s, x, 3.3, cw3, 1.75, t, b)
# quote
rect(s, MARGIN, 5.4, 0.09, 1.0, CRIMSON)
tf = textbox(s, MARGIN + 0.3, 5.4, CW - 0.3, 1.1, anchor=MSO_ANCHOR.MIDDLE)
para(tf, "“Ensuring people see impact for their efforts will be vital if this "
         "is going to work.”", 19, NAVY, italic=True, font=SERIF, first=True, line=1.25)

# ---- save ------------------------------------------------------------------
OUT = "Collaboration_Hub_Overview.pptx"
prs.save(OUT)
print(f"Saved {OUT}  ({len(prs.slides._sldIdLst)} slides)")
