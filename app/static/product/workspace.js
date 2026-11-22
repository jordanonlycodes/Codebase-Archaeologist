'use strict';
let result=null;
const pageName=document.body.dataset.page;
const controls={overview:['file-search','language-filter','file-sort'],risk:['risk-search','risk-filter','risk-sort'],structure:['structure-search','structure-language','structure-sort']};
const error=message=>{$('workspace-error').textContent=message;$('workspace-error').hidden=false;};
function restoreControls(values){for(const [id,value]of Object.entries(values||{}))if($(id)&&typeof value==='string')$(id).value=value;}
function capture(){if(!result)return;try{let state={};if(controls[pageName])state=Object.fromEntries(controls[pageName].map(id=>[id,$(id).value]));if(pageName==='graph')state={...graphExplorer.state,collapsed:graphExplorer.state.collapsed.slice(0,100)};if(['architecture','heatmaps'].includes(pageName))state={...architectureExplorer.state};if(pageName==='blast-radius')state={origin:impactExplorer.origin,depth:$('impact-depth').value,direction:$('impact-direction').value};if(pageName==='jordan')state=jordanWorkspace.state();workspaceStore.view(pageName,state);}catch{/* Small UI preferences are optional; the snapshot remains the source of truth. */}}
function cleanup(){capture();window.jordanWorkspace?.destroy();if(window.graphExplorer){graphExplorer.suspended=true;graphExplorer.observer.disconnect();graphExplorer.resize.disconnect();graphExplorer.epoch++;graphExplorer.adapter?.destroy();graphExplorer.adapter=null;}if(window.architectureExplorer){architectureExplorer.suspended=true;architectureExplorer.observer.disconnect();architectureExplorer.scene?.destroy();architectureExplorer.scene=null;architectureExplorer.key=null;}if(window.impactExplorer){impactExplorer.scene?.destroy();impactExplorer.scene=null;}}
function initialize(handoff){
 indexWorkspaceEntities(result);
 const saved=workspaceStore.view(pageName);
 if(pageName==='jordan')jordanWorkspace.initialize(result,workspaceStore.current.id,saved,handoff);
 if(pageName==='overview'){renderOverview(result);restoreControls(saved);/* Inventory filters render again after hydration. */for(const id of controls.overview)$(id).dispatchEvent(new Event(id==='file-search'?'input':'change'));renderOverviewContext();}
 if(pageName==='risk'){renderDefectRisk(result.defect_risk);restoreControls(saved);renderRiskTable();}
 if(pageName==='structure'){renderStructure(result.structural);restoreControls(saved);renderStructureTable();if(handoff?.id){const f=result.structural?.functions.find(f=>f.id===handoff.id);if(f)showStructureDetail(f);}}
 if(pageName==='graph'){
  renderKnowledgeGraph(result.knowledge_graph, saved);if(handoff?.id)graphExplorer.choose(handoff.id);
 }
 if(['architecture','heatmaps'].includes(pageName)){
  renderArchitecture(result.architecture, result.knowledge_graph, result.structural);if(saved)Object.assign(architectureExplorer.state,saved);architectureExplorer.state.view=pageName==='heatmaps'?'heatmap':'architecture';architectureExplorer.key=null;
  if(handoff?.id){if(pageName==='heatmaps')architectureExplorer.openDirectory(handoff.id);else {const candidate=architectureExplorer.ix.components.get(handoff.id)||[...architectureExplorer.ix.components.values()].find(c=>c.graph_id===handoff.id||c.graph_id===architectureExplorer.ix.nodes.get(handoff.id)?.graph_id);if(candidate)architectureExplorer.selectComponent(candidate.id);}}
  for(const [id,key]of [['ai-search','query'],['ai-metric','metric'],['ai-area','area'],['ai-relationships','relationship']])$(id).value=architectureExplorer.state[key];architectureExplorer.draw();
 }
 if(pageName==='blast-radius'){
  renderImpact(result.knowledge_graph, result.architecture, result.structural);if(saved){$('impact-depth').value=saved.depth||'1';$('impact-direction').value=saved.direction||'both';}const id=handoff?.id||saved?.origin;if(id)impactExplorer.open(id);
 }
}
function renderOverviewContext(){
 const container=$('overview-pathways');if(!container)return;container.replaceChildren();const s=result.structural,g=result.knowledge_graph,a=result.architecture,m=result.defect_risk;
 for(const [page,label,measure,detail]of [
  ['structure','Function structure',s?number(s.summary.analyzed_functions):'Unavailable','Observed C/Python functions; unsupported measurements remain missing.'],
  ['graph','Source relationships',g?number(g.summary.edges):'Unavailable','Retained hierarchy, call, import and include relationships.'],
  ['architecture','Architecture components',a?number(a.components.length):'Unavailable','Directory groups, based on actual direct-member files.'],
  ['risk','C-function research scores',m?number(m.analyzed_functions):'Unavailable',m?.message||'Optional trusted model unavailable.'],
  ['blast-radius','Potential change impact','Explore','Trace resolved relationships; reachability is not guaranteed breakage.']]){
  const link=node('a',undefined,'overview-pathway');link.href='/workspace/'+page;link.append(node('span',label),node('strong',measure),node('p',detail),node('b','↗'));container.append(link);
 }
}
$("download-json").addEventListener("click", () => {
 if(!result)return;
 const query=window.impactExplorer?.result;
 if(query)result.blast_radius=query;else delete result.blast_radius;
 const url=URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)],{type:'application/json'})),link=node('a');link.href=url;link.download='codebase-analysis.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('forget-repository').addEventListener('click',async()=>{if(!confirm('Forget this tab’s source-free analysis snapshot and selections?'))return;try{await workspaceStore.forget();location.assign('/explore');}catch(e){error(e.message);}});
