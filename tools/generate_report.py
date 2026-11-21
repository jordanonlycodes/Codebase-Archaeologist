#!/usr/bin/env python3
"""Build editable DOCX and submission PDF from one evidence-driven page model.

Run: .venv/bin/python tools/generate_report.py
Dependencies: existing matplotlib and Pillow (requirements-ml.txt).
No model import, dataset loading, training or prediction occurs here.
DOCX uses standard Office Open XML; PDF uses Matplotlib's text/vector backend.
"""
from pathlib import Path
import json
import hashlib
import zipfile
from xml.sax.saxutils import escape
import tempfile
from functools import lru_cache

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.font_manager import FontProperties
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
ML = ROOT / 'reports/ml'
BLACK, BURGUNDY, CRIMSON, PALE = '#0A0A0D', '#30151D', '#E54859', '#F8E8EA'
INK, MUTED = '#28252A', '#655D63'
WIDTH, HEIGHT, MARGIN = 595.28, 841.89, 49
BODY_WIDTH = WIDTH - 2 * MARGIN
DATE = '22 November 2026'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42, 'font.size': 10})

def read(name):
    return json.loads((ML / name).read_text())

COMPARISON = read('model_comparison.json')
TEST = read('test_evaluation.json')
AUDIT = read('cleaning_audit.json')
EDA = read('eda_summary.json')
META = read('model_metadata.json')
SCHEMA = read('feature_schema.json')
SOURCE = read('source_manifest.json')
METRICS = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
# Fail rather than silently publish an unsupported model or a different experiment.
assert META['model'] == TEST['model'] == 'random_forest'
assert TEST['evaluations'] == 1 and TEST['selected_before_test']
assert TEST['test_rows_modified'] == 0
assert SCHEMA['names'] == META['feature_names'] == EDA['feature_order']
assert max(COMPARISON, key=lambda n: COMPARISON[n]['validation']['f1']) == 'random_forest'
if (ROOT / 'artifacts/devign-v1/metadata.json').exists():
    assert json.loads((ROOT / 'artifacts/devign-v1/metadata.json').read_text()) == META
    assert json.loads((ROOT / 'artifacts/devign-v1/test_evaluation.json').read_text()) == TEST

PAGES = []
def page(chapter, title, subtitle=''):
    p = {'chapter': chapter, 'title': title, 'subtitle': subtitle, 'blocks': []}
    PAGES.append(p)
    return p['blocks']
def para(blocks, text): blocks.append(('p', text))
def sub(blocks, text): blocks.append(('h', text))
def table(blocks, headings, rows, widths=None): blocks.append(('table', headings, rows, widths))
def figure(blocks, path, caption, height): blocks.append(('figure', str(path), caption, height))
def callout(blocks, text): blocks.append(('callout', text))

def diagram(path, kind):
    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    fig.patch.set_facecolor('#fffafa'); ax.set(xlim=(-.2, 10.25), ylim=(0, 6)); ax.axis('off')
    def box(x,y,label,w=2.7,h=.72,dark=False):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08,rounding_size=.08',facecolor=BURGUNDY if dark else PALE,edgecolor=CRIMSON,lw=1))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10,color=PALE if dark else INK,linespacing=1.35)
    def arrow(x1,y1,x2,y2):
        ax.annotate('',(x2,y2),(x1,y1),arrowprops={'arrowstyle':'-|>','color':CRIMSON,'lw':1.6})
    if kind == 'architecture':
        for x,y,t in [(0,4.8,'Repository ZIP'),(3.5,4.8,'Secure ZIP ingestion'),(7,4.8,'Inventory + static metrics'),(7,3.1,'C-function extraction'),(3.5,3.1,'Shared feature engineering'),(0,3.1,'Random Forest inference'),(0,1.4,'FastAPI result delivery'),(3.5,1.4,'Interactive risk dashboard'),(7,1.4,'JSON export')]: box(x,y,t)
        for a in [(2.8,5.16,3.4,5.16),(6.3,5.16,6.9,5.16),(8.35,4.7,8.35,3.9),(6.9,3.46,6.3,3.46),(3.4,3.46,2.8,3.46),(1.35,3,1.35,2.2),(2.8,1.76,3.4,1.76),(6.3,1.76,6.9,1.76)]: arrow(*a)
        ax.text(5,.35,'Static results remain available when the model is unavailable.\nOperator-trusted artifacts feed inference; uploaded code is never executed.',ha='center',va='center',fontsize=10,color=MUTED)
    elif kind == 'training':
        box(0,4.8,'Official train + validation',3.6); box(6.1,4.8,'Official test holdout',3.6, dark=True)
        box(0,3.4,'Audit + clean development',3.6); box(6.1,3.4,'Source hashes only\nfor overlap removal',3.6)
        box(0,2,'Shared features + train-fit\nimputation; fit 3 candidates',3.6)
        box(6.1,2,'Validation F1 selection\nSave selected pipeline',3.6)
        box(6.1,.5,'Evaluate selected model once\nPersist metrics + artifacts',3.6,dark=True)
        for a in [(1.8,4.7,1.8,4.2),(1.8,3.3,1.8,2.8),(3.7,2.36,6,2.36),(7.9,1.9,7.9,1.3),(7.9,4.7,7.9,4.2),(6,3.76,3.7,3.76)]: arrow(*a)
        ax.annotate('', (9.8,.86), (9.8,4.75), arrowprops={'arrowstyle':'-|>', 'color':BURGUNDY, 'lw':1.2, 'linestyle':'dashed'})
        ax.text(10.08,2.8,'Labels after selection',rotation=90,ha='center',va='center',fontsize=8,color=MUTED)
        ax.text(1.8,.8,'Test labels remain sealed\nuntil selection is recorded.',ha='center',color=MUTED,fontsize=10)
    else:
        for x,y,t in [(0,4.8,'Included .c files'),(3.5,4.8,'Bounds + Tree-sitter parse'),(7,4.8,'Genuine definitions\nwith paths + lines'),(7,3,'Unchanged feature extractor'),(3.5,3,'Saved imputer + classifier'),(0,3,'Validate output\nclass + probability'),(0,1.2,'Structured function results'),(3.5,1.2,'UI counts, filters + details'),(7,1.2,'No new inference\non navigation')]: box(x,y,t)
        for a in [(2.8,5.16,3.4,5.16),(6.3,5.16,6.9,5.16),(8.35,4.7,8.35,3.8),(6.9,3.36,6.3,3.36),(3.4,3.36,2.8,3.36),(1.35,2.9,1.35,2),(2.8,1.56,3.4,1.56),(6.3,1.56,6.9,1.56)]: arrow(*a)
        ax.text(5,.25,'Invalid functions abstain. File issues expose unknown coverage. No source text is returned.',ha='center',fontsize=10,color=MUTED)
    fig.subplots_adjust(.025,.025,.975,.975)
    fig.savefig(path); plt.close(fig)

def selected_panels(path, original, title):
    """Reuse original EDA pixels: four documented panel crops, not new data."""
    image = Image.open(original)
    w,h=image.size
    # Original 3x4 grid: physical lines, bytes, complexity and calls.
    cells=[(0,0),(0,2),(2,0),(2,2)]
    fig,axes=plt.subplots(2,2,figsize=(8,5.7),dpi=180)
    for ax,(row,col) in zip(axes.flat,cells):
        crop=image.crop((int(col*w/4),int(row*h/3),int((col+1)*w/4),int((row+1)*h/3)))
        ax.imshow(crop);ax.axis('off')
    fig.subplots_adjust(.005,.005,.995,.995,wspace=.01,hspace=.01)
    fig.savefig(path);plt.close(fig)

