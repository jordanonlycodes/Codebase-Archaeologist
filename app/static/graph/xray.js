/* RELIC // X-RAY: a projection of the canonical retained graph, never a new analysis. */
(function(root){
  'use strict';
  const TYPES=['repository','directory','file','function'],LIMIT=36;
  function lineage(ix,id){
    const path=[],seen=new Set();
    while(ix.nodes.has(id)&&!seen.has(id)&&path.length<128){seen.add(id);path.unshift(ix.nodes.get(id));id=ix.hierarchy.parent.get(id);}
    return path;
  }
  function descendants(ix,id){
    const found=new Set(),queue=[id];let cursor=0;
    // The canonical server graph is already bounded (12,000 nodes / 20,000 edges).
    // Visit each retained entity once so summary counts are exact, even above 6,000.
    while(cursor<queue.length){const next=queue[cursor++];if(found.has(next))continue;found.add(next);for(const child of ix.hierarchy.children.get(next)||[])if(!found.has(child))queue.push(child);}
    return ix.ordered.filter(n=>found.has(n.id)&&n.id!==id);
  }
  function projection(ix,id){
    const selected=ix.nodes.get(id)||null,path=lineage(ix,selected?.id),directory=[...path].reverse().find(n=>n.type==='directory'),file=[...path].reverse().find(n=>n.type==='file');
    const anchor=directory?.id||ix.ordered.find(n=>n.type==='repository')?.id;
    // Orphans remain accessible at root; no ownership is invented from a similar name.
    const children=ix.ordered.filter(n=>ix.hierarchy.parent.get(n.id)===anchor||(!directory&&!ix.hierarchy.parent.has(n.id)&&n.type!=='repository'));
    return {selected,path,directory,file,level:selected?.type==='function'?'function':file?'file':'directory',directories:children.filter(n=>n.type==='directory'),files:children.filter(n=>n.type==='file'),functions:file?ix.ordered.filter(n=>n.type==='function'&&ix.hierarchy.parent.get(n.id)===file.id):children.filter(n=>n.type==='function')};
  }
  function trace(ix,id,direction='both'){
    return ix.edges.filter(e=>(direction!=='out'&&e.target===id)||(direction!=='in'&&e.source===id)).map(e=>({edge:e,direction:e.source===id?'outgoing':'incoming',related:ix.nodes.get(e.source===id?e.target:e.source),kind:['CONTAINS','DEFINES'].includes(e.type)?'Structural ownership':'Static dependency'}));
  }
  function risk(n){
    const m=n?.metadata||{},p=m.ml?.model_probability;
    return n?.type==='function'&&m.language==='C'&&m.ml?.status==='analyzed'&&[0,1].includes(m.ml.predicted_class)&&Number.isFinite(p)&&p>=0&&p<=1?{score:p,predicted:m.ml.predicted_class}:null;
  }
  class History {
    constructor(){this.reset();}
    reset(){this.ids=[null];this.cursor=0;}
    push(id){if(this.ids[this.cursor]===id)return;this.ids=this.ids.slice(0,this.cursor+1);this.ids.push(id);if(this.ids.length>40)this.ids.shift();this.cursor=this.ids.length-1;}
    move(delta){this.cursor=Math.max(0,Math.min(this.ids.length-1,this.cursor+delta));return this.ids[this.cursor];}
  }
  const api={lineage,descendants,projection,trace,risk,History,LIMIT};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.ArchaeologistXRay=api;
  if(!root.document?.getElementById('xray-workspace')||!root.graphExplorer)return;
  const $=id=>document.getElementById(id),el=(tag,value,cls)=>{const n=document.createElement(tag);if(value!=null)n.textContent=String(value);if(cls)n.className=cls;return n;};
  class XRay {
    constructor(explorer){
      this.explorer=explorer;this.active=false;this.history=new History();this.animations=[];this.tracing=false;this.direction='both';this.media=matchMedia('(prefers-reduced-motion: reduce)');
      this.onReduced=()=>this.cancel();this.media.addEventListener?.('change',this.onReduced);
      this.bind('xray-activate',()=>this.open(this.explorer.state.selected,$('xray-activate')));
      this.bind('xray-exit',()=>this.exit());this.bind('xray-root',()=>this.navigate(null));this.bind('xray-clear',()=>this.navigate(null));
      this.bind('xray-back',()=>this.navigate(this.history.move(-1),false));this.bind('xray-forward',()=>this.navigate(this.history.move(1),false));
      this.bind('xray-universe',()=>this.locate());
      this.onKey=e=>{if(e.key==='Escape'&&this.active){e.preventDefault();if(this.tracing){this.tracing=false;this.render();$('xray-trace')?.focus();}else this.exit();}};
      document.addEventListener('keydown',this.onKey);
      this.onHidden=()=>{if(document.hidden)this.cancel();};document.addEventListener('visibilitychange',this.onHidden);
      root.addEventListener('pagehide',()=>this.cancel());
      this.reset();
    }
    bind(id,fn){$(id).addEventListener('click',()=>this.safe(fn));}
    safe(fn){try{fn();}catch{this.exit(false);$('graph-state').textContent='X-Ray could not open this evidence. The repository graph remains available.';}}
    reset(){this.cancel();this.active=false;this.history.reset();this.tracing=false;this.explorer.state.selected=null;$('xray-workspace').hidden=true;$('xray-activate').disabled=false;$('xray-activate').setAttribute('aria-expanded','false');$('xray-evidence').replaceChildren();}
    open(id=null,trigger=null){
      this.trigger=trigger||$('xray-activate');this.explorer.stopTour('X-Ray investigation opened.');
      if(document.fullscreenElement===$('graph-workspace'))document.exitFullscreen().catch(()=>{});
      if($('graph-workspace').classList.contains('is-expanded'))this.explorer.collapse();
      if(!this.explorer.adapter)this.explorer.epoch++; // Cancel only a pending renderer load, preserving an existing context-loss guard.
      this.explorer.adapter?.pause?.();this.explorer.adapter?.cancelCamera?.();
      this.active=true;$('graph-content').hidden=true;$('xray-workspace').hidden=false;$('xray-activate').setAttribute('aria-expanded','true');
      this.navigate(id);this.animate($('xray-workspace'),true);$('xray-title').focus({preventScroll:true});$('xray-workspace').scrollIntoView({block:'start',behavior:'instant'});
    }
    exit(restore=true){
      this.cancel();this.active=false;$('xray-workspace').hidden=true;$('graph-content').hidden=!this.explorer.ix.graph;$('xray-activate').setAttribute('aria-expanded','false');
      if(this.explorer.adapter){this.explorer.refresh();this.explorer.adapter.resize();this.explorer.adapter.wake?.();}
      else if(this.explorer.ix.nodes.size&&!this.explorer.suspended)this.explorer.switchMode(this.explorer.state.mode).then(()=>{if(!this.active)this.explorer.focusEntity(this.explorer.state.selected);});
      if(restore)(this.trigger?.isConnected?this.trigger:$('xray-activate')).focus({preventScroll:true});
    }
    locate(){
      const id=this.explorer.state.selected;if(!this.explorer.ix.nodes.has(id)){$('xray-status').textContent='Choose a retained entity to locate in Universe.';return;}
      this.exit(false);this.explorer.choose(id);this.explorer.host.scrollIntoView({block:'center',behavior:'instant'});this.explorer.host.focus({preventScroll:true});
    }
    navigate(id,push=true){
      if(id!=null&&!this.explorer.ix.nodes.has(id)){$('xray-status').textContent='This entity is not retained in the current repository. Choose another structure.';return;}
      this.explorer.state.selected=id;this.tracing=false;this.direction='both';if(push)this.history.push(id);this.render();this.animate($('xray-plates'));
      const selected=[...$('xray-plates').querySelectorAll('button')].find(b=>b.dataset.entityId===id);
      (selected||$('xray-title')).focus({preventScroll:true});
    }
    cancel(){for(const a of this.animations)a.cancel();this.animations=[];}
    animate(target,activation=false){
      this.cancel();if(this.media.matches||document.hidden||!target.animate)return;
      const a=target.animate([{opacity:.45,transform:`translateY(${activation?12:6}px)`},{opacity:1,transform:'translateY(0)'}],{duration:activation?650:320,easing:'cubic-bezier(.22,1,.36,1)'});this.animations.push(a);
      a.onfinish=()=>{this.animations=this.animations.filter(item=>item!==a);};
    }
    button(label,fn,cls=''){const b=el('button',label,cls);b.type='button';b.addEventListener('click',()=>this.safe(fn));return b;}
    list(host,nodes,empty){
      host.replaceChildren();if(!nodes.length){host.append(el('p',empty,'xray-empty'));return;}
      let page=0;const draw=()=>{host.replaceChildren();const items=el('div',null,'xray-entities');
        for(const n of nodes.slice(page*LIMIT,(page+1)*LIMIT)){
          const b=this.button('',()=>this.navigate(n.id),'xray-entity');b.dataset.entityId=n.id;b.setAttribute('aria-pressed',String(n.id===this.explorer.state.selected));
          const owned=this.explorer.ix.hierarchy.children.get(n.id)||[];b.append(el('span',n.type==='directory'?'DIR /':n.type==='file'?'FILE /':'FN /','kicker'),el('strong',n.name),el('small',n.path||'Location unavailable'));
          if(n.type==='file')b.append(el('small',`${n.metadata?.language||'Language unavailable'} · ${owned.filter(id=>this.explorer.ix.nodes.get(id)?.type==='function').length} retained functions`));
          items.append(b);
        }host.append(items);if(nodes.length>LIMIT){const pages=el('div',null,'xray-pagination'),back=this.button('← Previous',()=>{page--;draw();}),next=this.button('Next →',()=>{page++;draw();});back.disabled=page===0;next.disabled=(page+1)*LIMIT>=nodes.length;pages.append(back,el('span',`${page+1} / ${Math.ceil(nodes.length/LIMIT)} · ${nodes.length} entities`),next);host.append(pages);}};draw();
    }
    render(){
      const ix=this.explorer.ix,p=projection(ix,this.explorer.state.selected),n=p.selected;
      $('xray-back').disabled=this.history.cursor===0;$('xray-forward').disabled=this.history.cursor===this.history.ids.length-1;$('xray-universe').disabled=!n;
      const crumbs=$('xray-breadcrumb');crumbs.replaceChildren(this.button('REPOSITORY',()=>this.navigate(null)));
      for(const item of p.path.filter(n=>n.type!=='repository')){crumbs.append(el('span','/'),this.button(item.name,()=>this.navigate(item.id)));}
      for(const plane of $('xray-plates').querySelectorAll('[data-plane]')){const active=plane.dataset.plane===p.level;plane.classList.toggle('is-active',active);if(active)plane.setAttribute('aria-current','step');else plane.removeAttribute('aria-current');}
      $('xray-status').textContent=ix.nodes.size?`${p.level.toUpperCase()} / ${n?.path||n?.name||'Repository overview'} · ${ix.nodes.size} retained entities. Counts reflect extraction coverage, not all repository contents.`:'No retained architecture is available. Analyze a repository with supported source files to investigate its structure.';
      this.list($('xray-directories'),p.directories,p.directory?'No child directories retained here. The file layer shows this directory’s direct files.':'No directory nodes retained. Root files, if available, appear below.');
      this.list($('xray-files'),p.files,'No direct files retained in this directory. Choose a child directory or return to Structure.');
      this.list($('xray-functions'),p.functions,p.file?'No extracted functions retained for this file.':'Select a file to reveal its extracted functions.');
      this.inspect(p);
    }
    inspect(p){
      const ix=this.explorer.ix,n=p.selected,box=$('xray-evidence');box.replaceChildren(el('p','RELIC // EVIDENCE','kicker'));
      if(!n){box.append(el('h3','Begin an investigation'),el('p','Choose a real directory, file or function. Each structural plate is a different level of the same retained graph.'));return;}
      const m=n.metadata||{},dl=el('dl',null,'xray-facts'),fact=(key,value)=>{dl.append(el('dt',key),el('dd',value==null?'Unavailable':value));};
      box.append(el('span',n.type.toUpperCase(),'section-tag'),el('h3',n.name),el('p',n.path||'Repository root','xray-path'));
      fact('Entity ID',n.id);fact('Relative path',n.path);fact('Evidence scope','Retained static analysis');
      if(n.type==='directory'||n.type==='repository'){const owned=descendants(ix,n.id);fact('Retained files',owned.filter(n=>n.type==='file').length);fact('Retained functions',owned.filter(n=>n.type==='function').length);fact('Direct child directories',(ix.hierarchy.children.get(n.id)||[]).filter(id=>ix.nodes.get(id)?.type==='directory').length);}
      if(['file','function'].includes(n.type))fact('Language',m.language);
      if(n.type==='file')fact('Retained functions',p.functions.length);
      if(n.type==='function'){fact('Owning file',p.file?.path);fact('Source lines',m.start_line==null?null:`${m.start_line}–${m.end_line??m.start_line}`);fact('Cyclomatic complexity',m.cyclomatic_complexity);fact('Maximum nesting',m.max_nesting_depth);fact('Parameters',m.parameter_count);}
      fact('Incoming relationships',(ix.incoming.get(n.id)||[]).length);fact('Outgoing relationships',(ix.outgoing.get(n.id)||[]).length);
      if(n.type==='function'){
        const score=risk(n);box.append(el('h4','C FUNCTION DEFECT-RISK ESTIMATE'));
        if(score){box.append(el('strong',`${(score.score*100).toFixed(1)}%`,'xray-risk'),el('p',score.predicted===1?'Predicted defect-related pattern':'Predicted non-defect-related pattern'));}
        else box.append(el('p',m.language==='Python'?'Defect-risk prediction is not available for Python functions.':'No eligible C-model result is available for this function.'));
        box.append(el('p','Existing C-only Random Forest output, when available. An uncalibrated research estimate, not a confirmed defect or vulnerability. Structural metrics are not model explanations.','graph-caution'));
      }
      const identity=el('details',null,'xray-measurements');identity.append(el('summary','Identity & structural measurements'),dl);
      if(n.type!=='function')identity.open=true;
      box.append(identity);
      const traceButton=this.button(this.tracing?'Clear tracing':'Trace Dependencies',()=>{this.tracing=!this.tracing;this.render();$('xray-trace')?.focus();});traceButton.id='xray-trace';traceButton.setAttribute('aria-pressed',String(this.tracing));box.append(traceButton);
      if(!this.tracing)return;
      const controls=el('div',null,'xray-trace-controls');for(const [value,label]of [['both','All directions'],['in','← Incoming'],['out','Outgoing →']]){const b=this.button(label,()=>{this.direction=value;this.inspect(p);$('xray-direction-'+value)?.focus();});b.id='xray-direction-'+value;b.setAttribute('aria-pressed',String(this.direction===value));controls.append(b);}box.append(controls,el('p','DIRECT EVIDENCE / arrows preserve source → target. CONTAINS and DEFINES are ownership, not observed calls. No transitive paths are implied.','graph-caution'));
      const relations=trace(ix,n.id,this.direction),list=el('div',null,'xray-traces');
      if(!relations.length)list.append(el('p','No direct relationships retained in this direction. Absence of evidence is not evidence of independence.'));
      for(const item of relations.slice(0,40)){const {edge:e,related,direction,kind}=item,row=el('article',null,'xray-trace');row.append(el('span',`${direction==='incoming'?'← INCOMING':'OUTGOING →'} / ${e.type}`,'kicker'),el('p',kind),this.button(related.name,()=>this.navigate(related.id)));
        for(const evidence of (e.evidence||[]).slice(0,3))row.append(el('small',`${evidence.path}:${evidence.line??'?'}${evidence.column!=null?':'+evidence.column:''}`));list.append(row);}
      if(relations.length>40)list.append(el('p',`Showing 40 of ${relations.length} retained direct relationships; JSON export contains the remainder.`));
      const refs=ix.references.get(n.id)||[];if(refs.length)list.append(el('p',`${refs.length} unresolved or external references are not internal graph edges; inspect them in Universe or the JSON export.`));box.append(list);
    }
  }
  root.RelicXRay=new XRay(root.graphExplorer);
})(globalThis);
