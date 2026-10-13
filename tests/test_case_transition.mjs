/** Actual app transition functions with synthetic delayed API/DOM fixtures.
 * This covers request ownership and UI identity, without scoring patient data.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
const transitions=source.slice(source.indexOf('function setCaseChoice(viewKey){'),source.indexOf('function renderCaseJourney(){'));
const revealSource=source.slice(source.indexOf('async function reveal(){'),source.indexOf('async function recalculate(){'));
const scrollBehaviorSource=source.slice(source.indexOf('function workspaceScrollBehavior(){'),source.indexOf('function navigateWorkspace(section){'));
assert.ok(transitions.startsWith('function setCaseChoice(viewKey){'));
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
function fixture(api){
 const elements=new Map();let restoredJourney=0;
 const element=id=>{
  if(!elements.has(id))elements.set(id,{value:'',hidden:false,disabled:false,textContent:'',options:[],
   replaceChildren(){},append(option){this.options.push(option);},querySelector(){return this.options.find(option=>option.dataset.auditOption);},querySelectorAll(){return [];},scrollIntoView(options){this.lastScrollOptions=options;}});
  return elements.get(id);
 };
 const ctx=vm.createContext({api,$:element,console,Error,window:{matchMedia(){return {matches:false};}},runtimeProbe:{begin(){return null;},end(){}},
  document:{createElement(){return {dataset:{},value:'',textContent:''};}},
  renderInputs(){},renderEvidence(){},renderPredictions(){},paintAnatomy(){},setEditing(){},renderTruth(){},selectTarget(){},renderCaseJourney(){restoredJourney++;}});
 vm.runInContext(`let current={case_id:'OLD',kind:'development',profile:'full',fold:0}, currentViewKey='OLD', schema,
 currentEvidence={profile:'full'},activeProfile='full',caseVersion=0,caseLoading=false,edited=false,revealed=false,journeyData,selected='LAD',decisionMode='learned';
 const journeyCache=new Map(),profileCatalog={profiles:[{id:'full',n_features:55},{id:'history',n_features:17}]};
 ${transitions}${revealSource}${scrollBehaviorSource}`,ctx);
 element('case-select').value='OLD';element('profile-select').value='full';element('case-caption').textContent='OLD · existing case';element('error').hidden=true;
 return {ctx,element,run:code=>vm.runInContext(code,ctx),restoredJourney:()=>restoredJourney};
}
async function successfulApi(path){
 const profile=new URL(path,'http://fixture.local').searchParams.get('profile')??'full';
 if(path.startsWith('/api/schema'))return {profile};
 if(path.startsWith('/api/evidence'))return {profile};
 if(path.includes('/journey/'))return {case_id:path.split('/').at(-1)};
 return {case_id:path.split('/').at(-1).split('?')[0],kind:'development',profile,fold:0,inputs:{}};
}

test('A pending profile request preserves the committed model identity until data is complete',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/schema?profile=history'?gate.promise:successfulApi(path));
 f.element('profile-select').value='history';const pending=f.run(`loadCase('OLD','history')`);
 assert.equal(f.run('activeProfile'),'full');assert.equal(f.run('current.profile'),'full');assert.equal(f.run('caseLoading'),true);
 assert.equal(f.element('case-load-status').hidden,false);assert.match(f.element('case-load-status').textContent,/Loading OLD with history.*Showing OLD with full/);
 gate.resolve({profile:'history'});assert.equal(await pending,true);
 assert.equal(f.run('activeProfile'),'history');assert.equal(f.run('current.profile'),'history');assert.equal(f.run('currentEvidence.profile'),'history');
 assert.equal(f.element('profile-select').value,'history');assert.equal(f.run('caseLoading'),false);
 assert.equal(f.element('case-load-status').hidden,true);
});
test('Failure restores the committed case/profile selectors and retains original edit/label state',async()=>{
 const f=fixture(async()=>{throw Error('Synthetic current failure');});
 f.run(`edited=true;revealed=true;`);f.element('case-select').value='NEW';f.element('profile-select').value='history';
 await assert.rejects(f.run(`loadCase('NEW','history','RCA')`),/Synthetic current failure/);
 assert.equal(f.run('current.case_id'),'OLD');assert.equal(f.run('current.profile'),'full');assert.equal(f.run('activeProfile'),'full');
 assert.equal(f.element('case-select').value,'OLD');assert.equal(f.element('profile-select').value,'full');
 assert.equal(f.run('selected'),'LAD');assert.equal(f.run('edited'),true);assert.equal(f.run('revealed'),true);
 assert.equal(f.element('reveal').disabled,true);assert.equal(f.run('caseLoading'),false);assert.equal(f.restoredJourney(),1);
});
test('A superseded failure does not reject into a caller that could show a stale error',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/journey/A'?gate.promise:successfulApi(path));
 const old=f.run(`loadCase('A','history','LCX')`);assert.equal(await f.run(`loadCase('B','full','RCA')`),true);
 gate.reject(Error('Synthetic superseded failure'));assert.equal(await old,false);
 assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('current.profile'),'full');assert.equal(f.run('selected'),'RCA');
 assert.equal(f.element('case-select').value,'B');assert.equal(f.element('error').hidden,true);assert.equal(f.restoredJourney(),0);
});
test('A superseded success cannot overwrite the newer complete case/profile/target',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/journey/A'?gate.promise:successfulApi(path));
 const old=f.run(`loadCase('A','full','LCX')`);await f.run(`loadCase('B','history','RCA')`);
 gate.resolve({case_id:'A'});assert.equal(await old,false);
 assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('activeProfile'),'history');assert.equal(f.run('selected'),'RCA');
 assert.equal(f.element('case-select').value,'B');assert.equal(f.element('profile-select').value,'history');
});
test('Rollback restores a previous audit record even though there is one dynamic audit option',async()=>{
 const f=fixture(async()=>{throw Error('Synthetic audit failure');});
 f.run(`current.case_id='AUDIT-OLD';current.origin='audit';currentViewKey='audit:AUDIT-OLD';setCaseChoice(currentViewKey);`);
 f.run(`setCaseChoice('audit:AUDIT-NEW')`);assert.equal(f.element('case-select').options.length,1);
 await assert.rejects(f.run(`loadCase('audit:AUDIT-NEW','history')`),/Synthetic audit failure/);
 assert.equal(f.element('case-select').value,'audit:AUDIT-OLD');assert.equal(f.element('case-select').options.length,1);
 assert.equal(f.element('case-select').options[0].value,'audit:AUDIT-OLD');
 assert.equal(f.element('case-select').options[0].textContent,'Audit record AUDIT-OLD');
});
test('A stale request does not release loading controls owned by a newer pending request',async()=>{
 const oldGate=deferred(),newGate=deferred(),f=fixture(path=>path==='/api/journey/A'?oldGate.promise:path==='/api/journey/B'?newGate.promise:successfulApi(path));
 const old=f.run(`loadCase('A')`),latest=f.run(`loadCase('B','history')`);
 oldGate.reject(Error('Synthetic superseded failure'));assert.equal(await old,false);
 assert.equal(f.run('caseLoading'),true);assert.equal(f.element('run-prediction').disabled,true);assert.equal(f.element('reveal').disabled,true);
 assert.equal(f.element('case-load-status').hidden,false);assert.match(f.element('case-load-status').textContent,/Loading B/);
 newGate.resolve({case_id:'B'});await latest;assert.equal(f.run('caseLoading'),false);assert.equal(f.element('run-prediction').disabled,false);
});
test('A stale recorded-label error is discarded after a newer case commits',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/labels/OLD'?gate.promise:successfulApi(path));
 const old=f.run('reveal()');await f.run(`loadCase('B')`);gate.reject(Error('Synthetic stale label failure'));
 await assert.doesNotReject(old);assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('current.truth'),null);assert.equal(f.run('revealed'),false);
});
test('A current recorded-label failure still reaches the caller for an explicit error',async()=>{
 const f=fixture(async()=>{throw Error('Synthetic current label failure');});
 await assert.rejects(f.run('reveal()'),/Synthetic current label failure/);assert.equal(f.run('current.case_id'),'OLD');assert.equal(f.run('revealed'),false);
});
test('A successful old label response cannot reveal outcomes on a newly committed record',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/labels/OLD'?gate.promise:successfulApi(path));
 const old=f.run('reveal()');await f.run(`loadCase('B')`);gate.resolve({truth:{CAD:1,LAD:1,LCX:1,RCA:1}});await old;
 assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('current.truth'),null);assert.equal(f.run('revealed'),false);
});
test('A requested tour target is committed with its record, never during a pending load',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/journey/NEW'?gate.promise:successfulApi(path));
 const pending=f.run(`loadCase('NEW','history','RCA')`);assert.equal(f.run('selected'),'LAD');assert.equal(f.run('activeProfile'),'full');
 gate.resolve({case_id:'NEW'});await pending;assert.equal(f.run('selected'),'RCA');assert.equal(f.run('current.case_id'),'NEW');assert.equal(f.run('activeProfile'),'history');
});
test('Returning to the currently committed profile through the matrix supersedes a pending different profile',async()=>{
 const gate=deferred(),requests=[],f=fixture(path=>{requests.push(path);return path==='/api/schema?profile=history'?gate.promise:successfulApi(path);});
 let options;f.ctx.renderJourney=value=>{options=value;};f.ctx.fail=error=>{throw error;};
 const actual=source.slice(source.indexOf('function renderCaseJourney(){'),source.indexOf('function renderWaterfall(prediction){'));
 f.run(actual+';renderCaseJourney();');const callback=options.onProfile;
 const history=callback('history');assert.equal(f.run('activeProfile'),'full');assert.equal(f.run('caseLoading'),true);
 f.ctx.window.matchMedia=()=>({matches:true});
 await callback('full');assert.equal(f.run('current.profile'),'full');assert.equal(f.run('caseLoading'),false);
 assert.equal(f.element('explorer').lastScrollOptions.behavior,'instant');
 assert.ok(requests.includes('/api/schema?profile=full'));
 gate.resolve({profile:'history'});await history;assert.equal(f.run('current.profile'),'full');assert.equal(f.run('activeProfile'),'full');
});

function installPredictionHandler(f){
 const errors=[];
 f.ctx.fail=error=>{errors.push(error.message);};
 const recalculate=source.slice(source.indexOf('async function recalculate(){'),source.indexOf('function chosenMetrics(target){'));
 const click=source.slice(source.indexOf("$('run-prediction').onclick=async()=>"),source.indexOf("$('reveal').onclick="));
 assert.ok(recalculate.startsWith('async function recalculate(){'));
 assert.ok(click.startsWith("$('run-prediction').onclick=async()=>"));
 f.run(recalculate+click);
 return errors;
}
test('A rejected old input prediction cannot display its error over a newer loaded case',async()=>{
 const predictionGate=deferred(),f=fixture(path=>path==='/api/predict'?predictionGate.promise:successfulApi(path));
 const errors=installPredictionHandler(f),pending=f.element('run-prediction').onclick();
 await f.run(`loadCase('B','history')`);
 predictionGate.reject(Error('Synthetic old input prediction failure'));await pending;
 assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('current.profile'),'history');
 assert.deepEqual(errors,[]);assert.equal(f.element('run-prediction').disabled,false);
});
test('An old prediction finally cannot release the button owned by a newer pending case load',async()=>{
 const predictionGate=deferred(),caseGate=deferred(),f=fixture(path=>path==='/api/predict'?predictionGate.promise:path==='/api/journey/B'?caseGate.promise:successfulApi(path));
 const errors=installPredictionHandler(f),prediction=f.element('run-prediction').onclick(),loading=f.run(`loadCase('B','history')`);
 assert.equal(f.run('caseLoading'),true);assert.equal(f.element('run-prediction').disabled,true);
 predictionGate.reject(Error('Synthetic superseded prediction failure'));await prediction;
 assert.deepEqual(errors,[]);assert.equal(f.run('caseLoading'),true);assert.equal(f.element('run-prediction').disabled,true);
 caseGate.resolve({case_id:'B'});await loading;
 assert.equal(f.run('current.case_id'),'B');assert.equal(f.element('run-prediction').disabled,false);
});
test('A current input prediction rejection remains visible and releases its own button',async()=>{
 const f=fixture(path=>path==='/api/predict'?Promise.reject(Error('Synthetic current prediction failure')):successfulApi(path));
 const errors=installPredictionHandler(f);await f.element('run-prediction').onclick();
 assert.equal(f.run('current.case_id'),'OLD');assert.deepEqual(errors,['Synthetic current prediction failure']);
 assert.equal(f.element('run-prediction').disabled,false);assert.equal(f.run('caseLoading'),false);
});
test('A successful old input prediction cannot overwrite a newer loaded case',async()=>{
 const gate=deferred(),f=fixture(path=>path==='/api/predict'?gate.promise:successfulApi(path));
 installPredictionHandler(f);const pending=f.run('recalculate()');await f.run(`loadCase('B','history')`);
 gate.resolve({predictions:{},changed_features:['synthetic'],outside_development_range:[],elapsed_ms:0});
 assert.equal(await pending,false);assert.equal(f.run('current.case_id'),'B');assert.equal(f.run('current.profile'),'history');
 assert.equal(f.run('edited'),false);assert.equal(f.run('revealed'),false);
});

function predictionFixture(focusedInside){
 const doc={activeElement:{name:'outside'}},elements=new Map();let focusOptions;
 const grid={children:[],contains(node){return this.children.includes(node);},querySelector(selector){return this.children.find(button=>selector.includes(`"${button.dataset.target}"`));}};
 Object.defineProperty(grid,'innerHTML',{set(){if(grid.contains(doc.activeElement))doc.activeElement={name:'body'};grid.children=['CAD','LAD','LCX','RCA'].map(target=>({dataset:{target},focus(options){focusOptions=options;doc.activeElement=this;}}));}});
 grid.innerHTML='';if(focusedInside)doc.activeElement=grid.children[1];const previousFocus=doc.activeElement;
 const element=id=>id==='prediction-grid'?grid:elements.get(id)??elements.set(id,{textContent:'',innerHTML:''}).get(id);
 const ctx=vm.createContext({$:element,document:doc,renderWaterfall(){},renderCaseJourney(){},renderCharts(){},renderTruth(){}});
 const fragment=source.slice(source.indexOf('function thresholdFor(prediction){'),source.indexOf('function renderInputs(){'));
 vm.runInContext(`const targets=['CAD','LAD','LCX','RCA'],names={LAD:'Left anterior descending artery'},pretty={},esc=String,format=String,
 percent=p=>(100*p).toFixed(1)+'%';let selected='LAD',decisionMode='learned',edited=false,revealed=false;
 const p={probability:.5,operating_threshold:.5,baseline_log_odds:0,log_odds:0,contributions:[]};
 let current={kind:'development',fold:0,predictions:Object.fromEntries(targets.map(target=>[target,p]))};${fragment};renderPredictions();`,ctx);
 return {doc,previousFocus,focusOptions,grid};
}
test('Replacing prediction cards preserves the focused target without scrolling',()=>{
 const f=predictionFixture(true);assert.notEqual(f.doc.activeElement,f.previousFocus);assert.equal(f.doc.activeElement.dataset.target,'LAD');
 assert.equal(f.focusOptions.preventScroll,true);
});
test('Prediction rendering does not steal focus from controls outside the grid',()=>{
 const f=predictionFixture(false);assert.equal(f.doc.activeElement,f.previousFocus);assert.equal(f.focusOptions,undefined);
});
