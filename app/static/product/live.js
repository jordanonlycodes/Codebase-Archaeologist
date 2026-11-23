/* RELIC // LIVE. One snapshot, existing instruments, manual presentation. */
(function(root){
 'use strict';
 const SCENES=['The Awakening','Intelligence Awakens','Repository Universe','Relic X-Ray','Risk & Time','The Final Reveal'];
 const NOTES=[
  'Introduce Codebase Archaeologist as repository intelligence with C-function defect-risk estimation. This is the repository loaded in this tab; the presentation creates no new analysis.',
  'Explain the included files, extracted functions and languages. Dependency counts exclude ownership edges. These are snapshot measurements, not invented demonstration numbers.',
  'Explore a real directory constellation. Rotate, pan and zoom; select an entity to illuminate its actual relationships. The optional existing tour can be paused or exited at any time.',
  'Choose a directory, then a file and a function. Inspect source locations and trace direct relationships. CONTAINS and DEFINES indicate ownership; CALLS and imports are distinct static evidence.',
  'C-only Random Forest scores are modest research estimates, not proof of defects. Python has no C-model prediction. Time Machine uses pinned Git ancestry; a ZIP has no Git history. Only explicitly retrieve history if network access is appropriate.',
  'Summarize structural analysis, relationships and progressive investigation. State which risk and history evidence was available for this repository. Invite questions; do not imply every capability produced evidence for every language.'
 ];
 class Sequence {
  constructor(){this.state='inactive';this.scene=0;this.generation=0;}
  prepare(){this.state='preparing';return ++this.generation;}
  go(scene){this.scene=Math.max(0,Math.min(5,Number.isFinite(scene)?Math.trunc(scene):0));this.state='transitioning';return ++this.generation;}
  settle(token){if(token===this.generation&&this.state==='transitioning'){this.state='active';return true;}return false;}
  exit(){this.state='exiting';return ++this.generation;}
  inactive(token){if(token===this.generation)this.state='inactive';}
 }
 const validScore=n=>n.type==='function'&&n.metadata?.language==='C'&&n.metadata.ml?.status==='analyzed'&&[0,1].includes(n.metadata.ml.predicted_class)&&Number.isFinite(n.metadata.ml.model_probability)&&n.metadata.ml.model_probability>=0&&n.metadata.ml.model_probability<=1;
 function evidence(data){
  const graph=data?.knowledge_graph,nodes=graph?.nodes||[],ids=new Set(nodes.map(n=>n.id)),edges=(graph?.edges||[]).filter(e=>e.status==='resolved_internal'&&ids.has(e.source)&&ids.has(e.target));
  const source=data?.source,h=data?.history,history=source?.type==='github'&&/^[a-f0-9]{40}$/.test(source.snapshot_commit||'')&&h?.anchor===source.snapshot_commit&&h?.repository_url===source.url&&Array.isArray(h?.commits)?h:null;
  return {nodes,edges,scores:nodes.filter(validScore),history,metrics:[['Files',data?.summary?.files],['Functions',data?.structural?.summary?.analyzed_functions],['Languages',data?.summary?.languages],['Dependencies',graph?edges.filter(e=>['CALLS','IMPORTS','INCLUDES'].includes(e.type)).length:null]],xray:nodes.some(n=>['directory','file','function'].includes(n.type))};
 }
 function shortcut(event){
  if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return null;
  if(event.key==='Escape'&&!event.target?.closest?.('#knowledge-explorer,[role=dialog]'))return 'escape';
  if(event.target?.closest?.('input,textarea,select,button,a,summary,[contenteditable=true],[role=dialog],#knowledge-explorer,#time-machine'))return null;
  return {'ArrowRight':'next','ArrowLeft':'previous',' ':'next',Home:'first',End:'last',f:'fullscreen',F:'fullscreen',Escape:'escape'}[event.key]||null;
 }
 const api={Sequence,evidence,shortcut,SCENES,NOTES};root.RelicLiveData=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
 if(!root.document?.getElementById('live-shell'))return;
 const $=id=>document.getElementById(id),element=(tag,text,css)=>{const n=document.createElement(tag);if(text!=null)n.textContent=String(text);if(css)n.className=css;return n;};
 class Live {
  constructor(){
   this.sequence=new Sequence();this.animation=null;this.loadGeneration=0;this.expiry=null;this.recording=false;this.riskView='risk';this.data=null;this.boundId=null;this.ready=false;this.graphReady=false;this.tmReady=false;this.syncing=false;this.media=matchMedia('(prefers-reduced-motion: reduce)');
   this.shell=$('live-shell');this.stage=$('live-stage');this.graph=$('knowledge-explorer');this.graphRoot=root.graphExplorer;this.graphRoot.suspended=true;
   for(const [id,fn]of Object.entries({'live-launch':()=>this.launch(),'live-refresh':()=>this.load(),'live-prev':()=>this.go(this.sequence.scene-1),'live-next':()=>this.go(this.sequence.scene+1),'live-restart':()=>this.go(0),'live-restart-end':()=>this.go(0),'live-exit':()=>this.exit(),'live-return-end':()=>this.returnWorkspace(),'live-fullscreen':()=>this.fullscreen(),'live-record':()=>this.record(!this.recording),'live-notes-toggle':()=>this.notes(),'live-risk-tab':()=>this.subview('risk'),'live-history-tab':()=>this.subview('history'),'live-tour':()=>this.graphRoot.startTour(),'live-focus':()=>this.focusStructure(),'live-reset-camera':()=>{$('graph-reset').click();}}))$(id).addEventListener('click',()=>this.guard(fn));
   for(const b of document.querySelectorAll('[data-live-next]'))b.addEventListener('click',()=>this.guard(()=>this.go(this.sequence.scene+1)));
   SCENES.forEach((title,i)=>$('live-jump').append(new Option(`${String(i+1).padStart(2,'0')} / ${title}`,String(i))));$('live-jump').addEventListener('change',()=>this.guard(()=>this.go(Number($('live-jump').value))));
   $('live-record-ready').addEventListener('change',()=>this.record($('live-record-ready').checked));
   this.key=e=>{if(!this.running)return;const action=shortcut(e);if(!action)return;e.preventDefault();if(e.repeat)return;this.guard(()=>{if(action==='escape'){if(document.fullscreenElement)this.fullscreen();else this.exit();}else if(action==='fullscreen')this.fullscreen();else this.go(action==='first'?0:action==='last'?5:this.sequence.scene+(action==='next'?1:-1));});};
   document.addEventListener('keydown',this.key);
   // Existing X-Ray handlers execute first. Reflect their shared selection/mode,
   // rather than wrapping or duplicating either controller's navigation methods.
   this.bridge=e=>{if(!this.running||this.syncing||![2,3].includes(this.sequence.scene))return;if(this.sequence.scene===2&&(e?.target?.closest?.('#universe-exit')||(e?.key==='Escape'&&this.graphRoot.tour?.status==='idle')||(this.graph.contains(document.activeElement)&&!document.activeElement.getClientRects().length)))$('live-tour').focus();const active=!!root.RelicXRay.active;if(active&&this.sequence.scene===2)this.go(3,true);else if(!active&&this.sequence.scene===3)this.go(2,true);};
   this.graph.addEventListener('click',this.bridge);this.graph.addEventListener('keydown',e=>{if(e.key==='Escape')queueMicrotask(()=>this.guard(()=>this.bridge(e)));});
   this.motionChange=()=>{this.cancel();this.sequence.settle(this.sequence.generation);};this.media.addEventListener?.('change',this.motionChange);
   document.addEventListener('fullscreenchange',()=>{$('live-fullscreen').setAttribute('aria-pressed',String(document.fullscreenElement===this.shell));this.graphRoot.adapter?.resize();});
   document.addEventListener('visibilitychange',()=>{if(document.hidden){this.cancel();this.suspend();}else if(this.running){if(!this.current())this.invalidate();else this.activateInstrument(this.sequence.scene,this.sequence.generation);}});
   root.addEventListener('storage',e=>{if(e.key==='archaeologist.active'&&this.data&&!this.current())this.invalidate();});
   root.addEventListener('focus',()=>{if(this.data&&!this.current())this.invalidate();});
   root.addEventListener('pagehide',()=>this.dispose());root.addEventListener('pageshow',e=>{if(e.persisted){this.sequence.inactive(this.sequence.exit());this.shell.hidden=true;$('live-preflight').hidden=false;this.load();}});
   this.load();
  }
  get running(){return !['inactive','preparing','exiting'].includes(this.sequence.state);}
  async guard(fn){try{await fn();}catch{this.cancel();this.sequence.settle(this.sequence.generation);this.message('This scene could not finish preparing. Use Previous, Next or Exit; the repository snapshot remains available.');}}
  message(text){$('live-status').textContent=text;}
  current(){try{return this.boundId===sessionStorage.getItem('archaeologist.active')&&workspaceStore.current?.expires>Date.now();}catch{return false;}}
  async load(){
   const token=++this.loadGeneration;this.sequence.prepare();this.ready=false;$('live-launch').disabled=true;
   try{const data=await workspaceStore.load();if(token!==this.loadGeneration)return;this.data=data;this.boundId=workspaceStore.current?.id||null;root.activeAnalysis=data;this.facts=evidence(data);this.ready=!!data;this.graphReady=false;this.tmReady=false;this.graphRoot.suspended=true;root.RelicXRay.reset();this.graphRoot.setGraph(data?.knowledge_graph||null);if(data)indexWorkspaceEntities(data);
    $('live-repository').textContent=data?.repository||'No active repository in this tab.';$('live-context').textContent=data?.repository||'No repository';
    for(const n of document.querySelectorAll('.live-repo-name'))n.textContent=data?.repository||'';
    const saved=workspaceStore.view('graph');if(saved?.selected&&this.graphRoot.ix.nodes.has(saved.selected))this.graphRoot.state.selected=saved.selected;
    if(this.graphRoot.supports3D&&innerWidth>=1000&&!this.media.matches)this.graphRoot.state.mode='3d';
    this.graphRoot.syncControls();this.graphRoot.observer?.observe(this.graph);this.graphRoot.resize?.observe(this.graphRoot.host);this.preflight();this.populate();clearTimeout(this.expiry);if(data)this.expiry=setTimeout(()=>this.invalidate(),Math.max(0,workspaceStore.current.expires-Date.now()));
   }catch{$('live-preflight-status').textContent='The active snapshot could not be restored. Load a repository or enable site storage, then retry.';this.data=null;this.ready=false;}
   this.sequence.state='inactive';$('live-launch').disabled=!this.ready;
  }
  preflight(){
   const f=this.facts,d=this.data,rows=[['Repository',d?'Loaded':'Load a repository'],['Analysis',d?.summary?'Available':'Unavailable'],['Overview metrics',f.metrics.some(([,v])=>Number.isFinite(v))?'Available':'Unavailable'],['Repository Universe',f.nodes.length?`${f.nodes.length} retained entities`:'No graph evidence'],['X-Ray architecture',f.xray?'Available':'No retained hierarchy'],['C risk evidence',f.scores.length?`${f.scores.length} retained C scores`:'Unavailable · structural analysis remains usable'],['Git history',f.history?.commits.length?`${f.history.commits.length} cached commits`:d?.source?.type==='github'?'Not loaded · retrieve explicitly in Time Machine':'Unavailable for ZIP snapshots'],['Browser fullscreen',document.fullscreenEnabled?'Supported · optional':'Viewport layout available']];
   $('live-checks').replaceChildren();for(const [label,value]of rows)$('live-checks').append(element('dt',label),element('dd',value));
   $('live-preflight-status').textContent=d?'Ready for a manual presentation. Missing capabilities will show explanatory states.':'Load a repository to present its actual evidence.';
  }
  populate(){
   const f=this.facts,d=this.data;this.metricElements=[];$('live-metrics').replaceChildren();for(const [label,value]of f.metrics){const card=element('article',null,'live-metric'),number=element('strong',Number.isFinite(value)?value.toLocaleString():'Unavailable');card.append(number,element('span',label));$('live-metrics').append(card);this.metricElements.push({element:number,value,key:label});}
   $('live-languages').replaceChildren();for(const lang of (d?.languages||[]).slice(0,8)){const row=element('div',null,'live-language'),bar=element('progress');bar.max=Math.max(1,d.summary.files);bar.value=lang.files;bar.setAttribute('aria-label',`${lang.language}: ${lang.files} included files`);row.append(element('span',lang.language),element('strong',`${lang.files} files`),bar);$('live-languages').append(row);}if(!d?.languages?.length)$('live-languages').append(element('p','No language composition is available.'));
   const scores=[...f.scores].sort((a,b)=>b.metadata.ml.model_probability-a.metadata.ml.model_probability||a.id.localeCompare(b.id));$('live-risk-cards').replaceChildren();
   $('live-risk-summary').textContent=scores.length?`${scores.length} scored C functions retained in this graph. Showing up to six, ordered by existing score. Model: ${d.defect_risk?.model_version||'metadata unavailable'}.`:'No eligible C-function risk evidence is available in this snapshot. Python and other languages receive no C-model prediction.';
   for(const n of scores.slice(0,6)){const item=element('article',null,'live-risk-card'),score=n.metadata.ml.model_probability,button=element('button','Investigate in X-Ray ↗');button.type='button';button.addEventListener('click',()=>{this.graphRoot.state.selected=n.id;this.go(3);});item.append(element('p','C / FUNCTION ESTIMATE','kicker'),element('h3',n.name),element('strong',`${(score*100).toFixed(1)}%`),element('p',n.path||'Location unavailable'),element('small',n.metadata.ml.predicted_class===1?'Predicted defect-related':'Predicted non-defect-related'),button);$('live-risk-cards').append(item);}
   if(!scores.length)$('live-risk-cards').append(element('div','Evidence unavailable. Continue with architecture or inspect genuine Git history when available.','live-unavailable'));
   $('live-closing-metrics').textContent=f.metrics.map(([label,v])=>`${Number.isFinite(v)?v.toLocaleString():'Unavailable'} ${label.toLowerCase()}`).join(' / ');
   $('live-capabilities').replaceChildren();for(const [name,ready]of [['Structural analysis',!!d?.structural],['Dependency visualization',f.nodes.length>0],['X-Ray investigation',f.xray],['C-only defect-risk estimation',scores.length>0],['Genuine Git history',!!f.history?.commits.length]])$('live-capabilities').append(element('span',`${name} · ${ready?'evidence available':'unavailable in this snapshot'}`));
   // A bounded, decorative projection of actual edge endpoints, never random entities.
   const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 800 400');const sample=f.nodes.slice(0,40),points=new Map(sample.map((n,i)=>[n.id,{x:400+Math.cos(i*2*Math.PI/Math.max(1,sample.length))*330,y:200+Math.sin(i*2*Math.PI/Math.max(1,sample.length))*160}]));
   for(const e of f.edges.slice(0,100)){const a=points.get(e.source),b=points.get(e.target);if(!a||!b)continue;const line=document.createElementNS(svg.namespaceURI,'line');for(const [k,v]of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y}))line.setAttribute(k,String(v));svg.append(line);}for(const p of points.values()){const circle=document.createElementNS(svg.namespaceURI,'circle');circle.setAttribute('cx',p.x);circle.setAttribute('cy',p.y);circle.setAttribute('r','3');svg.append(circle);}$('live-echo').replaceChildren(svg);
  }
  launch(){if(!this.ready||!this.current()){this.invalidate();return;}this.returnFocus=document.activeElement;$('live-preflight').hidden=true;this.shell.hidden=false;this.record($('live-record-ready').checked);this.go(0);}
  cancel(){this.animation?.cancel();this.animation=null;root.LivingStatistics?.stop();}
  suspend(){this.graphRoot.suspended=true;this.graphRoot.stopTour('Presentation scene changed.');this.graphRoot.adapter?.pause?.();this.graphRoot.adapter?.cancelCamera?.();if(!this.graphRoot.adapter)this.graphRoot.epoch++;root.timeMachine.pausePlayback();root.timeMachine.cancel();root.WorkspaceMotion?.destroy();}
  go(scene,fromInstrument=false){
   if(!this.current()){this.invalidate();return;}const next=Math.max(0,Math.min(5,Math.trunc(scene)));this.cancel();this.suspend();const token=this.sequence.go(next);this.syncing=true;
   try{for(const n of document.querySelectorAll('[data-live-scene]'))n.hidden=Number(n.dataset.liveScene)!==next;
    if([2,3].includes(next))$(next===2?'live-universe-slot':'live-xray-slot').append(this.graph);else $('live-storage').append(this.graph);
    $('live-index').textContent=`${String(next+1).padStart(2,'0')} / 06`;$('live-jump').value=String(next);$('live-progress').value=next+1;$('live-prev').disabled=next===0;$('live-next').disabled=next===5;$('live-note-copy').textContent=NOTES[next];this.message('');this.stage.scrollTop=0;
    if(next!==3&&root.RelicXRay.active)root.RelicXRay.exit(false);
    this.activateInstrument(next,token,fromInstrument);
    if(next===5){this.facts=evidence(this.data);this.populate();}
    if(next===1)for(const item of this.metricElements)root.LivingStatistics?.set(item.element,item.value,{scope:this.boundId,key:'live:'+item.key});
    const active=document.querySelector(`[data-live-scene="${next}"]`);$('live-title-'+next).focus({preventScroll:true});
    if(!this.media.matches&&!document.hidden&&active.animate){this.animation=active.animate([{opacity:.25,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:next===0?850:560,easing:'cubic-bezier(.22,1,.36,1)'});this.animation.onfinish=()=>{if(this.sequence.settle(token))this.animation=null;};}else this.sequence.settle(token);
   }finally{this.syncing=false;}
  }
  async activateInstrument(scene,token,fromInstrument=false){
   if(!this.running||document.hidden)return;
   try{
    if(scene===2){this.graphRoot.suspended=false;if(!this.graphRoot.ix.nodes.size){this.message('No graph evidence is retained for this repository.');return;}
     if(!this.graphRoot.adapter)await this.graphRoot.switchMode(this.graphRoot.state.mode);
     if(token!==this.sequence.generation||this.sequence.scene!==2)return;
     this.graphRoot.adapter?.resize();this.graphRoot.adapter?.wake?.();if(!this.graphReady){this.graphRoot.adapter?.fit();this.graphReady=true;}else if(fromInstrument)this.graphRoot.focusEntity(this.graphRoot.state.selected);
    }else if(scene===3){if(!fromInstrument||!root.RelicXRay.active)root.RelicXRay.open(this.graphRoot.state.selected,$('live-title-3'));}
    else if(scene===4)this.subview(this.riskView);
   }catch{if(token===this.sequence.generation)this.message('This instrument could not initialize. Its accessible evidence controls or another scene remain available.');}
  }
  focusStructure(){const groups=this.graphRoot.groups?.groups||[],group=[...groups].sort((a,b)=>b.ids.length-a.ids.length||a.key.localeCompare(b.key))[0];if(!group){this.message('No directory constellation is available. Select a retained entity instead.');return;}this.graphRoot.stopTour('Presenter selected a structure.');if(group.directoryId)this.graphRoot.select(group.directoryId);else this.graphRoot.adapter?.focusCluster?.(group.key);}
  subview(view){this.riskView=view==='history'?'history':'risk';const history=this.riskView==='history';$('live-risk').hidden=history;$('live-history').hidden=!history;$('live-risk-tab').setAttribute('aria-pressed',String(!history));$('live-history-tab').setAttribute('aria-pressed',String(history));if(history&&!this.tmReady){root.timeMachine.initialize(this.data,workspaceStore,workspaceStore.view('time-machine'),null);this.tmReady=true;}else if(history)root.timeMachine.render();else{root.timeMachine.pausePlayback();root.timeMachine.cancel();}}
  record(value){this.recording=!!value;this.shell.classList.toggle('is-recording',this.recording);$('live-record').setAttribute('aria-pressed',String(this.recording));$('live-record-ready').checked=this.recording;if(this.recording){$('live-notes').hidden=true;$('live-notes-toggle').setAttribute('aria-expanded','false');}this.graphRoot.adapter?.resize();}
  notes(){const open=$('live-notes').hidden;$('live-notes').hidden=!open;$('live-notes-toggle').setAttribute('aria-expanded',String(open));if(open)this.message('Presenter notes are visible here and will appear in a screen recording.');else this.message('');}
  async fullscreen(){try{if(document.fullscreenElement===this.shell)await document.exitFullscreen();else if(this.running&&this.shell.requestFullscreen)await this.shell.requestFullscreen();else this.message('Fullscreen is unavailable. The viewport presentation remains usable.');}catch{this.message('Fullscreen was not granted. Continue in the full-viewport presentation.');}}
  exit(){const token=this.sequence.exit();this.cancel();this.suspend();this.syncing=true;try{if(root.RelicXRay.active)root.RelicXRay.exit(false);}finally{this.syncing=false;}$('live-storage').append(this.graph);if(document.fullscreenElement===this.shell)document.exitFullscreen().catch(()=>{});this.shell.hidden=true;$('live-preflight').hidden=false;$('live-notes').hidden=true;$('live-notes-toggle').setAttribute('aria-expanded','false');this.sequence.inactive(token);if(this.returnFocus?.isConnected)this.returnFocus.focus();else $('live-launch').focus();}
  returnWorkspace(){this.saveViews();this.exit();location.assign('/workspace/overview');}
  saveViews(){if(!this.current())return;try{workspaceStore.view('graph',{...this.graphRoot.state,collapsed:this.graphRoot.state.collapsed.slice(0,100)});if(this.tmReady)workspaceStore.view('time-machine',root.timeMachine.state());}catch{/* Optional presentation preferences do not affect evidence. */}}
  invalidate(){this.exit();this.ready=false;this.data=null;this.boundId=null;this.graphReady=false;this.tmReady=false;this.graphRoot.setGraph(null);root.timeMachine.destroy();$('live-launch').disabled=true;$('live-checks').replaceChildren();$('live-repository').textContent='Repository context changed or expired.';$('live-preflight-status').textContent='Refresh readiness to restore the current snapshot, or load a repository.';}
  dispose(){this.loadGeneration++;clearTimeout(this.expiry);this.saveViews();this.cancel();this.graphRoot.suspend();root.timeMachine.destroy();workspaceStore.close?.();}
 }
 root.RelicLive=new Live();
})(globalThis);
