# Cumulative feature-availability experiment

This is a real refitting experiment for five predefined input profiles. Each reduced profile has its own models, fitted preprocessing, calibration, operating thresholds and explanations. Unavailable groups are not filled with imputed values in the full-feature model.

Profiles come from `coronary-evidence/submission/clinical-groups.json`, a checked 55-feature disjoint/exhaustive mapping informed by the authors' primary papers. Separating echo and laboratory and using this cumulative ordering are our operational choices. This experiment does not establish an acquisition order, clinical utility, cost saving or causal effect of a medical test. Source-verified units and unverified units remain explicitly recorded.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python experiment_availability.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python availability_deltas.py
```

The availability run took 121.1 CPU seconds. The same 242 development rows, five outer folds and V2 inner log-loss selection/calibration/F1-threshold procedure are used for all profiles. Reduced models refit all steps inside their training partitions. The full-55 profile reuses the exact V2 models/scores. The 61-record final holdout is neither predicted nor scored. No reduced profile is selected as a final model based on this experiment.

| Profile ID | Inputs | CAD AUC / F1 | LAD AUC / F1 | LCX AUC / F1 | RCA AUC / F1 |
|---|---:|---|---|---|---|
| history | 17 | .828 / .859 | .713 / .743 | .736 / .626 | .682 / .598 |
| history_exam | 31 | .921 / .916 | .776 / .809 | .732 / .630 | .708 / .636 |
| history_exam_ecg | 38 | .937 / .905 | .798 / .812 | .714 / .608 | .726 / .619 |
| history_exam_ecg_lab | 52 | .922 / .916 | .791 / .800 | .706 / .600 | .724 / .610 |
| full | 55 | .926 / .911 | .814 / .794 | .701 / .602 | .722 / .605 |

More available recorded inputs do not uniformly improve development discrimination. These are exploratory comparisons on a small dataset and do not establish that some medical tests are harmful or unnecessary. Confidence intervals in the benchmark are conditional patient bootstraps of fixed OOF scores and omit retraining/protocol uncertainty. `paired_deltas.json` additionally uses paired resamples for each predefined incremental comparison and the full-versus-38-input comparison; no multiplicity correction is applied.

## Application contract

All artifacts live in `results-availability`:

- `profiles.json`: `profiles` array with exact `id`, `label`, `groups`, `n_features`, `feature_order`, and reduced numeric/categorical schemas. IDs are history, history_exam, history_exam_ecg, history_exam_ecg_lab and full. The source grouping's all profile is mapped to full.
- `models.json`: `models[model_id]`, using identifiers such as CAD-history-outer-0 and RCA-full-outer-4. Model numeric/categorical lists contain only the selected profile's predictors. Each includes threshold, calibration details, exact composed coefficients and training identities.
- `cases.json`: the same eight V2 development cases and selection policy. Raw `inputs` retain all 55 source fields. Each has `profile_predictions[profile_id][target]`. The default `predictions` object equals `profile_predictions.full`, using model IDs in this directory's models file.
- `benchmark.json`: `profiles[profile_id].targets[target].oof.selected` and its compatibility alias `oof.logistic` contain metrics, reliability bins and conditional AUC interval. Classification metrics use each outer model's own inner-learned threshold. `metrics_at_0_5` is provided separately.
- `development_oof.csv`: all profile probabilities, decisions and thresholds for all 242 records.
- `verification.json`: 160 selected case/profile/target predictions checked, exact feature contracts, target/holdout exclusions and full-profile score identity. The experiment checked all 4,840 portable OOF predictions against the fitted sklearn model, maximum error 3.89e-16 at tolerance 1e-12.
- `shap-verification.json`: all 160 case/profile/target explanations checked with the actual SHAP LinearExplainer and complete Independent training-fold background. See `README-explanations.md` for exact conventions and limits; displayed values can accurately be called grouped interventional linear SHAP in log-odds units.

Before invoking `predict_json`, filter a case's raw inputs to the selected profile's `feature_order`. Passing extra unavailable fields will be rejected by its exact schema contract. Label reveal must use `predicted_label` or the model's `operating_threshold`. Edited inputs have no observed edited-patient labels. Keep excluding-fold models for the public case explorer; full-development models are a separate new-input mode.

No final-development reduced models have been fitted. The default final-protocol candidate remains full-55 V2. The availability experiment provides a transparent account of input dependence rather than a winner chosen from favorable development comparisons.
