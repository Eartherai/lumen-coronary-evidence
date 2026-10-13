import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {renderJourney} from './evidence-journey.js';
import {installAnatomyControls} from './anatomy-controls.js';
import {createStaticApi} from './static-client.js';
import {mountCohortAudit} from './cohort-audit.js';
import {createRuntimeProbe,mountRuntimeProbe} from './runtime-probe.js';
import {describeOutcome} from './outcome-description.js';
import {createAnatomyFrameRenderer} from './anatomy-frame.js';

const $=id=>document.getElementById(id);
const names={CAD:'Overall coronary artery disease',LAD:'Left anterior descending artery',LCX:'Left circumflex artery',RCA:'Right coronary artery'};
const targets=['CAD','LAD','LCX','RCA'];
const pretty={'BP':'Blood pressure','PR':'Pulse rate','EF-TTE':'Ejection fraction','HTN':'Hypertension','DM':'Diabetes','FH':'Family history','Tinversion':'T-wave inversion','Region RWMA':'RWMA region','Length':'Length','FBS':'Fasting blood sugar'};
const esc=v=>String(v??'Missing').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const format=v=>typeof v==='number'?Number(v.toFixed(2)).toString():v==='Fmale'?'Female':String(v??'Missing');
const percent=p=>(100*p).toFixed(1)+'%';
let current,selected='LAD',schema,edited=false,revealed=false,caseVersion=0;
let activeProfile='full',decisionMode='learned',profileCatalog,currentEvidence,newInputReady=false,finalEvidence;
let scene,camera,renderer,controls,anatomy,meshes={},labels={},centers={},rotation=0;
let anatomyControls,journeyData;
let renderAnatomyFrame=()=>false;
let currentViewKey,cohortConsole,caseLoading=false;
let runtimePanel,runtimeEnvironment={};
const runtimeProbe=createRuntimeProbe({environment:()=>({user_agent:navigator.userAgent,platform:navigator.platform,device_pixel_ratio:devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},document_visibility:document.visibilityState,webgl_context_lost:renderer?.getContext().isContextLost()??null,...runtimeEnvironment}),onUpdate:capture=>{runtimePanel?.update(capture);$('runtime-live').hidden=!capture.active;$('runtime-live').textContent=capture.active?`Runtime sample · ${capture.frames.length} callbacks · keep this tab visible`:'';}});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState!=='visible')runtimeProbe.hidden();});
const journeyCache=new Map();
const staticApi=document.querySelector('meta[name="lumen-runtime"]')?.content==='static'?createStaticApi({baseUrl:new URL('./',location.href).href}):null;

async function api(path,options){if(staticApi)return staticApi(path,options);const response=await fetch(path,options);const value=await response.json();if(!response.ok)throw Error(value.error||response.statusText);return value;}
function failAnatomy(error){$('anatomy-status').hidden=false;$('anatomy-status').textContent='Anatomy rendering failed: '+error.message;$('viewer-status').hidden=false;$('viewer-status').textContent='Anatomy unavailable';console.error(error);}
function fail(error){$('error').textContent=error.message;$('error').hidden=false;console.error(error);}
function colorFor(p){return new THREE.Color(p<.5?'#71cebb':'#dfc474').lerp(new THREE.Color(p<.5?'#dfc474':'#e76b5e'),p<.5?p*2:(p-.5)*2);}

