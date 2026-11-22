/* Source-free, snapshot-local lexical retrieval. No external requests or code execution. */
(function(root){
 'use strict';
 const LIMITS=Object.freeze({question:1600,evidence:12,candidates:8,history:8,historyBytes:18000,cloudBytes:24576});
 const order=(a,b)=>String(a).localeCompare(String(b),'en');
 const clip=(v,n=256)=>String(v??'Unavailable').slice(0,n);
 function index(data){
  const impact=root.ArchaeologistImpact.index(data.knowledge_graph,data.architecture,data.structural),entities=new Map(impact.nodes);
  for(const c of impact.components.values())entities.set(c.id,c);
  for(const f of data.structural?.functions||[])if(!entities.has(f.id))entities.set(f.id,{id:f.id,name:f.name,path:f.path,type:'function',metadata:f});
  const ordered=[...entities.values()].sort((a,b)=>order(a.path||'',b.path||'')||order(a.id,b.id));
  return {data,impact,entities,ordered,lexical:ordered.map(n=>({node:n,keys:[n.name,n.path,n.metadata?.qualified_name].filter(Boolean).map(s=>s.toLowerCase())}))};
 }
 function search(ix,query){const q=query.trim().toLowerCase().replace(/\(\)$/,'');if(!q)return[];const hits=ix.lexical.map(({node,keys})=>({node,rank:keys.includes(q)?0:keys.some(k=>k.endsWith('/'+q)||k.endsWith('.'+q))?1:keys.some(k=>k.includes(q))?2:3})).filter(h=>h.rank<3);hits.sort((a,b)=>a.rank-b.rank||order(a.node.path||'',b.node.path||'')||order(a.node.id,b.node.id));return hits;}
 function resolve(ix,question,context){
  const quoted=[...question.matchAll(/[`"']([^`"']+)[`"']/g)].map(m=>m[1]);
  if(quoted.length){const hits=search(ix,quoted[0]);return {matches:hits.filter(h=>h.rank===(hits[0]?.rank)).map(h=>h.node),terms:quoted};}
  const q=question.toLowerCase();
  const mentioned=ix.lexical.filter(({keys})=>keys.some(k=>k.length>1&&q.includes(k)&&new RegExp('(^|[^a-z0-9_])'+k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'(?=$|[^a-z0-9_])','i').test(question))).map(h=>h.node);
  if(mentioned.length)return {matches:mentioned,terms:[]};
  if(context&&ix.entities.has(context)&&/\b(it|this|that|selected|its)\b/i.test(question))return {matches:[ix.entities.get(context)],terms:[]};
  return {matches:[],terms:quoted};
 }
 function fact(label,value){return {label:clip(label,64),value:clip(value)};}
 function entityEvidence(n){const m=n.metadata||n.metrics||{},facts=[fact('Entity type',n.type)];
  if(n.type==='function')for(const [key,label]of [['language','Language'],['cyclomatic_complexity','Cyclomatic complexity'],['max_nesting_depth','Control nesting'],['span_lines','Function span (physical lines)'],['parameter_count','Parameter count']])facts.push(fact(label,m[key]));
  if(n.type==='component')for(const key of ['files','functions','max_complexity','hotspots'])facts.push(fact(key,m[key]));
  if(m.ml?.status==='analyzed'&&m.language==='C')facts.push(fact('Uncalibrated C model score',m.ml.model_probability));
  else if(n.type==='function')facts.push(fact('ML coverage','Unscored; missing is not low risk'));
  return {entity_id:clip(n.id),kind:n.type,name:clip(n.name),path:n.path?clip(n.path):null,line:Number.isInteger(m.start_line)?m.start_line:null,facts};
 }
 function edgeEvidence(ix,e){return {entity_id:clip(e.id),kind:'relationship',name:clip(e.type),path:e.evidence?.[0]?.path?clip(e.evidence[0].path):null,line:e.evidence?.[0]?.line||null,facts:[fact('Source',ix.entities.get(e.source)?.name||e.source),fact('Source ID',e.source),fact('Target',ix.entities.get(e.target)?.name||e.target),fact('Target ID',e.target),fact('Resolution',e.status||'resolved_internal'),fact('Occurrences',e.occurrences),fact('Reference',e.reference||e.type)]};}
 function packet(records){const seen=new Set(),result=[];for(const r of records){if(!r||seen.has(r.entity_id))continue;seen.add(r.entity_id);const item={...r,id:'E'+(result.length+1)};if(result.length>=LIMITS.evidence||new TextEncoder().encode(JSON.stringify([...result,item])).length>LIMITS.cloudBytes)break;result.push(item);}return result;}
 function history(turns,snapshot){let out=turns.filter(t=>t.mode==='local'&&t.snapshot===snapshot).slice(-LIMITS.history);while(new TextEncoder().encode(JSON.stringify(out)).length>LIMITS.historyBytes)out.shift();return out;}
 const api={LIMITS,index,search,resolve,fact,entityEvidence,edgeEvidence,packet,history};root.JordanEvidence=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
