"""Fit the fixed v2 procedure on development data only; never score holdout.

Run after recording a final protocol freeze. The new-input models differ from
the case-explorer outer-fold models: public development cases must continue to
use their excluding outer-fold model for honest label-reveal comparisons.
"""
import hashlib
import json
import time
from pathlib import Path

import joblib
import pandas as pd

from benchmark import EXCLUDE, ROOT, SOURCE, TARGETS, primitive
from experiment_v2 import select_and_fit_development


def fit_final_development(output_directory=None):
    started = time.perf_counter()
    output = Path(output_directory) if output_directory else ROOT / "results-final-development"
    if (output / "models.json").exists():
        raise FileExistsError("Final-development artifacts already exist; refusing to silently replace a frozen fit")
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == frozen["dataset_sha256"]
    data = pd.read_excel(SOURCE, sheet_name=0).iloc[frozen["development_row_indices"]].copy()
    data.columns = data.columns.str.strip()
    Xtrain = data.drop(columns=EXCLUDE).reset_index(drop=True)
    for feature in Xtrain.select_dtypes(include=["object", "str"]).columns:
        Xtrain[feature] = Xtrain[feature].str.strip().astype(object)
    labels = {name: (data[column].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int).to_numpy()
              for name, column in TARGETS.items()}
    del data
    output.mkdir(exist_ok=True, parents=True)
    models, diagnostics = {}, {}
    for target in TARGETS:
        estimator, spec, diagnostic = select_and_fit_development(
            Xtrain, labels[target], frozen["development_row_indices"], f"{target}-final-development")
        models[spec["model_id"]], diagnostics[target] = spec, diagnostic
        joblib.dump(estimator, output / f"{spec['model_id']}.joblib")
        print(f"{target}: {spec['family']} C={spec['C']} threshold={spec['operating_threshold']}", flush=True)
    payload = {"schema_version": 1, "experiment_version": 2, "use": "New-input inference; never use fitted development rows as unseen examples",
               "models": models, "feature_order": list(Xtrain), "targets": list(TARGETS),
               "training_row_indices": frozen["development_row_indices"], "holdout_scored": False}
    (output / "models.json").write_text(json.dumps(payload, indent=2, default=primitive, allow_nan=False))
    (output / "fit_diagnostics.json").write_text(json.dumps({"targets": diagnostics,
            "runtime_seconds": round(time.perf_counter() - started, 3), "holdout_scored": False},
            indent=2, default=primitive, allow_nan=False))
    return payload


if __name__ == "__main__":
    fit_final_development()
