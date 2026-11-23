/* Shared controller: one canonical graph, interaction state and inspector for both adapters. */
(function(root){
  'use strict';
  const D=root.ArchaeologistGraph, $=id=>document.getElementById(id);
  const text=(tag,value,css)=>{const el=document.createElement(tag);if(value!==undefined)el.textContent=String(value);if(css)el.className=css;return el;};
  const metric=value=>value===null||value===undefined?'Unavailable':String(value);
  class Explorer {
    constructor(){
      this.suspended=false;this.state=D.initial();this.ix=D.index(null);this.adapter=null;this.epoch=0;this.notice='';this.timer=null;
      this.host=$('graph-canvas');this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
      this.tourRequest=0;
      this.tour=root.ArchaeologistUniverse?new root.ArchaeologistUniverse.Tour({onScene:scene=>this.tourScene(scene),onStatus:status=>this.tourStatus(status),onCancel:()=>this.adapter?.cancelCamera?.()}):null;
      $('universe-start').addEventListener('click',()=>this.startTour());
      $('universe-pause').addEventListener('click',()=>this.tour?.status==='playing'?this.tour.pause():this.tour?.resume());
      $('universe-next').addEventListener('click',()=>this.tour?.next());
      $('universe-exit').addEventListener('click',()=>{this.stopTour('Tour ended. Manual investigation is available.');$('universe-start').focus();});
      $('universe-frame').addEventListener('click',()=>{this.stopTour('Directory framing selected.');this.adapter?.focusCluster?.($('universe-cluster').value);});
      this.resize=new ResizeObserver(()=>this.adapter?.resize());this.resize.observe(this.host);
      this.supports3D=root.ArchaeologistThree.webgl();
      $('graph-3d').disabled=!this.supports3D;
      $('graph-3d').title=this.supports3D?'Orbit, pan and inspect in WebGL':'WebGL is unavailable on this device. 2D remains available.';
      for(const mode of ['2d','3d'])$('graph-'+mode).addEventListener('click',()=>this.switchMode(mode));
      const bindings={'graph-view':'view','graph-overlay':'overlay','graph-language':'language','graph-direction':'direction','graph-layout':'layout','graph-quality':'quality'};
      for(const [id,key]of Object.entries(bindings))$(id).addEventListener('change',()=>{if(key==='view')this.changeView($(id).value);else{this.state[key]=$(id).value;this.refresh();}});
      for(const [kind,values]of [['types',D.TYPES],['relations',D.RELATIONS]]){
        const container=$('graph-'+kind);
        for(const value of values){
          const label=text('label'),input=document.createElement('input');input.type='checkbox';input.value=value;input.checked=true;
          input.addEventListener('change',()=>{this.state[kind]=[...container.querySelectorAll('input:checked')].map(i=>i.value);this.refresh();});
          label.append(input,text('span',value));container.append(label);
        }
      }
      $('graph-search').addEventListener('input',()=>{clearTimeout(this.timer);this.timer=setTimeout(()=>{this.state.query=$('graph-search').value;this.state.focus=null;this.state.branch=null;this.refresh();this.adapter?.fit();},160);});
      $('graph-clear').addEventListener('click',()=>this.clear());
      $('graph-fit').addEventListener('click',()=>{this.stopTour('Fit selected.');this.adapter?.fit();});
      $('graph-reset').addEventListener('click',()=>{this.stopTour('Universe reset.');const {mode,quality}=this.state;this.state=D.initial();this.state.mode=mode;this.state.quality=quality;this.syncControls();this.refresh();this.adapter?.reset();});
      $('graph-pan').addEventListener('click',()=>{this.panEnabled=!this.panEnabled;$('graph-pan').setAttribute('aria-pressed',String(this.panEnabled));this.adapter?.panMode?.(this.panEnabled);});
      $('graph-in').addEventListener('click',()=>{this.stopTour('Manual zoom selected.');this.adapter?.zoom(1.3);});
      $('graph-out').addEventListener('click',()=>{this.stopTour('Manual zoom selected.');this.adapter?.zoom(1/1.3);});
      $('graph-fullscreen').addEventListener('click',()=>this.fullscreen());
      $('graph-close-expanded').addEventListener('click',()=>this.collapse());
      for(const hops of [1,2])$('graph-hop-'+hops).addEventListener('click',()=>{if(this.state.selected){this.state.focus=this.state.selected;this.state.hops=hops;this.refresh();this.adapter?.fit();}});
      $('graph-focus').addEventListener('click',()=>{this.stopTour('Entity framing selected.');this.focusEntity(this.state.selected);});
      $('graph-group').addEventListener('click',()=>{const id=this.state.selected;if(!id)return;const values=new Set(this.state.collapsed);values.has(id)?values.delete(id):values.add(id);this.state.collapsed=[...values];this.state.focus=null;this.state.query='';this.syncControls();this.refresh();});
      $('graph-branch').addEventListener('click',()=>{this.state.view='knowledge';this.state.branch=this.state.selected;this.state.focus=null;this.state.query='';this.state.types=[...D.TYPES];this.state.relations=[...D.RELATIONS];this.state.language='';this.syncControls();this.refresh();this.adapter?.fit();});
      document.addEventListener('keydown',e=>{
        if(e.key==='Escape'&&['playing','paused'].includes(this.tour?.status)){this.stopTour('Tour ended with Escape.');$('universe-start').focus();}
        const workspace=$('graph-workspace');if(!workspace.classList.contains('is-expanded'))return;
        if(e.key==='Escape')this.collapse();
        if(e.key==='Tab'){const focusable=[...workspace.querySelectorAll('button, input, select, [tabindex]')].filter(el=>!el.disabled&&el.getClientRects().length&&el.tabIndex!==-1),first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}
      });
      this.observer=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;if(!this.suspended&&!document.hidden&&this.visible&&this.ix.nodes.size&&!this.adapter)this.switchMode(this.state.mode);});
      this.observer.observe($('knowledge-explorer'));
      this.visible=false;
    }
    setGraph(graph,preferences=null){
      root.RelicXRay?.reset();
      this.stopTour('Repository changed.');
      this.epoch++;clearTimeout(this.timer);this.adapter?.destroy();this.adapter=null;this.notice='';
      const quality=this.state.quality;this.ix=D.index(graph);this.state=D.initial();this.state.quality=quality;this.searchKey=null;this.inspectKey=null;this.view=null;this.groups=null;this.clusterKey=null;$('universe-start').disabled=true;
      if(this.ix.nodes.size>D.LIMITS.nodes)this.state.collapsed=this.ix.ordered.filter(n=>n.type==='file').map(n=>n.id);
      if(this.supports3D&&matchMedia('(min-width: 1000px) and (pointer: fine)').matches&&!this.reduced)this.state.mode='3d';
      // Restore preferences before any renderer starts, so saved 2D does not
      // fetch/initialize showcase 3D and unsupported saved 3D falls back honestly.
      if(preferences){for(const key of Object.keys(this.state))if(preferences[key]!==undefined)this.state[key]=preferences[key];this.state.mode=preferences.mode==='3d'&&this.supports3D?'3d':'2d';if(!this.ix.nodes.has(this.state.selected))this.state.selected=null;}
      this.syncControls();
      $('graph-content').hidden=!graph;
      $('graph-state').textContent=graph?(this.ix.nodes.size?'Graph ready. Explore retained source relationships.':'No graph nodes were retained. Review coverage and limits.'):'Knowledge graph unavailable for this analysis.';
      this.refresh();
      if(this.visible&&this.ix.nodes.size)this.switchMode(this.state.mode);
    }
    syncControls(){
      for(const [id,key]of Object.entries({'graph-view':'view','graph-overlay':'overlay','graph-direction':'direction','graph-search':'query','graph-layout':'layout','graph-quality':'quality'}))$(id).value=this.state[key];
      const languages=[...new Set(this.ix.ordered.map(D.language).filter(Boolean))].sort();
      $('graph-language').replaceChildren(new Option('All languages',''),...languages.map(l=>new Option(l,l)));$('graph-language').value=this.state.language;
      for(const key of ['types','relations'])for(const input of $('graph-'+key).querySelectorAll('input'))input.checked=this.state[key].includes(input.value);
      this.modeButtons();
    }
    modeButtons(){for(const mode of ['2d','3d'])$('graph-'+mode).setAttribute('aria-pressed',String(this.state.mode===mode));$('graph-pan').hidden=this.state.mode!=='3d';$('graph-pan').setAttribute('aria-pressed',String(!!this.panEnabled));}
    async switchMode(mode,tourLaunch=false){
      if(this.suspended||root.RelicXRay?.active)return;
      if(!tourLaunch)this.stopTour('Renderer changed.');
      if(mode==='3d'&&!this.supports3D){mode='2d';this.notice='WebGL unavailable; using 2D.';}
      const token=++this.epoch;
      this.adapter?.destroy();this.adapter=null;this.panEnabled=false;this.state.mode=mode;this.modeButtons();
      this.host.replaceChildren(text('p',mode==='3d'?'Loading local WebGL renderer…':'Preparing graph…','graph-canvas-message'));
      try{
        if(mode==='3d'){
          await root.ArchaeologistThree.load();
          if(token!==this.epoch)return;
          this.adapter=new root.ArchaeologistThree.Adapter(this.host,id=>this.select(id),this.reduced,()=>this.qualityStatus(),()=>{if(['playing','paused'].includes(this.tour?.status))this.stopTour('Manual navigation ended the tour.');},message=>{if(token!==this.epoch)return;this.notice=message;this.switchMode('2d');});
          this.notice='';
        }else this.adapter=new root.ArchaeologistSVG(this.host,id=>this.select(id));
        this.refresh();this.adapter.fit();root.WorkspaceMotion?.reveal(this.host,{key:'graph:'+mode,kind:'fade',duration:450});
      }catch(error){
        if(token!==this.epoch)return;
        this.adapter?.destroy();this.adapter=null;
        this.notice=mode==='3d'?'3D unavailable: '+error.message:'Graph rendering unavailable. Use the searchable node list below.';
        if(mode==='3d'){
          this.state.mode='2d';this.modeButtons();
          this.adapter=new root.ArchaeologistSVG(this.host,id=>this.select(id));
        }
        this.refresh();
      }
    }
    changeView(view){
      this.state.view=view;this.state.types=[...D.TYPES];this.state.relations=[...D.RELATIONS];this.state.language='';this.state.branch=null;
      const selected=this.ix.nodes.get(this.state.selected);
      if(selected&&!D.allowedNode(selected,this.state))this.state.selected=null;
      const focus=this.ix.nodes.get(this.state.focus);if(focus&&!D.allowedNode(focus,this.state))this.state.focus=null;
      this.notice='Perspective changed: entity, relationship and language filters reset. Layout selection and overlay preserved.';
      this.syncControls();this.refresh();this.adapter?.fit();
    }
    select(id){this.stopTour('Entity selected.');this.state.selected=id&&this.ix.nodes.has(id)?id:null;this.refresh();if(this.state.selected)this.focusEntity(this.state.selected);root.WorkspaceMotion?.reveal($('graph-inspection'),{key:'inspect:'+this.state.selected});}
    choose(id){
      this.stopTour('Search or related entity selected.');
      const n=this.ix.nodes.get(id);if(!n)return;
      // Search spans the full retained graph, even beyond current filters and bounds.
      this.state.selected=id;this.state.focus=id;this.state.branch=null;this.state.query='';this.state.types=[...D.TYPES];this.state.language='';
      if(!D.subset(this.ix,this.state).nodes.some(item=>item.id===id))this.state.view='knowledge';
      this.syncControls();this.refresh();this.focusEntity(id);root.WorkspaceMotion?.reveal($('graph-inspection'),{key:'inspect:'+id});
    }
    clear(){this.stopTour('Selection and filters cleared.');const {mode,quality}=this.state;this.state=D.initial();this.state.mode=mode;this.state.quality=quality;clearTimeout(this.timer);this.syncControls();this.refresh();this.adapter?.fit();}
    focusEntity(id){
      const n=this.ix.nodes.get(id);if(!n)return;
      if(this.state.mode==='3d'&&n.type==='repository')return this.adapter?.fit();
      const group=this.groups?.groups.find(g=>g.directoryId===id);
      if(this.state.mode==='3d'&&group)return this.adapter?.focusCluster?.(group.key);
      this.adapter?.focus(id);
    }
    filterIdentity(){return JSON.stringify([this.state.view,this.state.query,this.state.types,this.state.relations,this.state.language,this.state.layout,this.state.focus,this.state.branch,this.state.collapsed]);}
    stopTour(message=''){this.tourRequest++;this.tour?.stop(['playing','paused'].includes(this.tour.status)?message:'');}
    async startTour(){
      if(!this.tour||!this.view?.nodes.length)return;
      this.stopTour();const request=this.tourRequest;
      if(this.state.mode!=='3d'&&this.supports3D)await this.switchMode('3d',true);
      if(request!==this.tourRequest||this.suspended)return;
      this.tourFilterKey=this.filterIdentity();this.tour.start(root.ArchaeologistUniverse.scenes(this.view,this.ix));$('universe-pause').focus({preventScroll:true});
    }
    tourScene(scene){
      this.state.selected=scene.id||null;
      if(scene.kind==='cluster')this.state.selected=this.groups?.groups.find(g=>g.key===scene.key)?.directoryId||null;
      this.refresh();
      if(scene.kind==='cluster'){if(this.adapter?.focusCluster)this.adapter.focusCluster(scene.key);else if(this.state.selected)this.adapter?.focus(this.state.selected);else this.adapter?.fit();}
      else if(scene.id)this.adapter?.focus(scene.id);else this.adapter?.fit();
    }
    tourStatus(status){
      const active=['playing','paused'].includes(status.status);
      for(const id of ['universe-pause','universe-next','universe-exit'])$(id).hidden=!active;
      $('universe-tour').hidden=!active;$('universe-start').hidden=active;
      $('universe-pause').textContent=status.status==='paused'?'Resume tour':'Pause tour';$('universe-pause').setAttribute('aria-pressed',String(status.status==='paused'));
      if(active){$('universe-tour-step').textContent=`SCENE ${status.index+1} / ${status.total} · ${this.state.mode==='3d'?'SPATIAL EVIDENCE':'ACCESSIBLE 2D EVIDENCE'}`;$('universe-tour-title').textContent=status.scene.title;$('universe-tour-description').textContent=status.scene.description;}
      $('universe-tour-status').textContent=active?`${status.status==='paused'?'Paused':'Playing'} · ${status.manual?'Reduced motion: use Skip scene to advance.':'Pause, skip, exit or navigate manually at any time.'}`:status.message||'';
      $('universe-tour-status').hidden=!active&&!status.message;
      if(!active&&['universe-pause','universe-next','universe-exit'].includes(document.activeElement?.id))$('universe-start').focus({preventScroll:true});
    }
    syncUniverse(view){
      if(!root.ArchaeologistUniverse)return;
      this.groups=root.ArchaeologistUniverse.grouping(view,this.ix);
      const key=JSON.stringify(this.groups.groups.map(g=>[g.key,g.ids]));
      if(key!==this.clusterKey){this.clusterKey=key;const chosen=$('universe-cluster').value;$('universe-cluster').replaceChildren(new Option('Choose a visible directory',''),...this.groups.groups.map(g=>new Option(`${g.label} · ${g.ids.length} visible entities`,g.key)));$('universe-cluster').value=this.groups.groups.some(g=>g.key===chosen)?chosen:this.groups.groups[0]?.key||'';}
      $('universe-frame').disabled=this.state.mode!=='3d'||!this.groups.groups.length;$('universe-frame').title=this.state.mode==='3d'?'Frame the chosen directory grouping':'Directory camera framing is available in 3D Universe.';
      $('universe-start').disabled=!view.nodes.length;
      $('universe-grouping').textContent=`${this.groups.groups.length} visible directory grouping(s). Retained ownership or relative paths; not inferred runtime modules. Constellation labels are bounded to 12 (6 in Performance).`;
    }
    suspend(){this.suspended=true;this.stopTour('Navigation ended the tour.');clearTimeout(this.timer);this.observer.disconnect();this.resize.disconnect();this.epoch++;this.adapter?.destroy();this.adapter=null;}
    refresh(){
      if(!this.ix.graph)return;
      if(['playing','paused'].includes(this.tour?.status)&&this.filterIdentity()!==this.tourFilterKey)this.stopTour('View filters changed; tour ended.');
      const view=D.subset(this.ix,this.state);this.view=view;
      this.syncUniverse(view);
      if(this.adapter)this.adapter.set(view,this.ix,this.state);
      this.qualityStatus();
      const coverage=this.ix.graph.coverage||{};
      $('graph-counts').textContent=`${view.nodes.length} / ${this.ix.nodes.size} retained nodes · ${view.edges.length} / ${this.ix.edges.length} retained relationships · ${view.matching} nodes match the current view · ${view.groupHidden} hidden by collapsed groups`;
      $('graph-coverage').textContent=`${coverage.analyzed_files??'Unavailable'} analyzed files · ${coverage.skipped_files??'Unavailable'} skipped · ${coverage.unsupported_source_files??'Unavailable'} unsupported source files. ${coverage.complete?'Defined extraction coverage complete.':'Partial or unavailable extraction coverage.'} ${coverage.truncated?'Backend extraction limits reached. ':''}${view.truncated?'Visualization bounded; explore search results or a focused neighborhood. ':''}${(coverage.issues||[]).join(', ')} ${this.state.focus?'Focused on '+(this.ix.nodes.get(this.state.focus)?.name||'selected node')+'. ':''}${this.state.branch?'Branch: '+(this.ix.nodes.get(this.state.branch)?.name||'')+'. ':''}${this.notice}`;
      const summary=this.ix.graph.summary||{};
      for(const [id,key]of Object.entries({'graph-stat-nodes':'nodes','graph-stat-edges':'edges','graph-stat-calls':'resolved_call_edges','graph-stat-dependencies':'internal_dependency_edges'}))$(id).textContent=metric(summary[key]);
      $('graph-legend').textContent=({entity:'Entity shapes / size: repository ◇ 14 · directory □ 10 · file ▭ 8 · function ○ 6. Sizes encode type only.',complexity:'Complexity: green 1–5 · amber 6–10 · crimson 11–20 · magenta ≥21 · gray unavailable.',ml:'ML: crimson predicted defect-related · green predicted non-defect-related · gray unscored. C functions only; estimated, uncalibrated model probabilities.'})[this.state.overlay]+' Relations: containment dashed gray · definitions dashed mauve · calls pale crimson · imports green · includes dashed amber. Hotspots: crimson outline in 2D, larger marker in 3D. Selected: pale outline/marker; outgoing: crimson edges; incoming: amber edges. Unrelated entities are dimmed.';
      if(this.state.mode==='3d')$('graph-legend').textContent+=' Universe rings: solid large = selected, dashed = incoming, plain small = outgoing, double = both. Arrowheads follow actual directed edges. Directory captions are spatial annotations, not extra entities. Automatic knowledge layout uses directory constellations; other perspectives/layouts retain their analytical arrangement.';
      $('graph-empty').hidden=!!view.nodes.length;
      const searchKey=this.state.query+'|'+this.epoch;if(searchKey!==this.searchKey){this.searchKey=searchKey;this.searchResults();}
      const inspectKey=this.state.selected+'|'+this.epoch;if(inspectKey!==this.inspectKey){this.inspectKey=inspectKey;this.inspect();}
      const selected=this.ix.nodes.get(this.state.selected),group=selected&&['directory','file','repository'].includes(selected.type);
      $('graph-group').disabled=!group;$('graph-branch').disabled=!group;
      $('graph-group').textContent=this.state.collapsed.includes(this.state.selected)?'Expand group':'Collapse group';
      for(const id of ['graph-hop-1','graph-hop-2','graph-focus'])$(id).disabled=!this.state.selected;
    }
    qualityStatus(){
      $('graph-quality-status').textContent=this.adapter?.qualityDescription?.()||`3D quality preference: ${this.state.quality}. 2D uses SVG; the graphics profile applies when 3D is active. MSAA is not requested by the 3D renderer.`;
    }
    searchResults(){
      const result=D.search(this.ix,this.state.query);
      $('graph-search-count').textContent=this.state.query.trim()?`${result.total} retained matches (independent of filters); showing up to ${D.LIMITS.search}.`:`Browse retained nodes; showing ${result.nodes.length} of ${result.total}. Search includes hidden entities.`;
      $('graph-search-results').replaceChildren(...result.nodes.map(n=>{
        const button=text('button',`${n.name} · ${n.path||n.type}`);button.type='button';button.addEventListener('click',()=>this.choose(n.id));return button;
      }));
    }
    inspect(){
      const panel=$('graph-inspection'),n=this.ix.nodes.get(this.state.selected);panel.replaceChildren();
      if(!n){panel.append(text('h3','Inspect an entity'),text('p','Select a node or a search result to inspect actual relationships and source metrics.','muted'));return;}
      const m=n.metadata||{};
      const actions=text('div',undefined,'universe-inspector-actions');
      if(root.RelicXRay&&['directory','file','function'].includes(n.type)){const xray=text('button','Inspect in X-Ray','graph-related');xray.type='button';xray.addEventListener('click',()=>root.RelicXRay.open(n.id,xray));actions.append(xray);}
      panel.append(text('p','ENTITY INSPECTION','kicker'),text('span',n.type.toUpperCase(),'section-tag'),text('h3',n.name));
      const identity=text('p',n.path||'Repository anchor','universe-identity-path');panel.append(identity);
      const connections=text('div',undefined,'universe-connection-summary');connections.append(text('span',`← ${(this.ix.incoming.get(n.id)||[]).length} incoming`),text('span',`${(this.ix.outgoing.get(n.id)||[]).length} outgoing →`));panel.append(connections,text('p','Counts cover retained relationships; illumination follows the current filters.','muted'));
      if(root.activeAnalysis?.source?.type==='github'&&root.WorkspaceNavigation?.file(n.id)){const history=text('button','Explore file history','graph-related');history.type='button';history.addEventListener('click',()=>root.WorkspaceNavigation.fileHistory(n.id));actions.append(history);}
      if(root.WorkspaceNavigation?.askJordan){const ask=text('button','Ask Jordan about these relationships','graph-related');ask.type='button';ask.addEventListener('click',()=>root.WorkspaceNavigation.askJordan(n.id,{question:'What does this selected entity depend on?'}));actions.append(ask);}
      if(['function','file','directory'].includes(n.type)){const impact=text('button','Explore potential change impact','graph-related');impact.type='button';impact.addEventListener('click',()=>root.WorkspaceNavigation?root.WorkspaceNavigation.open('blast-radius',n.id):root.impactExplorer?.open(n.id));actions.append(impact);}
      if(root.WorkspaceNavigation){const component=root.WorkspaceNavigation.component(n.id),file=root.WorkspaceNavigation.file(n.id);if(component){const link=text('button','Inspect component architecture','graph-related');link.type='button';link.addEventListener('click',()=>root.WorkspaceNavigation.open('architecture',component));actions.append(link);}if(file){const link=text('button','Explore file heatmap','graph-related');link.type='button';link.addEventListener('click',()=>root.WorkspaceNavigation.open('heatmaps',file));actions.append(link);}}
      const section=(heading,values)=>{panel.append(text('h4',heading));const dl=text('dl',undefined,'graph-details');for(const [key,value]of Object.entries(values)){const dd=text('dd',metric(value));dd.title=metric(value);if(key==='Snapshot'||key==='Node ID')dd.className='graph-identifier';dl.append(text('dt',key),dd);}panel.append(dl);};
      section('Entity identity',{'Name':n.name,'Node ID':n.id});
      if(n.type==='repository'){
        const source=m.source||{};section('Source information',{'Source':source.type,'Repository':source.owner&&source.name?`${source.owner}/${source.name}`:source.filename,'Default branch':source.default_branch,'Snapshot':source.snapshot_commit});
      }else section('Source information',n.type==='directory'?{'Relative directory':n.path}:{'Relative path':n.path,'Language':m.language,...(n.type==='function'?{'Source lines':m.start_line==null?null:`${m.start_line}–${m.end_line}`}:{'Physical lines':m.lines,'Bytes':m.bytes})});
      if(n.type==='function'){
        section('Structural metrics',{'Status':m.status,'Cyclomatic complexity':m.cyclomatic_complexity,'Maximum nesting':m.max_nesting_depth,'Function span':m.span_lines,'Parameters':m.parameter_count});
        if(m.hotspots?.length){panel.append(text('h4','Structural review indicators'));for(const h of m.hotspots)panel.append(text('p',h.explanation));}
        panel.append(text('h4','ML defect risk'));
        if(m.language==='C'&&m.ml?.status==='analyzed'&&[0,1].includes(m.ml.predicted_class))panel.append(text('p',`${m.ml.predicted_class===1?'Predicted defect-related':'Predicted non-defect-related'} · Estimated model probability: ${Number.isFinite(m.ml.model_probability)?(m.ml.model_probability*100).toFixed(1)+'%':'Unavailable'}`));
        else panel.append(text('p','Unscored / unavailable. ML inference applies only to eligible C functions.','muted'));
        panel.append(text('p','Structural indicators and uncalibrated research estimates do not establish confirmed defects or vulnerabilities.','graph-caution'));
      }else if(n.type==='file'&&m.structural)section('File structural summary',{'Status':m.structural.status,'Analyzed functions':m.structural.summary?.analyzed_functions,'Maximum function complexity':m.structural.summary?.maximum_complexity});
      if(actions.children.length){panel.append(text('h4','Continue the investigation'),actions);}
      for(const [heading,edges,incoming]of [['Incoming',this.ix.incoming.get(n.id)||[],true],['Outgoing',this.ix.outgoing.get(n.id)||[],false]]){
        panel.append(text('h4',`${heading} relationships · ${edges.length}`));
        for(const e of edges.slice(0,D.LIMITS.details)){
          const related=this.ix.nodes.get(incoming?e.source:e.target),button=text('button',`${e.type} ${incoming?'←':'→'} ${related.name} · ${e.occurrences} occurrence(s)`,'graph-related');button.type='button';
          button.addEventListener('click',()=>this.choose(related.id));panel.append(button);
          if(e.evidence?.length){const details=text('details'),summary=text('summary',`${e.reference||e.type} · ${e.evidence.length} retained evidence location(s)${e.evidence_truncated?' · bounded':''}`);details.append(summary);for(const location of e.evidence)details.append(text('p',`${location.path}:${location.line}:${location.column}`));panel.append(details);}
        }
        if(edges.length>D.LIMITS.details)panel.append(text('p',`Showing ${D.LIMITS.details}; all retained relationships are in JSON export.`));
      }
      const refs=this.ix.references.get(n.id)||[];panel.append(text('h4',`Dependency / callable references · ${refs.length}`));
      for(const ref of refs.slice(0,D.LIMITS.details))panel.append(text('p',`${ref.type}: ${ref.reference} · ${ref.status} · ${ref.evidence.path}:${ref.evidence.line}`,'graph-reference'));
      if(refs.length>D.LIMITS.details)panel.append(text('p',`Showing ${D.LIMITS.details}; remaining references are in JSON export.`));
    }
    async fullscreen(){
      const el=$('graph-workspace');
      if(document.fullscreenElement===el){await document.exitFullscreen();return;}
      if(el.requestFullscreen){try{await el.requestFullscreen();return;}catch{/* CSS expansion remains available. */}}
      if(el.classList.contains('is-expanded')){this.collapse();return;}el.classList.add('is-expanded');el.setAttribute('role','dialog');el.setAttribute('aria-modal','true');$('graph-fullscreen').setAttribute('aria-expanded','true');$('graph-close-expanded').focus();this.adapter?.resize();
    }
    collapse(){if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});$('graph-workspace').classList.remove('is-expanded');$('graph-workspace').removeAttribute('role');$('graph-workspace').removeAttribute('aria-modal');$('graph-fullscreen').setAttribute('aria-expanded','false');this.adapter?.resize();$('graph-fullscreen').focus();}
  }
  const explorer=new Explorer();
  root.renderKnowledgeGraph=(graph,preferences)=>explorer.setGraph(graph,preferences);
  root.graphExplorer=explorer;
})(globalThis);