const menu=$('workspace-menu');menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));$('workspace-sidebar').classList.toggle('is-open',open);});document.addEventListener('keydown',event=>{if(event.key==='Escape'&&menu.getAttribute('aria-expanded')==='true'){menu.setAttribute('aria-expanded','false');$('workspace-sidebar').classList.remove('is-open');menu.focus();}});
let bootId=null,expiryTimer=null,leaving=false;
(async()=>{try{const loaded=await workspaceStore.load();if(leaving)return;result=loaded;window.activeAnalysis=result;if(!result){$('workspace-empty').hidden=false;$('workspace-status').textContent='No active snapshot. Import once to open all workspaces.';return;}bootId=workspaceStore.current.id;$('context-repository').textContent=result.repository;$('context-repository').title=result.repository;$('workspace-content').hidden=false;$('download-json').hidden=false;$('forget-repository').hidden=false;$('workspace-status').textContent=`${result.source?.type==='github'?'Public GitHub snapshot':'ZIP snapshot'} · analyzed ${new Date(result.analyzed_at).toLocaleString()} · source files removed after analysis. Browser snapshot expires ${new Date(workspaceStore.current.expires).toLocaleTimeString()}.`;const handoff=workspaceStore.handoff();initialize(handoff?.page===pageName?handoff:null);expiryTimer=setTimeout(async()=>{try{await workspaceStore.forget();}catch{/* Logical expiry is also enforced by load(). */}location.assign('/explore');},Math.max(0,workspaceStore.current.expires-Date.now()));}catch(e){error(e.message);$('workspace-empty').hidden=false;$('workspace-status').textContent='The active workspace could not be restored.';}})();
addEventListener('pagehide',()=>{leaving=true;clearTimeout(expiryTimer);cleanup();workspaceStore.close?.();});
addEventListener('pageshow',event=>{if(!event.persisted)return;leaving=false;if(!result||!workspaceStore.current||sessionStorage.getItem('archaeologist.active')!==bootId||workspaceStore.current.expires<=Date.now()){location.reload();return;}clearTimeout(expiryTimer);expiryTimer=setTimeout(()=>location.reload(),Math.max(0,workspaceStore.current.expires-Date.now()));if(window.jordanWorkspace){jordanWorkspace.initialize(result,bootId,workspaceStore.view('jordan'),null);}if(window.graphExplorer){graphExplorer.suspended=false;graphExplorer.observer.observe($('knowledge-explorer'));graphExplorer.resize.observe(graphExplorer.host);if(graphExplorer.ix.nodes.size)graphExplorer.switchMode(graphExplorer.state.mode);}if(window.architectureExplorer){architectureExplorer.suspended=false;architectureExplorer.observer.observe($('architecture-intelligence'));architectureExplorer.draw();}if(window.impactExplorer?.result)impactExplorer.draw();});
