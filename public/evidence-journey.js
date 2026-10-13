const TARGETS=['CAD','LAD','LCX','RCA'];
const SHORT=['History','+ examination','+ ECG','+ laboratory','+ echo'];
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const percent=value=>(value*100).toFixed(1)+'%';

export function summarizeJourney(journey,target,mode='learned'){
  const points=journey.snapshots.map(snapshot=>{
    const prediction=snapshot.predictions[target];
    const threshold=mode==='fixed'?.5:prediction.operating_threshold;
    return {profile_id:snapshot.profile_id,n_features:snapshot.n_features,probability:prediction.probability,threshold,positive:prediction.probability>=threshold};
  });
  const changes=points.slice(1).filter((point,index)=>point.positive!==points[index].positive).length;
  return {points,changes,min:Math.min(...points.map(p=>p.probability)),max:Math.max(...points.map(p=>p.probability))};
}

export function journeyReceipt(journey,selected,activeProfile,mode){
  return {format:'lumen-evidence-journey-v1',case_id:journey.case_id,row_index:journey.row_index,validation_fold:journey.fold,
    selected_target:selected,selected_profile:activeProfile,decision_rule:mode,
    classification_formula:'probability >= 0.5 for fixed mode; otherwise probability >= each prediction.operating_threshold',
    scope:'Original public development record. Every snapshot uses separately fitted models that excluded this record. No recorded outcomes included.',
    limitations:'Profile differences are model comparisons, not treatment effects, test benefit, a confidence interval or a recommended sequence of care.',
    snapshots:journey.snapshots};
}

