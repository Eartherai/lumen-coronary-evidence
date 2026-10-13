"""Verify portable inference, fold exclusion and reusable-fit equivalence.

This script selects development rows immediately and never scores holdout.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from benchmark import EXCLUDE, ROOT, SEED, SOURCE, TARGETS
from experiment_v2 import select_and_fit_development
from predict import predict_json


def main():
    frozen = json.loads((ROOT / "results" / "split.json").read_text())
    data = pd.read_excel(SOURCE).iloc[frozen["development_row_indices"]].copy()
    data.columns = data.columns.str.strip()
    X = data.drop(columns=EXCLUDE).reset_index(drop=True)
    for feature in X.select_dtypes(include=["object", "str"]).columns:
        X[feature] = X[feature].str.strip().astype(object)
    y = pd.DataFrame({name: (data[col].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int).to_numpy()
                      for name, col in TARGETS.items()})
    del data
    models = json.loads((ROOT / "results-v2" / "models.json").read_text())["models"]
    cases = json.loads((ROOT / "results-v2" / "cases.json").read_text())["cases"]
    table = pd.read_csv(ROOT / "results-v2" / "development_oof.csv")
    dev_ids = np.asarray(frozen["development_row_indices"])
    assert table.row_index.tolist() == dev_ids.tolist()
    errors = []
    for i in range(len(X)):
        for target in TARGETS:
            spec = models[f"{target}-outer-{int(table.iloc[i].fold)}"]
            assert int(dev_ids[i]) not in spec["training_row_indices"]
            assert not set(spec["training_row_indices"]) & set(frozen["holdout_row_indices"])
            pred = predict_json(spec, X.iloc[i].to_dict())
            errors.append(abs(pred["probability"] - float(table.iloc[i][target + "_selected"])))
            assert pred["predicted_label"] == int(table.iloc[i][target + "_selected_decision"])
            assert abs(pred["operating_threshold"] - float(table.iloc[i][target + "_selected_threshold"])) < 1e-12
    assert max(errors) < 1e-12
    for case in cases:
        for target in TARGETS:
            spec = models[case["predictions"][target]["model_id"]]
            pred = predict_json(spec, case["inputs"])
            assert abs(pred["probability"] - case["predictions"][target]["probability"]) < 1e-12
            assert pred["predicted_label"] == case["predictions"][target]["predicted_label"]
    spec, raw = models["LCX-outer-0"], X.iloc[0].to_dict()
    bad = dict(raw, Cath="CAD")
    try:
        predict_json(spec, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("Target leakage input accepted")
    bad = dict(raw, Age=float("inf"))
    try:
        predict_json(spec, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("Nonfinite input accepted")
    missing = dict(raw, Age=None)
    assert "Age" in predict_json(spec, missing)["imputed_features"]
    unknown = dict(raw, Sex="outside-dataset")
    assert {"feature": "Sex", "value": "outside-dataset"} in predict_json(spec, unknown)["unknown_categories"]
    tr, te = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y.CAD))[0]
    fitted, reproduced, diagnostic = select_and_fit_development(X.iloc[tr], y.LCX.to_numpy()[tr],
                                                               dev_ids[tr], "LCX-outer-0", seed_offset=0)
    assert reproduced["inner_selection"] == spec["inner_selection"]
    assert reproduced == spec
    assert np.allclose(fitted.predict_proba(X.iloc[te])[:, 1], table.iloc[te].LCX_selected.to_numpy(),
                       atol=1e-12, rtol=0)
    bad_ids = dev_ids[tr].copy()
    bad_ids[0] = frozen["holdout_row_indices"][0]
    try:
        select_and_fit_development(X.iloc[tr], y.LCX.to_numpy()[tr], bad_ids, "LCX-invalid")
    except AssertionError:
        pass
    else:
        raise AssertionError("Reusable fit accepted a frozen holdout row")
    result = {"checked_development_predictions": len(errors), "maximum_absolute_error": max(errors),
              "case_predictions_checked": len(cases) * len(TARGETS), "portable_thresholds_match": True,
              "target_and_nonfinite_inputs_rejected": True, "null_and_unknown_category_diagnostics": True,
              "reusable_fit_reproduces_outer_model_exactly": True,
              "reusable_fit_rejects_holdout_training_identity": True, "holdout_scored": False}
    (ROOT / "results-v2" / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
