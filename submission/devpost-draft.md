# Lumen - Coronary Evidence Explorer

Submission copy reflecting the executed release evidence. The remaining bracketed fields concern real human information and publication URLs; resolve those before submitting.

## Tagline

Challenge every development prediction: inspect its artery, verify its explanation, and expose its mistakes.

## Inspiration

A single CAD score hides vessel differences and the evidence behind an estimate. We built an educational interface where a user can follow a prediction from measurements to a named coronary artery, inspect its explanation, and compare it with a recorded outcome.

## What it does

Lumen predicts overall CAD and separate LAD, LCX and RCA stenosis status from the UCI extension of the Z-Alizadeh Sani dataset. Real BodyParts3D meshes make the vessels separately selectable. Selecting an artery connects the same named structure to its probability and grouped interventional linear SHAP explanation.

Five separately fitted input profiles let users compare available clinical evidence: history, examination, ECG, laboratory and echo. A same-case matrix and probability/threshold chart display all 20 estimates simultaneously. Selecting any cell updates the anatomy, required measurements and exact explanation. A downloadable comparison contains the inputs and model IDs behind every estimate. The displayed range is a comparison of fitted models, not a confidence interval, the benefit of ordering a test or a recommended care sequence.

Users can rotate, zoom, focus or isolate a named artery; inspect the complete baseline-to-score SHAP waterfall; edit inputs; and recalculate. Three entry points demonstrate tracing an artery, a flag changing across input profiles and a missed positive. Recorded labels can be revealed for unchanged cases, including mistakes. Edited inputs have no observed edited-patient outcome and cannot retain the recorded-label or original-record profile comparison.

A separate new-input mode uses frozen models fitted on the 242 development records. Development examples retain excluding-fold models rather than being presented as unseen by a model that already trained on them. The interface labels its anatomy as generic reference geometry and its output as educational decision support.

The complete cohort audit goes beyond the eight introductory examples. Browse all 242 development records across five folds; filter false alarms, missed positives and profile agreement. Every record opens in the same excluding-fold anatomy/explanation view. Filters and displayed flags share the selected research/fixed threshold rule. Outcomes are visible and used for selection: this is exploratory development review, not a blinded test. Nine recorded LCX positives are missed by all five profiles; agreement is not confidence. Selection exports preserve exact values, model IDs and source hashes.

## How we built it

Cath, LAD, LCX and RCA are excluded from every predictor set. The full-input pipeline has 55 clinical predictors. Five outer development folds evaluate a nested procedure that selects regularization, weighting and optional cross-fitted sigmoid calibration by inner out-of-fold log loss. Inner out-of-fold F1 selects a research classification threshold. Preprocessing, calibration and threshold fitting remain inside the applicable training partitions.

We froze the full-input V2 procedure before scoring the 61-record final holdout exactly once. Reduced input profiles and tree comparisons remain exploratory development evidence. Final outcomes were not used to retune the submitted models or operating rules.

Model preprocessing, coefficients and thresholds are exported to JSON. Python's standard library provides the reference inference implementation. An optional static demo computes the same models in browser memory, allowing free static hosting without a model service. Five Node checks verify 160 original outputs, 60 edited or synthetic comparisons and 32 frozen-model predictions on public development inputs against Python. Typed values are not transmitted by that client. These are software parity checks, not additional clinical samples or holdout evaluation. The public demo URL remains pending.

The SHAP attribution is additive in model log-odds, with all encoded training-fold rows as the Independent masker background. Categorical one-hot terms are grouped into their raw feature. Actual SHAP LinearExplainer verification matched all 4,840 complete-cohort case/profile/target outputs across 100 models, with maximum grouped-term error 5.55e-17 at tolerance 1e-12. The preserved 160-output certificate remains scoped to the original eight examples. Independence breaks correlations and can create invalid intermediate one-hot states; these are model associations rather than treatment effects.

Three.js renders source-identified coronary geometry. The source anatomy's FMA memberships define LAD, LCX and RCA; the app does not infer patient-specific plaque or lesion coordinates.

The demonstration was built with HyperFrames 0.8.143 and GSAP, with locally generated Kokoro af_heart English narration. It is synthetic, not a recording of the submitter. The 5 minute 42.83 second, 1920x1080, 24 fps local MP4 begins with the complete development audit, then shows real captured anatomy/profile/error interactions. All composition gates, seven narration-alignment checks and eight decoded-frame reviews passed. Source and QA are included; human release review and public/unlisted YouTube publication remain pending.

## Results

Final holdout, n=61, scored once after protocol freeze. Classification metrics use fitted thresholds chosen on development data. AUC intervals are conditional patient bootstraps of fixed test predictions and exclude refitting uncertainty.

