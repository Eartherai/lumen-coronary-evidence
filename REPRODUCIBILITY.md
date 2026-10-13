# Reproduce Lumen

The shipped application uses portable JSON weights. Running it or its integration checks does not train models or rescore the final holdout. All paths below are relative to the `coronary-evidence` directory unless stated otherwise.

## Local CPU quickstart

Prerequisites are Python 3.10 or newer, Node.js/npm and a WebGL-capable browser. The tested macOS application environment used Python 3.14.7, Node.js 24.21.0, npm 11.19.0 and Three.js 0.186.1.

```sh
npm ci
python3 server.py
```

Open **http://127.0.0.1:8766/**. Use `python3 server.py --port 8767` to change the port. Direct `file://` loading cannot load the local API and module imports. The server binds to `127.0.0.1`, does not persist input values and rejects cross-origin prediction requests. Python inference uses only the standard library; WebGL renders the reference anatomy. No GPU, hosted model API or training package is required. Initial npm installation needs package access; optional Google Fonts have system-font fallbacks.

Run the original and complete-cohort runtime checks:

```sh
python3 -m unittest discover -s tests -v
node tests/test_journey.mjs
node --test tests/test_cohort_static.mjs tests/test_cohort_filters.mjs tests/test_static_client.mjs tests/test_runtime_probe.mjs tests/test_outcome_description.mjs tests/test_case_transition.mjs
```

The checks exercise exact input contracts, all case/profile model routes, excluded case identities, label separation, threshold agreement, explanation sums, editable values, missing/unknown inputs and final-development routing for unlabelled inputs. They never read the holdout workbook rows or recompute final metrics.

## Static browser runtime

`public/static-client.js` implements the same API value contract using the shipped portable weights. Build with `python3 scripts/build_static_demo.py`, then run `node --test tests/test_static_client.mjs`. The five Node checks cover all 160 original case/profile/target outputs, 60 edited/missing/unknown/synthetic Python comparisons, 32 frozen-model comparisons on public development inputs, rejection behavior and actual HTTP loading under a repository prefix. Prediction calls do not transmit inputs. `node tests/test_journey.mjs` also checks every one of the 64 case/target/decision-rule paths, including changing thresholds.

The static builder copies the eight original introductory examples and a separate complete 242-record development audit, portable weights, reference geometry and aggregate evidence into `dist/site`. It excludes final holdout input records and per-row final prediction CSVs. It checks every development identity, entire-fold/holdout training exclusion and exact source-bound 4,840-output SHAP certificate before building. The audit explicitly uses recorded outcomes for filtering; label reveal is an educational interaction, not a secrecy boundary. The manifest records exact hashes; the Pages workflow is prepared but no public URL is claimed.

The separate cohort Node tests compare all 4,840 browser probabilities, log-odds, baselines and grouped terms with Python; test case/journey/label/edit routes across all five folds; and verify cached inference sends no POST. Filter tests independently recompute all target/outcome/agreement/fold combinations under both decision rules. [Complete audit guide](docs/cohort-audit.md) and [actual-SHAP reproduction](training/cohort-audit-verification/README.md).

## Included evidence and artifact routing

| Path | Purpose |
|---|---|
| `training/extention of Z-Alizadeh sani dataset.xlsx` | Original public UCI workbook, 303 records |
| `training/download.json` | Original archive URL and download hash |
| `training/results/split.json` | Workbook SHA-256; 242 development and 61 holdout row identities |
| `training/results/` | Historical V1 benchmark, fixed-0.5 OOF predictions and fold models |
| `training/results-v2/` | Primary nested probability/calibration/threshold development procedure |
| `training/results-v3/` | Bounded exploratory tree comparison; not integrated into the app |
| `training/results-availability/` | Five profile specifications, models, OOF results and verification records |
| `training/results-final-development/` | Four models fitted on development data, fit diagnostics and once-only final evaluation record |
| `submission/final-protocol-freeze.json` | Pre-evaluation method, source hashes and no-retuning policy |
| `artifacts/` | Portable application weights, examples, schemas and metric JSON |
| `public/assets/anatomy-provenance.json` | Official anatomy membership, hashes and mesh modifications |
| `output/pdf/lumen-report.pdf` | Verified six-page technical report |

Row indices are zero-based workbook data rows, excluding the Excel header. The seed-2026 split is CAD-stratified. Cath maps to the displayed CAD target; original Cath, LAD, LCX and RCA columns are excluded from every model's 55 predictors. Source category spelling, including `Fmale`, is preserved for encoding. Development data had no missing cells or duplicate predictor rows and one overall-CAD/vessel-label disagreement; original labels were retained.

