"""One predeclared profile-agreement rule, existing development OOF only.

Run from any directory with Python's standard library. No fitting or heldout data.
The fixed protocol is written separately before this script is first executed.
"""
import csv
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
PROTOCOL = OUT / "protocol.json"
protocol = json.loads(PROTOCOL.read_text())
assert protocol["rule"]["new_rules_or_tuning_allowed"] is False
allowed_inputs = {(ROOT / name).resolve() for name in protocol["source_sha256"]}
opened = set()


def restrict_open(event, args):
    if event != "open" or isinstance(args[0], int):
        return
    path, _mode, flags = args
    resolved = Path(path).resolve()
    is_write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    if is_write:
        assert resolved.is_relative_to(OUT), f"Write outside owned probe: {resolved}"
    else:
        assert resolved in allowed_inputs or resolved.is_relative_to(OUT), f"Unapproved input: {resolved}"
        opened.add(str(resolved.relative_to(ROOT)))


sys.addaudithook(restrict_open)
started = time.perf_counter()
for name in ("results.json", "row-decisions.csv", "verification-receipt.json"):
    assert not (OUT / name).exists(), "This is one bounded probe; existing outputs cannot be overwritten."


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {name: sha(ROOT / name) for name in protocol["source_sha256"]}


assert source_hashes() == protocol["source_sha256"]
protocol_hash = sha(PROTOCOL)
profiles = protocol["profiles"]
targets = protocol["targets"]
split = json.loads((ROOT / "training/results/split.json").read_text())
# Only development IDs are used. No heldout IDs, heldout row inputs or labels are consumed.
dev_ids = split["development_row_indices"]
assert len(dev_ids) == len(set(dev_ids)) == protocol["n_expected"] == 242
dev_set = set(dev_ids)
del split
profile_meta = json.loads((ROOT / "training/results-availability/profiles.json").read_text())["profiles"]
assert [p["id"] for p in profile_meta] == profiles
assert [p["n_features"] for p in profile_meta] == protocol["feature_counts"]
for i, meta in enumerate(profile_meta):
    assert len(meta["feature_order"]) == len(set(meta["feature_order"])) == meta["n_features"]
    assert not {"Cath", "LAD", "LCX", "RCA"}.intersection(meta["feature_order"])
    if i:
        assert set(profile_meta[i - 1]["feature_order"]).issubset(meta["feature_order"])
verification = json.loads((ROOT / "training/results-availability/verification.json").read_text())
assert verification["holdout_scored"] is False
assert verification["all_model_holdout_training_exclusions_passed"]
assert verification["exact_profile_feature_contracts_passed"]
assert verification["full_profile_matches_v2_metrics"]
assert verification["oof_portable_validation"]["all_passed"]
v2_verification = json.loads((ROOT / "training/results-v2/verification.json").read_text())
assert v2_verification["holdout_scored"] is False
assert v2_verification["portable_thresholds_match"]


def read_rows(name):
    with (ROOT / name).open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 242
    ids = [int(r["row_index"]) for r in rows]
    assert len(ids) == len(set(ids)) and set(ids) == dev_set
    return {int(r["row_index"]): r for r in rows}


availability = read_rows("training/results-availability/development_oof.csv")
v2 = read_rows("training/results-v2/development_oof.csv")
folds = {int(r["fold"]) for r in availability.values()}
assert folds == {0, 1, 2, 3, 4}
fold_members = {fold: {i for i, r in availability.items() if int(r["fold"]) == fold} for fold in sorted(folds)}
model_metadata = json.loads((ROOT / "training/results-availability/models.json").read_text())["models"]
assert len(model_metadata) == 100
thresholds = {}
max_full_probability_difference = 0.0
for row_id in dev_ids:
    row, original = availability[row_id], v2[row_id]
    fold = int(row["fold"])
    assert fold == int(original["fold"])
    for target in targets:
        truth = int(row[target + "_truth"])
        assert truth in (0, 1) and truth == int(original[target + "_truth"])
        for profile in profiles:
            prefix = profile + "_" + target
            p, threshold = float(row[prefix + "_probability"]), float(row[prefix + "_threshold"])
            flag = int(row[prefix + "_decision"])
            assert math.isfinite(p) and math.isfinite(threshold)
            assert 0 <= p <= 1 and 0 <= threshold <= 1 and flag in (0, 1)
            assert flag == int(p >= threshold)
            key = profile, target, fold
            if key in thresholds:
                assert threshold == thresholds[key]
            else:
                thresholds[key] = threshold
        full_p = float(row["full_" + target + "_probability"])
        orig_p = float(original[target + "_selected"])
        assert math.isfinite(orig_p) and 0 <= orig_p <= 1
        difference = abs(full_p - orig_p)
        assert difference < 1e-12
        max_full_probability_difference = max(max_full_probability_difference, difference)
        assert int(row["full_" + target + "_decision"]) == int(original[target + "_selected_decision"])
        assert float(row["full_" + target + "_threshold"]) == float(original[target + "_selected_threshold"])
        assert int(original[target + "_selected_decision"]) == int(orig_p >= float(original[target + "_selected_threshold"]))

for profile, target, fold in thresholds:
    spec = model_metadata[f"{target}-{profile}-outer-{fold}"]
    training_ids = spec["training_row_indices"]
    assert len(training_ids) == len(set(training_ids))
    assert set(training_ids) == dev_set - fold_members[fold]
    assert spec["profile_id"] == profile
    meta = profile_meta[profiles.index(profile)]
    assert spec["feature_order"] == meta["feature_order"]
    assert float(spec["operating_threshold"]) == thresholds[profile, target, fold]
