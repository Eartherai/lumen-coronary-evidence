# Lumen — Coronary Evidence Explorer

Lumen makes coronary predictions inspectable across the complete 242-record development cohort. Find false alarms, missed positives and flags that change across five independently fitted input profiles. Open any record in named artery anatomy, trace its exact score, and compare the recorded outcome. Four prediction targets, fold-excluded models and 4,840 actual-SHAP checks support the evidence loop. Training runs on CPU; inference needs no hosted model API or machine-learning packages.

This is educational decision support and does not replace diagnostic imaging. The meshes are generic reference anatomy; vessel colors do not locate plaque or represent patient-specific imaging.

The 11 October interface redesign uses locally served Figtree, a light workspace around the actual navy anatomy stage, compact case disclosures, and navigation that tracks the visible section. Phone and tablet controls keep model estimates, edited inputs and recorded outcomes distinct. [Current UI and export status](submission/UI-REDESIGN-2026-10-11.md). Frozen scientific models, thresholds and final-test results are unchanged. Older screenshots, films and dated software receipts below describe earlier interface revisions.

![The redesigned Lumen workspace with the real generic BodyParts3D anatomy and a public development record](public/assets/lumen-ui-2026-10-11.jpg)

![The same public development record compared across five independently fitted profiles](public/assets/demo-comparison.png)

![An uncurated recorded positive missed by all five profiles, from the complete development audit](output/cohort-browser-review/cohort-stable-lcx-miss.png)

The audit uses recorded development outcomes for selection. It is exploratory review, not a new blinded or final-test score. Agreement is not confidence: under each model's research threshold, all five LCX profiles agree on 172 records and are wrong on 60. [Audit guide, scope and verification](docs/cohort-audit.md).

## Run locally

Prerequisites: Python 3.10 or newer, Node.js/npm, and a browser with WebGL support. The tested application environment used Python 3.14.7, Node.js 24.21.0 and npm 11.19.0 on macOS. Run from this directory:

```sh
npm ci
python3 server.py
```

Open **http://127.0.0.1:8766/**. The shipped JSON weights and anatomy are sufficient to run the app; training is optional. Use `python3 server.py --port 8767` if the default port is occupied. Opening `public/index.html` as a file cannot load the local API or module dependencies.

Python's standard library performs inference, and locally installed Three.js 0.186.1 renders the anatomy using ordinary browser graphics. After npm installation, model inference and geometry loading are local. Figtree is served from the included font file with a system-font fallback. The server binds to localhost and does not persist entered inputs.

## Browser-only judge demo

An optional static build runs the same portable models entirely in the browser, with no Python inference service or paid API. Build and preview it from this directory:

