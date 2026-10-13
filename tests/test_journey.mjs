import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarizeJourney,journeyReceipt} from '../public/evidence-journey.js';

const cases=JSON.parse(readFileSync(new URL('../artifacts/availability-cases.json',import.meta.url))).cases;
const profiles=JSON.parse(readFileSync(new URL('../artifacts/availability-profiles.json',import.meta.url))).profiles;
for(const record of cases){
  const journey={case_id:record.case_id,row_index:record.row_index,fold:record.fold,snapshots:profiles.map(p=>({profile_id:p.id,n_features:p.n_features,predictions:record.profile_predictions[p.id]}))};
  for(const target of ['CAD','LAD','LCX','RCA'])for(const mode of ['learned','fixed']){
    const actual=summarizeJourney(journey,target,mode);
    const expected=profiles.map(p=>{const prediction=record.profile_predictions[p.id][target];return prediction.probability>=(mode==='fixed'?.5:prediction.operating_threshold);});
    assert.deepEqual(actual.points.map(p=>p.positive),expected);
    assert.equal(actual.changes,expected.slice(1).filter((flag,i)=>flag!==expected[i]).length);
  }
  const receipt=journeyReceipt(journey,'LAD','full','learned');
  assert.equal(receipt.snapshots,journey.snapshots);
  assert.equal('truth' in receipt,false);
}
const case128=cases.find(c=>c.case_id==='UCI411-128');
const journey128={snapshots:profiles.map(p=>({profile_id:p.id,n_features:p.n_features,predictions:case128.profile_predictions[p.id]}))};
assert.deepEqual(summarizeJourney(journey128,'LAD').points.map(p=>p.positive),[true,false,false,false,true]);
assert.equal(summarizeJourney(journey128,'LAD').changes,2);
assert.equal(summarizeJourney(journey128,'LAD','fixed').changes,1);
console.log('Verified all 64 case/target/rule paths, thresholds, receipt routing and the nonmonotonic LAD example.');
