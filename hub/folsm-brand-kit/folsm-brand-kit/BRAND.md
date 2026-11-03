# FoLSM AI Collaboration Hub — Brand Guide

Instructions for anyone (including Claude Code) building with the FoLSM AI Collaboration Hub identity.

## The logo

The mark is a navy **F** drawn as connected nodes, sitting in front of a soft grey **H** (for *Hub*), also drawn with nodes. The F's middle arm reaches into the H's crossbar, and the **crimson node** marks the point where FoLSM meets the Hub.

| File | Use |
|---|---|
| `folsm-logo-horizontal.svg` | Primary logo: mark + the full name, "FoLSM" over "AI Collaboration Hub". Site header, documents. |
| `folsm-mark.svg` | Mark only, on white or light grey backgrounds. |
| `folsm-mark-on-dark.svg` | Mark only, on navy or other dark backgrounds. |
| `folsm-favicon.svg` | Favicon and anything under ~48px. The H is dropped so it stays legible. |

The horizontal logo's text uses the **Manrope** font, so pages using it must load Manrope (see below). For print or apps that can't load web fonts, convert the text to outlines first.

### Usage rules
- Keep clear space around the logo of at least the height of the crimson node.
- Minimum size: full mark 40px tall; below that use `folsm-favicon.svg`.
- Don't recolour the nodes, stretch the logo, add shadows or gradients, or place the light version on busy photos.
- On navy backgrounds always use the `-on-dark` version.

## Colours

```css
:root {
  --folsm-navy:        #14234A; /* primary: text, F of the mark, dark backgrounds */
  --folsm-crimson:     #B3123A; /* accent: the hub node, buttons, highlights, banner rule */
  --folsm-grey:        #C9CDD4; /* the H, borders, dividers */
  --folsm-grey-dark:   #5B6270; /* secondary text, taglines */
  --folsm-grey-light:  #EEF0F3; /* section backgrounds, cards */
  --folsm-navy-muted:  #4A5573; /* the H on navy backgrounds */
  --folsm-white:       #FFFFFF;
}
```

- Navy is the main colour; crimson is used sparingly as the accent.
- White text on navy or crimson passes contrast. Don't put crimson text on navy (too low contrast).
- These colours were matched to the website by eye — swap in the site's exact values if they differ.

## Typography

- **Manrope** (Google Fonts), weights 600 and 800.
- The name is always **"FoLSM AI Collaboration Hub"**: "AI Collaboration Hub" is part of the name, not a tagline. In the logo, "FoLSM" is set in 800 and "AI Collaboration Hub" in 700 at just over half its size, both in navy.
- Headings: 800, slightly tight letter-spacing (about -0.02em).
- Small labels: 600, uppercase, wide letter-spacing (about 0.22em).

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;800&display=swap">
```

## Quick start for a website

```html
<link rel="icon" type="image/svg+xml" href="/brand/folsm-favicon.svg">

<header class="site-header">
  <a href="/" aria-label="FoLSM AI Collaboration Hub home">
    <img src="/brand/folsm-logo-horizontal.svg" alt="FoLSM AI Collaboration Hub" height="56">
  </a>
</header>
```

## Newsletter banner

A 1200×300 email header (displays at 600×150) is on the design canvas: navy background, the on-dark logo on the left, issue title and date on the right, and a crimson rule along the bottom. Export it as a PNG from the canvas for each issue.
