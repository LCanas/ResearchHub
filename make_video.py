"""Record a walkthrough video of the Collaboration Hub.

Drives the running app in headless Chromium, captures FULL pages (panning
through anything taller than the frame so nothing is cut), demonstrates
creating a project, contrasts a project-lead view with an ordinary-user view,
and ends on a QR code for viewers to try it / create their own profile.

Prereqs: playwright(+chromium), imageio, imageio-ffmpeg, numpy, Pillow, qrcode.
The dev server must be running on http://127.0.0.1:5000.

Run:   python make_video.py   ->  collaboration_hub_demo.mp4
"""
import io
import os

import numpy as np
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
# Where a viewer's phone should go when they scan the QR on the end card.
# Change to your deployed URL once the app is live.
APP_URL = "https://collab-hub-0bz7.onrender.com"

W, H, FPS = 1280, 720, 30
CONTENT_H, BAR_H = 630, 90          # page area + lower-third caption bar
NAVY = (10, 31, 68)
CRIMSON = (200, 16, 46)
PINK = (255, 159, 172)
LIGHT = (205, 216, 236)
WHITE = (255, 255, 255)
FDIR = "C:/Windows/Fonts/"
OUT = "collaboration_hub_demo.mp4"


# ---- fonts -----------------------------------------------------------------
def font(names, size):
    for n in names:
        p = os.path.join(FDIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def f_title(s): return font(["georgiab.ttf", "georgia.ttf", "arialbd.ttf"], s)
def f_semi(s):  return font(["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"], s)
def f_reg(s):   return font(["segoeui.ttf", "arial.ttf"], s)


# ---- drawing helpers -------------------------------------------------------
def brand_mark(d, x, y, s=54):
    d.rounded_rectangle([x, y, x + s, y + s], radius=12, fill=CRIMSON)
    ff = f_title(int(s * 0.5))
    tw = d.textlength("CH", font=ff)
    d.text((x + (s - tw) / 2, y + s * 0.20), "CH", font=ff, fill=WHITE)


def make_bar(title, sub):
    bar = Image.new("RGB", (W, BAR_H), NAVY)
    d = ImageDraw.Draw(bar)
    d.rectangle([0, 0, W, 3], fill=CRIMSON)
    d.rounded_rectangle([40, 24, 47, 66], radius=3, fill=CRIMSON)
    d.text((62, 18), title, font=f_semi(28), fill=WHITE)
    d.text((62, 54), sub, font=f_reg(18), fill=LIGHT)
    return bar


def compose(content, bar):
    canvas = Image.new("RGB", (W, H), NAVY)
    canvas.paste(content, (0, 0))
    canvas.paste(bar, (0, CONTENT_H))
    return np.asarray(canvas)


def make_qr(data):
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=(10, 31, 68), back_color=(255, 255, 255)).convert("RGB")


# ---- scene generators (streamed, low memory) -------------------------------
def title_scene():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(230):
        d.line([(0, i), (W, i)], fill=(200, 16, 46, int(70 * (1 - i / 230))))
    d.rectangle([0, 0, W, 8], fill=CRIMSON)
    brand_mark(d, 96, 150, 60)
    d.text((172, 158), "KING'S COLLEGE LONDON", font=f_semi(20), fill=PINK)
    d.text((172, 188), "FoLSM × BMEIS", font=f_reg(18), fill=LIGHT)
    d.text((92, 262), "Collaboration Hub", font=f_title(76), fill=WHITE)
    d.text((96, 372), "AI Deployment in Healthcare Research", font=f_reg(32), fill=LIGHT)
    d.text((96, 452), "A matchmaking platform connecting clinical need with AI expertise.",
           font=f_reg(21), fill=(150, 170, 205))
    arr = np.asarray(img)

    def gen():
        for _ in range(int(2.9 * FPS)):
            yield arr
    return gen


def end_scene():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 8], fill=CRIMSON)
    brand_mark(d, 90, 84, 52)
    d.text((156, 90), "Collaboration Hub", font=f_title(38), fill=WHITE)
    d.text((158, 142), "AI Deployment in Healthcare Research", font=f_reg(19), fill=LIGHT)
    d.text((92, 250), "Try it yourself", font=f_title(42), fill=WHITE)
    d.text((94, 332), "Scan the code to open the app and", font=f_reg(23), fill=LIGHT)
    d.text((94, 366), "create your own researcher profile.", font=f_reg(23), fill=LIGHT)
    d.text((94, 442), "Or sign in with the demo account:", font=f_reg(22), fill=LIGHT)
    d.text((94, 482), "s.cooper@kcl.ac.uk", font=f_semi(25), fill=PINK)
    d.text((94, 518), "password123", font=f_semi(25), fill=PINK)
    qs = 250
    qr = make_qr(APP_URL + "/register").resize((qs, qs))
    px, py = 902, 240
    d.rounded_rectangle([px - 26, py - 26, px + qs + 26, py + qs + 68], radius=18, fill=WHITE + (255,))
    img.paste(qr, (px, py))
    d2 = ImageDraw.Draw(img)
    t = "Scan to get started"
    d2.text((px + (qs - d2.textlength(t, font=f_semi(19))) / 2, py + qs + 22),
            t, font=f_semi(19), fill=NAVY)
    arr = np.asarray(img)

    def gen():
        for _ in range(int(3.6 * FPS)):
            yield arr
    return gen


