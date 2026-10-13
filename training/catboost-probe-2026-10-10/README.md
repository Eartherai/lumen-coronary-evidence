# CatBoost development probe, 10 October 2026

The bounded CatBoost probe gives no overall reason to replace Lumen’s frozen logistic procedure. LAD improves modestly in these development folds, CAD and RCA AUC/log loss worsen, and LCX is essentially unchanged. The app, final models, final evaluation, reports and videos were not modified.

These are descriptive exploratory development comparisons after earlier development experiments. They are not final-test scores, established superiority, clinical validation, or patient confidence. No second scoring of the opened final holdout was performed.

## Results

All rows below use the same 242 development identities and the same five outer folds. F1/precision/recall use each outer model’s independently learned inner-OOF threshold. Brier and log loss are better when smaller.

| Target | V2 AUC | CatBoost AUC | V2 F1 | CatBoost F1 | CatBoost precision | CatBoost recall | V2 Brier | CatBoost Brier | V2 log loss | CatBoost log loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CAD | 0.9260 | 0.9148 | 0.9106 | 0.9127 | 0.8901 | 0.9364 | 0.0963 | 0.0990 | 0.3068 | 0.3258 |
| LAD | 0.8138 | 0.8287 | 0.7937 | 0.8121 | 0.7707 | 0.8582 | 0.1744 | 0.1616 | 0.5174 | 0.4961 |
| LCX | 0.7011 | 0.6993 | 0.6024 | 0.6024 | 0.4777 | 0.8152 | 0.2106 | 0.2098 | 0.6086 | 0.6060 |
| RCA | 0.7218 | 0.6968 | 0.6050 | 0.6154 | 0.4810 | 0.8539 | 0.2023 | 0.2066 | 0.5871 | 0.5965 |

The run completed exactly **200 fits in 190.33 seconds wall time**, with 356.49 seconds user CPU and 4.86 seconds system CPU. Peak process RAM was 422.8 MB (including imported libraries), measured by `resource.getrusage` on macOS. Each fit used CPU and `thread_count=2`; no GPU was used. CatBoost 1.2.8 and all other packages came from the existing UV cache in an isolated environment, with no package download or global-environment modification.

CAD changed from 210 to 211 correct development decisions: 8 previously correct became wrong and 9 previously wrong became correct. LAD changed from 177 to 186 correct: 16 became wrong and 25 became correct. LCX had 143 correct with either procedure, but 17 decisions changed in each direction. RCA changed from 148 to 147 correct: 18 became wrong and 17 became correct. These paired counts caution against describing marginal aggregate changes as uniformly better predictions.

## Predeclared procedure

The declaration was saved before model execution in `protocol.json`, then bound with the exact script and invocation in `run-declaration.json`. Only three configurations were permitted:

| Configuration | Depth | Trees | Learning rate | L2 leaf regularization |
|---|---:|---:|---:|---:|
| 1 | 4 | 160 | .030 | 10 |
| 2 | 5 | 220 | .035 | 20 |
| 3 | 6 | 280 | .030 | 30 |

Fixed settings included Ordered boosting, CPU, two threads, one-dimensional categorical statistics (`max_ctr_complexity=1`), numeric `nan_mode=Min`, no posthoc calibration, no eval set, no early stopping, and a fixed seed of 2026 for every fit. The hard budget was 600 seconds. There was no result-dependent parameter or seed sweep. No model weights were exported.

Outer folds were five shared CAD-stratified folds, shuffled with seed 2026. Within each outer training fold, three target-stratified inner folds used `2026 + outer_fold_index`, exactly matching V2. Each configuration was fitted independently in every inner training partition. The lowest pooled inner-OOF log loss selected the configuration, with stable declaration order resolving exact ties. Its inner probabilities supplied the exact existing V2 threshold helper: maximize F1 over .05–.95 in .01 increments, choosing the threshold closest to .5 and then the higher value if still tied. The chosen model was refitted using only outer training rows and applied once to the outer validation rows.

All 55 predictors were retained and `Cath`, `LAD`, `LCX`, `RCA` were excluded from inputs. Numeric columns stayed numeric, with native missing-value handling. String categories were stripped row by row and missing/empty values mapped to a fixed `__MISSING__` string. This conversion has no fitted statistics. Numeric borders and native category statistics were learned within each CatBoost fit; validation rows were never supplied in an `eval_set`. There were 34 numeric and 21 categorical predictors.

The original workbook contains 303 records and must be read by the Excel parser; code immediately selects `.iloc[development_row_indices]`. No holdout records are retained or passed to fitting, prediction, selection or metrics. A Python audit hook also denies reads of evaluated final artifacts and records the actual project input paths. The hook did not report any blocked read attempt. It is an additional process guard, not a claim that the original workbook’s holdout bytes were absent from disk IO.

## Evidence and independent verification

- `protocol.json`: pre-execution settings, split identities, excluded targets, budget and primary-source links.
- `run-declaration.json`: exact script hash, declaration hash and invocation. Its `model_execution_started=false` value describes the timestamp of that declaration; completion is recorded separately in `benchmark.json` and `progress.json`.
- `benchmark.json`: complete metrics, paired V2 deltas, selected candidates and full native outer-model parameters, environment/CPU/RAM and actual read paths.
- `development-oof.csv`: all 242 rows, fold, truth, predicted probabilities, decisions and operating thresholds for all four targets.
- `inner-oof-predictions.json`: all 60 candidate vectors used for selection and thresholds.
- `fit-ledger.json`: all 200 fits with original row identities, validation identities and fit wall time.
- `fold-training-identities.json`: all outer/inner training and validation identities.
- `verify.py`: validates every fit’s identities, all 60 candidate selections and thresholds, the 20 outer partitions, and all four paired target metrics without fitting a model.
- `verification-receipt.json`: result and file hashes.

To verify the saved run without any new model fitting:

```sh
uv run --offline --python 3.12 --with pandas==3.0.6 --with openpyxl==3.1.5 --with scikit-learn==1.9.1 --with joblib==1.6.0 python training/catboost-probe-2026-10-10/verify.py
```

The original model invocation is preserved in `run-declaration.json` for reproducibility. Do not rerun `probe.py` in this dated directory because it writes the run artifacts there; preserve this completed run before a separately declared reproduction.

## Primary sources

Native named categorical features and parameters use the official [CatBoostClassifier API](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier). Numeric NaNs and the explicit categorical sentinel follow the [missing values documentation](https://catboost.ai/docs/en/concepts/algorithm-missing-values-processing). The choice of Ordered boosting for a small dataset and limited categorical-combination complexity reflects the [CPU speed/quality guidance](https://catboost.ai/docs/en/concepts/speed-up-training). The [CatBoost paper](https://arxiv.org/abs/1706.09516) explains ordered boosting and categorical processing; it does not establish accuracy on this dataset. The two-thread setting uses the [performance parameter](https://catboost.ai/docs/en/references/training-parameters/performance). Conservative depth/L2 values were our bounded experimental choices, not a claim that documentation recommends this exact grid.
