"""Local Python model inference, development evidence and static application.

Public source-data examples only; no patient-input persistence. Label fields are
never accepted as model inputs. Final-development models serve new inputs;
recorded case comparisons use models fitted without those cases.
"""
import argparse
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import time
from urllib.parse import unquote, urlparse, parse_qs

from inference import predict_json

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'
def read(name):
    return json.loads((ARTIFACTS / name).read_text())

MODELS = read('models.json')['models']
CASE_DATA = read('cases.json')
CASES = {c['case_id']: c for c in CASE_DATA['cases']}
SCHEMA = read('input_schema.json')
EVIDENCE = read('benchmark.json')
PROFILES = {'full': {'id':'full', 'label':'All measurement groups', 'n_features':55,
                     'feature_order':SCHEMA['feature_order'], 'numeric':SCHEMA['numeric'],
                     'categorical':SCHEMA['categorical']}}
AVAILABILITY = None
if (ARTIFACTS/'availability-profiles.json').exists():
    profile_data = read('availability-profiles.json')
    PROFILES = {p['id']:p for p in profile_data['profiles']}
    MODELS.update(read('availability-models.json')['models'])
    CASE_DATA = read('availability-cases.json')
    CASES = {c['case_id']:c for c in CASE_DATA['cases']}
    AVAILABILITY = read('availability-benchmark.json')
FINAL_MODELS = read('final_models.json')['models'] if (ARTIFACTS/'final_models.json').exists() else None
FINAL_EVALUATION = read('final_evaluation.json') if (ARTIFACTS/'final_evaluation.json').exists() else None
TARGETS = ['CAD', 'LAD', 'LCX', 'RCA']


def validate_audit_data(data, models, profiles, split):
    """Validate cohort membership and excluding-fold model routing, not outcomes.

    The artifact is deliberately outcomes-aware for browsing errors. Prediction
    inputs never include those labels; no final input/prediction CSV is read.
    """
    development = set(split['development_row_indices'])
    holdout = set(split['holdout_row_indices'])
    records = data['cases']
    if (len(development) != 242 or len(holdout) != 61 or development & holdout
            or data.get('holdout_included') is not False
            or data.get('n_development') != 242 or len(records) != 242):
        raise ValueError('Audit cohort must contain exactly the frozen development records')
    rows = [case['row_index'] for case in records]
    ids = [case['case_id'] for case in records]
    if len(set(rows)) != 242 or set(rows) != development or len(set(ids)) != 242:
        raise ValueError('Audit case identities do not match the complete development cohort')
    if data.get('profile_order') != list(profiles) or data.get('target_order') != TARGETS:
        raise ValueError('Audit profile/target routing mismatch')
    folds = {fold: {case['row_index'] for case in records if case['fold'] == fold} for fold in range(5)}
    if any(not rows for rows in folds.values()) or set().union(*folds.values()) != development:
        raise ValueError('Audit cohort must preserve all five outer validation folds')
    used_models = set()
    for case in records:
        if case['case_id'] != f"UCI411-{case['row_index']:03d}":
            raise ValueError('Audit public case identity mismatch')
        if set(case['inputs']) != set(profiles['full']['feature_order']):
            raise ValueError('Audit raw inputs must contain exactly the 55 predictors')
        if set(case['truth']) != set(TARGETS) or any(value not in (0, 1) for value in case['truth'].values()):
            raise ValueError('Audit recorded labels must contain exactly four binary outcomes')
        if set(case['profile_predictions']) != set(profiles):
            raise ValueError('Audit record lacks an input-profile prediction')
        for profile, predictions in case['profile_predictions'].items():
            if set(predictions) != set(TARGETS):
                raise ValueError('Audit record lacks a required target prediction')
            for target, saved in predictions.items():
                model_id = f"{target}-{profile}-outer-{case['fold']}"
                if saved['model_id'] != model_id:
                    raise ValueError('Audit prediction must route to the original excluding-fold model')
                model = models[model_id]
                training_rows = model['training_row_indices']
                if (len(set(training_rows)) != len(training_rows)
                        or set(training_rows) != development - folds[case['fold']]
                        or model['target'] != target or model['profile_id'] != profile
                        or model['feature_order'] != profiles[profile]['feature_order']):
                    raise ValueError('Audit model must exclude the entire validation fold and final holdout')
                probability, threshold = saved['probability'], saved['operating_threshold']
                if (not math.isfinite(probability) or not 0 <= probability <= 1
                        or threshold != model['operating_threshold']
                        or saved['predicted_label'] != int(probability >= threshold)):
                    raise ValueError('Audit saved prediction/operating rule mismatch')
                used_models.add(model_id)
    if len(used_models) != 100:
        raise ValueError('Audit cohort must route to all 100 existing profile/target/fold models')


AUDIT_DATA = read('cohort-audit.json') if (ARTIFACTS/'cohort-audit.json').exists() else None
if AUDIT_DATA:
    validate_audit_data(AUDIT_DATA, MODELS, PROFILES,
                        json.loads((ROOT/'training/results/split.json').read_text()))
AUDIT_CASES = {case['case_id']: case for case in AUDIT_DATA['cases']} if AUDIT_DATA else {}