def page_scene(full_img, title, sub):
    if full_img.width != W:
        full_img = full_img.resize((W, round(full_img.height * W / full_img.width)))
    bar = make_bar(title, sub)
    ph = full_img.height

    def gen():
        if ph <= CONTENT_H:
            base = Image.new("RGB", (W, CONTENT_H), NAVY)
            base.paste(full_img, (0, 0))
            frame = compose(base, bar)
            for _ in range(int(2.7 * FPS)):
                yield frame
        else:
            max_off = ph - CONTENT_H
            split = int(max_off * 0.66)          # boundary: top ~2/3 vs bottom ~1/3
            top_hold = int(0.35 * FPS)
            bot_hold = int(0.08 * FPS)            # barely pause at the bottom
            # slow, readable scroll through the top two-thirds…
            slow_n = min(int(4.2 * FPS), max(int(1.4 * FPS), split // 7))
            # …then move through the bottom third quickly.
            fast_n = max(int(0.4 * FPS), (max_off - split) // 30)

            def offsets():
                for _ in range(top_hold):
                    yield 0
                for i in range(1, slow_n + 1):
                    yield int(split * i / slow_n)
                for i in range(1, fast_n + 1):
                    yield split + int((max_off - split) * i / fast_n)
                for _ in range(bot_hold):
                    yield max_off

            for off in offsets():
                yield compose(full_img.crop((0, off, W, off + CONTENT_H)), bar)
    return gen


def render(factories):
    fade = int(0.45 * FPS)
    w = imageio.get_writer(OUT, fps=FPS, quality=8, macro_block_size=16)
    prev_last = None
    for factory in factories:
        g = factory()
        first = next(g)
        if prev_last is not None:
            pf = prev_last.astype(np.float32)
            ff = first.astype(np.float32)
            for k in range(fade):
                a = (k + 1) / fade
                w.append_data((pf * (1 - a) + ff * a).astype(np.uint8))
        w.append_data(first)
        last = first
        for fr in g:
            w.append_data(fr)
            last = fr
        prev_last = last
    w.close()


# ---- capture ---------------------------------------------------------------
def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")


def login(pg, email):
    pg.goto(BASE + "/logout")
    pg.goto(BASE + "/login", wait_until="networkidle")
    pg.fill('input[name="email"]', email)
    pg.fill('input[name="password"]', "password123")
    pg.click('button[type="submit"]')
    pg.wait_for_load_state("networkidle")


def capture():
    scenes = []   # list of (full_img, title, sub) in narrative order
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": W, "height": 820})
        pg = ctx.new_page()

        # --- Login screen (shown in the video, credentials pre-filled) ---
        pg.goto(BASE + "/login", wait_until="networkidle")
        pg.fill('input[name="email"]', "s.cooper@kcl.ac.uk")
        pg.fill('input[name="password"]', "password123")
        pg.wait_for_timeout(500)
        scenes.append((shot(pg), "Sign in", "Researchers sign in to the hub"))
        pg.click('button[type="submit"]')
        pg.wait_for_load_state("networkidle")

        tour = [
            ("/",            "Home",        "Dashboard — news, events & open calls", 3000),
            ("/projects",    "Projects",    "Browse & filter across the lifecycle", 1400),
            ("/workstreams", "Workstreams", "Research themes that organise the hub", 1400),
            ("/directory",   "People",      "Find collaborators by expertise & availability", 1400),
            ("/impact",      "Impact",      "Completed projects and their outcomes", 1400),
            ("/about",       "About",       "Mission, how it works & the review panel", 1400),
        ]
        for path, t, s, wait in tour:
            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(wait)
            scenes.append((shot(pg), t, s))

        # --- Create a project ---
        pg.goto(BASE + "/projects/new", wait_until="networkidle")
        pg.wait_for_timeout(500)
        scenes.append((shot(pg), "Create a project", "Open the ‘Propose a project’ form"))
        pg.fill('input[name="title"]', "AI triage for emergency chest X-rays")
        pg.fill('input[name="summary"]', "Prioritise urgent findings on the ED worklist.")
        pg.fill('textarea[name="description"]',
                "A proof-of-concept to triage chest X-rays in the emergency department, "
                "flagging urgent findings for faster review. Seeking imaging and "
                "evaluation collaborators.")
        pg.select_option('select[name="status"]', "Open")
        pg.select_option('select[name="project_type"]', "Proof of Concept")
        pg.select_option('select[name="workstream"]', "Medical Imaging AI")
        pg.fill('input[name="keywords"]', "radiology, triage, chest X-ray, evaluation")
        pg.fill('textarea[name="expected_outcomes"]',
                "A validated triage prototype and a plan for a silent trial.")
        pg.wait_for_timeout(400)
        scenes.append((shot(pg), "Create a project", "Fill in the details, then submit"))
        pg.click('button:has-text("Create project")')
        pg.wait_for_load_state("networkidle")
        pg.wait_for_timeout(600)
        scenes.append((shot(pg), "Create a project", "…and it's published to the hub"))

        # --- Lead view (admin / PI can manage) of an Open project with requests ---
        pg.goto(BASE + "/projects/2", wait_until="networkidle")
        pg.wait_for_timeout(700)
        scenes.append((shot(pg), "As a project lead",
                       "Edit, manage the roadmap & review join requests"))

        # --- Ordinary-user view of the SAME project ---
        login(pg, "s.bloom@kcl.ac.uk")     # Stuart — not a manager of project 2
        pg.goto(BASE + "/projects/2", wait_until="networkidle")
        pg.wait_for_timeout(700)
        scenes.append((shot(pg), "As a collaborator",
                       "No admin controls — just ‘express interest’ to join"))

        b.close()
    return scenes


def main():
    print("Capturing pages…")
    scenes = capture()
    factories = [title_scene()]
    factories += [page_scene(img, t, s) for (img, t, s) in scenes]
    factories += [end_scene()]
    print(f"Rendering {len(factories)} scenes -> {OUT}")
    render(factories)
    print(f"Done: {OUT}")


if __name__ == "__main__":
    main()
