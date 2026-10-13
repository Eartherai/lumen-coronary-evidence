/** Full development-cohort browser contract; no final prediction CSV read. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createStaticApi, predictJson} from '../public/static-client.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = name => JSON.parse(readFileSync(new URL(`../artifacts/${name}`, import.meta.url), 'utf8'));
const models = {...read('models.json').models, ...read('availability-models.json').models};
const cohort = read('cohort-audit.json');
const profiles = read('availability-profiles.json').profiles;
const bundle = {schema:read('input_schema.json'), cases:read('availability-cases.json'), models, profiles,
  evidence:read('benchmark.json'), availability:read('availability-benchmark.json'), cohort_audit:cohort};
const api = createStaticApi({data:bundle});
const tolerance = 1e-12;
const close = (a,b,context) => assert.ok(Math.abs(a-b) <= tolerance, `${context}: ${a} vs ${b}`);
const withoutTruth = value => {
  if (Array.isArray(value)) value.forEach(withoutTruth);
  else if (value && typeof value === 'object') {
    assert.equal(Object.hasOwn(value,'truth'),false);
    assert.equal(Object.hasOwn(value,'recorded_labels'),false);
    assert.equal(Object.hasOwn(value,'Cath'),false);
    Object.values(value).forEach(withoutTruth);
  }
};

test('all 4840 portable scores match compact OOF and every excluding-fold model', async () => {
  const development = new Set(cohort.cases.map(record => record.row_index));
  assert.equal(development.size,242);
  const used = new Set();
  let checked = 0;
  for (const record of cohort.cases) {
    const validation = new Set(cohort.cases.filter(other => other.fold === record.fold).map(other => other.row_index));
    for (const profile of profiles) {
      const projected = await api(`/api/audit/cases/${record.case_id}?profile=${profile.id}`);
      withoutTruth(projected);
      assert.deepEqual(Object.keys(projected.inputs), profile.feature_order);
      assert.equal(projected.origin,'audit');
      assert.equal(projected.outcome_aware_selection,true);
      for (const target of cohort.target_order) {
        const prediction = projected.predictions[target], saved = record.profile_predictions[profile.id][target];
        const model = models[prediction.model_id];
        assert.equal(prediction.model_id,`${target}-${profile.id}-outer-${record.fold}`);
        assert.equal(model.training_row_indices.length,development.size-validation.size);
        assert.ok(model.training_row_indices.every(row => development.has(row) && !validation.has(row)));
        close(prediction.probability,saved.probability,`${record.case_id}/${profile.id}/${target}`);
        close(prediction.operating_threshold,saved.operating_threshold,'threshold');
        assert.equal(prediction.predicted_label,saved.predicted_label);
        close(prediction.baseline_log_odds + prediction.contributions.reduce((sum,term) => sum+term.log_odds_contribution,0),
          prediction.log_odds,'score reconstruction');
        assert.equal(prediction.contributions.length,profile.n_features);
        used.add(prediction.model_id);
        checked++;
      }
    }
  }
  assert.equal(used.size,100);
  assert.equal(checked,4840);
});

test('all 4840 browser probabilities, baselines and grouped terms match actual Python runtime', () => {
  const code = `import json,server
out=[]
for case in server.AUDIT_CASES.values():
 for profile in server.PROFILES:
  result=server.audit_case_for_profile(case['case_id'],profile)
  for target,p in result['predictions'].items():
   out.append([case['case_id'],profile,target,p['probability'],p['log_odds'],p['baseline_log_odds'],
    [[c['feature'],c['log_odds_contribution']] for c in p['contributions']]])
print(json.dumps(out,separators=(',',':'),allow_nan=False))`;
  const process = spawnSync('python3',['-c',code], {cwd:root, encoding:'utf8',maxBuffer:32*1024*1024});
  assert.equal(process.status,0,process.stderr);
  const cases = Object.fromEntries(cohort.cases.map(record => [record.case_id,record]));
  const python = JSON.parse(process.stdout);
  assert.equal(python.length,4840);
  for (const [caseId,profileId,target,probability,logOdds,baseline,terms] of python) {
    const record = cases[caseId], profile = profiles.find(profile => profile.id===profileId);
    const inputs = Object.fromEntries(profile.feature_order.map(feature => [feature,record.inputs[feature]]));
    const model = models[record.profile_predictions[profileId][target].model_id];
    const prediction = predictJson(model,inputs);
    close(prediction.probability,probability,'Python/browser probability');
    close(prediction.log_odds,logOdds,'Python/browser score');
    close(prediction.baseline_log_odds,baseline,'Python/browser baseline');
    const browserTerms = Object.fromEntries(prediction.contributions.map(term => [term.feature,term.log_odds_contribution]));
    assert.equal(Object.keys(browserTerms).length,terms.length);
    for (const [feature,value] of terms) close(browserTerms[feature],value,`Python/browser ${caseId}/${profileId}/${target}/${feature}`);
  }
});

test('legacy catalog remains eight; audit catalog is explicitly outcome aware and replies do not alias it', async () => {
  const legacy = await api('/api/cases');
  assert.equal(legacy.cases.length,8);
  const data = await api('/api/audit');
  assert.equal(data.cases.length,242);
  assert.equal(data.holdout_included,false);
  assert.ok(data.cases.every(record => Object.keys(record.truth).length===4));
  data.cases.length=0;
  assert.equal((await api('/api/audit')).cases.length,242);
});

test('every fold has correct case/journey/label/edited inference separation', async () => {
  for(let fold=0;fold<5;fold++) {
    const record = cohort.cases.find(record => record.fold===fold);
    const result = await api(`/api/audit/cases/${record.case_id}?profile=history`);
    const journey = await api(`/api/audit/journey/${record.case_id}`);
    withoutTruth(result); withoutTruth(journey);
    assert.equal(journey.snapshots.length,5);
    assert.equal(journey.origin,'audit');
    assert.deepEqual(await api(`/api/audit/labels/${record.case_id}`),{truth:record.truth});
    const edited = {...result.inputs,Age:null};
    const predicted = await api('/api/audit/predict',{method:'POST',body:JSON.stringify({case_id:record.case_id,profile:'history',inputs:edited})});
    withoutTruth(predicted);
    assert.equal(predicted.origin,'audit');
    assert.deepEqual(predicted.changed_features,['Age']);
    assert.ok(Object.values(predicted.predictions).every(p => p.imputed_features.includes('Age')));
  }
});

test('recorded labels never affect inference and target injection is rejected', async () => {
  const record = cohort.cases[0];
  const altered = structuredClone(bundle);
  altered.cohort_audit.cases[0].truth = Object.fromEntries(Object.entries(record.truth).map(([target,value]) => [target,1-value]));
  const changedLabels = createStaticApi({data:altered});
  assert.deepEqual(await api(`/api/audit/cases/${record.case_id}`),await changedLabels(`/api/audit/cases/${record.case_id}`));
  for (const forbidden of ['CAD','Cath','LAD','LCX','RCA','truth','target','targets']) {
    await assert.rejects(api('/api/audit/predict',{method:'POST',body:JSON.stringify({case_id:record.case_id,
      inputs:{...record.inputs,[forbidden]:1}})}),/Target labels/);
  }
  await assert.rejects(api('/api/audit/predict',{method:'POST',body:JSON.stringify({case_id:record.case_id,
    inputs:record.inputs,truth:record.truth})}),/Expected case_id/);
  await assert.rejects(api('/api/audit/cases/new-input'),/Unknown audit/);
  await assert.rejects(api(`/api/audit/cases/${record.case_id}?profile=unknown`),/Unknown input profile/);
  await assert.rejects(api('/api/audit/new'),/Not found/);
});

test('one cached public load supports subsequent audit inference without network POSTs', async () => {
  const requests=[];
  const network = createStaticApi({baseUrl:'https://static.local/lumen/',fetchImpl:async(url,options) => {
    requests.push({url,method:options?.method??'GET'});
    return {ok:true,json:async()=>structuredClone(bundle)};
  }});
  const data = await network('/api/audit');
  const record = data.cases[0];
  await network(`/api/audit/journey/${record.case_id}`);
  await network(`/api/audit/labels/${record.case_id}`);
  await network('/api/audit/predict',{method:'POST',body:JSON.stringify({case_id:record.case_id,inputs:record.inputs})});
  assert.deepEqual(requests,[{url:'https://static.local/lumen/data/lumen-data.json',method:'GET'}]);
});
