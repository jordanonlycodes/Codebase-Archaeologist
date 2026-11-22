# Authentic product screenshots

No application screenshots are committed yet. Chromium failed before rendering with
`setsockopt: Operation not permitted` (exit 133); Firefox headless also exited 139.
The README hero is explicitly brand artwork, not a substitute screenshot.

Capture locally from the running application after analysis of a real, shareable
repository. Do not publish private filenames, commit identifiers or sensitive labels.

1. Start `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
2. Open `http://127.0.0.1:8000/` at 1366×768 and capture `landing.png`.
3. Import a small C/Python repository at `/explore`; use its actual analysis for all
   following screenshots, preserving the browser tab/workspace state.
4. Capture `overview.png`, `structure.png`, `risk.png` (with actual scored C functions,
   or explicitly show model unavailable), `graph-2d.png`, `graph-3d.png` (only genuine
   WebGL), `architecture.png`, `heatmaps.png`, `blast-radius.png`.
5. In graph/architecture/impact views select a real entity and show source evidence.
6. Repeat key pages at 390×844 and tablet width. Check long paths, keyboard focus,
   toolbars, reduced motion, scrolling and console errors.
7. Crop only browser chrome, never remove coverage/uncertainty labels to imply better
   results. Record browser, dimensions, fixture/repository and capture date here.
8. Add only authentic images and update README links after checking files exist.

Do not generate mockups, invented metrics, placeholder screenshots or a fake 3D view.
Visual application verification remains outstanding until these captures are performed.
