# Task7D — final university compliance matrix

> Historical Task7D record. Current resolution: [Task7E](task7e_release_validation.md). Original findings below are retained as dated evidence.
Original AI Project Requirements.pdf was read in Task7C; its hash/source are in the
report evidence matrix. Statuses below do not substitute extra product features for
academic criteria. Group permission and new academic fields are explicit user confirmations.

| Criterion | Status | Evidence / limit |
|---|---|---|
|Problem definition|PASS|ReportCh1–2, README, actual repository/model output contracts.|
|Dataset/source|PASS|Pinned CodeXGLUE/Devign manifest/card/Parquet validation and source link.|
|Features/labels|PASS|11numeric features, bool target, no origin/label predictors; C-only.|
|Missingness/duplicates/splits|PASS|113development removals,54conflict groups, train-only median/LRscaling, official splits; clone/dependence limits preserved.|
|Categorical encoding|NOT APPLICABLE|No categorical predictors; target conversion is separate.|
|Tree feature scaling|NOT APPLICABLE|Tree thresholds do not require LR-style scaling.|
|EDA|PASS|Actual saved development distributions, correlations and observations, not app heatmaps.|
|Multiple model training/evaluation|PARTIAL|3original families train/validation-evaluated; only selectedRF has historical final-test evaluation. Four families in bounded optimization. Literal test-each-final-holdout interpretation requires instructor clarification; no retroactive tuning.|
|Comparison/selection/understanding|PASS|Saved metrics; RF original validation-F1 selection; controlled gate/retention and always-positive caveat. No excellent/generalized-vulnerability claim.|
|Model-integrated app|PASS automated/PARTIAL manual|Packaged exactRF loads in isolated minimal venv/clean source and returns genuine C estimates; Python unscored. Physical browser/demo remains pending.|
|GitHub source delivery|PARTIAL|Origin URL valid; normal push attempted, remote release equality must be verified. Clean source archive is offline fallback, not false remote publication.|
|Academic report|PARTIAL|Word/PDF valid, academic fields now confirmed; screenshots/Office layout remain pending.|
|Demonstration|PARTIAL|Real deterministic ZIP/API smoke passes; current human-reviewed live demo and history require local browser/network.|
|Two-member permission/identity|PASS user-confirmed|Bilal Malik24P-3061 and Aun Anis24P-3017; instructor permits two, no invented certificate/roles.|

Model remains RF devign-v1-4a23cc304ca8,11features,score>=0.5. Historical exposed-test
F1 .526316/AUC .587354; newoptimization did not justify deployment improvement. Always-
positive validation F1 .606092 has zero specificity; diagnostic794rows are not independent.
No new test-set selection, raw data relabeling or model retraining occurs in release work.
