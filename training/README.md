# Track A CPU feasibility proof

This is a reproducible development benchmark and portable inference proof, not clinical validation. No GPU is used. The 61-row final holdout is frozen and has never been predicted or scored by this code.

Run from this directory:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python benchmark.py
```

Data: UCI 411, extension of Z-Alizadeh Sani, downloaded before this experiment. See `download.json`; `results/split.json` stores its SHA-256 and frozen row identities. The original dataset is CC BY 4.0: https://archive.ics.uci.edu/dataset/411/extention+of+z+alizadeh+sani+dataset

## Protocol

- 303 total records; seed 2026, CAD-stratified 20% holdout gives 242 development and 61 locked holdout rows. Row indices are zero-based Excel data rows, excluding the header.
- Four targets: Cath mapped to CAD, plus LAD, LCX and RCA. All four original target columns are excluded from the 55 inputs, for every model.
- Five shared outer development folds, stratified by CAD. Within each training partition, three target-stratified inner folds select hyperparameters by ROC-AUC. Numeric imputation/scaling and categorical imputation/one-hot encoding are refit inside each training fold.
- Compare a prior-only classifier, regularized logistic regression and a small histogram boosted tree. The explainable prototype is preselected as logistic; this is not a model-family selection followed by a claimed untouched evaluation.
- Logistic C grid: 0.01, 0.1, 1, 10. Tree: 100 rounds, seven leaves, minimum 15 samples per leaf, learning rate 0.05/0.1, L2 penalty 1/10. Classification threshold fixed at 0.5, not optimized on validation labels.
- Pooled out-of-fold metrics and outer-fold metrics are both saved. A prior can have pooled AUC below 0.5 because its prevalence differs across training folds; each fold's constant-prior AUC is 0.5.
- AUC intervals bootstrap patients from fixed OOF predictions, 1,000 draws. They omit retraining/model-selection uncertainty. No external validation, no prospective validation and no calibration correction were performed.

## Initial results

The benchmark ran in 14.4 seconds on the available CPU. Logistic results:

| Target | ROC-AUC | Conditional 95% interval | Accuracy | Precision | Recall | F1 | Brier |
|---|---:|---|---:|---:|---:|---:|---:|
| CAD | 0.928 | 0.892–0.957 | 0.880 | 0.896 | 0.942 | 0.918 | 0.097 |
| LAD | 0.822 | 0.768–0.871 | 0.744 | 0.737 | 0.872 | 0.799 | 0.182 |
| LCX | 0.712 | 0.642–0.775 | 0.657 | 0.636 | 0.228 | 0.336 | 0.210 |
| RCA | 0.732 | 0.663–0.793 | 0.686 | 0.724 | 0.236 | 0.356 | 0.203 |

Tree AUCs: CAD 0.867, LAD 0.788, LCX 0.676, RCA 0.670. These results justify an interactive research proof, not a claim that all vessel predictions are accurate: LCX and RCA miss many positive cases at the fixed threshold.

Development audit found no duplicate input rows or missing cells and one CAD-versus-any-vessel label disagreement. Original labels were preserved. Correlated clinical inputs complicate attribution, and independent vessel probabilities need not obey a coherent joint CAD probability model.

## Frontend/backend contract

`results/cases.json` contains eight real development cases, each with raw `inputs`, hidden `truth`, shared outer `fold`, and `predictions` keyed by CAD/LAD/LCX/RCA. Case selection covers different recorded label patterns using seed 2026; it does not select favorable predictions. Some cases are model failures.

`results/models.json` contains `models[model_id]`. For a selected case/target, find the ID in `case['predictions'][target]['model_id']`. Each model exports its numeric imputer/scaler/coefficients, categorical encoder/imputer/coefficients, training indices, intercept and training reference means. This model excluded the selected case in both preprocessing and fitting.

The standard-library module `predict.py` exposes:

```python
result = predict_json(models['models'][model_id], case['inputs'])
```

It never reads target labels. Complete raw features are required; nulls use the model's training-fold imputer. Unknown categories use the fitted encoder's all-zero behavior and are returned in `unknown_categories`; the UI should flag these and constrain choices to the dataset schema. Nonfinite numeric inputs, extra fields, omitted fields and target fields are rejected.

Results include `probability`, `log_odds`, `baseline_log_odds`, `baseline_probability`, sorted `contributions`, `model_id`, and diagnostics. Each contribution includes `feature`, `value`, and `log_odds_contribution`. Numeric contribution is coefficient × (standardized value − training mean standardized value). Categorical contributions sum across that raw feature's encoded columns. Baseline plus all contributions exactly reconstructs log-odds, and applying sigmoid reconstructs probability. These are exact centered linear-model contributions, not conditional SHAP estimates, percentage-point contributions, calibrated uncertainty or causal effects. The baseline probability is sigmoid(mean training log-odds), not mean training probability.

`results/input_schema.json` includes raw feature order, numeric development min/max/median and observed integer flags, plus development categorical choices. These are observed data ranges, not medically accepted ranges. Units and meanings need clinical/source verification before product labels are finalized. Preserve the source categorical spelling `Fmale` in encoded inputs even if the display label is corrected.

`results/development_oof.csv` stores predictions and truth for all 242 development records. `results/benchmark.json` stores complete metrics, reliability bins, per-fold parameters and methodology. Twenty `*-outer-*.joblib` files preserve fold pipelines. `results/progress.json` reports completion.

The benchmark verifies exported JSON inference against scikit-learn on all 968 OOF predictions to absolute tolerance 1e-12, and verifies explanation sums. The standalone standard-library predictor was additionally checked against the exported predictions on all 32 selected case/target pairs. Edited case inputs are exploratory model sensitivity; their predictions have no observed edited-patient outcome and must not retain an implied ground-truth comparison.
