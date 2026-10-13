"""True separately fitted feature-availability experiment, development only.

Profiles are an operational grouping informed by primary source categories.
They are not a validated acquisition order. No cost or clinical-utility claim is
made. Every example is excluded from all fitting, calibration and thresholds.
"""
import copy
import hashlib
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from benchmark import EXCLUDE, ROOT, SEED, SOURCE, TARGETS, calibration_bins, ci, primitive
from experiment_v2 import metrics, select_and_fit_development
from predict import predict_json

OUT = ROOT / "results-availability"
GROUP_PATH = ROOT.parent / "submission" / "clinical-groups.json"


def save(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, default=primitive, allow_nan=False))
    tmp.replace(path)


def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    grouping = json.loads(GROUP_PATH.read_text())
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
    flat = [feature for features in grouping["groups"].values() for feature in features]
    assert len(flat) == len(set(flat)) == len(X.columns) == 55 and set(flat) == set(X.columns)
    assert not set(EXCLUDE) & set(flat)
    dev_ids = np.asarray(frozen["development_row_indices"])
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y.CAD))
    v2_models = json.loads((ROOT / "results-v2" / "models.json").read_text())
    v2_benchmark = json.loads((ROOT / "results-v2" / "benchmark.json").read_text())
    v2_cases = json.loads((ROOT / "results-v2" / "cases.json").read_text())
    v2_oof = pd.read_csv(ROOT / "results-v2" / "development_oof.csv")
    model_output = {"schema_version": 1, "experiment_version": "availability-v1", "models": {},
                    "feature_order": list(X), "targets": list(TARGETS), "profiles": {}}
    profiles = []
    labels = {"history": "History", "history_exam": "History + examination",
              "history_exam_ecg": "History + examination + ECG",
              "history_exam_ecg_lab": "History + examination + ECG + laboratory",
              "all": "All recorded inputs (+ echo)"}
    for profile in grouping["cumulative_profiles"]:
        members = {feature for group in profile["groups"] for feature in grouping["groups"][group]}
        features = [feature for feature in X if feature in members]
        assert len(features) == profile["n_features"]
        profile_id = "full" if profile["id"] == "all" else profile["id"]
        profiles.append({**profile, "id": profile_id, "source_profile_id": profile["id"],
                         "label": labels[profile["id"]], "feature_order": features,
                         "numeric": [field for field in json.loads((ROOT / "results" / "input_schema.json").read_text())["numeric"] if field["feature"] in members],
                         "categorical": [field for field in json.loads((ROOT / "results" / "input_schema.json").read_text())["categorical"] if field["feature"] in members]})
        model_output["profiles"][profile_id] = {"label": labels[profile["id"]], "feature_order": features, "groups": profile["groups"], "n_features": len(features)}
    profiles_payload = {"schema_version": 1, "profiles": profiles, "groups": grouping["groups"],
                        "sources": grouping["sources"], "caveats": grouping["caveats"],
                        "verified_units": grouping["verified_units"], "unverified_units": grouping["unverified_units"]}
    save("profiles.json", profiles_payload)
    result = {"protocol": {**copy.deepcopy(v2_benchmark["protocol"]),
                            "experiment": "Cumulative feature availability, separately fitted reduced-input models",
                            "full_55_policy": "Reuse exact v2 full-55 excluding-fold models and scores",
                            "profile_definition_sha256": hashlib.sha256(GROUP_PATH.read_bytes()).hexdigest(),
                            "profile_definition_source": str(GROUP_PATH),
                            "feature_groups": grouping["groups"],
                            "interpretation": "Development comparison of available-input groups; not causal benefit, test utility, validated workflow or cost effectiveness",
                            "holdout_scored": False}, "profiles": {}}
    table = pd.DataFrame({"row_index": dev_ids, "fold": v2_oof.fold})
    max_errors = []
    for profile in profiles:
        profile_id, features = profile["id"], profile["feature_order"]
        Xprofile = X[features]
        profile_result = {"label": profile["label"], "groups": profile["groups"], "n_features": len(features), "feature_order": features, "targets": {}}
        for target in TARGETS:
            yt = y[target].to_numpy()
            p = np.full(len(X), np.nan)
            pred = np.zeros(len(X), bool)
            thresholds = np.full(len(X), np.nan)
            records = []
            for fold, (tr, te) in enumerate(folds):
                model_id = f"{target}-{profile_id}-outer-{fold}"
                if profile_id == "full":
                    spec = copy.deepcopy(v2_models["models"][f"{target}-outer-{fold}"])
                    spec["model_id"] = model_id
                    diagnostic = {"selection": spec["inner_selection"], "source": "Exact v2 full-55 model reuse", "holdout_scored": False}
                    reference_p = v2_oof.iloc[te][target + "_selected"].to_numpy()
                else:
                    fitted, spec, diagnostic = select_and_fit_development(
                        Xprofile.iloc[tr], yt[tr], dev_ids[tr], model_id, seed_offset=fold,
                        allowed_feature_subset=features)
                    joblib.dump(fitted, OUT / f"{model_id}.joblib")
                    reference_p = fitted.predict_proba(Xprofile.iloc[te])[:, 1]
                assert not set(spec["training_row_indices"]) & set(dev_ids[te])
                assert not set(spec["training_row_indices"]) & set(frozen["holdout_row_indices"])
                spec["profile_id"] = profile_id
                spec["feature_order"] = features
                model_output["models"][model_id] = spec
                portable = [predict_json(spec, Xprofile.iloc[i].to_dict()) for i in te]
                portable_p = np.asarray([row["probability"] for row in portable])
                error = float(np.max(np.abs(portable_p - reference_p)))
                max_errors.append(error)
                assert error < 1e-12
                p[te], pred[te], thresholds[te] = portable_p, [row["predicted_label"] for row in portable], spec["operating_threshold"]
                records.append({"fold": fold, "train_n": len(tr), "validation_n": len(te),
                                "selection": diagnostic["selection"], "metrics": metrics(yt[te], p[te], pred[te]),
                                "metrics_at_0_5": metrics(yt[te], p[te]), "json_inference_max_abs_error": error,
                                "inner_diagnostics": diagnostic})
                print(f"{profile_id} {target} outer {fold + 1}/5 complete", flush=True)
                save("progress.json", {"stage": "running", "profile": profile_id, "target": target,
                                       "fold": fold, "holdout_scored": False})
            assert np.isfinite(p).all()
            summary = {**metrics(yt, p, pred), "metrics_at_0_5": metrics(yt, p),
                       "roc_auc_95_ci_conditional": ci(yt, p), "calibration_bins": calibration_bins(yt, p),
                       "outer_thresholds": [float(thresholds[te[0]]) for _, te in folds]}
            profile_result["targets"][target] = {"positive_n": int(yt.sum()), "negative_n": int(len(yt) - yt.sum()),
                                                  "oof": {"selected": summary, "logistic": copy.deepcopy(summary)}, "outer_folds": records}
            table[f"{profile_id}_{target}_probability"] = p
            table[f"{profile_id}_{target}_decision"] = pred.astype(int)
            table[f"{profile_id}_{target}_threshold"] = thresholds
            table[f"{target}_truth"] = yt
        result["profiles"][profile_id] = profile_result
        save("benchmark.json", result)
        save("models.json", model_output)
    cases = copy.deepcopy(v2_cases)
    cases["experiment_version"] = "availability-v1"
    for case in cases["cases"]:
        case["profile_predictions"] = {}
        for profile in profiles:
            profile_id = profile["id"]
            inputs = {feature: case["inputs"][feature] for feature in profile["feature_order"]}
            case["profile_predictions"][profile_id] = {}
            for target in TARGETS:
                spec = model_output["models"][f"{target}-{profile_id}-outer-{case['fold']}"]
                assert case["row_index"] not in spec["training_row_indices"]
                case["profile_predictions"][profile_id][target] = predict_json(spec, inputs)
        # Keep the default prediction field self-consistent with this directory's
        # model IDs; all four default predictions are exactly the full v2 model.
        case["predictions"] = copy.deepcopy(case["profile_predictions"]["full"])
    cases["profile_input_policy"] = "Original cases keep all raw inputs; filter to profiles[profile_id].feature_order before passing to that model. Missing entire groups are handled by separately fitted profile models, not imputation of unavailable groups."
    save("cases.json", cases)
    table.to_csv(OUT / "development_oof.csv", index=False)
    result["runtime_seconds"] = round(time.perf_counter() - started, 3)
    result["portable_model_validation"] = {"n_oof_predictions_checked": len(X) * len(TARGETS) * len(profiles),
                                           "atol": 1e-12, "maximum_absolute_error": max(max_errors), "all_passed": True}
    save("benchmark.json", result)
    save("progress.json", {"stage": "complete", "runtime_seconds": result["runtime_seconds"], "holdout_scored": False})
    print(json.dumps({profile_id: {target: {key: round(value, 3) for key, value in row["oof"]["selected"].items()
                                          if key in ["roc_auc", "f1", "brier"]}
                                  for target, row in profile["targets"].items()}
                      for profile_id, profile in result["profiles"].items()}, indent=2))
    print(f"Finished in {result['runtime_seconds']}s. Frozen final holdout untouched.", flush=True)


if __name__ == "__main__":
    main()