The case explorer uses eight development examples selected by recorded label patterns and a fixed seed, not favorable prediction results. Each case/profile/target prediction uses that case's excluding outer-fold model. There are five profiles with 17, 31, 38, 52 and 55 inputs; the exact exhaustive, disjoint grouping is in `submission/clinical-groups.json`. Laboratory versus echocardiography separation and the cumulative order are operational choices, not a validated sequence of care.

The unlabelled input form uses `artifacts/final_models.json`, fitted on exactly 242 development records. Its four model IDs end in `-final-development`. It accepts only the full 55-input profile. Development examples retain models ending in their excluding `-outer-N` fold. Using a final-development model on a development record would not be unseen evaluation. Editing an example disables label comparison because there is no observed modified-patient outcome.

`inference.py` implements the same portable predictor as `training/predict.py`. JSON contains fitted imputers, scales, categorical encoders, coefficients, intercepts, training reference means, calibration composition and thresholds. Joblib pipelines are historical training outputs; the live app loads JSON, not joblib.

## Exact training environment

Training and SHAP verification used Python **3.12.13**, scikit-learn **1.9.1**, NumPy **2.5.3**, pandas **3.0.6**, SciPy **1.18.1**, joblib **1.6.0** and openpyxl **3.1.5**, on macOS arm64. `requirements-training.txt` and `training/requirements-training.txt` pin those package versions. SHAP verification additionally pins SHAP **0.52.0**, numba **0.68.0**, llvmlite **0.50.0** and slicer **0.0.8** in `training/requirements-explanation.txt`. The complete recorded explanation environment, including threadpoolctl 3.7.0, is in `training/results-availability/explanation-version-manifest.json`.