def content(assets):
    b=page('02','Abstract','A reproducible prototype, with measured limits')
    para(b,'Codebase Archaeologist combines repository structure analysis with machine-learning-assisted review of C functions. Its local web application accepts ZIP archives, validates and extracts them without executing their contents, and reports actual file, language and line metrics. A separate inference path identifies genuine C function definitions using Tree-sitter and applies the same deterministic features used during training.')
    para(b,f'The experiment uses the official CodeXGLUE/Devign splits: 21,854 training, 2,732 validation and 2,732 test functions. Leakage-aware development cleaning retains 21,750 training and 2,723 validation rows; the test holdout remains unchanged. Eleven syntax and size features feed three scikit-learn pipelines: Logistic Regression, Random Forest and histogram-based gradient boosting. Random Forest is selected on validation F1 ({COMPARISON["random_forest"]["validation"]["f1"]}), followed by one held-out evaluation with F1 {TEST["metrics"]["f1"]} and ROC-AUC {TEST["metrics"]["roc_auc"]}. [1–3, E1–E4]')
    para(b,'The integrated dashboard exposes function locations, predicted classes, estimated model probabilities, measured features and incomplete-coverage states. The work demonstrates reproducible acquisition, explicit data-quality policy, consistent training/inference representation and a functioning end-to-end application. It does not establish production-grade vulnerability detection: syntax counts, noisy labels, shared projects, parser limitations and uncalibrated scores restrict the conclusions. A negative prediction is not a safety guarantee.')
    callout(b,'Research contribution: an auditable path from secure repository ingestion to bounded function-level inference, with limitations visible to the reviewer.')
    sub(b,'Keywords')
    para(b,'Repository intelligence; C source code; defect prediction; Tree-sitter; Random Forest; reproducibility; leakage prevention.')
    sub(b,'Evidence boundary')
    para(b,'This report documents Tasks 1, 2 and 3A at implementation commit ce5d032216274d24800e61ca392c674426442851. Task 3B creates documents only. Saved numerical evidence is reused; no training or held-out evaluation is repeated. Student and participation details are supplied by the project owner.')

    b=page('03','Introduction','From repository structure to reviewable signals')
    para(b,'Understanding an unfamiliar repository starts with concrete questions: which files are present, which languages dominate, where source volume is concentrated, and what should be inspected first? Repository intelligence makes this structure visible. Maintainability benefits from a navigable inventory and consistent measurements, but file size or line count alone cannot establish correctness, maintainability quality or security.')
    para(b,'Machine-learning-assisted defect review addresses a narrower question: whether a function exhibits statistical patterns associated with vulnerability-related labels in a research dataset. A learned association may prioritize attention, but it cannot replace compilation, tests, dataflow reasoning or security review. In this project, repository statistics and C-function predictions are therefore presented as separate forms of evidence.')
    para(b,'The application follows a local workflow. A user uploads one ZIP, receives static inventory and metrics, and inspects optional C-function predictions through a FastAPI/Jinja2 interface with vanilla JavaScript. The model is a conventional supervised classifier rather than a language model or autonomous code-execution agent. No database, cloud service, authentication system or GPU is required for the implemented scope. [7, E5]')
    sub(b,'Engineering and research responsibilities')
    para(b,'The engineering responsibility is to preserve repository integrity, bound resource use and return interpretable results even if the model is missing. The research responsibility is to separate development decisions from final evaluation, disclose contradictory data, preserve the feature contract and avoid overstating measured performance. Neither responsibility is satisfied by an attractive dashboard alone.')
    sub(b,'Report organization')
    para(b,'Sections 4–5 define the scope and objectives. Sections 6–10 document data provenance, preprocessing, exploratory analysis, features and models. Sections 11–12 interpret the saved evaluation. Sections 13–15 describe implementation and verification. Sections 16–19 state limitations, future work, conclusions and references. Figures are either original implementation diagrams or explicitly identified saved experimental plots; no conceptual UI image is presented as an application screenshot.')

    b=page('04','Problem Statement','Two related tasks; two different claims')
    sub(b,'Repository-level analysis')
    para(b,'The first problem is the lack of an immediate, consistent view of an uploaded codebase. The system must safely ingest a ZIP and calculate real inventory, language, directory, size and line statistics. Its outputs are descriptive facts about included UTF-8 text files, subject to documented exclusions and counting rules. These facts do not directly predict vulnerabilities.')
    sub(b,'Function-level prediction')
    para(b,'The second problem is ranking review attention among eligible C functions using a reproducible model trained on vulnerability-related labels. The unit of prediction is one C function, not a file, project or repository. The model inputs are numerical syntax features derived only from function source; labels and origin metadata cannot be used as predictors.')
    table(b,['Aspect','Implemented scope'],[
        ['Input','One ZIP archive; UTF-8 files accepted by the scanner'],
        ['Static output','File inventory, language shares and measured line/byte totals'],
        ['ML unit','Genuine definitions in lowercase .c files'],
        ['ML output','Binary predicted class and uncalibrated label-1 probability'],
        ['Failure contract','Static results survive unavailable model; partial coverage is disclosed'],
        ['Outside scope','Confirmed exploitability, repository probability, automatic repair']],[.25,.75])
    sub(b,'Operational constraints')
    para(b,'Uploaded code must never execute. Extraction must prevent path traversal, links and archive expansion abuse. Inference must use trusted operator-controlled artifacts, bound source and function workloads, and preserve the exact training representation. The interface must not fabricate statistics, silently classify unsupported languages, or imply that unknown coverage means no defects. [E5–E6]')
    callout(b,'The research question is whether simple, reproducible C syntax features provide useful defect-related signals within the official benchmark—not whether the system proves a repository secure.')

    b=page('05','Project Objectives','Measurable delivery criteria')
    table(b,['Objective','Evidence of implementation'],[
        ['Safely analyze repository ZIPs','Path/link/size/count checks; recursive scanner; security tests'],
        ['Report actual repository metrics','Inventory, language breakdown, size and supported line counts'],
        ['Establish a reproducible dataset pipeline','Pinned revision, checksums, schema validation and original splits'],
        ['Audit quality and contamination','Explicit conflict quarantine and cross-split hash audit'],
        ['Maintain one feature contract','11 ordered C features, versioned schema and shared extractor'],
        ['Compare three classical models','Saved validation metrics and fixed configurations'],
        ['Protect final evaluation','Selection recorded before one selected-model test evaluation'],
        ['Integrate genuine inference','Cached trusted model, bounded C extraction and API results'],
        ['Make output reviewable','Locations, probabilities, features, filtering and JSON export'],
        ['Expose uncertainty and failures','Unavailable/partial/no-functions states and limitations']],[.40,.60])
    para(b,'Completion is assessed through code, saved reports, contracts and tests rather than an unsupported accuracy target. The objective is a coherent and honest research prototype. No minimum performance threshold was retrospectively introduced after observing the test results.')
    para(b,'The individual project was undertaken by Bilal Malik (24P-3061), Software Engineering (SE), Class 5A, FAST-NUCES, Peshawar, academic year 2026. Instructor-approved solo participation is recorded as provided by the student; no instructor identity or institutional certification is inferred.')

    b=page('06','Dataset Description','CodeXGLUE / Devign · provenance and schema')
    para(b,'The legitimate dataset is google/code_x_glue_cc_defect_detection on Hugging Face, the CodeXGLUE defect-detection task derived from Devign. Samples contain C functions from FFmpeg and QEMU, with binary vulnerability-related labels. The project uses the provider’s official train, validation and test partitions without a new random split. [1–2]')
    table(b,['Field','Verified type','Role'],[['func','string','C function source; only input to feature extraction'],['target','bool','Original binary label: 1 vulnerability-related, 0 negative'],['project','string','Source project; audit only'],['commit_id','string','Original commit identifier; audit only'],['id','int32','Record identifier; provenance only']],[.18,.18,.64])
    table(b,['Official split','Rows','Label 0','Label 1'],[[s.capitalize(),str(AUDIT['raw'][s]['rows']),str((TEST['metrics']['class_counts'] if s=='test' else AUDIT['raw'][s]['labels'])['0']),str((TEST['metrics']['class_counts'] if s=='test' else AUDIT['raw'][s]['labels'])['1'])] for s in ['train','validation','test']],[.28,.24,.24,.24])
    para(b,'Test class counts in this retrospective report come from the saved post-selection evaluation. They were not used for development EDA or model selection. The labels are research annotations, not a proof that every positive function is exploitable or every negative function is safe.')
    sub(b,'Licensing and reproducible acquisition')
    para(b,'The provider declares C-UDA for data; CodeXGLUE software separately declares MIT. Acquisition preserves the dataset card, agreement text and source hashes. This report records attribution and does not treat a dataset declaration as a blanket license for every underlying source project. No raw source samples are redistributed here. [1–3, E1]')
    para(b,'Pinned revision: '+SOURCE['revision']+'. Acquisition reads Parquet directly and verifies the schema and expected row counts. It does not execute a remote dataset script. The two shared source projects and commit-derived labeling restrict transfer claims to new repositories.')

    b=page('07','Data Preprocessing','Quality checks without rewriting the holdout')
    para(b,'The preparation code validates field types, nonempty function inputs and binary labels. The recorded train/validation audit contains zero missing values in func, target, project, commit_id and id, and zero invalid labels. The post-selection test audit likewise reports no missing fields or invalid labels. A configured invalid-record policy therefore did not cause missing-value row removals in this run. [E1–E2]')
    para(b,'Duplicate fingerprints use SHA-256 after universal-newline normalization and trimming only outer whitespace. Internal whitespace, comments, literals and identifiers are retained. This detects exact/normalized function identity, not semantic clones. Raw training contains 46 duplicate groups, all contradictory; validation contains none. Eight function groups cross train/validation, four cross train/test and one crosses validation/test.')
    table(b,['Cleaning result','Recorded count'],[['Contradictory development groups quarantined','54 groups / 108 rows'],['Development rows matching test source','5'],['Total development rows removed','113'],['Training retained','21,750 (11,786 label 0; 9,964 label 1)'],['Validation retained','2,723 (1,539 label 0; 1,184 label 1)'],['Test retained','2,732; zero rows modified'],['Cross-split identical groups after cleaning','0']],[.65,.35])
    para(b,'All conflicting development copies are quarantined without majority voting. Same-label duplicates retain the first official row; validation takes precedence over training. Test source hashes take precedence over both development splits. Every removal records split, original index, ID, hash and all reasons. The untouched test set retains its one contradictory duplicate group; it is disclosed after selection, not removed.')
    para(b,'During development, test target is omitted from Parquet reads. Test source hashes and integrity counts are inspected for contamination removal, so the holdout is not source-blind; its labels and predictive evaluation remain sealed. Shared project/commit pairs still number 1,134 train/test, 1,132 train/validation and 446 validation/test after cleaning. The policy does not establish temporal or project independence.')

    b=page('08','Exploratory Data Analysis','Population and data-quality evidence')
    figure(b,ML/'split_and_label_counts.png','Figure 1. Original Task 2 plot: official split sizes and cleaned development label counts. Test labels remain sealed in this EDA figure. Source: reports/ml/split_and_label_counts.png.',205)
    para(b,'The cleaned training positive fraction is 9,964 / 21,750 = 0.458115. Both classes are substantial; class balancing is still applied consistently across the three classifiers. These proportions characterize the benchmark and cannot be interpreted as the defect prevalence of a new uploaded repository.')
    figure(b,ML/'missing_and_duplicates.png','Figure 2. Original training missing-field counts and normalized duplicate excess rows. A flat missing-field panel means zero recorded missing values, not missing measurement. Source: reports/ml/missing_and_duplicates.png.',183)
    para(b,'Raw missing fields and parser failures are different phenomena. Source strings can be present yet fail structural parsing. Duplicate counts motivated explicit quarantine and overlap checks, while the official test rows were preserved.')

    b=page('08','Function Size & Complexity','Saved distributions; no new experimental runs')
    figure(b,assets/'distributions_selected.png','Figure 3. Four panels reused from the original feature-distributions plot: physical lines, function bytes, approximate decision complexity and calls. Axes are log(1 + value); structural plots use observed parses only. Cropping changes presentation, not data.',350)
    table(b,['Training feature','Median','95th percentile','Maximum'],[[f.replace('_',' '),str(EDA['feature_statistics']['train'][f]['quantiles']['median']),str(EDA['feature_statistics']['train'][f]['quantiles']['p95']),str(EDA['feature_statistics']['train'][f]['quantiles']['max'])] for f in ['physical_lines','function_bytes','decision_complexity','call_count']],[.40,.18,.22,.20])
    para(b,'The distributions are right-skewed: a minority of long, structurally complex functions extend the tail. Logarithmic display improves visibility without changing model inputs. Training uses original numerical values; no log transform, clipping or feature selection was applied. Size and complexity may indicate review effort, but they do not establish a causal defect mechanism. [E2]')

    b=page('08','Feature Relationships','Correlation is not attribution')
    figure(b,ML/'feature_correlations.png','Figure 4. Original pairwise Pearson correlations on observed training features. Missing structural values are excluded per pair; the matrix is descriptive, not a learned explanation. Source: reports/ml/feature_correlations.png.',430)
    r=EDA['correlation'][EDA['feature_order'].index('function_bytes')][EDA['feature_order'].index('nonblank_lines')]
    para(b,f'The strongest absolute pair is function_bytes versus nonblank_lines (r = {r:.12f}). Several size and control-flow counts move together. Redundant signals may constrain the benefit of additional size metrics, but no ablation study was conducted; this report cannot claim which feature causes or improves predictions.')
    para(b,'The plot uses cleaned training data only. Correlations are neither test-set performance estimates nor function-level attributions. Missing-value handling in descriptive plots differs from train-fitted imputation used by the models.')

    b=page('08','Class-Conditional Patterns','Small shifts with substantial overlap')
    figure(b,assets/'classes_selected.png','Figure 5. Four panels reused from features_by_class.png. Box plots show log(1 + value) by original target; fliers are hidden in the saved plot. Label-conditioned associations do not prove causation or exploitability.',350)
    table(b,['Training median','Label 0','Label 1'],[[f.replace('_',' '),str(EDA['training_features_by_class']['0'][f]['quantiles']['median']),str(EDA['training_features_by_class']['1'][f]['quantiles']['median'])] for f in ['physical_lines','function_bytes','decision_complexity','call_count']],[.50,.25,.25])
    para(b,'Positive-labeled functions have somewhat larger median size and more calls in these observed data, yet class distributions overlap. Simple thresholds on length or complexity would not resolve the task. Structural-feature summaries exclude 4,029 unsuccessful training parses; this missingness itself limits descriptive interpretation. No test feature/class analysis was used to design the models. [E2]')

    b=page('09','Feature Engineering','One deterministic C-function schema')
    para(b,'Tree-sitter builds syntax trees without running source code. The C grammar identifies functions and control/expression nodes. The project uses bindings 0.25.2 and grammar 0.24.2. Version c-function-v1 supplies the following ordered float64 features; source metadata and parsing-status labels are excluded from the predictive matrix. [4, E3]')
    table(b,['Order / feature','Operational meaning'],[[str(i+1)+'. '+f['name'],f['description']] for i,f in enumerate(SCHEMA['features'])],[.37,.63])
    para(b,'Size summarizes function extent; branch/loop/return and nesting metrics characterize control structure; pointer and call counts describe syntactic interaction patterns. These are plausible review signals rather than verified causal mechanisms. Approximate decision complexity is not a full compiler-derived control-flow metric. No include resolution, type checking, dataflow analysis or semantic proof is performed.')

    b=page('09','Training–Inference Consistency','Parsing policy and numerical representation')
    para(b,'The shared extractor normalizes line endings and trims outer whitespace, then requires exactly one function definition and no Tree-sitter error for structural features. Empty, invalid, NUL-containing or oversized source is rejected or marked unavailable. For a nonempty failed parse, lexical size values can remain while structural features become NaN. Strings, comments and multiplication operators do not become pointer or control counts.')
    table(b,['Partition','Valid parses','Parse errors','Not one function'],[['Training','17,721','4,001','28'],['Validation','2,260','460','3'],['Test (post-selection)','2,237','493','2']],[.34,.22,.22,.22])
    para(b,'Training and offline function prediction call feature_matrix. Repository inference calls the same extract_features routine and forms float64 rows in FEATURE_NAMES order. The persisted pipeline preserves median imputation fitted on training rows; all-empty columns are retained. Logistic Regression additionally uses training-fitted standard scaling. There is no vocabulary encoding, one-hot encoding, metadata encoding or training-only representation. [E3–E5]')
    sub(b,'A deliberate coverage difference')
    para(b,'The benchmark scores every official test row, including parse failures, with the saved imputer. Live inference abstains unless the individual function parses successfully. Valid definitions within a partly malformed file may be scored, while a file-level issue remains visible. Consequently the benchmark metrics do not directly measure the accuracy or coverage of the live abstaining policy.')
    sub(b,'Artifact compatibility')
    para(b,'The loader verifies feature version and order, full schema including parser versions, recorded numerical-library versions, pipeline checksum, feature count and binary classes. The repository service also requires RandomForestClassifier and probability support. An incompatible artifact yields model unavailable, not a fallback estimator. The serialization is trusted local joblib; uploaded models are never deserialized.')

    b=page('10','Models and Training','Three conventional supervised baselines')
    sub(b,'Logistic Regression')
    para(b,'Logistic Regression learns a weighted combination of features and maps it through a logistic function to estimate the positive class. It provides a relatively simple linear decision boundary. Here, median imputation and standard scaling precede the classifier; C = 1.0, solver = lbfgs, max_iter = 2000 and balanced class weights are recorded. [5, E4]')
    sub(b,'Random Forest')
    para(b,'A Random Forest combines many decision trees trained with sampling and random feature subsets. Averaging their outputs can capture nonlinear interactions while reducing the instability of an individual tree. The saved configuration has 200 trees, maximum depth 12, minimum leaf size 3, sqrt feature selection, Gini criterion, bootstrap sampling, balanced class weights and n_jobs = 1. Median imputation is retained; scaling is not added. [6, E4]')
    sub(b,'HistGradientBoostingClassifier')
    para(b,'Histogram-based gradient boosting builds trees sequentially, each improving the current loss-based approximation. Binning numerical values makes split search efficient. This run uses learning_rate = 0.08, max_iter = 160, max_leaf_nodes = 15, min_samples_leaf = 20, l2_regularization = 1.0, balanced class weights and early_stopping = False. It receives median-imputed features. [6, E4]')
    sub(b,'Reproducibility controls')
    para(b,'All configurations use seed 42 and a fixed evaluation threshold of 0.5. Each full candidate is fitted once on the cleaned training set. There is no hyperparameter search, threshold tuning, cross-validation study or refit on validation data. Thread limiting makes this a laptop-sized experiment. The saved fit_seconds spans fitting and training/validation metric computation; it is not isolated fit time or a controlled performance benchmark.')
    para(b,'Checksummed source, schema and code identities, model parameters and package versions are recorded. The successful environment uses Python 3.14.10 and scikit-learn 1.9.1. requirements-ml-frozen.txt preserves the exact environment. A completed run is reused; locks and an evaluation-start marker guard against accidental repeated holdout evaluation. [E4]')

    b=page('10','Training and Selection Workflow','Keep model selection upstream of test evaluation')
    figure(b,assets/'training.png','Figure 6. Implemented offline workflow. Only test source hashes enter development contamination checks. Test labels are loaded after selection, and only the selected pipeline receives final evaluation. Source: dataset.py, prepare.py and train.py.',310)
    para(b,'Development cleaning precedes feature preparation. Each candidate learns preprocessing and classifier parameters from training rows. Validation F1 determines the winner; tie-breakers are recall, fewer false positives, smaller absolute train/validation F1 gap and model name. The chosen pipeline is persisted and reloaded before evaluation, verifying the actual inference artifact.')
    table(b,['Candidate','Recorded fit_seconds','Training F1'],[[name,f'{COMPARISON[key]["fit_seconds"]:.6f}',f'{COMPARISON[key]["train"]["f1"]:.12f}'] for key,name in [('logistic_regression','Logistic Regression'),('random_forest','Random Forest'),('hist_gradient_boosting','Histogram boosting')]],[.45,.25,.30])
    para(b,'Selection was saved at 2026-11-21T17:51:21.751143+00:00. The test record completed at '+TEST['completed_at']+'. These timestamps establish the saved sequence; they are not a substitute for a fully independent external evaluation. Once results are known, later experiments cannot claim this same holdout is unseen.')

    b=page('11','Model Evaluation and Comparison','Validation results only · 2,723 functions')
    para(b,'Accuracy measures total correct classifications. Precision measures the fraction of predicted positives that are labeled positive. Recall measures the fraction of labeled positives retrieved. F1 is the harmonic mean of precision and recall: 2PR / (P + R). ROC-AUC measures score ranking across thresholds, not probability calibration. Positive-class metrics below use the original label 1. [E4]')
    # Vertical table preserves the exact JSON decimal representations at readable size.
    table(b,['Validation metric','Logistic Regression','Random Forest','Histogram boosting'],[[metric.replace('_',' ').upper() if metric in ('f1','roc_auc') else metric.title(),*[str(COMPARISON[k]['validation'][metric]) for k in ['logistic_regression','random_forest','hist_gradient_boosting']]] for metric in METRICS],[.19,.27,.27,.27])
    para(b,'Table values reproduce the saved decimal representations; they do not imply that performance is known to this precision. Confidence intervals and repeated-seed uncertainty were not estimated. All three columns refer to the same cleaned validation partition and threshold 0.5. No unselected model’s test results are reported because those models were not evaluated on the holdout.')
    table(b,['Validation confusion counts','Logistic','Forest','Boosting'],[[label,*[str(COMPARISON[k]['validation']['confusion_matrix'][r][c]) for k in ['logistic_regression','random_forest','hist_gradient_boosting']]] for label,r,c in [('True negative',0,0),('False positive',0,1),('False negative',1,0),('True positive',1,1)]],[.40,.20,.20,.20])
    para(b,'Random Forest has the highest validation F1 and recall among the three configurations. Logistic Regression produces fewer false positives but misses more positive examples. This trade-off matters for review cost: the highest F1 among these candidates is not a demonstration of acceptable operational performance. [E4]')

    b=page('11','Final Held-Out Evaluation','Selected Random Forest only · 2,732 functions')
    table(b,['Held-out metric','Exact saved value'],[[m.replace('_',' ').upper() if m in ('f1','roc_auc') else m.title(),str(TEST['metrics'][m])] for m in METRICS]+[['False-positive rate',str(TEST['metrics']['false_positive_rate'])]],[.48,.52])
    table(b,['Actual / predicted','Predicted 0','Predicted 1'],[['Actual 0','842 true negatives','635 false positives'],['Actual 1','580 false negatives','675 true positives']],[.34,.33,.33])
    figure(b,ML/'confusion_matrices.png','Figure 7. Original saved selected-model confusion matrices. Validation (left) and test (right) remain separate. Rows are actual class, columns predicted class. Source: reports/ml/confusion_matrices.png.',225)
    para(b,'The record reports one evaluation, zero modified test rows and selection before test access. All 2,732 official test functions are retained, including one contradictory duplicate group. Five test rows disagree with original development labels for matching source; the development copies had already been excluded. No new prediction pass was performed to prepare this report. [E4]')

    b=page('12','Selected Model','Why Random Forest—and why caution remains')
    para(b,f'Random Forest was selected because validation F1 = {COMPARISON["random_forest"]["validation"]["f1"]} is higher than the other two fixed candidates. Its validation recall is {COMPARISON["random_forest"]["validation"]["recall"]}, but it also produces 630 false positives. Selection follows the predeclared validation rule rather than the final test outcome. The selected pipeline was not refitted on validation data.')
    para(b,f'Training F1 is {COMPARISON["random_forest"]["train"]["f1"]}; the saved train–validation gap is {COMPARISON["random_forest"]["train_validation_f1_gap"]}. This substantial gap is consistent with overfitting. The test ROC-AUC of {TEST["metrics"]["roc_auc"]} shows only modest discrimination, and the 635 false positives and 580 false negatives are material practical limitations.')
    sub(b,'Context from class prevalence')
    negatives, positives = TEST['metrics']['class_counts']['0'], TEST['metrics']['class_counts']['1']
    para(b,f'Using saved test counts alone, always predicting class 0 gives accuracy {negatives/(negatives+positives):.6f}. Always predicting class 1 gives F1 {2*positives/(2*positives+negatives):.6f}, with a 100% false-positive rate. These are algebraic reference values, not newly fitted or test-evaluated models. The latter exceeds the selected model’s F1, showing why F1 in isolation cannot establish usefulness.')
    callout(b,'The result supports an exploratory review aid, not production-grade vulnerability detection. A high score does not confirm a defect; a low score does not establish safety.')
    sub(b,'Interpretation in the application')
    para(b,'The UI calls scores estimated model probabilities and explicitly notes their lack of calibration. Review priorities order functions by score, not severity. Feature details show measured syntax counts without invented causal explanations or attribution. No probability is aggregated into a repository-wide risk estimate. Independent-project evaluation and calibration are future research requirements. [E5]')

    b=page('13','System Architecture','Separate evidence collection, inference and presentation')
    figure(b,assets/'architecture.png','Figure 8. Implemented repository analysis path. Static metrics and optional C-function inference form one response. The diagram describes code modules, not a conceptual UI screenshot. Source: app/routes/analysis.py, scanner.py and app/ml/repository.py.',310)
    table(b,['Layer','Principal modules / responsibility'],[['Presentation','templates/dashboard.html; static/app.js, risk.js, styles.css'],['HTTP boundary','main.py, middleware.py, routes/analysis.py; structured errors'],['Ingestion + static','ingestion/archive.py; analysis/scanner.py and counting policy'],['ML runtime','ml/repository.py; features.py; model_store.py; schemas.py'],['Offline research','acquire.py, dataset.py, prepare.py, eda.py, train.py'],['Persisted evidence','reports/ml JSON/PNG; trusted artifacts/devign-v1 locally']],[.28,.72])
    para(b,'FastAPI handles one multipart upload and runs synchronous analysis in a worker thread. A temporary directory contains extraction through inference and is removed on normal completion or handled failure. Browser results remain in memory until replaced/refreshed. Trusted model artifacts sit outside uploads and are loaded once per process, independently of the raw dataset. [7, E5]')

    b=page('14','Web Application Implementation','Upload, inventory and transparent boundaries')
    para(b,'The entry point is POST /api/analyze with one multipart file field. GET / serves the Jinja2 dashboard and GET /api/health reports service health. The existing response retains repository identity, timestamp, archive entries, summary, languages, files, largest files, skipped reasons and notes; Task 3A adds an explicit defect_risk object. [E5]')
    sub(b,'Secure ingestion and static measurements')
    para(b,'ZIP checks reject traversal/absolute paths, symlinks and special files, conflicting entries, unsupported compression and excessive expansion. Limits are 25 MiB uploaded, 100 MiB expanded, 2 MiB per file, 5,000 entries, 30 path levels and a 200:1 compression ratio. The scanner excludes Git internals, dependencies, environments, build outputs, caches, binaries and unsupported non-UTF-8 files. Code is never executed.')
    para(b,'Static metrics include file/source-file counts, directories, language/format shares, bytes, physical lines, blank lines and largest files. Source lines include comments and blanks in recognized source files. Comment-only and code-line counts are reliably supported for tokenizable Python and standard JSON; other formats use null rather than false zero counts. Directory counts exclude the extraction root and preserve ZIP wrapper folders.')
    sub(b,'Interaction and result lifecycle')
    para(b,'Users choose or drop one ZIP. Upload progress reflects bytes sent, followed by an indeterminate validation/scanning/inference phase. Existing inventory supports search, sort and pagination. JSON export downloads the full response including ML results. Failed uploads preserve the previous successful display with an explicit notice. Relative paths are rendered as text, not HTML.')
    para(b,'The app is local and single-user in scope. Two analyses may run concurrently per process; additional requests receive 429. It has no persistent result database or working GitHub URL ingestion. A crash can leave temporary operating-system files, unlike normal cleanup. No real application screenshot is included because browser capture and verification were blocked by sandbox socket restrictions.')

    b=page('14','Inference and Risk Intelligence','Bounded workload; honest failure states')
    figure(b,assets/'inference.png','Figure 9. Runtime inference workflow. The exact feature schema and saved preprocessing are reused. No training occurs during startup, requests or dashboard navigation. Source: app/ml/repository.py and app/static/risk.js.',280)
    para(b,'Only included lowercase .c files enter ML extraction. Limits are 1,000 definitions per analysis, 512 KiB per C file, 8 MiB total parsed C source and 128 KiB per scored function. These are workload bounds, not a hard CPU-time deadline. Names and 1-based line ranges come from Tree-sitter nodes; oversized/invalid functions abstain and unprocessed counts remain explicitly unknown.')
    para(b,'ARCHAEOLOGIST_MODEL_DIR optionally selects an operator-trusted directory; the default is artifacts/devign-v1. A locked first load caches success or failure per process. Missing/corrupt/incompatible artifacts yield unavailable status while static results remain operational. Recovery restores the matching pipeline, metadata and schema, installs compatible recorded dependencies and restarts the server. Uploaded files never control this path.')
    para(b,'The black-and-crimson section presents actual analyzed/positive/negative/known-skipped counts, a searchable and paginated function table, feature details, predicted-class bars, five probability bins, top-eight files by positive count and five review-priority functions. Accessible native progress bars render charts; there is no Chart.js dependency. States include ready, partial, unavailable and no_functions. Other languages receive static analysis only.')

    b=page('15','Testing and Validation','Verified outcomes, with provenance')
    table(b,['Recorded stage','Outcome','Evidence'],[['Task 1','73 passed','ZIP, API, scanner and middleware tests'],['Task 2','120 passed total','47 additional feature/data/model tests'],['Task 3A','140 passed; 0 failed; 0 skipped','20 additional inference/integration cases']],[.22,.34,.44])
    para(b,'These are the completed implementation verification outcomes documented in README.md and the preceding task run, not a newly executed Task 3B test run. The preserved suite includes two small Logistic Regression fitting checks on 128 authentic training rows; those tests are not rerun for document generation. No full model fitting or held-out evaluation is repeated. [8, E6]')
    sub(b,'Coverage')
    para(b,'Security tests exercise unsafe paths, symlinks/special entries, duplicate paths, compression limits, corrupt archives, forged metadata, unsupported content and temporary-file cleanup. ML tests cover deterministic features, ordering, malformed input, duplicate/conflict policy, leakage checks, serialization compatibility and evaluation guards. Integration tests verify multiple C functions, correct relative paths/line ranges, mixed languages, no C functions, workload limits, probability bounds, failed inference, missing artifacts and API/schema/export wiring.')
    sub(b,'Real integration and operational checks')
    para(b,'The Task 3A API test posts a real ZIP containing two C functions with Python/C++ files and verifies two genuine saved-model predictions. A separate recorded ZIP smoke check produced scores 0.6183925272514844 and 0.5682846681501781 for two illustrative C functions. These are integration observations without ground-truth labels, not accuracy evidence. The model version was devign-v1-4a23cc304ca8.')
    para(b,'Dependency and JavaScript syntax checks passed; the base application imported without optional ML dependencies. Uvicorn completed startup, but sandbox restrictions prevented port binding. Chromium failed with a socket-permission error, so live visual/browser interaction validation remains pending. One upstream Starlette/httpx deprecation warning was reported. JSON export coverage verifies response inclusion and wiring, not a browser download interaction.')

    b=page('16','Limitations','What the evidence cannot establish')
    table(b,['Limitation','Consequence'],[['Modest discrimination','Test F1 0.5263157894736842 and ROC-AUC 0.5873540367979673 do not establish deployment utility.'],['Shared data origins','FFmpeg/QEMU and shared commits limit transfer to independent projects; near clones remain.'],['Noisy labels','Commit-derived labels and a contradictory test group limit label fidelity.'],['C-only scope','Other languages, headers and uppercase .C files do not receive ML predictions.'],['Parser coverage','Macros and fragments can fail; live abstention differs from benchmark imputation coverage.'],['Syntax-only representation','No types, call-graph reasoning, dataflow, exploitability proof or code execution.'],['Uncalibrated probability','Scores are estimates, not certainty, severity or a repository-level probability.'],['Local trusted artifacts','Model files are Git-ignored; a fresh clone alone cannot perform predictions.'],['Evaluation uncertainty','No repeated seeds, intervals, ablations, external benchmark or calibration study.'],['Application constraints','No durable result storage; bounded local workloads; browser validation remains pending.']],[.30,.70])
    para(b,'False positives can waste review time; false negatives can create misplaced reassurance if limitations are ignored. The interface’s warning language and explicit unavailable/partial states mitigate presentation risks but do not improve classifier performance. Human review, independent testing and appropriate static/security tools remain necessary.')
    para(b,'Exact-function cleaning reduces one contamination mechanism, not every form of information dependence. Test source hashes were consulted for deduplication; the official split is therefore an untouched label/evaluation holdout rather than a completely unseen source corpus. Conclusions should stay within that boundary.')

    b=page('17','Future Enhancements','Planned work—not implemented claims')
    table(b,['Planned enhancement','Research / engineering requirement'],[['GitHub URL ingestion','Define safe acquisition, repository size limits and remote failure handling.'],['Advanced repository metrics','Add justified dependency/complexity metrics with transparent language coverage.'],['Cinematic Black & Crimson UI','Task 5 full-interface redesign; Task 3A styles only the ML section.'],['Jordan hybrid AI assistant','Specify assistant behavior, grounding, privacy and evaluation before integration.'],['Further repository intelligence','Investigate change-aware review and traceable repository navigation.'],['Stronger evaluation','Use independent-project/time splits, uncertainty estimates and calibrated thresholds.'],['Improved representations','Study additional reproducible features and parser coverage through controlled experiments.']],[.34,.66])
    para(b,'These features are proposals. They do not exist merely because the report describes them. Each future addition should preserve the current separation between measured facts, model estimates and unverified suggestions. New experiments must use an appropriate independent evaluation protocol; the known official test result cannot be repeatedly used as a tuning target.')
    sub(b,'Suggested sequencing')
    para(b,'First, complete normal-environment browser verification and establish artifact distribution/recovery practices. Next, assess generalization and calibration before making stronger prediction claims. Product enhancements can then be evaluated against explicit user needs and operational limits. An assistant should expose its evidence and uncertainty rather than convert an uncalibrated classifier score into a definitive diagnosis.')

    b=page('18','Conclusion','Unearth the Unseen. Report only the evidenced.')
    para(b,'Codebase Archaeologist delivers a working local path from secure ZIP ingestion to repository inventory and optional C-function defect-related inference. Tasks 1, 2 and 3A establish modular boundaries between extraction, static analysis, data preparation, deterministic features, persisted models and interactive presentation. The resulting system supports inspectable outputs and graceful failure without executing uploaded code.')
    para(b,'The research pipeline uses the legitimate official CodeXGLUE/Devign splits, records data-quality issues, quarantines contradictory development examples and removes exact cross-split function overlap while preserving every test row. It compares three fixed classical pipelines and selects Random Forest using validation F1 before one final held-out evaluation. Saved metadata and checksums make the experiment auditable.')
    para(b,'The empirical result is deliberately modest. Random Forest’s test F1 of 0.5263157894736842 and ROC-AUC of 0.5873540367979673 support only limited discrimination in this benchmark. A substantial train–validation gap, shared projects, noisy labels and live parsing abstention restrict external conclusions. The contribution is an honest, reproducible engineering and research foundation, not proof of production-grade vulnerability detection.')
    callout(b,'A useful repository intelligence tool must make its evidence and its uncertainty equally visible.')
    sub(b,'Submission scope')
    para(b,'This editable report and companion PDF document the completed implementation and saved experiment. They include genuine EDA figures, original implementation diagrams and explicit verification limits. No fabricated application screenshots, additional experiments or future features are represented as completed work.')

    b=page('19','References','Primary sources consulted · accessed '+DATE)
    refs=[
        ('1','Google / Hugging Face. CodeXGLUE defect-detection dataset card.','https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection'),
        ('2','Microsoft. CodeXGLUE: Code-Code / Defect-detection task documentation.','https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection'),
        ('3','Microsoft. Computational Use of Data Agreement, C-UDA 1.0.','https://github.com/microsoft/Computational-Use-of-Data-Agreement/blob/master/C-UDA-1.0.md'),
        ('4','Tree-sitter. Introduction and syntax-tree parsing documentation.','https://tree-sitter.github.io/tree-sitter/'),
        ('5','scikit-learn. Linear models: Logistic Regression documentation.','https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression'),
        ('6','scikit-learn. Ensemble methods: forests and histogram gradient boosting.','https://scikit-learn.org/stable/modules/ensemble.html'),
        ('7','FastAPI. Official framework documentation.','https://fastapi.tiangolo.com/'),
        ('8','pytest. Official testing framework documentation.','https://docs.pytest.org/en/stable/'),
    ]
    for n,title,url in refs:
        sub(b,f'[{n}] {title}');para(b,url)
    para(b,'External sources support dataset provenance and method/library descriptions. Project-specific counts, parameters, results and implemented behaviors are grounded in the local evidence register on the next page. No external benchmark score is claimed as this project’s result.')

    b=page('19','Project Evidence Register','Exact local sources and implementation snapshot')
    table(b,['Key','Evidence source','Supports'],[
        ['E1','reports/ml/source_manifest.json; cleaning_audit.json','Pinned revision, schema, split counts, conflicts and overlaps'],
        ['E2','reports/ml/eda_summary.json; observations.txt; six PNG figures','Statistics, class comparisons, correlations and plots'],
        ['E3','reports/ml/feature_schema.json; app/ml/features.py','Ordered feature definitions and parsing policy'],
        ['E4','reports/ml/model_comparison.json; test_evaluation.json; model_metadata.json','Exact metrics, parameters, selection, environment and saved test record'],
        ['E4a','artifacts/devign-v1/metadata.json; selection.json; test_evaluation.json','Local artifact evidence checked against tracked reports'],
        ['E5','app/routes/analysis.py; app/ml/repository.py; schemas.py; model_store.py; scanner.py','Runtime flow, response contracts, limits and trusted loading'],
        ['E5a','app/templates/dashboard.html; app/static/app.js; risk.js; styles.css','Actual interface, charts, filters and export'],
        ['E6','tests/test_archive.py; test_api.py; test_scanner.py; tests/ml/; README.md','Coverage and recorded completed-test outcomes']],[.10,.53,.37])
    para(b,'Preparation and training behavior was checked against app/ml/dataset.py, prepare.py, eda.py, estimators.py and train.py. Additional explanatory documentation: docs/ml_pipeline.md and docs/inference_api.md. Task 2 metadata retains a historical “dashboard disabled” scope string; the later Task 3A route and service establish current integration. Historical artifacts were not edited.')
    para(b,'Implementation snapshot: ce5d032216274d24800e61ca392c674426442851. Model: '+META['model_version']+'. Feature schema: '+META['feature_version']+'. Dataset revision: '+SOURCE['revision']+'.')
    para(b,'Repository: https://github.com/jordanonlycodes/Codebase-Archaeologist. The document generator reads saved reports only and writes a checksum manifest alongside the deliverables. Raw datasets and executable model artifacts remain outside the submission. The PDF and DOCX share one substantive content model; pagination may change when editing the DOCX.')

