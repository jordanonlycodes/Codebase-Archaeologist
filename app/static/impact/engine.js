/* Source-free impact queries over retained graph evidence. Browser and Node share this engine. */
(function(root){
 'use strict';
 const TYPES=new Set(['CALLS','IMPORTS','INCLUDES']);
 const LIMITS=Object.freeze({seeds:128,membership:3000,visited:400,edges:2500,references:100,internal:32,evidence:3,bytes:262144,depth:3,visible:32,search:30});
 const order=(a,b)=>a<b?-1:a>b?1:0;
 const byteSize=value=>new TextEncoder().encode(JSON.stringify(value)).length;
 function index(graph,architecture,structural){
  const nodes=new Map((graph?.nodes||[]).map(n=>[n.id,n])),edges=new Map(),incoming=new Map(),outgoing=new Map(),children=new Map(),functions=new Map(),owner=new Map(),component=new Map(),references=new Map();
  const add=(map,key,item)=>{if(!map.has(key))map.set(key,[]);map.get(key).push(item);};
  for(const e of graph?.edges||[]){
   if(e.status!=='resolved_internal'||!nodes.has(e.source)||!nodes.has(e.target))continue;
   if(e.type==='CONTAINS')add(children,e.source,e.target);
   if(e.type==='DEFINES'&&nodes.get(e.source).type==='file'&&nodes.get(e.target).type==='function'){owner.set(e.target,e.source);add(functions,e.source,e.target);}
   if(TYPES.has(e.type)){edges.set(e.id,e);add(incoming,e.target,e);add(outgoing,e.source,e);}
  }
  for(const n of nodes.values())if(n.type==='file')owner.set(n.id,n.id);
  const components=new Map((architecture?.components||[]).map(c=>[c.id,{...c,type:'component'}]));
  for(const c of components.values())for(const id of c.file_ids)component.set(id,c.id);
  for(const r of graph?.references||[])add(references,r.source,r);
  for(const map of [incoming,outgoing,references])for(const list of map.values())list.sort((a,b)=>order(a.id,b.id));
  for(const map of [children,functions])for(const list of map.values())list.sort(order);
  const hotspots=new Map((structural?.hotspots||[]).map(h=>[h.function_id,h]));
  const entities=[...nodes.values()].filter(n=>['file','function','directory'].includes(n.type)).concat([...components.values()]).sort((a,b)=>order(a.path||'',b.path||'')||order(a.id,b.id));
  return {graph,architecture,nodes,edges,incoming,outgoing,children,functions,owner,component,components,references,hotspots,entities};
 }
 function entity(ix,id){return ix.components.get(id)||ix.nodes.get(id);}
 function search(ix,q,type='all'){q=q.trim().toLowerCase();return ix.entities.filter(n=>(type==='all'||n.type===type)&&`${n.name} ${n.path||''} ${n.metadata?.qualified_name||''}`.toLowerCase().includes(q)).slice(0,LIMITS.search);}
 function seeds(ix,id,limits){
  const selected=entity(ix,id),ids=new Set(),files=new Set(),seen=new Set(),issues=new Set();let expanded=0;
  if(!selected)return {ids:[],issues:['entity_unavailable'],files:[],expanded};
  const stack=selected.type==='component'?[...selected.file_ids].sort(order).reverse():[id];
  while(stack.length){
   if(expanded>=limits.membership){issues.add('membership_limit');break;}
   const current=stack.pop();if(seen.has(current))continue;seen.add(current);expanded++;
   const n=ix.nodes.get(current);if(!n){issues.add('membership_not_retained');continue;}
   if(n.type==='directory'||n.type==='repository'){stack.push(...[...ix.children.get(current)||[]].reverse());continue;}
   if(!['file','function'].includes(n.type))continue;
   if(ids.size>=limits.seeds){issues.add('seed_limit');break;}
   ids.add(current);if(n.type==='file'){files.add(current);stack.push(...[...ix.functions.get(current)||[]].reverse());}
   else if(ix.owner.has(current))files.add(ix.owner.get(current));
  }
  return {ids:[...ids].sort(order),files:[...files].sort(order),issues:[...issues].sort(order),expanded};
 }
 function query(ix,id,options={},overrides={}){
  const limits={...LIMITS,...overrides};
  for(const [key,value]of Object.entries(limits))if(!Number.isInteger(value)||value<0)throw new RangeError('Impact limits must be nonnegative integers');
  if(limits.bytes<4096)throw new RangeError('Impact output budget must be at least 4096 bytes');
  const depth=Math.max(1,Math.min(limits.depth||1,Math.trunc(Number(options.depth))||1,3)),direction=['upstream','downstream','both'].includes(options.direction)?options.direction:'both';
  const membership=seeds(ix,id,limits),seedSet=new Set(membership.ids),issues=new Set(membership.issues),records=[],evidence=new Map(),internal=new Map();let visits=0,scanned=0,revisited=0;
  for(const side of direction==='both'?['upstream','downstream']:[direction]){
   const found=new Map(membership.ids.map(n=>[n,{id:n,distance:0,node_path:[n],edge_path:[]}])),queue=[...found.values()];let cursor=0,stop=false;
   while(cursor<queue.length&&!stop){const current=queue[cursor++];if(current.distance>=depth)continue;
    for(const edge of (side==='upstream'?ix.incoming:ix.outgoing).get(current.id)||[]){
     if(scanned>=limits.edges){issues.add('edge_scan_limit');stop=true;break;}scanned++;
     const target=side==='upstream'?edge.source:edge.target;
     if(seedSet.has(edge.source)&&seedSet.has(edge.target))internal.set(edge.id,edge);
     if(found.has(target)){revisited++;const previous=found.get(target);if(!seedSet.has(target)&&previous.edge_path.at(-1)!==edge.id)previous.other_paths_observed=true;continue;}
     if(visits>=limits.visited){issues.add('visited_limit');stop=true;break;}visits++;
     const record={id:target,side,distance:current.distance+1,node_path:[...current.node_path,target],edge_path:[...current.edge_path,edge.id],other_paths_observed:false};
     found.set(target,record);queue.push(record);records.push(record);
    }
   }
  }
  const attributable=new Set([...seedSet,...records.map(r=>r.id)]),refs=[];let referenceCount=0;
  for(const source of [...attributable].sort(order))for(const r of ix.references.get(source)||[]){referenceCount++;if(refs.length<limits.references)refs.push({id:r.id,source:r.source,type:r.type,status:r.status,reference:r.reference,reason:r.reason,evidence:r.evidence});}
  if(referenceCount>refs.length)issues.add('reference_limit');
  const edgeRecord=e=>({id:e.id,source:e.source,target:e.target,type:e.type,reference:e.reference,occurrences:e.occurrences,evidence:(e.evidence||[]).slice(0,limits.evidence),evidence_truncated:!!e.evidence_truncated||(e.evidence||[]).length>limits.evidence});
  const internalEdges=[...internal.values()].sort((a,b)=>order(a.id,b.id)).slice(0,limits.internal).map(edgeRecord);if(internal.size>internalEdges.length)issues.add('internal_evidence_limit');
  const result={schema_version:'1.0',origin:id,depth,direction,seeds:membership.ids,membership_expanded:membership.expanded,records,edges:[],internal_edges:internalEdges,references:refs,summary:{},coverage:{graph_complete:!!ix.graph?.coverage?.complete,graph_truncated:!!ix.graph?.coverage?.truncated,architecture_truncated:!!ix.architecture?.coverage?.truncated,issues:[],truncated:false},limits};
  function finalize(){
   evidence.clear();for(const record of records)for(const edgeId of record.edge_path){const e=ix.edges.get(edgeId);evidence.set(edgeId,edgeRecord(e));}
   result.edges=[...evidence.values()].sort((a,b)=>order(a.id,b.id));
   const ids=new Set(records.map(r=>r.id)),files=new Set([...ids].map(n=>ix.owner.get(n)).filter(Boolean)),components=new Set([...files].map(n=>ix.component.get(n)).filter(Boolean));
   const up=records.filter(r=>r.side==='upstream'),down=records.filter(r=>r.side==='downstream');
   const boundaries=new Set();for(const e of result.edges){const a=ix.component.get(ix.owner.get(e.source)),b=ix.component.get(ix.owner.get(e.target));if(a&&b&&a!==b)boundaries.add(a+'>'+b);}
   result.summary={direct_upstream:up.filter(r=>r.distance===1).length,transitive_upstream:up.filter(r=>r.distance>1).length,direct_downstream:down.filter(r=>r.distance===1).length,transitive_downstream:down.filter(r=>r.distance>1).length,distinct_reached_entities:ids.size,functions:[...ids].filter(n=>ix.nodes.get(n)?.type==='function').length,files:files.size,components:components.size,cross_component_pairs:boundaries.size,hotspot_functions:[...ids].filter(n=>ix.hotspots.has(n)).length,scored_c_functions:[...ids].filter(n=>{const m=ix.nodes.get(n)?.metadata;return m?.language==='C'&&m.ml?.status==='analyzed'&&m.ml.model_probability!=null;}).length,attributable_references:referenceCount,retained_references:refs.length,scanned_edges:scanned,visited_records:visits,revisited_edges:revisited,observed_internal_seed_edges:internal.size,observed_internal_seed_occurrences:[...internal.values()].reduce((n,e)=>n+(e.occurrences||0),0)};
   result.coverage.issues=[...issues].sort(order);result.coverage.truncated=issues.size>0;
  }
  finalize();
  // Hard UTF-8 JSON budget, including chains and bounded source evidence, not just record counts.
  while(byteSize(result)>limits.bytes&&(records.length||refs.length||internalEdges.length||result.seeds.length)){
   issues.add('serialized_output_limit');if(refs.length)refs.pop();else if(internalEdges.length)internalEdges.pop();else if(records.length)records.pop();else result.seeds.pop();finalize();
  }
  return result;
 }
 function layout(result){
  const positions=new Map([['@origin',{x:0,y:0}]]),groups=new Map();
  for(const record of result.records){const key=record.side+record.distance;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(record);}
  const visible=[];for(const side of ['upstream','downstream'])for(let depth=1;depth<=result.depth;depth++){
   const list=groups.get(side+depth)||[];for(const [row,r]of list.slice(0,Math.floor(LIMITS.visible/6)).entries()){const key=side+':'+r.id;positions.set(key,{x:(side==='upstream'?-1:1)*depth*290,y:(row-(Math.min(list.length,5)-1)/2)*110});visible.push({...r,key});}
  }
  return {positions,records:visible,truncated:visible.length<result.records.length};
 }
 const api={LIMITS,index,entity,search,seeds,query,layout,byteSize};root.ArchaeologistImpact=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
