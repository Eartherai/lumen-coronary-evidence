"""Development audit contract tests; never open or rescore final predictions."""
import copy
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


def assert_no_truth(test, value):
    if isinstance(value, dict):
        test.assertFalse({'truth', 'recorded_labels', 'Cath'} & set(value))
        for child in value.values():
            assert_no_truth(test, child)
    elif isinstance(value, list):
        for child in value:
            assert_no_truth(test, child)


class CohortRuntimeTests(unittest.TestCase):
    def test_all_compact_probabilities_and_exact_reconstruction(self):
        checked = 0
        for case in server.AUDIT_CASES.values():
            for profile in server.PROFILES:
                result = server.audit_case_for_profile(case['case_id'], profile)
                self.assertNotIn('truth', result)
                self.assertFalse(set(server.TARGETS) & set(result['inputs']))
                for target, prediction in result['predictions'].items():
                    saved = case['profile_predictions'][profile][target]
                    self.assertLessEqual(abs(prediction['probability'] - saved['probability']), 1e-12)
                    self.assertEqual(prediction['model_id'], saved['model_id'])
                    self.assertEqual(prediction['operating_threshold'], saved['operating_threshold'])
                    self.assertEqual(prediction['predicted_label'], saved['predicted_label'])
                    self.assertLessEqual(abs(prediction['baseline_log_odds'] +
                        sum(c['log_odds_contribution'] for c in prediction['contributions']) - prediction['log_odds']), 1e-12)
                    checked += 1
        self.assertEqual(checked, 4840)

    def test_every_model_excludes_its_whole_outer_fold(self):
        split = json.loads((ROOT/'training/results/split.json').read_text())
        server.validate_audit_data(server.AUDIT_DATA, server.MODELS, server.PROFILES, split)
        used = {p['model_id'] for case in server.AUDIT_CASES.values()
                for predictions in case['profile_predictions'].values() for p in predictions.values()}
        self.assertEqual(len(used), 100)
        for model_id in used:
            fold = int(model_id.rsplit('-', 1)[1])
            excluded = {case['row_index'] for case in server.AUDIT_CASES.values() if case['fold'] == fold}
            self.assertEqual(set(server.MODELS[model_id]['training_row_indices']),
                             set(split['development_row_indices']) - excluded)

    def test_validator_rejects_duplicate_row_and_contaminated_fold(self):
        split = json.loads((ROOT/'training/results/split.json').read_text())
        corrupt = copy.deepcopy(server.AUDIT_DATA)
        corrupt['cases'][0] = copy.deepcopy(corrupt['cases'][1])
        with self.assertRaises(ValueError):
            server.validate_audit_data(corrupt, server.MODELS, server.PROFILES, split)
        case = next(iter(server.AUDIT_CASES.values()))
        model_id = case['profile_predictions']['full']['LAD']['model_id']
        models = dict(server.MODELS)
        models[model_id] = {**models[model_id], 'training_row_indices':
            [*models[model_id]['training_row_indices'], case['row_index']]}
        with self.assertRaises(ValueError):
            server.validate_audit_data(server.AUDIT_DATA, models, server.PROFILES, split)

    def test_labels_cannot_change_predictions(self):
        case = next(iter(server.AUDIT_CASES.values()))
        original = case['truth']
        before = server.audit_case_for_profile(case['case_id'])
        try:
            case['truth'] = {target:1-value for target, value in original.items()}
            after = server.audit_case_for_profile(case['case_id'])
            self.assertEqual(before, after)
        finally:
            case['truth'] = original


class CohortHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def request(self, route, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        try:
            connection.request('POST' if body is not None else 'GET', route,
                               None if body is None else json.dumps(body),
                               {} if body is None else {'Content-Type':'application/json'})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_full_outcome_aware_catalog_keeps_original_eight(self):
        status, catalog = self.request('/api/cases')
        self.assertEqual(status, 200)
        self.assertEqual(len(catalog['cases']), 8)
        status, audit = self.request('/api/audit')
        self.assertEqual(status, 200)
        self.assertEqual(len(audit['cases']), 242)
        self.assertFalse(audit['holdout_included'])
        self.assertIn('truth', audit['cases'][0])

    def test_case_journey_prediction_and_explicit_labels_from_every_fold(self):
        for fold in range(5):
            case = next(c for c in server.AUDIT_CASES.values() if c['fold'] == fold)
            case_id = case['case_id']
            status, result = self.request(f'/api/audit/cases/{case_id}?profile=history')
            self.assertEqual(status, 200)
            self.assertEqual(len(result['inputs']), 17)
            self.assertEqual(result['origin'], 'audit')
            self.assertTrue(result['outcome_aware_selection'])
            assert_no_truth(self, result)
            status, journey = self.request(f'/api/audit/journey/{case_id}')
            self.assertEqual(status, 200)
            self.assertEqual(len(journey['snapshots']), 5)
            assert_no_truth(self, journey)
            status, predicted = self.request('/api/audit/predict', {'case_id':case_id,
                'profile':'history', 'inputs':result['inputs']})
            self.assertEqual(status, 200)
            self.assertEqual(predicted['predictions'], result['predictions'])
            assert_no_truth(self, predicted)
            status, labels = self.request(f'/api/audit/labels/{case_id}')
            self.assertEqual(status, 200)
            self.assertEqual(labels, {'truth':case['truth']})

    def test_editing_and_label_injection(self):
        case = next(iter(server.AUDIT_CASES.values()))
        edited = {**case['inputs'], 'Age':None}
        status, result = self.request('/api/audit/predict', {'case_id':case['case_id'], 'inputs':edited})
        self.assertEqual(status, 200)
        self.assertIn('Age', result['changed_features'])
        self.assertTrue(all('Age' in prediction['imputed_features'] for prediction in result['predictions'].values()))
        assert_no_truth(self, result)
        for forbidden in ['CAD','Cath','LAD','LCX','RCA','truth','target','targets']:
            status, error = self.request('/api/audit/predict', {'case_id':case['case_id'],
                'inputs':{**case['inputs'], forbidden:1}})
            self.assertEqual(status, 400)
            self.assertIn('Target labels', error['error'])
        status, _ = self.request('/api/audit/predict', {'case_id':case['case_id'],
            'inputs':case['inputs'], 'truth':case['truth']})
        self.assertEqual(status, 400)

    def test_wrong_roster_profile_and_new_input_route_rejected(self):
        case_id = next(iter(server.AUDIT_CASES))
        status, _ = self.request(f'/api/audit/cases/{case_id}?profile=unknown')
        self.assertEqual(status, 400)
        status, _ = self.request('/api/audit/cases/new-input')
        self.assertEqual(status, 400)
        status, _ = self.request('/api/audit/new')
        self.assertEqual(status, 404)
        status, _ = self.request('/api/audit/new', {'inputs':{}})
        self.assertEqual(status, 404)


if __name__ == '__main__':
    unittest.main()
