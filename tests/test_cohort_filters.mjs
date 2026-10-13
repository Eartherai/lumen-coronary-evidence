import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {auditDecision, auditRecord, filterAudit, summarizeAudit, auditSelection} from '../public/cohort-audit.js';
const audit=JSON.parse(readFileSync(new URL('../artifacts/cohort-audit.json',import.meta.url)));
const filters={target:'LCX',outcome:'fn',behavior:'agree',fold:'all',query:''};
test('Complete audit includes 242 unique development records and five folds',()=>{
 assert.equal(audit.cases.length,242);assert.equal(new Set(audit.cases.map(r=>r.case_id)).size,242);
 assert.deepEqual([...new Set(audit.cases.map(r=>r.fold))].sort(),[0,1,2,3,4]);assert.equal(audit.holdout_included,false);
});
test('All outcome, agreement and fold filters recompute from the shared decision rule',()=>{
 for(const mode of ['learned','fixed'])for(const target of audit.target_order)for(const outcome of ['all','error','fn','fp','correct'])for(const behavior of ['all','agree','change'])for(const fold of ['all','0','1','2','3','4']){
  const expected=audit.cases.filter(record=>{
   const flag=profile=>Number(record.profile_predictions[profile][target].probability >= (mode==='fixed'?.5:record.profile_predictions[profile][target].operating_threshold));
   const full=flag('full'),truth=record.truth[target],error=full!==truth,agree=audit.profile_order.every(p=>flag(p)===full);
   return (fold==='all'||record.fold===Number(fold))&&(outcome==='all'||outcome==='error'&&error||outcome==='fn'&&error&&truth===1||outcome==='fp'&&error&&truth===0||outcome==='correct'&&!error)&&(behavior==='all'||behavior==='agree'&&agree||behavior==='change'&&!agree);
  }).map(r=>r.case_id);
  assert.deepEqual(filterAudit(audit,{target,outcome,behavior,fold},mode).map(r=>r.record.case_id),expected);
 }
});
test('All-five agreement retains genuine mistakes rather than implying confidence',()=>{
 const rows=filterAudit(audit,filters);assert.equal(rows.length,9);
 assert.ok(rows.every(row=>row.truth===1&&row.profiles.every(p=>p.flag===0)));
 assert.ok(rows.some(row=>row.record.case_id==='UCI411-288'));
 const summary=summarizeAudit(audit,'LCX');assert.equal(summary.agreement,172);assert.equal(summary.stable_errors,60);
});
test('Fixed rule changes cohort membership and exact probability ties are positive',()=>{
 assert.notDeepEqual(filterAudit(audit,filters,'fixed').map(r=>r.record.case_id),filterAudit(audit,filters).map(r=>r.record.case_id));
 assert.equal(auditDecision({probability:.5,operating_threshold:.6},'fixed').flag,1);
 assert.equal(auditDecision({probability:.5,operating_threshold:.6}).flag,0);
 assert.equal(auditDecision({probability:.6,operating_threshold:.6}).flag,1);
});
test('Record search, export and inspector use the identical target, threshold and outcomes',()=>{
 for(const mode of ['learned','fixed']){
  const selectedFilters={target:'RCA',outcome:'all',behavior:'all',fold:'all',query:' uci411-001 '};
  const rows=filterAudit(audit,selectedFilters,mode), exported=auditSelection(audit,selectedFilters,mode);
  assert.equal(rows.length,1);assert.equal(exported.n_selected,1);assert.equal(exported.decision_mode,mode);assert.equal(exported.holdout_included,false);
  assert.equal(exported.records[0].recorded_label,rows[0].truth);assert.equal(exported.records[0].excel_row,rows[0].record.row_index+2);
  assert.equal(exported.records[0].full_model_outcome,rows[0].outcome);
  for(const p of exported.records[0].profile_predictions)assert.deepEqual({...p,model_id:undefined},{...rows[0].profiles.find(v=>v.id===p.id),model_id:undefined});
 }
 assert.throws(()=>auditRecord(audit.cases[0],'Cath'));
});