FONT = FontProperties(family='DejaVu Sans', size=10)
_measure_fig=plt.figure(figsize=(1,1),dpi=72)
_measure_fig.canvas.draw()
RENDERER=_measure_fig.canvas.get_renderer()
@lru_cache(maxsize=8192)
def wrap(text, width, size=10):
    font=FontProperties(family='DejaVu Sans',size=size)
    def measure(s): return RENDERER.get_text_width_height_descent(s,font,False)[0]
    lines=[]
    for original in str(text).split('\n'):
        line=''
        for word in original.split():
            if measure(word)>width:
                pieces=[];part=''
                for char in word:
                    if part and measure(part+char)>width: pieces.append(part);part=''
                    part+=char
                pieces.append(part)
            else: pieces=[word]
            for piece in pieces:
                candidate=(line+' '+piece).strip()
                if line and measure(candidate)>width: lines.append(line);line=piece
                else: line=candidate
        lines.append(line)
    return lines

def layout(blocks):
    planned=[];height=0
    for block in blocks:
        kind=block[0]
        if kind in ('p','h','callout'):
            size={'p':10,'h':11,'callout':11}[kind]
            pad=12 if kind=='callout' else 0
            lines=wrap(block[1],BODY_WIDTH-pad*2,size)
            h=len(lines)*(15 if kind!='h' else 16)+(18 if kind=='callout' else 10)
            planned.append((block,h,lines));height+=h
        elif kind=='table':
            _,heads,rows,widths=block
            widths=widths or [1/len(heads)]*len(heads)
            wrapped=[]
            for row in [heads]+rows:
                cells=[wrap(str(cell),BODY_WIDTH*w-14,8.5) for cell,w in zip(row,widths)]
                h=max(len(c) for c in cells)*12+14
                wrapped.append((cells,h))
            h=sum(row[1] for row in wrapped)+13
            planned.append((block,h,wrapped));height+=h
        else:
            lines=wrap(block[2],BODY_WIDTH,8.4)
            h=block[3]+len(lines)*12+18
            planned.append((block,h,lines));height+=h
    return planned,height

