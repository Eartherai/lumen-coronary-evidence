"""Verify saved CatBoost probe receipts and predictions without any model fit."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
TRAINING = OUT.parent
sys.path.insert(0, str(TRAINING))

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold

from experiment_v2 import metrics, threshold_from_inner


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    protocol = json.loads((OUT / "protocol.json").read_text())
    declaration = json.loads((OUT / "run-declaration.json").read_text())
    benchmark = json.loads((OUT / "benchmark.json").read_text())
    ledger = json.loads((OUT / "fit-ledger.json").read_text())
    inner_predictions = json.loads((OUT / "inner-oof-predictions.json").read_text())
    fold_records = json.loads((OUT / "fold-training-identities.json").read_text())
    split = json.loads((TRAINING / "results/split.json").read_text())
    table = pd.read_csv(OUT / "development-oof.csv")
    baseline = pd.read_csv(TRAINING / "results-v2/development_oof.csv").set_index("row_index").loc[table.row_index].reset_index()
    dev_ids = np.asarray(split["development_row_indices"])
    holdout_ids = set(split["holdout_row_indices"])
    assert benchmark["status"] == "complete"
    assert benchmark["holdout_scored"] is False
    assert benchmark["blocked_artifact_reads"] == []
    assert benchmark["fit_count"] == len(ledger) == 200
    assert len(inner_predictions) == 60 and len(fold_records) == 20
    assert benchmark["elapsed_wall_seconds"] < protocol["cpu_wall_budget_seconds"]
    assert benchmark["protocol_sha256"] == declaration["protocol_sha256"] == sha(OUT / "protocol.json")
    assert benchmark["script_sha256"] == declaration["script_sha256"] == sha(OUT / "probe.py")
    assert table.row_index.tolist() == baseline.row_index.tolist() == dev_ids.tolist()
    assert np.array_equal(table.fold, baseline.fold)
    assert not set(table.row_index) & holdout_ids
    assert len(benchmark["numeric_features"]) + len(benchmark["categorical_features"]) == 55
    assert not set(protocol["excluded_inputs"]) & set(benchmark["numeric_features"] + benchmark["categorical_features"])
    outer = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=2026).split(table, table.CAD_truth))
    candidate_checks = 0
    for target in ("CAD", "LAD", "LCX", "RCA"):
        yt = table[f"{target}_truth"].to_numpy()
        assert np.array_equal(yt, baseline[f"{target}_truth"])
        p = table[f"{target}_probability"].to_numpy()
        decision = table[f"{target}_decision"].to_numpy()
        thresholds = table[f"{target}_threshold"].to_numpy()
        assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
        assert np.array_equal(decision, (p >= thresholds).astype(int))
        recorded = benchmark["targets"][target]
        recomputed = metrics(yt, p, decision)
        v2_metrics = metrics(yt, baseline[f"{target}_selected"].to_numpy(),
                             baseline[f"{target}_selected_decision"].to_numpy())
        for name in ("roc_auc", "average_precision", "accuracy", "precision", "recall", "f1", "brier", "log_loss"):
            assert abs(recomputed[name] - recorded["oof"][name]) < 1e-12
            assert abs(v2_metrics[name] - recorded["v2_paired_same_rows"][name]) < 1e-12
            assert abs(recomputed[name] - v2_metrics[name] - recorded["catboost_minus_v2"][name]) < 1e-12
        assert recomputed["confusion_matrix_tn_fp_fn_tp"] == recorded["oof"]["confusion_matrix_tn_fp_fn_tp"]
        for fold, (tr, te) in enumerate(outer):
            rec = next(r for r in fold_records if r["target"] == target and r["outer_fold"] == fold)
            assert rec["outer_training_row_indices"] == dev_ids[tr].tolist()
            assert rec["outer_validation_row_indices"] == dev_ids[te].tolist()
            inner = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=2026 + fold).split(table.iloc[tr], yt[tr]))
            for k, (fit, val) in enumerate(inner):
                assert rec["inner_partitions"][k]["training_row_indices"] == dev_ids[tr[fit]].tolist()
                assert rec["inner_partitions"][k]["validation_row_indices"] == dev_ids[tr[val]].tolist()
            fold_benchmark = recorded["outer_folds"][fold]
            for configuration in protocol["configurations"]:
                inner_p = next(r for r in inner_predictions if r["target"] == target and r["outer_fold"] == fold and r["configuration"] == configuration["id"])
                assert inner_p["row_indices"] == dev_ids[tr].tolist()
                assert inner_p["truth"] == yt[tr].tolist()
                candidate = next(c for c in fold_benchmark["inner_candidates"] if c["configuration"]["id"] == configuration["id"])
                predicted = np.asarray(inner_p["probabilities"])
                assert np.isfinite(predicted).all()
                assert abs(log_loss(yt[tr], predicted) - candidate["inner_log_loss"]) < 1e-12
                threshold, training_f1 = threshold_from_inner(yt[tr], predicted)
                assert threshold == candidate["operating_threshold"]
                assert abs(training_f1 - candidate["inner_threshold_f1_training_diagnostic"]) < 1e-12
                for k, (fit, val) in enumerate(inner):
                    entry = next(r for r in ledger if r["target"] == target and r["outer_fold"] == fold and r["configuration"] == configuration["id"] and r["stage"] == f"inner-{k}")
                    assert entry["fit_row_indices"] == dev_ids[tr[fit]].tolist()
                    assert entry["validation_row_indices"] == dev_ids[tr[val]].tolist()
                    assert not set(entry["fit_row_indices"]) & (holdout_ids | set(dev_ids[te]) | set(entry["validation_row_indices"]))
                    assert entry["tree_count"] == configuration["iterations"]
                candidate_checks += 1
            selected = min(fold_benchmark["inner_candidates"], key=lambda c: c["inner_log_loss"])
            assert selected == fold_benchmark["selected"]
            assert np.allclose(thresholds[te], selected["operating_threshold"], atol=0, rtol=0)
            final = next(r for r in ledger if r["target"] == target and r["outer_fold"] == fold and r["stage"] == "outer-final-fit")
            assert final["fit_row_indices"] == dev_ids[tr].tolist()
            assert final["validation_row_indices"] == dev_ids[te].tolist()
            assert not set(final["fit_row_indices"]) & (holdout_ids | set(final["validation_row_indices"]))
            assert final["configuration"] == selected["configuration"]["id"]
            native = fold_benchmark["fitted_native_parameters"]
            assert native["task_type"] == "CPU" and native["boosting_type"] == "Ordered"
            assert native["random_seed"] == 2026
    receipt = {"status": "passed", "fit_identity_checks": 200, "candidate_selection_and_threshold_checks": candidate_checks,
               "outer_partition_checks": 20, "paired_target_metric_checks": 4,
               "holdout_scored": False, "model_fits_in_verifier": 0,
               "scope": "Saved receipts/numerical identities verified; does not establish statistical/clinical superiority",
               "hashes": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "verification-receipt.json"}}
    (OUT / "verification-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "hashes"}, indent=2))


if __name__ == "__main__":
    verify()
