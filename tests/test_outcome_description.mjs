import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {describeOutcome} from '../public/outcome-description.js';
test('Positive flag on recorded negative is a false alarm, never a missed positive',()=>{
 assert.deepEqual(describeOutcome(.7,.5,0),{flag:1,match:false,kind:'false_alarm',text:'false alarm'});
});
test('Negative flag on recorded positive is a missed positive; both correct states agree',()=>{
 assert.equal(describeOutcome(.2,.5,1).text,'missed positive');
 assert.equal(describeOutcome(.7,.5,1).text,'agrees');assert.equal(describeOutcome(.2,.5,0).text,'agrees');
});
test('An observed case may change from false alarm to agreement when the shared threshold changes',()=>{
 const data=JSON.parse(readFileSync(new URL('../artifacts/cohort-audit.json',import.meta.url))),record=data.cases.find(c=>c.case_id==='UCI411-128');
 const prediction=record.profile_predictions.full.LCX;
 assert.equal(record.truth.LCX,0);assert.equal(describeOutcome(prediction.probability,prediction.operating_threshold,record.truth.LCX).text,'false alarm');
 assert.equal(describeOutcome(prediction.probability,.5,record.truth.LCX).text,'agrees');
});
test('Equality at the cutoff is positive and invalid recorded labels are rejected',()=>{
 assert.equal(describeOutcome(.5,.5,0).text,'false alarm');assert.throws(()=>describeOutcome(.5,.5,2));assert.throws(()=>describeOutcome(NaN,.5,0));
});