def draw_text(ax,text,x,y,size=10,color=INK,weight='normal'):
    ax.text(x,y,text,va='top',ha='left',fontsize=size,color=color,fontweight=weight,linespacing=1.42)

def pdf_cover(pdf):
    fig=plt.figure(figsize=(WIDTH/72,HEIGHT/72),dpi=72)
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,WIDTH),ylim=(HEIGHT,0));ax.axis('off')
    ax.add_patch(Rectangle((0,0),WIDTH,540,color=BLACK))
    ax.add_patch(Rectangle((0,0),16,540,color=CRIMSON))
    for i in range(9):
        ax.plot([360+i*20,WIDTH],[40,260-i*13],color=BURGUNDY,lw=.8)
        ax.plot([320,WIDTH],[340+i*16,340+i*16],color=BURGUNDY,lw=.7)
    draw_text(ax,'RESEARCH PUBLICATION  /  2026',MARGIN,58,10,CRIMSON,'bold')
    draw_text(ax,'CODEBASE',MARGIN,142,36,PALE,'bold')
    draw_text(ax,'ARCHAEOLOGIST',MARGIN,189,33,PALE,'bold')
    draw_text(ax,'AI-Powered Repository Intelligence\n& Defect Risk Analyzer',MARGIN,265,17,PALE)
    ax.plot([MARGIN,145],[350,350],color=CRIMSON,lw=3)
    draw_text(ax,'Unearth the Unseen.',MARGIN,377,23,PALE)
    draw_text(ax,'SECURE INGESTION  /  REPRODUCIBLE ML  /  HONEST INFERENCE',MARGIN,485,8.4,PALE)
    draw_text(ax,'Bilal Malik',MARGIN,582,21,INK,'bold')
    draw_text(ax,'24P-3061  ·  Class 5A\nDepartment of Software Engineering (SE)\nFAST-NUCES, Peshawar',MARGIN,626,12,INK)
    draw_text(ax,'Individual AI project\nInstructor-approved solo participation',MARGIN,710,10,MUTED)
    draw_text(ax,'TASKS 1, 2 & 3A  /  ACADEMIC REPORT',MARGIN,795,9,CRIMSON,'bold')
    pdf.savefig(fig, dpi=220);plt.close(fig)

