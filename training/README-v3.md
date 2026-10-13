# Bounded exploratory tree comparison

`experiment_v3.py` compares two predeclared ExtraTrees configurations and two strongly regularized histogram-boosting configurations. It reuses the frozen 242 development records, five CAD-stratified outer folds, seed 2026, three target-stratified inner folds and excluded target columns from V2. Numeric/categorical preprocessing is fitted inside each training partition. Each family chooses its parameters by inner OOF log loss and its classification threshold by inner OOF F1. All 61 final holdout records remain unscored.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python experiment_v3.py
```

The run completed in 20.0 CPU seconds with scikit-learn 1.9.1. Artifacts are separate in `results-v3`: full benchmark and inner choices, development OOF CSV, and reproducible fold joblib pipelines. No new tree runtime has been connected to the demo. Parameter grids and methodology are recorded in the benchmark/code.

| Target | V2 nested logistic AUC / F1 / Brier | ExtraTrees AUC / F1 / Brier | Regularized boosting AUC / F1 / Brier |
|---|---|---|---|
| CAD | .926 / .911 / .096 | .896 / .897 / .105 | .890 / .888 / .111 |
| LAD | .814 / .794 / .174 | .804 / .799 / .173 | .826 / .809 / .165 |
| LCX | .701 / .602 / .211 | .679 / .626 / .215 | .685 / .587 / .216 |
| RCA | .722 / .605 / .202 | .667 / .598 / .216 | .670 / .540 / .217 |

The bounded probe does not provide an overall reason to replace the exact explainable logistic procedure. Boosting modestly improves LAD on these development folds but weakens the other targets. ExtraTrees increases LCX F1 by predicting positives more frequently (recall .946, precision .468), while worsening AUC and Brier. These are exploratory comparisons on a small dataset, not statistically established superiority or final test results. No additional family/seed sweep was run after seeing them.

The final holdout can only evaluate a single procedure selected and recorded before scoring. Selecting whichever family happens to have the largest outer score per target, and then presenting those outer scores as untouched validation, would overstate the evidence.
