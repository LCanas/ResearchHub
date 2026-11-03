"""Render the video's final scene (the QR call-to-action) as a slide.

Outputs:
  end_card.png                     — 2560x1440 image (drop into any deck)
  Collaboration_Hub_QR_slide.pptx  — one 16:9 slide containing it

Run:  python make_end_slide.py
"""
import os

from PIL import Image, ImageDraw, ImageFont
import qrcode
from pptx import Presentation
from pptx.util import Inches

# Where the QR should point (matches make_video.py). Change if you deploy elsewhere.
APP_URL = "https://collab-hub-0bz7.onrender.com"

S = 2                       # render scale: 2 -> 2560x1440 (crisp)
W, H = 1280 * S, 720 * S
NAVY = (10, 31, 68)
CRIMSON = (200, 16, 46)
PINK = (255, 159, 172)
LIGHT = (205, 216, 236)
WHITE = (255, 255, 255)
FDIR = "C:/Windows/Fonts/"


def P(v):
    return int(v * S)


def FT(names, base):
    for n in names:
        p = os.path.join(FDIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, int(base * S))
    return ImageFont.load_default()


def f_title(s): return FT(["georgiab.ttf", "georgia.ttf", "arialbd.ttf"], s)
def f_semi(s):  return FT(["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"], s)
def f_reg(s):   return FT(["segoeui.ttf", "arial.ttf"], s)


def brand_mark(d, x, y, size):
    x, y, s = P(x), P(y), P(size)
    d.rounded_rectangle([x, y, x + s, y + s], radius=P(12), fill=CRIMSON)
    ff = f_title(size * 0.5)
    tw = d.textlength("CH", font=ff)
    d.text((x + (s - tw) / 2, y + s * 0.20), "CH", font=ff, fill=WHITE)


def make_qr(data):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=NAVY, back_color=WHITE).convert("RGB")


def render():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, P(8)], fill=CRIMSON)
    brand_mark(d, 90, 84, 52)
    d.text((P(156), P(90)), "Collaboration Hub", font=f_title(38), fill=WHITE)
    d.text((P(158), P(142)), "AI Deployment in Healthcare Research", font=f_reg(19), fill=LIGHT)
    d.text((P(92), P(250)), "Try it yourself", font=f_title(42), fill=WHITE)
    d.text((P(94), P(332)), "Scan the code to open the app and", font=f_reg(23), fill=LIGHT)
    d.text((P(94), P(366)), "create your own researcher profile.", font=f_reg(23), fill=LIGHT)
    d.text((P(94), P(442)), "Or sign in with the demo account:", font=f_reg(22), fill=LIGHT)
    d.text((P(94), P(482)), "s.cooper@kcl.ac.uk", font=f_semi(25), fill=PINK)
    d.text((P(94), P(518)), "password123", font=f_semi(25), fill=PINK)

    qs = P(250)
    qr = make_qr(APP_URL + "/register").resize((qs, qs))
    px, py = P(902), P(240)
    d.rounded_rectangle([px - P(26), py - P(26), px + qs + P(26), py + qs + P(68)],
                        radius=P(18), fill=WHITE + (255,))
    img.paste(qr, (px, py))
    d2 = ImageDraw.Draw(img)
    t = "Scan to get started"
    d2.text((px + (qs - d2.textlength(t, font=f_semi(19))) / 2, py + qs + P(22)),
            t, font=f_semi(19), fill=NAVY)

    img.save("end_card.png")
    print("Saved end_card.png", img.size)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture("end_card.png", 0, 0,
                         width=prs.slide_width, height=prs.slide_height)
    prs.save("Collaboration_Hub_QR_slide.pptx")
    print("Saved Collaboration_Hub_QR_slide.pptx")


if __name__ == "__main__":
    render()
