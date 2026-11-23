# Task7D — demonstration guide

**Bilal Malik —24P-3061; Aun Anis —24P-3017.** No individual roles assigned.
FAST NUCES Peshawar /SE /AI-lab /M. Saad Khan /semester5 /23November,2026.

## Preparation

Follow README's exact runtime setup. Run from the extracted committed source/checkout:

```bash
source .venv/bin/activate
python tools/install_model.py
python tools/release_smoke.py --write-demo /tmp/university-demo.zip
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The smoke really loads the approved model and posts a two-file original educational ZIP.
No dataset/internet/cloud key is required. Input is tests/fixtures/university_demo/review.c
and helpers.py, original unlabeled project fixture code, not a published benchmark or
proof that any sample is actually defective. Do not compile/execute imported files.

## Short browser sequence (record actual PASS/FAIL locally)

1. Open http://127.0.0.1:8000 → **Explore a repository** → ZIP input. Select
   /tmp/university-demo.zip and analyze. Expected:2files,3Cmodel estimates,Python structure
   without C-model predictions. No fabricated progress percentage.
2. Overview:inspect inventory/provenance/coverage. Switch to Structural intelligence and
   Defect risk intelligence; inspect clamp_index,sum_values,entry. Observed smoke scores
   .6446299251/.4640631120/.4411504144 are integration outputs, not accuracy labels.
3. Knowledge explorer:inspect hierarchy/calls and select actual entry→sum_values evidence.
   In2D zoom/pan/fit. In3D only if a verified local bundle is installed:rotate,zoom,enable
   **Pan camera**,drag,then **Reset view**; confirm centering after resize. If absent,show
   the truthful2D fallback. Portable OFFLINE3D is not yet licensed/provenance-complete.
4. Architecture atlas:inspect actual root-file component and relationship evidence.
   Repository heatmaps:switch among metrics,inspect a real tile/unscored distinction.
5. Blast radius explorer:select a real function,depth1,upstream/downstream; inspect actual
   path. Reachability is potential impact,not guaranteed breakage.
6. Jordan Local:ask “Who calls sum_values?” or “Summarize this repository.” Follow real
   entity evidence. Ambiguity should request selection. Do not activate cloud or paste keys.
7. Source ZIP Time Machine must show missing history. For genuine timeline/churn/activity/
   comparison/evolution,import a small public GitHub repository through the real URL flow,
   record the pinnedSHA and fetch history. No internet:explain the history boundary,do not
   show invented commits or claim offline ZIP history. Respect cooldown/errors.
8. Export actual analysis JSON. Navigate between pages without reupload. Reload to restore
   snapshot,then forget/replace it and verify no stale data. Capture real report screenshots
   only after data settles,with provenance per task7c_screenshot_capture_guide.md.

## Recovery

Missing model:verify/install approved files then restart (model failures are cached).
Wrong package versions:use exact runtime lock; do not alter loader compatibility checks.
Storage blocked:use displayed error/unsaved export; avoid private repositories in shared
browser profiles. Network/quota failure:keep already loaded evidence and retry only after
reported cooldown.3Dmissing:use2D; don't hide fallback. Broken ZIP:show safe rejection.

## Scientific explanation for evaluator

Inputs are11Csyntax/size features; RF estimates uncalibrated label-related scores.
Selection used validation F1 among3original candidates. OnlyRF has the historical exposed
final-test evaluation. Modest F1/AUC,always-positive F1,clone/dependence and threshold
tradeoffs are openly reported. Explain why optimization retainedRF rather than claiming
an improvement. Show saved comparison JSON/academic tables separately from demo scores.
