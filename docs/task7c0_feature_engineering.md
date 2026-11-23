# Task7C.0 — feature engineering and parity

Production c-function-v1 remains frozen at11features in app/ml/features.py. It is used
unchanged by deployed C-only inference. Optional experiments add11AST-derived fields,
for22columns, in app/ml/optimization/features.py, version c-function-v2-experimental:

ast_leaf_tokens,identifier_occurrences,unique_identifiers,array_subscripts,assignments,
comparisons,arithmetic_operators,local_declarations,comment_fraction,
tokens_per_nonblank_line,decisions_per_nonblank_line.

Feature choices were specified before candidate validation. Counts are syntactic:
subscripts are subscript_expression nodes, assignments assignment_expression nodes;
comparison/arithmetic operators use AST operator fields (pointer dereference is not
counted as multiplication); declarations count local declaration nodes. Identifiers
include ordinary/field/type identifiers inside the function. Comments are excluded
from token counts and their byte span/function-snippet bytes defines comment fraction.
Token/decision density divides by measured nonblank lines. These are style/structure
signals, not semantic defect indicators or proof of vulnerabilities.

Reuse existing Tree-sitter language/base extractor; do not extract a second independent
function inventory. Existing exactly-one-function/no-error policy applies. Unparseable
inputs retain existing lexical measurements and NaN AST additions. Source-only callable
`extract` has no labels, project IDs, commit IDs or metadata inputs. Group/clone metadata
is used only to form evaluation groups, never as predictors.

Offline feature-cache generation and candidate prediction both call the same extractor.
The full cached v2 first11columns must equal genuine prepared v1 matrices (including
NaNs) for **all**21750training/2723validation rows. Tests also cover raw-function parity,
malformed/missing values, exact column ordering, AST counts and determinism. Median
imputation is training-fold-only, scaling only LR. No validation/test-fitted transform.

This experimental schema is not silently accepted by the strict production v1 loader.
Any adoption requires explicit versioned loader/metadata/runtime changes and regression
acceptance; otherwise original v1 production remains. Candidate artifacts/caches stay
under ignored artifacts/devign-optimization/task7c0-v1; schema/metrics/code are tracked.
