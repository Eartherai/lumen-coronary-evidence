"""Bounded clean-extraction verification; never retrain or rescore final test.

Build a source archive with the release owner's builder unless --archive names
an existing one. Extract into a temporary folder, verify manifest hashes,
install cached runtime modules, run contract tests and development-only SHAP
checks. Evidence is written in the original project after the bounded run.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "submission" / "release-verification.json"
REQUIRED = [
    "README.md", "REPRODUCIBILITY.md", "THIRD_PARTY_NOTICES.md", "LICENSE",
    "requirements-training.txt", "package.json", "package-lock.json", "server.py", "inference.py",
    "artifacts/models.json", "artifacts/cases.json", "artifacts/input_schema.json", "artifacts/benchmark.json",
    "artifacts/availability-models.json", "artifacts/availability-cases.json",
    "artifacts/availability-profiles.json", "artifacts/availability-benchmark.json",
    "artifacts/final_models.json", "artifacts/final_evaluation.json",
    "public/index.html", "public/app.js", "public/style.css", "public/runtime-probe.js", "public/outcome-description.js", "tests/test_runtime_probe.mjs", "tests/test_outcome_description.mjs", "tests/test_case_transition.mjs", ".github/workflows/source-ci.yml",
    "public/evidence-journey.js", "public/anatomy-controls.js", "public/static-client.js",
    "scripts/build_static_demo.py", "tests/test_journey.mjs", "tests/test_static_client.mjs", ".github/workflows/pages.yml",
    "public/assets/anatomy.json", "public/assets/anatomy-provenance.json",
    "public/assets/shap-verification.json", "tests/test_inference.py",
    "artifacts/cohort-audit.json", "public/cohort-audit.js", "public/assets/cohort-audit-verification.json",
    "scripts/build_cohort_audit.py", "training/verify_cohort_audit.py", "docs/cohort-audit.md",
    "tests/test_cohort_api.py", "tests/test_cohort_filters.mjs", "tests/test_cohort_static.mjs",
    "training/benchmark.py", "training/experiment_v2.py", "training/fit_final_development.py",
    "training/evaluate_final.py", "training/predict.py", "training/verify_shap.py",
    "training/requirements-training.txt", "training/requirements-explanation.txt",
    "training/extention of Z-Alizadeh sani dataset.xlsx", "training/download.json", "training/results/split.json",
    "training/results-availability/models.json", "training/results-availability/cases.json",
    "training/results-availability/profiles.json", "training/results-availability/development_oof.csv",
    "training/results-availability/shap-verification.json", "training/results-final-development/models.json",
    "training/results-final-development/final_evaluation.json", "training/results-final-development/holdout_predictions.csv",
    "submission/clinical-groups.json", "submission/final-protocol-freeze.json", "submission/demo-plan.md",
    "submission/ai-disclosure.md", "output/pdf/lumen-report.pdf",
    "submission/HARDENING-EVIDENCE-2026-10-11.md", "output/pdf/lumen-report-hardening-2026-10-11.pdf",
    "output/pdf/lumen-report-hardening-r2-2026-10-11.pdf",
    "research/runtime-hardening-r2-2026-10-11/browser-verification.json",
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, directory, timeout=180):
    started = time.perf_counter()
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    try:
        result = subprocess.run(command, cwd=directory, env=env, text=True, capture_output=True,
                                timeout=timeout, check=False)
        return {"command": command, "returncode": result.returncode,
                "seconds": round(time.perf_counter() - started, 3),
                "stdout": result.stdout[-14000:], "stderr": result.stderr[-14000:]}
    except (subprocess.TimeoutExpired, FileNotFoundError) as error:
        return {"command": command, "returncode": None, "seconds": round(time.perf_counter() - started, 3),
                "error": str(error)}


def verify_portable_models(folder):
    spec = importlib.util.spec_from_file_location("release_portable_predictor", folder / "inference.py")
    predictor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(predictor)
    models = json.loads((folder / "artifacts/availability-models.json").read_text())["models"]
    case_data = json.loads((folder / "artifacts/availability-cases.json").read_text())
    profiles = json.loads((folder / "artifacts/availability-profiles.json").read_text())["profiles"]
    split = json.loads((folder / "training/results/split.json").read_text())
    checked = 0
    max_error = 0.0
    for case in case_data["cases"]:
        for profile in profiles:
            raw = {feature: case["inputs"][feature] for feature in profile["feature_order"]}
            for target, saved in case["profile_predictions"][profile["id"]].items():
                model = models[saved["model_id"]]
                if case["row_index"] in model["training_row_indices"]:
                    raise AssertionError("Case appears in excluding model training rows")
                if set(model["training_row_indices"]) & set(split["holdout_row_indices"]):
                    raise AssertionError("Development model includes final holdout training rows")
                actual = predictor.predict_json(model, raw)
                error = abs(actual["probability"] - saved["probability"])
                max_error = max(max_error, error)
                if error >= 1e-12 or actual["predicted_label"] != saved["predicted_label"]:
                    raise AssertionError("Portable case prediction mismatch")
                reconstructed = actual["baseline_log_odds"] + sum(row["log_odds_contribution"] for row in actual["contributions"])
                if abs(reconstructed - actual["log_odds"]) >= 1e-10:
                    raise AssertionError("Explanation reconstruction mismatch")
                checked += 1
    final = json.loads((folder / "artifacts/final_models.json").read_text())
    for model in final["models"].values():
        if len(model["training_row_indices"]) != 242 or set(model["training_row_indices"]) != set(split["development_row_indices"]):
            raise AssertionError("Final development training identities mismatch")
    # Check final pipeline portability on one existing public development input;
    # this is runtime equivalence only, with no observed-outcome scoring.
    final_runtime_checked = 0
    for model in final["models"].values():
        result = predictor.predict_json(model, case_data["cases"][0]["inputs"])
        if not 0 <= result["probability"] <= 1:
            raise AssertionError("Invalid portable final-model probability")
        final_runtime_checked += 1
    return {"status": "passed", "case_profile_target_predictions_checked": checked,
            "maximum_case_probability_error": max_error, "final_models_runtime_checked_on_unscored_development_input": final_runtime_checked,
            "training_identity_exclusions_checked": True, "final_holdout_rescored": False}


def verify_frozen_artifacts(folder):
    freeze = json.loads((folder / "submission/final-protocol-freeze.json").read_text())
    checked = {}
    for name, expected in freeze["source_sha256"].items():
        actual = sha256(folder / "training" / name)
        if actual != expected:
            raise AssertionError(f"Frozen source hash differs: {name}")
        checked[name] = actual
    evaluation = json.loads((folder / "training/results-final-development/final_evaluation.json").read_text())
    if evaluation["n_holdout"] != 61 or evaluation["evaluation_status"] != "complete":
        raise AssertionError("Completed final evaluation missing or malformed")
    provenance = evaluation["provenance"]
    if sha256(folder / "submission/final-protocol-freeze.json") != provenance["protocol_freeze_sha256"]:
        raise AssertionError("Saved final result protocol hash differs")
    if sha256(folder / "training/results-final-development/models.json") != provenance["models_sha256"]:
        raise AssertionError("Saved final result model hash differs")
    if sha256(folder / "training/extention of Z-Alizadeh sani dataset.xlsx") != provenance["dataset_sha256"]:
        raise AssertionError("Saved final result dataset hash differs")
    if sha256(folder / "training/results-final-development/holdout_predictions.csv") != provenance["holdout_predictions_sha256"]:
        raise AssertionError("Saved final predictions hash differs")
    if sha256(folder / "artifacts/final_models.json") != sha256(folder / "training/results-final-development/models.json"):
        raise AssertionError("Runtime final models differ from saved evaluated models")
    if sha256(folder / "artifacts/final_evaluation.json") != sha256(folder / "training/results-final-development/final_evaluation.json"):
        raise AssertionError("Runtime final evidence differs from saved evaluation")
    return {"status": "passed", "n_frozen_source_files_checked": len(checked), "saved_final_evaluation_hashes_verified": True,
            "runtime_final_models_match_evaluated_models": True, "final_holdout_rescored": False}


SMOKE_CODE = r'''
import json, threading
from urllib.request import Request, urlopen
import server
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
base='http://127.0.0.1:'+str(http.server_port)
checks={}
try:
    for route in ['/', '/app.js','/style.css','/vendor/three.module.js','/vendor/three.core.js',
                  '/vendor/addons/controls/OrbitControls.js',
                  '/assets/anatomy.json','/assets/anatomy-provenance.json','/api/cases','/api/schema','/api/profiles','/api/final-evaluation']:
        with urlopen(base+route, timeout=5) as response:
            assert response.status==200
            assert len(response.read())>0
            checks[route]=200
    case=next(iter(server.CASES.values()))
    req=Request(base+'/api/predict-new',data=json.dumps({'inputs':case['inputs']}).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=5) as response:
        prediction=json.load(response)
        assert prediction['kind']=='unlabelled'
        assert len(prediction['predictions'])==4
        checks['/api/predict-new']=200
finally:
    http.shutdown();http.server_close();thread.join(timeout=3)
print(json.dumps({'status':'passed','routes':checks,'standard_library_runtime':True,'final_holdout_rescored':False}))
'''


def findings(folder):
    issues = []
    readme = (folder / "README.md").read_text()
    if "../research/" in readme or "has not been predicted or scored" in readme:
        issues.append({"severity": "documentation", "file": "README.md",
                       "finding": "README contains stale development/holdout claims or an outside-release research path."})
    availability = (folder / "training/experiment_availability.py").read_text()
    if 'ROOT.parents[2] / "coronary-evidence"' in availability:
        issues.append({"severity": "reproducibility", "file": "training/experiment_availability.py",
                       "finding": "Clinical grouping path depends on original workspace ancestry; resolve ROOT.parent/submission instead."})
    notices = (folder / "THIRD_PARTY_NOTICES.md").read_text()
    if "BodyParts3D" not in notices or "CC Attribution 4.0" not in notices:
        issues.append({"severity": "attribution", "file": "THIRD_PARTY_NOTICES.md", "finding": "Required anatomy attribution/license was not found."})
    external_runtime = []
    for name in ["server.py", "inference.py", "public/app.js", "public/index.html", "public/style.css"]:
        text = (folder / name).read_text()
        if "/Users/" in text or "../research" in text:
            external_runtime.append(name)
    if external_runtime:
        issues.append({"severity": "runtime", "files": external_runtime, "finding": "Runtime contains absolute/outside research references."})
    return issues


def relocated_group_source(folder):
    # Static inspection avoids importing/fitting training code solely to verify
    # its path. The exact relative expression was corrected during packaging.
    source = (folder / "training/experiment_availability.py").read_text()
    corrected = 'GROUP_PATH = ROOT.parent / "submission" / "clinical-groups.json"' in source
    grouping_exists = (folder / "submission/clinical-groups.json").is_file()
    return {"status": "passed" if corrected and grouping_exists else "failed",
            "corrected_workspace_ancestor_dependency": corrected,
            "group_source_exists_inside_extracted_release": grouping_exists,
            "non_frozen_availability_source_only": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, help="Existing release zip; otherwise build with scripts/build_release.py")
    parser.add_argument("--skip-shap", action="store_true", help="Record SHAP as skipped if unavailable")
    parser.add_argument("--output", type=Path, help="Write exact ZIP verification to a sidecar, avoiding a self-referential rebuild")
    parser.add_argument("--content-record", action="store_true", help="Write a stable in-package content record; exact ZIP hash belongs in a separate sidecar")
    args = parser.parse_args()
    evidence_path = args.output.resolve() if args.output else EVIDENCE_PATH
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = {"schema_version": 1, "verification": "Clean extracted source release", "final_holdout_rescored": False,
              "models_retrained": False, "checks": {}, "findings": []}
    if args.archive:
        archive = args.archive.resolve()
    else:
        build_result = run([sys.executable, str(ROOT / "scripts/build_release.py")], ROOT)
        result["checks"]["build_archive"] = build_result
        if build_result.get("returncode") != 0:
            result["status"] = "failed"
            evidence_path.write_text(json.dumps(result, indent=2))
            raise SystemExit("Release build failed; evidence saved")
        archive = ROOT / "dist/lumen-submission-source.zip"
    result["archive"] = str(archive)
    result["archive_sha256"] = sha256(archive)
    result["archive_bytes"] = archive.stat().st_size
    with tempfile.TemporaryDirectory(prefix="lumen-release-verification-") as temporary:
        destination = Path(temporary)
        with zipfile.ZipFile(archive) as zipped:
            for member in zipped.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise RuntimeError("Archive member escapes extraction directory")
            if zipped.testzip() is not None:
                raise RuntimeError("Archive CRC verification failed")
            zipped.extractall(destination)
        folder = destination / "lumen"
        manifest = json.loads((folder / "release-manifest.json").read_text())
        payload = {name: info for name, info in manifest["files"].items() if name != "submission/release-verification.json"}
        result["verified_content_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result["verified_content_files"] = len(payload)
        missing = [name for name in REQUIRED if not (folder / name).is_file()]
        mismatches = [name for name, metadata in manifest["files"].items()
                      if not (folder / name).is_file() or sha256(folder / name) != metadata["sha256"]]
        result["checks"]["manifest"] = {"status": "passed" if not mismatches else "failed",
                                          "files_checked": len(manifest["files"]), "mismatches": mismatches}
        result["checks"]["required_files"] = {"status": "passed" if not missing else "failed", "missing": missing}
        result["findings"] = findings(folder)
        result["checks"]["relocated_availability_source"] = relocated_group_source(folder)
        for name, verifier in [("frozen_artifacts", verify_frozen_artifacts), ("portable_models", verify_portable_models)]:
            try:
                result["checks"][name] = verifier(folder)
            except Exception as error:
                result["checks"][name] = {"status": "failed", "error": str(error)}
        npm = run(["npm", "ci", "--offline", "--ignore-scripts", "--no-audit", "--no-fund"], folder)
        result["checks"]["npm_ci_offline"] = npm
        result["checks"]["unit_tests"] = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], folder)
        if npm.get("returncode") == 0:
            result["checks"]["outcome_and_runtime_probe"] = run(["node", "--test", "tests/test_outcome_description.mjs", "tests/test_runtime_probe.mjs", "tests/test_case_transition.mjs", "tests/test_anatomy_frame.mjs"], folder)
            result["checks"]["frontend_comparison"] = run(["node", "tests/test_journey.mjs"], folder)
            result["checks"]["static_build"] = run([sys.executable, "scripts/build_static_demo.py"], folder)
            result["checks"]["static_runtime"] = run(["node", "--test", "tests/test_static_client.mjs"], folder)
            result["checks"]["cohort_runtime_and_filters"] = run(["node", "--test", "tests/test_cohort_static.mjs", "tests/test_cohort_filters.mjs"], folder)
            result["checks"]["http_runtime"] = run([sys.executable, "-c", SMOKE_CODE], folder)
        else:
            result["checks"]["http_runtime"] = {"status": "skipped", "reason": "npm dependency installation failed"}
        if args.skip_shap:
            result["checks"]["shap"] = {"status": "skipped", "reason": "Explicit skip request"}
        else:
            shap_result = run(["uv", "run", "--offline", "--python", "3.12", "--with-requirements",
                               "requirements-explanation.txt", "python", "verify_shap.py"], folder / "training")
            result["checks"]["shap"] = shap_result
            if shap_result.get("returncode") == 0:
                verification = json.loads((folder / "training/results-availability/shap-verification.json").read_text())
                result["checks"]["shap"]["summary"] = {name: verification[name] for name in
                    ["status", "n_case_profile_target_predictions", "maximum_grouped_contribution_error",
                     "maximum_baseline_error", "maximum_reconstruction_error", "holdout_scored", "models_changed"]}
        # Training checks above use only frozen development identities. Retained
        # final-evaluation files must remain byte-identical through verification.
        result["checks"]["final_evaluation_unchanged"] = {
            "status": "passed" if sha256(folder / "training/results-final-development/final_evaluation.json") ==
                       manifest["files"]["training/results-final-development/final_evaluation.json"]["sha256"] else "failed"}
    failed = [name for name, check in result["checks"].items()
              if check.get("status") == "failed" or ("returncode" in check and check["returncode"] != 0)]
    result["status"] = "passed" if not failed else "failed"
    result["failed_checks"] = failed
    result["runtime_seconds"] = round(time.perf_counter() - started, 3)
    evidence = dict(result)
    if args.content_record:
        for key in ["archive", "archive_sha256", "archive_bytes"]:
            evidence.pop(key, None)
        evidence["verification"] = "Clean release payload verification; in-package record"
        evidence["verification_scope"] = "All release payload files excluding submission/release-verification.json itself; verified_content_sha256 hashes the sorted manifest entries of that payload. Exact ZIP verification is the separate dist/release-verification.json sidecar."
        evidence["checks"] = dict(result["checks"])
        evidence["checks"]["manifest"] = dict(result["checks"]["manifest"])
        evidence["checks"]["manifest"]["files_checked"] = result["verified_content_files"]
    evidence_path.write_text(json.dumps(evidence, indent=2, allow_nan=False))
    print(json.dumps({key: result[key] for key in ["status", "failed_checks", "findings", "runtime_seconds", "archive_sha256"]}, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