def build_pdf(path):
    with PdfPages(path,metadata={'Title':'CODEBASE ARCHAEOLOGIST','Author':'Bilal Malik','Subject':'AI-Powered Repository Intelligence & Defect Risk Analyzer'}) as pdf:
        pdf_cover(pdf)
        for index,p in enumerate(PAGES,start=2):
            plan,height=layout(p['blocks'])
            if height>638:
                raise ValueError(f'Page overflows ({height:.0f}pt): {p["title"]}')
            fig=plt.figure(figsize=(WIDTH/72,HEIGHT/72),dpi=72)
            ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,WIDTH),ylim=(HEIGHT,0));ax.axis('off')
            draw_text(ax,'CODEBASE ARCHAEOLOGIST',MARGIN,25,8,MUTED,'bold')
            draw_text(ax,'RESEARCH / 2026',440,25,8,MUTED)
            ax.plot([MARGIN,WIDTH-MARGIN],[46,46],color=PALE,lw=1)
            draw_text(ax,p['chapter']+'  /  '+('CONTENTS' if p['chapter']=='00' else 'RESEARCH & IMPLEMENTATION'),MARGIN,61,8.5,CRIMSON,'bold')
            draw_text(ax,p['title'],MARGIN,82,22,BLACK,'bold')
            draw_text(ax,p['subtitle'],MARGIN,115,9,MUTED)
            y=145
            for block,h,aux in plan:
                kind=block[0]
                if kind in ('p','h','callout'):
                    if kind=='callout':
                        ax.add_patch(Rectangle((MARGIN,y-3),BODY_WIDTH,h-4,color=PALE))
                        ax.add_patch(Rectangle((MARGIN,y-3),3,h-4,color=CRIMSON))
                    draw_text(ax,'\n'.join(aux),MARGIN+(12 if kind=='callout' else 0),y+(5 if kind=='callout' else 0),10 if kind=='p' else 11,BURGUNDY if kind!='p' else INK,'bold' if kind!='p' else 'normal')
                elif kind=='table':
                    widths=block[3] or [1/len(block[1])]*len(block[1]);yy=y
                    for rowidx,(cells,rh) in enumerate(aux):
                        ax.add_patch(Rectangle((MARGIN,yy),BODY_WIDTH,rh,facecolor=BURGUNDY if rowidx==0 else '#FCF4F5' if rowidx%2 else '#FFFFFF',edgecolor='none'))
                        x=MARGIN
                        for lines,w in zip(cells,widths):
                            draw_text(ax,'\n'.join(lines),x+7,yy+7,8.5,PALE if rowidx==0 else INK,'bold' if rowidx==0 else 'normal')
                            x+=BODY_WIDTH*w
                        yy+=rh
                        ax.plot([MARGIN,MARGIN+BODY_WIDTH],[yy,yy],color='#E8DADF',lw=.4)
                else:
                    image=Image.open(block[1]);iw,ih=image.size
                    boxh=block[3];boxw=min(BODY_WIDTH,boxh*iw/ih);actualh=boxw*ih/iw
                    x=MARGIN+(BODY_WIDTH-boxw)/2
                    ax.imshow(image,extent=(x,x+boxw,y+actualh,y),aspect='auto')
                    draw_text(ax,'\n'.join(aux),MARGIN,y+boxh+7,8.4,MUTED)
                y+=h
            ax.plot([MARGIN,WIDTH-MARGIN],[796,796],color=PALE,lw=1)
            draw_text(ax,'BILAL MALIK  ·  24P-3061',MARGIN,809,7.8,MUTED)
            draw_text(ax,f'{index:02d} / {len(PAGES)+1:02d}',505,809,8,CRIMSON,'bold')
            pdf.savefig(fig, dpi=220);plt.close(fig)

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
XML='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
def run(text,size=20,color='28252A',bold=False):
    return f'<w:r><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="{size}"/><w:color w:val="{color}"/>'+('<w:b/>' if bold else '')+'</w:rPr><w:t xml:space="preserve">'+escape(str(text))+'</w:t></w:r>'
