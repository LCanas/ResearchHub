"""Brand images for emails, drawn from the FoLSM brand kit (hub/folsm-brand-kit).

Email programs don't show SVG, so the horizontal logo and the newsletter banner
are drawn here as PNGs with Pillow: the mark is the same lines and circles as
folsm-mark.svg, and the text uses Manrope (hub/static/fonts, SIL Open Font
Licence), as the brand guide asks.
"""
import io
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

NAVY = (20, 35, 74)          # --folsm-navy    #14234A
CRIMSON = (179, 18, 58)      # --folsm-crimson #B3123A
GREY = (201, 205, 212)       # --folsm-grey    #C9CDD4
GREY_DARK = (91, 98, 112)    # --folsm-grey-dark #5B6270
DIVIDER = (138, 144, 153)    # #8A9099 (the rule in the horizontal logo)
WHITE = (255, 255, 255)

_FONT = os.path.join(os.path.dirname(__file__), "static", "fonts", "Manrope-VariableFont_wght.ttf")


def _font(size, weight):
    f = ImageFont.truetype(_FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:       # Pillow/FreeType without variable-font support
        pass
    return f


def _text(draw, xy, text, font, fill, spacing=0.0):
    """Draw text with extra letter-spacing (in pixels), as the brand uses."""
    x, y = xy
    if not spacing:
        draw.text((x, y), text, font=font, fill=fill)
        return x + draw.textlength(text, font=font)
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + spacing
    return x - spacing


def _mark(draw, ox, oy, s):
    """folsm-mark.svg (viewBox 120x120) at offset (ox, oy), scale s."""
    def line(x1, y1, x2, y2, w, colour):
        draw.line([(ox + x1 * s, oy + y1 * s), (ox + x2 * s, oy + y2 * s)], fill=colour, width=round(w * s))

    def dot(cx, cy, r, colour):
        draw.ellipse([ox + (cx - r) * s, oy + (cy - r) * s, ox + (cx + r) * s, oy + (cy + r) * s], fill=colour)

    for x1, y1, x2, y2 in ((58, 14, 58, 106), (104, 14, 104, 106), (58, 60, 104, 60)):
        line(x1, y1, x2, y2, 10, GREY)
    for cx, cy in ((58, 14), (104, 14), (58, 106), (104, 106), (104, 60)):
        dot(cx, cy, 10, GREY)
        # round line ends, like stroke-linecap="round"
    for x1, y1, x2, y2 in ((22, 25, 22, 95), (22, 25, 82, 25), (22, 60, 64, 60)):
        line(x1, y1, x2, y2, 9, NAVY)
    for cx, cy in ((22, 25), (82, 25), (22, 95), (22, 60)):
        dot(cx, cy, 11, NAVY)
    dot(66, 60, 11, CRIMSON)


def _horizontal_logo(draw, ox, oy, s):
    """folsm-logo-horizontal.svg (viewBox 560x132) at (ox, oy), scale s:
    the mark, a thin rule, then "FoLSM" over "AI Collaboration Hub", both navy
    (the full name: "AI Collaboration Hub" is part of it, not a tagline)."""
    _mark(draw, ox, oy, 1.1 * s)
    draw.rectangle([ox + 160 * s, oy + 14 * s, ox + 162 * s, oy + 118 * s], fill=DIVIDER)
    # SVG text y is the baseline; Pillow's "ls" anchor draws from the baseline.
    for text, x, y, size, weight, tracking in (("FoLSM", 186, 70, 58, 800, -1.5),
                                                ("AI Collaboration Hub", 188, 110, 31, 700, -0.3)):
        font = _font(round(size * s), weight)
        cx = ox + x * s
        for ch in text:
            draw.text((cx, oy + y * s), ch, font=font, fill=NAVY, anchor="ls")
            cx += draw.textlength(ch, font=font) + tracking * s


def _png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


@lru_cache(maxsize=1)
def email_logo_png():
    """The horizontal logo on white, for the top of every email
    (1120x264 px, shown at 280x66)."""
    s = 2
    img = Image.new("RGB", (560 * s, 132 * s), WHITE)
    _horizontal_logo(ImageDraw.Draw(img), 0, 0, s)
    return _png(img)


@lru_cache(maxsize=32)
def newsletter_banner_png(number, month):
    """1200x300 newsletter header (shown at 600x150): the horizontal logo on
    the left, "Issue N" and the month on the right, a crimson rule below.
    ``number`` may be None (no issue number, e.g. a preview)."""
    w, h = 1200, 300
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    s = 1.42                                   # logo ~795x187
    _horizontal_logo(d, 60, (h - 12 - 132 * s) / 2, s)

    right = w - 64
    label = _font(24, 600)
    big = _font(64, 800)
    sub = _font(30, 600)
    top = 82
    newsletter = "NEWSLETTER"
    lw = sum(d.textlength(c, font=label) + 5 for c in newsletter) - 5
    _text(d, (right - lw, top), newsletter, label, CRIMSON, spacing=5)
    title = f"Issue {number}" if number else "Monthly update"
    d.text((right, top + 40), title, font=big, fill=NAVY, anchor="ra")
    d.text((right, top + 120), month, font=sub, fill=GREY_DARK, anchor="ra")

    d.rectangle([0, h - 12, w, h], fill=CRIMSON)
    return _png(img)