| Target | ROC-AUC (95% interval) | Accuracy | Precision | Recall | F1 | Brier | Threshold |
|---|---|---:|---:|---:|---:|---:|---:|
| CAD | 0.908 (0.815-0.972) | 0.836 | 0.851 | 0.930 | 0.889 | 0.110 | 0.21 |
| LAD | 0.893 (0.804-0.966) | 0.852 | 0.814 | 0.972 | 0.886 | 0.126 | 0.36 |
| LCX | 0.748 (0.621-0.859) | 0.607 | 0.535 | 0.852 | 0.657 | 0.216 | 0.30 |
| RCA | 0.724 (0.579-0.844) | 0.590 | 0.500 | 0.760 | 0.603 | 0.209 | 0.25 |

Final LCX has 23 true positives, 4 false negatives and 20 false positives; RCA has 19 true positives, 6 false negatives and 19 false positives. Higher sensitivity has a substantial false-positive cost. This small same-source holdout does not establish external generalization or clinical readiness.

Development group comparisons show which predictive evidence survives with available inputs. For CAD, AUC changes from 0.828 with 17 history inputs to 0.937 with history, examination and ECG, and 0.926 with all 55 inputs. More groups do not uniformly improve every target. These comparisons are not causal test utility or a validated care sequence.

## Challenges

Vessel prediction is harder than overall CAD classification, and correlated measurements complicate explanation. A compelling 3D display does not remove those limitations. We expose per-target metrics, operating rules, source anatomy, calculation checks and case failures. A model probability is not percentage narrowing; input editing is sensitivity exploration, not a treatment simulation.

## What we are proud of

The working loop links a real development case, its excluding-fold model, a named artery and a verified explanation. V2 exported probabilities matched all 968 saved scikit-learn out-of-fold predictions within 1e-12; availability exports checked 4,840 outputs. Actual SHAP verification and 20 Python integration checks passed. Cohort browser/Python parity checks cover all 4,840 scores and grouped contributions; independent filter checks cover both decision rules. The original frontend checks retain all 64 introductory comparison paths. The final report presents all four test targets and the false-positive tradeoff, including weak vessel outcomes.

## What is next

External-cohort and prospective evaluation, clinical review, and evidence for any intended medical decisions would be needed before medical use. The current project is an educational research prototype.

## Built With

Python; scikit-learn; pandas; NumPy; SHAP; Three.js; JavaScript; HTML; CSS; ReportLab; HyperFrames; GSAP; Kokoro; UCI Machine Learning Repository; BodyParts3D; OpenAI Codex.

[ADD OTHER AI TOOLS ONLY IF ACTUALLY USED, INCLUDING CHATGPT IF SEPARATELY USED.]

## AI assistance disclosure

OpenAI Codex assisted with research, implementation, experiment/evaluation code, debugging, verification, documentation, report preparation and video preparation. Kokoro generated the English demo narration locally with its `af_heart` synthetic voice. Human review of the final code, evidence, narration and disclosures is required and has not been claimed as completed. The human submitter is responsible for the submission and judging explanations. AI assistance is not a human teammate. This disclosure follows the [official AI-tools rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules).

## Links and team fields

- Public source: [PUBLIC_GITHUB_URL]
- Six-page report: [PUBLIC_REPORT_URL_OR_REPOSITORY_PATH]
- YouTube demo, public or unlisted: [YOUTUBE_URL]
- Optional hosted demo: [HOSTED_URL_ONLY_IF_DEPLOYED]
- Track: Track A, Cardiovascular Risk Visualization & Prediction
- Human submitter and actual teammates: [REAL_FULL_NAMES_AND_DEVPOST_ACCOUNTS]
- Eligibility confirmation: [ACTUAL_ELIGIBILITY_INFORMATION]

## Resource credits

Alizadehsani, R., Roshanzamir, M., & Sani, Z. (2013). *extention of Z-Alizadeh sani dataset*. UCI Machine Learning Repository. [doi:10.24432/C5461K](https://doi.org/10.24432/C5461K). CC BY 4.0.

BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International. [Official license](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html). Anatomical parts were merged by source membership, triangulated, translated and rotated for viewing.


### Independent review and implementation checks

A fresh AI reviewer attempted six frozen tasks before inspecting the implementation or answer key. It found two interface defects, which we repaired and checked in the running browser: stale case context and false alarms labelled as misses. This is AI review; human usability and human release signoff remain pending. Local Chromium software measurements on one Apple M5 averaged about 58.6–58.7 render callbacks/s in short samples. The final capture retained all eight actions and stopped automatically after ten seconds. These timings measure software render submissions and DOM updates, not physical display latency. A 390-pixel layout was checked on the same Mac. The automated Safari rendering attempt remains unpassed. The independent dataset search admitted no compatible cohort for the frozen 55-input model; external clinical validity remains absent.
