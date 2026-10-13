"""Verify every development-cohort explanation with the actual SHAP library.

No fitting, calibration search, new threshold, holdout inputs or outcome scoring.
Uses the complete exported development inputs and each model's entire original
training-fold Independent background. Original eight-case certificates remain
unchanged. Each attempt preserves a separate success/failure run receipt.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd
import shap

from verify_shap import encode_frame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inference import predict_json, sigmoid

ATOL = 1e-12
COHORT = ROOT / 'artifacts/cohort-audit.json'
OUTPUT = ROOT / 'training/cohort-audit-verification'
PUBLIC = ROOT / 'public/assets/cohort-audit-verification.json'
DEPENDENCIES = ['shap', 'numpy', 'pandas', 'openpyxl', 'scikit-learn', 'scipy',
                'joblib', 'threadpoolctl', 'numba', 'llvmlite', 'slicer']
PRESERVED = ['artifacts/final_models.json', 'artifacts/final_evaluation.json',
             'submission/final-protocol-freeze.json', 'artifacts/availability-cases.json',
             'training/results-availability/shap-verification.json',
             'public/assets/shap-verification.json']
SOURCES = ['artifacts/cohort-audit.json', 'artifacts/availability-models.json',
           'artifacts/availability-profiles.json', 'training/results/split.json',
           'training/results-availability/development_oof.csv', 'inference.py',
           'training/verify_shap.py', 'training/verify_cohort_audit.py',
           'training/requirements-explanation.txt', 'training/requirements-training.txt']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bindings(paths):
    return {name: {'sha256': sha(ROOT / name), 'bytes': (ROOT / name).stat().st_size}
            for name in paths}


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    started = time.perf_counter()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    run = OUTPUT / ('shap-' + timestamp)
    run.mkdir(parents=True)
    source_before, preserved_before = bindings(SOURCES), bindings(PRESERVED)
    receipt = {'schema_version': 1, 'created_utc': timestamp, 'status': 'running',
               'scope': 'All 242 public development records, existing five input profiles and four targets; no individual holdout inputs, labels or scores.',
               'method': 'Actual shap.LinearExplainer with complete model-specific training-fold shap.maskers.Independent background; identity link and grouped encoded features in log-odds units.',
               'tolerance': ATOL, 'source_bindings': source_before,
               'preserved_bindings': preserved_before, 'model_fitting': False,
               'threshold_search': False, 'final_holdout_rescored': False,
               'holdout_prediction_csv_opened': False, 'dependencies': {name: version(name) for name in DEPENDENCIES}}
    try:
        cohort = read_json(COHORT)
        frozen = read_json(ROOT / 'training/results/split.json')
        development_set, holdout_set = set(frozen['development_row_indices']), set(frozen['holdout_row_indices'])
        cases = cohort['cases']
        lookup = {case['row_index']: case for case in cases}
        assert len(cases) == len(lookup) == cohort['n_development'] == 242
        assert set(lookup) == development_set and not set(lookup) & holdout_set
        assert cohort['holdout_included'] is False
        assert bindings(list(cohort['source_bindings'])) == cohort['source_bindings']
        models = read_json(ROOT / 'artifacts/availability-models.json')['models']
        profiles = read_json(ROOT / 'artifacts/availability-profiles.json')['profiles']
        assert [p['id'] for p in profiles] == cohort['profile_order']
        assert len(models) == 100 and len(profiles) == 5
        assert cohort['target_order'] == ['CAD', 'LAD', 'LCX', 'RCA']
        dev = pd.DataFrame([case['inputs'] for case in cases], index=[case['row_index'] for case in cases])
        assert set(dev.columns) == set(profiles[-1]['feature_order']) and len(dev.columns) == 55
        assert not {'Cath', 'LAD', 'LCX', 'RCA', 'truth', 'target', 'targets'} & set(dev.columns)
        with (ROOT / 'training/results-availability/development_oof.csv').open(newline='') as handle:
            oof_rows = list(csv.DictReader(handle))
        oof = {int(row['row_index']): row for row in oof_rows}
        assert len(oof_rows) == len(oof) == 242 and set(oof) == development_set
        fold_members = {fold: [case['row_index'] for case in cases if case['fold'] == fold] for fold in range(5)}
        assert sum(map(len, fold_members.values())) == 242
        checks = []
        max_grouped = max_baseline = max_reconstruction = max_probability = max_reference_mean = max_oof_probability = 0.0
        encoded_value_checks = calibrated_checks = 0
        checked_models = []
        for profile in profiles:
            profile_id, features = profile['id'], profile['feature_order']
            for target in cohort['target_order']:
                for fold in range(5):
                    model_id = f'{target}-{profile_id}-outer-{fold}'
                    spec = models[model_id]
                    train_ids, validation_ids = spec['training_row_indices'], fold_members[fold]
                    assert len(train_ids) == len(set(train_ids))
                    assert set(train_ids) == development_set - set(validation_ids)
                    assert not set(train_ids) & holdout_set
                    assert spec['profile_id'] == profile_id and spec['feature_order'] == features
                    assert set(features) == {field['feature'] for field in spec['numeric'] + spec['categorical']}
                    background, coefficients, reference, groups, names = encode_frame(spec, dev.loc[train_ids, features])
                    reference_error = float(np.max(np.abs(background.mean(axis=0) - reference)))
                    max_reference_mean = max(max_reference_mean, reference_error)
                    assert reference_error < ATOL
                    masker = shap.maskers.Independent(background, max_samples=len(train_ids))
                    assert masker.data.shape == background.shape and np.array_equal(masker.data, background)
                    explainer = shap.LinearExplainer((coefficients, float(spec['intercept'])), masker,
                                                     link=shap.links.identity, feature_names=names)
                    assert explainer.feature_perturbation == 'interventional'
                    encoded, validation_coefficients, _, validation_groups, _ = encode_frame(spec, dev.loc[validation_ids, features])
                    assert np.array_equal(validation_coefficients, coefficients) and validation_groups == groups
                    explanation = explainer(encoded)
                    phi = np.asarray(explanation.values, dtype=float)
                    baselines = np.asarray(explanation.base_values, dtype=float).reshape(-1)
                    if baselines.size == 1:
                        baselines = np.repeat(baselines, len(validation_ids))
                    assert phi.shape == encoded.shape and baselines.shape == (len(validation_ids),)
                    for offset, row_id in enumerate(validation_ids):
                        case = lookup[row_id]
                        assert case['fold'] == int(oof[row_id]['fold']) == fold
                        assert case['case_id'] == f'UCI411-{row_id:03d}' and row_id not in train_ids
                        inputs = {name: case['inputs'][name] for name in features}
                        portable = predict_json(spec, inputs)
                        saved = case['profile_predictions'][profile_id][target]
                        assert saved['model_id'] == model_id
                        assert saved['operating_threshold'] == spec['operating_threshold'] == portable['operating_threshold']
                        assert saved['predicted_label'] == portable['predicted_label'] == int(saved['probability'] >= saved['operating_threshold'])
                        prefix = profile_id + '_' + target
                        assert saved['probability'] == float(oof[row_id][prefix + '_probability'])
                        assert saved['operating_threshold'] == float(oof[row_id][prefix + '_threshold'])
                        assert saved['predicted_label'] == int(oof[row_id][prefix + '_decision'])
                        assert case['truth'][target] == int(oof[row_id][target + '_truth'])
                        grouped_shap = {feature: float(phi[offset, indices].sum()) for feature, indices in groups.items()}
                        exported = {contribution['feature']: contribution['log_odds_contribution'] for contribution in portable['contributions']}
                        assert set(grouped_shap) == set(exported) == set(features)
                        grouped_error = max(abs(grouped_shap[feature] - exported[feature]) for feature in features)
                        baseline = float(baselines[offset])
                        baseline_error = abs(baseline - portable['baseline_log_odds'])
                        reconstructed = baseline + sum(grouped_shap.values())
                        reconstruction_error = abs(reconstructed - portable['log_odds'])
                        probability_error = abs(sigmoid(reconstructed) - portable['probability'])
                        oof_error = abs(portable['probability'] - saved['probability'])
                        assert all(error < ATOL for error in [grouped_error, baseline_error, reconstruction_error, probability_error, oof_error])
                        max_grouped = max(max_grouped, grouped_error)
                        max_baseline = max(max_baseline, baseline_error)
                        max_reconstruction = max(max_reconstruction, reconstruction_error)
                        max_probability = max(max_probability, probability_error)
                        max_oof_probability = max(max_oof_probability, oof_error)
                        encoded_value_checks += len(coefficients)
                        calibrated_checks += int(spec.get('calibration', {}).get('method') == 'sigmoid')
                        checks.append({'case_id': case['case_id'], 'row_index': row_id, 'fold': fold,
                                       'profile_id': profile_id, 'target': target, 'model_id': model_id,
                                       'background_n': len(train_ids), 'encoded_features': len(coefficients),
                                       'grouped_features': len(features), 'max_grouped_shap_error': grouped_error,
                                       'baseline_error': baseline_error, 'reconstruction_error': reconstruction_error,
                                       'probability_error': probability_error, 'oof_probability_error': oof_error})
                    checked_models.append(model_id)
                    print(f'{model_id}: {len(validation_ids)} explanations passed', flush=True)
        assert len(checks) == 4840 and len(checked_models) == len(set(checked_models)) == 100
        assert bindings(SOURCES) == source_before and bindings(PRESERVED) == preserved_before
        receipt.update(status='passed', n_development=242, n_profiles=5, n_targets=4,
                       n_models_verified=100, n_explanations_verified=4840,
                       n_encoded_feature_values_verified=encoded_value_checks,
                       n_sigmoid_calibrated_explanations=calibrated_checks,
                       max_grouped_shap_error=max_grouped, max_baseline_error=max_baseline,
                       max_reconstruction_error=max_reconstruction, max_probability_error=max_probability,
                       max_training_reference_mean_error=max_reference_mean,
                       max_oof_probability_error=max_oof_probability,
                       all_entire_outer_fold_training_exclusions_passed=True,
                       all_holdout_training_exclusions_passed=True,
                       source_and_preserved_hashes_unchanged=True,
                       cohort_sha256=sha(COHORT), checks=checks,
                       assumptions=['Independent masking breaks correlations among predictors.',
                                    'Encoded indicator SHAP values are summed to their original categorical feature; intermediate masks need not preserve valid one-hot states.',
                                    'Values are additive model associations in log-odds units, not probability percentage points or causal effects.',
                                    'Sigmoid of expected background log-odds is not mean background probability.',
                                    'Complete development audit uses recorded outcomes for descriptive filtering; it is not external or prospective validation.',
                                    'This certificate verifies Python decomposition against the specified actual-SHAP convention; browser parity is verified separately.'])
    except BaseException as error:
        receipt.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        receipt.update(runtime_seconds=time.perf_counter() - started, python=platform.python_version(),
                       platform=platform.platform(), machine=platform.machine())
        write_json(run / 'verification.json', receipt)
        if receipt['status'] == 'passed':
            public = {key: value for key, value in receipt.items() if key not in {'checks', 'preserved_bindings'}}
            public.update(full_verification_path=str((run / 'verification.json').relative_to(ROOT)),
                          full_verification_sha256=sha(run / 'verification.json'))
            write_json(PUBLIC, public)
        print(json.dumps({'status': receipt['status'], 'receipt': str(run / 'verification.json'),
                          **{key: receipt[key] for key in ['n_models_verified', 'n_explanations_verified',
                             'max_grouped_shap_error', 'max_reconstruction_error', 'runtime_seconds'] if key in receipt}}, indent=2))


if __name__ == '__main__':
    main()
