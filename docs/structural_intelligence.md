# Structural Intelligence — Task 4A.2

The additive `structural` object on `AnalysisResult` schema 1.0 contains its own schema version, `summary`, `coverage`, `composition`, `files`, `functions`, `hotspots`, `thresholds`, `limits` and `definitions`. It is included in existing JSON export. Both ZIP and GitHub acquisition call the same `analyze_archive` route helper. This layer uses no trained model and remains operational when inference artifacts are absent.

## Supported source and scope

- C: lowercase `.c` files, using the existing optional Tree-sitter C grammar/bindings.
- Python: `.py` and `.pyi`, using the installed interpreter's standard-library `ast` parser.
- Other included source files receive `unsupported` structural status while preserving existing inventory/line metrics. Headers, C++, JavaScript and uppercase suffix variants are outside this release's structural scope. Non-source files are `not_source` rather than classified as low complexity.

Valid independent C definitions in a file with other parsing errors may receive metrics; the file remains partial. Invalid definitions have null metrics and an explicit status. A malformed Python module produces no recovered function metrics. Missing Tree-sitter marks C unavailable without affecting Python. The analysis is syntactic: preprocessing, include resolution, type checking, runtime behavior and dataflow are not resolved. Conditional-compilation alternatives may both appear in the syntax tree.

## Metric definitions

Every valid function has baseline complexity 1. Additional AST decisions are:

| Language | Adds one decision per occurrence |
| --- | --- |
| C | `if` (including else-if), `for`, `while`, `do`, ternary, each non-default `case` label, each `&&` / `||` node |
| Python | `if` / `elif`, `for` / `async for` / `while`, ternary, each `and` / `or` link, `except` / `except*` handler, each non-irrefutable or guarded match case, each comprehension generator and filter |

C `switch` itself and `default` add no decision. Python `match` itself, plain wildcard/capture cases, pattern alternatives, assertions, `with`, bare `try` / `finally`, and `else` add no decision. A guarded case contributes one case decision, not an additional guard decision; Boolean links inside guards still count. Python Boolean chains contribute `len(values)-1`. Syntax nodes, not keyword searches, determine counts; comments and string text cannot inflate them. These are documented conventional approximations, not a compiler-derived control-flow graph or a claim of equivalence with every complexity tool.

Maximum control-flow nesting starts at zero and adds one for each enclosing supported control node. C includes if/switch/loops/ternary. Python includes if/loops/ternary/with/try/handlers/match. An except inside try therefore reaches depth 2. Else-if/elif adds another level, matching AST containment. Ordinary containers, Boolean operations, case labels, pattern nodes and comprehension generators do not increase depth. This intentionally separates comprehension complexity decisions from statement nesting.

`conditional_count` counts C if/switch/ternary and Python if/ternary/match cases/comprehension filters. `loop_count` counts supported loop nodes and Python comprehension generators. `decision_points = cyclomatic_complexity - 1`. Only the function body is measured; Python decorators, annotations and default expressions are excluded. Nested functions, classes and lambdas are excluded from enclosing metrics. Named nested functions and methods receive their own lexical qualified names and records; lambdas are not listed as functions.

Function span is inclusive start-to-end source lines, including blanks/comments/nested definitions; it is **not executable LOC**. Python decorators are outside the definition span. Source columns are zero-based UTF-8 byte offsets; lines are 1-based and end lines inclusive. C parameter count excludes lone `void` and ellipsis; Python counts positional, positional-only, keyword-only, `*args` and `**kwargs`, including `self`/`cls`. C names come from declarators; no unsupported qualified scope is invented.

## Composition

Existing inventory line metrics retain their Task 1 meaning. Structural composition reuses Python/standard-JSON inventory counts and classifies C only after a complete error-free file parse using Tree-sitter comment ranges. It blanks comment bytes without modifying newlines, then distinguishes comment-only lines from mixed source/comment lines. No universal lexer is introduced.

For each covered file, physical lines = blank + comment-only + code. Whitespace-only lines count as blank even inside multiline comments/strings. Inline/mixed comment lines count as code. Python docstrings and nonblank multiline string rows count as code; they are not comments. Preprocessor directives count as code. Density is comment-only / nonblank physical lines, in [0,1], null for a zero denominator or unavailable classification.

**Repository `composition` totals use only fully classified files**, so its categories remain consistent even with partial coverage. All-file physical/blank totals remain in the existing repository summary. `coverage.composition_files` and `composition_physical_lines` identify the denominator. Unsupported-language file composition retains physical/blank counts but uses null comment/code/density; a reliable standard JSON or Python classification can be available independently of function analysis. Structural thresholds do not consume composition metrics.

## Aggregation, identities and review thresholds

File/repository summaries aggregate only functions with `status: analyzed`. Average complexity is total / valid function count (function-weighted, not an average of file averages). No valid measurements means null average/maximum/total complexity and nesting, rather than a claim of simple code. Complexity bands count valid functions only:

