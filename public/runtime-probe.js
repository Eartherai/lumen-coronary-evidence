/** Opt-in local measurements. No clinical inputs, predictions or outcomes are recorded. */
const percentile=(values,q)=>{
  if(!values.length)return null;
  const sorted=[...values].sort((a,b)=>a-b),position=(sorted.length-1)*q,low=Math.floor(position),high=Math.ceil(position);
  return sorted[low]+(sorted[high]-sorted[low])*(position-low);
};
export function summarizeFrames(frames){
  const intervals=frames.slice(1).map((frame,i)=>frame.at_ms-frames[i].at_ms);
  const span=frames.length>1?frames.at(-1).at_ms-frames[0].at_ms:0;
  return {n_frame_callbacks:frames.length,observed_span_ms:span,
    frame_callbacks_per_second:span>0?1000*(frames.length-1)/span:null,
    interval_ms:{median:percentile(intervals,.5),p95:percentile(intervals,.95),maximum:intervals.length?Math.max(...intervals):null},
    callback_cpu_ms:{median:percentile(frames.map(f=>f.callback_cpu_ms),.5),p95:percentile(frames.map(f=>f.callback_cpu_ms),.95)},
    intervals_over_33_34ms:intervals.filter(v=>v>33.34).length,
    interpretation:'Foreground animation callbacks and main-thread render submission only; no GPU-completion or physical-display measurement.'};
}
const allowedMeta=meta=>Object.fromEntries(['case_id','kind','profile','target','origin'].filter(k=>typeof meta?.[k]==='string').map(k=>[k,meta[k]]));
export function createRuntimeProbe({
  now=()=>performance.now(),environment=()=>({}),onUpdate=()=>{},
  schedule=(callback,delayMs)=>setTimeout(callback,delayMs),cancel=id=>clearTimeout(id),
}={}){
  const coverageLimitMs=250;
  let capture=null,nextId=0,timer=null;const tokens=new Map(),pending=[];
  function clearTimer(){if(timer!==null){cancel(timer);timer=null;}}
  function finish(reason='duration_completed'){
    if(!capture)return null;
    if(!capture.active)return structuredClone(capture);
    clearTimer();
    capture.finished_at_ms=now();capture.finish_reason=reason;
    capture.elapsed_ms=Math.max(0,capture.finished_at_ms-capture.started_at_ms);
    capture.leading_frame_gap_ms=capture.frames.length?Math.max(0,capture.frames[0].at_ms-capture.started_at_ms):capture.elapsed_ms;
    capture.trailing_frame_gap_ms=capture.frames.length?Math.max(0,capture.finished_at_ms-capture.frames.at(-1).at_ms):capture.elapsed_ms;
    for(const operation of capture.operations){
      if(operation.status==='pending'||operation.status==='awaiting_render_callback'){
        operation.status=operation.status==='pending'?'incomplete_at_sample_end':'incomplete_render_at_sample_end';
        operation.elapsed_ms=Math.max(0,capture.finished_at_ms-operation.started_at_ms);
      }
    }
    tokens.clear();pending.splice(0);
    capture.environment_end=environment();capture.active=false;
    const reasons=[...capture.fps_invalid_reasons];
    if(capture.hidden_transitions||capture.environment_start.document_visibility==='hidden'||capture.environment_end.document_visibility==='hidden')reasons.push('hidden_or_started_hidden');
    if(capture.frames.length<2)reasons.push('insufficient_frame_callbacks');
    if(capture.leading_frame_gap_ms>coverageLimitMs)reasons.push('leading_frame_gap_exceeds_250ms');
    if(capture.trailing_frame_gap_ms>coverageLimitMs)reasons.push('trailing_frame_gap_exceeds_250ms');
    capture.fps_invalid_reasons=reasons;capture.frame_coverage_limit_ms=coverageLimitMs;
    capture.status=reasons.length?'invalid_for_foreground_fps':'measured';
    capture.frame_summary=summarizeFrames(capture.frames);
    capture.frame_summary.observed_callback_rate_per_second=capture.frame_summary.frame_callbacks_per_second;
    capture.frame_summary.valid_for_foreground_fps=reasons.length===0;
    if(reasons.length)capture.frame_summary.frame_callbacks_per_second=null;
    onUpdate(capture);return structuredClone(capture);
  }
  function start(seconds=10){
    if(!Number.isFinite(seconds)||seconds<1||seconds>30)throw Error('Capture duration must be 1–30 seconds');
    clearTimer();
    tokens.clear();pending.splice(0);
    capture={schema:'lumen-local-runtime-sample-v1',created_utc:new Date().toISOString(),active:true,status:'recording',
      requested_duration_ms:seconds*1000,started_at_ms:now(),hidden_transitions:0,fps_invalid_reasons:[],frames:[],operations:[],environment_start:environment(),
      scope:'Opt-in software measurement on this browser/device; not a human usability study, clinical validation or hosted benchmark.',
      privacy:'No entered clinical values, probabilities or recorded outcomes are collected. Only operation names and public case/profile/target identifiers.'};
    const startedCapture=capture;
    timer=schedule(()=>{if(capture===startedCapture&&capture.active)finish();},seconds*1000);
    onUpdate(capture);return structuredClone(capture);
  }
  function begin(name,metadata={}){
    if(!capture?.active)return null;
    const token=++nextId,operation={name,metadata:allowedMeta(metadata),started_at_ms:now(),
      status:'pending',dom_updated_ms:null,next_render_callback_ms:null,elapsed_ms:null};
    tokens.set(token,operation);capture.operations.push(operation);return token;
  }
  function end(token,metadata={}){
    if(token===null||!tokens.has(token))return;
    const operation=tokens.get(token);tokens.delete(token);
    if(!capture?.active)return;
    Object.assign(operation,{metadata:{...operation.metadata,...allowedMeta(metadata)},
      dom_updated_ms:now()-operation.started_at_ms,status:'awaiting_render_callback'});
    pending.push(operation);
  }
  function frame(at,callbackCpuMs,visible=true){
    if(!capture?.active)return;
    if(!visible){capture.hidden_transitions++;return;}
    if(!Number.isFinite(at)||!Number.isFinite(callbackCpuMs)||callbackCpuMs<0)return;
    if(capture.frames.length&&at<=capture.frames.at(-1).at_ms)return;
    if(capture.frames.length<5000)capture.frames.push({at_ms:at,callback_cpu_ms:callbackCpuMs});
    for(const operation of pending.splice(0)){
      operation.next_render_callback_ms=at-operation.started_at_ms;
      operation.elapsed_ms=operation.next_render_callback_ms;operation.status='completed';
    }
    if(at-capture.started_at_ms>=capture.requested_duration_ms)finish();
    else if(capture.frames.length%15===0)onUpdate(capture);
  }
  function invalidate(reason){
    if(reason!=='webgl_context_lost')throw Error('Unknown runtime invalidation reason');
    if(capture?.active&&!capture.fps_invalid_reasons.includes(reason))capture.fps_invalid_reasons.push(reason);
  }
  return {start,begin,end,frame,finish,invalidate,hidden(){if(capture?.active)capture.hidden_transitions++;},get active(){return Boolean(capture?.active);},snapshot(){return capture?structuredClone(capture):null;}};
}
export function mountRuntimeProbe({element,onStart,onStop,onExport}){
  element.innerHTML=`<summary>Measure this browser’s runtime</summary><div class="runtime-body"><p>Record a 10-second foreground sample while using the anatomy, case and profile controls. This measures animation callbacks and the time from an action to DOM updates/the next completed render callback. It does not measure physical display latency or validate medical predictions.</p><div class="runtime-actions"><button class="secondary" data-runtime-start>Record 10 seconds</button><button class="secondary" data-runtime-stop disabled>Stop sample</button><button class="secondary" data-runtime-export disabled>Export measured JSON</button></div><p class="muted" data-runtime-status>No sample recorded. Inputs, estimates and outcomes are excluded from the diagnostic.</p><p class="muted" data-runtime-diagnostic hidden></p><p class="muted" data-runtime-environment hidden></p><pre data-runtime-result hidden></pre></div>`;
  const find=s=>element.querySelector(s);find('[data-runtime-start]').onclick=onStart;find('[data-runtime-stop]').onclick=onStop;find('[data-runtime-export]').onclick=onExport;
  return {update(capture){
    const active=capture?.active;find('[data-runtime-start]').disabled=Boolean(active);find('[data-runtime-stop]').disabled=!active;find('[data-runtime-export]').disabled=!capture||Boolean(active);
    const completed=capture?.operations.filter(operation=>operation.status==='completed').length??0;
    find('[data-runtime-status]').textContent=active?`Recording ${capture.frames.length} render callbacks. Keep this tab in the foreground and use the case/artery controls.`:capture?`${capture.status==='measured'?'Sample measured':'Foreground FPS sample invalid'} · ${capture.frames.length} callbacks · ${completed}/${capture.operations.length} actions completed. Read the measurement scope before interpreting these values.`:'No sample recorded.';
    const result=find('[data-runtime-result]');result.hidden=!capture||Boolean(active);
    const diagnostic=find('[data-runtime-diagnostic]'),environmentText=find('[data-runtime-environment]');
    diagnostic.hidden=environmentText.hidden=!capture||Boolean(active);
    if(capture&&!active){
      const ms=value=>Number.isFinite(value)?`${value.toFixed(1)} ms`:'unavailable';
      diagnostic.textContent=`Status: ${capture.status}. Hidden transitions: ${capture.hidden_transitions}. Elapsed: ${ms(capture.elapsed_ms)}. Leading/trailing frame gaps: ${ms(capture.leading_frame_gap_ms)} / ${ms(capture.trailing_frame_gap_ms)}.`;
      const start=capture.environment_start,end=capture.environment_end;
      environmentText.textContent=`Visibility start/end: ${start.document_visibility??'unknown'} / ${end.document_visibility??'unknown'}. WebGL: ${end.webgl_version??start.webgl_version??'unavailable'}. Renderer: ${end.renderer??start.renderer??'unavailable'}.`;
    }
    if(capture&&!active)result.textContent=JSON.stringify({status:capture.status,elapsed_ms:capture.elapsed_ms,
      leading_frame_gap_ms:capture.leading_frame_gap_ms,trailing_frame_gap_ms:capture.trailing_frame_gap_ms,
      fps_invalid_reasons:capture.fps_invalid_reasons,frame_summary:capture.frame_summary,
      operations:capture.operations.map(o=>({name:o.name,metadata:o.metadata,status:o.status,elapsed_ms:o.elapsed_ms,dom_updated_ms:o.dom_updated_ms,next_render_callback_ms:o.next_render_callback_ms})),
      hidden_transitions:capture.hidden_transitions,environment_start:capture.environment_start},null,2);
  }};
}
