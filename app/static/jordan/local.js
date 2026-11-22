/* Deterministic supported investigations, not an unrestricted language model. */
(function(root){
 'use strict';
 const R=root.JordanEvidence,E=root.ArchaeologistImpact;
 const NOTE='Static analysis shows observed structure, not runtime behavior. Function bodies are not retained. C-only model estimates are uncalibrated research signals, not confirmed defects; unscored does not mean low risk.';
 function intent(q){
  if(/unavailable|limitations|coverage|missing information|what.*know.*not/i.test(q))return 'coverage';
  if(/unscored|not scored|without.*score/i.test(q))return 'unscored';
  if(/highest.*(model|risk|score)|defect|model estimates|risk|review signals/i.test(q))return 'risk';
  if(/hotspot|deeply nested/i.test(q))return 'hotspots';
  if(/most complex|highest.*complexity|complexity ranking/i.test(q))return 'complexity';
  if(/affected|impact|change.*(function|file|component|it|this)|blast radius/i.test(q))return 'impact';
  if(/relationships? (exist )?between/i.test(q))return 'between';
  if(/who calls|which components depend on|callers|calls (it|this)|what imports|what includes|depend on (this|it)|depends on|dependents/i.test(q))return 'incoming';
  if(/what.*call|callees|what.*import|what.*include|dependencies|depend on/i.test(q))return 'outgoing';
  if(/architecture|cycles|component (overview|summary)|largest.*components|connected components/i.test(q))return 'architecture';
  if(/languages?/i.test(q))return 'languages';
  if(/how many.*function|function (count|total)/i.test(q))return 'functions';
  if(/summari[sz]e|overview|inventory|how many.*file/i.test(q))return 'overview';
  if(/explain|what.*know|tell me|find|inspect|look up/i.test(q))return 'entity';
  return 'unsupported';
 }
 function answer(ix,question,context={}){
  if(typeof question!=='string'||!question.trim()||question.length>R.LIMITS.question)throw new Error('Enter a question of 1–1600 characters.');
  const q=question.trim(),kind=intent(q),records=[],lines=[],actions=[];let entityId=null,candidates=[];
  const add=n=>{if(n){const record=R.entityEvidence(n);for(const r of (ix.impact.hotspots.get(n.id)?.reasons||[]).slice(0,4))record.facts.push(R.fact('Structural hotspot',`${r.explanation}; threshold ${r.threshold}; measured ${r.value}`));records.push(record);}};
  const reply={intent:kind,answer:'',entity_id:null,evidence:[],candidates:[],limitations:[NOTE],actions};
  const finish=()=>{reply.answer=lines.join('\n').slice(0,6000);reply.entity_id=entityId;reply.evidence=R.packet(records);reply.candidates=candidates.slice(0,R.LIMITS.candidates).map(n=>({id:n.id,name:n.name,path:n.path||'',type:n.type}));if(ix.data.knowledge_graph?.coverage?.complete!==true)reply.limitations.push('Graph coverage is partial or unavailable; absence of a relationship is not proof of independence.');return reply;};
  const functions=ix.ordered.filter(n=>n.type==='function'),scored=n=>n.metadata?.language==='C'&&n.metadata?.ml?.status==='analyzed'&&Number.isFinite(n.metadata.ml.model_probability);
  const repo=(facts)=>records.push({entity_id:'repository-summary',kind:'repository',name:R.clip?R.clip(ix.data.repository):String(ix.data.repository||'Repository').slice(0,256),path:null,line:null,facts});
  if(kind==='overview'){
   const s=ix.data.summary||{},st=ix.data.structural?.summary;
   lines.push(`${ix.data.repository||'This snapshot'} contains ${s.files??'unavailable'} inventoried files in ${s.directories??'unavailable'} directories, with ${s.total_lines??'unavailable'} physical lines.`,`${st?.analyzed_functions??'Unavailable'} C/Python functions were structurally analyzed. ${ix.data.structural?.hotspots?.length??'Unavailable'} retained structural hotspots are rule-based review indicators.`);
   repo([R.fact('Files',s.files),R.fact('Directories',s.directories),R.fact('Physical lines',s.total_lines),R.fact('Analyzed functions',st?.analyzed_functions)]);return finish();
  }
  if(kind==='languages'){lines.push(ix.data.languages?.length?ix.data.languages.map(l=>`${l.language}: ${l.files} files, ${l.lines??'unavailable'} physical lines`).join('\n'):'No language records are available.');repo((ix.data.languages||[]).slice(0,16).map(l=>R.fact(l.language,`${l.files} files; ${l.lines??'unavailable'} lines`)));return finish();}
  if(kind==='functions'){const n=ix.data.structural?.summary?.analyzed_functions;lines.push(`${n??'Unavailable'} functions were structurally analyzed; ${functions.length} function entities are retained for Jordan lookup.`);repo([R.fact('Analyzed functions',n),R.fact('Retained functions',functions.length)]);return finish();}
  if(['complexity','hotspots','risk','unscored'].includes(kind)){
   let list=functions;
   if(kind==='complexity')list=list.filter(n=>Number.isFinite(n.metadata?.cyclomatic_complexity)).sort((a,b)=>b.metadata.cyclomatic_complexity-a.metadata.cyclomatic_complexity||a.id.localeCompare(b.id));
   if(kind==='hotspots')list=list.filter(n=>ix.impact.hotspots.has(n.id));
   if(kind==='risk')list=list.filter(scored).sort((a,b)=>b.metadata.ml.model_probability-a.metadata.ml.model_probability||a.id.localeCompare(b.id));
   if(kind==='unscored')list=list.filter(n=>!scored(n));
   lines.push(`${list.length} retained functions match this investigation. Showing at most 6.`);
   for(const n of list.slice(0,6)){add(n);let detail=kind==='risk'?`uncalibrated C model estimate ${n.metadata.ml.model_probability.toFixed(3)}`:kind==='unscored'?'unscored':`complexity ${n.metadata?.cyclomatic_complexity??'unavailable'}`;const h=ix.impact.hotspots.get(n.id);if(h)detail+='; '+h.reasons.map(r=>r.explanation).join('; ');lines.push(`${n.name} — ${n.path||'path unavailable'}: ${detail}`);}
   if(!list.length)lines.push(kind==='risk'?'No genuine C-function scores are available. The model may be unavailable, or no eligible C functions were scored.':'No matching retained measurements are available.');
   if(list.length){entityId=list[0].id;candidates=list.slice(0,6);actions.push({label:'Who calls it?',question:'Who calls it?'},{label:'Potential impact',question:'What could be affected if I change it?'});}return finish();
  }
  if(kind==='architecture'){
   const components=[...ix.impact.components.values()].sort((a,b)=>(b.incoming_components+b.outgoing_components)-(a.incoming_components+a.outgoing_components)||a.id.localeCompare(b.id));
   lines.push(`${components.length} retained directory-based components; ${ix.data.architecture?.edges?.length??'unavailable'} aggregated directed relationships. These are observed static groupings, not inferred runtime services.`);
   for(const c of components.slice(0,5)){add(c);lines.push(`${c.name} (${c.path||'.'}): ${c.metrics?.files??'unavailable'} files, ${c.metrics?.functions??'unavailable'} functions, ${c.incoming_components??'unavailable'} incoming / ${c.outgoing_components??'unavailable'} outgoing component neighbors.`);}
   for(const cycle of (ix.data.architecture?.dependency_cycles||[]).slice(0,4))lines.push('Observed component dependency cycle: '+cycle.map(id=>ix.entities.get(id)?.name||id).join(' ↔ '));
   reply.limitations.push(ix.data.architecture?.coverage?.truncated?'Architecture output is truncated.':'Cycle groups are static dependency evidence, not runtime execution paths.');return finish();
  }
  if(kind==='coverage'){
   const g=ix.data.knowledge_graph?.coverage,st=ix.data.structural?.coverage,m=ix.data.defect_risk;
   lines.push(`Graph coverage: ${g?.complete?'complete within supported rules':'partial or unavailable'}; ${g?.analyzed_files??'unavailable'} files analyzed, ${g?.skipped_files??'unavailable'} skipped.`, `Structural truncation: ${st?.truncated??'unavailable'}. Model status: ${m?.status??'unavailable'}. ${m?.message||''}`, 'Dynamic dispatch, runtime behavior, full source explanations and confirmed vulnerability detection are unavailable. Unresolved and ambiguous references are not confirmed dependencies.');
   repo([R.fact('Graph complete',g?.complete),R.fact('Graph truncated',g?.truncated),R.fact('Model status',m?.status)]);return finish();
  }
  if(kind==='unsupported'){lines.push('Local Jordan supports repository summaries, languages, function counts, complexity, hotspots, C-model review signals, entity lookup, callers/callees, imports/includes, component dependencies, relationships between two quoted paths, and bounded change-impact investigations. Try “Who calls `parse_config`?” or select a real entity. I cannot infer implementation behavior from unavailable source bodies.');return finish();}
  const resolved=R.resolve(ix,q,context.entity_id);let matches=resolved.matches;
  if(kind==='between'){
   const terms=resolved.terms;if(terms.length!==2){lines.push('Quote exactly two file paths, for example: relationships between `app/main.py` and `lib/util.py`.');return finish();}
   const pair=terms.map(t=>R.search(ix,t).filter(h=>h.node.type==='file'&&h.rank===0).map(h=>h.node));
   if(pair.some(p=>p.length!==1)){lines.push('Each quoted path must identify one retained file.');candidates=pair.flat();return finish();}
   const [a,b]=pair.map(p=>p[0]);add(a);add(b);const owns=id=>ix.impact.owner.get(id)||id;
   const links=[...ix.impact.edges.values()].filter(e=>(owns(e.source)===a.id&&owns(e.target)===b.id)||(owns(e.source)===b.id&&owns(e.target)===a.id));
   lines.push(`${links.length} resolved semantic relationships connect these files (including cross-file calls). Showing at most 8.`);for(const e of links.slice(0,8)){records.push(R.edgeEvidence(ix,e));lines.push(`${ix.entities.get(e.source)?.name} → ${ix.entities.get(e.target)?.name} (${e.type})`);}return finish();
  }
  if(/\b(file|module)\b/i.test(q)||resolved.terms.some(t=>/\.(py|c|h|pyi)$/.test(t))){const files=matches.filter(n=>n.type==='file');if(files.length)matches=files;}
  if(matches.length!==1){lines.push(matches.length?'Several entities match. Select the intended path before continuing.':'No unique retained entity matches. Quote its exact name or path, or select an evidence item first.');candidates=matches;return finish();}
  const n=matches[0];entityId=n.id;add(n);
  if(kind==='entity'){
   lines.push(`${n.name} is a retained ${n.type} at ${n.path||'repository root'}.`);const ev=R.entityEvidence(n);for(const f of ev.facts)lines.push(`${f.label}: ${f.value}`);
   for(const r of ix.impact.hotspots.get(n.id)?.reasons||[])lines.push(r.explanation);
   lines.push('This describes extracted structure and relationships; I have not read a retained function body.');
  }
  if(['incoming','outgoing'].includes(kind)){
   const direction=kind==='incoming'?'upstream':'downstream';const impact=E.query(ix.impact,n.id,{depth:1,direction});
   lines.push(`${impact.records.length} direct ${direction==='upstream'?'dependents / callers':'dependencies / callees'} observed from the selected entity’s bounded membership. Arrows retain source → dependency direction.`);
   for(const e of impact.edges.slice(0,8)){records.push(R.edgeEvidence(ix,e));lines.push(`${ix.entities.get(e.source)?.name||e.source} → ${ix.entities.get(e.target)?.name||e.target} (${e.type}; ${e.occurrences} occurrence(s))`);}
   if(impact.coverage.truncated)reply.limitations.push('Relationship query reached a resource limit: '+impact.coverage.issues.join(', '));
   if(impact.references.length)lines.push(`${impact.summary.attributable_references} attributable unresolved/ambiguous/dynamic references are excluded from confirmed relationships.`);
  }
  if(kind==='impact'){
   const depth=Number(q.match(/\b([123])\s*(?:hop|step)/i)?.[1]||context.depth||1),direction=context.direction||'both',p=E.query(ix.impact,n.id,{depth,direction});
   lines.push(`Potential impact within ${p.depth} hop(s): ${p.summary.direct_upstream} direct and ${p.summary.transitive_upstream} transitive upstream dependents; ${p.summary.direct_downstream+p.summary.transitive_downstream} downstream dependencies. These are statically reachable entities, not predicted breakages.`);
   for(const r of (context.target_id?p.records.filter(r=>r.id===context.target_id):p.records).slice(0,5)){const chain=r.node_path.map(id=>ix.entities.get(id)?.name||id);lines.push(`${r.side}, ${r.distance} hop(s): ${chain.join(r.side==='upstream'?' ← ':' → ')}${r.other_paths_observed?' (additional paths observed)':''}`);for(const id of r.edge_path)records.push(R.edgeEvidence(ix,ix.impact.edges.get(id)));}
   reply.limitations.push(`Impact coverage: ${p.coverage.graph_complete?'supported graph complete':'partial graph'}; traversal ${p.coverage.truncated?'truncated: '+p.coverage.issues.join(', '):'within limits'}. Membership edges select seeds only; they do not propagate change.`);
   if(context.target_id&&!p.records.some(r=>r.id===context.target_id))lines.push('The requested path target is not reachable within the current retained query limits.');
   actions.push({label:'Open exact impact investigation',page:'blast-radius',id:n.id});
  }
  for(const [label,question]of [['Callers / dependents','Who calls it?'],['Callees / dependencies','What does it call?']])actions.push({label,question});
  return finish();
 }
 root.JordanLocal={intent,answer,NOTE};if(typeof module!=='undefined'&&module.exports)module.exports=root.JordanLocal;
})(globalThis);
