# RELIC // LIVE — 5–7 minute demonstration

Presenters: Bilal Malik — 24P-3061; Aun Anis — 24P-3017.
No individual contribution allocation is implied.

## Preparation

From the repository root, with the existing pinned environment:

```bash
.venv/bin/python tools/create_xray_acceptance_fixture.py /tmp/relic-live-demo.zip
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If the application already runs on port 8000, use that instance. Open
http://127.0.0.1:8000/explore, choose the generated ZIP and **Analyze repository**
(the upload submit control). Wait for Overview. This original project fixture
has five files, five extracted functions, and three genuine C-model outputs.
Do not describe it as a large production repository.

Click **RELIC // LIVE ↗** in the workspace header. Review pre-flight. Enable
**Recording Layout**, then **Launch RELIC // LIVE ↗**. Fullscreen is optional.
Recording Layout produces no video: start OBS or Ubuntu's screen recorder
separately, after reviewing the repository for private contents. Close presenter
notes before recording; they are visible on the same display, not a private
second-monitor channel. Snapshot retention is bounded; refresh/reanalyze before
an expired session, rather than expecting permanent offline storage.

## 0:00–0:45 — Awakening

Say: “Codebase Archaeologist combines source-grounded repository exploration,
relationships and C-function defect-risk estimation. Every repository has a
story; we will follow the evidence in this imported snapshot.”

Click **Begin Investigation →**. No repository is secretly being analyzed during
the opening animation. All facts were produced by the completed import.

## 0:45–1:25 — Intelligence

Point to the real files, functions, languages and dependencies. Explain that
ownership edges are excluded from the displayed dependency count. The language
bars count included files, not lines or prediction coverage. C and Python
structural support does not mean both languages have defect models.

Click **Next →**.

## 1:25–2:35 — Repository Universe

Click **Focus Structure** to frame the largest visible directory constellation.
Drag empty canvas to orbit. Use right-drag or **Pan with left drag** to translate;
scroll to zoom. Click **Reset Camera** to restore the complete bounded graph.

Click **Explore Universe** for the existing guided tour; demonstrate **Pause
tour**, resume with the same control, **Skip scene →**, then **Exit tour**.
Select a real entity. Explain that incoming/outgoing illumination follows
retained static edges; a directory grouping is not an inferred runtime module.
Use **Continue →** to move into X-Ray.

If WebGL is unavailable, the existing **2D Graph** remains interactive. Explain
the rendering fallback without implying the analysis failed.

## 2:35–3:50 — X-Ray

Click **Return to Structure**, then `src`, `review.c`, and `clamp_index`.
Show the breadcrumbs and source ownership. Click **Trace Dependencies**;
explain the displayed relationship type. `DEFINES` is ownership, not an observed
runtime call. To demonstrate actual calls, inspect `entry` and its `CALLS` edge
to `sum_values`.

Click **Locate in Universe ↗** to return with the selected entity preserved.
Return to scene 4 using the scene selector or Next. A Python function has
structural evidence but no C-model score. Click **Next →** for Risk & Time.

## 3:50–5:15 — Risk & Time

Say: “These are existing Random Forest estimates for eligible C functions.
They are research review signals, not confirmed bugs or vulnerabilities. The
production model and its threshold have not changed.”

Cards show up to six scored C functions retained in the graph, ordered by the
actual saved score. This is not a complete repository-wide risk ranking when
the graph is capped. **Investigate in X-Ray ↗** opens the corresponding entity.

Click **Codebase Time Machine**. For the ZIP fixture, explain: “A ZIP contains
files, not Git ancestry. We do not invent commits from archive timestamps.”
Continue without a fabricated timeline.

For a GitHub demonstration instead, import an authorized public repository
before recording and explicitly retrieve its pinned history in the existing
Time Machine workspace. Return to Live in the same tab. Pre-flight should show
cached commits. In the historical panel, select actual commits and inspect
parents, dates and changed files. Only claim a comparison when both revisions
are actually available. Network failure or rate limits are handled by existing
controls; use already cached evidence or explain the gap.

If no eligible C score exists, explain the unavailable state and continue with
structural evidence. Never substitute a Python score or a made-up example.

## 5:15–6:00 — Final reveal

Click **Next →**. Say: “The application brings structural analysis, dependency
visualization and progressive investigation into one workspace. Risk and
history remain bounded by the available evidence.”

Read the actual closing summary and available/unavailable capability labels.
Choose **Restart Presentation** for questions or **Return to Workspace ↗** to
resume ordinary analysis. Neither action closes the application.

## Recovery and controls

- Previous/Next or the scene selector advances immediately; no automatic pacing.
- Arrow keys, Space, Home, End and F work outside interactive instruments/forms.
- Escape exits fullscreen first; a subsequent Escape exits the presentation.
  Within X-Ray, Escape first clears a trace, then exits X-Ray to Universe.
- **Exit** returns to pre-flight and restores launch focus. The pre-flight
  **Return to Workspace ↗** link returns to Overview.
- Reduced motion uses immediate scene changes and final metric values.
- Optional Notes contain technical prompts but will appear in a recording.
- Fullscreen denial is nonfatal; the full-viewport layout still works.
