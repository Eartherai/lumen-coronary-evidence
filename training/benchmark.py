"""CPU feasibility benchmark. The frozen holdout is never predicted or scored.

Run: uv run --offline --with pandas --with openpyxl --with scikit-learn --with joblib python benchmark.py
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, f1_score, log_loss, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "extention of Z-Alizadeh sani dataset.xlsx"
OUT = ROOT / "results"
SEED = 2026
TARGETS = {"CAD": "Cath", "LAD": "LAD", "LCX": "LCX", "RCA": "RCA"}
EXCLUDE = list(TARGETS.values())


def primitive(value):
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def save(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, default=primitive, allow_nan=False))
    tmp.replace(path)


def make_preprocessor(numeric, categorical):
    return ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scaler", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                  ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
    ], sparse_threshold=0)


def metric_set(y, p):
    pred = p >= 0.5
    return {"roc_auc": float(roc_auc_score(y, p)), "average_precision": float(average_precision_score(y, p)),
            "accuracy": float(accuracy_score(y, pred)), "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)), "f1": float(f1_score(y, pred, zero_division=0)),
            "brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, p)),
            "confusion_matrix_tn_fp_fn_tp": confusion_matrix(y, pred, labels=[0, 1]).ravel().tolist()}


def ci(y, p):
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(1000):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            vals.append(roc_auc_score(y[idx], p[idx]))
    return np.percentile(vals, [2.5, 97.5]).tolist()


def calibration_bins(y, p):
    edges = np.linspace(0, 1, 6)
    output = []
    for k in range(5):
        keep = (p >= edges[k]) & (p < edges[k + 1] if k < 4 else p <= edges[k + 1])
        output.append({"lo": float(edges[k]), "hi": float(edges[k + 1]), "n": int(keep.sum()),
                       "mean_probability": float(p[keep].mean()) if keep.any() else None,
                       "observed_fraction": float(y[keep].mean()) if keep.any() else None})
    return output


def export_logistic(model, train, numeric, categorical, model_id, train_indices):
    pre, estimator = model.named_steps["preprocess"], model.named_steps["model"]
    transformed = pre.transform(train)
    reference = transformed.mean(axis=0)
    coeff = estimator.coef_[0]
    intercept = float(estimator.intercept_[0])
    num = pre.named_transformers_["numeric"]
    cat = pre.named_transformers_["categorical"]
    offset = 0
    spec = {"model_id": model_id, "target": model_id.split("-")[0], "model_type": "logistic_regression",
            "positive_class": 1, "intercept": intercept, "C": float(estimator.C),
            "baseline_log_odds": float(intercept + reference @ coeff),
            "explanation": "Exact additive log-odds contributions centered on this training fold's mean encoded inputs; associations, not causal effects or calibrated confidence.",
            "training_row_indices": [int(x) for x in train_indices], "numeric": [], "categorical": []}
    for i, feature in enumerate(numeric):
        spec["numeric"].append({"feature": feature, "impute": float(num.named_steps["imputer"].statistics_[i]),
                                "mean": float(num.named_steps["scaler"].mean_[i]),
                                "scale": float(num.named_steps["scaler"].scale_[i]),
                                "coefficient": float(coeff[offset]), "reference_encoded_mean": float(reference[offset])})
        offset += 1
    for i, feature in enumerate(categorical):
        cats = [str(x) for x in cat.named_steps["encoder"].categories_[i]]
        width = len(cats)
        spec["categorical"].append({"feature": feature, "impute": str(cat.named_steps["imputer"].statistics_[i]),
                                    "categories": cats, "coefficients": coeff[offset:offset + width].tolist(),
                                    "reference_encoded_means": reference[offset:offset + width].tolist(),
                                    "unknown_category": "all-zero encoding; UI should flag unknown category"})
        offset += width
    assert offset == len(coeff)
    return spec


def infer_spec(spec, inputs):
    contributions = []
    raw_log_odds = spec["intercept"]
    for f in spec["numeric"]:
        raw = inputs.get(f["feature"])
        value = f["impute"] if raw is None else float(raw)
        encoded = (value - f["mean"]) / f["scale"]
        raw_log_odds += encoded * f["coefficient"]
        contributions.append({"feature": f["feature"], "value": raw,
                              "log_odds_contribution": (encoded - f["reference_encoded_mean"]) * f["coefficient"]})
    for f in spec["categorical"]:
        raw = inputs.get(f["feature"])
        value = f["impute"] if raw is None else str(raw)
        encoded = np.asarray([float(value == c) for c in f["categories"]])
        coeff = np.asarray(f["coefficients"])
        raw_log_odds += float(encoded @ coeff)
        contributions.append({"feature": f["feature"], "value": raw,
                              "log_odds_contribution": float((encoded - np.asarray(f["reference_encoded_means"])) @ coeff)})
    reconstructed = spec["baseline_log_odds"] + sum(f["log_odds_contribution"] for f in contributions)
    assert abs(raw_log_odds - reconstructed) < 1e-10
    return {"probability": float(1 / (1 + np.exp(-raw_log_odds))), "log_odds": raw_log_odds,
            "baseline_log_odds": spec["baseline_log_odds"], "baseline_probability": float(1 / (1 + np.exp(-spec["baseline_log_odds"]))),
            "contributions": sorted(contributions, key=lambda f: abs(f["log_odds_contribution"]), reverse=True),
            "model_id": spec["model_id"]}


def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    data = pd.read_excel(SOURCE, sheet_name=0)
    data.columns = data.columns.str.strip()
    X = data.drop(columns=EXCLUDE)
    for col in X.select_dtypes(include=["object", "str"]).columns:
        X[col] = X[col].str.strip().astype(object)
    y = pd.DataFrame({name: (data[col].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int)
                      for name, col in TARGETS.items()})
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    assert len(X.columns) == 55 and not set(EXCLUDE) & set(X.columns)
    dev_ids, holdout_ids = train_test_split(np.arange(len(data)), test_size=0.2, random_state=SEED, stratify=y.CAD)
    dev_ids, holdout_ids = np.sort(dev_ids), np.sort(holdout_ids)
    frozen = {"dataset_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "seed": SEED,
              "stratification": "CAD", "test_size": 0.2, "development_row_indices": dev_ids.tolist(),
              "holdout_row_indices": holdout_ids.tolist(), "holdout_policy": "Never predicted or scored by this script; keep locked until final protocol freeze.",
              "row_indexing": "zero-based data row, excluding Excel header"}
    split_path = OUT / "split.json"
    if split_path.exists():
        assert json.loads(split_path.read_text()) == frozen, "Refusing to alter frozen split"
    else:
        save("split.json", frozen)
    # Only development inputs and labels are used below this boundary.
    Xdev, ydev = X.iloc[dev_ids].reset_index(drop=True), y.iloc[dev_ids].reset_index(drop=True)
    del X, y, data, holdout_ids
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(Xdev, ydev.CAD))
    fold_assignment = np.zeros(len(Xdev), int)
    oof = {target: {name: np.full(len(Xdev), np.nan) for name in ["prior", "logistic", "small_tree"]} for target in TARGETS}
    models = {}
    results = {"protocol": {"dataset": "UCI 411 extension of Z-Alizadeh Sani", "seed": SEED,
                "n_total": len(dev_ids) + len(frozen["holdout_row_indices"]), "n_development": len(dev_ids),
                "n_locked_holdout": len(frozen["holdout_row_indices"]), "excluded_features": EXCLUDE,
                "n_input_features": len(Xdev.columns), "numeric_features": numeric, "categorical_features": categorical,
                "outer_cv": "5 shared CAD-stratified folds", "inner_cv": "3 target-stratified folds within each outer training partition",
                "selection_metric": "ROC-AUC", "classification_threshold": 0.5,
                "holdout_scored": False, "sklearn_version": sklearn.__version__,
                "calibration": "No posthoc calibration fit; report Brier and five equal-width reliability bins",
                "auc_ci": "1000 patient bootstrap resamples of fixed development OOF predictions; conditional, excludes retraining uncertainty",
                "comparison": "Logistic remains the explainable prototype irrespective of score; small tree is a benchmark, no winner selection on OOF",
                "limitations": ["Small single-dataset feasibility study; no external or prospective validation.", "No clinical diagnosis or treatment recommendation.", "Displayed local contributions are exact linear-model decomposition, not causal effects."]},
               "development_audit": {"positive_counts": ydev.sum().to_dict(), "missing_cells": int(Xdev.isna().sum().sum()),
                                     "duplicate_input_rows": int(Xdev.duplicated().sum()),
                                     "cad_vs_any_vessel_label_disagreements": int((ydev.CAD != ydev[["LAD", "LCX", "RCA"]].max(axis=1)).sum())},
               "targets": {}}
    save("progress.json", {"stage": "split_frozen", "holdout_scored": False})
    for target in TARGETS:
        yt = ydev[target].to_numpy()
        records = []
        for fold, (tr, te) in enumerate(folds):
            fold_assignment[te] = fold
            inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + fold)
            row = {"fold": fold, "train_n": len(tr), "validation_n": len(te), "train_positive": int(yt[tr].sum()), "validation_positive": int(yt[te].sum())}
            for kind in ["prior", "logistic", "small_tree"]:
                if kind == "prior":
                    fitted = DummyClassifier(strategy="prior").fit(np.zeros((len(tr), 1)), yt[tr])
                    p = fitted.predict_proba(np.zeros((len(te), 1)))[:, 1]
                    row[kind] = {"parameters": {}, "metrics": metric_set(yt[te], p)}
                else:
                    estimator = (LogisticRegression(max_iter=2000, solver="lbfgs", random_state=SEED)
                                 if kind == "logistic" else HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=7,
                                    min_samples_leaf=15, early_stopping=False, random_state=SEED))
                    grid = {"model__C": [0.01, 0.1, 1.0, 10.0]} if kind == "logistic" else {"model__learning_rate": [0.05, 0.1], "model__l2_regularization": [1.0, 10.0]}
                    pipe = Pipeline([("preprocess", make_preprocessor(numeric, categorical)), ("model", estimator)])
                    search = GridSearchCV(pipe, grid, scoring="roc_auc", cv=inner, n_jobs=1, refit=True, error_score="raise")
                    search.fit(Xdev.iloc[tr], yt[tr])
                    fitted = search.best_estimator_
                    p = fitted.predict_proba(Xdev.iloc[te])[:, 1]
                    row[kind] = {"parameters": search.best_params_, "inner_best_auc": float(search.best_score_), "metrics": metric_set(yt[te], p)}
                    if kind == "logistic":
                        model_id = f"{target}-outer-{fold}"
                        spec = export_logistic(fitted, Xdev.iloc[tr], numeric, categorical, model_id, dev_ids[tr])
                        models[model_id] = spec
                        # Validate portable JSON inference and all contribution sums on the whole unseen fold.
                        json_p = np.asarray([infer_spec(spec, Xdev.iloc[i].to_dict())["probability"] for i in te])
                        row["json_inference_max_abs_error"] = float(np.max(np.abs(json_p - p)))
                        assert np.allclose(json_p, p, atol=1e-12, rtol=0)
                        joblib.dump(fitted, OUT / f"{model_id}.joblib")
                oof[target][kind][te] = p
            records.append(row)
            print(f"{target} fold {fold + 1}/5 complete", flush=True)
            save("progress.json", {"stage": "nested_cv", "target": target, "fold_completed": fold + 1, "holdout_scored": False})
        summary = {}
        for kind, pred in oof[target].items():
            assert np.isfinite(pred).all()
            summary[kind] = {**metric_set(yt, pred), "roc_auc_95_ci_conditional": ci(yt, pred),
                             "calibration_bins": calibration_bins(yt, pred),
                             "outer_fold_auc_mean": float(np.mean([r[kind]["metrics"]["roc_auc"] for r in records])),
                             "outer_fold_auc_std": float(np.std([r[kind]["metrics"]["roc_auc"] for r in records], ddof=1))}
        results["targets"][target] = {"positive_n": int(yt.sum()), "negative_n": int(len(yt) - yt.sum()), "oof": summary, "outer_folds": records}
        save("benchmark.json", results)
        save("models.json", {"schema_version": 1, "models": models, "feature_order": Xdev.columns.tolist(), "targets": list(TARGETS)})
    # Coverage-based case selection: first shuffled member of each available true-label pattern,
    # then fill to eight. No selection on prediction success or explanation magnitude.
    rng = np.random.default_rng(SEED)
    selected, patterns = [], set()
    for idx in rng.permutation(len(Xdev)):
        pattern = tuple(ydev.iloc[idx][list(TARGETS)])
        if pattern not in patterns:
            selected.append(int(idx)); patterns.add(pattern)
        if len(selected) == 8:
            break
    if len(selected) < 8:
        for idx in rng.permutation(len(Xdev)):
            if int(idx) not in selected:
                selected.append(int(idx))
            if len(selected) == 8:
                break
    cases = []
    for idx in selected:
        case = {"case_id": f"UCI411-{int(dev_ids[idx]):03d}", "row_index": int(dev_ids[idx]),
                "fold": int(fold_assignment[idx]), "inputs": Xdev.iloc[idx].to_dict(),
                "truth": ydev.iloc[idx].to_dict(), "predictions": {}}
        for target in TARGETS:
            spec = models[f"{target}-outer-{fold_assignment[idx]}"]
            case["predictions"][target] = infer_spec(spec, case["inputs"])
            assert case["row_index"] not in spec["training_row_indices"]
            assert abs(case["predictions"][target]["probability"] - oof[target]["logistic"][idx]) < 1e-12
        cases.append(case)
    save("cases.json", {"schema_version": 1, "selection": "Seed2026 shuffled development rows; distinct recorded four-target patterns first, fill to 8; not selected for model success. Truth must remain hidden until reveal.",
                       "holdout_included": False, "prediction_type": "Outer-fold out-of-fold logistic", "cases": cases})
    oof_table = pd.DataFrame({"row_index": dev_ids, "fold": fold_assignment})
    for target in TARGETS:
        oof_table[target + "_truth"] = ydev[target]
        for kind, p in oof[target].items():
            oof_table[target + "_" + kind] = p
    oof_table.to_csv(OUT / "development_oof.csv", index=False)
    schema = {"schema_version": 1, "feature_order": Xdev.columns.tolist(), "excluded_features": EXCLUDE,
              "numeric": [{"feature": c, "min_development": float(Xdev[c].min()), "max_development": float(Xdev[c].max()), "median_development": float(Xdev[c].median()),
                           "integer_observed": bool(np.all(Xdev[c] == np.floor(Xdev[c])))} for c in numeric],
              "categorical": [{"feature": c, "categories_development": sorted(Xdev[c].astype(str).unique().tolist())} for c in categorical],
              "units": "Dataset column names retained; clinical unit labels have not been independently verified."}
    save("input_schema.json", schema)
    results["runtime_seconds"] = round(time.perf_counter() - started, 3)
    results["portable_model_validation"] = {"n_oof_predictions_checked": len(dev_ids) * len(TARGETS), "atol": 1e-12, "all_passed": True}
    save("benchmark.json", results)
    save("progress.json", {"stage": "complete", "runtime_seconds": results["runtime_seconds"], "holdout_scored": False})
    print(json.dumps({t: {k: round(v["roc_auc"], 3) for k, v in results["targets"][t]["oof"].items()} for t in TARGETS}, indent=2))
    print(f"Finished in {results['runtime_seconds']}s. Holdout untouched.", flush=True)


if __name__ == "__main__":
    main()
