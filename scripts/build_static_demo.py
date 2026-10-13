"""Build the optional static browser demo without training or final rescoring.

The generated site includes portable model coefficients, eight original public
development examples, a separate outcomes-aware complete development audit,
and aggregate evaluation evidence. It contains no final
holdout input records. Typed form inputs are evaluated in browser memory only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import validate_audit_data


def read(name):
    return json.loads((ROOT / 'artifacts' / name).read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')


def build(output=None):
    output = Path(output).resolve() if output else ROOT / 'dist/site'
    if output in {ROOT, ROOT / 'public', ROOT / 'dist'} or not output.is_relative_to(ROOT / 'dist'):
        raise ValueError('Static output must be a child of this project\'s dist directory')
    three = ROOT / 'node_modules/three'
    if not (three / 'build/three.module.js').is_file():
        raise FileNotFoundError('Run npm ci to install the pinned Three.js runtime before building')
    source_models = read('models.json')['models']
    source_models.update(read('availability-models.json')['models'])
    cases = read('availability-cases.json')
    profiles = read('availability-profiles.json')['profiles']
    final = read('final_models.json')['models']
    split = json.loads((ROOT / 'training/results/split.json').read_text())
    development = set(split['development_row_indices'])
    holdout = set(split['holdout_row_indices'])
    if len(development) != 242 or len(holdout) != 61 or development & holdout:
        raise ValueError('Frozen split identity mismatch')
    cohort = read('cohort-audit.json')
    validate_audit_data(cohort, source_models, {profile['id']:profile for profile in profiles}, split)
    cohort_raw = (ROOT / 'artifacts/cohort-audit.json').read_bytes()
    cohort_sha256 = hashlib.sha256(cohort_raw).hexdigest()
    certificate_path = ROOT / 'public/assets/cohort-audit-verification.json'
    certificate = json.loads(certificate_path.read_text())
    if (certificate.get('status') != 'passed' or certificate.get('cohort_sha256') != cohort_sha256
            or certificate.get('n_development') != 242 or certificate.get('n_profiles') != 5
            or certificate.get('n_models_verified') != 100
            or certificate.get('n_explanations_verified') != 4840):
        raise ValueError('Full-cohort SHAP verification must pass for this exact development artifact')
    for relative, binding in certificate['source_bindings'].items():
        source = (ROOT / relative).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError('SHAP verification source binding is missing or outside this project')
        raw = source.read_bytes()
        if len(raw) != binding['bytes'] or hashlib.sha256(raw).hexdigest() != binding['sha256']:
            raise ValueError(f'SHAP verification source changed: {relative}')
    full_verification = (ROOT / certificate['full_verification_path']).resolve()
    if (not full_verification.is_relative_to(ROOT) or not full_verification.is_file()
            or hashlib.sha256(full_verification.read_bytes()).hexdigest() != certificate['full_verification_sha256']):
        raise ValueError('Full-cohort SHAP verification receipt is missing or changed')
    if len(cases['cases']) != 8 or cases['holdout_included']:
        raise ValueError('Static demonstration accepts exactly the existing development case roster')
    for case in cases['cases']:
        if case['row_index'] not in development or case['row_index'] in holdout:
            raise ValueError('Only original development examples may enter the static bundle')
        for predictions in case['profile_predictions'].values():
            for prediction in predictions.values():
                model = source_models[prediction['model_id']]
                if case['row_index'] in model['training_row_indices'] or set(model['training_row_indices']) & holdout:
                    raise ValueError('Static case model must exclude the example and frozen holdout')
    for model in final.values():
        if set(model['training_row_indices']) != development or len(model['training_row_indices']) != 242:
            raise ValueError('Static new-input mode requires the frozen full-development models')
    aggregate = read('final_evaluation.json')
    # Aggregate final metrics/provenance only; never copy per-row final outcomes,
    # inputs, prediction CSV or frozen holdout row identities into the site.
    aggregate = {key: value for key, value in aggregate.items() if key != 'holdout_row_indices'}
    bundle = {'schema_version': 1, 'runtime': 'static', 'schema': read('input_schema.json'),
              'cases': cases, 'models': source_models, 'profiles': profiles,
              'cohort_audit': cohort,
              'evidence': read('benchmark.json'), 'availability': read('availability-benchmark.json'),
              'final_models': final, 'final_evaluation': aggregate,
              'privacy': 'Entered values are evaluated in browser memory; this client does not store or transmit form inputs.',
              'public_data_note': 'The source bundle contains eight public development examples plus all 242 development audit records and their recorded labels. Audit selection is explicitly outcome-aware; reveal is educational, not a secrecy boundary.'}
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / 'public', output)
    (output / 'data').mkdir()
    write_json(output / 'data/lumen-data.json', bundle)
    full = bundle['availability']['profiles']['full']
    downloadable_evidence = {**bundle['evidence'], 'targets': full['targets'], 'availability_profile': 'full'}
    write_json(output / 'data/evidence.json', downloadable_evidence)
    write_json(output / 'data/final-evaluation.json', aggregate)
    (output / 'vendor').mkdir()
    for filename in ['three.module.js', 'three.core.js']:
        shutil.copyfile(three / 'build' / filename, output / 'vendor' / filename)
    (output / 'vendor/addons/controls').mkdir(parents=True)
    shutil.copyfile(three / 'examples/jsm/controls/OrbitControls.js',
                    output / 'vendor/addons/controls/OrbitControls.js')
    shutil.copyfile(three / 'LICENSE', output / 'vendor/THREE-LICENSE.txt')
    for name in ['THIRD_PARTY_NOTICES.md', 'LICENSE']:
        shutil.copyfile(ROOT / name, output / name)
    html = (output / 'index.html').read_text()
    html = html.replace('<head>', '<head><meta name="lumen-runtime" content="static">', 1)
    html = re.sub(r'<script>if\(location\.protocol===\x27file:\x27\).*?</script>', '', html)
    html = html.replace('href="/api/evidence"', 'href="./data/evidence.json"')
    html = html.replace('href="/"', 'href="./"')
    html = re.sub(r'(["\x27])/(style\.css|app\.js|assets/|vendor/)', r'\1./\2', html)
    (output / 'index.html').write_text(html)
    (output / '.nojekyll').write_text('')
    manifest = {'schema_version': 1, 'runtime': 'static', 'final_holdout_inputs_included': False,
                'models_retrained': False, 'final_holdout_rescored': False,
                'n_public_development_cases': 8, 'n_profiles': len(profiles), 'files': {}}
    manifest.update({'n_audit_development_cases':242, 'n_audit_profile_predictions':4840,
                     'audit_outcome_aware_selection':True, 'cohort_audit_sha256':cohort_sha256,
                     'audit_explanation_verification':{
                         'url':'./assets/cohort-audit-verification.json',
                         'sha256':hashlib.sha256(certificate_path.read_bytes()).hexdigest(),
                         'n_models_verified':100, 'n_explanations_verified':4840,
                         'scope':'All existing model/profile/target explanations on the complete development cohort; no final holdout inputs or rescoring.'}})
    for path in sorted(output.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            manifest['files'][str(path.relative_to(output))] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    write_json(output / 'static-manifest.json', manifest)
    print(json.dumps({'site': str(output), 'files': len(manifest['files']),
                      'bytes': sum(row['bytes'] for row in manifest['files'].values()),
                      'n_public_development_cases': 8, 'n_audit_development_cases':242,
                      'n_audit_profile_predictions':4840, 'final_holdout_inputs_included': False}, indent=2))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    build(parser.parse_args().output)
