"""Execute the frozen full-input final holdout evaluation exactly once.

This module performs no fitting, calibration, threshold tuning or profile
selection. The protocol freeze and all listed training-source hashes must match
before it reads holdout rows. Root reviews and executes this script after the
four full-development models have been fitted. No development examples are
substituted for final holdout cases.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score,
                             brier_score_loss, confusion_matrix, f1_score,
                             log_loss, precision_score, recall_score,
                             roc_auc_score)


ROOT = Path(__file__).resolve().parent
FREEZE_PATH = ROOT.parent / "submission" / "final-protocol-freeze.json"
EXPECTED_FREEZE_SHA256 = "47749cd2a5aa944eb531a6eeb54386cad5e5b29bad9ffa11b048d6715ccc1305"
SOURCE = ROOT / "extention of Z-Alizadeh sani dataset.xlsx"
OUT = ROOT / "results-final-development"
MODEL_PATH = OUT / "models.json"
RESULT_PATH = OUT / "final_evaluation.json"
PREDICTIONS_PATH = OUT / "holdout_predictions.csv"
RUN_CLAIM_PATH = OUT / "final_evaluation.started.json"
TARGETS = {"CAD": "Cath", "LAD": "LAD", "LCX": "LCX", "RCA": "RCA"}
EXCLUDED = {"Cath", "LAD", "LCX", "RCA"}
BOOTSTRAP_SEED = 2026
N_BOOTSTRAP = 1000


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def metric_set(y, probability, threshold):
    """Metrics at an already frozen threshold; never choose one here."""
    prediction = probability >= threshold
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(y, probability)) if len(np.unique(y)) == 2 else None,
        "average_precision": float(average_precision_score(y, probability)) if np.any(y == 1) else None,
        "accuracy": float(accuracy_score(y, prediction)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "brier": float(brier_score_loss(y, probability)),
        "log_loss": float(log_loss(y, probability, labels=[0, 1])),
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "classification_threshold": float(threshold),
        "confusion_matrix_tn_fp_fn_tp": [int(tn), int(fp), int(fn), int(tp)],
        "confusion_counts": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def reliability_bins(y, probability):
    edges = np.linspace(0, 1, 6)
    bins = []
    for i in range(5):
        selected = ((probability >= edges[i]) &
                    ((probability < edges[i + 1]) if i < 4 else (probability <= edges[i + 1])))
        bins.append({"lo": float(edges[i]), "hi": float(edges[i + 1]), "n": int(selected.sum()),
                     "mean_probability": float(probability[selected].mean()) if selected.any() else None,
                     "observed_fraction": float(y[selected].mean()) if selected.any() else None})
    return bins


def conditional_intervals(y, probability, threshold, resamples):
    """Resample patients with fixed predictions and fixed research threshold."""
    auc_values, f1_values, f1_at_half_values = [], [], []
    research_prediction = probability >= threshold
    half_prediction = probability >= 0.5
    for sample in resamples:
        ys = y[sample]
        if len(np.unique(ys)) == 2:
            auc_values.append(float(roc_auc_score(ys, probability[sample])))
        f1_values.append(float(f1_score(ys, research_prediction[sample], zero_division=0)))
        f1_at_half_values.append(float(f1_score(ys, half_prediction[sample], zero_division=0)))

    def interval(values):
        return np.percentile(values, [2.5, 97.5]).tolist() if values else None

    return {"roc_auc_95_ci_conditional": interval(auc_values),
            "f1_95_ci_conditional": interval(f1_values),
            "f1_at_0_5_95_ci_conditional": interval(f1_at_half_values),
            "auc_valid_resamples": len(auc_values), "f1_resamples": len(f1_values),
            "resamples_requested": len(resamples)}


def validate_pre_evaluation():
    """Verify immutable protocol, source and training identities before access."""
    require(not RESULT_PATH.exists(), "Final evaluation already exists; refusing another evaluation")
    require(not PREDICTIONS_PATH.exists(), "Holdout predictions already exist; refusing another evaluation")
    require(not RUN_CLAIM_PATH.exists(),
            "A final evaluation execution was already started; inspect its retained status instead of silently retrying")
    require(FREEZE_PATH.is_file(), "Missing final protocol freeze")
    freeze_hash = sha256(FREEZE_PATH)
    require(freeze_hash == EXPECTED_FREEZE_SHA256, "Protocol freeze SHA-256 mismatch; evaluation refused")
    freeze = json.loads(FREEZE_PATH.read_text())
    require(freeze.get("primary_profile") == "full" and freeze.get("n_features") == 55,
            "The frozen primary procedure must use the full 55-input profile")
    require(set(freeze.get("excluded_features", [])) == EXCLUDED, "Frozen excluded targets mismatch")
    require(freeze.get("c_grid") == [0.01, 0.1, 1, 10], "Frozen regularization grid mismatch")
    frozen_at = datetime.fromisoformat(freeze["frozen_at_utc"])
    require(frozen_at.tzinfo is not None and frozen_at <= datetime.now(timezone.utc),
            "Protocol freeze time must precede evaluation")
    verified_sources = {}
    for relative, expected in freeze["source_sha256"].items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT), "Frozen source path escapes training directory")
        require(path.is_file(), f"Missing frozen source: {relative}")
        actual = sha256(path)
        require(actual == expected, f"Frozen training source SHA-256 mismatch: {relative}")
        verified_sources[relative] = actual
    require(set(verified_sources) == {"benchmark.py", "experiment_v2.py", "fit_final_development.py",
                                     "predict.py", "results/split.json"}, "Incomplete frozen source identities")
    split = json.loads((ROOT / "results" / "split.json").read_text())
    dev_ids, holdout_ids = split["development_row_indices"], split["holdout_row_indices"]
    require(len(dev_ids) == len(set(dev_ids)) == 242, "Expected exactly 242 unique frozen development rows")
    require(len(holdout_ids) == len(set(holdout_ids)) == 61, "Expected exactly 61 unique frozen holdout rows")
    require(not set(dev_ids) & set(holdout_ids), "Development and holdout identities overlap")
    require(set(dev_ids) | set(holdout_ids) == set(range(303)), "Frozen row identities do not partition the source")
    require(sha256(SOURCE) == split["dataset_sha256"], "Dataset SHA-256 differs from the frozen split")
    require(MODEL_PATH.is_file(), "Fit the four final-development models before evaluation")
    payload = json.loads(MODEL_PATH.read_text())
    model_hash = sha256(MODEL_PATH)
    require(payload.get("holdout_scored") is False, "Final fit must not contain a preceding holdout evaluation")
    require(payload.get("targets") == list(TARGETS), "Final model target list mismatch")
    require(set(payload.get("training_row_indices", [])) == set(dev_ids) and
            len(payload["training_row_indices"]) == 242, "Final bundle must use exactly the frozen development rows")
    features = payload["feature_order"]
    require(len(features) == len(set(features)) == 55 and not set(features) & (EXCLUDED | {"CAD"}),
            "Final feature schema must contain exactly 55 non-target inputs")
    schema = json.loads((ROOT / "results" / "input_schema.json").read_text())
    require(features == schema["feature_order"], "Final input feature order differs from the development schema")
    require(set(payload["models"]) == {f"{target}-final-development" for target in TARGETS},
            "Expected only four final-development full-input models")
    for target in TARGETS:
        model = payload["models"][f"{target}-final-development"]
        rows = model["training_row_indices"]
        require(len(rows) == len(set(rows)) == 242 and set(rows) == set(dev_ids),
                f"{target} training identities are not exactly the 242 frozen development rows")
        require(not set(rows) & set(holdout_ids), f"{target} model includes holdout training rows")
        require(model.get("target") == target and model.get("positive_class") == 1,
                f"{target} model target/class mismatch")
        require(model.get("model_type") in ["logistic_regression", "sigmoid_calibrated_logistic"],
                f"{target} is not the frozen linear model family")
        require(model.get("family") in ["unweighted", "balanced", "unweighted_sigmoid", "balanced_sigmoid"],
                f"{target} family is outside the frozen procedure")
        require(float(model["C"]) in freeze["c_grid"], f"{target} regularization differs from frozen grid")
        threshold = float(model["operating_threshold"])
        require(math.isfinite(threshold) and 0.05 <= threshold <= 0.95 and
                abs(100 * threshold - round(100 * threshold)) < 1e-9,
                f"{target} threshold is outside the frozen research grid")
        require(model.get("threshold_selection", {}).get("metric") == "F1",
                f"{target} threshold policy differs from the frozen procedure")
        selection = model["inner_selection"]
        require(selection["family"] == model["family"] and float(selection["C"]) == float(model["C"]) and
                float(selection["operating_threshold"]) == threshold,
                f"{target} exported parameters differ from its recorded development selection")
        expected_calibration = "sigmoid" if model["family"].endswith("sigmoid") else "none"
        require(model["calibration"]["method"] == expected_calibration,
                f"{target} calibration differs from its selected family")
        encoded_fields = [field["feature"] for field in model["numeric"] + model["categorical"]]
        require(len(encoded_fields) == len(set(encoded_fields)) == 55 and set(encoded_fields) == set(features),
                f"{target} encoded inputs differ from the full feature schema")
        if model["calibration"]["method"] == "sigmoid":
            require(set(model["calibration"]["training_row_indices"]) == set(dev_ids),
                    f"{target} calibration reference differs from frozen development rows")
    return freeze, freeze_hash, verified_sources, split, payload, model_hash


def main():
    started = time.perf_counter()
    freeze, freeze_hash, verified_sources, split, payload, model_hash = validate_pre_evaluation()
    OUT.mkdir(exist_ok=True)
    # An exclusive retained claim prevents concurrent or accidental repeat runs.
    # If execution fails, preserve it for review; do not silently re-evaluate.
    claim = {"status": "started", "started_at_utc": utc_now(), "protocol_freeze_sha256": freeze_hash,
             "models_sha256": model_hash, "pid": os.getpid()}
    with RUN_CLAIM_PATH.open("x") as handle:
        json.dump(claim, handle, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        # Import the predictor only after its frozen source identity is checked.
        from predict import predict_json

        holdout_ids = split["holdout_row_indices"]
        holdout = pd.read_excel(SOURCE, sheet_name=0).iloc[holdout_ids].copy()
        holdout.columns = holdout.columns.str.strip()
        require(len(holdout) == 61, "Holdout source row count mismatch")
        for feature in holdout.select_dtypes(include=["object", "str"]).columns:
            holdout[feature] = holdout[feature].str.strip().astype(object)
        # Target columns remain outside the input dictionary for every model.
        X = holdout[payload["feature_order"]]
        labels = {}
        for target, column in TARGETS.items():
            positive = "CAD" if target == "CAD" else "Stenotic"
            require(holdout[column].notna().all(), f"Missing {target} holdout outcome")
            require(set(holdout[column].astype(str)) <= {positive, "Normal"},
                    f"Unexpected {target} holdout outcome category")
            labels[target] = (holdout[column] == positive).astype(int).to_numpy()
        del holdout
        raw_rows = [{feature: (None if pd.isna(value) else value)
                     for feature, value in X.iloc[i].to_dict().items()} for i in range(len(X))]
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        resamples = rng.integers(0, len(X), size=(N_BOOTSTRAP, len(X)))
        predictions_table = pd.DataFrame({"row_index": holdout_ids})
        target_results = {}
        for target in TARGETS:
            model_id = f"{target}-final-development"
            model = payload["models"][model_id]
            threshold = float(model["operating_threshold"])
            outputs = [predict_json(model, inputs) for inputs in raw_rows]
            probability = np.asarray([output["probability"] for output in outputs])
            require(np.isfinite(probability).all() and np.all((probability >= 0) & (probability <= 1)),
                    f"Invalid {target} probability")
            require(all(output["operating_threshold"] == threshold for output in outputs),
                    f"{target} predictor changed the frozen threshold")
            y = labels[target]
            research_metrics = metric_set(y, probability, threshold)
            conventional_metrics = metric_set(y, probability, 0.5)
            intervals = conditional_intervals(y, probability, threshold, resamples)
            research_metrics["roc_auc_95_ci_conditional"] = intervals["roc_auc_95_ci_conditional"]
            research_metrics["f1_95_ci_conditional"] = intervals["f1_95_ci_conditional"]
            conventional_metrics["roc_auc_95_ci_conditional"] = intervals["roc_auc_95_ci_conditional"]
            conventional_metrics["f1_95_ci_conditional"] = intervals["f1_at_0_5_95_ci_conditional"]
            target_results[target] = {
                "model_id": model_id, "recorded_target_column": TARGETS[target],
                "n_positive": int(y.sum()), "n_negative": int(len(y) - y.sum()),
                "operating_threshold": threshold, "threshold_selection": model["threshold_selection"],
                "model_family": model["family"], "C": model["C"],
                "calibration_method": model["calibration"]["method"],
                "metrics": research_metrics, "metrics_at_0_5": conventional_metrics,
                "conditional_intervals": intervals, "calibration_bins": reliability_bins(y, probability),
                "inference_diagnostics": {
                    "rows_with_imputed_features": sum(bool(output["imputed_features"]) for output in outputs),
                    "rows_with_unknown_categories": sum(bool(output["unknown_categories"]) for output in outputs),
                },
            }
            predictions_table[f"{target}_truth"] = y
            predictions_table[f"{target}_probability"] = probability
            predictions_table[f"{target}_operating_threshold"] = threshold
            predictions_table[f"{target}_predicted_label"] = (probability >= threshold).astype(int)
            predictions_table[f"{target}_predicted_label_at_0_5"] = (probability >= 0.5).astype(int)
        require(sha256(MODEL_PATH) == model_hash, "Model bundle changed during final evaluation")
        require(sha256(FREEZE_PATH) == freeze_hash, "Protocol freeze changed during final evaluation")
        for relative, expected in verified_sources.items():
            require(sha256(ROOT / relative) == expected, f"Frozen source changed during final evaluation: {relative}")
        result = {
            "schema_version": 1, "evaluation_status": "complete", "evaluated_at_utc": utc_now(),
            "n_holdout": 61, "n_development": 242, "n_input_features": 55,
            "primary_profile": "full", "holdout_scored": True,
            "protocol": freeze, "targets": target_results,
            "holdout_row_indices": holdout_ids,
            "conditional_bootstrap": {
                "seed": BOOTSTRAP_SEED, "n_resamples": N_BOOTSTRAP,
                "sampling": "Patients sampled with replacement; same 61-row resamples reused across targets",
                "interval": "2.5th and 97.5th percentiles of fixed-model resampled metrics",
                "auc_policy": "Exclude one-class resamples for ROC-AUC; record valid count per target",
                "f1_policy": "Use fixed research threshold; zero_division=0, with conventional 0.5 comparison",
                "limitations": [
                    "Conditional on the fitted development models and thresholds; no retraining or retuning in bootstrap.",
                    "Intervals exclude training, hyperparameter, calibration, threshold and protocol-selection uncertainty.",
                    "A 61-record single-dataset holdout provides limited precision, especially for vessel-specific outcomes.",
                    "No external or prospective validation, clinical operating-point validation or medical-utility claim.",
                    "Reliability bins have small sample counts; calibration fitting and Brier alone do not establish calibrated patient probabilities.",
                ],
            },
            "provenance": {
                "protocol_freeze_sha256": freeze_hash, "dataset_sha256": split["dataset_sha256"],
                "split_sha256": verified_sources["results/split.json"], "models_sha256": model_hash,
                "verified_training_source_sha256": verified_sources,
                "evaluation_script_sha256": sha256(Path(__file__)),
                "training_identity_policy": "Each target model uses exactly the same 242 frozen development identities; disjoint from all 61 holdout identities",
                "no_post_evaluation_retuning": True,
                "versions": {"python": platform.python_version(), "numpy": version("numpy"),
                             "pandas": version("pandas"), "openpyxl": version("openpyxl"),
                             "scikit-learn": version("scikit-learn")},
            },
            "runtime_seconds": round(time.perf_counter() - started, 3),
        }
        # Claim/result existence was checked before any holdout access. Exclusive
        # creation preserves the once-only contract even under concurrent callers.
        with PREDICTIONS_PATH.open("x") as handle:
            predictions_table.to_csv(handle, index=False)
        result["provenance"]["holdout_predictions_sha256"] = sha256(PREDICTIONS_PATH)
        with RESULT_PATH.open("x") as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
        claim.update({"status": "complete", "completed_at_utc": utc_now(),
                      "final_evaluation_sha256": sha256(RESULT_PATH)})
        RUN_CLAIM_PATH.write_text(json.dumps(claim, indent=2, allow_nan=False))
        print(json.dumps({"n_holdout": result["n_holdout"],
                          "targets": {target: row["metrics"] for target, row in result["targets"].items()}}, indent=2))
    except Exception as error:
        claim.update({"status": "failed", "failed_at_utc": utc_now(),
                      "error_type": type(error).__name__, "error": str(error)})
        RUN_CLAIM_PATH.write_text(json.dumps(claim, indent=2, allow_nan=False))
        raise


if __name__ == "__main__":
    main()