- Low: 1–5; moderate: 6–10; high: 11–20; very high: 21+.
- Review hotspot thresholds: complexity **≥11**, nesting **≥4**, span **≥80 lines**, parameters **≥6**.

These values are centralized in `StructuralThresholds` (`app/config.py`) and emitted in results. Each hotspot contains file/function IDs, source location, measured values, applicable thresholds and human-readable reasons. Ordering is descending complexity, nesting and span, then path/start line/column. The list is deterministic; the UI displays the first eight and JSON includes the bounded full list. No maintainability score, debt percentage, defect probability or causal claim is derived from thresholds.

`file_` and `function_` identifiers use full SHA-256 of a versioned domain-separated tuple. File IDs use normalized repository-relative POSIX paths. Function IDs additionally use language, qualified/name symbol and line/byte-column source range. Multiple same-name definitions have distinct IDs. These identify snapshot-local entities and are reproducible for identical paths/symbols/ranges; they do not claim stability across edits, wrapper-folder changes or renames, and are not a content hash.

C functions can reference `defect_risk.functions` by `ml_result_index` only when path, start/end lines and name have one unambiguous match. Name-only matching is never used. `ml_status` reports the existing result status; Python and unmatched/absent results remain unavailable. A static record is never converted into an ML prediction. The numerical feature definitions, ordering, saved preprocessing and model binaries are unchanged. Request-local C trees are reused for file-level ML extraction where available; the model's original independent snippet parsing remains intact for representation compatibility.

## Coverage and safety

`coverage` records supported/analyzed/unsupported/skipped/partial files, invalid/unmeasured definitions, charged AST node visits, parsed bytes, composition coverage and truncation. Function counts mean discovered definitions; files omitted or incompletely parsed have unknown undiscovered counts. `complete` means all **included source files** received complete supported analysis. Archive-excluded/binary/dependency files are outside this denominator; non-source files do not imply incomplete function coverage. `status` can be complete, partial, no_supported_files or no_functions. Partial results never silently become complete.

`StructuralLimits` centralizes 512 KiB per file, 8 MiB total source, 128 KiB per measured function, 2,000 discovered function records, 100,000 node visits per file and 400,000 total charged visits. C discovery, metric and comment passes share a budget; Python discovery and metrics share one. Traversals are iterative; syntax/recursion/parser failures and work exhaustion yield explicit file/function statuses. Source bytes bound initial parser allocation before node traversal checks, but this is not a hard CPU or process-memory deadline. Files retain the original ingestion limits (5,000 entries etc.), and all outputs are bounded by that inventory and the function limit.

No source is executed, imported as a Python module or installed. Only scanner-approved paths are reopened, with size, symlink and root-containment checks. Trees/source bytes are temporary request-local data and do not appear in JSON. Both routes retain their shared concurrent-analysis limit and temporary-resource cleanup. The academic report and model artifacts are not regenerated.

## Dashboard and local checks

The Structural Intelligence section provides four summary cards, valid-function complexity distribution, classified-line composition, top-eight file complexity totals, eight prioritized hotspots, up to 24 file issue notices and a searchable/sortable 25-row function page. Complete issue lists, definitions and bounded records are available in JSON export. Long paths wrap and the existing mobile table/card patterns are reused. The ML section remains distinct; static complexity is not a vulnerability verdict.

```bash
cd /home/jordan/Projects/codebase-archaeologist
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# In a second terminal:
python -m pytest -q tests/test_structural.py
python -m pytest -q
```

Open http://127.0.0.1:8000, upload a ZIP with C and Python functions (or import a small public C repository using the existing GitHub mode). Check straight-line complexity 1, branches/loops against the above rules, nested functions' separate metrics, review thresholds and source locations. Test unsupported JS-only and malformed Python/C inputs, search/sort/pagination, JSON's `structural` component, and narrow screen widths. Repeat with unavailable model artifacts: structural metrics must still appear. Do not move or delete your artifact merely to test the app; automated tests inject a missing-model directory.

Socket restrictions in the development sandbox prevent live port/browser verification; use the documented polling selector wrapper in `ml_pipeline.md` for in-process pytest there. Network calls in GitHub tests remain mocked. The preserved Task 2 suite includes two small authentic-subset Logistic Regression checks; normal verification does not repeat full benchmark training or held-out evaluation.

Verification: **279 passed, 0 failed, 0 skipped** (228 existing plus 51 structural cases). Existing ZIP/GitHub equivalence now also checks the structural component. The real saved-model check confirms identical C predictions with and without the file-tree cache. A mixed C/Python ZIP smoke check produced complexities 3 / 2 / 2 for C, outer Python and inner Python functions; only C received ML inference. JavaScript syntax, selector consistency and a direct empty/search/25-row rendering bound check passed. Uvicorn started successfully but localhost binding was blocked, so browser/responsive visual verification remains outstanding. One existing upstream Starlette/httpx deprecation warning remains.
