# Task7B — Dependency Relic brand system

## Approved direction and actual reference

The user supplied a three-concept reference image during this task and explicitly
selected the **left-hand Minimalist Relic**. The implementation follows that direction:
a distinctive angular shard, sparse horizontal code inscriptions, a broken right
seam and a small branching node network. It deliberately omits the central concept's
stone textures, glow and ornamental frame. This is custom editable vector geometry,
not a pixel-perfect image trace. The supplied reference itself is not redistributed.

Palette: graphite `#0B0C0E`, ivory `#E6DDD1`, garnet `#7A1E2B`. Existing application
colors/type remain unchanged. Garnet is ornamental rather than body-text color: its
contrast against graphite is insufficient for small instructional text. Critical
wordmarks/labels use ivory or graphite; tiny marks use ivory branches for visibility.

## Implemented assets

All under `app/static/brand/`:

- `relic-dark.svg`: transparent ivory/garnet mark for dark surfaces.
- `relic-light.svg`: transparent graphite/garnet mark for light surfaces.
- `logo-dark.svg`, `logo-light.svg`: horizontal two-line serif wordmarks with symbol.
- `relic-small.svg`: simplified, fewer inscriptions/nodes, monochrome light linework.
- `favicon.svg`: simplified mark with opaque graphite background for either browser theme.
- `touch-icon.svg`, `apple-touch-icon.png`: app/touch icon source and180×180 output.
- `app/static/mark.svg`: backward-compatible previous URL, now the full relic mark.

`tools/generate_relic_assets.py` reproducibly authors the SVGs. Wordmark glyphs are
outlined from the existing local Noto Serif Display regular/italic WOFFs. Their SIL
Open Font License/attribution is retained in `app/static/product/fonts/OFL.txt`.
No remote font, stock icon, external image or new runtime dependency is used.
Regenerate with `.venv/bin/python tools/generate_relic_assets.py`; PNG generation:

```bash
rsvg-convert -w 180 -h 180 app/static/brand/touch-icon.svg \
  -o app/static/brand/apple-touch-icon.png
```

FontTools/librsvg are asset-generation tools, not application prerequisites.

## Integration and accessibility

Public navigation (landing/import) and the common nine-workspace shell use the full
mark with existing readable live-text brand names. Images have explicit dimensions,
empty alt text beside the same live name (avoids duplicate announcements), and SVGs
have their own accessible titles when opened directly. Both shells declare the SVG
favicon and touch PNG. The landing composition and motion are preserved, without
adding splash screens or repeating logos inside every instrument.

Assets have no scripts, embedded HTML, external URLs, font fetches or animation.
Static route/XML tests verify the complete system. Actual librsvg/Pillow composite
review inspected dark/light wordmarks and16/32/64px icons; this is asset inspection,
**not browser/nav responsiveness acceptance**. Browser startup remains blocked in
this sandbox. Reference size16 remains intentionally simple, not a detailed illustration.

## Originality and legal limits

No other company's symbol was traced or imported. A limited public web search for
“Codebase Archaeologist logo” and “dependency relic logo” found other uses of the
product name, including [codebasearc.com](https://codebasearc.com/) and
[sohappie/codebase-archaeologist](https://github.com/sohappie/codebase-archaeologist).
This is evidence **against claiming exclusive ownership of the name**, not a finding
of infringement. No reliable visual-similarity/trademark-registry clearance was
completed; originality in construction is not legal exclusivity. Trademark/name and
visual clearance remain unverified; obtain qualified review before commercial use.
The user's reference provenance/rights have not been independently established.