export function renderJourney({element,journey,selected,activeProfile,mode,edited,kind,onProfile,onTarget,onRestore}){
  // Preserve the keyboard position when a target/profile action rebuilds the matrix.
  const active=element.ownerDocument.activeElement;
  const focused=element.contains(active)&&active.matches('button[data-profile],button[data-journey-target]')?{profile:active.dataset.profile,target:active.dataset.target,journeyTarget:active.dataset.journeyTarget}:null;
  if(element.dataset.downloadUrl){URL.revokeObjectURL(element.dataset.downloadUrl);delete element.dataset.downloadUrl;}
  if(!journey||kind==='unlabelled'||edited){
    element.innerHTML=`<div class="journey-heading"><div><p class="eyebrow">Compare available evidence</p><h2>One record. Five input profiles.</h2></div></div><p class="muted">${kind==='unlabelled'?'The unlabelled form uses the frozen full-input model. Five-profile comparisons are available for the original development examples.':edited?'The original-record comparison is paused while measurements are edited. Restore the recorded values to compare matching cases.':'Loading the matching profile predictions…'}</p>${edited?'<button class="secondary" id="journey-restore">Restore recorded values</button>':''}`;
    element.querySelector('#journey-restore')?.addEventListener('click',onRestore);
    return;
  }
  const summary=summarizeJourney(journey,selected,mode),points=summary.points;
  const x=index=>55+index*100,y=value=>210-value*155;
  const line=key=>points.map((point,index)=>`${x(index)},${y(point[key])}`).join(' ');
  const accessible=points.map((p,i)=>`${SHORT[i]}, ${p.n_features} inputs: ${percent(p.probability)}, threshold ${percent(p.threshold)}, ${p.positive?'positive flag':'below threshold'}`).join('; ');
  const receipt=JSON.stringify(journeyReceipt(journey,selected,activeProfile,mode),null,2);
  element.innerHTML=`<div class="journey-heading"><div><p class="eyebrow">Compare available evidence</p><h2>One record. Five input profiles.</h2><p class="muted">${escape(journey.case_id)} · fold ${journey.fold+1} · this record was excluded from every model below.</p></div><a class="secondary" id="journey-download" download="lumen-${escape(journey.case_id)}-comparison.json">Download comparison</a></div>
    <p class="table-hint">Scroll the comparison horizontally on smaller screens to inspect every profile.</p><div class="journey-layout"><div class="journey-chart"><div class="journey-selected"><strong>${selected}</strong><span>${percent(summary.min)}–${percent(summary.max)} across profiles</span><span class="journey-badge ${summary.changes?'changing':''}">${summary.changes?'Research flag changes':'Same research flag'}</span></div>
    <svg viewBox="0 0 500 290" role="img" aria-label="${escape(selected+' profile comparison. '+accessible)}">
      <g fill="var(--muted)" font-size="12">${[0,.5,1].map(v=>`<line x1="45" y1="${y(v)}" x2="475" y2="${y(v)}" stroke="var(--line)"/><text x="38" y="${y(v)+4}" text-anchor="end">${100*v}%</text>`).join('')}
      <polyline points="${line('threshold')}" fill="none" stroke="var(--orange)" stroke-width="2" stroke-dasharray="6 5"/><polyline points="${line('probability')}" fill="none" stroke="var(--mint)" stroke-width="3"/>
      ${points.map((p,i)=>`<g><line x1="${x(i)}" y1="45" x2="${x(i)}" y2="220" stroke="${p.profile_id===activeProfile?'var(--mint)':'transparent'}" stroke-opacity=".2" stroke-width="28"/><circle cx="${x(i)}" cy="${y(p.probability)}" r="6" fill="${p.positive?'var(--mint)':'var(--panel)'}" stroke="var(--mint)" stroke-width="2"/><text x="${x(i)}" y="${y(p.probability)-14}" text-anchor="middle" fill="var(--text)">${percent(p.probability)}</text><text x="${x(i)}" y="248" text-anchor="middle">${SHORT[i]}</text><text x="${x(i)}" y="271" text-anchor="middle">${p.n_features} inputs</text></g>`).join('')}</g></svg>
      <div class="journey-legend"><span><i class="probability-key"></i>Model probability</span><span><i class="threshold-key"></i>${mode==='fixed'?'Fixed 50% threshold':'Each model’s fitted threshold'}</span></div></div>
    <div class="journey-matrix-wrap" tabindex="0" role="region" aria-label="All target and profile comparisons"><table class="journey-matrix"><caption>Compare all four targets. Select a cell to update anatomy and explanation.</caption><thead><tr><th>Target</th>${journey.snapshots.map((s,i)=>`<th scope="col">${SHORT[i]}<small>${s.n_features} inputs</small></th>`).join('')}</tr></thead><tbody>${TARGETS.map(target=>{
      const row=summarizeJourney(journey,target,mode);
      return `<tr class="${target===selected?'selected-row':''}"><th scope="row"><button data-journey-target="${target}" aria-pressed="${target===selected}">${target}<small>${row.changes?'Flag changes':'Same flag'}</small></button></th>${row.points.map(p=>`<td><button class="journey-cell ${target===selected&&p.profile_id===activeProfile?'active':''}" data-profile="${p.profile_id}" data-target="${target}" aria-label="${escape(`${target}, ${p.n_features} inputs, probability ${percent(p.probability)}, threshold ${percent(p.threshold)}, ${p.positive?'positive research flag':'below research threshold'}`)}"><strong>${percent(p.probability)}</strong><small class="${p.positive?'positive':'negative'}">${p.positive?'Positive':'Below'}</small><small>cutoff ${percent(p.threshold)}</small></button></td>`).join('')}</tr>`;
    }).join('')}</tbody></table></div></div>
    <p class="journey-limits">The same recorded values are projected into each input set. Differences include refitting and calibration; they do not isolate the effect of a test. The displayed range is not a confidence interval, and this ordering is not a recommended care sequence.</p><details class="journey-receipt"><summary>View exact comparison JSON</summary><pre>${escape(receipt)}</pre></details>`;
  for(const button of element.querySelectorAll('[data-profile]'))button.onclick=()=>{onTarget(button.dataset.target);onProfile(button.dataset.profile);};
  for(const button of element.querySelectorAll('[data-journey-target]'))button.onclick=()=>onTarget(button.dataset.journeyTarget);
  const url=URL.createObjectURL(new Blob([receipt],{type:'application/json'}));
  element.dataset.downloadUrl=url;element.querySelector('#journey-download').href=url;
  if(focused){const replacement=[...element.querySelectorAll('button[data-profile],button[data-journey-target]')].find(button=>button.dataset.profile===focused.profile&&button.dataset.target===focused.target&&button.dataset.journeyTarget===focused.journeyTarget);replacement?.focus({preventScroll:true});}
}
