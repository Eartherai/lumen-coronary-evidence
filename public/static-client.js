/** Portable, in-browser counterpart of the local Python API.
 * Only the initial public artifact/asset loads use fetch. Form inputs are
 * evaluated here and are never stored, sent to a service or scored as outcomes.
 */
const TARGETS = ['CAD', 'LAD', 'LCX', 'RCA'];
const FORBIDDEN = new Set(['CAD', 'Cath', 'LAD', 'LCX', 'RCA', 'truth', 'target', 'targets']);
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const clone = value => structuredClone(value);
const now = () => globalThis.performance?.now() ?? Date.now();
const sigmoid = value => value >= 0 ? 1 / (1 + Math.exp(-value)) : Math.exp(value) / (1 + Math.exp(value));

function numeric(value, feature) {
  if (!['number', 'string', 'boolean'].includes(typeof value) ||
      (typeof value === 'string' && !value.trim())) throw Error(`${feature} must be a finite number or null`);
  const number = Number(value);
  if (!Number.isFinite(number)) throw Error(`${feature} must be a finite number or null`);
  return number;
}
function pythonString(value) {
  if (value === true) return 'True';
  if (value === false) return 'False';
  return String(value);
}
function sameValue(a, b) {
  if (typeof a === 'boolean' && typeof b === 'number') return Number(a) === b;
  if (typeof b === 'boolean' && typeof a === 'number') return a === Number(b);
  return a === b;
}
function sameKeys(actual, expected) {
  return actual.length === expected.length && actual.every(key => expected.includes(key));
}

export function predictJson(model, rawInputs) {
  if (!isObject(rawInputs)) throw Error('A complete inputs object is required');
  const expected = [...model.numeric, ...model.categorical].map(field => field.feature);
  const actual = Object.keys(rawInputs);
  if (actual.some(key => FORBIDDEN.has(key))) throw Error('Target labels must never enter model inputs');
  if (!sameKeys(actual, expected)) {
    const missing = expected.filter(key => !actual.includes(key)).sort();
    const extra = actual.filter(key => !expected.includes(key)).sort();
    throw Error(`Input feature mismatch: missing=${JSON.stringify(missing)}, extra=${JSON.stringify(extra)}`);
  }
  let rawLogOdds = Number(model.intercept);
  const contributions = [], imputed = [], unknownCategories = [];
  for (const field of model.numeric) {
    const name = field.feature, raw = rawInputs[name];
    const value = numeric(raw === null ? field.impute : raw, name);
    if (raw === null) imputed.push(name);
    const encoded = (value - field.mean) / field.scale;
    rawLogOdds += encoded * field.coefficient;
    contributions.push({feature: name, value: raw,
      log_odds_contribution: (encoded - field.reference_encoded_mean) * field.coefficient});
  }
  for (const field of model.categorical) {
    const name = field.feature, raw = rawInputs[name];
    const value = pythonString(raw === null ? field.impute : raw);
    if (!field.categories.includes(value)) unknownCategories.push({feature: name, value});
    if (raw === null) imputed.push(name);
    let rawTerm = 0, centeredTerm = 0;
    for (let i = 0; i < field.categories.length; i++) {
      const indicator = Number(value === field.categories[i]);
      rawTerm += indicator * field.coefficients[i];
      centeredTerm += (indicator - field.reference_encoded_means[i]) * field.coefficients[i];
    }
    rawLogOdds += rawTerm;
    contributions.push({feature: name, value: raw, log_odds_contribution: centeredTerm});
  }
  if (!Number.isFinite(rawLogOdds) || contributions.some(row => !Number.isFinite(row.log_odds_contribution))) {
    throw Error('Numeric inputs exceed the finite arithmetic range of this model');
  }
  const reconstructed = model.baseline_log_odds + contributions.reduce((sum, row) => sum + row.log_odds_contribution, 0);
  if (Math.abs(rawLogOdds - reconstructed) > Math.max(1e-10, 1e-9 * Math.max(Math.abs(rawLogOdds), Math.abs(reconstructed)))) {
    throw Error('Attribution reconstruction failed');
  }
  const probability = sigmoid(rawLogOdds), threshold = model.operating_threshold ?? 0.5;
  return {probability, log_odds: rawLogOdds, baseline_log_odds: model.baseline_log_odds,
    baseline_probability: sigmoid(model.baseline_log_odds),
    contributions: contributions.sort((a, b) => Math.abs(b.log_odds_contribution) - Math.abs(a.log_odds_contribution)),
    model_id: model.model_id, imputed_features: imputed, unknown_categories: unknownCategories,
    operating_threshold: threshold, predicted_label: Number(probability >= threshold),
    model_family: model.family ?? 'unweighted', calibration: model.calibration?.method ?? 'none',
    explanation_method: "Exact linear log-odds decomposition centered on this training fold's encoded feature means; not causal."};
}

