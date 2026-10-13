"""Actual SHAP-library verification of grouped linear log-odds explanations.

No fitting or holdout scoring. Each Independent masker contains every encoded
row of that model's own training fold, excluding the explained case/fold and all
frozen holdout records. Calibrated models already compose the sigmoid slope and
offset into their coefficients/intercept, retaining a linear log-odds score.
"""
from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import platform
import time

import numpy as np
import pandas as pd
import shap

from benchmark import EXCLUDE, ROOT, SOURCE
from predict import predict_json, sigmoid


OUT = ROOT / "results-availability"
ATOL = 1e-12
DEPENDENCIES = ["shap", "numpy", "pandas", "openpyxl", "scikit-learn", "scipy",
                "joblib", "threadpoolctl", "numba", "llvmlite", "slicer"]


def encode_frame(spec, raw_frame):
    """Reconstruct exported training-fold preprocessing, without refitting it."""
    columns, coefficients, reference, groups, names = [], [], [], {}, []
    offset = 0
    for field in spec["numeric"]:
        feature = field["feature"]
        raw = pd.to_numeric(raw_frame[feature], errors="raise").to_numpy(dtype=float)
        values = np.where(np.isnan(raw), float(field["impute"]), raw)
        columns.append((values - float(field["mean"])) / float(field["scale"]))
        coefficients.append(float(field["coefficient"]))
        reference.append(float(field["reference_encoded_mean"]))
        groups[feature] = [offset]
        names.append(feature)
        offset += 1
    for field in spec["categorical"]:
        feature = field["feature"]
        values = raw_frame[feature].map(lambda value: str(field["impute"] if pd.isna(value) else value)).to_numpy()
        groups[feature] = []
        for category, coefficient, mean in zip(field["categories"], field["coefficients"], field["reference_encoded_means"]):
            columns.append((values == category).astype(float))
            coefficients.append(float(coefficient))
            reference.append(float(mean))
            groups[feature].append(offset)
            names.append(f"{feature}={category}")
            offset += 1
    return np.column_stack(columns), np.asarray(coefficients), np.asarray(reference), groups, names


