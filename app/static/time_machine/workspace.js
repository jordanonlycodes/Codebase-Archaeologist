(function(root){
 'use strict';
 const D=root.TimeMachineData,$=id=>document.getElementById(id),el=(tag,value,css)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=String(value);if(css)n.className=css;return n;};
 const button=(label,action)=>{const n=el('button',label);n.type='button';n.addEventListener('click',action);return n;};
 class TimeMachine{
  constructor(){this.epoch=0;this.requestController=null;this.history=null;this.selected=null;this.active=false;this.view='timeline';this.trees=new Map();this.comparison=null;this.comparisons=new Map();
   for(const view of ['timeline','churn','compare','evolution'])$('tm-tab-'+view).addEventListener('click',()=>{this.pausePlayback();this.view=view;this.directory='';this.render();});
   document.addEventListener('visibilitychange',()=>{if(document.hidden)this.pausePlayback();});
   $('tm-retry').addEventListener('click',()=>this.retryLast());$('tm-load').addEventListener('click',()=>this.load());$('tm-cancel').addEventListener('click',()=>this.cancel());
   for(const id of ['tm-search','tm-from','tm-to'])$(id).addEventListener(id==='tm-search'?'input':'change',()=>{clearTimeout(this.debounce);this.debounce=setTimeout(()=>this.render(),id==='tm-search'?160:0);});
   $('tm-clear').addEventListener('click',()=>{this.fileScope=null;this.pendingPath=null;for(const id of ['tm-search','tm-from','tm-to'])$(id).value='';this.directory='';this.render();});
  }
  initialize(analysis,store,saved,handoff){this.destroy();this.active=true;this.analysis=analysis;this.store=store;this.source=analysis.source;this.fileScope=saved?.fileScope||null;this.pendingPath=null;this.history=null;this.selected=null;this.directory='';this.view=['timeline','churn','compare','evolution'].includes(saved?.view)?saved.view:'timeline';this.metric=saved?.metric||'touches';this.directory=saved?.directory||'';this.base=saved?.base;this.head=saved?.head;this.comparison=null;this.comparisons.clear();this.api=null;this.cooldownUntil=0;this.lastAttempt=null;$('tm-retry').hidden=true;$('tm-error').hidden=true;this.trees.clear();this.savedViewport=saved?.viewport;
   for(const [id,key]of [['tm-search','query'],['tm-from','from'],['tm-to','to']])$(id).value=typeof saved?.[key]==='string'?saved[key].slice(0,256):'';
   this.supported=this.source?.type==='github'&&/^[0-9a-f]{40}$/.test(this.source.snapshot_commit||'')&&/^https:\/\/github\.com\/[a-z0-9-]+\/[a-z0-9_.-]+$/i.test(this.source.url||'');
   $('tm-api-status').textContent=this.supported?'GitHub API · not checked':'GitHub history unavailable for ZIP snapshots';$('tm-load').disabled=!this.supported;$('tm-results').hidden=true;$('tm-empty').hidden=false;
   $('tm-source').textContent=this.supported?`${this.source.owner}/${this.source.name} · pinned ${this.source.snapshot_commit.slice(0,12)}`:'ZIP snapshot · no genuine Git history retained';
   $('tm-empty-copy').textContent=this.supported?'Retrieve an explicit, bounded ancestor window from the pinned GitHub snapshot. This fetches history; it does not repeat current-code analysis.':'Ordinary ZIP archives contain files, not genuine Git ancestry. Time Machine never invents commits from archive timestamps.';
   if(this.supported&&analysis.history?.anchor===this.source.snapshot_commit&&analysis.history.repository_url===this.source.url&&Array.isArray(analysis.history.commits)){this.history=analysis.history;for(const tree of (this.history.revision_trees||[]).slice(-3))if(this.history.commits.some(c=>c.sha===tree.revision)&&Array.isArray(tree.files)&&tree.files.length<=5000)this.trees.set(tree.revision,tree);this.selected=this.history.commits.find(c=>c.sha===saved?.selected)?.sha||this.history.commits[0]?.sha;this.apiStatus(null,true);this.render();}
   if(handoff?.id){const node=analysis.knowledge_graph?.nodes.find(n=>n.id===handoff.id);if(node?.type==='file'){this.pendingPath=node.path;this.applyPath();this.render();}}

  }
  state(){return {selected:this.selected,view:this.view,fileScope:this.fileScope,metric:this.metric,directory:this.directory,base:this.base,head:this.head,viewport:this.timeline?.viewport||this.savedViewport,from:$('tm-from').value,to:$('tm-to').value,query:$('tm-search').value};}
  applyPath(){if(!this.pendingPath||!this.history)return;const observed=new Set(this.history.commits.flatMap(c=>c.files.flatMap(f=>[f.path,f.previous_path].filter(Boolean))));const roots=new Set(this.analysis.files.map(f=>f.path.split('/')[0]));const stripped=roots.size===1?this.pendingPath.split('/').slice(1).join('/'):null;this.fileScope=observed.has(this.pendingPath)?this.pendingPath:stripped&&observed.has(stripped)?stripped:null;if(this.fileScope)$('tm-search').value='';else $('tm-search').value=this.pendingPath;}
  filtered(){const rows=D.filter(this.history,{from:$('tm-from').value,to:$('tm-to').value,query:$('tm-search').value});return this.fileScope?rows.filter(c=>c.files.some(f=>f.path===this.fileScope||f.previous_path===this.fileScope)):rows;}

  apiStatus(meta,cached=false){
   if(meta&&typeof meta==='object')this.api=meta;
   const api=this.api||{},parts=[cached?'Using cached evidence':'GitHub API'];
   parts.push(api.state==='limited'?'limited':api.state==='connected'?'connected':api.state==='unavailable'?'temporarily unavailable':'status not checked');
   if(Number.isInteger(api.remaining)&&api.remaining>=0)parts.push(`${api.remaining} requests last reported remaining`);
   if(Number.isFinite(api.reset_at)&&api.reset_at>0&&Number.isFinite(new Date(api.reset_at*1000).getTime()))parts.push('reported reset '+new Date(api.reset_at*1000).toLocaleString());
   if(Number.isFinite(api.retry_at)&&api.retry_at*1000>Date.now()){
    this.cooldownUntil=api.retry_at*1000;
    parts.push((api.cooldown_source==='reported'?'retry no earlier than ':'conservative retry backoff until ')+new Date(this.cooldownUntil).toLocaleTimeString());
   }
   $('tm-api-status').textContent=parts.join(' · ');
  }
  cachedComparison(base,head){
   const key=base+':'+head,row=this.comparisons.get(key);
   if(!row)return null;if(row.expires<=Date.now()){this.comparisons.delete(key);return null;}
   this.comparisons.delete(key);this.comparisons.set(key,row);return row.value;
  }
  rememberComparison(value){
   const key=value.base+':'+value.head,size=new TextEncoder().encode(JSON.stringify(value)).length;
   if(size>2097152)return;
   this.comparisons.delete(key);this.comparisons.set(key,{value,size,expires:Date.now()+120000});
   while(this.comparisons.size>3||[...this.comparisons.values()].reduce((n,r)=>n+r.size,0)>2097152)this.comparisons.delete(this.comparisons.keys().next().value);
  }
  request(kind,extra={}){
   const key=JSON.stringify([this.source.url,this.source.snapshot_commit,kind,Object.entries(extra).sort(([a],[b])=>a.localeCompare(b))]);
   if(this.pendingKey===key&&this.pendingRequest)return this.pendingRequest;
   const cached=kind==='tree'?this.trees.get(extra.revision):kind==='compare'?this.cachedComparison(extra.base,extra.head):null;
   if(cached){this.cancel();$('tm-error').hidden=true;$('tm-retry').hidden=true;this.apiStatus(null,true);$('tm-status').textContent='Using loaded historical evidence. No GitHub request was made.';return Promise.resolve(cached);}
   this.lastAttempt={kind,extra:{...extra}};
   if(this.cooldownUntil>Date.now()){
    this.error('GitHub cooldown is active until '+new Date(this.cooldownUntil).toLocaleString()+'. Loaded history, trees and comparisons remain usable. Retry afterward; availability is not guaranteed.');$('tm-retry').hidden=false;return Promise.resolve(null);
   }
   this.cancel();const controller=new AbortController();this.requestController=controller;this.pendingKey=key;
   const generation=this.epoch,timer=setTimeout(()=>controller.abort(),65000);
   $('tm-cancel').hidden=false;$('tm-load').disabled=true;for(const id of ['tm-tree-load','tm-compare'])if($(id))$(id).disabled=true;
   $('tm-error').hidden=true;$('tm-retry').hidden=true;$('tm-api-status').textContent='GitHub API · loading historical evidence';
   $('tm-status').textContent=`Retrieving Git ${kind==='load'?'history':kind} for the pinned repository. Valid server caches are reused; current analysis is unchanged.`;
   this.pendingRequest=(async()=>{
    try{
     const response=await fetch('/api/history/'+kind,{method:'POST',credentials:'same-origin',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({url:this.source.url,anchor:this.source.snapshot_commit,...extra})});
     const body=await response.json();
     if(!this.active||generation!==this.epoch||this.requestController!==controller)return null;
     let api;try{api=JSON.parse(response.headers?.get?.('X-History-API')||'null');}catch{}
     if(!response.ok){this.apiStatus(body.error?.api||{state:'unavailable'});throw Error(body.error?.message||'History retrieval failed.');}
     this.apiStatus(api,api?.cache==='hit'||api?.cache==='coalesced');
     if(kind==='compare'){
      if(body.base!==extra.base||body.head!==extra.head||body.repository_url!==this.source.url||!Array.isArray(body.files))throw Error('Comparison identity mismatch.');
      this.rememberComparison(body);
     }
     $('tm-status').textContent='Historical evidence retrieved. Coverage and measurement gaps remain explicit.';return body;
    }catch(error){
     if(this.active&&generation===this.epoch){this.error(controller.signal.aborted?'History retrieval cancelled or timed out. Existing evidence is preserved.':error.message);$('tm-retry').hidden=false;if(!this.api||this.api.state!=='limited')this.apiStatus({state:'unavailable'});}
     return null;
    }finally{
     clearTimeout(timer);if(this.requestController===controller){this.requestController=null;this.pendingRequest=null;this.pendingKey=null;$('tm-cancel').hidden=true;$('tm-load').disabled=!this.supported;this.buttonsReady();}
    }
   })();return this.pendingRequest;
  }
  async compare(){
   const base=this.base,head=this.head,value=await this.request('compare',{base,head});
   if(!value||!this.active||this.base!==base||this.head!==head)return;
   this.comparison=value;this.comparePage=0;this.render();
  }
  retryLast(){const attempt=this.lastAttempt;if(!attempt)return;if(attempt.kind==='load')this.load();else if(attempt.kind==='tree')root.TimeMachineEvolution.retrieve(this,attempt.extra.revision);else this.compare();}
  async load(){if(!this.supported)return;const value=await this.request('load');if(!value)return;if(value.anchor!==this.source.snapshot_commit||value.repository_url!==this.source.url||!Array.isArray(value.commits)){this.error('History identity did not match the active repository.');return;}
   if(this.history&&value.commits.length<this.history.commits.length){this.error('A smaller partial history window was returned. The previously loaded, larger window remains available.');return;}
   this.history=value;this.analysis.history=value;this.selected=value.commits.some(c=>c.sha===this.selected)?this.selected:value.commits[0]?.sha;this.applyPath();
   const retained=new Set(value.commits.map(c=>c.sha));for(const id of this.trees.keys())if(!retained.has(id))this.trees.delete(id);
   value.revision_trees=[...this.trees.values()];this.render();try{await this.store.saveHistory(value);}catch(error){this.error('History is available for this page but could not be retained: '+error.message);}
  }
  error(message){$('tm-error').textContent=message;$('tm-error').hidden=false;}
  render(){if(!this.active||!this.history)return;$('tm-empty').hidden=true;$('tm-results').hidden=false;const commits=this.filtered(),rows=D.churn(commits),summary=$('tm-summary');summary.replaceChildren();for(const [value,label]of [[commits.length,'commits matching history filters'],[rows.length,'historical file paths'],[commits.filter(c=>c.parents.length>1).length,'observed merge commits'],[new Set(commits.map(c=>c.author)).size,'author display names']]){const cell=el('div');cell.append(el('strong',value),el('span',label));summary.append(cell);}
   $('tm-coverage').textContent=`${this.fileScope?'Path focus: '+this.fileScope+'. ':''}${this.history.coverage.scope} ${this.history.coverage.complete_ancestry?'Retained parent evidence closes ancestry.':'Partial history.'} ${this.history.coverage.issues.join(' · ')}. Dates use committer time / UTC; change counts are not productivity or defect measures.`;
   for(const v of ['timeline','churn','compare','evolution'])$('tm-tab-'+v).setAttribute('aria-pressed',String(v===this.view));
   this.draw(commits);if(this.view==='compare'&&this.comparison?.files.length)root.TimeMachineStudio.inspectChange(this,this.comparison.files[0]);else this.inspectCommit(this.history.commits.find(c=>c.sha===this.selected)||commits[0]);
  }
  draw(commits){
   this.map?.destroy();this.map=null;
   if(this.view!=='timeline'){if(this.timeline){this.savedViewport={...this.timeline.viewport};this.timeline.destroy();this.timeline=null;}if(this.view==='churn')root.TimeMachineStudio.churn(this,commits);else if(this.view==='evolution')root.TimeMachineEvolution.draw(this);else root.TimeMachineStudio.comparison(this);return;}
   if(!this.timeline)this.timeline=new root.TimeMachineTimeline($('tm-view'),$('tm-view-controls'),$('tm-secondary'),sha=>{this.selected=sha;this.render();},month=>{const end=new Date(month+'-01T00:00:00Z');end.setUTCMonth(end.getUTCMonth()+1);end.setUTCDate(0);$('tm-from').value=month+'-01';$('tm-to').value=end.toISOString().slice(0,10);this.render();});
   this.timeline.draw(commits,this.selected);
   if(this.savedViewport&&Number.isFinite(this.savedViewport.x)&&Number.isFinite(this.savedViewport.w)){this.timeline.viewport={x:this.savedViewport.x,w:Math.max(180,Math.min(this.timeline.world*1.15,this.savedViewport.w))};this.timeline.update();this.savedViewport=null;}
  }

  inspectCommit(c){const panel=$('tm-inspection');panel.replaceChildren();if(!c){panel.append(el('p','Select a retained commit to inspect its evidence.'));return;}panel.append(el('p',c.parents.length>1?'MERGE / OBSERVED PARENTS':'COMMIT / HISTORICAL EVIDENCE','kicker'),el('h3',c.subject),el('div',c.sha,'tm-code'));const dl=el('dl');for(const [key,value]of [['Author',c.author],['Author date',c.author_date],['Committer date',c.committer_date],['Parents',c.parents.length?c.parents.join('\n'):'Initial commit'],['Changed files',c.files.length+(c.files_complete?'':' · incomplete')]])dl.append(el('dt',key),el('dd',value));panel.append(dl);if(!this.filtered().some(n=>n.sha===c.sha))panel.append(el('p','This selected commit is outside the active history filters.'));panel.append(button('Inspect this exact revision tree',()=>{this.pausePlayback();this.selected=c.sha;this.view='evolution';this.directory='';this.render();}),button('Use as comparison base',()=>{this.base=c.sha;this.view='compare';this.render();}));for(const f of c.files.slice(0,50))panel.append(button(`${f.status} · ${f.path}`,()=>this.inspectFile(f.path)));if(c.files.length>50)panel.append(el('p','Inspector shows 50 files; the retained list is in JSON export.'));}
  inspectFile(path){const rows=D.churn(this.filtered()),row=rows.find(r=>r.path===path);if(!row)return;const panel=$('tm-inspection');panel.replaceChildren(el('p','HISTORICAL PATH / OBSERVED WINDOW','kicker'),el('h3',path.split('/').at(-1)),el('div',path,'tm-code'));const dl=el('dl');for(const [k,v]of [['Commit touches',row.touches],['Added lines',row.additions??'Unavailable / incomplete'],['Deleted lines',row.deletions??'Unavailable / incomplete'],['Unmeasured commits',row.unmeasured],['Observed prior paths',row.previous.join(', ')||'None recorded']])dl.append(el('dt',k),el('dd',v));panel.append(dl,el('p','Churn records changes, not defects. Rename continuity is not guessed across ambiguous paths.'));for(const id of row.commits.slice(0,24)){const c=this.history.commits.find(c=>c.sha===id);panel.append(button(c.subject,()=>{this.selected=id;this.render();}));}const current=D.currentFile(this.analysis,path);if(current)for(const [page,label]of [['graph','Inspect current dependency context'],['heatmaps','Inspect current file metrics']])panel.append(button(label+' ↗',()=>root.WorkspaceNavigation.open(page,current.id)));panel.append(el('p','Current metrics describe the imported anchor, not this file’s historical versions.'));}
  pausePlayback(){clearTimeout(this.playTimer);this.playTimer=null;this.playing=false;const control=$('tm-play');if(control){control.textContent='Play loaded revisions';control.setAttribute('aria-pressed','false');}}
  togglePlayback(){if(this.playing){this.pausePlayback();this.render();return;}if(root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return;const rows=D.chronology(this.history.commits).filter(c=>this.trees.has(c.sha));if(rows.length<2)return;this.playing=true;let at=Math.max(0,rows.findIndex(c=>c.sha===this.selected));const step=()=>{if(!this.active||document.hidden||this.view!=='evolution'){this.pausePlayback();return;}at=(at+1)%rows.length;this.selected=rows[at].sha;this.directory='';this.render();this.playTimer=setTimeout(step,1400);};this.playTimer=setTimeout(step,1400);this.render();}
  buttonsReady(){if($('tm-tree-load'))$('tm-tree-load').disabled=false;if($('tm-compare'))$('tm-compare').disabled=!this.base||this.base===this.head;}
  cancel(){const pending=!!this.requestController;this.epoch++;this.requestController?.abort();this.requestController=null;this.pendingRequest=null;this.pendingKey=null;if($('tm-cancel'))$('tm-cancel').hidden=true;if($('tm-load'))$('tm-load').disabled=!this.supported;this.buttonsReady();if(pending)$('tm-status').textContent='Historical retrieval cancelled. Existing evidence is preserved; the server request remains bounded.';}
  destroy(){this.pausePlayback();this.map?.destroy();this.map=null;this.timeline?.destroy();this.timeline=null;this.cancel();clearTimeout(this.debounce);clearTimeout(this.treeDebounce);this.active=false;this.comparisons.clear();}
 }
 root.timeMachine=new TimeMachine();
})(globalThis);
