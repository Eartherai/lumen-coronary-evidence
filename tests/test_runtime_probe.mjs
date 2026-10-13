import test from 'node:test';
import assert from 'node:assert/strict';
import {createRuntimeProbe,summarizeFrames} from '../public/runtime-probe.js';

function scheduledProbe(environment=()=>({document_visibility:'visible'})){
 let clock=0,nextTimer=0;const timers=new Map(),cancelled=[];
 const probe=createRuntimeProbe({now:()=>clock,environment,
  schedule:(callback,delayMs)=>{const id=++nextTimer;timers.set(id,{callback,delayMs});return id;},
  cancel:id=>{cancelled.push(id);timers.delete(id);}});
 return {probe,timers,cancelled,setTime:ms=>{clock=ms;},fire:id=>timers.get(id).callback()};
}
test('Frame rate is derived from observed intervals rather than an assumed refresh rate',()=>{
 const summary=summarizeFrames([{at_ms:100,callback_cpu_ms:1},{at_ms:110,callback_cpu_ms:2},{at_ms:130,callback_cpu_ms:3},{at_ms:160,callback_cpu_ms:4}]);
 assert.equal(summary.frame_callbacks_per_second,50);assert.equal(summary.interval_ms.median,20);assert.equal(summary.interval_ms.p95,29);assert.equal(summary.observed_span_ms,60);
 assert.equal(summarizeFrames([]).frame_callbacks_per_second,null);
});
test('DOM and next-render callback latency are distinct measured endpoints, with clinical values stripped',()=>{
 let clock=100;const probe=createRuntimeProbe({now:()=>clock,environment:()=>({browser:'synthetic_test'})});probe.start(1);
 const token=probe.begin('recalculation',{case_id:'new-input',kind:'unlabelled',inputs:{Age:60},truth:1,probability:.8});clock=107;probe.end(token);clock=116;probe.frame(clock,2,true);clock=132;probe.frame(clock,3,true);
 const capture=probe.finish('manual_stop');assert.equal(capture.operations[0].dom_updated_ms,7);assert.equal(capture.operations[0].next_render_callback_ms,16);
 assert.deepEqual(capture.operations[0].metadata,{case_id:'new-input',kind:'unlabelled'});assert.equal(capture.status,'measured');
});
test('Background transitions invalidate foreground FPS; samples are opt-in and bounded',()=>{
 let clock=0;const probe=createRuntimeProbe({now:()=>clock});assert.equal(probe.begin('target'),null);probe.start(1);probe.frame(10,1,true);probe.hidden();probe.frame(20,1,true);assert.equal(probe.finish().status,'invalid_for_foreground_fps');
 assert.throws(()=>probe.start(0));assert.throws(()=>probe.start(60));
});
test('A new capture discards unfinished operations from the old sample',()=>{
 let clock=0;const probe=createRuntimeProbe({now:()=>clock});probe.start(1);const token=probe.begin('old');probe.start(1);clock=10;probe.end(token);probe.frame(10,1,true);probe.frame(20,1,true);assert.equal(probe.finish().operations.length,0);
});
test('The independent deadline ends a capture with no render callbacks',()=>{
 const {probe,timers,setTime,fire}=scheduledProbe();probe.start(1);
 assert.equal(timers.get(1).delayMs,1000);setTime(1000);fire(1);
 const capture=probe.snapshot();assert.equal(capture.active,false);assert.equal(capture.finish_reason,'duration_completed');
 assert.equal(capture.elapsed_ms,1000);assert.equal(capture.leading_frame_gap_ms,1000);assert.equal(capture.trailing_frame_gap_ms,1000);
 assert.equal(capture.status,'invalid_for_foreground_fps');assert.equal(capture.frame_summary.frame_callbacks_per_second,null);
 assert.ok(capture.fps_invalid_reasons.includes('insufficient_frame_callbacks'));assert.equal(timers.size,0);
});
test('Restart cancels its old deadline and a late old timer cannot finish the new capture',()=>{
 const {probe,timers,cancelled,setTime,fire}=scheduledProbe();probe.start(1);
 const oldDeadline=timers.get(1).callback,oldToken=probe.begin('old');setTime(100);probe.start(1);
 assert.deepEqual(cancelled,[1]);assert.equal(timers.get(2).delayMs,1000);
 setTime(1000);oldDeadline();probe.end(oldToken);assert.equal(probe.active,true);assert.equal(probe.snapshot().operations.length,0);
 setTime(1100);fire(2);assert.equal(probe.snapshot().started_at_ms,100);assert.equal(probe.snapshot().elapsed_ms,1000);
});
test('Finish is idempotent and manual stop cancels the pending deadline',()=>{
 const {probe,timers,setTime}=scheduledProbe();probe.start(1);const deadline=timers.get(1).callback;
 setTime(100);const first=probe.finish('manual_stop');setTime(200);const repeated=probe.finish('duration_completed');deadline();
 assert.deepEqual(repeated,first);assert.deepEqual(probe.snapshot(),first);assert.equal(timers.size,0);
});
test('An unfinished action remains exported with null endpoints and elapsed lower bound',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);setTime(16);probe.frame(16,1,true);setTime(32);probe.frame(32,1,true);
 setTime(40);const token=probe.begin('case_or_profile_load',{case_id:'UCI411-057',inputs:{Age:70},probability:.7});
 setTime(1000);fire(1);const capture=probe.snapshot(),operation=capture.operations[0];
 assert.equal(operation.status,'incomplete_at_sample_end');assert.equal(operation.elapsed_ms,960);
 assert.equal(operation.dom_updated_ms,null);assert.equal(operation.next_render_callback_ms,null);
 assert.deepEqual(operation.metadata,{case_id:'UCI411-057'});setTime(1200);probe.end(token);assert.deepEqual(probe.snapshot(),capture);
});
test('DOM completion without a later render callback has a separate incomplete status',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);setTime(16);probe.frame(16,1,true);setTime(32);probe.frame(32,1,true);
 setTime(40);const token=probe.begin('input_recalculation');setTime(100);probe.end(token);setTime(1000);fire(1);
 const operation=probe.snapshot().operations[0];assert.equal(operation.status,'incomplete_render_at_sample_end');
 assert.equal(operation.dom_updated_ms,60);assert.equal(operation.next_render_callback_ms,null);assert.equal(operation.elapsed_ms,960);
});
test('A trailing render stall invalidates foreground rate while retaining raw observations',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);setTime(16);probe.frame(16,1,true);setTime(32);probe.frame(32,1,true);
 setTime(1000);fire(1);const capture=probe.snapshot();
 assert.equal(capture.status,'invalid_for_foreground_fps');assert.equal(capture.trailing_frame_gap_ms,968);
 assert.ok(capture.fps_invalid_reasons.includes('trailing_frame_gap_exceeds_250ms'));
 assert.equal(capture.frame_summary.frame_callbacks_per_second,null);assert.equal(capture.frame_summary.observed_callback_rate_per_second,62.5);
 assert.equal(capture.frame_summary.valid_for_foreground_fps,false);
 assert.deepEqual(capture.frames,[{at_ms:16,callback_cpu_ms:1},{at_ms:32,callback_cpu_ms:1}]);
});
test('A late first frame cannot make a tiny observed subspan a valid whole-sample rate',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);setTime(900);probe.frame(900,1,true);setTime(990);probe.frame(990,1,true);
 setTime(1000);fire(1);const capture=probe.snapshot();assert.equal(capture.leading_frame_gap_ms,900);
 assert.ok(capture.fps_invalid_reasons.includes('leading_frame_gap_exceeds_250ms'));assert.equal(capture.frame_summary.frame_callbacks_per_second,null);
});
test('Boundary coverage of exactly 250 ms remains valid and completed actions keep both endpoints',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);setTime(16);probe.frame(16,1,true);
 setTime(20);const token=probe.begin('target_selection');setTime(25);probe.end(token);setTime(32);probe.frame(32,1,true);
 setTime(750);probe.frame(750,1,true);setTime(1000);fire(1);const capture=probe.snapshot(),operation=capture.operations[0];
 assert.equal(capture.trailing_frame_gap_ms,250);assert.equal(capture.status,'measured');assert.deepEqual(capture.fps_invalid_reasons,[]);
 assert.equal(operation.status,'completed');assert.equal(operation.dom_updated_ms,5);assert.equal(operation.next_render_callback_ms,12);assert.equal(operation.elapsed_ms,12);
});
test('An explicitly hidden start is invalid even without a later visibility transition',()=>{
 let visibility='hidden';const {probe,setTime,fire}=scheduledProbe(()=>({document_visibility:visibility}));probe.start(1);
 visibility='visible';setTime(16);probe.frame(16,1,true);setTime(990);probe.frame(990,1,true);setTime(1000);fire(1);
 assert.equal(probe.snapshot().status,'invalid_for_foreground_fps');assert.ok(probe.snapshot().fps_invalid_reasons.includes('hidden_or_started_hidden'));
});
test('Context loss invalidates a visible well-covered sample and repeated reasons stay unique',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.start(1);probe.invalidate('webgl_context_lost');probe.invalidate('webgl_context_lost');
 setTime(16);probe.frame(16,1,true);setTime(990);probe.frame(990,1,true);setTime(1000);fire(1);
 const capture=probe.snapshot();assert.equal(capture.hidden_transitions,0);assert.equal(capture.status,'invalid_for_foreground_fps');
 assert.deepEqual(capture.fps_invalid_reasons,['webgl_context_lost']);assert.equal(capture.frame_summary.frame_callbacks_per_second,null);
 assert.equal(capture.frame_summary.valid_for_foreground_fps,false);
});
test('Only the allowlisted context-loss reason is collected, and restart clears it',()=>{
 const {probe,setTime,fire}=scheduledProbe();probe.invalidate('webgl_context_lost');probe.start(1);
 assert.throws(()=>probe.invalidate('entered_private_value'),/Unknown runtime invalidation reason/);
 assert.deepEqual(probe.snapshot().fps_invalid_reasons,[]);probe.invalidate('webgl_context_lost');probe.start(1);
 assert.deepEqual(probe.snapshot().fps_invalid_reasons,[]);setTime(1000);fire(2);
});
