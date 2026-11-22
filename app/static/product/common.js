'use strict';
const $=id=>document.getElementById(id);
const number=value=>new Intl.NumberFormat().format(value);
const bytes=value=>value<1024?`${number(value)} B`:value<1048576?`${(value/1024).toFixed(1)} KiB`:`${(value/1048576).toFixed(1)} MiB`;
function node(tag,text,css){const element=document.createElement(tag);if(text!==undefined)element.textContent=String(text);if(css)element.className=css;return element;}
const workspaceStore=(()=>{try{return new ArchaeologistStore.Store({records:new ArchaeologistStore.BrowserRecords(window.indexedDB),tab:window.sessionStorage});}catch{const unavailable=async()=>{throw new Error('Browser workspace storage is unavailable. Enable site storage to preserve analysis between pages.');};return {load:unavailable,save:unavailable,forget:unavailable,view:()=>null,handoff:()=>null};}})();
const workspacePages=new Set(['overview','risk','structure','graph','architecture','heatmaps','blast-radius','jordan','time-machine']);
window.WorkspaceNavigation={open(page,id){if(!workspacePages.has(page))return false;if(id)workspaceStore.handoff({page,id});location.assign('/workspace/'+page);return true;}};
function riskBars(id,entries){const container=$(id);container.replaceChildren();const maximum=Math.max(1,...entries.map(e=>e[1]));for(const [label,count]of entries){const row=node('div',undefined,'risk-bar'),title=node('div'),bar=node('progress');title.append(node('span',label),node('strong',number(count)));bar.max=maximum;bar.value=count;bar.setAttribute('aria-label',`${label}: ${count}`);row.append(title,bar);container.append(row);}if(!entries.length)container.append(node('p','No measured functions to display.','risk-chart-empty'));}

const workspaceEntities={nodes:new Map(),fileComponents:new Map(),owners:new Map()};
function indexWorkspaceEntities(data){workspaceEntities.nodes=new Map((data.knowledge_graph?.nodes||[]).map(n=>[n.id,n]));workspaceEntities.fileComponents.clear();workspaceEntities.owners.clear();for(const c of data.architecture?.components||[])for(const id of c.file_ids)workspaceEntities.fileComponents.set(id,c.id);for(const e of data.knowledge_graph?.edges||[])if(e.type==='DEFINES'&&e.status==='resolved_internal')workspaceEntities.owners.set(e.target,e.source);for(const n of workspaceEntities.nodes.values())if(n.type==='file')workspaceEntities.owners.set(n.id,n.id);}
window.WorkspaceNavigation.component=id=>workspaceEntities.fileComponents.get(workspaceEntities.owners.get(id));
window.WorkspaceNavigation.file=id=>workspaceEntities.owners.get(id);

window.workspaceStoreForJordan=workspaceStore;

window.WorkspaceNavigation.askJordan=(id,options={})=>{
 if(id&&(!workspaceEntities.nodes.has(id)&&!window.activeAnalysis?.structural?.functions.some(f=>f.id===id)&&!window.activeAnalysis?.architecture?.components.some(c=>c.id===id)))return false;
 const from=document.body.dataset.page,question=typeof options.question==='string'?options.question.slice(0,1600):'Explain this selected entity.';
 const handoff={page:'jordan',id:id||null,from:workspacePages.has(from)?from:'overview',question};
 if([1,2,3].includes(options.depth))handoff.depth=options.depth;
 if(['upstream','downstream','both'].includes(options.direction))handoff.direction=options.direction;
 if(options.target_id&&workspaceEntities.nodes.has(options.target_id))handoff.target_id=options.target_id;
 workspaceStore.handoff(handoff);location.assign('/workspace/jordan');return true;
};

window.WorkspaceNavigation.fileHistory=id=>{
 const file=workspaceEntities.owners.get(id)||id;
 if(window.activeAnalysis?.source?.type!=='github'||workspaceEntities.nodes.get(file)?.type!=='file')return false;
 return window.WorkspaceNavigation.open('time-machine',file);
};