A Python 3.12 training environment can be created without affecting the standard-library app:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r training/requirements-explanation.txt
```

Use the exact recorded environment for closest numeric reproducibility. Different library/platform versions may change optimization or serialization slightly; timings are measurements of this machine, not performance guarantees. Set the following when running historical experiments to limit numerical-library threads:

```sh
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
```

## Historical development experiments

All development experiments use the frozen 242 identities and exclude holdout records from fitting and validation. They use five shared CAD-stratified outer folds and target-stratified inner selection. Preprocessing is fitted inside each training partition. The original script notes describe their development-only state at execution; `artifacts/final_evaluation.json` and the final protocol are the current evaluation record.

| Experiment | Selection and evaluation | Recorded CPU elapsed time |
|---|---|---:|
| V1 | Regularized logistic C selected by three-fold inner ROC-AUC; threshold fixed at 0.5; prior/small-tree comparisons | 14.4 s |
| V2 | Four logistic weighting/calibration families × four C values; pooled three-fold inner log loss; inner F1 threshold; five-fold outer evaluation | 39.6 s |
| V3 | Two configurations each for ExtraTrees and regularized boosting; inner selection and F1 threshold; exploratory outer results | 20.0 s |
| Availability | Four reduced profiles independently refitted with V2; exact full-profile V2 reuse | 121.1 s |

For V2, C is 0.01, 0.1, 1 or 10. The candidate families are unweighted, balanced, unweighted plus sigmoid calibration and balanced plus sigmoid calibration. Calibrated models use three additional cross-fitted calibration subfolds with `ensemble=False`, so the relevant validation cases are excluded from base fitting and calibration. The selected candidate maximizes inner OOF F1 over thresholds 0.05 through 0.95 in 0.01 steps; ties favor proximity to 0.5, then the higher value. All classification metrics use the excluding model's fitted threshold. Conventional 0.5 comparisons are saved separately.

V2 was designed after inspecting V1 development results. Development intervals resample fixed OOF predictions and omit retraining and experiment-selection uncertainty. The tree and profile comparisons remain exploratory; no best target/profile was selected from outer scores and re-labelled as final test performance.

To rerun historical development experiments, use a **separate working copy** so the archived artifacts, frozen source hashes and release evidence remain intact. These scripts write their fixed result directories. From the working copy's project directory, after creating the training environment:

```sh
.venv/bin/python training/benchmark.py
.venv/bin/python training/experiment_v2.py
.venv/bin/python training/verify_v2.py
.venv/bin/python training/experiment_v3.py
.venv/bin/python training/experiment_availability.py
.venv/bin/python training/verify_shap.py
```

V1 precedes V2, and V2 precedes availability. Availability also requires `submission/clinical-groups.json`. These commands do not call the final evaluator. The package preserves final results for inspection; the final fit/evaluation commands are intentionally not part of ordinary reproduction or the app quickstart.

To copy existing development and final artifacts into an app working copy, without fitting or scoring:

```sh
python3 scripts/sync_models.py --source training/results-v2
python3 -m unittest discover -s tests -v
```

The sync script copies availability artifacts and frozen final-development models/evaluation when present, and copies `training/predict.py` to `inference.py`. It does not recompute SHAP verification or rebuild anatomy. Restart the server after syncing.

## Frozen final evaluation record

The primary **full 55-input V2 procedure** was frozen at 2026-10-05T19:35:01.194619+00:00. Four development-only models used inner selection, calibration and F1 threshold fitting on the 242 development identities. The final evaluation completed once at 2026-10-05T19:42:48.834689+00:00, on all 61 reserved identities. Reduced profiles were not scored there. No fitting, calibration, threshold selection or post-evaluation retuning used those outcomes.

| Target | AUC | F1 | Precision | Recall | Threshold | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---|
| CAD | 0.908 | 0.889 | 0.851 | 0.930 | 0.21 | 11 / 7 / 3 / 40 |
| LAD | 0.893 | 0.886 | 0.814 | 0.972 | 0.36 | 17 / 8 / 1 / 35 |
| LCX | 0.748 | 0.657 | 0.535 | 0.852 | 0.30 | 14 / 20 / 4 / 23 |
| RCA | 0.724 | 0.603 | 0.500 | 0.760 | 0.25 | 17 / 19 / 6 / 19 |

`training/results-final-development/final_evaluation.json` contains full metrics, conditional intervals, calibration bins and provenance; `artifacts/final_evaluation.json` is its application copy. The evaluator validates the freeze, workbook, split, source and model hashes before holdout access. Its exclusive `final_evaluation.started.json` claim and result creation refuse a second run. Retain the existing claim/results; do not remove them to evade the once-only contract. `fit_final_development.py` likewise refuses to silently overwrite an existing fit.

The final 1,000 patient-bootstrap samples reuse fixed predictions and thresholds, with no refitting. Intervals omit model/threshold/protocol-selection uncertainty. They are not individual-patient confidence intervals. The 61-record holdout is small and comes from the same public dataset; there is no external or prospective validation. In particular, LCX/RCA have substantial false-positive counts, and probability calibration is not established by the fitting method alone.

For a read-only hash check, the recorded identities are:

| Artifact | SHA-256 |
|---|---|
| Included workbook | `739343245c2ba578b541370217531750d8e936022f928b83e0d91756caa3ff0b` |
| Frozen split | `9f7d16b087155205a77227d812786f0d651b589f5633e9705210c03c4e62871b` |
| Protocol freeze | `47749cd2a5aa944eb531a6eeb54386cad5e5b29bad9ffa11b048d6715ccc1305` |
| Final portable models | `04bb3286e0dc593ad2b1f611fef7655bb6457beb421fe231f068e482c4dc52e6` |
| Final evaluation JSON | `80833dc966a78226edb378b810e9e4efcca71b56c12071632d7f4ae21c3f2944` |

For example, `shasum -a 256 artifacts/final_evaluation.json` should match the final row. Source hashes and environment versions are also recorded inside the evaluation JSON and freeze document.

## Portable inference and actual SHAP verification

The V2 export check compared all 968 target/OOF probabilities with scikit-learn, maximum absolute difference 3.33e-16. Availability checked **4,840** probabilities, maximum difference **3.89e-16**, tolerance 1e-12. `training/results-availability/verification.json` also checks 160 case/profile/target outputs, exact reduced feature membership, training exclusions and full-profile identity to V2.

The explanation verification uses the actual `shap.LinearExplainer`, `shap.maskers.Independent` and an identity link on the exported composed linear score. Every model's background contains all its encoded training records, with `max_samples` set to their full count; the explained case, its validation fold and holdout records are excluded. Numeric preprocessing and categorical encoding are reconstructed without refitting. Calibrated models already compose the calibration slope/offset into their coefficients/intercept. Indicator SHAP values are summed to each original categorical feature.

The approved display name is **Grouped interventional linear SHAP (log-odds)**. The preserved introductory-case certificate covered **160 outputs, 60 distinct models, 8,960 encoded values and 120 sigmoid-calibrated predictions**. The complete-cohort certificate separately covers **4,840 outputs across 100 models**, maximum grouped-term error5.55e-17; see `training/cohort-audit-verification/README.md`. Maximum errors were 6.94e-18 for grouped contributions, 4.44e-16 for the baseline, 1.55e-15 for reconstructed log-odds and 3.33e-16 for probability. The tolerance was 1e-12; no model, calibration or threshold changed. The full evidence and package/source hashes are in `training/results-availability/shap-verification.json` and `explanation-version-manifest.json`; a browser-readable copy is at `public/assets/shap-verification.json`.

Independent masking breaks correlations and can create invalid intermediate one-hot states. Conditional explanations can assign credit differently. Terms add in log-odds, not percentage-point probability space. Sigmoid of expected background log-odds is not average background probability. The terms describe this model, not causal interventions, treatment recommendations, clinical utility or explanation uncertainty. See the [SHAP LinearExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) and [Independent masker documentation](https://shap.readthedocs.io/en/latest/generated/shap.maskers.Independent.html).

## Anatomy, licenses and release state

Anatomy comes from the official BodyParts3D archive. Per-file CRC32/SHA-256 and official part memberships were checked before merging, triangulating, rounding, translating and rotating the reference meshes. Heart/LAD/LCX/RCA concepts are FMA 7088/3862/3895/50039. No patient-specific geometry or lesions were generated. `public/assets/anatomy-provenance.json` records the transformations and source hashes.

Project code is MIT. The UCI dataset and BodyParts3D retain CC BY 4.0 licenses and attribution requirements; dependencies and fonts retain their licenses. Review [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution. Keep the original source manifests and notices in any release archive.

The latest dated technical report is `output/pdf/lumen-report-hardening-r2-2026-10-11.pdf`: six pages, SHA256 `e2ddf023ec79fe71c9de1697794e6e9193917fc38d3f17e54121c64c8dd5903b`. Each rendered page passed AI visual review; its adjacent provenance and QA receipts bind the saved sources and page images. It covers current stale-prediction error/control ownership, dated failed-load recovery and keyboard checks, the complete 242-development-record audit and separate unchanged 61-record final evaluation. `submission/build_report_hardening_r2_20261011.py` reads saved evidence and does not fit or evaluate a model. Earlier reports remain dated artifacts. See `submission/HARDENING-EVIDENCE-2026-10-11.md` for the actual browser failure checks and their limits.

The verified local demo is [output/video/lumen-demo.mp4](output/video/lumen-demo.mp4): 1920x1080, 24 fps, H.264/AAC, 342.833333 seconds. SHA256 `50ac052afe6f583e79d6deb02b6c40fcfb4dd106e499b1a10dbdb6173cabe53e`. The complete-cohort opening uses actual labelled static screenshots; six original chapters retain real interaction clips. All seven narration-alignment checks and eight encoded-frame inspections passed; the minimum five-second audio correlation was 0.950. HyperFrames was upgraded 0.8.134 to 0.8.143 and its checks passed. Local Kokoro af_heart generated English narration; no training GPU or cloud rendering. [Source and rerender commands](submission/video-source/README.md).

Before publication, package code, portable weights, the split, training source, public workbook, provenance, disclosures, report and demo materials. Exclude credentials, caches, `node_modules` and temporary captures. Record SHA-256 values for the actual packaged files. Public GitHub/YouTube links, real-human team names/accounts/eligibility and the Devpost submission are still unconfirmed; the release owner tracks those in `submission/release-status.json`. A local report or demo does not establish external publication.

OpenAI Codex assisted with research, code, experiments, tests, anatomical integration, explanation verification, report/video preparation and documentation. Kokoro generated the English narration locally; its `af_heart` voice is synthetic and does not impersonate or record the submitter. Human submitters must review the final evidence, code, narration and disclosures and be able to explain their work; that review has not been asserted as complete. Add OpenAI Codex and Kokoro, plus any additional AI tools actually used, to Devpost Built With as required by the [official rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules). Add ChatGPT if separately used. AI assistance does not count as a human team member. See `submission/ai-disclosure.md` for the disclosure draft.

## Release verification records

`submission/release-verification.json` records clean payload verification. Its content digest covers the sorted source-manifest entries excluding that record itself, so including the record in the source ZIP does not create a self-referential hash. The separately generated `dist/release-verification.json` identifies the exact ZIP bytes. Rebuild and verify a local release with:

```sh
python3 scripts/build_release.py
python3 scripts/verify_release.py --archive dist/lumen-submission-source.zip --output dist/release-verification.json
```

These checks extract a temporary folder, check hashes, install cached dependencies, run app contract checks and verify development SHAP equivalence. They neither retrain models nor repeat the final evaluation. `--content-record` refreshes the in-package record; rebuild the ZIP afterward, then generate its exact sidecar.