def audit_case_for_profile(case_id, profile='full'):
    """Compute exact explanations lazily, independently of recorded outcomes."""
    case, specification = AUDIT_CASES[case_id], PROFILES[profile]
    inputs = {name: case['inputs'][name] for name in specification['feature_order']}
    predictions = {target: predict_json(MODELS[saved['model_id']], inputs)
                   for target, saved in case['profile_predictions'][profile].items()}
    return {'case_id':case_id, 'row_index':case['row_index'], 'fold':case['fold'],
            'profile':profile, 'kind':'development', 'origin':'audit',
            'outcome_aware_selection':True, 'inputs':inputs, 'predictions':predictions}


def audit_case_journey(case_id):
    case = AUDIT_CASES[case_id]
    snapshots = []
    for profile, specification in PROFILES.items():
        projected = audit_case_for_profile(case_id, profile)
        snapshots.append({'profile_id':profile, 'label':specification['label'],
                          'n_features':specification['n_features'],
                          'row_index':case['row_index'], 'fold':case['fold'],
                          'inputs':projected['inputs'], 'predictions':projected['predictions']})
    return {'case_id':case_id, 'row_index':case['row_index'], 'fold':case['fold'],
            'kind':'development', 'origin':'audit', 'outcome_aware_selection':True,
            'original_inputs_only':True, 'profile_order':list(PROFILES), 'snapshots':snapshots,
            'interpretation':'Outcome-aware development audit: every profile uses existing models that excluded '
                             'this entire outer validation fold. Recorded outcomes are not prediction inputs; '
                             'profile agreement is not clinical confidence and profile differences are not causal effects.'}


def predict_audit_case(case_id, inputs, profile='full'):
    case = AUDIT_CASES[case_id]
    # predict_json enforces exact feature keys, including target-field rejection.
    start = time.perf_counter()
    results = {target:predict_json(MODELS[saved['model_id']], inputs)
               for target, saved in case['profile_predictions'][profile].items()}
    changed = [name for name, value in inputs.items() if value != case['inputs'][name]]
    return {'case_id':case_id, 'profile':profile, 'kind':'development', 'origin':'audit',
            'outcome_aware_selection':True, 'predictions':results, 'changed_features':changed,
            **diagnostics(inputs,results,profile), 'elapsed_ms':(time.perf_counter()-start)*1000,
            'interpretation':'Edited model sensitivity; original labels do not validate modified inputs' if changed
                             else 'Development audit case predicted by models that excluded this entire validation fold'}


def profile_schema(profile='full'):
    chosen = PROFILES[profile]
    return {**SCHEMA, 'profile':profile, 'feature_order':chosen['feature_order'],
            'numeric':chosen['numeric'], 'categorical':chosen['categorical']}


def case_for_profile(case_id, profile='full'):
    case = CASES[case_id]
    predictions = case.get('profile_predictions',{}).get(profile)
    if predictions is None:
        if profile != 'full': raise ValueError('Profile predictions unavailable')
        predictions = case['predictions']
    return {'case_id':case_id,'row_index':case['row_index'],'fold':case['fold'],
            'profile':profile,'kind':'development',
            'inputs':{name:case['inputs'][name] for name in PROFILES[profile]['feature_order']},
            'predictions':predictions}


def case_journey(case_id):
    """Original development record across separately fitted input profiles.

    Uses saved excluding-fold predictions only. Edited or new-input requests do
    not enter this route, and recorded target fields are never returned.
    """
    case = CASES[case_id]
    snapshots = []
    for profile_id, specification in PROFILES.items():
        projected = case_for_profile(case_id, profile_id)
        snapshots.append({'profile_id':profile_id, 'label':specification['label'],
                          'n_features':specification['n_features'],
                          'row_index':projected['row_index'], 'fold':projected['fold'],
                          'inputs':projected['inputs'], 'predictions':projected['predictions']})
    return {'case_id':case_id, 'row_index':case['row_index'], 'fold':case['fold'],
            'kind':'development', 'original_inputs_only':True,
            'profile_order':list(PROFILES), 'snapshots':snapshots,
            'interpretation':'The same recorded development case across separately refitted input-profile models that excluded this record. '
                             'Differences combine available inputs, fitted model, calibration and research threshold changes; '
                             'they do not establish causal effects, clinical utility or confidence.'}


def diagnostics(inputs, predictions, profile):
    schema = profile_schema(profile)
    outside = [f['feature'] for f in schema['numeric'] if inputs[f['feature']] is not None
               and not f['min_development'] <= float(inputs[f['feature']]) <= f['max_development']]
    return {'outside_development_range':outside}


def predict_case(case_id, inputs, profile='full'):
    case = case_for_profile(case_id, profile)
    start = time.perf_counter()
    results = {target:predict_json(MODELS[p['model_id']], inputs)
               for target,p in case['predictions'].items()}
    changed = [name for name,value in inputs.items() if value != case['inputs'][name]]
    return {'case_id':case_id,'profile':profile,'predictions':results,'changed_features':changed,
            **diagnostics(inputs,results,profile),'elapsed_ms':(time.perf_counter()-start)*1000,
            'interpretation':'Edited model sensitivity; original labels do not validate modified inputs' if changed
                             else 'Development case predicted by models that excluded this record'}


