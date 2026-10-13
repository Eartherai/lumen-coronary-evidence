"""One predeclared, bounded CPU CatBoost development experiment.

No final holdout inputs are supplied to any fit, prediction, or metric.
All outputs stay in this new dated directory. No models are exported.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import resource
import signal
import sys
import time
import traceback
from pathlib import Path

OUT = Path(__file__).resolve().parent
TRAINING = OUT.parent
PROJECT = TRAINING.parent
SOURCE = TRAINING / "extention of Z-Alizadeh sani dataset.xlsx"
READ_PATHS: set[str] = set()
BLOCKED_READS: list[str] = []
FORBIDDEN_PARTS = (
    "results-final-development", "holdout_predictions", "final_evaluation",
    "final_models", "evaluate_final.py", "fit_final_development.py",
)


def audit(event, args):
    if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(args[0])).absolute()
    mode = args[1]
    flags = args[2]
    reading = (isinstance(mode, str) and "r" in mode) or (
        mode is None and isinstance(flags, int) and (flags & os.O_ACCMODE) == os.O_RDONLY
    )
    if not reading:
        return
    if any(part in str(path) for part in FORBIDDEN_PARTS):
        BLOCKED_READS.append(str(path))
        raise PermissionError(f"Final holdout artifact access is forbidden: {path}")
    try:
        rel = path.relative_to(PROJECT)
        if not path.is_relative_to(OUT):
            READ_PATHS.add(str(rel))
    except ValueError:
        pass


sys.addaudithook(audit)
sys.path.insert(0, str(TRAINING))

import catboost  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402
import sklearn  # noqa: E402
from catboost import CatBoostClassifier  # noqa: E402
from sklearn.metrics import log_loss  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from benchmark import EXCLUDE, SEED, TARGETS, primitive  # noqa: E402
from experiment_v2 import metrics, threshold_from_inner  # noqa: E402


class BudgetExceeded(RuntimeError):
    pass


def save(name, value):
    p = OUT / name
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, default=primitive, allow_nan=False) + "\n")
    tmp.replace(p)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def peak_rss_bytes():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if platform.system() == "Darwin" else rss * 1024)


def native_frame(X):
    """Pure row-wise type/missing conversion; no fitted global statistics."""
    out = X.copy()
    numeric = out.select_dtypes(include="number").columns.tolist()
    categorical = [c for c in out if c not in numeric]
    for feature in numeric:
        out[feature] = pd.to_numeric(out[feature], errors="raise").astype(float)
    for feature in categorical:
        out[feature] = out[feature].map(
            lambda v: "__MISSING__" if pd.isna(v) or str(v).strip() == "" else str(v).strip()
        )
    return out, numeric, categorical


def main():
    started = time.perf_counter()
    started_utc = utc()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    declaration = json.loads((OUT / "run-declaration.json").read_text())
    assert declaration["script_sha256"] == sha(Path(__file__))
    assert declaration["protocol_sha256"] == sha(OUT / "protocol.json")
    protocol = json.loads((OUT / "protocol.json").read_text())
    configurations = protocol["configurations"]
    fixed = protocol["fixed_parameters"]
    assert len(configurations) == 3
    assert fixed["thread_count"] <= 2 and fixed["task_type"] == "CPU"
    assert max(c["iterations"] for c in configurations) <= 300
    split_path = TRAINING / "results" / "split.json"
    frozen = json.loads(split_path.read_text())
    assert sha(SOURCE) == frozen["dataset_sha256"] == protocol["source_sha256"]
    dev_ids = np.asarray(frozen["development_row_indices"], dtype=int)
    holdout_ids = set(frozen["holdout_row_indices"])
    assert len(dev_ids) == 242 and len(set(dev_ids)) == 242
    assert not set(dev_ids) & holdout_ids
    assert dev_ids.tolist() == protocol["development_row_indices"]
    # Immediately select authorized rows; no holdout input/label is retained.
    data = pd.read_excel(SOURCE, sheet_name=0).iloc[dev_ids].copy()
    data.columns = data.columns.str.strip()
    X = data.drop(columns=EXCLUDE).reset_index(drop=True)
    y = pd.DataFrame({
        name: (data[column].str.strip() == ("CAD" if name == "CAD" else "Stenotic")).astype(int).to_numpy()
        for name, column in TARGETS.items()
    })
    del data
    X, numeric, categorical = native_frame(X)
    assert len(X.columns) == 55 and not set(EXCLUDE) & set(X.columns)
    assert list(TARGETS) == ["CAD", "LAD", "LCX", "RCA"]
    outer = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y.CAD))
    fold_assignment = np.zeros(len(X), int)
    for fold, (tr, te) in enumerate(outer):
        fold_assignment[te] = fold
        assert not set(dev_ids[tr]) & set(dev_ids[te])
        assert not set(dev_ids[tr]) & holdout_ids
    baseline_path = TRAINING / "results-v2" / "development_oof.csv"
    baseline = pd.read_csv(baseline_path).set_index("row_index").loc[dev_ids].reset_index()
    assert baseline.row_index.tolist() == dev_ids.tolist()
    assert np.array_equal(baseline.fold.to_numpy(), fold_assignment)
    for target in TARGETS:
        assert np.array_equal(baseline[f"{target}_truth"].to_numpy(), y[target].to_numpy())

    benchmark = {
        "scope": "Exploratory development only; no final holdout access/scoring/model replacement",
        "protocol_sha256": sha(OUT / "protocol.json"),
        "script_sha256": sha(Path(__file__)),
        "source_sha256": sha(SOURCE),
        "split_sha256": sha(split_path),
        "baseline_oof_sha256": sha(baseline_path),
        "n_development": len(X), "n_locked_holdout": len(holdout_ids),
        "holdout_scored": False,
        "numeric_features": numeric, "categorical_features": categorical,
        "categorical_cardinality_development_diagnostic": {c: int(X[c].nunique()) for c in categorical},
        "versions": {"python": platform.python_version(), "catboost": catboost.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__,
                     "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "environment": {"platform": platform.platform(), "machine": platform.machine(),
                        "cpu_count": os.cpu_count(), "thread_count_per_fit": 2,
                        "gpu_used": False},
        "started_utc": started_utc, "status": "running", "targets": {},
    }
    table = pd.DataFrame({"row_index": dev_ids, "fold": fold_assignment})
    fit_ledger = []
    inner_predictions = []
    fold_records = []

    def persist():
        benchmark["elapsed_wall_seconds"] = time.perf_counter() - started
        benchmark["fit_count"] = len(fit_ledger)
        benchmark["process_peak_rss_bytes"] = peak_rss_bytes()
        benchmark["project_read_paths"] = sorted(READ_PATHS)
        benchmark["blocked_artifact_reads"] = BLOCKED_READS
        save("benchmark.json", benchmark)
        save("fit-ledger.json", fit_ledger)
        save("inner-oof-predictions.json", inner_predictions)
        save("fold-training-identities.json", fold_records)
        table.to_csv(OUT / "development-oof.csv", index=False)

    def check_budget():
        if time.perf_counter() - started >= protocol["cpu_wall_budget_seconds"]:
            raise BudgetExceeded("The predeclared 600-second CPU wall budget expired")

    def timeout(signum, frame):
        raise BudgetExceeded("The predeclared 600-second CPU wall budget expired")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(protocol["cpu_wall_budget_seconds"])

    def fit_model(config, target, outer_fold, stage, fit_idx, validation_idx):
        check_budget()
        assert not set(dev_ids[fit_idx]) & holdout_ids
        assert not set(fit_idx) & set(validation_idx)
        parameters = {k: v for k, v in config.items() if k != "id"}
        estimator = CatBoostClassifier(
            **parameters, **fixed, random_seed=SEED, cat_features=categorical
        )
        save("progress.json", {"status": "running", "target": target, "outer_fold": outer_fold,
                               "stage": stage, "configuration": config["id"],
                               "completed_fits": len(fit_ledger),
                               "elapsed_wall_seconds": time.perf_counter() - started,
                               "holdout_scored": False})
        fit_start = time.perf_counter()
        estimator.fit(X.iloc[fit_idx], y[target].to_numpy()[fit_idx])
        fit_elapsed = time.perf_counter() - fit_start
        assert estimator.tree_count_ == config["iterations"]
        fit_ledger.append({"target": target, "outer_fold": outer_fold, "stage": stage,
                           "configuration": config["id"], "tree_count": estimator.tree_count_,
                           "fit_row_indices": dev_ids[fit_idx].tolist(),
                           "validation_row_indices": dev_ids[validation_idx].tolist(),
                           "fit_wall_seconds": fit_elapsed, "peak_rss_bytes": peak_rss_bytes()})
        check_budget()
        return estimator

    try:
        for target in TARGETS:
            yt = y[target].to_numpy()
            p_all = np.full(len(X), np.nan)
            decision_all = np.full(len(X), -1, int)
            threshold_all = np.full(len(X), np.nan)
            records = []
            benchmark["targets"][target] = {"status": "running", "outer_folds": records}
            table[f"{target}_truth"] = yt
            table[f"{target}_probability"] = p_all
            table[f"{target}_decision"] = decision_all
            table[f"{target}_threshold"] = threshold_all
            for fold, (tr, te) in enumerate(outer):
                inner = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + fold).split(X.iloc[tr], yt[tr]))
                fold_records.append({"target": target, "outer_fold": fold,
                                     "outer_training_row_indices": dev_ids[tr].tolist(),
                                     "outer_validation_row_indices": dev_ids[te].tolist(),
                                     "inner_seed": SEED + fold,
                                     "inner_partitions": [{"inner_fold": k,
                                                           "training_row_indices": dev_ids[tr[fit]].tolist(),
                                                           "validation_row_indices": dev_ids[tr[val]].tolist()}
                                                          for k, (fit, val) in enumerate(inner)]})
                candidates = []
                for config in configurations:
                    inner_p = np.full(len(tr), np.nan)
                    for k, (fit, val) in enumerate(inner):
                        estimator = fit_model(config, target, fold, f"inner-{k}", tr[fit], tr[val])
                        assert not set(dev_ids[tr[fit]]) & set(dev_ids[te])
                        inner_p[val] = estimator.predict_proba(X.iloc[tr[val]])[:, 1]
                        del estimator
                    assert np.isfinite(inner_p).all()
                    threshold, inner_f1 = threshold_from_inner(yt[tr], inner_p)
                    candidates.append({"configuration": config, "inner_log_loss": float(log_loss(yt[tr], inner_p)),
                                       "operating_threshold": threshold,
                                       "inner_threshold_f1_training_diagnostic": inner_f1})
                    inner_predictions.append({"target": target, "outer_fold": fold, "configuration": config["id"],
                                              "row_indices": dev_ids[tr].tolist(),
                                              "truth": yt[tr].tolist(), "probabilities": inner_p.tolist()})
                selected = min(candidates, key=lambda c: c["inner_log_loss"])
                estimator = fit_model(selected["configuration"], target, fold, "outer-final-fit", tr, te)
                p = estimator.predict_proba(X.iloc[te])[:, 1]
                threshold = selected["operating_threshold"]
                pred = p >= threshold
                p_all[te], decision_all[te], threshold_all[te] = p, pred.astype(int), threshold
                records.append({"fold": fold, "train_n": len(tr), "validation_n": len(te),
                                "inner_candidates": candidates, "selected": selected,
                                "fitted_native_parameters": estimator.get_all_params(),
                                "metrics": metrics(yt[te], p, pred),
                                "metrics_at_0_5": metrics(yt[te], p)})
                del estimator
                table[f"{target}_probability"] = p_all
                table[f"{target}_decision"] = decision_all
                table[f"{target}_threshold"] = threshold_all
                persist()
                print(f"{target} fold {fold + 1}/5 complete; selected {selected['configuration']['id']}; "
                      f"fits {len(fit_ledger)}/200; wall {time.perf_counter() - started:.1f}s", flush=True)
            assert np.isfinite(p_all).all()
            cb_metrics = metrics(yt, p_all, decision_all)
            v2_metrics = metrics(yt, baseline[f"{target}_selected"].to_numpy(),
                                 baseline[f"{target}_selected_decision"].to_numpy())
            base_correct = baseline[f"{target}_selected_decision"].to_numpy() == yt
            cb_correct = decision_all == yt
            benchmark["targets"][target].update({
                "status": "complete", "oof": cb_metrics, "metrics_at_0_5": metrics(yt, p_all),
                "v2_paired_same_rows": v2_metrics,
                "catboost_minus_v2": {name: cb_metrics[name] - v2_metrics[name]
                                      for name in ("roc_auc", "average_precision", "accuracy", "precision", "recall", "f1", "brier", "log_loss")},
                "paired_correctness_counts": {"both_correct": int((base_correct & cb_correct).sum()),
                                              "v2_correct_catboost_wrong": int((base_correct & ~cb_correct).sum()),
                                              "v2_wrong_catboost_correct": int((~base_correct & cb_correct).sum()),
                                              "both_wrong": int((~base_correct & ~cb_correct).sum())},
                "comparison_warning": "Descriptive paired development results after previous development experiments; no significance, final-test or clinical superiority claim",
            })
            persist()
        assert len(fit_ledger) == 200
        assert not BLOCKED_READS
        benchmark["status"] = "complete"
    except Exception as error:
        benchmark["status"] = "incomplete_budget" if isinstance(error, BudgetExceeded) else "failed"
        benchmark["failure"] = {"class": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        print(benchmark["failure"]["traceback"], flush=True)
    finally:
        signal.alarm(0)
        usage_end = resource.getrusage(resource.RUSAGE_SELF)
        benchmark["completed_utc"] = utc()
        benchmark["cpu_user_seconds"] = usage_end.ru_utime - usage_start.ru_utime
        benchmark["cpu_system_seconds"] = usage_end.ru_stime - usage_start.ru_stime
        persist()
        save("progress.json", {"status": benchmark["status"], "completed_fits": len(fit_ledger),
                               "elapsed_wall_seconds": benchmark["elapsed_wall_seconds"], "holdout_scored": False})
    if benchmark["status"] != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
