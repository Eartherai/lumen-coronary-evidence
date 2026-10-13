# Lumen: judging questions and code walkthrough

Judging preparation, updated 6 October 2026. Answers distinguish executed V2 development evidence from the frozen 61-record final test. Final models and input-profile switching are integrated. Keep the human speaker's wording natural and be able to show the source behind each answer. Publication URLs and actual human information remain pending.

## What problem does Lumen solve?

It lets a user follow a coronary model's estimate from recorded measurements to a named vessel on reference anatomy, inspect the score's contributors, and compare an unchanged development case with its recorded angiography labels. The contribution is the working, auditable connection between these elements. It is an educational research prototype.

## Which labels do you predict, and why exclude four columns?

There are four classification tasks: overall CAD from Cath, and vessel status for LAD, LCX and RCA. All four original angiography columns are removed from every input set. Otherwise one outcome could reveal another and produce misleadingly strong validation. Inference also rejects target fields; tests change the stored truth and confirm predictions stay the same. The supplied Track A statement explicitly requires this exclusion.

## How was the model validated?

The frozen split contains 242 development records and 61 final holdout records. The V2 procedure reuses five outer development folds. Within each outer training partition, three target-stratified inner folds select regularization, weighting and whether to use sigmoid calibration by pooled inner log loss. Preprocessing is refitted inside the relevant training partitions. The chosen procedure predicts the outer validation records it did not train on. V2 was developed after seeing V1 development results, so those results remain development evidence with experiment-selection uncertainty.

