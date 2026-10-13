"""Nested CPU experiment: probability selection, sigmoid calibration, F1 threshold.

The frozen final holdout is never predicted or scored. Output is separate from v1.
Every exported example is predicted by a model whose fitting, preprocessing,
calibration and threshold selection excluded that example's entire outer fold.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, f1_score, log_loss, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from benchmark import (EXCLUDE, ROOT, SEED, SOURCE, TARGETS, calibration_bins, ci,
                       export_logistic, make_preprocessor, primitive)
from predict import predict_json

OUT = ROOT / "results-v2"
C_GRID = [0.01, 0.1, 1.0, 10.0]
FAMILIES = ["unweighted", "balanced", "unweighted_sigmoid", "balanced_sigmoid"]
THRESHOLDS = np.arange(0.05, 0.951, 0.01)


def save(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, default=primitive, allow_nan=False))
    tmp.replace(path)


def metrics(y, p, pred=None):
    pred = p >= 0.5 if pred is None else pred
    return {"roc_auc": float(roc_auc_score(y, p)),
            "average_precision": float(average_precision_score(y, p)),
            "accuracy": float(accuracy_score(y, pred)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, p)),
            "confusion_matrix_tn_fp_fn_tp": confusion_matrix(y, pred, labels=[0, 1]).ravel().tolist()}


def threshold_from_inner(y, p):
    scores = np.asarray([f1_score(y, p >= threshold, zero_division=0)
                         for threshold in THRESHOLDS])
    ties = np.flatnonzero(np.isclose(scores, scores.max(), atol=1e-12, rtol=0))
    # A deterministic tie-break, predeclared before observing outer predictions.
    best = sorted(ties, key=lambda i: (abs(float(THRESHOLDS[i]) - 0.5), -float(THRESHOLDS[i])))[0]
    return float(np.round(THRESHOLDS[best], 2)), float(scores[best])


def make_estimator(family, C, numeric, categorical, calibration_seed):
    pipe = Pipeline([
        ("preprocess", make_preprocessor(numeric, categorical)),
        ("model", LogisticRegression(C=C, class_weight="balanced" if family.startswith("balanced") else None,
                                     max_iter=2000, solver="lbfgs", random_state=SEED)),
    ])
    if family.endswith("sigmoid"):
        return CalibratedClassifierCV(estimator=pipe, method="sigmoid", ensemble=False,
                                      cv=StratifiedKFold(n_splits=3, shuffle=True,
                                                        random_state=calibration_seed), n_jobs=1)
    return pipe


def export_estimator(fitted, family, Xtrain, numeric, categorical, model_id, train_ids,
                     threshold, inner_selection):
    if family.endswith("sigmoid"):
        calibrated = fitted.calibrated_classifiers_[0]
        pipe = calibrated.estimator
        calibrator = calibrated.calibrators[0]
        slope, offset = -float(calibrator.a_), -float(calibrator.b_)
        calibration = {"method": "sigmoid", "ensemble": False, "slope": slope, "offset": offset,
                       "mapping": "sigmoid(slope * base_log_odds + offset)",
                       "source": "Three target-stratified cross-fitted training-fold decision scores; no outer validation labels",
                       "base_coefficients_composed": True,
                       "training_row_indices": [int(i) for i in train_ids]}
    else:
        pipe, slope, offset = fitted, 1.0, 0.0
        calibration = {"method": "none", "slope": 1.0, "offset": 0.0}
    spec = export_logistic(pipe, Xtrain, numeric, categorical, model_id, train_ids)
    spec["base_intercept"] = spec["intercept"]
    spec["intercept"] = slope * spec["intercept"] + offset
    spec["baseline_log_odds"] = slope * spec["baseline_log_odds"] + offset
    for field in spec["numeric"]:
        field["coefficient"] *= slope
    for field in spec["categorical"]:
        field["coefficients"] = [slope * value for value in field["coefficients"]]
    spec["model_type"] = "sigmoid_calibrated_logistic" if family.endswith("sigmoid") else "logistic_regression"
    spec["family"] = family
    spec["class_weight"] = "balanced" if family.startswith("balanced") else None
    spec["calibration"] = calibration
    spec["operating_threshold"] = threshold
    spec["threshold_selection"] = {"metric": "F1", "candidate_range": [0.05, 0.95], "step": 0.01,
                                    "source": "Three inner validation folds pooled within this outer training partition",
                                    "ties": "Closest to 0.5; higher threshold if still tied",
                                    "clinical_operating_point": False}
    spec["inner_selection"] = inner_selection
    spec["explanation"] = ("Exact additive log-odds contributions centered on the outer training fold's encoded input means; "
                           "sigmoid calibration slope is composed into all coefficients and offset into the intercept where present. "
                           "Associations, not causal effects or patient uncertainty.")
    return spec


def select_and_fit_development(Xtrain, ytrain, training_row_indices, model_id, seed_offset=0):
    """Fit the v2 procedure to authorized development rows and export one model.

    Returns ``(fitted_sklearn_estimator, portable_spec, inner_diagnostics)``.
    Inputs must have exactly the development feature schema, and original row
    identities must be a subset of the locked split's development identities.
    The function never reads, predicts or scores holdout records. Use once on
    all 242 development rows per target after the final protocol is frozen.
    ``seed_offset=0`` is the fixed full-development training seed convention.
    """
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    row_ids = [int(i) for i in training_row_indices]
    assert len(row_ids) == len(Xtrain) == len(ytrain)
    assert len(set(row_ids)) == len(row_ids)
    assert set(row_ids) <= set(frozen["development_row_indices"]), "Only frozen development rows may be fitted"
    assert not set(row_ids) & set(frozen["holdout_row_indices"])
    schema = json.loads((ROOT / "results" / "input_schema.json").read_text())
    assert list(Xtrain.columns) == schema["feature_order"]
    assert not set(EXCLUDE) & set(Xtrain.columns)
    numeric = [field["feature"] for field in schema["numeric"]]
    categorical = [field["feature"] for field in schema["categorical"]]
    Xtrain, ytrain = Xtrain.reset_index(drop=True), np.asarray(ytrain)
    assert set(np.unique(ytrain)) == {0, 1}
    inner_splits = list(StratifiedKFold(n_splits=3, shuffle=True,
                                      random_state=SEED + seed_offset).split(Xtrain, ytrain))
    candidates = []
    for family in FAMILIES:
        for C in C_GRID:
            inner_p = np.full(len(Xtrain), np.nan)
            for k, (fit_idx, val_idx) in enumerate(inner_splits):
                estimator = make_estimator(family, C, numeric, categorical,
                                           SEED + 100 + 10 * seed_offset + k)
                estimator.fit(Xtrain.iloc[fit_idx], ytrain[fit_idx])
                inner_p[val_idx] = estimator.predict_proba(Xtrain.iloc[val_idx])[:, 1]
            threshold, training_f1 = threshold_from_inner(ytrain, inner_p)
            candidates.append({"family": family, "C": C, "inner_log_loss": float(log_loss(ytrain, inner_p)),
                               "inner_roc_auc": float(roc_auc_score(ytrain, inner_p)),
                               "operating_threshold": threshold,
                               "inner_threshold_f1_training_diagnostic": training_f1})
    selected = min(candidates, key=lambda candidate: candidate["inner_log_loss"])
    fitted = make_estimator(selected["family"], selected["C"], numeric, categorical,
                            SEED + 1000 + seed_offset)
    fitted.fit(Xtrain, ytrain)
    spec = export_estimator(fitted, selected["family"], Xtrain, numeric, categorical,
                            model_id, row_ids, selected["operating_threshold"], selected)
    return fitted, spec, {"selection": selected, "candidates": candidates,
                          "inner_selection_seed": SEED + seed_offset,
                          "final_calibration_seed": SEED + 1000 + seed_offset,
                          "diagnostics_only": True, "holdout_scored": False}


def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == frozen["dataset_sha256"]
    # Select development rows immediately. No holdout inputs or labels used below.
    data = pd.read_excel(SOURCE, sheet_name=0).iloc[frozen["development_row_indices"]].copy()
    data.columns = data.columns.str.strip()
    Xdev = data.drop(columns=EXCLUDE).reset_index(drop=True)
    for col in Xdev.select_dtypes(include=["object", "str"]).columns:
        Xdev[col] = Xdev[col].str.strip().astype(object)
    ydev = pd.DataFrame({name: (data[col].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int).to_numpy()
                         for name, col in TARGETS.items()})
    del data
    dev_ids = np.asarray(frozen["development_row_indices"])
    numeric = Xdev.select_dtypes(include="number").columns.tolist()
    categorical = [c for c in Xdev if c not in numeric]
    assert not set(EXCLUDE) & set(Xdev) and len(Xdev.columns) == 55
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(Xdev, ydev.CAD))
    fold_assignment = np.zeros(len(Xdev), int)
    saved_models, summaries, oof_table = {}, {}, pd.DataFrame({"row_index": dev_ids})
    protocol = {
        "dataset": "UCI 411 extension of Z-Alizadeh Sani", "seed": SEED,
        "n_total": 303, "n_development": len(Xdev), "n_locked_holdout": len(frozen["holdout_row_indices"]),
        "excluded_features": EXCLUDE, "n_input_features": len(Xdev.columns),
        "numeric_features": numeric, "categorical_features": categorical,
        "outer_cv": "Same 5 shared CAD-stratified development folds as v1",
        "inner_cv": "3 target-stratified folds; preprocessing fit independently inside each training partition",
        "selection_metric": "Mean log loss on pooled inner OOF probabilities; select C, class weighting and sigmoid calibration together",
        "c_grid": C_GRID, "families": FAMILIES,
        "calibration": "Sigmoid with ensemble=False; each inner estimator calibrates on its own 3 cross-fitted subfolds; final outer estimator calibrates on 3 cross-fitted outer-training subfolds",
        "classification_threshold": "Different in each outer model: maximize F1 on its selected candidate's inner OOF probabilities over 0.05..0.95 in 0.01 steps",
        "threshold_tie_break": "Closest to 0.5, then the higher threshold",
        "holdout_scored": False, "sklearn_version": sklearn.__version__,
        "comparison": "Outer validation evaluates the entire inner-selection procedure, not the best family selected by outer score. All family comparisons are exploratory development results.",
        "auc_ci": "1000 patient bootstrap resamples of fixed development OOF predictions; conditional, excludes retraining and experiment-selection uncertainty",
        "calibration_warning": "A sigmoid calibration step does not establish calibrated patient probabilities; reliability bins are small and Brier combines calibration and discrimination",
        "limitations": ["Small single dataset; no external or prospective validation.",
                       "V2 protocol was developed after viewing v1 development results. Final holdout remains frozen.",
                       "Inner model/threshold optimization scores are training diagnostics and are not performance claims.",
                       "Four independent predictions are not constrained to a joint CAD/vessel disease model.",
                       "F1-selected thresholds are research operating points, not medical recommendations."],
    }
    benchmark = {"protocol": protocol, "development_audit": json.loads((ROOT / "results" / "benchmark.json").read_text())["development_audit"], "targets": {}}
    save("split.json", frozen)
    save("progress.json", {"stage": "running", "holdout_scored": False})
    for target in TARGETS:
        yt = ydev[target].to_numpy()
        probabilities = {family: np.full(len(Xdev), np.nan) for family in FAMILIES + ["selected"]}
        decisions = {family: np.zeros(len(Xdev), bool) for family in FAMILIES + ["selected"]}
        threshold_array = {family: np.full(len(Xdev), np.nan) for family in FAMILIES + ["selected"]}
        records = []
        for fold, (tr, te) in enumerate(folds):
            fold_assignment[te] = fold
            Xtrain, ytrain = Xdev.iloc[tr], yt[tr]
            inner_splits = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + fold).split(Xtrain, ytrain))
            candidates = []
            # None of these fits receives the outer validation inputs or labels.
            for family in FAMILIES:
                for C in C_GRID:
                    inner_p = np.full(len(tr), np.nan)
                    for k, (fit_idx, val_idx) in enumerate(inner_splits):
                        estimator = make_estimator(family, C, numeric, categorical,
                                                   SEED + 100 + 10 * fold + k)
                        estimator.fit(Xtrain.iloc[fit_idx], ytrain[fit_idx])
                        inner_p[val_idx] = estimator.predict_proba(Xtrain.iloc[val_idx])[:, 1]
                    threshold, training_f1 = threshold_from_inner(ytrain, inner_p)
                    candidates.append({"family": family, "C": C, "inner_log_loss": float(log_loss(ytrain, inner_p)),
                                       "inner_roc_auc": float(roc_auc_score(ytrain, inner_p)),
                                       "operating_threshold": threshold, "inner_threshold_f1_training_diagnostic": training_f1})
            # Stable sort maintains predeclared family/C order in an exact tie.
            ranked = sorted(candidates, key=lambda candidate: candidate["inner_log_loss"])
            selected = ranked[0]
            family_best = {family: next(row for row in ranked if row["family"] == family) for family in FAMILIES}
            record = {"fold": fold, "train_n": len(tr), "validation_n": len(te),
                      "train_positive": int(yt[tr].sum()), "validation_positive": int(yt[te].sum()),
                      "selection": selected, "inner_candidates": candidates, "families": {}}
            fitted_best = {}
            for family, choice in family_best.items():
                estimator = make_estimator(family, choice["C"], numeric, categorical, SEED + 1000 + fold)
                estimator.fit(Xtrain, ytrain)
                p = estimator.predict_proba(Xdev.iloc[te])[:, 1]
                pred = p >= choice["operating_threshold"]
                probabilities[family][te], decisions[family][te] = p, pred
                threshold_array[family][te] = choice["operating_threshold"]
                record["families"][family] = {"parameters": choice, "metrics": metrics(yt[te], p, pred),
                                              "metrics_at_0_5": metrics(yt[te], p)}
                fitted_best[family] = estimator
            family = selected["family"]
            probabilities["selected"][te] = probabilities[family][te]
            decisions["selected"][te] = decisions[family][te]
            threshold_array["selected"][te] = threshold_array[family][te]
            model_id = f"{target}-outer-{fold}"
            spec = export_estimator(fitted_best[family], family, Xtrain, numeric, categorical,
                                    model_id, dev_ids[tr], selected["operating_threshold"], selected)
            assert not set(spec["training_row_indices"]) & set(dev_ids[te])
            exported_p = np.asarray([predict_json(spec, Xdev.iloc[i].to_dict())["probability"] for i in te])
            error = float(np.max(np.abs(exported_p - probabilities["selected"][te])))
            assert np.allclose(exported_p, probabilities["selected"][te], atol=1e-12, rtol=0)
            saved_models[model_id] = spec
            joblib.dump(fitted_best[family], OUT / f"{model_id}.joblib")
            record["selected"] = {"parameters": selected, "metrics": metrics(yt[te], probabilities["selected"][te], decisions["selected"][te]),
                                   "metrics_at_0_5": metrics(yt[te], probabilities["selected"][te]),
                                   "json_inference_max_abs_error": error}
            record["logistic"] = record["selected"]
            records.append(record)
            print(f"{target} outer {fold + 1}/5: {family} C={selected['C']} threshold={selected['operating_threshold']:.2f}", flush=True)
            save("progress.json", {"stage": "nested_cv", "target": target, "fold_completed": fold + 1, "holdout_scored": False})
        oof_metrics = {}
        for family in FAMILIES + ["selected"]:
            p, pred = probabilities[family], decisions[family]
            assert np.isfinite(p).all()
            oof_metrics[family] = {**metrics(yt, p, pred), "metrics_at_0_5": metrics(yt, p),
                                   "roc_auc_95_ci_conditional": ci(yt, p), "calibration_bins": calibration_bins(yt, p),
                                   "outer_thresholds": [float(threshold_array[family][te[0]]) for _, te in folds]}
            oof_table[f"{target}_{family}"] = p
            oof_table[f"{target}_{family}_decision"] = pred.astype(int)
            oof_table[f"{target}_{family}_threshold"] = threshold_array[family]
        # Compatibility alias refers to the predeclared nested procedure, not an outer winner.
        oof_metrics["logistic"] = copy.deepcopy(oof_metrics["selected"])
        oof_metrics["logistic"]["display_name"] = "Nested selected logistic"
        oof_table[f"{target}_truth"] = yt
        benchmark["targets"][target] = {"positive_n": int(yt.sum()), "negative_n": int(len(yt) - yt.sum()),
                                         "oof": oof_metrics, "outer_folds": records}
        save("benchmark.json", benchmark)
        save("models.json", {"schema_version": 1, "experiment_version": 2, "models": saved_models,
                              "feature_order": Xdev.columns.tolist(), "targets": list(TARGETS)})
    oof_table["fold"] = fold_assignment
    oof_table.to_csv(OUT / "development_oof.csv", index=False)
    existing_cases = json.loads((ROOT / "results" / "cases.json").read_text())
    cases = []
    for original in existing_cases["cases"]:
        case = {key: copy.deepcopy(value) for key, value in original.items() if key != "predictions"}
        case["predictions"] = {}
        for target in TARGETS:
            spec = saved_models[f"{target}-outer-{case['fold']}"]
            assert case["row_index"] not in spec["training_row_indices"]
            result = predict_json(spec, case["inputs"])
            result["operating_threshold"] = spec["operating_threshold"]
            result["predicted_label"] = int(result["probability"] >= spec["operating_threshold"])
            result["model_family"] = spec["family"]
            result["calibration"] = spec["calibration"]["method"]
            case["predictions"][target] = result
        cases.append(case)
    save("cases.json", {"schema_version": 1, "experiment_version": 2, "selection": existing_cases["selection"],
                         "holdout_included": False, "prediction_type": "Outer-fold out-of-fold nested selected logistic",
                         "cases": cases})
    save("input_schema.json", json.loads((ROOT / "results" / "input_schema.json").read_text()))
    benchmark["runtime_seconds"] = round(time.perf_counter() - started, 3)
    benchmark["portable_model_validation"] = {"n_oof_predictions_checked": len(Xdev) * len(TARGETS),
                                               "atol": 1e-12, "all_passed": True,
                                               "maximum_absolute_error": max(r["selected"]["json_inference_max_abs_error"]
                                                                              for t in TARGETS for r in benchmark["targets"][t]["outer_folds"])}
    save("benchmark.json", benchmark)
    save("progress.json", {"stage": "complete", "runtime_seconds": benchmark["runtime_seconds"], "holdout_scored": False})
    print(json.dumps({target: {key: round(value, 3) for key, value in benchmark["targets"][target]["oof"]["selected"].items()
                              if key in ["roc_auc", "f1", "recall", "precision", "accuracy", "brier", "log_loss"]}
                      for target in TARGETS}, indent=2), flush=True)
    print(f"Finished in {benchmark['runtime_seconds']}s. Frozen final holdout untouched.", flush=True)


if __name__ == "__main__":
    main()
