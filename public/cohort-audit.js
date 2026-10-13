const TARGETS = ['CAD', 'LAD', 'LCX', 'RCA'];
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = value => `${(100 * value).toFixed(1)}%`;

export function auditDecision(prediction, mode = 'learned') {
  const threshold = mode === 'fixed' ? .5 : prediction.operating_threshold;
  return {probability:prediction.probability, threshold, flag:Number(prediction.probability >= threshold)};
}
export function auditRecord(record, target, mode = 'learned', profileOrder = Object.keys(record.profile_predictions)) {
  if (!TARGETS.includes(target)) throw Error('Unknown audit target');
  const profiles = profileOrder.map(id => ({id, ...auditDecision(record.profile_predictions[id][target], mode)}));
  const full = profiles.find(profile => profile.id === 'full');
  if (!full) throw Error('Full-input prediction is required');
  const truth = record.truth[target], agrees = profiles.every(profile => profile.flag === full.flag);
  const outcome = full.flag === truth ? 'correct' : truth ? 'fn' : 'fp';
  return {record, target, truth, full, profiles, agrees, outcome};
}
export function filterAudit(audit, filters, mode = 'learned') {
  const query = (filters.query ?? '').trim().toUpperCase();
  return audit.cases.map(record => auditRecord(record, filters.target, mode, audit.profile_order)).filter(row =>
    (filters.fold === 'all' || row.record.fold === Number(filters.fold)) &&
    (!query || row.record.case_id.includes(query)) &&
    (filters.outcome === 'all' || (filters.outcome === 'error' ? row.outcome !== 'correct' : row.outcome === filters.outcome)) &&
    (filters.behavior === 'all' || row.agrees === (filters.behavior === 'agree')));
}
export function summarizeAudit(audit, target, mode = 'learned') {
  const rows = audit.cases.map(record => auditRecord(record, target, mode, audit.profile_order));
  const counts = {n:rows.length, tp:0, tn:0, fp:0, fn:0, agreement:0, stable_errors:0};
  for (const row of rows) {
    const key = row.outcome === 'correct' ? row.truth ? 'tp' : 'tn' : row.outcome;
    counts[key]++;
    counts.agreement += Number(row.agrees);
    counts.stable_errors += Number(row.agrees && row.outcome !== 'correct');
  }
  return counts;
}
export function auditSelection(audit, filters, mode = 'learned') {
  const rows = filterAudit(audit, filters, mode);
  return {schema_version:1, scope:'Outcome-aware descriptive development audit; not final-test validation',
    n_development:audit.n_development, holdout_included:false, filters:{...filters}, decision_mode:mode,
    interpretation:audit.interpretation, source_bindings:audit.source_bindings,
    n_selected:rows.length, records:rows.map(row => ({case_id:row.record.case_id, row_index:row.record.row_index,
      excel_row:row.record.row_index + 2, fold:row.record.fold, target:row.target, recorded_label:row.truth,
      full_model_outcome:row.outcome, all_profiles_agree:row.agrees,
      profile_predictions:row.profiles.map(profile => ({...profile,
        model_id:row.record.profile_predictions[profile.id][row.target].model_id}))}))};
}