assert len(thresholds) == 100


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def metrics(pairs):
    counts = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    for truth, prediction in pairs:
        key = "TP" if truth and prediction else "FN" if truth else "FP" if prediction else "TN"
        counts[key] += 1
    tp, tn, fp, fn = [counts[k] for k in ("TP", "TN", "FP", "FN")]
    return {"n": len(pairs), **counts, "accuracy": ratio(tp + tn, len(pairs)),
            "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn), "errors": fp + fn}


row_results = []
results = {"protocol_id": protocol["protocol_id"], "protocol_sha256": protocol_hash,
           "scope": protocol["scope"], "n_development": 242, "targets": {},
           "metric_denominators": protocol["denominator_policy"],
           "full_same_retained_subset_policy": "Agreement includes the full profile, so the two retained-subset predictions are identical by construction.",
           "confidence_intervals": None, "calibrated_uncertainty_claim": False,
           "primary_models_or_final_evaluation_changed": False}
for target in targets:
    target_rows = []
    for row_id in dev_ids:
        row = availability[row_id]
        flags = [int(row[profile + "_" + target + "_decision"]) for profile in profiles]
        retain = len(set(flags)) == 1
        truth = int(row[target + "_truth"])
        target_rows.append({"row_index": row_id, "fold": int(row["fold"]), "target": target,
                            "truth": truth, **dict(zip(profiles, flags)), "retained": retain,
                            "retained_prediction": flags[0] if retain else None,
                            "full_prediction": flags[-1], "stable_wrong": retain and flags[0] != truth})
    retained = [r for r in target_rows if r["retained"]]
    withheld = [r for r in target_rows if not r["retained"]]
    positive_n = sum(r["truth"] for r in target_rows)
    negative_n = 242 - positive_n
    retained_positive_n = sum(r["truth"] for r in retained)
    retained_negative_n = len(retained) - retained_positive_n
    retained_metrics = metrics([(r["truth"], r["retained_prediction"]) for r in retained])
    same_subset_metrics = metrics([(r["truth"], r["full_prediction"]) for r in retained])
    assert retained_metrics == same_subset_metrics
    full_baseline = metrics([(r["truth"], r["full_prediction"]) for r in target_rows])
    stable_wrong_rows = [r["row_index"] for r in retained if r["stable_wrong"]]
    assert len(stable_wrong_rows) == retained_metrics["errors"]
    fold_results = []
    for fold in sorted(folds):
        batch = [r for r in target_rows if r["fold"] == fold]
        kept = [r for r in batch if r["retained"]]
        fold_results.append({"fold": fold, "n": len(batch), "retained_n": len(kept),
                             "coverage": ratio(len(kept), len(batch)),
                             "stable_wrong_n": sum(r["stable_wrong"] for r in kept),
                             "retained_metrics": metrics([(r["truth"], r["retained_prediction"]) for r in kept])})
    results["targets"][target] = {
        "positive_n": positive_n, "negative_n": negative_n,
        "retained_n": len(retained), "withheld_n": len(withheld), "coverage": len(retained) / 242,
        "retained_positive_n": retained_positive_n, "retained_negative_n": retained_negative_n,
        "positive_class_coverage": retained_positive_n / positive_n,
        "negative_class_coverage": retained_negative_n / negative_n,
        "withheld_positive_n": positive_n - retained_positive_n,
        "withheld_negative_n": negative_n - retained_negative_n,
        "retained_metrics": retained_metrics, "full_original_same_retained_subset": same_subset_metrics,
        "full_original_all242_baseline": full_baseline,
        "retained_true_positive_yield_all_development_positives": retained_metrics["TP"] / positive_n,
        "stable_wrong_n": len(stable_wrong_rows), "stable_wrong_row_indices": stable_wrong_rows,
        "withheld_full_original_metrics": metrics([(r["truth"], r["full_prediction"]) for r in withheld]),
        "outer_folds_descriptive": fold_results}
    row_results.extend(target_rows)

(OUT / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
with (OUT / "row-decisions.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(row_results[0]))
    writer.writeheader()
    writer.writerows(row_results)
assert source_hashes() == protocol["source_sha256"]
assert sha(PROTOCOL) == protocol_hash
receipt = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "runtime_seconds": time.perf_counter() - started,
           "python": platform.python_version(), "machine": platform.machine(),
           "ml_library_imported": False, "network_library_imported": False, "fitting_or_threshold_search": False,
           "heldout_input_or_label_csv_opened": False, "final_evaluator_called": False,
           "read_allowlist_enforced": True, "writes_restricted_to_owned_probe_directory": True,
           "read_files_after_audit_hook": sorted(opened), "source_hashes_unchanged": True,
           "row_identities_exactly_development_set": True, "row_labels_and_folds_aligned": True,
           "profile_feature_contracts_valid": True,
           "all100_model_training_ids_exact_development_excluding_outer_fold": True,
           "all_recorded_decisions_match_probability_threshold": True,
           "all_thresholds_match_outer_model_metadata": True,
           "max_full_profile_v2_selected_probability_difference": max_full_probability_difference,
           "full_profile_v2_decision_and_threshold_match": True,
           "source_sha256": protocol["source_sha256"],
           "artifact_sha256": {name: sha(OUT / name) for name in ("protocol.json", "probe.py", "results.json", "row-decisions.csv")}}
(OUT / "verification-receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
print(json.dumps({target: {key: row[key] for key in ("coverage", "positive_class_coverage", "negative_class_coverage", "stable_wrong_n", "retained_metrics", "full_original_all242_baseline")}
                  for target, row in results["targets"].items()}, indent=2))
print(f"All checks passed; standard-library-only runtime {receipt['runtime_seconds']:.4f} seconds.")
