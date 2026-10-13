# Eight judge prompts and defensible answers

Current evidence, 11 October 2026. These are preparation answers, not human signoff. The human speaker should be able to explain them without reading a script and open the cited local source when challenged.

## 1. What is the contribution, and does it diagnose a lesion?

The contribution is an integrated evidence loop: clinical inputs → four model outputs → source-identified named meshes → exact contributions → recorded development outcomes. BodyParts3D supplies generic reference geometry; LAD/LCX/RCA whole-vessel colors reflect predicted probabilities. Neither a color nor a 70% probability means 70% narrowing, a plaque coordinate, or patient-specific anatomy. The dataset provides vessel-status labels, not lesion maps. This is educational research support, not a replacement for diagnostic imaging. Evidence: `public/assets/anatomy-provenance.json`, `public/app.js`, Track A's primer and visible UI disclaimer.

## 2. How did you prevent leakage and separate validation?

The 303 records were split into 242 development and 61 final holdout records using the locked seed-2026 CAD-stratified split. Cath, LAD, LCX and RCA are excluded from every predictor; the runtime rejects outcome fields. Five shared outer development folds evaluate procedures chosen using three target-stratified inner folds. Each shown development record's entire outer fold is excluded from preprocessing, fitting, calibration, threshold selection and explanation background. V2 followed V1 development inspection, so experiment-selection uncertainty remains. Evidence: `training/results/split.json`, `training/experiment_v2.py`, `inference.py`, `submission/final-protocol-freeze.json`.

## 3. What exactly is the frozen method?

The primary procedure uses all 55 predictors and regularized logistic models. Pooled inner out-of-fold log loss selects C from 0.01/0.1/1/10, class weighting, and optional cross-fitted sigmoid calibration. F1 on the selected inner predictions chooses a research threshold from 0.05–0.95 in 0.01 steps; ties favor nearest 0.5, then higher. The procedure froze at 2026-10-05 19:35:01 UTC, and the 61 holdout records were evaluated once at 19:42:48 UTC. No post-test model or threshold retuning is claimed. Calibration can differ by model; inspect the returned method. Evidence: `submission/final-protocol-freeze.json`, `artifacts/final_evaluation.json`.

## 4. What were the final results, including errors?

At each final model's development-selected threshold:

| Target | AUC | Accuracy | Precision | Recall | F1 | Brier | Cutoff | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CAD | 0.908 | 0.836 | 0.851 | 0.930 | 0.889 | 0.110 | 0.21 | 11 / 7 / 3 / 40 |
| LAD | 0.893 | 0.852 | 0.814 | 0.972 | 0.886 | 0.126 | 0.36 | 17 / 8 / 1 / 35 |
| LCX | 0.748 | 0.607 | 0.535 | 0.852 | 0.657 | 0.216 | 0.30 | 14 / 20 / 4 / 23 |
| RCA | 0.724 | 0.590 | 0.500 | 0.760 | 0.603 | 0.209 | 0.25 | 17 / 19 / 6 / 19 |

LCX/RCA recall has a substantial false-positive cost. The 1,000 patient-bootstrap intervals condition on fixed models and thresholds, omitting refitting and protocol-selection uncertainty. Small reliability bins, sigmoid calibration and Brier score do not establish reliable individual patient probabilities. This is a small single-dataset test, not external or prospective validation. Fixed-0.5 metrics are also preserved; a favorable test comparator does not justify retrospective retuning. Evidence: `artifacts/final_evaluation.json`.

## 5. What do five profiles and agreement tell us?

History, + examination, + ECG, + laboratory and full + echo contain 17/31/38/52/55 inputs. Each profile was independently fitted on the same development folds; 20 estimates means five profiles × four targets. Five outer folds × five profiles × four targets gives 100 audit models. The four final-development models are separate full-input models. Reduced profiles were not final-test candidates or evaluated on that test. In the LCX development audit, 172 records have five agreeing flags and 60 are wrong, including nine shared misses. Agreement is not confidence; profile deltas are not uncertainty intervals, causal test benefits, test-order recommendations or cost savings. Evidence: `artifacts/availability-profiles.json`, `artifacts/cohort-audit.json`.

## 6. Are these explanations really SHAP, and what do they prove?

They are grouped interventional linear SHAP in log-odds, with an Independent background of all encoded training records for the explained model. Categorical indicator terms are summed into their original feature. Baseline plus every contribution reconstructs log-odds; sigmoid produces probability. Selected sigmoid calibration is composed into coefficients/intercept. Actual `shap.LinearExplainer` checked 242 × five × four = 4,840 outputs across 100 models; maximum grouped-term difference 5.55e-17 at tolerance 1e-12. Independent masking breaks correlations and can create invalid intermediate one-hot states. Verification proves agreement with that convention, not causality, medical usefulness, or explanation uncertainty. Evidence: `public/assets/cohort-audit-verification.json`, `training/README-explanations.md`, `inference.py`.

## 7. What changes when you switch rules or edit inputs?

A rule switch changes flags and error counts while preserving probabilities, explanations and probability-based vessel colors. UCI411-057 LCX remains 43.9%; its flag changes from positive at 31% to negative at 50%. An input edit changes the score through the same excluding-fold model. UCI411-128's Age 62→63 changes full LAD 44.4%→45.4%. It has no observed edited-patient outcome, so original-label comparison is disabled and the original profile matrix pauses until restoration. This is sensitivity, not a simulated treatment effect. Nulls use fitted imputers; unresolved measurement units remain unresolved. Evidence: `public/app.js`, `inference.py`, `artifacts/cohort-audit.json`.

## 8. What did AI do, who is responsible, and what review exists?

OpenAI Codex assisted with research, code, CPU experiments, verification, documentation, report and video preparation. Kokoro generated the synthetic English narration with `af_heart`; it is not a human recording. These tools must be disclosed in README and Built With; list other tools only if actually used. AI tools are not human teammates. The real submitter owns evidence review, final submission and judging explanations. Automated checks or a fresh AI reviewer can find defects, but cannot substitute for human usability measurements or human release signoff. **Independent human review is unmeasured and pending in this kit.** Training/inference need no cloud GPU or paid model API; actual browser performance is a separate measured claim. Evidence: `README.md`, `submission/ai-disclosure.md`, `submission/video-source/README.md`.