def main():
    started = time.perf_counter()
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == frozen["dataset_sha256"]
    # Only development rows are retained before any feature encoding or SHAP call.
    dev = pd.read_excel(SOURCE).iloc[frozen["development_row_indices"]].copy()
    dev.columns = dev.columns.str.strip()
    dev = dev.drop(columns=EXCLUDE)
    for feature in dev.select_dtypes(include=["object", "str"]).columns:
        dev[feature] = dev[feature].str.strip().astype(object)
    dev.index = frozen["development_row_indices"]
    models = json.loads((OUT / "models.json").read_text())["models"]
    models_initial_sha256 = hashlib.sha256((OUT / "models.json").read_bytes()).hexdigest()
    cases = json.loads((OUT / "cases.json").read_text())["cases"]
    profiles = {profile["id"]: profile for profile in json.loads((OUT / "profiles.json").read_text())["profiles"]}
    fold_rows = pd.read_csv(OUT / "development_oof.csv")[["row_index", "fold"]]
    cache, checks, encoded_feature_checks = {}, [], 0
    max_contribution_error = max_baseline_error = max_reconstruction_error = 0.0
    max_training_mean_error = max_probability_error = 0.0
    for case in cases:
        assert case["row_index"] in frozen["development_row_indices"]
        for profile_id, target_predictions in case["profile_predictions"].items():
            features = profiles[profile_id]["feature_order"]
            assert not set(EXCLUDE) & set(features)
            inputs = {feature: case["inputs"][feature] for feature in features}
            for target, saved in target_predictions.items():
                spec = models[saved["model_id"]]
                train_ids = spec["training_row_indices"]
                assert case["row_index"] not in train_ids
                assert set(train_ids) <= set(frozen["development_row_indices"])
                assert not set(train_ids) & set(frozen["holdout_row_indices"])
                validation_ids = fold_rows.loc[fold_rows.fold == case["fold"], "row_index"].tolist()
                assert case["row_index"] in validation_ids
                assert not set(train_ids) & set(validation_ids)
                assert set(features) == {field["feature"] for field in spec["numeric"] + spec["categorical"]}
                if spec["model_id"] not in cache:
                    background_raw = dev.loc[train_ids, features]
                    background, coefficients, reference, groups, names = encode_frame(spec, background_raw)
                    mean_error = float(np.max(np.abs(background.mean(axis=0) - reference)))
                    max_training_mean_error = max(max_training_mean_error, mean_error)
                    assert mean_error < ATOL
                    # Override SHAP's default 100-row subsample so its reference
                    # matches this model's exact entire-training-fold reference.
                    masker = shap.maskers.Independent(background, max_samples=len(train_ids))
                    assert masker.data.shape == background.shape
                    assert np.array_equal(masker.data, background)
                    explainer = shap.LinearExplainer((coefficients, float(spec["intercept"])), masker,
                                                     link=shap.links.identity, feature_names=names)
                    assert explainer.feature_perturbation == "interventional"
                    cache[spec["model_id"]] = (explainer, coefficients, reference, groups, len(train_ids))
                explainer, coefficients, reference, groups, background_n = cache[spec["model_id"]]
                encoded, encoded_coefficients, _, _, _ = encode_frame(spec, pd.DataFrame([inputs]))
                assert np.array_equal(encoded_coefficients, coefficients)
                explanation = explainer(encoded)
                phi = np.asarray(explanation.values[0], dtype=float)
                baseline = float(np.asarray(explanation.base_values).reshape(-1)[0])
                assert len(phi) == len(coefficients)
                grouped_shap = {feature: float(phi[indices].sum()) for feature, indices in groups.items()}
                portable = predict_json(spec, inputs)
                exported = {row["feature"]: row["log_odds_contribution"] for row in portable["contributions"]}
                assert set(grouped_shap) == set(exported) == set(features)
                contribution_error = max(abs(grouped_shap[feature] - exported[feature]) for feature in features)
                baseline_error = abs(baseline - portable["baseline_log_odds"])
                reconstructed = baseline + sum(grouped_shap.values())
                reconstruction_error = abs(reconstructed - portable["log_odds"])
                probability_error = abs(sigmoid(reconstructed) - portable["probability"])
                assert contribution_error < ATOL
                assert baseline_error < ATOL
                assert reconstruction_error < ATOL
                assert probability_error < ATOL
                assert abs(portable["probability"] - saved["probability"]) < ATOL
                max_contribution_error = max(max_contribution_error, contribution_error)
                max_baseline_error = max(max_baseline_error, baseline_error)
                max_reconstruction_error = max(max_reconstruction_error, reconstruction_error)
                max_probability_error = max(max_probability_error, probability_error)
                encoded_feature_checks += len(phi)
                checks.append({"case_id": case["case_id"], "row_index": case["row_index"],
                               "profile_id": profile_id, "target": target, "model_id": spec["model_id"],
                               "calibration": spec["calibration"]["method"], "background_n": background_n,
                               "encoded_features": len(phi), "raw_features": len(features),
                               "maximum_grouped_contribution_error": contribution_error,
                               "baseline_error": baseline_error, "reconstruction_error": reconstruction_error,
                               "probability_error": probability_error,
                               "shap_baseline_log_odds": baseline, "shap_reconstructed_log_odds": reconstructed})
    assert len(checks) == 160
    versions = {package: version(package) for package in DEPENDENCIES}
    manifest = {"python": platform.python_version(), "platform": platform.platform(), "packages": versions,
                "runtime_seconds": round(time.perf_counter() - started, 3),
                "script_sha256": hashlib.sha256((ROOT / "verify_shap.py").read_bytes()).hexdigest(),
                "dataset_sha256": frozen["dataset_sha256"],
                "models_sha256": hashlib.sha256((OUT / "models.json").read_bytes()).hexdigest(),
                "cases_sha256": hashlib.sha256((OUT / "cases.json").read_bytes()).hexdigest()}
    assert manifest["models_sha256"] == models_initial_sha256
    result = {"status": "passed", "method": "Actual shap.LinearExplainer with shap.maskers.Independent training-fold background",
              "approved_display_name": "Grouped interventional linear SHAP (log-odds)",
              "n_case_profile_target_predictions": len(checks), "n_unique_explainers": len(cache),
              "n_encoded_feature_values_checked": encoded_feature_checks,
              "n_sigmoid_calibrated_predictions_checked": sum(row["calibration"] == "sigmoid" for row in checks),
              "atol": ATOL, "maximum_grouped_contribution_error": max_contribution_error,
              "maximum_baseline_error": max_baseline_error, "maximum_reconstruction_error": max_reconstruction_error,
              "maximum_training_reference_mean_error": max_training_mean_error,
              "maximum_probability_error": max_probability_error,
              "background_policy": "All rows from each exported model's training_row_indices; no 100-row background subsample; excludes explained case, its outer validation fold and all frozen holdout rows",
              "model_policy": "Use composed calibration slope/intercept already exported in the linear log-odds model; no weight/calibration/threshold fitting or changes",
              "one_hot_grouping": "Sum SHAP values of all encoded indicator columns belonging to each original categorical feature; numeric predictors each have one encoded column",
              "assumptions": ["Independent masker uses marginal/background expectations and breaks dependencies among encoded predictors.",
                              "Correlated clinical predictors can receive different attribution under a correlation-aware conditional explanation.",
                              "One-hot columns are explained as encoded model inputs and then summed; intermediate independent masks need not preserve valid one-hot states.",
                              "Values are additive effects on this model's log-odds, not additive percentage-point probability effects.",
                              "Background expected value is expected log-odds; its sigmoid is not mean background probability.",
                              "These are model associations, not causal effects, medical recommendations, explanation uncertainty or proof of clinical utility."],
              "sources": ["https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html",
                          "https://shap.readthedocs.io/en/latest/generated/shap.maskers.Independent.html"],
              "holdout_scored": False, "models_changed": False, "manifest": manifest, "checks": checks}
    (OUT / "shap-verification.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    (OUT / "explanation-version-manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False))
    print(json.dumps({key: value for key, value in result.items() if key not in ["checks", "assumptions", "sources", "manifest"]}, indent=2))


if __name__ == "__main__":
    main()