def predict_new(inputs):
    if not FINAL_MODELS: raise ValueError('Final-development models are not yet frozen')
    start = time.perf_counter()
    results = {t:predict_json(FINAL_MODELS[t+'-final-development'],inputs) for t in ['CAD','LAD','LCX','RCA']}
    return {'case_id':'new-input','kind':'unlabelled','profile':'full','predictions':results,
            'changed_features':[],'elapsed_ms':(time.perf_counter()-start)*1000,
            **diagnostics(inputs,results,'full'),
            'interpretation':'Unlabelled inputs; no recorded outcome for comparison'}


def evidence_for_profile(profile='full'):
    if not AVAILABILITY: return EVIDENCE
    chosen = AVAILABILITY['profiles'][profile]
    return {**EVIDENCE, 'targets':chosen['targets'], 'availability_profile':profile,
            'protocol':{**EVIDENCE['protocol'],'n_input_features':PROFILES[profile]['n_features']}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def reply(self, data, status=200):
        encoded=json.dumps(data,allow_nan=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',len(encoded)); self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed=urlparse(self.path); path=unquote(parsed.path)
        profile=parse_qs(parsed.query).get('profile',['full'])[0]
        if path.startswith('/api/'):
            try:
                if profile not in PROFILES: raise ValueError('Unknown input profile')
                if path=='/api/audit':
                    if AUDIT_DATA is None: raise ValueError('Development audit artifact is unavailable')
                    self.reply(AUDIT_DATA); return
                if path.startswith('/api/audit/cases/'):
                    self.reply(audit_case_for_profile(path[len('/api/audit/cases/'):],profile)); return
                if path.startswith('/api/audit/journey/'):
                    self.reply(audit_case_journey(path[len('/api/audit/journey/'):])) ; return
                if path.startswith('/api/audit/labels/'):
                    self.reply({'truth':AUDIT_CASES[path[len('/api/audit/labels/'):]]['truth']}); return
                if path=='/api/profiles': self.reply({'profiles':list(PROFILES.values()),'availability_evidence':AVAILABILITY}); return
                if path=='/api/cases':
                    self.reply({'selection':CASE_DATA['selection'], 'new_input_ready':bool(FINAL_MODELS),
                                'cases':[{'case_id':c['case_id'],'fold':c['fold']} for c in CASES.values()]}); return
                if path=='/api/schema': self.reply(profile_schema(profile)); return
                if path=='/api/evidence': self.reply(evidence_for_profile(profile)); return
                if path=='/api/final-evaluation': self.reply(FINAL_EVALUATION or {'available':False}); return
                if path.startswith('/api/journey/'):
                    self.reply(case_journey(path[len('/api/journey/'):])) ; return
                if path.startswith('/api/cases/'):
                    self.reply(case_for_profile(path[len('/api/cases/'):],profile)); return
                if path.startswith('/api/labels/'):
                    self.reply({'truth':CASES[path[len('/api/labels/'):]]['truth']}); return
                self.reply({'error':'Not found'},404)
            except (ValueError,KeyError,TypeError) as error:
                self.reply({'error':str(error)},400)
            return
        if path.startswith('/vendor/addons/'):
            base=ROOT/'node_modules/three/examples/jsm'; relative=path[len('/vendor/addons/'):]
        elif path.startswith('/vendor/'):
            base=ROOT/'node_modules/three/build'; relative=path[len('/vendor/'):]
        else:
            base=ROOT/'public'; relative=path.lstrip('/') or 'index.html'
        target=(base/relative).resolve()
        if not target.is_relative_to(base.resolve()) or not target.is_file():
            self.reply({'error':'Not found'},404); return
        data=target.read_bytes()
        self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(target)[0] or 'application/octet-stream')
        self.send_header('Content-Length',len(data)); self.send_header('Cache-Control','no-cache'); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        if self.path not in {'/api/predict','/api/predict-new','/api/audit/predict'}: self.reply({'error':'Not found'},404); return
        if self.headers.get('Origin') and self.headers['Origin'] != 'http://'+self.headers.get('Host',''):
            self.reply({'error':'Cross-origin requests are disabled'},403); return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=65536: raise ValueError('Invalid request size')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict) or not isinstance(body.get('inputs'),dict): raise ValueError('A complete inputs object is required')
            if self.path=='/api/predict-new':
                if set(body)!={'inputs'}: raise ValueError('Expected only inputs')
                result=predict_new(body['inputs'])
            else:
                if set(body) not in [{'case_id','inputs'},{'case_id','inputs','profile'}]: raise ValueError('Expected case_id, inputs and optional profile')
                predict = predict_audit_case if self.path=='/api/audit/predict' else predict_case
                result=predict(body['case_id'],body['inputs'],body.get('profile','full'))
            self.reply(result)
        except (ValueError,KeyError,TypeError,ArithmeticError) as error:
            self.reply({'error':str(error)},400)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8766); args=parser.parse_args()
    print(f'Lumen: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