/** Return async api(path, options) with the server's JSON value contract.
 * data may be supplied only for Node tests; normal browser use fetches the one
 * public bundle relative to the page, including GitHub Pages repo subpaths.
 */
export function createStaticApi({baseUrl = './', fetchImpl = globalThis.fetch, data} = {}) {
  let dataPromise = data ? Promise.resolve(data) : null;
  const base = new URL(baseUrl, globalThis.location?.href ?? 'http://static.local/');
  const assetUrl = path => new URL(path.replace(/^\/+/, ''), base).href;
  async function readPublic(path) {
    if (typeof fetchImpl !== 'function') throw Error('Public artifact fetch is unavailable');
    const response = await fetchImpl(assetUrl(path));
    if (!response.ok) throw Error(`Unable to load public artifact: ${path}`);
    return response.json();
  }
  const getData = () => dataPromise ??= readPublic('data/lumen-data.json');
  return async function staticApi(path, options = {}) {
    const url = new URL(path, 'http://api.local/');
    const route = decodeURIComponent(url.pathname), method = (options.method ?? 'GET').toUpperCase();
    if (!route.startsWith('/api/')) {
      if (method !== 'GET' || !route.startsWith('/assets/') || route.includes('..')) throw Error('Not found');
      return readPublic(route);
    }
    const bundle = await getData();
    const profileId = url.searchParams.get('profile') ?? 'full';
    const profileMap = Object.fromEntries(bundle.profiles.map(profile => [profile.id, profile]));
    const cases = Object.fromEntries(bundle.cases.cases.map(record => [record.case_id, record]));
    const auditCases = Object.fromEntries((bundle.cohort_audit?.cases ?? []).map(record => [record.case_id, record]));
    const getProfile = id => {if (!Object.hasOwn(profileMap, id)) throw Error('Unknown input profile'); return profileMap[id];};
    const getCase = id => {if (!Object.hasOwn(cases, id)) throw Error('Unknown development case'); return cases[id];};
    const getAuditCase = id => {if (!Object.hasOwn(auditCases, id)) throw Error('Unknown audit development case'); return auditCases[id];};
    const schema = id => {const chosen = getProfile(id); return {...bundle.schema, profile: id,
      feature_order: chosen.feature_order, numeric: chosen.numeric, categorical: chosen.categorical};};
    const project = (id, profile = 'full') => {
      const record = getCase(id), chosen = getProfile(profile);
      const predictions = record.profile_predictions?.[profile] ?? (profile === 'full' ? record.predictions : null);
      if (!predictions) throw Error('Profile predictions unavailable');
      return {case_id: id, row_index: record.row_index, fold: record.fold, profile, kind: 'development',
        inputs: Object.fromEntries(chosen.feature_order.map(feature => [feature, record.inputs[feature]])), predictions};
    };
    const projectAudit = (id, profile = 'full') => {
      const record = getAuditCase(id), chosen = getProfile(profile);
      const inputs = Object.fromEntries(chosen.feature_order.map(feature => [feature, record.inputs[feature]]));
      const saved = record.profile_predictions[profile];
      const predictions = Object.fromEntries(TARGETS.map(target => [target,
        predictJson(bundle.models[saved[target].model_id], inputs)]));
      return {case_id:id, row_index:record.row_index, fold:record.fold, profile, kind:'development',
        origin:'audit', outcome_aware_selection:true, inputs, predictions};
    };
    const diagnostics = (inputs, profile) => ({outside_development_range: schema(profile).numeric
      .filter(field => inputs[field.feature] !== null &&
        !(field.min_development <= numeric(inputs[field.feature], field.feature) &&
          numeric(inputs[field.feature], field.feature) <= field.max_development)).map(field => field.feature)});
    if (method === 'GET') {
      getProfile(profileId);
      if (route === '/api/audit') {
        if (!bundle.cohort_audit) throw Error('Development audit artifact is unavailable');
        return clone(bundle.cohort_audit);
      }
      if (route.startsWith('/api/audit/cases/')) return clone(projectAudit(route.slice('/api/audit/cases/'.length), profileId));
      if (route.startsWith('/api/audit/labels/')) return clone({truth:getAuditCase(route.slice('/api/audit/labels/'.length)).truth});
      if (route.startsWith('/api/audit/journey/')) {
        const id = route.slice('/api/audit/journey/'.length), record = getAuditCase(id);
        return {case_id:id, row_index:record.row_index, fold:record.fold, kind:'development', origin:'audit',
          outcome_aware_selection:true, original_inputs_only:true, profile_order:bundle.profiles.map(profile => profile.id),
          snapshots:bundle.profiles.map(chosen => {
            const projected = projectAudit(id, chosen.id);
            return {profile_id:chosen.id, label:chosen.label, n_features:chosen.n_features,
              row_index:record.row_index, fold:record.fold, inputs:projected.inputs, predictions:projected.predictions};
          }), interpretation:'Outcome-aware development audit: every profile uses existing models that excluded ' +
            'this entire outer validation fold. Recorded outcomes are not prediction inputs; ' +
            'profile agreement is not clinical confidence and profile differences are not causal effects.'};
      }
      if (route === '/api/cases') return clone({selection: bundle.cases.selection, new_input_ready: Boolean(bundle.final_models),
        cases: bundle.cases.cases.map(record => ({case_id: record.case_id, fold: record.fold}))});
      if (route === '/api/profiles') return clone({profiles: bundle.profiles, availability_evidence: bundle.availability});
      if (route === '/api/schema') return clone(schema(profileId));
      if (route === '/api/evidence') {
        const chosen = bundle.availability?.profiles[profileId];
        return clone(chosen ? {...bundle.evidence, targets: chosen.targets, availability_profile: profileId,
          protocol: {...bundle.evidence.protocol, n_input_features: getProfile(profileId).n_features}} : bundle.evidence);
      }
      if (route === '/api/final-evaluation') return clone(bundle.final_evaluation ?? {available: false});
      if (route.startsWith('/api/cases/')) return clone(project(route.slice('/api/cases/'.length), profileId));
      if (route.startsWith('/api/labels/')) return clone({truth: getCase(route.slice('/api/labels/'.length)).truth});
      if (route.startsWith('/api/journey/')) {
        const id = route.slice('/api/journey/'.length), record = getCase(id);
        return clone({case_id: id, row_index: record.row_index, fold: record.fold, kind: 'development', original_inputs_only: true,
          profile_order: bundle.profiles.map(profile => profile.id), snapshots: bundle.profiles.map(chosen => {
            const projected = project(id, chosen.id);
            return {profile_id: chosen.id, label: chosen.label, n_features: chosen.n_features,
              row_index: record.row_index, fold: record.fold, inputs: projected.inputs, predictions: projected.predictions};
          }), interpretation: 'The same recorded development case across separately refitted input-profile models that excluded this record. ' +
            'Differences combine available inputs, fitted model, calibration and research threshold changes; ' +
            'they do not establish causal effects, clinical utility or confidence.'});
      }
      throw Error('Not found');
    }
    if (method !== 'POST' || !['/api/predict', '/api/predict-new', '/api/audit/predict'].includes(route)) throw Error('Not found');
    if (typeof options.body !== 'string' || new TextEncoder().encode(options.body).length > 65536 || !options.body.length) {
      throw Error('Invalid request size');
    }
    const body = JSON.parse(options.body);
    if (!isObject(body) || !isObject(body.inputs)) throw Error('A complete inputs object is required');
    const started = now();
    if (route === '/api/predict-new') {
      if (!sameKeys(Object.keys(body), ['inputs'])) throw Error('Expected only inputs');
      if (!bundle.final_models) throw Error('Final-development models are not yet frozen');
      const predictions = Object.fromEntries(TARGETS.map(target => [target,
        predictJson(bundle.final_models[`${target}-final-development`], body.inputs)]));
      return {case_id: 'new-input', kind: 'unlabelled', profile: 'full', predictions, changed_features: [],
        elapsed_ms: now() - started, ...diagnostics(body.inputs, 'full'),
        interpretation: 'Unlabelled inputs; no recorded outcome for comparison'};
    }
    if (!sameKeys(Object.keys(body), ['case_id', 'inputs']) && !sameKeys(Object.keys(body), ['case_id', 'inputs', 'profile'])) {
      throw Error('Expected case_id, inputs and optional profile');
    }
    const isAudit = route === '/api/audit/predict';
    const profile = body.profile ?? 'full', record = isAudit ? projectAudit(body.case_id, profile) : project(body.case_id, profile);
    const predictions = Object.fromEntries(Object.entries(record.predictions).map(([target, saved]) => [target,
      predictJson(bundle.models[saved.model_id], body.inputs)]));
    const changed = Object.keys(body.inputs).filter(name => !sameValue(body.inputs[name], record.inputs[name]));
    return {case_id: body.case_id, profile, predictions, changed_features: changed,
      ...(isAudit ? {kind:'development', origin:'audit', outcome_aware_selection:true} : {}),
      ...diagnostics(body.inputs, profile), elapsed_ms: now() - started,
      interpretation: changed.length ? 'Edited model sensitivity; original labels do not validate modified inputs' :
        isAudit ? 'Development audit case predicted by models that excluded this entire validation fold' :
          'Development case predicted by models that excluded this record'};
  };
}
