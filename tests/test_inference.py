"""Integration checks for the case/model contract; never access the final holdout.

Run: python3 -m unittest discover -s coronary-evidence/tests -v
"""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen


APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location("coronary_test_server", APP / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_keys(child)


class ModelContractTests(unittest.TestCase):
    def setUp(self):
        self.case = next(iter(server.CASES.values()))

    def test_every_displayed_case_excluded_from_all_four_fitted_models(self):
        self.assertEqual(len(server.CASES), 8)
        for case in server.CASES.values():
            self.assertEqual(set(case["predictions"]), {"CAD", "LAD", "LCX", "RCA"})
            self.assertEqual(len(case["inputs"]), 55)
            for target, saved in case["predictions"].items():
                with self.subTest(case=case["case_id"], target=target):
                    model = server.MODELS[saved["model_id"]]
                    self.assertEqual(model["target"], target)
                    self.assertTrue(saved["model_id"].startswith(target+"-") and saved["model_id"].endswith(f"outer-{case['fold']}"))
                    self.assertNotIn(case["row_index"], model["training_row_indices"])
                    feature_names = {f["feature"] for f in model["numeric"] + model["categorical"]}
                    self.assertEqual(feature_names, set(case["inputs"]))
                    self.assertTrue(feature_names.isdisjoint({"Cath", "CAD", "LAD", "LCX", "RCA"}))

    def test_live_predictions_match_saved_oof_and_all_contributions_reconstruct(self):
        for case in server.CASES.values():
            result = server.predict_case(case["case_id"], case["inputs"])
            self.assertEqual(result["changed_features"], [])
            self.assertEqual(result["outside_development_range"], [])
            self.assertTrue({"truth", "labels"}.isdisjoint(all_keys(result)))
            for target, actual in result["predictions"].items():
                with self.subTest(case=case["case_id"], target=target):
                    self.assertAlmostEqual(actual["probability"], case["predictions"][target]["probability"], places=12)
                    self.assertEqual(len(actual["contributions"]), 55)
                    reconstructed = actual["baseline_log_odds"] + sum(c["log_odds_contribution"] for c in actual["contributions"])
                    self.assertAlmostEqual(reconstructed, actual["log_odds"], places=11)
                    self.assertAlmostEqual(1 / (1 + math.exp(-reconstructed)), actual["probability"], places=12)

    def test_each_availability_profile_uses_its_exact_refitted_feature_set(self):
        self.assertEqual(len(server.PROFILES), 5)
        for profile, specification in server.PROFILES.items():
            for case in server.CASES.values():
                with self.subTest(profile=profile, case=case['case_id']):
                    projected = server.case_for_profile(case['case_id'], profile)
                    self.assertEqual(set(projected['inputs']), set(specification['feature_order']))
                    result = server.predict_case(case['case_id'], projected['inputs'], profile)
                    for target, prediction in result['predictions'].items():
                        model = server.MODELS[prediction['model_id']]
                        self.assertNotIn(case['row_index'], model['training_row_indices'])
                        self.assertEqual(len(prediction['contributions']), specification['n_features'])
                        self.assertAlmostEqual(prediction['probability'], projected['predictions'][target]['probability'], places=12)
                        self.assertEqual(prediction['operating_threshold'], model['operating_threshold'])

    def test_recorded_truth_is_not_used_for_inference(self):
        original = server.predict_case(self.case["case_id"], self.case["inputs"])["predictions"]
        changed_case = deepcopy(self.case)
        changed_case["truth"] = {t: 1 - value for t, value in self.case["truth"].items()}
        with patch.dict(server.CASES, {self.case["case_id"]: changed_case}):
            changed = server.predict_case(self.case["case_id"], self.case["inputs"])["predictions"]
        self.assertEqual(original, changed)

    def test_journey_matches_all_excluding_profile_snapshots_without_recorded_outcomes(self):
        for case in server.CASES.values():
            journey = server.case_journey(case['case_id'])
            self.assertEqual(journey['kind'], 'development')
            self.assertTrue(journey['original_inputs_only'])
            self.assertEqual(journey['profile_order'], list(server.PROFILES))
            self.assertEqual(len(journey['snapshots']), 5)
            self.assertTrue({'truth', 'labels', 'outcomes'}.isdisjoint(all_keys(journey)))
            for snapshot in journey['snapshots']:
                profile = snapshot['profile_id']
                expected = server.case_for_profile(case['case_id'], profile)
                self.assertEqual(snapshot['row_index'], case['row_index'])
                self.assertEqual(snapshot['fold'], case['fold'])
                self.assertEqual(snapshot['label'], server.PROFILES[profile]['label'])
                self.assertEqual(snapshot['n_features'], server.PROFILES[profile]['n_features'])
                self.assertEqual(set(snapshot['inputs']), set(server.PROFILES[profile]['feature_order']))
                self.assertEqual(snapshot['inputs'], expected['inputs'])
                self.assertEqual(snapshot['predictions'], expected['predictions'])
                for target, prediction in snapshot['predictions'].items():
                    with self.subTest(case=case['case_id'], profile=profile, target=target):
                        model = server.MODELS[prediction['model_id']]
                        self.assertNotIn(case['row_index'], model['training_row_indices'])
                        self.assertNotIn('final-development', prediction['model_id'])
                        self.assertEqual(model['target'], target)
                        expected_features = {field['feature'] for field in model['numeric'] + model['categorical']}
                        self.assertEqual(expected_features, set(snapshot['inputs']))
                        self.assertEqual(len(prediction['contributions']), snapshot['n_features'])
                        fresh = server.predict_json(model, snapshot['inputs'])
                        self.assertAlmostEqual(prediction['probability'], fresh['probability'], places=12)
                        self.assertEqual(prediction['operating_threshold'], fresh['operating_threshold'])
                        self.assertEqual(prediction['predicted_label'], fresh['predicted_label'])
        with self.assertRaises(KeyError):
            server.case_journey('new-input')

    def test_edited_measurement_changes_model_without_changing_case_or_using_labels(self):
        inputs = deepcopy(self.case["inputs"])
        inputs["Age"] += 1
        result = server.predict_case(self.case["case_id"], inputs)
        self.assertEqual(result["changed_features"], ["Age"])
        self.assertIn("original labels do not validate", result["interpretation"])
        self.assertTrue({"truth", "labels"}.isdisjoint(all_keys(result)))
        self.assertNotEqual(inputs["Age"], server.CASES[self.case["case_id"]]["inputs"]["Age"])
        for target, actual in result["predictions"].items():
            model = server.MODELS[actual["model_id"]]
            age = next(f for f in model["numeric"] if f["feature"] == "Age")
            expected_change = age["coefficient"] / age["scale"]
            self.assertAlmostEqual(actual["log_odds"] - self.case["predictions"][target]["log_odds"], expected_change, places=11)

    def test_out_of_range_missing_and_unseen_categories_are_diagnosed(self):
        inputs = deepcopy(self.case["inputs"])
        field = next(f for f in server.SCHEMA["numeric"] if f["feature"] == "Age")
        inputs["Age"] = field["max_development"] + 1
        inputs["BP"] = None
        inputs["Sex"] = "unseen-audit-category"
        result = server.predict_case(self.case["case_id"], inputs)
        self.assertIn("Age", result["outside_development_range"])
        for prediction in result["predictions"].values():
            self.assertIn("BP", prediction["imputed_features"])
            self.assertIn({"feature": "Sex", "value": "unseen-audit-category"}, prediction["unknown_categories"])
            self.assertTrue(math.isfinite(prediction["probability"]))

    def test_new_inputs_use_frozen_final_models_without_recorded_outcomes(self):
        result=server.predict_new(self.case['inputs'])
        self.assertEqual(result['kind'], 'unlabelled')
        self.assertTrue({'truth','labels'}.isdisjoint(all_keys(result)))
        for target,prediction in result['predictions'].items():
            self.assertEqual(prediction['model_id'],target+'-final-development')
            self.assertEqual(len(server.FINAL_MODELS[prediction['model_id']]['training_row_indices']),242)
        for profile in server.PROFILES:
            projected=server.case_for_profile(self.case['case_id'],profile)
            recorded=server.predict_case(self.case['case_id'],projected['inputs'],profile)
            self.assertTrue(all('final-development' not in p['model_id'] for p in recorded['predictions'].values()))

    def test_targets_missing_fields_and_nonfinite_values_rejected(self):
        for forbidden in ["CAD", "Cath", "LAD", "LCX", "RCA", "truth"]:
            with self.subTest(forbidden=forbidden):
                inputs = {**self.case["inputs"], forbidden: 1}
                with self.assertRaises(ValueError):
                    server.predict_case(self.case["case_id"], inputs)
        inputs = deepcopy(self.case["inputs"])
        del inputs["Age"]
        with self.assertRaises(ValueError):
            server.predict_case(self.case["case_id"], inputs)
        for value in [float("nan"), float("inf"), -float("inf")]:
            inputs = {**self.case["inputs"], "Age": value}
            with self.assertRaises(ValueError):
                server.predict_case(self.case["case_id"], inputs)


class HTTPContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"
        cls.case = next(iter(server.CASES.values()))

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=3)

    def request_json(self, path, body=None):
        req = Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_case_endpoint_does_not_reveal_truth_and_labels_are_separate(self):
        status, case = self.request_json("/api/cases/" + self.case["case_id"])
        self.assertEqual(status, 200)
        self.assertTrue({"truth", "labels"}.isdisjoint(all_keys(case)))
        self.assertEqual(case["inputs"], self.case["inputs"])
        status, labels = self.request_json("/api/labels/" + self.case["case_id"])
        self.assertEqual(status, 200)
        self.assertEqual(labels, {"truth": self.case["truth"]})

    def test_predict_endpoint_returns_predictions_only_and_rejects_labels(self):
        body = {"case_id": self.case["case_id"], "inputs": self.case["inputs"]}
        status, result = self.request_json("/api/predict", body)
        self.assertEqual(status, 200)
        self.assertTrue({"truth", "labels"}.isdisjoint(all_keys(result)))
        with_label = {**body, "truth": self.case["truth"]}
        self.assertEqual(self.request_json("/api/predict", with_label)[0], 400)
        body["inputs"] = {**body["inputs"], "Cath": "CAD"}
        self.assertEqual(self.request_json("/api/predict", body)[0], 400)

    def test_journey_endpoint_excludes_recorded_outcomes_and_rejects_unknown_case(self):
        status, journey = self.request_json('/api/journey/' + self.case['case_id'])
        self.assertEqual(status, 200)
        self.assertEqual(journey, server.case_journey(self.case['case_id']))
        self.assertTrue({'truth', 'labels', 'outcomes'}.isdisjoint(all_keys(journey)))
        self.assertEqual(self.request_json('/api/journey/unknown-case')[0], 400)
        self.assertEqual(self.request_json('/api/journey/new-input')[0], 400)


if __name__ == "__main__":
    unittest.main()