def paragraph(text='',size=20,color='28252A',bold=False,style=None,before=0,after=130,keep=False,shade=None):
    props=f'<w:spacing w:before="{before}" w:after="{after}" w:line="{max(290,size*13)}" w:lineRule="exact"/>'
    if style: props+=f'<w:pStyle w:val="{style}"/>'
    if keep: props+='<w:keepNext/>'
    if shade: props+=f'<w:shd w:fill="{shade}"/>'
    return '<w:p><w:pPr>'+props+'</w:pPr>'+run(text,size,color,bold)+'</w:p>'

def build_docx(path):
    media=[]
    parts=[]
    cover=[]
    for text,size,color,bold,before,after in [
        ('RESEARCH PUBLICATION / 2026',20,'E54859',True,280,600),
        ('CODEBASE',68,'F8E8EA',True,0,380),
        ('ARCHAEOLOGIST',60,'F8E8EA',True,0,500),
        ('AI-Powered Repository Intelligence',30,'F8E8EA',False,0,150),
        ('& Defect Risk Analyzer',30,'F8E8EA',False,0,750),
        ('Unearth the Unseen.',42,'F8E8EA',False,0,700),
        ('SECURE INGESTION / REPRODUCIBLE ML / HONEST INFERENCE',16,'F8E8EA',False,0,240)]:
        cover.append(paragraph(text,size,color,bold,before=before,after=after))
    parts.append('<w:tbl><w:tblPr><w:tblW w:w="9946" w:type="dxa"/><w:tblCellMar><w:top w:w="240" w:type="dxa"/><w:left w:w="260" w:type="dxa"/><w:bottom w:w="240" w:type="dxa"/><w:right w:w="220" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="9946"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:shd w:fill="0A0A0D"/></w:tcPr>'+''.join(cover)+'</w:tc></w:tr></w:tbl>')
    parts.extend([paragraph('Bilal Malik',36,bold=True,before=500,after=260),paragraph('24P-3061 · Class 5A',24),paragraph('Department of Software Engineering (SE)',24),paragraph('FAST-NUCES, Peshawar · 2026',24),paragraph('Individual AI project, with instructor-approved solo participation.',20,before=250),paragraph('TASKS 1, 2 & 3A / ACADEMIC REPORT',18,'E54859',True,before=220)])
    for index,p in enumerate(PAGES,start=2):
        parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        parts.append(paragraph(p['chapter']+' / RESEARCH & IMPLEMENTATION',17,'E54859',True,before=100,after=220))
        parts.append(paragraph(p['title'],40,'0A0A0D',True,style='Heading1',after=320,keep=True))
        parts.append(paragraph(p['subtitle'],18,'655D63',after=280,keep=True))
        for block in p['blocks']:
            kind=block[0]
            if kind in ('p','h','callout'):
                parts.append(paragraph(block[1],20 if kind=='p' else 22,'28252A' if kind=='p' else '30151D',kind!='p',style='Heading2' if kind=='h' else None,before=60 if kind=='h' else 0,after=140,keep=kind=='h',shade='F8E8EA' if kind=='callout' else None))
            elif kind=='table':
                heads,rows,widths=block[1:];widths=widths or [1/len(heads)]*len(heads)
                t=['<w:tbl><w:tblPr><w:tblW w:w="9946" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>']
                for width in widths:t.append(f'<w:gridCol w:w="{int(width*9946)}"/>')
                t.append('</w:tblGrid>')
                for ri,row in enumerate([heads]+rows):
                    t.append('<w:tr><w:trPr><w:cantSplit/>'+('<w:tblHeader/>' if ri==0 else '')+'</w:trPr>')
                    for text,width in zip(row,widths):
                        fill='30151D' if ri==0 else 'FCF4F5' if ri%2 else 'FFFFFF'
                        t.append(f'<w:tc><w:tcPr><w:tcW w:w="{int(width*9946)}" w:type="dxa"/><w:shd w:fill="{fill}"/></w:tcPr>'+paragraph(text,17,'F8E8EA' if ri==0 else '28252A',ri==0,after=0).replace('w:line="290"','w:line="240"')+'</w:tc>')
                    t.append('</w:tr>')
                t.append('</w:tbl>');parts.append(''.join(t));parts.append(paragraph('',after=60,size=2))
            else:
                image=Path(block[1]);im=Image.open(image);iw,ih=im.size
                h=block[3];w=min(BODY_WIDTH,h*iw/ih);h=w*ih/iw
                media.append(image);n=len(media);cx,cy=int(w*12700),int(h*12700)
                parts.append(f'''<w:p><w:pPr><w:jc w:val="center"/><w:keepNext/><w:spacing w:after="80"/></w:pPr><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figure {n}" descr="{escape(block[2])}"/><a:graphic xmlns:a="{A}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{n}" name="figure{n}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="img{n}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>''')
                parts.append(paragraph(block[2],17,'655D63',after=160))
    sect='<w:sectPr><w:headerReference w:type="default" r:id="header"/><w:footerReference w:type="default" r:id="footer"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="980" w:right="980" w:bottom="980" w:left="980" w:header="400" w:footer="400"/><w:titlePg/></w:sectPr>'
    document=XML+f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'+''.join(parts)+sect+'</w:body></w:document>'
    rels=[('styles','styles','styles.xml'),('header','header','header1.xml'),('footer','footer','footer1.xml')]+[(f'img{i}','image',f'media/image{i}.png') for i in range(1,len(media)+1)]
    relationships=XML+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="{i}" Type="{R}/{t}" Target="{target}"/>' for i,t,target in rels)+'</Relationships>'
    types=XML+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'+''.join(f'<Override PartName="/word/{name}.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{typ}+xml"/>' for name,typ in [('document','document.main'),('styles','styles'),('header1','header'),('footer1','footer')])+'</Types>'
    styles=XML+f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="20"/></w:rPr></w:rPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'+''.join(f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="{i-1}"/></w:pPr></w:style>' for i in (1,2))+'</w:styles>'
    header=XML+f'<w:hdr xmlns:w="{W}">'+paragraph('CODEBASE ARCHAEOLOGIST                                      RESEARCH / 2026',16,'655D63',after=0)+'</w:hdr>'
    footer=XML+f'<w:ftr xmlns:w="{W}"><w:p>'+run('BILAL MALIK · 24P-3061                                     ',15,'655D63')+'<w:fldSimple w:instr="PAGE">'+run('1',16,'E54859')+'</w:fldSimple></w:p></w:ftr>'
    core=XML+'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>CODEBASE ARCHAEOLOGIST</dc:title><dc:creator>Bilal Malik</dc:creator><cp:lastModifiedBy>Bilal Malik</cp:lastModifiedBy><dc:subject>AI-Powered Repository Intelligence &amp; Defect Risk Analyzer</dc:subject></cp:coreProperties>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in {'[Content_Types].xml':types,'_rels/.rels':XML+f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="doc" Type="{R}/officeDocument" Target="word/document.xml"/><Relationship Id="core" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>','docProps/core.xml':core,'word/document.xml':document,'word/_rels/document.xml.rels':relationships,'word/styles.xml':styles,'word/header1.xml':header,'word/footer1.xml':footer}.items():z.writestr(name,value)
        for i,image in enumerate(media,start=1):z.write(image,f'word/media/image{i}.png')