async function buildAnatomy(){
  const data=await api('/assets/anatomy.json');
  const container=$('viewer');
  scene=new THREE.Scene(); camera=new THREE.PerspectiveCamera(35,1,.1,2000);
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x000000,0);
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
  container.prepend(renderer.domElement);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=130;controls.maxDistance=550;
  scene.add(new THREE.HemisphereLight(0xd5f1ff,0x243547,2.2));
  for(const [position,intensity,color] of [[[100,130,180],2.8,0xfde2d6],[[-130,30,50],2,0x7ce1ea],[[20,90,-150],2.8,0x598bab]]){const light=new THREE.DirectionalLight(color,intensity);light.position.set(...position);scene.add(light);}
  anatomy=new THREE.Group();scene.add(anatomy);
  const fullBox=new THREE.Box3();
  for(const [key,dataGroup] of Object.entries(data.groups)){
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(dataGroup.positions,3));geometry.setIndex(dataGroup.indices);geometry.computeVertexNormals();geometry.computeBoundingBox();fullBox.union(geometry.boundingBox);
    const material=new THREE.MeshStandardMaterial({color:key==='heart'?0x72929d:0xdfc473,metalness:.12,roughness:.42,transparent:key==='heart',opacity:key==='heart'?.18:1,depthWrite:key!=='heart',side:THREE.DoubleSide});
    const mesh=new THREE.Mesh(geometry,material);mesh.name=key;mesh.renderOrder=key==='heart'?0:1;anatomy.add(mesh);meshes[key]=mesh;
  }
  const center=fullBox.getCenter(new THREE.Vector3());
  for(const [key,mesh] of Object.entries(meshes)){mesh.geometry.translate(-center.x,-center.y,-center.z);mesh.geometry.rotateX(-Math.PI/2);mesh.geometry.computeBoundingBox();centers[key]=mesh.geometry.boundingBox.getCenter(new THREE.Vector3());}
  for(const key of ['LAD','LCX','RCA']){const button=document.createElement('button');button.className='vessel-tag';button.textContent=key;button.onclick=()=>selectTarget(key);button.setAttribute('aria-label','Select '+names[key]);$('vessel-labels').append(button);labels[key]=button;}
  anatomyControls=installAnatomyControls({THREE,camera,controls,meshes,container,onViewChange:()=>renderAnatomyFrame()});resetView();
  const gl=renderer.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info');runtimeEnvironment={webgl_version:gl.getParameter(gl.VERSION),renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),anatomy_triangles:Object.values(meshes).reduce((n,m)=>n+m.geometry.index.count/3,0)};
  const resize=()=>{camera.aspect=container.clientWidth/container.clientHeight;camera.updateProjectionMatrix();renderer.setSize(container.clientWidth,container.clientHeight);renderAnatomyFrame();};new ResizeObserver(resize).observe(container);resize();
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let start;
  renderer.domElement.addEventListener('pointerdown',event=>{start=[event.clientX,event.clientY];});
  renderer.domElement.addEventListener('pointerup',event=>{if(!start||Math.hypot(event.clientX-start[0],event.clientY-start[1])>6)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(['LAD','LCX','RCA'].map(k=>meshes[k]));if(hit.length)selectTarget(hit[0].object.name);});
  let rendered=false,renderFailed=false;
  renderer.domElement.addEventListener('webglcontextlost',()=>{rendered=false;runtimeProbe.invalidate('webgl_context_lost');$('anatomy-status').hidden=false;$('anatomy-status').textContent='Browser graphics context lost. Anatomy rendering is paused.';});
  renderer.domElement.addEventListener('webglcontextrestored',()=>{rendered=false;$('anatomy-status').hidden=false;$('anatomy-status').textContent='Browser graphics context restored. Waiting for a completed anatomy frame.';renderAnatomyFrame();});
  setTimeout(()=>{if(!rendered&&!renderFailed){$('anatomy-status').hidden=false;$('anatomy-status').textContent='No anatomy frame has completed. Keep the browser window visible; if the message persists, this browser has not passed the rendering check.';}},3000);
  const stopRendering=error=>{renderFailed=true;renderer.setAnimationLoop(null);failAnatomy(error);};
  renderAnatomyFrame=createAnatomyFrameRenderer({isContextLost:()=>renderer.getContext().isContextLost(),draw:()=>{
    renderer.render(scene,camera);
    for(const [key,tag] of Object.entries(labels)){const point=centers[key].clone();point.x+=key==='RCA'?-24:key==='LCX'?25:18;point.y+=key==='LAD'?-25:10;point.applyMatrix4(anatomy.matrixWorld).project(camera);tag.style.left=((point.x+1)/2*container.clientWidth)+'px';tag.style.top=((-point.y+1)/2*container.clientHeight)+'px';tag.hidden=point.z>1;}
  },onSuccess:()=>{rendered=true;$('viewer-status').hidden=true;$('anatomy-status').hidden=true;},onFailure:stopRendering});
  // Native controls and the initial view work even if animation callbacks are delayed.
  let animationTick=false;
  controls.addEventListener('change',()=>{if(!animationTick)renderAnatomyFrame();});
  renderer.setAnimationLoop(()=>{try{if(renderer.getContext().isContextLost())return;const began=runtimeProbe.active?performance.now():null;animationTick=true;controls.update();const completed=renderAnatomyFrame();if(completed&&began!==null){const end=performance.now();runtimeProbe.frame(end,end-began,document.visibilityState==='visible');}}catch(error){stopRendering(error);}finally{animationTick=false;}});
  paintAnatomy();
  renderAnatomyFrame();
}
function resetView(){if(!camera)return;camera.position.set(35,22,285);controls.target.set(0,0,0);controls.update();}
function paintAnatomy(){if(!current||!meshes.heart)return;for(const key of ['LAD','LCX','RCA']){meshes[key].material.color.copy(colorFor(current.predictions[key].probability));meshes[key].material.emissive.copy(new THREE.Color(key===selected?'#27524c':'#000000'));meshes[key].material.emissiveIntensity=.55;labels[key].classList.toggle('selected',key===selected);}meshes.heart.visible=$('shell-toggle').checked;anatomyControls?.update(selected);for(const key of ['LAD','LCX','RCA'])labels[key].style.visibility=meshes[key].visible?'visible':'hidden';renderAnatomyFrame();}
function selectTarget(key){const token=runtimeProbe.begin('target_selection',{target:key});selected=key;renderPredictions();paintAnatomy();runtimeProbe.end(token,{case_id:current?.case_id,kind:current?.kind,profile:activeProfile,origin:current?.origin});}

