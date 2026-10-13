"""Export the complete development cohort, without fitting or holdout scoring.

Uses only Python's standard library. Worksheet values are decoded only for the
55 predictors of the exact frozen development rows; outcome cells are not read.
Recorded development outcomes and compact predictions come from the existing
availability OOF CSV. Detailed contributions are computed on demand at runtime.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import posixpath
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ['CAD', 'LAD', 'LCX', 'RCA']
FORBIDDEN = {'CAD', 'Cath', 'LAD', 'LCX', 'RCA', 'truth', 'target', 'targets'}
OUT = ROOT / 'artifacts/cohort-audit.json'
RECEIPTS = ROOT / 'training/cohort-audit-verification'
SOURCES = [
    'training/extention of Z-Alizadeh sani dataset.xlsx',
    'training/results/split.json',
    'training/results-availability/development_oof.csv',
    'artifacts/availability-models.json',
    'artifacts/availability-profiles.json',
    'artifacts/availability-cases.json',
    'inference.py',
    'scripts/build_cohort_audit.py',
]
PRESERVED = [
    'artifacts/final_models.json', 'artifacts/final_evaluation.json',
    'submission/final-protocol-freeze.json',
    'artifacts/availability-cases.json',
    'training/results-availability/shap-verification.json',
    'public/assets/shap-verification.json',
]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bindings(paths):
    return {name: {'sha256': sha(ROOT / name), 'bytes': (ROOT / name).stat().st_size}
            for name in paths}


def read_json(name):
    return json.loads((ROOT / name).read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')
    temporary.replace(path)


def column_index(cell_address):
    value = 0
    for letter in cell_address:
        if not letter.isalpha():
            break
        value = value * 26 + ord(letter.upper()) - ord('A') + 1
    return value - 1


def cell_value(cell, strings):
    kind = cell.get('t', 'n')
    if kind == 'inlineStr':
        return ''.join(part.text or '' for part in cell.findall('.//s:t', NS))
    part = cell.find('s:v', NS)
    if part is None or part.text is None:
        return None
    value = part.text
    if kind == 's':
        return strings[int(value)]
    if kind in {'str', 'e'}:
        if kind == 'e':
            raise ValueError('Spreadsheet error cell is not a model input')
        return value
    if kind == 'b':
        return bool(int(value))
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Nonfinite spreadsheet input')
    return int(number) if number.is_integer() else number


def development_inputs(workbook, development_ids, feature_order, numeric_features):
    """Skip non-development rows and forbidden columns before decoding cells."""
    selected_excel_rows = {row_id + 2: row_id for row_id in development_ids}
    selected = {}
    with zipfile.ZipFile(workbook) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [''.join(part.text or '' for part in item.findall('.//s:t', NS))
                       for item in root.findall('s:si', NS)]
        workbook_root = ET.fromstring(archive.read('xl/workbook.xml'))
        first_sheet = workbook_root.find('s:sheets/s:sheet', NS)
        if first_sheet is None:
            raise ValueError('No workbook worksheet')
        relationship = first_sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(item.get('Target') for item in relationships if item.get('Id') == relationship)
        sheet_name = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        headers, feature_columns = {}, {}
        with archive.open(sheet_name) as sheet:
            for event, element in ET.iterparse(sheet, events=['end']):
                if element.tag != '{' + NS['s'] + '}row':
                    continue
                excel_row = int(element.get('r'))
                if excel_row == 1:
                    headers = {column_index(cell.get('r')): str(cell_value(cell, strings)).strip()
                               for cell in element.findall('s:c', NS)}
                    if len(headers) != len(set(headers.values())):
                        raise ValueError('Duplicate worksheet column name')
                    if not set(feature_order) <= set(headers.values()):
                        raise ValueError('Worksheet predictor headers do not match the frozen schema')
                    feature_columns = {index: name for index, name in headers.items() if name in feature_order}
                    if len(feature_columns) != 55 or FORBIDDEN.intersection(feature_columns.values()):
                        raise ValueError('Exact predictor-only workbook contract failed')
                elif excel_row in selected_excel_rows:
                    if not feature_columns:
                        raise ValueError('Worksheet has no header before development records')
                    cells = {column_index(cell.get('r')): cell for cell in element.findall('s:c', NS)}
                    row = {}
                    for column, name in feature_columns.items():
                        value = cell_value(cells[column], strings) if column in cells else None
                        if value is not None:
                            if name in numeric_features:
                                if isinstance(value, bool) or not isinstance(value, (int, float)):
                                    raise ValueError(f'Unexpected numeric cell type: {name}')
                            else:
                                value = str(value).strip()
                        row[name] = value
                    selected[selected_excel_rows[excel_row]] = {name: row[name] for name in feature_order}
                element.clear()
    if set(selected) != set(development_ids) or len(selected) != 242:
        raise ValueError('Worksheet development identities are incomplete or duplicated')
    return selected


def main():
    started = time.perf_counter()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    receipt_path = RECEIPTS / ('export-' + timestamp + '.json')
    source_before = bindings(SOURCES)
    preserved_before = bindings(PRESERVED)
    receipt = {'created_utc': timestamp, 'phase': 'development-cohort-export', 'status': 'running',
               'source_bindings': source_before, 'preserved_bindings': preserved_before,
               'model_fitting': False, 'final_holdout_rescored': False,
               'holdout_prediction_csv_opened': False, 'worksheet_outcome_cells_decoded': False}
    try:
        frozen = read_json('training/results/split.json')
        development = frozen['development_row_indices']
        development_set, holdout_set = set(development), set(frozen['holdout_row_indices'])
        assert len(development) == len(development_set) == 242
        assert len(holdout_set) == 61 and not development_set & holdout_set
        assert source_before[SOURCES[0]]['sha256'] == frozen['dataset_sha256']
        profiles = read_json('artifacts/availability-profiles.json')['profiles']
        profile_order = [p['id'] for p in profiles]
        assert profile_order == ['history', 'history_exam', 'history_exam_ecg', 'history_exam_ecg_lab', 'full']
        assert [p['n_features'] for p in profiles] == [17, 31, 38, 52, 55]
        feature_order = profiles[-1]['feature_order']
        assert len(feature_order) == len(set(feature_order)) == 55 and not FORBIDDEN & set(feature_order)
        raw_inputs = development_inputs(ROOT / SOURCES[0], development, feature_order,
                                        {field['feature'] for field in profiles[-1]['numeric']})
        with (ROOT / SOURCES[2]).open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        by_id = {int(row['row_index']): row for row in rows}
        assert len(rows) == len(by_id) == 242 and set(by_id) == development_set
        folds = {fold: {row_id for row_id, row in by_id.items() if int(row['fold']) == fold} for fold in range(5)}
        assert sum(map(len, folds.values())) == 242 and all(len(rows) in {48, 49} for rows in folds.values())
        models = read_json('artifacts/availability-models.json')['models']
        assert len(models) == 100
        module_spec = importlib.util.spec_from_file_location('lumen_cohort_portable_inference', ROOT / 'inference.py')
        inference = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(inference)
        verified_models = set()
        max_probability_error = 0.0
        cases = []
        for row_id in development:
            row, inputs = by_id[row_id], raw_inputs[row_id]
            fold = int(row['fold'])
            truth = {target: int(row[target + '_truth']) for target in TARGETS}
            assert set(truth.values()) <= {0, 1}
            profile_predictions = {}
            for profile in profiles:
                profile_id, features = profile['id'], profile['feature_order']
                projected = {name: inputs[name] for name in features}
                assert len(features) == profile['n_features'] and not FORBIDDEN & set(features)
                target_predictions = {}
                for target in TARGETS:
                    model_id = f'{target}-{profile_id}-outer-{fold}'
                    model = models[model_id]
                    if model_id not in verified_models:
                        training_ids = model['training_row_indices']
                        assert len(training_ids) == len(set(training_ids))
                        assert set(training_ids) == development_set - folds[fold]
                        assert not set(training_ids) & holdout_set
                        assert model['profile_id'] == profile_id and model['feature_order'] == features
                        assert set(projected) == {field['feature'] for field in model['numeric'] + model['categorical']}
                        verified_models.add(model_id)
                    prefix = profile_id + '_' + target
                    probability = float(row[prefix + '_probability'])
                    threshold = float(row[prefix + '_threshold'])
                    flag = int(row[prefix + '_decision'])
                    assert math.isfinite(probability) and 0 <= probability <= 1
                    assert math.isfinite(threshold) and 0 <= threshold <= 1
                    assert flag == int(probability >= threshold)
                    prediction = inference.predict_json(model, projected)
                    error = abs(prediction['probability'] - probability)
                    max_probability_error = max(max_probability_error, error)
                    assert error < 1e-12
                    assert prediction['operating_threshold'] == threshold and prediction['predicted_label'] == flag
                    target_predictions[target] = {'probability': probability, 'operating_threshold': threshold,
                                                   'predicted_label': flag, 'model_id': model_id}
                profile_predictions[profile_id] = target_predictions
            cases.append({'case_id': f'UCI411-{row_id:03d}', 'row_index': row_id, 'fold': fold,
                          'inputs': inputs, 'truth': truth, 'profile_predictions': profile_predictions})
        assert len(verified_models) == 100
        original = read_json('artifacts/availability-cases.json')['cases']
        new_lookup = {record['case_id']: record for record in cases}
        for record in original:
            projected = new_lookup[record['case_id']]
            assert all(projected[key] == record[key] for key in ['case_id', 'row_index', 'fold', 'inputs', 'truth'])
            for profile_id in profile_order:
                for target in TARGETS:
                    old, new = record['profile_predictions'][profile_id][target], projected['profile_predictions'][profile_id][target]
                    assert abs(old['probability'] - new['probability']) < 1e-12
                    assert all(old[key] == new[key] for key in ['operating_threshold', 'predicted_label', 'model_id'])
        assert bindings(SOURCES) == source_before and bindings(PRESERVED) == preserved_before
        payload = {'schema_version': 1, 'n_development': 242, 'n_profiles': 5,
                   'profile_order': profile_order, 'target_order': TARGETS,
                   'selection': 'Complete frozen 242-record development set; not selected for model success. Outcome-aware audit filters use recorded development labels.',
                   'interpretation': 'Post-development descriptive audit of existing out-of-fold predictions. Each model excludes the explained record and its entire outer fold. Agreement is not confidence; profile differences are not causal effects or clinical test utility.',
                   'row_indexing': 'Zero-based original workbook data row excluding the header; Excel row equals row_index + 2.',
                   'source_bindings': source_before, 'holdout_included': False, 'cases': cases}
        write_json(OUT, payload)
        assert OUT.stat().st_size < 2_000_000
        receipt.update(status='passed', n_development=242, n_models=100, n_predictions_verified=4840,
                       max_probability_error=max_probability_error, tolerance=1e-12,
                       all_entire_outer_fold_training_exclusions_passed=True,
                       all_holdout_training_exclusions_passed=True,
                       original_eight_cases_inputs_labels_folds_and_predictions_unchanged=True,
                       source_and_preserved_hashes_unchanged=True,
                       cohort_sha256=sha(OUT), cohort_bytes=OUT.stat().st_size)
    except BaseException as error:
        receipt.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        receipt.update(runtime_seconds=time.perf_counter() - started, python=platform.python_version(),
                       platform=platform.platform(), machine=platform.machine())
        write_json(receipt_path, receipt)
        print(json.dumps({'receipt': str(receipt_path), **{key: receipt[key] for key in
                         ['status', 'runtime_seconds', 'cohort_bytes', 'cohort_sha256', 'max_probability_error'] if key in receipt}}, indent=2))


if __name__ == '__main__':
    main()