/** The audit intentionally exposes outcomes for selection. It is not a blinded prediction workflow. */
export function mountCohortAudit({element, audit, profiles, certificate, getMode, onMode, onInspect}) {
  let filters = {target:'LCX', outcome:'error', behavior:'all', fold:'all', query:''}, page = 0, chosenId = null;
  const pageSize = 10, labels = Object.fromEntries(profiles.map(p => [p.id,p.label]));
  element.innerHTML = `<div class="audit-heading"><div><p class="eyebrow">Complete development audit</p><h2>Inspect every error. Not just the examples.</h2></div><span class="pill">${audit.n_development} records · all 5 folds</span></div>
    <p class="audit-intro">Find a false alarm, a missed positive, or a record whose flags change across input profiles. Open it in the anatomy and trace its exact score.</p>
    <p class="audit-scope"><b>Outcomes are visible here and used by the filters.</b> These are development records with existing out-of-fold predictions. This exploratory audit is not a new final test. Agreement between profiles is not confidence.</p>
    <div class="audit-presets"><span>Try a challenge</span><button data-preset="stable-miss">Find an LCX miss all five profiles share</button><button data-preset="changing">Find a changing LAD flag</button><button data-preset="all">Browse every record</button></div>
    <div class="audit-filters">
      <label>Target<select data-filter="target">${TARGETS.map(t=>`<option>${t}</option>`).join('')}</select></label>
      <label>Full-input outcome<select data-filter="outcome"><option value="all">All outcomes</option><option value="error">All errors</option><option value="fn">Missed positive</option><option value="fp">False alarm</option><option value="correct">Correct flag</option></select></label>
      <label>Across five profiles<select data-filter="behavior"><option value="all">Any behavior</option><option value="agree">All five flags agree</option><option value="change">At least one flag changes</option></select></label>
      <label>Outer fold<select data-filter="fold"><option value="all">All five folds</option>${[0,1,2,3,4].map(i=>`<option value="${i}">Fold ${i+1}</option>`).join('')}</select></label>
      <label>Shared decision rule<select data-audit-mode><option value="learned">Training-selected F1 threshold</option><option value="fixed">Fixed 50% threshold</option></select></label>
      <label>Record ID<input data-filter="query" type="search" placeholder="e.g. UCI411-288" aria-label="Search audit record ID"></label>
    </div>
    <div class="audit-counts" aria-live="polite"></div>
    <div class="audit-body"><section class="audit-roster"><div class="audit-list-heading"><h3>Matching records <span data-audit-matches></span></h3><button class="secondary compact" data-audit-export>Export this selection</button></div><p class="table-hint">Scroll horizontally to compare estimates, labels and profile flags.</p><div class="table-wrap" tabindex="0" role="region" aria-label="Matching development audit records"><table class="audit-table"><thead><tr><th>Record / fold</th><th>Full estimate</th><th>Recorded label</th><th>Full flag</th><th>Five profiles</th><th>Open</th></tr></thead><tbody></tbody></table></div><div class="audit-pagination"><button class="secondary compact" data-page="previous">Previous</button><span data-page-status></span><button class="secondary compact" data-page="next">Next</button></div></section><aside class="audit-inspector" aria-live="polite"></aside></div>
    <p class="muted audit-proof">${certificate?.status === 'passed' ? `Actual SHAP independently checked ${certificate.n_explanations_verified} explanations across ${certificate.n_models_verified} models.` : 'Full-cohort explanations use the excluding-fold portable models.'} All 61 final-test records are excluded from this browser audit. <a href="./assets/cohort-audit-verification.json">Verification receipt</a></p>`;
  const find = selector => element.querySelector(selector);
  function update() {
    const mode=getMode(), rows=filterAudit(audit,filters,mode), counts=summarizeAudit(audit,filters.target,mode);
    page=Math.min(page,Math.max(0,Math.ceil(rows.length/pageSize)-1));
    if (!rows.some(row=>row.record.case_id===chosenId)) chosenId=rows[0]?.record.case_id ?? null;
    for(const input of element.querySelectorAll('[data-filter]'))input.value=filters[input.dataset.filter];
    find('[data-audit-mode]').value=mode;
    find('[data-audit-matches]').textContent=`${rows.length} / ${audit.n_development}`;
    find('.audit-counts').innerHTML=`<div><strong>${counts.fn}</strong><span>missed positives</span></div><div><strong>${counts.fp}</strong><span>false alarms</span></div><div><strong>${counts.tp+counts.tn}/${counts.n}</strong><span>correct full-input flags</span></div><div><strong>${counts.stable_errors}/${counts.agreement}</strong><span>errors among records with all five flags agreeing</span></div><p>All ${counts.n} records · ${filters.target} · ${mode==='fixed'?'fixed 50%':'each model’s training-selected'} threshold. Counts describe development predictions; they are not a new score or uncertainty guarantee.</p>`;
    find('tbody').innerHTML=rows.slice(page*pageSize,(page+1)*pageSize).map(row=>`<tr class="${row.record.case_id===chosenId?'audit-selected':''}"><td><button class="audit-record" data-record="${esc(row.record.case_id)}">${esc(row.record.case_id)}</button><small>Fold ${row.record.fold+1} · Excel row ${row.record.row_index+2}</small></td><td>${pct(row.full.probability)}<small>Cutoff ${pct(row.full.threshold)}</small></td><td>${row.truth?'Positive':'Negative'}</td><td><span class="audit-outcome ${row.outcome==='correct'?'is-correct':'is-error'}">${row.outcome==='fn'?'Missed positive':row.outcome==='fp'?'False alarm':row.full.flag?'Positive · correct':'Negative · correct'}</span></td><td>${row.agrees?'All agree':'Flags change'}</td><td><button class="secondary compact" data-open="${esc(row.record.case_id)}">Inspect</button></td></tr>`).join('')||'<tr><td colspan="6">No records match these filters. Try another outcome or decision rule.</td></tr>';
    find('[data-page-status]').textContent=rows.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,rows.length)} of ${rows.length}`:'0 records';
    find('[data-page="previous"]').disabled=page===0;
    find('[data-page="next"]').disabled=(page+1)*pageSize>=rows.length;
    const row=rows.find(row=>row.record.case_id===chosenId), inspector=find('.audit-inspector');
    inspector.innerHTML=row?`<p class="eyebrow">${row.outcome==='correct'?'A correct flag':'An error you can trace'}</p><h3>${esc(row.record.case_id)} · ${row.target}</h3><div class="audit-score"><strong>${pct(row.full.probability)}</strong><span>Full-input estimate<br>Research cutoff ${pct(row.full.threshold)}</span></div><div class="audit-label-pair"><div><span>Recorded outcome</span><b>${row.truth?'Positive':'Negative'}</b></div><div><span>Full-input flag</span><b>${row.full.flag?'Positive':'Negative'}</b></div></div><p class="audit-verdict">${row.outcome==='fn'?'The full-input model misses a recorded positive.':row.outcome==='fp'?'The full-input model flags a recorded negative.':'The full-input flag agrees with this recorded label.'} ${row.agrees?'All five profiles share this flag. Agreement does not make it reliable.':'At least one profile has a different flag. The models were separately fitted.'}</p><div class="audit-profile-list">${row.profiles.map(p=>`<div><span>${esc(labels[p.id])}</span><b>${pct(p.probability)}</b><small>${p.flag?'Positive':'Negative'} · cutoff ${pct(p.threshold)}</small></div>`).join('')}</div><button class="primary" data-inspect-chosen>Inspect ${row.target} in the 3D explorer</button><p class="muted audit-model">Fold ${row.record.fold+1} was excluded from fitting, calibration and threshold selection. Model: ${esc(row.record.profile_predictions.full[row.target].model_id)}.</p>`:'<p>Select matching records to inspect their outcomes and all five profile flags.</p>';
    for(const button of element.querySelectorAll('[data-record]'))button.onclick=()=>{chosenId=button.dataset.record;update();};
    for(const button of element.querySelectorAll('[data-open]'))button.onclick=()=>{chosenId=button.dataset.open;update();onInspect(chosenId,filters.target);};
    if(row)find('[data-inspect-chosen]').onclick=()=>onInspect(chosenId,filters.target);
  }
  for(const input of element.querySelectorAll('[data-filter]'))input.addEventListener(input.type==='search'?'input':'change',()=>{filters[input.dataset.filter]=input.value;page=0;update();});
  find('[data-audit-mode]').onchange=event=>{onMode(event.target.value);update();};
  for(const button of element.querySelectorAll('[data-preset]'))button.onclick=()=>{
    const preset=button.dataset.preset;
    filters=preset==='stable-miss'?{target:'LCX',outcome:'fn',behavior:'agree',fold:'all',query:''}:preset==='changing'?{target:'LAD',outcome:'all',behavior:'change',fold:'all',query:''}:{target:filters.target,outcome:'all',behavior:'all',fold:'all',query:''};
    page=0;update();
  };
  find('[data-page="previous"]').onclick=()=>{page--;update();};find('[data-page="next"]').onclick=()=>{page++;update();};
  find('[data-audit-export]').onclick=()=>{
    const blob=new Blob([JSON.stringify(auditSelection(audit,filters,getMode()),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');
    link.href=url;link.download=`lumen-development-audit-${filters.target.toLowerCase()}-${getMode()}.json`;link.click();URL.revokeObjectURL(url);
  };
  update();return {update};
}
