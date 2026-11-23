# Task7C.0 — dataset quality and leakage diagnostics

Preserved raw and official split identities. Historical exact/normalized-source cleaning
removed113development rows:54conflicting-label groups quarantined, plus exact evaluation
source matches; full overlapping reasons in reports/ml/cleaning_audit.json. No official
test row changed. Raw/prepared inputs and prior evaluation artifacts are unchanged.
Missing/invalid source and label counts are in that genuine audit; no missing labels
were synthesized.4029training and463validation structural-feature rows remain NaN and
are imputed inside each fitted training fold, not deleted as difficult examples.
No categorical model inputs exist; metadata is excluded. Imbalance is mild (45.81%
positive training,43.48%validation); weighted/unweighted models are compared without
resampling validation/test. Numeric feature distributions/EDA remain in reports/ml.

## Fresh source-only clone/group audit

Reproduce: `PYTHONPATH=. .venv/bin/python tools/audit_optimization_data.py`.
Measured25.69seconds on this environment. Tracked machine-readable output:
reports/ml/optimization/task7c0-v1/dataset_quality.json . No test labels loaded.

C lexical token **shape** normalizes identifiers/numeric/string literals while retaining
keywords/operators and ignoring comments. This is deliberately conservative: different
semantics can have the same shape; it is not proof of label mistakes or literal copies.
Training has1132shape duplicate excess rows; validation33, test-source24.233validation
and227test-source rows share a training token shape. Exact normalized-source overlap
remains zero under the original cleaned policy; these are additional similarity risks.

Near-match retrieval uses bottom24five-token-shingle hashes, skips postings>64 and
checks at most50candidates/query with exact shingle Jaccard>=.85. At least554validation
and544test-source rows have verified matches to training. These are **lower bounds**:
common postings are omitted,1937/1932queries have capped candidate lists. The similarity
measure is lexical, not semantic or a compiler equivalence test. Only20hashed-index
pair examples per query split are retained, no function bodies. No all-pairs search.

1816validation rows share a project+commit pair with training. A predeclared, source-only
validation diagnostic mask excludes these, shared shapes and confirmed near matches:
**794retained /1929excluded**, with overlapping reasons1816/233/554. No evaluation
labels selected the exclusions. This is a separate conservative diagnostic subset,
not a rewritten official benchmark or new independent dataset; it still shares projects
and can contain missed clones. Do not present its numbers as directly interchangeable
with the2723-row validation scores. Test-source similarities are descriptive only and
do not drive candidate parameters or additional test-based record removal.

Training CV groups connect project+commit and exact token-shape groups transitively:
10177groups, largest1191rows. Three fixed-seed stratified group folds keep these groups
disjoint. Approximate near clones are not exhaustively grouped inside training, and
project/time-independent evaluation is not established. Fold sizes/prevalence/index
hashes are persisted. All final shortlist choices occur before validation predictions.

Full source-byte percentile tables, near-search caps and timings are in the JSON.
No source modification, relabeling, benchmark split overwrite or test-set tuning occurs.