```sh
npm ci
python3 scripts/build_static_demo.py
node --test tests/test_static_client.mjs
python3 -m http.server 8768 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:8768/site/** and select **Cohort audit**. Legacy Node checks verify all 160 introductory-case predictions plus edited/missing/unknown/synthetic-input comparisons. Separate cohort checks verify all 4,840 browser probabilities, scores, baselines and grouped terms against Python, all 100 fold exclusions, outcomes separated from prediction routes, and cached inference without POST requests. None recomputes holdout outcomes or metrics. Entered values remain in browser memory; public development inputs and recorded labels are included in the downloadable bundle. The approximately 9.38 MB site contains no final holdout input rows.

The included [Pages workflow](.github/workflows/pages.yml) can publish the site after a real GitHub repository exists and Pages is enabled with GitHub Actions as its source. A hosted URL is not yet claimed. The local Python app remains the reference API implementation.

## Independent AI review and local runtime evidence

A fresh AI reviewer tried six frozen tasks before reading the implementation or answer key. It found two P2 defects: a stale case notice and false alarms described as misses. Both were repaired and checked in the actual browser. Human usability and human release signoff remain pending. The [dated review, fixes and verification](docs/review-hardening-2026-10-11.md) keeps AI findings separate from human evidence.

The opt-in runtime diagnostic records local render callbacks and action-to-DOM/next-callback times without entered clinical values, predictions or labels. A dated Chromium sample on this Apple M5 averaged 58.6 callbacks/s with eight actions taking 6.9–19.7 ms to update the DOM; it also contained a 264.2 ms callback interval. These software timings at 683 × 760 are not physical display latency or a general laptop benchmark. A 390-pixel layout and artery isolation were checked on the same Mac. The attempted Safari rendering check remains unpassed; no second physical device was tested. Capture timers finish even if rendering stops, incomplete actions stay visible, and lost graphics contexts invalidate frame-rate claims.

An independent dataset search found no cohort eligible for the frozen 55-input, four-target schema. Its [admission dossier](research/lumen-external-cohort-2026-10-11/README.md) records missing inputs and unresolved endpoint mappings. No external validation result is claimed.

The [11 October UI hardening note](submission/HARDENING-EVIDENCE-2026-10-11.md) records actual injected case/profile load failures, restoration of the prior loaded state, successful retries and keyboard focus retained during prediction/profile selection. The frozen models and final evaluation remain unchanged. The new [six-page hardening report](output/pdf/lumen-report-hardening-2026-10-11.pdf) has exact source bindings and rendered-page QA; human usability/signoff, external validation and public publication remain pending.

## What the demo shows

- Eight real UCI development cases, including failures. Each case uses four outer-fold models whose preprocessing, fitting, calibration and threshold selection excluded that case.
- A separate complete cohort audit adds every one of the 242 development records, spanning all five folds. Outcome, profile-agreement, fold and record-ID filters share the case explorer's learned/fixed decision rule. Probability, recorded label, flag and all five profile cutoffs appear together. Each record opens the same anatomy/explanation workflow; a source-bound JSON export preserves the selection.
- Separate overall CAD, LAD, LCX and RCA probabilities. Select an artery to inspect its BodyParts3D geometry and the six largest grouped interventional linear SHAP contributions in log-odds units.
- Orbit, zoom, overview, opposite-view, mesh-based artery focus and isolation controls. Colors apply to whole named reference vessels.
- Five cumulative input profiles: history (17 inputs), history plus examination (31), plus ECG (38), plus laboratory (52), and all groups including echocardiography (55). Reduced profiles have their own fitted models; unavailable groups are not merely imputed in a full-input model.
- A simultaneous same-case comparison shows all 20 probabilities and each model's actual threshold. Select any cell to synchronize the anatomy, inputs and explanation. The comparison can be downloaded with exact inputs, model IDs and contributions; recorded outcomes are excluded. Its JSON is also viewable in the app for environments that do not handle downloads. The range across profiles is not an uncertainty interval or the effect of ordering a test. Edited and unlabelled inputs cannot retain this original-record comparison.
- A complete log-odds waterfall adds the baseline, six largest terms and every remaining term, then applies sigmoid only at the endpoint. The three-button evidence loop opens an anatomy example, a changing-profile example and a visible model failure.
- Recorded-label reveal after prediction inspection. Agreement uses each model's training-selected research threshold by default; a fixed 50% comparison is also available. Both errors and correct predictions remain visible.
- Editable measurements with real Python inference. Edited development cases retain their excluding-fold model, but recorded-outcome comparison is disabled because no edited-patient outcome was observed. Null values use the fitted imputer; range and unknown-category diagnostics are reported.
- A separate unlabelled input form using the four frozen models fitted on all 242 development records. Its illustrative defaults are not an observed patient and have no recorded outcome. This mode uses all 55 inputs.
- Development/profile metrics and the separate frozen final evaluation, with provenance and limitations. All four label columns are excluded from every predictor.

## Frozen final evaluation

The public dataset has 303 records and 55 predictors after excluding Cath, LAD, LCX and RCA. A seed-2026 CAD-stratified split reserved 61 records and kept 242 for development. The full-input V2 procedure was frozen at **2026-10-05 19:35:01 UTC** and evaluated on the 61-record holdout **once**, at **2026-10-05 19:42:48 UTC**. Models, calibration, thresholds and profile choice were not tuned on those outcomes.

The table uses each final model's development-selected F1 threshold. AUC and Brier depend on probabilities, not on that decision threshold.

| Target | ROC-AUC (conditional 95% interval) | Accuracy | Precision | Recall | F1 | Brier | Threshold |
|---|---|---:|---:|---:|---:|---:|---:|
| CAD | 0.908 (0.815–0.972) | 0.836 | 0.851 | 0.930 | 0.889 | 0.110 | 0.21 |
| LAD | 0.893 (0.804–0.966) | 0.852 | 0.814 | 0.972 | 0.886 | 0.126 | 0.36 |
| LCX | 0.748 (0.621–0.859) | 0.607 | 0.535 | 0.852 | 0.657 | 0.216 | 0.30 |
| RCA | 0.724 (0.579–0.844) | 0.590 | 0.500 | 0.760 | 0.603 | 0.209 | 0.25 |

The LCX model produced **20 false positives and 4 false negatives**; RCA produced **19 false positives and 6 false negatives**. Higher vessel recall carries a substantial false-positive cost. These are research operating points, not validated medical thresholds.

Full metrics, counts, fixed-0.5 comparisons, reliability bins and source/model hashes are in [artifacts/final_evaluation.json](artifacts/final_evaluation.json). The 1,000-resample patient-bootstrap intervals condition on fixed fitted models and thresholds; they omit retraining and protocol-selection uncertainty. This small, single-dataset test is not external or prospective clinical validation. A calibration step or Brier score alone does not establish calibrated individual probabilities.

## Development evidence and input availability

V2 uses five shared outer folds and three target-stratified inner folds. Inner OOF log loss selects regularization, class weighting and optional cross-fitted sigmoid calibration. Inner predictions also select the F1 threshold; outer validation evaluates the complete procedure. V2 was designed after inspecting V1 development results, so these remain development results.

| Target | V2 development ROC-AUC | Precision | Recall | F1 | Brier |
|---|---:|---:|---:|---:|---:|
| CAD | 0.926 | 0.881 | 0.942 | 0.911 | 0.096 |
| LAD | 0.814 | 0.718 | 0.887 | 0.794 | 0.174 |
| LCX | 0.701 | 0.478 | 0.815 | 0.602 | 0.211 |
| RCA | 0.722 | 0.483 | 0.809 | 0.605 | 0.202 |

Compared with V1's fixed-0.5 procedure, LCX/RCA development recall rose from 0.228/0.236 to 0.815/0.809 while precision fell from 0.636/0.724 to 0.478/0.483. Their AUC did not improve. The bounded V3 tree comparison is archived and was not substituted into the app.

The profile comparison reuses the same development identities and outer folds, refitting every reduced procedure. The full profile reuses the exact V2 models and scores.

| Cumulative profile | Inputs | CAD AUC | LAD AUC | LCX AUC | RCA AUC |
|---|---:|---:|---:|---:|---:|
| History | 17 | 0.828 | 0.713 | 0.736 | 0.682 |
| + examination | 31 | 0.921 | 0.776 | 0.732 | 0.708 |
| + ECG | 38 | 0.937 | 0.798 | 0.714 | 0.726 |
| + laboratory | 52 | 0.922 | 0.791 | 0.706 | 0.724 |
| + echocardiography (full) | 55 | 0.926 | 0.814 | 0.701 | 0.722 |

These exploratory comparisons do not establish a clinical acquisition order, test cost saving or causal utility. More recorded inputs did not uniformly improve development discrimination. The reduced profiles were not evaluated on the final holdout or chosen to replace the frozen primary profile. Exact memberships, verified units and source limits are in [submission/clinical-groups.json](submission/clinical-groups.json); full evidence is in [artifacts/availability-benchmark.json](artifacts/availability-benchmark.json).

## Explanation verification and limits

The exported explanation is **grouped interventional linear SHAP (log-odds)**. Actual `shap.LinearExplainer` with a complete model-specific `Independent` background verified all **4,840 complete-cohort outputs across 100 models**. Maximum grouped-term error was **5.55e-17**, within tolerance 1e-12. Every background excludes the entire explained outer fold and all holdout records. [Full-cohort certificate and commands](training/cohort-audit-verification/README.md). The preserved original certificate separately verifies 160 outputs from the eight introductory cases, with maximum grouped-term difference 6.94e-18. No weights or thresholds changed during either verification.

The baseline plus every feature contribution reconstructs the model's log-odds exactly; sigmoid gives its probability. Calibrated linear models include the fitted sigmoid slope and offset in the exported coefficients and intercept. Categorical indicator contributions are summed into their original feature.

Independent masking breaks predictor dependencies and can form invalid intermediate one-hot states. Correlated clinical variables may receive different attribution under a conditional explanation. Values are model associations, not causal treatment effects or percentage-point probability changes. The sigmoid of expected background log-odds is not mean background probability. Verification establishes agreement with this SHAP convention, not clinical validity or explanation uncertainty. See [training/README-explanations.md](training/README-explanations.md) and [the verification record](training/results-availability/shap-verification.json).

The four models do not impose a coherent joint CAD/vessel distribution. One development record's overall CAD label disagreed with its vessel labels; original labels were retained. Observed input ranges are dataset ranges, not medically accepted ranges. Several source measurement units remain unverified and are not invented.

## Reproduce and inspect

The self-contained [reproducibility guide](REPRODUCIBILITY.md) covers dependencies, archived experiments, artifact checks and the once-only evaluation record. The original and cohort Python integration checks and frontend checks run without training packages:

```sh
python3 -m unittest discover -s tests -v
node tests/test_journey.mjs
node --test tests/test_cohort_filters.mjs tests/test_cohort_static.mjs tests/test_outcome_description.mjs tests/test_runtime_probe.mjs
```

They cover case exclusions, exact profile contracts, rejected target inputs, contribution reconstruction, portable predictions, separate label reveal, edits, input diagnostics and new-input model routing. The comparison checks cover every one of the 64 case/target/decision-rule paths. They do not rescore the final holdout. All 4,840 profile OOF probabilities were independently checked against scikit-learn; maximum difference was 3.89e-16 at tolerance 1e-12.

The [six-page technical report](output/pdf/lumen-report.pdf), [verified narrated demo](output/video/lumen-demo.mp4), [Devpost draft](submission/devpost-draft.md), [demo plan](submission/demo-plan.md) and [judge Q&A](submission/judge-qa.md) are included. Every report page passed rendered visual review. The demo is 1920x1080 at 24 fps, lasts 5 minutes 42.83 seconds, with H264/AAC English synthetic Kokoro narration. All composition gates, seven narration-alignment checks and eight encoded-frame inspections passed. [Video QA](output/video/video-qa.json) and [rerendering source](submission/video-source/README.md). Public GitHub/YouTube URLs, real human information and Devpost submission remain pending; see [release status](submission/release-status.json). Competition placement and track crowding are unknown.

## Sources and licenses

- Data: R. Alizadehsani, M. Roshanzamir and Z. Sani, [UCI extension of Z-Alizadeh Sani, dataset 411](https://archive.ics.uci.edu/dataset/411/extention+of+z+alizadeh+sani+dataset), DOI [10.24432/C5461K](https://doi.org/10.24432/C5461K), CC BY 4.0. The included workbook, download manifest and frozen split record source hashes. Feature groups were informed by the [authors' primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4253773/); splitting laboratory/echo and the cumulative ordering are our choices.
- Anatomy: BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International. [Official archive license](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html). FMA concepts: heart 7088, LAD 3862, LCX 3895, RCA 50039. Part memberships, hashes and modifications are in [public/assets/anatomy-provenance.json](public/assets/anatomy-provenance.json).
- Project code: [MIT](LICENSE). Dataset, meshes and dependencies retain their own licenses. Three.js 0.186.1 is MIT; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution.

## AI assistance disclosure

OpenAI Codex assisted with track and source research, software implementation, CPU model experiments, tests, anatomical integration, explanation verification, report preparation, video preparation and documentation. Kokoro generated the English demo narration locally with its `af_heart` voice; the narration is synthetic and is not a recording of the human submitter. HyperFrames and GSAP build the video composition. Human review of the final release is still required, including the code, evidence, narration and disclosures, and the submitter must be able to explain the system during judging. AI tools are not human team members. List the AI tools actually used in Devpost **Built With**, including OpenAI Codex and Kokoro, as required by the [official rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules). Add ChatGPT if separately used. Additional wording is in [submission/ai-disclosure.md](submission/ai-disclosure.md); no human name, student eligibility or publication account is inferred.
