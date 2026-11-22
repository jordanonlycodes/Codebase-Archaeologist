/* Self-contained feature controller, ready for a dedicated page. No repository requests. */
(function(root){
 'use strict';
 const A=root.ArchaeologistArchitecture,{Scene,svg}=root.ArchitectureScene,$=id=>document.getElementById(id);
 const el=(tag,value,css)=>{const node=document.createElement(tag);if(value!==undefined)node.textContent=String(value);if(css)node.className=css;return node;};
 const value=n=>n==null?'Unavailable':typeof n==='number'?new Intl.NumberFormat(undefined,{maximumFractionDigits:2}).format(n):n;
 const button=(label,action,css)=>{const b=el('button',label,css);b.type='button';b.addEventListener('click',action);return b;};
 class Explorer{
  constructor(){
   this.suspended=false;this.state=A.initial();this.ix=A.index(null);this.scene=null;this.key=null;this.items=new Map();this.edgeItems=new Map();this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
   for(const mode of ['architecture','heatmap'])$('ai-'+mode).addEventListener('click',()=>{if(root.WorkspaceNavigation){root.WorkspaceNavigation.open(mode==='heatmap'?'heatmaps':'architecture',this.state.directory);return;}this.state.view=mode;this.key=null;this.draw();});
   for(const [id,key]of [['ai-metric','metric'],['ai-area','area'],['ai-relationships','relationship']])$(id).addEventListener('change',()=>{this.state[key]=$(id).value;if(key!=='metric')this.key=null;this.draw();});
   let timer;this.cancelSearch=()=>clearTimeout(timer);$('ai-search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{this.state.query=$('ai-search').value;this.search();if(this.state.view==='architecture'){this.key=null;this.draw();}},150);});
   $('ai-fit').addEventListener('click',()=>this.scene?.reset());$('ai-zoom-in').addEventListener('click',()=>this.scene?.zoom(1.25));$('ai-zoom-out').addEventListener('click',()=>this.scene?.zoom(1/1.25));
   $('ai-reset').addEventListener('click',()=>{const mode=this.state.view;this.state=A.initial();this.state.view=mode;this.state.directory=this.ix.root?.id;this.key=null;$('ai-search').value='';this.cancelSearch();this.draw();});
   $('ai-focus').addEventListener('click',()=>{this.state.focus=!this.state.focus;this.key=null;this.draw();});
   $('ai-up').addEventListener('click',()=>{const n=this.ix.nodes.get(this.state.directory);if(n?.parent_id)this.openDirectory(n.parent_id);});
   for(const key of ['metric','area'])for(const [id,definition]of Object.entries(key==='metric'?A.METRICS:{physical_lines:{label:'Physical lines'},bytes:{label:'Bytes'}}))$('ai-'+key).append(new Option(definition.label,id));
   this.visible=false;this.observer=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;if(this.visible)this.draw();});this.observer.observe($('architecture-intelligence'));
  }
  set(data,graph,structural){
   this.cancelSearch();this.scene?.destroy();this.scene=null;this.key=null;this.items.clear();this.edgeItems.clear();this.state=A.initial();this.ix=A.index(data,graph);this.hotspots=new Map((structural?.hotspots||[]).map(h=>[h.function_id,h]));this.state.directory=this.ix.root?.id;
   $('ai-content').hidden=!data;$('ai-state').textContent=data?'Evidence assembled. Explore directory components and retained source measurements.':'Architecture intelligence is unavailable for this analysis.';
   $('ai-search').value='';$('ai-metric').value=this.state.metric;$('ai-area').value=this.state.area;$('ai-relationships').value='all';
   if(!data)return;
   const m=this.ix.root?.metrics;$('ai-ledger').textContent=`${value(m?.files)} retained files / ${value(m?.functions)} observed functions / ${value(data.summary.aggregate_edges)} component relationships`;
   const c=data.coverage;$('ai-coverage').textContent=`${c.retained_files}/${c.inventory_files} files retained · ${c.structural_measured_files} files with function measurements · ${c.graph_mapped_files} graph-mapped files. ${c.graph_complete?'Defined graph extraction complete.':'Graph evidence is partial or unavailable.'} ${c.truncated?'Architecture bounds reached. ':''}${c.unmapped_semantic_edges} unmapped semantic edges · ${c.omitted_component_edges} source edges omitted by aggregation limits. ${c.issues.join(' · ')}`;
   this.findings();this.search();this.draw();
  }
  selectComponent(id){this.state.component=id;this.state.selected=id;this.state.page=0;this.draw();}
  openDirectory(id){if(root.WorkspaceNavigation&&document.body.dataset.page==='architecture'){root.WorkspaceNavigation.open('heatmaps',id);return;}const n=this.ix.nodes.get(id);if(!n)return;this.state.directory=n.type==='directory'?id:n.parent_id;this.state.selected=id;this.state.component=n.component_id||[...this.ix.components.values()].find(c=>c.path===n.path)?.id||null;this.state.page=0;this.state.view='heatmap';this.key=null;this.draw();}
  graph(id){if(root.WorkspaceNavigation){root.WorkspaceNavigation.open('graph',id);return;}if(!id||!root.graphExplorer?.ix.nodes.has(id))return;root.graphExplorer.choose(id);$('knowledge-explorer').scrollIntoView({behavior:this.reduced?'auto':'smooth',block:'start'});}
  draw(){
   if(this.suspended||!this.ix.data)return;
   for(const mode of ['architecture','heatmap'])$('ai-'+mode).setAttribute('aria-pressed',String(this.state.view===mode));
   $('ai-heat-controls').hidden=this.state.view!=='heatmap';$('ai-arch-controls').hidden=this.state.view!=='architecture';$('ai-focus').disabled=!this.state.component;$('ai-focus').setAttribute('aria-pressed',String(this.state.focus));
   this.breadcrumbs();if(!this.visible){this.inspect();return;}
   if(!this.scene)this.scene=new Scene($('ai-canvas'),id=>this.state.view==='architecture'?this.selectComponent(id):this.openDirectory(id),id=>this.inspectEdge(id));
   this.state.view==='architecture'?this.architecture():this.heatmap();this.inspect();
  }
  architecture(){
   const view=A.componentView(this.ix,this.state),key=JSON.stringify(['components',this.state.relationship,view.components.map(c=>c.id),view.edges.map(e=>e.id)]);
   if(key!==this.key){
    this.key=key;this.items.clear();this.edgeItems.clear();this.scene.content.replaceChildren();this.positions=A.componentPositions(view);const routes=A.edgeRoutes(view,this.positions);
    for(const edge of view.edges){const a=this.positions.get(edge.source),b=this.positions.get(edge.target);const path=svg('path',{class:'ai-connection',d:routes.get(edge.id),'marker-end':'url(#architecture-arrow)','data-edge':edge.id,tabindex:0,role:'button','aria-label':`${edge.type}: ${edge.graph_edges} retained graph edges`});path.append(svg('title',{},`${this.ix.components.get(edge.source).path} → ${this.ix.components.get(edge.target).path}\n${edge.type}: ${edge.graph_edges} graph edges · ${edge.occurrences} occurrences`));this.scene.content.append(path);this.edgeItems.set(edge.id,path);}
    for(const component of view.components){const p=this.positions.get(component.id),g=svg('g',{transform:`translate(${p.x},${p.y})`,'data-entity':component.id,role:'button',tabindex:0,'aria-label':`${component.path}: ${component.metrics.files} files`});
     g.append(svg('path',{d:'M12,0 H214 L232,18 V116 Q232,128 220,128 H12 Q0,128 0,116 V12 Q0,0 12,0',class:'ai-component-shell'}),svg('path',{d:'M16,0 H88',class:'ai-component-accent'}),svg('title',{},`${component.path}\n${component.metrics.files} immediate files; ${value(component.metrics.functions)} observed functions`),svg('text',{x:16,y:29,class:'ai-component-tag'},component.path==='.'?'ROOT FILES':'DIRECTORY COMPONENT'),svg('text',{x:16,y:57,class:'ai-component-name'},component.name.length>22?component.name.slice(0,21)+'…':component.name),svg('text',{x:16,y:79,class:'ai-component-detail'},component.path.length>31?'…'+component.path.slice(-30):component.path),svg('text',{x:16,y:107,class:'ai-component-detail'},`${component.metrics.files} files · ${value(component.metrics.functions)} functions`));
     for(let i=0;i<Math.min(6,component.metrics.files);i++)g.append(svg('rect',{x:169+i*7,y:19,width:4,height:7,rx:1,class:'ai-member-mark'}));this.scene.content.append(g);this.items.set(component.id,g);
    }
    const points=[...this.positions.values()];this.scene.fit(points.length?{x:-40,y:-40,w:Math.max(...points.map(p=>p.x))+315,h:Math.max(...points.map(p=>p.y))+210}:{x:0,y:0,w:1000,h:600});
   }
   const connected=new Set([this.state.component]);for(const e of view.edges)if(e.source===this.state.component||e.target===this.state.component){connected.add(e.source);connected.add(e.target);}
   for(const [id,item]of this.items)item.setAttribute('class',`ai-component ${id===this.state.component?'is-selected':''} ${this.state.component&&!connected.has(id)?'is-dim':''}`);
   for(const edge of view.edges){const selected=edge.source===this.state.component||edge.target===this.state.component;this.edgeItems.get(edge.id).setAttribute('class',`ai-connection ${edge.type.toLowerCase()} ${edge.source===this.state.component?'is-outgoing':edge.target===this.state.component?'is-incoming':''} ${this.state.component&&!selected?'is-dim':''}`);}
   $('ai-view-status').textContent=`${view.components.length}/${this.ix.components.size} components · ${view.edges.length}/${this.ix.data.edges.length} aggregated relationships shown${view.truncated?' · Bounded subset; search or focus to explore.':''}${!view.components.length?' · No components match this view.':''}`;
   $('ai-legend').textContent='A component is a direct-parent-directory group, not an inferred layer. Solid pale links: CALLS · green: IMPORTS · dashed amber: INCLUDES. Selected outgoing: crimson · incoming: amber. Click a line to inspect retained source evidence.';
  }
  heatmap(){
   const map=A.treemap(this.ix,this.state.directory,this.state.area),key=`heat:${this.state.directory}:${this.state.area}`;
   if(this.key!==key){this.key=key;this.items.clear();this.scene.content.replaceChildren();const visibleParents=new Set(map.regions.map(r=>r.node.parent_id));for(const region of map.regions){const n=region.node,g=svg('g',{'data-entity':n.id,tabindex:0,role:'button','aria-label':`${n.type}: ${n.path}`});
     const box=svg('rect',{x:region.x,y:region.y,width:region.w,height:region.h,rx:n.type==='directory'?8:4,class:'ai-heat-region'}),title=svg('title');g.append(box,title);
     if(region.w>65&&region.h>24){const max=Math.max(3,Math.floor((region.w-16)/6.5)),label=n.name.length>max?n.name.slice(0,max-1)+'…':n.name;g.append(svg('text',{x:region.x+9,y:region.y+18,class:n.type==='directory'?'ai-folder-label':'ai-file-label'},`${n.type==='directory'?'▱ ':''}${label}`));}
     if((n.type==='file'||!visibleParents.has(n.id))&&region.w>90&&region.h>50)g.append(svg('text',{x:region.x+9,y:region.y+38,class:'ai-heat-value'}));this.scene.content.append(g);this.items.set(n.id,{group:g,box,title,region});}this.scene.fit({x:0,y:0,w:1000,h:600});}
   const metric=this.state.metric,visibleParents=new Set(map.regions.map(r=>r.node.parent_id)),maximum=metric==='max_c_function_score'?1:Math.max(0,...map.regions.filter(r=>!visibleParents.has(r.node.id)).map(r=>r.node.metrics[metric]??0));
   for(const [id,item]of this.items){const n=this.ix.nodes.get(id),tone=A.tone(n,metric,maximum);item.box.setAttribute('fill',n.type==='directory'&&visibleParents.has(n.id)?'#1d1e20':tone.fill);item.group.setAttribute('class',`ai-heat ${n.type} ${id===this.state.selected?'is-selected':''} ${tone.state}`);item.title.textContent=`${n.path}\n${A.METRICS[metric].label}: ${value(tone.value)}\n${tone.state} · ${tone.covered}/${tone.total} measured files\n${n.type==='directory'?'Click to open directory':'Click to inspect file'}`;const label=item.group.querySelector('.ai-heat-value');if(label)label.textContent=tone.value==null?tone.state:metric==='max_c_function_score'?tone.value.toFixed(3):value(tone.value);}
   $('ai-view-status').textContent=`${map.regions.length} rendered regions · ${map.entries} immediate entries in ${this.ix.nodes.get(this.state.directory)?.path||'.'} · At most two nested levels${map.truncated?' · Region limit reached; area is normalized among displayed sibling entries. Use directory drill-down or search.':''}`;
   $('ai-legend').textContent=`${A.METRICS[metric].label}: 0 → ${value(maximum)}${metric==='max_c_function_score'?' (estimated, uncalibrated)':''}. ${A.METRICS[metric].rule} Neutral means measured zero; hatching means unavailable/unscored (see tooltip for unsupported/partial coverage). Area: ${this.state.area==='bytes'?'bytes':'physical lines'}, minimum one unit per sibling entry for zero-size visibility. Colors use square-root intensity for non-ML values, linear intensity for ML scores. Expanded directory containers retain a neutral surface; collapsed directory regions show their measured aggregate. Non-ML scale follows visible leaf regions.`;
  }
  breadcrumbs(){const container=$('ai-breadcrumbs');container.replaceChildren();const nodes=A.breadcrumbs(this.ix,this.state.directory);for(const n of nodes)container.append(button(n.path==='.'?'Repository':n.name,()=>this.openDirectory(n.id)));$('ai-up').disabled=!this.ix.nodes.get(this.state.directory)?.parent_id;}
  search(){const results=this.state.query.trim()?A.search(this.ix,this.state.query):[];$('ai-search-results').replaceChildren(...results.map(n=>button(`${n.type==='directory'?'Directory':'File'} · ${n.path}`,()=>{this.state.query='';$('ai-search').value='';this.openDirectory(n.id);this.search();})));$('ai-search-results').hidden=!results.length;}
  findings(){
   const container=$('ai-findings');container.replaceChildren();for(const finding of this.ix.data.findings){const item=button(finding.title,()=>{this.state.view='architecture';this.state.query='';$('ai-search').value='';this.state.focus=true;this.selectComponent(finding.component_id);},'ai-finding');item.append(el('small',finding.text));container.append(item);}
   $('ai-cycle-note').textContent=this.ix.data.dependency_cycles.length?`${this.ix.data.dependency_cycles.length} observed component dependency cycle group(s). Cycles describe aggregated imports/includes, not guaranteed build/runtime cycles.`:'No multi-component import/include cycle was retained. Incomplete graph coverage can hide cycles.';
   for(const group of this.ix.data.dependency_cycles.slice(0,6))container.append(button('Cycle · '+group.map(id=>this.ix.components.get(id).path).join(' ↔ '),()=>{this.state.view='architecture';this.state.relationship='dependencies';$('ai-relationships').value='dependencies';this.state.query='';$('ai-search').value='';this.state.focus=false;this.selectComponent(group[0]);},'ai-cycle'));
  }
  inspectEdge(id){const edge=this.ix.data.edges.find(e=>e.id===id);if(!edge)return;const panel=$('ai-inspector');panel.replaceChildren(el('p',edge.type,'ai-kicker'),el('h3',`${this.ix.components.get(edge.source).path} → ${this.ix.components.get(edge.target).path}`),el('p',`${edge.graph_edges} retained graph edges; ${edge.occurrences} source occurrences. This is an aggregate, not an additional source relationship.`));this.evidence(panel,edge);}
  evidence(panel,edge){
   for(const id of edge.edge_ids){const original=this.ix.graphEdges.get(id);if(!original)continue;const detail=el('details'),summary=el('summary',`${original.type} · ${original.reference||'reference'} · ${original.occurrences} occurrence(s)`);detail.append(summary);for(const location of original.evidence||[])detail.append(el('p',`${location.path}:${location.line}:${location.column}`));if(original.evidence_truncated)detail.append(el('p','Source evidence locations are bounded in the graph.'));panel.append(detail);}
   if(edge.evidence_truncated)panel.append(el('p','Additional source-edge IDs are available in the retained knowledge graph; this evidence sample is bounded.','ai-note'));
  }
  inspect(){
   const panel=$('ai-inspector'),component=this.ix.components.get(this.state.selected),node=this.ix.nodes.get(this.state.selected);panel.replaceChildren();
   if(!component&&!node){panel.append(el('p','FOLLOW THE EVIDENCE','ai-kicker'),el('h3','Start with a component.'),el('p','Select a directory component or a heatmap region. Inspect its members, measured structure and observed relationships.','ai-note'));return;}
   const selected=component||node,m=selected.metrics,path=selected.path;panel.append(el('p',component?'DIRECTORY COMPONENT':node.type.toUpperCase(),'ai-kicker'),el('h3',selected.name),el('p',path,'ai-source-path'));
   const dl=el('dl');for(const [key,v]of Object.entries({'Files':m.files,'Observed functions':m.functions,'Physical lines':m.physical_lines,'Bytes':m.bytes,'Maximum function complexity':m.max_complexity,'Observed hotspot functions':m.hotspots,'Function-measured files':`${m.measured_files.functions||0}/${m.files}`,'Max C-function score':m.max_c_function_score==null?'Unscored':m.max_c_function_score.toFixed(3),'Scored C functions':m.scored_functions}))dl.append(el('dt',key),el('dd',value(v)));panel.append(dl,el('p','Max complexity and max C-function score are maxima of observed functions. Coverage may be partial. Neither is a confirmed defect or a directory defect probability.','ai-note'));
   if(node?.type==='file'&&root.activeAnalysis?.source?.type==='github'&&root.WorkspaceNavigation?.file(node.graph_id))panel.append(button('Explore file history',()=>root.WorkspaceNavigation.fileHistory(node.graph_id),'ai-link'));
   const impactId=component?.id||node?.graph_id;if(impactId&&root.WorkspaceNavigation?.askJordan)panel.append(button('Ask Jordan about this component / file',()=>root.WorkspaceNavigation.askJordan(impactId),'ai-link'));if(impactId)panel.append(button('Explore potential change impact',()=>root.WorkspaceNavigation?root.WorkspaceNavigation.open('blast-radius',impactId):root.impactExplorer?.open(impactId),'ai-link'));
   if(selected.graph_id){const b=button('Inspect in Knowledge Graph',()=>this.graph(selected.graph_id),'ai-link');b.disabled=!this.ix.graphNodes.has(selected.graph_id);panel.append(b);}
   if(component){
    const dir=this.ix.paths.get(path);if(dir)panel.append(button('Explore directory heatmap →',()=>this.openDirectory(dir.id),'ai-link'));
    panel.append(el('h4','Observed relationships'),el('p',`${component.intra_component_edges} graph edges stay within this component (${component.intra_component_occurrences} occurrences).`));
    for(const [heading,edges,incoming]of [['Depends / calls outward',this.ix.outgoing.get(component.id)||[],false],['Depended on / called by',this.ix.incoming.get(component.id)||[],true]]){
     panel.append(el('h4',`${heading} · ${edges.length} aggregates`));for(const edge of edges.slice(0,16)){const other=this.ix.components.get(incoming?edge.source:edge.target);panel.append(button(`${incoming?'←':'→'} ${other.path} · ${edge.type} · ${edge.graph_edges} edges`,()=>this.selectComponent(other.id)));const details=el('details');details.append(el('summary','Source evidence'));this.evidence(details,edge);panel.append(details);}if(edges.length>16)panel.append(el('p','More relationships are retained in JSON export.'));
    }
    panel.append(el('h4',`Unresolved / ambiguous references · ${component.unresolved_count}`));for(const id of component.unresolved_ids){const ref=this.ix.refs.get(id);if(ref)panel.append(el('p',`${ref.reference} · ${ref.status} · ${ref.evidence.path}:${ref.evidence.line}`,'ai-reference'));}if(component.unresolved_truncated)panel.append(el('p','Reference list bounded; consult knowledge graph export.'));
    const hot=component.function_ids.map(id=>this.hotspots.get(id)).filter(Boolean);if(hot.length){panel.append(el('h4','Structural review evidence'));for(const h of hot.slice(0,8)){const link=button(`${h.name} · ${h.reasons.map(r=>r.explanation).join(' ')}`,()=>this.graph(h.function_id));link.disabled=!this.ix.graphNodes.has(h.function_id);panel.append(link);}}
    if(component.function_ids.length){panel.append(el('h4','Function graph links'));for(const id of component.function_ids.slice(0,8)){const n=this.ix.graphNodes.get(id);if(n)panel.append(button(n.name,()=>this.graph(id)));}}
   }else if(node.type==='file')panel.append(el('p',`Structural status: ${node.structural_status}. ML coverage: ${node.ml_status}.`));
   const files=component?component.file_ids.map(id=>this.ix.nodes.get(id)).filter(Boolean):A.filesUnder(this.ix,node.id);this.members(panel,files);
  }
  members(panel,files){
   if(!files.length)return;this.state.page=Math.min(this.state.page,Math.max(0,Math.ceil(files.length/A.LIMITS.list)-1));panel.append(el('h4',`File inventory · ${files.length}`));for(const file of files.slice(this.state.page*A.LIMITS.list,(this.state.page+1)*A.LIMITS.list))panel.append(button(file.path,()=>this.openDirectory(file.id),'ai-file-link'));
   if(files.length>A.LIMITS.list){const nav=el('div',undefined,'ai-list-nav'),prev=button('Previous',()=>{this.state.page--;this.inspect();}),next=button('Next',()=>{this.state.page++;this.inspect();});prev.disabled=this.state.page===0;next.disabled=(this.state.page+1)*A.LIMITS.list>=files.length;nav.append(prev,el('span',`${this.state.page+1}/${Math.ceil(files.length/A.LIMITS.list)}`),next);panel.append(nav);}
  }
 }
 const explorer=new Explorer();root.renderArchitecture=(data,graph,structure)=>explorer.set(data,graph,structure);root.architectureExplorer=explorer;
})(globalThis);