def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='archaeologist-report-') as tmp:
        assets=Path(tmp)
        for kind in ('architecture','training','inference'):diagram(assets/(kind+'.png'),kind)
        selected_panels(assets/'distributions_selected.png',ML/'feature_distributions.png','Distributions')
        selected_panels(assets/'classes_selected.png',ML/'features_by_class.png','Classes')
        content(assets)
        contents={'chapter':'00','title':'Contents','subtitle':'An evidence-led research and implementation record','blocks':[]}
        titles={'01':('Title Page',1)}
        for number,p in enumerate(PAGES,start=3):
            if p['chapter'] not in titles:titles[p['chapter']]=(p['title'],number)
        table(contents['blocks'],['Section','Page'],[[n+'  '+title,str(pg)] for n,(title,pg) in titles.items()],[.90,.10])
        para(contents['blocks'],'Nine figures: saved EDA and confusion matrices plus three original workflow diagrams. Figures 3 and 5 reuse selected original panels; full plots remain in reports/ml/.')
        para(contents['blocks'],'Page references follow the submission PDF. DOCX edits may change pagination. Future enhancements are proposals, not implemented features.')
        PAGES.insert(0,contents)
        for p in PAGES:
            _,h=layout(p['blocks'])
            print(f'{p["chapter"]} {p["title"]}: {h:.0f} pt')
        build_pdf(OUT/'Codebase_Archaeologist_Report.pdf')
        build_docx(OUT/'Codebase_Archaeologist_Report.docx')
    evidence=[p for p in ML.iterdir() if p.suffix in ('.json','.png','.txt')]
    evidence += [ROOT/p for p in ['app/ml/features.py','app/ml/dataset.py','app/ml/prepare.py','app/ml/eda.py','app/ml/estimators.py','app/ml/train.py','app/ml/repository.py','app/ml/model_store.py','app/ml/schemas.py','app/routes/analysis.py','app/analysis/scanner.py','app/templates/dashboard.html','app/static/app.js','app/static/risk.js','tests/ml/test_repository.py']]
    manifest={'implementation_commit':'ce5d032216274d24800e61ca392c674426442851','report_date':DATE,'pdf_pages':len(PAGES)+1,'sections':19,'figures':9,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(evidence)},'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('Codebase_Archaeologist_Report.*')},'training_or_evaluation_rerun':False,'docx_rendering':'Not available in build sandbox; editable OOXML structure validated separately.'}
    (OUT/'report_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Generated {len(PAGES)+1}-page PDF and editable DOCX.')

if __name__=='__main__':main()
