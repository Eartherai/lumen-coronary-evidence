"""Bounded exploratory CPU probe of ExtraTrees and regularized boosting.

Same frozen development split and outer folds; no final holdout scores. Family
comparisons remain exploratory. Each candidate's operating threshold is learned
solely from inner OOF predictions. No choice is made using outer results.
"""
import hashlib
import json
import time

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from benchmark import EXCLUDE, ROOT, SEED, SOURCE, TARGETS, calibration_bins, ci, make_preprocessor, primitive
from experiment_v2 import metrics, threshold_from_inner

OUT = ROOT / "results-v3"
GRIDS = {
    "extra_trees": [
        {"n_estimators": 192, "max_depth": 5, "min_samples_leaf": 5, "max_features": 0.8},
        {"n_estimators": 192, "max_depth": None, "min_samples_leaf": 8, "max_features": 0.8},
    ],
    "regularized_boosting": [
        {"max_iter": 120, "max_leaf_nodes": 7, "min_samples_leaf": 20,
         "learning_rate": 0.04, "l2_regularization": 5.0},
        {"max_iter": 120, "max_leaf_nodes": 15, "min_samples_leaf": 20,
         "learning_rate": 0.04, "l2_regularization": 10.0},
    ],
}


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, default=primitive, allow_nan=False))


def estimator(family, parameters, numeric, categorical):
    model = (ExtraTreesClassifier(**parameters, n_jobs=1, random_state=SEED)
             if family == "extra_trees" else
             HistGradientBoostingClassifier(**parameters, early_stopping=False, random_state=SEED))
    return Pipeline([("preprocess", make_preprocessor(numeric, categorical)), ("model", model)])


def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == frozen["dataset_sha256"]
    data = pd.read_excel(SOURCE).iloc[frozen["development_row_indices"]].copy()
    data.columns = data.columns.str.strip()
    X = data.drop(columns=EXCLUDE).reset_index(drop=True)
    for feature in X.select_dtypes(include=["object", "str"]).columns:
        X[feature] = X[feature].str.strip().astype(object)
    y = pd.DataFrame({name: (data[col].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int).to_numpy()
                      for name, col in TARGETS.items()})
    del data
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = [feature for feature in X if feature not in numeric]
    assert not set(EXCLUDE) & set(X) and len(X.columns) == 55
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y.CAD))
    fold_assignment = np.zeros(len(X), int)
    table = pd.DataFrame({"row_index": frozen["development_row_indices"]})
    result = {"protocol": {"seed": SEED, "sklearn_version": sklearn.__version__,
                "n_development": len(X), "n_locked_holdout": len(frozen["holdout_row_indices"]), "holdout_scored": False,
                "dataset_sha256": frozen["dataset_sha256"],
                "excluded_features": EXCLUDE, "n_input_features": len(X.columns),
                "outer_cv": "Same five shared CAD-stratified folds as v1/v2",
                "inner_cv": "Three target-stratified folds, same seeds as v2; all preprocessing fit in training partitions",
                "grids": GRIDS, "selection_metric": "Pooled inner OOF log loss, within each family",
                "classification_threshold": "Each fitted outer model uses an inner-OOF F1-selected threshold on 0.05..0.95 grid, same deterministic tie break as v2",
                "calibration": "No posthoc calibration fit in this bounded exploratory probe",
                "selection_warning": "These separate family development results cannot be selected by outer score and claimed as untouched final evaluation",
                "portable_export": "No tree JSON runtime exported; pipelines saved for reproducibility only",
                "auc_ci": "1000 patient resamples of fixed OOF scores, conditional and excludes retraining/protocol selection"}, "targets": {}}
    for target in TARGETS:
        yt = y[target].to_numpy()
        p_all = {family: np.full(len(X), np.nan) for family in GRIDS}
        pred_all = {family: np.zeros(len(X), bool) for family in GRIDS}
        thresholds = {family: np.full(len(X), np.nan) for family in GRIDS}
        records = []
        for fold, (tr, te) in enumerate(folds):
            fold_assignment[te] = fold
            Xtrain, ytrain = X.iloc[tr], yt[tr]
            inner = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + fold).split(Xtrain, ytrain))
            record = {"fold": fold, "train_n": len(tr), "validation_n": len(te), "families": {}}
            for family, grid in GRIDS.items():
                candidates = []
                for parameters in grid:
                    inner_p = np.full(len(tr), np.nan)
                    for fit_idx, val_idx in inner:
                        fitted = estimator(family, parameters, numeric, categorical)
                        fitted.fit(Xtrain.iloc[fit_idx], ytrain[fit_idx])
                        inner_p[val_idx] = fitted.predict_proba(Xtrain.iloc[val_idx])[:, 1]
                    threshold, inner_f1 = threshold_from_inner(ytrain, inner_p)
                    candidates.append({"parameters": parameters, "inner_log_loss": metrics(ytrain, inner_p)["log_loss"],
                                       "operating_threshold": threshold,
                                       "inner_f1_training_diagnostic": inner_f1})
                selected = min(candidates, key=lambda item: item["inner_log_loss"])
                fitted = estimator(family, selected["parameters"], numeric, categorical)
                fitted.fit(Xtrain, ytrain)
                p = fitted.predict_proba(X.iloc[te])[:, 1]
                pred = p >= selected["operating_threshold"]
                p_all[family][te], pred_all[family][te], thresholds[family][te] = p, pred, selected["operating_threshold"]
                joblib.dump(fitted, OUT / f"{target}-{family}-outer-{fold}.joblib")
                record["families"][family] = {"selection": selected, "inner_candidates": candidates,
                                               "metrics": metrics(yt[te], p, pred), "metrics_at_0_5": metrics(yt[te], p),
                                               "training_row_indices": np.asarray(frozen["development_row_indices"])[tr].tolist()}
            records.append(record)
            print(f"{target} outer {fold + 1}/5 complete", flush=True)
            save("progress.json", {"stage": "running", "target": target, "fold": fold, "holdout_scored": False})
        summary = {}
        for family in GRIDS:
            assert np.isfinite(p_all[family]).all()
            summary[family] = {**metrics(yt, p_all[family], pred_all[family]),
                               "metrics_at_0_5": metrics(yt, p_all[family]),
                               "roc_auc_95_ci_conditional": ci(yt, p_all[family]),
                               "calibration_bins": calibration_bins(yt, p_all[family]),
                               "outer_thresholds": [float(thresholds[family][te[0]]) for _, te in folds]}
            table[f"{target}_{family}"] = p_all[family]
            table[f"{target}_{family}_decision"] = pred_all[family].astype(int)
            table[f"{target}_{family}_threshold"] = thresholds[family]
        table[f"{target}_truth"] = yt
        result["targets"][target] = {"positive_n": int(yt.sum()), "negative_n": int(len(yt) - yt.sum()),
                                     "oof": summary, "outer_folds": records}
        save("benchmark.json", result)
    table["fold"] = fold_assignment
    table.to_csv(OUT / "development_oof.csv", index=False)
    result["runtime_seconds"] = round(time.perf_counter() - started, 3)
    save("benchmark.json", result)
    save("progress.json", {"stage": "complete", "runtime_seconds": result["runtime_seconds"], "holdout_scored": False})
    print(json.dumps({target: {family: {key: round(value, 3) for key, value in row.items()
                                      if key in ["roc_auc", "f1", "precision", "recall", "brier", "log_loss"]}
                              for family, row in result["targets"][target]["oof"].items()}
                      for target in TARGETS}, indent=2))
    print(f"Finished in {result['runtime_seconds']}s. Frozen holdout untouched.", flush=True)


if __name__ == "__main__":
    main()
