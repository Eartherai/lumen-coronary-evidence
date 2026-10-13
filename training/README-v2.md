# Nested probability and threshold experiment

V2 improves development recall and F1 for LCX/RCA through a different research operating threshold. Discrimination does not improve over V1. Higher recall comes with many more false positives. The 61-record final holdout remains frozen and unscored by all scripts in this directory.

## Reproduce

Run from this model directory:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python experiment_v2.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python verify_v2.py
```

Outputs are separate in `results-v2`. V1 artifacts in `results` are preserved. V2 ran in 39.6 CPU seconds with scikit-learn 1.9.1. The reported runtime includes the bounded model search, portable model validation, conditional bootstraps and artifact creation.

## Protocol

1. Load only the 242 frozen development row identities from `results/split.json`. Verify the original XLSX SHA-256. Exclude Cath, LAD, LCX and RCA from all 55 predictors.
2. Reuse the five shared CAD-stratified outer folds from V1, seed 2026.
3. Each outer training partition has three target-stratified inner folds, seed 2026 + outer fold. Numeric imputation/scaling and categorical imputation/encoding are fitted inside every training partition.
4. Compare four linear model families: unweighted logistic, balanced logistic, unweighted logistic plus sigmoid calibration, and balanced logistic plus sigmoid calibration. Each has C = 0.01, 0.1, 1, 10. Choose the family and C with the lowest pooled inner OOF log loss. Exact ties retain the declared family/C order. This choice is made separately in every outer training partition.
5. Each calibrated inner model uses three further target-stratified calibration subfolds (`ensemble=False`). Thus inner validation cases were excluded from the base fitting and calibration. The chosen final outer model also calibrates using three cross-fitted scores from its own outer training partition. Calibration seeds are explicit in code.
6. Choose the threshold maximizing F1 on the chosen candidate's inner OOF probabilities, grid 0.05–0.95 inclusive in 0.01 increments. Ties favor the threshold nearest 0.5, then the higher threshold. The inner F1 is a training diagnostic; it is never presented as evaluation performance.
7. Score the complete model/calibration/threshold selection procedure on its outer validation partition. Pooled OOF classification metrics use the appropriate threshold for each record's excluding fold. AUC, Brier and log loss use the model probability, regardless of threshold. Report metrics at the conventional 0.5 threshold separately.

The main results evaluate this inner-selection procedure. They do not choose a winning family using outer scores and then claim that family's outer result as untouched evaluation. The four separately fitted family comparisons are exploratory development evidence. V2 was designed after viewing V1 development results, so all reported development metrics have experiment-selection uncertainty. The final holdout is reserved for a single frozen protocol evaluation.

This protocol follows the separation between probability estimation and classification threshold described in [scikit-learn's threshold documentation](https://scikit-learn.org/stable/modules/classification_threshold.html). Calibration needs predictions on examples excluded from base fitting, as described in [scikit-learn's calibration documentation](https://scikit-learn.org/stable/modules/calibration.html). A calibration step alone does not establish accurate probabilities for new patients. Brier combines reliability and discrimination, and the five reliability bins here have small sample counts.

## Primary development results

| Target | AUC | Accuracy | Precision | Recall | F1 | Brier | Thresholds across 5 outer folds |
|---|---:|---:|---:|---:|---:|---:|---|
| CAD | 0.926 | 0.868 | 0.881 | 0.942 | 0.911 | 0.096 | .46, .42, .34, .43, .49 |
| LAD | 0.814 | 0.731 | 0.718 | 0.887 | 0.794 | 0.174 | .39, .31, .39, .34, .31 |
| LCX | 0.701 | 0.591 | 0.478 | 0.815 | 0.602 | 0.211 | .28, .33, .31, .35, .30 |
| RCA | 0.722 | 0.612 | 0.483 | 0.809 | 0.605 | 0.202 | .30, .26, .23, .29, .31 |

LCX has 75 true positives, 17 false negatives, 82 false positives and 68 true negatives. RCA has 72 true positives, 17 false negatives, 77 false positives and 76 true negatives. Compared with V1 at its fixed 0.5 threshold, LCX/RCA recall increases from .228/.236 and F1 from .336/.356, but precision drops from .636/.724. This is a tradeoff, not evidence of improved disease discrimination or clinical effectiveness.

Conditional AUC intervals from 1,000 patient bootstrap resamples of fixed OOF predictions are CAD .889–.956, LAD .759–.864, LCX .632–.765 and RCA .653–.783. They exclude retraining, selection and protocol-development uncertainty. No external or prospective validation has been performed. The four independent target models do not impose a coherent joint CAD/vessel relationship.

## Integration contract

`results-v2/{models,cases,input_schema,benchmark}.json` use the V1 schema. Each portable model adds:

- `family`, `class_weight`, `calibration` and `inner_selection` diagnostics.
- `operating_threshold` and `threshold_selection` describing the inner F1 rule.
- `calibration.slope` and `offset` for the fitted mapping `sigmoid(slope * base_log_odds + offset)`.

For sigmoid models, the calibration slope is multiplied into every exported coefficient, and the offset is added to the intercept. This makes the existing standard-library `predict_json()` and its exact centered log-odds explanation work without a second estimator. The summed contributions explain the transformed model score. They are neither causal effects, independent feature effects nor percentage-point probability changes.

The predictor now returns `operating_threshold`, `predicted_label`, `model_family` and `calibration` for both selected example predictions and live edited inputs. V1 models default to threshold 0.5. Label reveal must compare `predicted_label`, not assume 0.5. Edited inputs have no corresponding observed edited-patient outcome.

The primary benchmark key is `targets[target].oof.selected`; `oof.logistic` is a compatibility alias for the same procedure. The conventional-threshold results are in `metrics_at_0_5`. The same eight V1 example records and selection policy are retained. All 968 portable OOF probabilities matched scikit-learn to a maximum absolute error of 3.33e-16, tolerance 1e-12.

## Frozen final-development fit API

After the final protocol has been recorded, root may run:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python fit_final_development.py
```

This creates `results-final-development/models.json`, four pipeline joblib files and `fit_diagnostics.json`. It fits exactly the V2 selection/calibration/threshold rule on all 242 development records and does not read or score holdout rows. It refuses to silently overwrite an existing final fit. These are the models for new-input inference and a separately implemented single final holdout evaluation. Development case examples must retain their excluding outer-fold models.

The reusable function is:

```python
from experiment_v2 import select_and_fit_development
fitted, spec, inner_diagnostics = select_and_fit_development(
    X_development, y_target, original_development_row_indices,
    model_id="LCX-final-development", seed_offset=0)
```

It accepts a dataframe in the exact schema order and original row identities. It rejects identities outside the frozen development split, and returns a sklearn estimator, portable spec and inner training diagnostics. `seed_offset=0` is the fixed final-development convention. Root owns the protocol-freeze and single final evaluation; this experiment does not unlock the holdout.

Dataset license/source: [UCI 411](https://archive.ics.uci.edu/dataset/411/extention+of+z+alizadeh+sani+dataset), CC BY 4.0. See the original download manifest and split SHA-256. Public educational research prototype only; F1 thresholds are not medical operating points.
