# Task7E real Chromium acceptance

Browser157.0.8103.79, sandboxed headless on active Wayland Linux host; native Node26 CDP
with temporary profile, existing app127.0.0.1:8000. No automation framework, --no-sandbox,
unsafe SwiftShader or user's browser profile. Browser HTTP cache was disabled on QA
connections after finding older scripts cached during development; application GitHub
caches were preserved. Exact machine results:reports/release/task7e/browser.json.

Observed actual ZIP upload, Overview2files/24lines/4functions, Risk3real C estimates and
Python unscored, Structure, local3D meshes/edges, pointer orbit/pan/zoom/reset, selected
inspector, Architecture, Heatmaps, Blast Radius, Jordan Local, ZIP no-history, export and
snapshot navigation. Additional original3-directory fixture gives3components/2aggregate
cross-component edges, a real heatmap-cell hover/click and browser-downloaded JSON.
Jordan answered structural complexity with correct4functions/E1–E4 references. Local
answers continued with browser networking emulated offline; no fake server request is
implied for deterministic client-side local handling.

Live GitHub:octocat/Hello-World pinned7fd1a60b01f91b314f59955a4e4d4e80d8edf11d;
3authentic retained commits,1historical path,1merge. Retrieved actual tree and comparison
553c2077…→7fd1a60…:1modified README,1addition/1deletion. Timeline zoom, pointer pan,
Fit History and commit selection exercised. First pan probe hit outside the SVG because
headless fullscreen changed viewport and scroll had not settled; repeat with explicit
viewport and instant scroll passed. No fake Git records or durable patches are stored.

28actual overflow checks:7workspaces at1440/1024/768/390width,900height; all page widths
within viewport. At reduced-motion emulation, Overview had zero running animations and
final real data immediately. Keyboard Tab produced focus; no full WCAG/screen-reader or
physical-touch audit is claimed. Additional screenshots use1440×1200/1440×1000.

Uncaught JS exceptions:none in captured workflow. Browser emitted automatic software-
WebGL deprecation and capture-time ReadPixels stall warnings; no unsafe flag was used.
Rendered controls work, but hardware GPU/FPS, sustained large-repository performance,
all assistive technology and Microsoft Word are not certified by these tests.

Camera race found:Focus450ms could finish after Fit340ms and reclip nodes. Adapter now
owns one cancelable RAF camera transition; later requests/user controls win. Regression
harness and fresh browser rendering verify bounded retained nodes after immediate Focus/Fit.

Reproduce:run app,generate /tmp/university-demo.zip with release_smoke.py,launch Chromium
with a new temporary profile and --headless --remote-debugging-port=9224. Import demo at
/explore in that dedicated CDP tab,then `node tools/browser_acceptance.mjs`. Capture is
in /tmp; curated report captures/provenance are separate. BASE_URL/CHROME_DEBUG_URL can
point this maintainer tool at an isolated localhost test server/profile. Do not attach it
to a personal browser or private repository. `tools/create_acceptance_fixture.py` creates
the additional dependency fixture. Close only this dedicated Chromium when finished.
