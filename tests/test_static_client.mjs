import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {createServer} from 'node:http';
import {dirname, join, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {createStaticApi, predictJson} from '../public/static-client.js';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SITE = join(ROOT, 'dist/site');
const bundle = JSON.parse(readFileSync(join(SITE, 'data/lumen-data.json'), 'utf8'));
const api = createStaticApi({data: bundle});
const targets = ['CAD', 'LAD', 'LCX', 'RCA'];
const clone = value => structuredClone(value);
const post = body => ({method: 'POST', body: JSON.stringify(body)});
const TOLERANCE = 1e-12;
function near(a, b, message) {assert.ok(Math.abs(a - b) < TOLERANCE, `${message}: ${a} != ${b}`);}
function allKeys(value) {
  if (Array.isArray(value)) return value.flatMap(allKeys);
  if (value && typeof value === 'object') return Object.entries(value).flatMap(([key, child]) => [key, ...allKeys(child)]);
  return [];
}
function noOutcomes(value) {
  assert.ok(allKeys(value).every(key => !['truth', 'labels', 'outcomes'].includes(key)));
}
function comparePrediction(actual, expected) {
  for (const key of ['probability', 'log_odds', 'baseline_log_odds', 'baseline_probability']) near(actual[key], expected[key], key);
  assert.equal(actual.model_id, expected.model_id);
  assert.equal(actual.operating_threshold, expected.operating_threshold);
  assert.equal(actual.predicted_label, expected.predicted_label);
  assert.equal(actual.calibration, expected.calibration);
  assert.deepEqual(actual.imputed_features, expected.imputed_features ?? []);
  assert.deepEqual(actual.unknown_categories, expected.unknown_categories ?? []);
  const actualTerms = Object.fromEntries(actual.contributions.map(row => [row.feature, row]));
  assert.equal(Object.keys(actualTerms).length, expected.contributions.length);
  for (const term of expected.contributions) {
    assert.deepEqual(actualTerms[term.feature].value, term.value);
    near(actualTerms[term.feature].log_odds_contribution, term.log_odds_contribution, term.feature);
  }
}
function pythonPredictions(requests) {
  const code = `
import json, sys
sys.path.insert(0, sys.argv[1])
from inference import predict_json
requests=json.load(sys.stdin)
print(json.dumps([predict_json(row['model'],row['inputs']) for row in requests],allow_nan=False))
`;
  const raw = execFileSync(process.env.PYTHON ?? 'python3', ['-c', code, ROOT],
    {input: JSON.stringify(requests), encoding: 'utf8', maxBuffer: 16 * 1024 * 1024});
  return JSON.parse(raw);
}

test('all 160 saved development profile predictions and hidden-outcome routes match', async () => {
  let checked = 0;
  const catalog = await api('/api/cases');
  assert.equal(catalog.cases.length, 8);
  noOutcomes(catalog);
  for (const record of bundle.cases.cases) {
    const journey = await api(`/api/journey/${record.case_id}`);
    assert.equal(journey.snapshots.length, 5);
    noOutcomes(journey);
    for (const profile of bundle.profiles) {
      const projected = await api(`/api/cases/${record.case_id}?profile=${profile.id}`);
      noOutcomes(projected);
      assert.deepEqual(Object.keys(projected.inputs), profile.feature_order);
      const predicted = await api('/api/predict', post({case_id: record.case_id, profile: profile.id, inputs: projected.inputs}));
      noOutcomes(predicted);
      assert.deepEqual(predicted.changed_features, []);
      assert.deepEqual(predicted.outside_development_range, []);
      for (const target of targets) {
        const saved = record.profile_predictions[profile.id][target];
        assert.ok(!bundle.models[saved.model_id].training_row_indices.includes(record.row_index));
        comparePrediction(predicted.predictions[target], saved);
        checked++;
      }
    }
    assert.deepEqual((await api(`/api/labels/${record.case_id}`)).truth, record.truth);
  }
  assert.equal(checked, 160);
  // Returned route values cannot mutate the public bundle or a future response.
  const record = await api(`/api/cases/${catalog.cases[0].case_id}`);
  record.inputs.Age = -1000;
  assert.notEqual((await api(`/api/cases/${record.case_id}`)).inputs.Age, -1000);
});

test('edited, missing, unknown-category and synthetic inputs match Python portable inference', async () => {
  const record = bundle.cases.cases[0];
  const requests = [], jsPredictions = [];
  for (const profile of bundle.profiles) {
    const original = Object.fromEntries(profile.feature_order.map(name => [name, record.inputs[name]]));
    const variants = [
      {...original, Age: original.Age + 3},
      {...original, Age: null, Sex: null},
      {...original, Age: -999, Sex: 'outside-public-dataset'},
    ];
    for (const inputs of variants) {
      const result = await api('/api/predict', post({case_id: record.case_id, profile: profile.id, inputs}));
      assert.ok(result.changed_features.length > 0);
      noOutcomes(result);
      if (inputs.Age === -999) assert.ok(result.outside_development_range.includes('Age'));
      for (const target of targets) {
        requests.push({model: bundle.models[result.predictions[target].model_id], inputs});
        jsPredictions.push(result.predictions[target]);
      }
    }
  }
  const python = pythonPredictions(requests);
  assert.equal(python.length, 60);
  jsPredictions.forEach((prediction, i) => comparePrediction(prediction, python[i]));
});

test('frozen final models reproduce Python on public development inputs without outcome scoring', async () => {
  const requests = [], jsPredictions = [];
  for (const record of bundle.cases.cases) {
    const result = await api('/api/predict-new', post({inputs: record.inputs}));
    assert.equal(result.kind, 'unlabelled');
    noOutcomes(result);
    for (const target of targets) {
      const model = bundle.final_models[`${target}-final-development`];
      assert.equal(model.training_row_indices.length, 242);
      requests.push({model, inputs: record.inputs});
      jsPredictions.push(result.predictions[target]);
    }
  }
  const python = pythonPredictions(requests);
  assert.equal(python.length, 32);
  jsPredictions.forEach((prediction, i) => comparePrediction(prediction, python[i]));
});

test('schemas, evidence and target/nonfinite/request validation preserve the server contract', async () => {
  const record = bundle.cases.cases[0];
  for (const profile of bundle.profiles) {
    const schema = await api(`/api/schema?profile=${profile.id}`);
    assert.deepEqual(schema.feature_order, profile.feature_order);
    const evidence = await api(`/api/evidence?profile=${profile.id}`);
    assert.equal(evidence.protocol.n_input_features, profile.n_features);
    assert.deepEqual(evidence.targets, bundle.availability.profiles[profile.id].targets);
  }
  assert.equal((await api('/api/profiles')).profiles.length, 5);
  assert.equal((await api('/api/final-evaluation')).n_holdout, 61);
  for (const forbidden of ['Cath', 'CAD', 'LAD', 'LCX', 'RCA', 'truth']) {
    await assert.rejects(api('/api/predict', post({case_id: record.case_id, inputs: {...record.inputs, [forbidden]: 1}})), /Target labels/);
  }
  const model = bundle.final_models['CAD-final-development'];
  for (const value of [NaN, Infinity, -Infinity, '', [], {}]) {
    assert.throws(() => predictJson(model, {...record.inputs, Age: value}), /finite number/);
  }
  const missing = clone(record.inputs); delete missing.Age;
  assert.throws(() => predictJson(model, missing), /Input feature mismatch/);
  await assert.rejects(api('/api/predict-new', post({inputs: record.inputs, truth: {CAD: 1}})), /Expected only inputs/);
  await assert.rejects(api('/api/cases/unknown-case'), /Unknown development case/);
  await assert.rejects(api('/api/journey/new-input'), /Unknown development case/);
  await assert.rejects(api('/api/schema?profile=unknown'), /Unknown input profile/);
  await assert.rejects(api('/api/predict', {method: 'POST', body: ' '.repeat(65537)}), /Invalid request size/);
});

test('the built demo resolves under a repository subpath and never transmits prediction requests', async () => {
  const prefix = '/lumen-coronary-evidence/';
  const server = createServer((request, response) => {
    const url = new URL(request.url, 'http://local.test');
    if (!url.pathname.startsWith(prefix)) {response.writeHead(404).end(); return;}
    const relative = decodeURIComponent(url.pathname.slice(prefix.length)) || 'index.html';
    const file = resolve(SITE, relative);
    if (!file.startsWith(SITE + sep)) {response.writeHead(404).end(); return;}
    try {
      const data = readFileSync(file);
      response.writeHead(200, {'Content-Type': relative.endsWith('.json') ? 'application/json' : relative.endsWith('.js') ? 'text/javascript' : 'text/plain'}).end(data);
    } catch {response.writeHead(404).end();}
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}${prefix}`;
  const requests = [];
  const fetchImpl = async (url, options) => {requests.push({url: String(url), method: options?.method ?? 'GET'}); return fetch(url, options);};
  try {
    const html = await (await fetch(base)).text();
    assert.match(html, /name="lumen-runtime" content="static"/);
    assert.match(html, /href="\.\/style\.css"/);
    assert.match(html, /src="\.\/app\.js"/);
    assert.match(html, /"three":"\.\/vendor\/three\.module\.js"/);
    assert.match(html, /href="\.\/data\/evidence\.json"/);
    for (const asset of ['style.css', 'app.js', 'static-client.js', 'vendor/three.module.js', 'vendor/three.core.js',
                         'vendor/addons/controls/OrbitControls.js', 'assets/anatomy.json', 'data/evidence.json']) {
      assert.equal((await fetch(new URL(asset, base))).status, 200, asset);
    }
    const onlineApi = createStaticApi({baseUrl: base, fetchImpl});
    const catalog = await onlineApi('/api/cases');
    await onlineApi('/assets/anatomy.json');
    const record = await onlineApi(`/api/cases/${catalog.cases[0].case_id}`);
    const result = await onlineApi('/api/predict-new', post({inputs: {...record.inputs, Age: record.inputs.Age + 1}}));
    noOutcomes(result);
    assert.equal(requests.length, 2, 'Only the bundle and requested anatomy asset were fetched');
    assert.ok(requests.every(request => request.method === 'GET' && request.url.startsWith(base)));
    assert.equal(requests.filter(request => request.url.endsWith('data/lumen-data.json')).length, 1);
    const serialized = readFileSync(join(SITE, 'data/lumen-data.json'), 'utf8');
    assert.ok(!serialized.includes('holdout_row_indices'));
    assert.ok(!allKeys(bundle).includes('holdout_predictions'));
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});