The full-input V2 procedure was frozen at 2026-10-05 19:35:01 UTC and the 61-record holdout was scored once at 19:42:48 UTC. Final CAD/LAD/LCX/RCA AUC is 0.908/0.893/0.748/0.724 and F1 is 0.889/0.886/0.657/0.603. The saved `artifacts/final_evaluation.json` records complete metrics, counts, thresholds, conditional intervals and the frozen protocol. No model retuning followed test scoring. Do not treat the inner optimization score as model performance. The separation of tuning and evaluation follows the purpose of [nested cross-validation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

## Why are thresholds below 0.5 for some vessels?

A probability estimate and a classification rule are separate. V2 selects the F1-maximizing threshold on the selected candidate's inner out-of-fold probabilities, from 0.05–0.95 in 0.01 steps. Ties favor the point nearest 0.5, then the higher point. Each outer validation record is classified using the threshold chosen without that record. This is a research operating rule, not a medical recommendation. Threshold changes affect labels and precision/recall; they do not by themselves improve probability ranking. [Threshold documentation](https://scikit-learn.org/stable/modules/classification_threshold.html)

## Did vessel predictions become more accurate?

The improvement is specifically in sensitivity and F1 at the selected operating rule, with a substantial false-positive tradeoff. V2 does not improve overall vessel discrimination over the initial baseline.

| Target | V2 development AUC | Precision | Recall | F1 | Brier |
|---|---:|---:|---:|---:|---:|
| CAD | 0.926 | 0.881 | 0.942 | 0.911 | 0.096 |
| LAD | 0.814 | 0.718 | 0.887 | 0.794 | 0.174 |
| LCX | 0.701 | 0.478 | 0.815 | 0.602 | 0.211 |
| RCA | 0.722 | 0.483 | 0.809 | 0.605 | 0.202 |

For LCX, V2 has 75 true positives, 17 false negatives, 82 false positives and 68 true negatives. For RCA it has 72 true positives, 17 false negatives, 77 false positives and 76 true negatives. Initial V1 at threshold 0.5 had LCX/RCA recall 0.228/0.236 and precision 0.636/0.724. State both sides of the change. These development numbers come from `results-v2/benchmark.json`, key `targets[target].oof.selected`. On the distinct final test, LCX has 23 TP, 4 FN and 20 FP (precision 0.535, recall 0.852); RCA has 19 TP, 6 FN and 19 FP (precision 0.500, recall 0.760). Those final errors are explicitly reported, and no clinically justified threshold is claimed.

## Does calibration make the probabilities medically reliable?

No such claim is supported. In calibrated candidates, sigmoid calibration is fitted on cross-fitted training-partition scores; inner validation records are excluded from its base fitting and calibration. V2 also considers uncalibrated candidates. The interface must show the selected model's actual method. A fitted calibration transformation does not establish reliability in another population. Brier score combines calibration and discrimination, while our reliability bins contain few examples. [Calibration documentation](https://scikit-learn.org/stable/modules/calibration.html)

## What do your confidence intervals cover?

The development AUC intervals bootstrap patients from fixed outer-fold predictions, with 1,000 draws. They are conditional on these fitted predictions and exclude refitting and experiment-selection uncertainty. They are not individual patient confidence intervals. Final test intervals likewise use 1,000 patient resamples of fixed test predictions, conditional on the frozen fitted models; they do not include refitting uncertainty. We have not performed external or prospective validation.

## Why logistic models rather than a large neural model?

They fit the available small tabular dataset quickly, can be exported faithfully into a lightweight runtime, and allow an exact score decomposition. The bounded tree probe is a development comparison: boosting modestly improves LAD on the observed folds while weakening other targets, and ExtraTrees raises LCX F1 with many more positive predictions. We do not present a per-target best-score sweep as independent validation. The primary frozen procedure is the full-input V2 logistic selection rule; reduced profiles and the tree probe remain development comparisons. No GPU is used for the current experiments.

## Is this SHAP or a causal explanation?

It is **Grouped interventional linear SHAP (log-odds)**. Actual `shap.LinearExplainer` with an `Independent` masker was run against the exported composed model. All encoded training-fold rows form the background, excluding the explained development case, its validation fold and the final holdout. All categorical one-hot terms are summed into their raw feature. All 4,840 complete-cohort outputs across 100 models passed actual-SHAP verification, maximum grouped error 5.55e-17 at tolerance 1e-12. The preserved original 160-output receipt applies only to the eight introductory cases.

For a transformed value z, training reference mean mu and coefficient beta, the interventional linear contribution is beta times (z minus mu). Baseline plus every contribution reconstructs log-odds, and sigmoid reconstructs probability. Where sigmoid calibration is selected, its slope and offset are already incorporated into the exported linear coefficients and intercept.

The Independent masker breaks feature dependencies. Intermediate masks of one-hot columns need not be valid categorical states. A correlation-aware conditional explanation could allocate credit differently. These terms are model associations, not clinical interventions, treatment effects or percentage-point probability changes. sigmoid(expected log-odds) is not mean background probability. See the [SHAP LinearExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html).

## Does the 3D model identify a lesion or severity percentage?

It displays a generic BodyParts3D heart with separate LAD, LCX and RCA groups identified by the source's FMA membership. A probability colors the whole corresponding vessel. The clinical table contains vessel status labels, not lesion coordinates or patient meshes. A 70% model probability is not 70% arterial narrowing. Reference anatomy makes the named outputs understandable; it cannot localize a patient's plaque.

## How do you know the colors correspond to the right artery?

The preprocessing manifest records source part memberships and FMA concepts: heart 7088, LAD 3862, LCX 3895 and RCA 50039. The viewer uses matching target/group keys. Picking the geometry selects that key and its prediction/explanation. The same mapping can be inspected in the anatomy conversion script and provenance JSON, rather than inferred from arbitrary screen coordinates. Show the provenance manifest, named meshes and the actual picker-to-target flow during judging.

## Why can CAD disagree with vessel estimates?

The four models are fitted independently and do not define a constrained joint probability distribution. The source development audit also preserves one CAD-versus-vessel label disagreement. We keep the separate estimates and source labels visible instead of forcing a convenient agreement or silently relabeling a record.

## Do the examples hide poor predictions?

The eight development records use a seeded selection covering recorded label patterns, not favorable outcomes. Each displayed record is predicted by an outer model that excluded it. UCI411-288 still exposes CAD/LCX/RCA false negatives in the executed V2 artifacts; the reveal compares each prediction using its own fitted threshold. The final recording should include that or another predeclared failure. Explain that a useful interface also needs to make uncertainty and errors inspectable.

## What happens when a user changes a measurement?

The backend validates the full input schema and runs the fitted artifact; the UI updates scores, artery colors and contributions. The edited case has no observed edited-patient outcome, so its original-label comparison is disabled. Restoring the original values restores the valid recorded-case comparison. This is model sensitivity, not a treatment simulation. The reveal uses the fitted model's returned predicted label and operating threshold, rather than assuming 0.5.

## What if ECG, lab or echo inputs are unavailable?

Five cumulative input profiles were separately fitted using the same development identities and outer folds. Inputs increase from 17 history features to 31 with examination, 38 with ECG, 52 with laboratory and 55 with echo. CAD development AUC is 0.828/0.921/0.937/0.922/0.926 across those profiles, so additional groups do not improve every target uniformly. Profile switching uses the corresponding excluding-fold artifacts for a development example. Reduced profiles remain development comparisons; the frozen final test evaluated the full-input primary procedure. Simply nulling a group in a full-input model would be imputation sensitivity. These deltas do not establish causal medical test utility or a care sequence.

## How do missing and unusual inputs behave?

Null values use the fitted training-fold imputer. Nonfinite numeric values, target fields, omitted fields and unknown extra fields are rejected. Categories unseen by a fitted encoder use its all-zero handling and are reported. Development-range diagnostics describe the training data rather than clinical normal ranges. Unresolved medical units remain source labels; plausible-looking units are not invented.

## How would you explain the code to a judge?

Show one complete flow rather than reciting framework names:

1. **Training:** open `experiment_v2.py`; point to frozen development identities, target exclusion, preprocessing pipeline, nested candidate selection and threshold rule. Show that outer validation identities are absent from fitting. The packaged copy is in `training/experiment_v2.py`.
2. **Export:** open one model JSON entry; explain imputer values, numeric mean/scale, category vocabulary, coefficients, intercept, reference means, fitted threshold and training identities. Describe how sigmoid calibration becomes an affine transformation of the score.
3. **Inference:** open `predict.py`/the app's `inference.py`; follow schema validation → imputation/encoding → score → sigmoid → threshold → contribution reconstruction. Explain why this function never accepts truth.
4. **API:** open `server.py`; show prediction requests, separate recorded-label reveal, and localhost static/module serving. Development cases use their excluding-fold/profile models; the new-input endpoint uses the four full-input frozen final-development models. Show the schema and returned model IDs.
5. **Viewer:** open `app.js`; follow the matching target key from prediction to named mesh color and selected explanation. Show source grouping in `prepare_anatomy.py` and the provenance manifest.
6. **Checks:** show a target-input rejection, explanation-sum check, excluded case identity and a real false-negative reveal. Reproduce a fresh installation from README if asked.

Before judging, the human submitter should be able to explain logistic regularization, why preprocessing fits within folds, how threshold tuning differs from calibration, the coordinate transform used for viewing, and one limitation demonstrated by the app. If unfamiliar with a detail, inspect the relevant source and say what the evidence establishes rather than guessing.

## Did AI build the project?

OpenAI Codex assisted with research, implementation, experiment/evaluation code, debugging, verification and draft documents. Disclose it in Built With and README as required by the [official AI-tools rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules). Add other AI tools only if actually used. The real human submitter owns verification and judging explanations. AI assistance is not a second human teammate.

## What would be needed for medical use?

The project would need external-cohort and prospective validation, appropriate clinical review, and evidence for its intended decisions and population. Those steps have not occurred. The current release is educational decision support and does not replace diagnostic imaging. The submission's defensible achievement is an integrated, reproducible and inspectable research system.

## Is the audit a new validation result?

No. It exposes all 242 existing development records with recorded outcomes used for filters. Every prediction excludes its entire outer fold. Shared learned/fixed rules keep filtered errors consistent with displayed flags. For LCX,172 records have five agreeing flags; 60 are wrong, including 9 missed positives. Agreement is not confidence. The final 61 was not retuned or rescored.

## Why not switch to a more complicated model?

The bounded 200-fit CatBoost CPU experiment improved LAD development AUC modestly (.814 to .829) while CAD/RCA weakened and LCX was unchanged. We retained all results and kept the frozen transparent primary model. These are exploratory comparisons, not a new final score.