function thresholdFor(prediction){return decisionMode==='fixed'?.5:(prediction.operating_threshold??.5);}
function renderPredictions(){
 if(!current)return;
 const grid=$('prediction-grid'),focusedTarget=grid.contains(document.activeElement)?document.activeElement.dataset.target:null;
 $('prediction-grid').innerHTML=targets.map(key=>{
   const p=current.predictions[key],threshold=thresholdFor(p),flag=p.probability>=threshold;
   return `<button class="prediction-card ${key===selected?'selected':''}" data-target="${key}" aria-pressed="${key===selected}"><span>${key==='CAD'?'Overall CAD':key}</span><strong>${percent(p.probability)}</strong><small>${flag?'Positive research flag':'Below research threshold'}</small></button>`;
 }).join('');
 for(const button of $('prediction-grid').children)button.onclick=()=>selectTarget(button.dataset.target);
 if(focusedTarget)grid.querySelector(`[data-target="${focusedTarget}"]`)?.focus({preventScroll:true});
 const p=current.predictions[selected],threshold=thresholdFor(p);
 $('selected-target').textContent=selected;$('selected-name').textContent=names[selected];$('selected-probability').textContent=percent(p.probability);
 $('model-fold').textContent=current.kind==='unlabelled'?'Frozen development fit':`${edited?'Edited inputs · ':''}Validation fold ${current.fold+1}`;
 $('decision-summary').textContent=`${p.probability>=threshold?'Positive research flag':'Below research threshold'} at ${percent(threshold)}. ${decisionMode==='learned'?'Threshold selected from training-fold predictions.':'Fixed 50% comparison.'} This is a research operating point.`;
 const top=p.contributions.slice(0,6),scale=Math.max(...top.map(c=>Math.abs(c.log_odds_contribution)),.01);
 $('contributions').innerHTML=top.map(c=>{
   const value=c.log_odds_contribution,width=Math.abs(value)/scale*48;
   return `<div class="contribution"><div class="contribution-label"><b>${esc(pretty[c.feature]||c.feature)}</b><span>${esc(format(c.value))}</span></div><div class="contribution-bar"><i style="left:${value>=0?50:50-width}%;width:${width}%;background:${value>=0?'var(--orange)':'var(--blue)'}"></i></div><div class="contribution-value"><span>${value>=0?'Increases':'Decreases'} model estimate</span><span>${value>=0?'+':''}${value.toFixed(2)}</span></div></div>`;
 }).join('');
 const sum=p.contributions.reduce((a,c)=>a+c.log_odds_contribution,0);
 $('calculation').textContent=`Baseline log-odds ${p.baseline_log_odds.toFixed(3)} + sum of all ${p.contributions.length} feature contributions ${sum.toFixed(3)} = ${p.log_odds.toFixed(3)}. Applying the logistic function gives ${percent(p.probability)}. Six largest contributions are shown above; all are included in the sum.`;
 renderWaterfall(p);renderCaseJourney();
 renderCharts();
 if(revealed)renderTruth();
}
function renderInputs(){
 const values=current.inputs;
 $('measurement-heading').textContent=current.kind==='unlabelled'?'Unlabelled inputs':edited?'Edited measurements':'Recorded measurements';
 $('patient-summary').innerHTML=`<div><strong>${esc(format(values.Age))}</strong><span>Age in years</span></div><div><strong>${esc(values.Sex==='Fmale'?'F':values.Sex==='Male'?'M':values.Sex)}</strong><span>Recorded sex</span></div>`;
 const subset=['Weight','BMI','BP','PR','EF-TTE','LDL','Typical Chest Pain','HTN','DM'].filter(k=>k in values);
 const rows=keys=>keys.map(k=>`<div><span>${esc(pretty[k]||k)}</span><strong>${esc(format(values[k]))}</strong></div>`).join('');
 $('measurements').innerHTML=rows(subset);$('all-inputs').innerHTML=rows(Object.keys(values));$('all-inputs').className='measurements';
 $('edit-form').replaceChildren();
 for(const key of schema.feature_order){
   const label=document.createElement('label');label.textContent=pretty[key]||key;
   const cat=schema.categorical.find(f=>f.feature===key),input=document.createElement(cat?'select':'input');input.dataset.feature=key;
   if(cat){for(const value of cat.categories_development){const option=document.createElement('option');option.value=value;option.textContent=format(value);input.append(option);}}
   else{input.type='number';input.step='any';}
   input.value=values[key]??'';label.append(input);$('edit-form').append(label);
 }
}
function setEditing(value){$('edit-form').hidden=!value;$('edit-actions').hidden=!value;$('measurements').hidden=value;$('edit-toggle').textContent=value?'Close editor':'Edit inputs';}
function setCaseChoice(viewKey){
 if(viewKey?.startsWith('audit:')){
  let option=$('case-select').querySelector('[data-audit-option]');
  if(!option){option=document.createElement('option');option.dataset.auditOption='true';$('case-select').append(option);}
  option.value=viewKey;option.textContent='Audit record '+viewKey.slice(6);
 }
 $('case-select').value=viewKey??'';
}
async function loadCase(id,requestedProfile=activeProfile,requestedTarget){
 const sample=runtimeProbe.begin('case_or_profile_load',{profile:requestedProfile});
 const viewKey=id,isAudit=id.startsWith('audit:');
 if(isAudit)id=id.slice(6);
 const route=isAudit?'/api/audit/':'/api/';
 const version=++caseVersion,profile=id==='new-input'?'full':requestedProfile;
 caseLoading=true;$('run-prediction').disabled=true;$('reveal').disabled=true;
 const profileLabel=value=>profileCatalog?.profiles?.find(p=>p.id===value)?.label??value;
 $('case-load-status').hidden=false;
 $('case-load-status').textContent=`Loading ${id==='new-input'?'the unlabelled form':id} with ${profileLabel(profile)}. ${current?`Showing ${current.case_id} with ${profileLabel(current.profile)} until it is ready.`:'Estimates will appear when it is ready.'}`;
 try{
 $('error').hidden=true;
 const [inputSchema,evidence,journey]=await Promise.all([api('/api/schema?profile='+profile),api('/api/evidence?profile='+profile),id==='new-input'?Promise.resolve(null):journeyCache.has(viewKey)?Promise.resolve(journeyCache.get(viewKey)):api(route+'journey/'+encodeURIComponent(id))]);
 let result;
 if(id==='new-input'){
   const inputs={};for(const f of inputSchema.numeric)inputs[f.feature]=f.median_development;
   for(const f of inputSchema.categorical)inputs[f.feature]=f.categories_development[0];
   const response=await api('/api/predict-new',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inputs})});
   result={...response,inputs,fold:null};
 }else result=await api(route+'cases/'+encodeURIComponent(id)+'?profile='+profile);
 if(version!==caseVersion)return false;
 currentViewKey=viewKey;journeyData=journey;if(journey)journeyCache.set(viewKey,journey);
 current=result;schema=inputSchema;activeProfile=profile;currentEvidence=evidence;edited=false;revealed=false;current.truth=null;
 if(requestedTarget!==undefined)selected=requestedTarget;
 setCaseChoice(viewKey);
 $('tour-note').hidden=true;$('tour-note').textContent='';
 $('profile-select').value=profile;$('profile-select').disabled=current.kind==='unlabelled';$('reset-inputs').textContent=current.kind==='unlabelled'?'Restore example defaults':'Restore recorded values';
 const specification=profileCatalog.profiles.find(p=>p.id===profile);
 $('profile-note').textContent=`${specification.label} · ${specification.n_features} model inputs. ${current.kind==='unlabelled'?'Full-input frozen model.':'Separately fitted and validated.'}`;
 $('truth').hidden=true;$('truth').replaceChildren();$('reveal').disabled=current.kind==='unlabelled';
 $('reveal').textContent=current.kind==='unlabelled'?'No recorded outcome':'Reveal recorded labels';
 $('reveal-note').textContent=current.kind==='unlabelled'?'This form starts with illustrative development medians and category defaults. Replace values to explore the frozen model; no outcome is known.':'Compare all four estimates with this case’s recorded angiography labels.';
 $('case-caption').textContent=current.kind==='unlabelled'?'Unlabelled input form · illustrative defaults, not an observed patient.':`${id} · validation fold ${result.fold+1}. This entire fold was excluded from fitting, calibration and threshold selection.${isAudit?' Selected from an outcome-aware development audit.':''}`;
 $('input-status').hidden=current.kind!=='unlabelled';
 $('input-status').textContent=current.kind==='unlabelled'?'Illustrative defaults, not an observed patient. No recorded outcome is available.':'';
 $('shap-scope').textContent=isAudit?'The portable formula was checked against the actual SHAP library on all 4,840 complete-cohort case/profile/target outputs.':'The portable formula was checked against the actual SHAP library on all 160 curated development case/profile/target outputs.';
 setEditing(current.kind==='unlabelled');renderInputs();renderEvidence();renderPredictions();paintAnatomy();
 runtimeProbe.end(sample,{case_id:current.case_id,kind:current.kind,profile,origin:current.origin,target:selected});
 return true;
 }catch(error){
  if(version!==caseVersion)return false;
  activeProfile=current?.profile??'full';setCaseChoice(currentViewKey);
  $('profile-select').value=activeProfile;$('profile-select').disabled=!current||current.kind==='unlabelled';
  renderCaseJourney();
  throw error;
 }finally{if(version===caseVersion){caseLoading=false;$('case-load-status').hidden=true;$('run-prediction').disabled=false;$('reveal').disabled=!current||current.kind==='unlabelled'||edited||revealed;}}
}
function renderCaseJourney(){
 if(!current)return;
 renderJourney({element:$('journey'),journey:journeyData,selected,activeProfile,mode:decisionMode,edited,kind:current.kind,
   onTarget:selectTarget,onProfile:async profile=>{try{if(profile!==activeProfile||caseLoading){$('profile-select').value=profile;if(!await loadCase(currentViewKey,profile))return;}$('explorer').scrollIntoView({behavior:workspaceScrollBehavior(),block:'start'});}catch(error){fail(error);}},
   onRestore:()=>loadCase(currentViewKey).catch(fail)});
}
function renderWaterfall(prediction){
 const top=prediction.contributions.slice(0,6),remaining=prediction.contributions.slice(6).reduce((sum,c)=>sum+c.log_odds_contribution,0);
 let score=prediction.baseline_log_odds;
 const rows=[{name:'Training baseline',from:0,to:score,delta:score,endpoint:true}];
 for(const contribution of top){const from=score;score+=contribution.log_odds_contribution;rows.push({name:pretty[contribution.feature]||contribution.feature,from,to:score,delta:contribution.log_odds_contribution});}
 const beforeRemaining=score;score+=remaining;rows.push({name:`Other ${prediction.contributions.length-top.length} inputs`,from:beforeRemaining,to:score,delta:remaining});
 rows.push({name:'Final log-odds',from:0,to:prediction.log_odds,delta:prediction.log_odds,endpoint:true});
 const low=Math.min(0,...rows.flatMap(r=>[r.from,r.to]))-.3,high=Math.max(0,...rows.flatMap(r=>[r.from,r.to]))+.3,x=value=>140+(value-low)/(high-low)*190;
 $('score-waterfall').innerHTML=`<svg viewBox="0 0 405 335" role="img" aria-label="${esc(`${selected} exact log-odds waterfall. `+rows.map(r=>r.name+': '+r.delta.toFixed(3)).join('; ')+'. Final probability '+percent(prediction.probability))}"><line x1="${x(0)}" y1="15" x2="${x(0)}" y2="291" stroke="var(--muted)" stroke-dasharray="3 3"/>${rows.map((row,i)=>{const y=27+i*29;return `<text x="0" y="${y+4}" fill="var(--muted)" font-size="12">${esc(row.name)}</text><rect x="${x(Math.min(row.from,row.to))}" y="${y-7}" width="${Math.max(Math.abs(x(row.to)-x(row.from)),1)}" height="14" rx="2" fill="${row.endpoint?'var(--mint)':row.delta>=0?'var(--orange)':'var(--blue)'}"/>${i<rows.length-1?`<line x1="${x(row.to)}" y1="${y+7}" x2="${x(row.to)}" y2="${y+22}" stroke="var(--line)" stroke-dasharray="2 2"/>`:''}<text x="398" y="${y+4}" text-anchor="end" fill="var(--text)" font-size="12">${row.delta>=0&&!row.endpoint?'+':''}${row.delta.toFixed(3)}</text>`;}).join('')}<text x="140" y="312" fill="var(--muted)" font-size="12">Additive units: log-odds</text><text x="0" y="334" fill="var(--mint)" font-size="13">Logistic(${prediction.log_odds.toFixed(3)}) = ${percent(prediction.probability)}</text></svg>`;
}
function renderTruth(){
 if(edited||!current.truth)return;
 const truth=current.truth;$('truth').hidden=false;
 $('truth').innerHTML=targets.map(key=>{
   const outcome=describeOutcome(current.predictions[key].probability,thresholdFor(current.predictions[key]),truth[key]);
   return `<div class="truth-row"><b>${key}</b><span>${truth[key]?(key==='CAD'?'CAD recorded':'Stenosis recorded'):'Negative label'} <span class="${outcome.match?'match':'miss'}">· ${outcome.text}</span></span></div>`;
 }).join('');
 $('reveal').textContent='Recorded labels revealed';$('reveal').disabled=true;
 $('reveal-note').textContent=`Agreement uses ${decisionMode==='learned'?'each model’s training-selected threshold':'a fixed 50% threshold'}. Positive means a recorded dataset label.`;
}
async function reveal(){
 if(caseLoading||edited||!current||current.kind==='unlabelled')return;
 const id=current.case_id,viewKey=currentViewKey,version=caseVersion;
 let response;
 try{response=await api((current.origin==='audit'?'/api/audit/labels/':'/api/labels/')+encodeURIComponent(id));}
 catch(error){if(version!==caseVersion||edited||caseLoading||currentViewKey!==viewKey||current.case_id!==id)return;throw error;}
 if(version!==caseVersion||edited||caseLoading||currentViewKey!==viewKey||current.case_id!==id)return;
 current.truth=response.truth;revealed=true;renderTruth();
}
async function recalculate(){
 if(caseLoading||!current)return false;
 const sample=runtimeProbe.begin('input_recalculation',{kind:current.kind,profile:current.profile,case_id:current.case_id,origin:current.origin});
 const inputs={};for(const el of $('edit-form').querySelectorAll('[data-feature]'))inputs[el.dataset.feature]=el.tagName==='SELECT'?el.value:el.value===''?null:Number(el.value);
 const id=current.case_id,viewKey=currentViewKey,profile=current.profile,origin=current.origin,version=caseVersion,isNew=current.kind==='unlabelled';
 const body=isNew?{inputs}:{case_id:id,profile,inputs};
 const ownsRequest=()=>version===caseVersion&&!caseLoading&&currentViewKey===viewKey&&current?.case_id===id&&current.profile===profile&&current.origin===origin;
 let result;
 try{result=await api(isNew?'/api/predict-new':origin==='audit'?'/api/audit/predict':'/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
 catch(error){if(!ownsRequest())return false;throw error;}
 if(!ownsRequest())return false;
 current={...current,inputs,predictions:result.predictions,truth:null};edited=!isNew&&result.changed_features.length>0;revealed=false;
 $('truth').hidden=true;$('reveal').disabled=edited||isNew;
 $('reveal').textContent=isNew?'No recorded outcome':edited?'Restore inputs to compare labels':'Reveal recorded labels';
 $('reveal-note').textContent=isNew?'No observed outcome is associated with these inputs.':edited?'Recorded labels belong to the original case and cannot validate modified measurements.':'Compare predictions with the original recorded labels.';
 const diagnostics=[];
 if(result.outside_development_range.length)diagnostics.push('Outside observed development range: '+result.outside_development_range.join(', '));
 const imputed=[...new Set(Object.values(result.predictions).flatMap(p=>p.imputed_features))];
 const unknown=[...new Set(Object.values(result.predictions).flatMap(p=>p.unknown_categories.map(c=>c.feature)))];
 if(imputed.length)diagnostics.push('Training-fold values imputed: '+imputed.join(', '));
 if(unknown.length)diagnostics.push('Category absent from a training fold: '+unknown.join(', '));
 $('case-caption').textContent=`${isNew?'Unlabelled inputs':result.changed_features.length+' edited inputs'} · four-model inference ${result.elapsed_ms.toFixed(1)} ms${diagnostics.length?' · '+diagnostics.join(' · '):''}.`;
 $('input-status').hidden=false;
 $('input-status').textContent=`${isNew?'Unlabelled inputs have no recorded outcome.':edited?result.changed_features.length+' edited input'+(result.changed_features.length===1?'':'s')+'. Restore recorded values to compare labels.':'Original input values retained; recorded labels can be compared.'}${diagnostics.length?' '+diagnostics.join(' · ')+'.':''}`;
 renderInputs();renderPredictions();paintAnatomy();
 runtimeProbe.end(sample,{target:selected});
 return true;
}
function chosenMetrics(target){
 const summary=currentEvidence.targets[target].oof.logistic;
 return decisionMode==='fixed'&&summary.metrics_at_0_5?{...summary,...summary.metrics_at_0_5}:summary;
}
function renderEvidence(){
 if(!currentEvidence)return;
 const evidence=currentEvidence,p=evidence.protocol;
 $('evaluation-summary').textContent=`${p.n_development} development records · 5 outer validation folds · 3 inner tuning folds · ${p.n_input_features} available inputs. Decisions use ${decisionMode==='learned'?'thresholds selected inside training folds':'a fixed 50% threshold'}.`;
 $('metric-rows').innerHTML=targets.map(key=>{
   const t=evidence.targets[key],m=chosenMetrics(key),confusion=m.confusion_matrix_tn_fp_fn_tp;
   return `<tr><td><b>${key}</b><br><span class="muted">${t.positive_n} positive / ${t.negative_n} negative</span></td><td>${m.roc_auc.toFixed(3)}<br><span class="muted">${m.roc_auc_95_ci_conditional.map(v=>v.toFixed(2)).join('–')}</span></td>${['f1','recall','precision','accuracy','brier'].map(metric=>`<td>${m[metric].toFixed(3)}</td>`).join('')}<td>${confusion[1]} / ${confusion[2]}</td></tr>`;
 }).join('');
 $('method-details').innerHTML=`<p>Inner training-fold log loss selects regularization, class weighting and optional sigmoid calibration. ${decisionMode==='learned'?'Each training fold also chooses an F1 threshold from its inner predictions.':'The displayed decision threshold is fixed at 0.5.'} Outer validation evaluates the complete selection procedure. All four target columns are excluded.</p><p>LCX/RCA recall is ${percent(chosenMetrics('LCX').recall)}/${percent(chosenMetrics('RCA').recall)}, with precision ${percent(chosenMetrics('LCX').precision)}/${percent(chosenMetrics('RCA').precision)}. False positives and false negatives are both shown. These operating points are research choices.</p><p>AUC intervals bootstrap fixed out-of-fold predictions and omit refitting/experiment-selection uncertainty. V2 was designed after inspecting V1 development results. A sigmoid calibration step does not establish calibrated individual probabilities.</p><p>${evidence.development_audit.cad_vs_any_vessel_label_disagreements} development record has inconsistent overall/vessel labels; labels were retained. Each availability profile was separately refitted on the same folds. Comparisons are exploratory and do not establish the clinical value or order of tests.</p>`;
 renderCharts();
}
function renderCharts(){
 if(!currentEvidence||!current)return;
 const bins=currentEvidence.targets[selected].oof.logistic.calibration_bins.filter(b=>b.n>0);
 const x=p=>45+p*275,y=p=>210-p*175;
 const grid=[0,.25,.5,.75,1].map(v=>`<line x1="45" y1="${y(v)}" x2="320" y2="${y(v)}" stroke="var(--line)"/><text x="36" y="${y(v)+4}" text-anchor="end">${v}</text><text x="${x(v)}" y="230" text-anchor="middle">${v}</text>`).join('');
 $('reliability-chart').innerHTML=`<svg viewBox="0 0 360 265" role="img" aria-label="${selected} development probability reliability: ${bins.map(b=>`${b.n} records, mean estimate ${percent(b.mean_probability)}, observed ${percent(b.observed_fraction)}`).join('; ')}"><g fill="var(--muted)" font-size="11">${grid}<line x1="45" y1="210" x2="320" y2="35" stroke="var(--mint)" stroke-dasharray="5 5"/><polyline points="${bins.map(b=>`${x(b.mean_probability)},${y(b.observed_fraction)}`).join(' ')}" fill="none" stroke="var(--orange)" stroke-width="2"/>${bins.map(b=>`<circle cx="${x(b.mean_probability)}" cy="${y(b.observed_fraction)}" r="5" fill="var(--orange)"><title>n=${b.n}</title></circle><text x="${x(b.mean_probability)}" y="${y(b.observed_fraction)-10}" text-anchor="middle">n=${b.n}</text>`).join('')}<text x="182" y="254" text-anchor="middle">Mean model probability · ${selected}</text><text x="45" y="19">Observed positive fraction</text></g></svg>`;
 const availability=profileCatalog?.availability_evidence;
 if(!availability){$('availability-comparison').textContent='Availability validation is loading.';return;}
 $('availability-comparison').innerHTML=`<table class="availability-table"><thead><tr><th>${selected} profile</th><th>AUC</th><th>F1</th></tr></thead><tbody>${profileCatalog.profiles.map(profile=>{const m=availability.profiles[profile.id].targets[selected].oof.logistic;const metrics=decisionMode==='fixed'?m.metrics_at_0_5:m;return `<tr class="${profile.id===activeProfile?'active-profile':''}"><td><button data-profile="${profile.id}">${esc(profile.label)}<span class="muted"> · ${profile.n_features}</span></button></td><td>${m.roc_auc.toFixed(3)}</td><td>${metrics.f1.toFixed(3)}</td></tr>`;}).join('')}</tbody></table>`;
 for(const button of $('availability-comparison').querySelectorAll('button'))button.onclick=()=>{if(current.kind==='unlabelled')return;const profile=button.dataset.profile;$('profile-select').value=profile;loadCase(currentViewKey,profile).catch(fail);};
}
function renderFinalEvaluation(evaluation){
 if(evaluation)finalEvidence=evaluation;
 if(!finalEvidence||finalEvidence.available===false||!finalEvidence.targets)return;
 const data=finalEvidence;$('final-validation').hidden=false;
 $('final-summary').textContent=`${data.n_holdout} held-out records · frozen full 55-input procedure. Displayed operating rule: ${decisionMode==='learned'?'training-selected research thresholds':'prespecified fixed 50% comparison'}. Intervals condition on fixed models and omit training uncertainty.`;
 $('final-results').innerHTML=`<table><thead><tr><th>Target</th><th>ROC-AUC</th><th>F1</th><th>Recall</th><th>Precision</th><th>Accuracy</th><th>Brier</th><th>FP / FN</th><th>Threshold</th></tr></thead><tbody>${targets.map(key=>{
   const row=data.targets[key],m=decisionMode==='fixed'?row.metrics_at_0_5:row.metrics;
   return `<tr><td><b>${key}</b><br><span class="muted">${row.n_positive} positive / ${row.n_negative} negative</span></td><td>${m.roc_auc.toFixed(3)}<br><span class="muted">${m.roc_auc_95_ci_conditional.map(v=>v.toFixed(2)).join('–')}</span></td>${['f1','recall','precision','accuracy','brier'].map(k=>`<td>${m[k].toFixed(3)}</td>`).join('')}<td>${m.confusion_counts.fp} / ${m.confusion_counts.fn}</td><td>${percent(m.classification_threshold)}</td></tr>`;
 }).join('')}</tbody></table>`;
}
$('reset-view').onclick=resetView;$('shell-toggle').onchange=paintAnatomy;
$('case-select').onchange=e=>{if(current)loadCase(e.target.value).catch(fail);};
$('profile-select').onchange=e=>{if(current)loadCase(currentViewKey,e.target.value).catch(fail);};
function setDecisionMode(mode){const token=runtimeProbe.begin('decision_rule_change');decisionMode=mode;$('decision-rule').value=mode;renderPredictions();renderEvidence();renderFinalEvaluation();cohortConsole?.update();runtimeProbe.end(token,{target:selected,profile:activeProfile,case_id:current?.case_id,kind:current?.kind});}
$('decision-rule').onchange=e=>setDecisionMode(e.target.value);
$('edit-toggle').onclick=()=>setEditing($('edit-form').hidden);
$('reset-inputs').onclick=()=>loadCase(currentViewKey).catch(fail);
$('run-prediction').onclick=async()=>{const version=caseVersion;$('run-prediction').disabled=true;try{await recalculate();}catch(error){if(version===caseVersion&&!caseLoading)fail(error);}finally{if(version===caseVersion&&!caseLoading)$('run-prediction').disabled=false;}};
$('reveal').onclick=()=>reveal().catch(fail);
const workspaceNavigation=[['case-nav','explorer'],['journey-nav','journey'],['audit-nav','cohort-audit'],['validation-nav','validation']];
function markWorkspaceSection(section){
 for(const [buttonId,sectionId] of workspaceNavigation){
  const button=$(buttonId),active=sectionId===section;
  button.classList.toggle('active',active);
  if(active)button.setAttribute('aria-current','location');else button.removeAttribute('aria-current');
 }
}
function workspaceScrollBehavior(){
 return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'instant':'smooth';
}
function navigateWorkspace(section){
 markWorkspaceSection(section);
 $(section).scrollIntoView({behavior:workspaceScrollBehavior(),block:'start'});
}
for(const [buttonId,sectionId] of workspaceNavigation)$(buttonId).onclick=()=>navigateWorkspace(sectionId);
$('view-comparison').onclick=$('journey-nav').onclick;
$('tour-audit').onclick=$('audit-nav').onclick;
let navigationObserver;
function observeWorkspaceNavigation(){
 navigationObserver?.disconnect();
 const top=document.querySelector('header').getBoundingClientRect().height+20;
 const bottom=Math.max(0,window.innerHeight-top-80);
 navigationObserver=new IntersectionObserver(entries=>{
  for(const entry of entries){
   if(entry.isIntersecting){
    const section=entry.target.id==='final-validation'?'validation':entry.target.id;
    markWorkspaceSection(section);
   }
  }
 },{rootMargin:`-${top}px 0px -${bottom}px 0px`,threshold:0});
 for(const [,sectionId] of workspaceNavigation)navigationObserver.observe($(sectionId));
 navigationObserver.observe($('final-validation'));
}
observeWorkspaceNavigation();
window.addEventListener('resize',observeWorkspaceNavigation);
async function openAuditCase(id,target){
 try{
  const key='audit:'+id,version=caseVersion+1;if(!await loadCase(key,'full',target))return;
  if(version!==caseVersion||currentViewKey!==key)return;
  await reveal();if(version!==caseVersion||currentViewKey!==key)return;$('score-detail').open=false;
  $('tour-note').hidden=false;$('tour-note').textContent=`${id} was chosen using recorded development outcomes. Its fold-excluded predictions and actual labels are shown together. Editing inputs explores the model and removes the outcome comparison.`;
  $('explorer').scrollIntoView({behavior:workspaceScrollBehavior(),block:'start'});
 }catch(error){fail(error);}
}
async function runTour(step){
 const specification=step==='compare'?{id:'UCI411-128',profile:'history',target:'LAD'}:step==='miss'?{id:'UCI411-288',profile:'full',target:'LCX'}:{id:'UCI411-171',profile:'full',target:'LAD'};
 const version=caseVersion+1;if(!await loadCase(specification.id,specification.profile,specification.target)||version!==caseVersion)return;
 setDecisionMode('learned');
 const isolation=$('explorer').querySelector('.anatomy-isolate input');if(isolation)isolation.checked=false;paintAnatomy();resetView();
 $('tour-note').hidden=false;$('tour-note').textContent=step==='compare'?'Compare the LAD row: its flag changes across separately fitted profiles. Select any cell to synchronize the anatomy and explanation. These are examples from the seeded case set, not a population summary.':step==='miss'?'This original case has a recorded positive LCX label that the full-input model misses. A compelling visualization does not remove the error.':'Select LAD on the anatomy, focus or isolate it, then follow the exact baseline-to-score calculation.';
 if(step==='miss'){await reveal();if(version!==caseVersion)return;}
 if(step==='trace'){$('score-detail').open=true;$('explorer').scrollIntoView({behavior:workspaceScrollBehavior(),block:'start'});}
 else if(step==='compare')$('journey').scrollIntoView({behavior:workspaceScrollBehavior(),block:'start'});
 else $('reveal').scrollIntoView({behavior:workspaceScrollBehavior(),block:'center'});
}
for(const step of ['trace','compare','miss'])$('tour-'+step).onclick=async()=>{const buttons=['trace','compare','miss'].map(s=>$('tour-'+s));buttons.forEach(b=>b.disabled=true);try{await runTour(step);}catch(error){fail(error);}finally{buttons.forEach(b=>b.disabled=false);}};
window.addEventListener('hashchange',()=>{if(location.hash==='#compare'&&current)runTour('compare').catch(fail);});
buildAnatomy().catch(failAnatomy);
runtimePanel=mountRuntimeProbe({element:$('runtime-panel'),onStart:()=>{runtimeProbe.start(10);$('explorer').scrollIntoView({behavior:'instant',block:'start'});},onStop:()=>runtimeProbe.finish('manual_stop'),onExport:()=>{const capture=runtimeProbe.snapshot();if(!capture||capture.active)return;const url=URL.createObjectURL(new Blob([JSON.stringify(capture,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='lumen-runtime-sample.json';link.click();URL.revokeObjectURL(url);}});
try{
 const [catalog,profiles,evaluation]=await Promise.all([api('/api/cases'),api('/api/profiles'),api('/api/final-evaluation')]);
 profileCatalog=profiles;newInputReady=catalog.new_input_ready;
 $('profile-select').replaceChildren();
 for(const profile of profiles.profiles){const option=document.createElement('option');option.value=profile.id;option.textContent=`${profile.label} · ${profile.n_features} inputs`;$('profile-select').append(option);}
 $('profile-select').value='full';
 for(const c of catalog.cases){const option=document.createElement('option');option.value=c.case_id;option.textContent=c.case_id;$('case-select').append(option);}
 if(newInputReady){const option=document.createElement('option');option.value='new-input';option.textContent='Unlabelled input form';$('case-select').append(option);}
 $('case-select').remove(0);renderFinalEvaluation(evaluation);await loadCase(catalog.cases[0].case_id);$('case-select').disabled=false;$('profile-select').disabled=false;
 const [audit,certificate]=await Promise.all([api('/api/audit'),api('/assets/cohort-audit-verification.json')]);
 cohortConsole=mountCohortAudit({element:$('cohort-audit'),audit,profiles:profiles.profiles,certificate,getMode:()=>decisionMode,onMode:setDecisionMode,onInspect:openAuditCase});
 if(location.hash==='#compare')await runTour('compare');
}catch(error){fail(error);}
