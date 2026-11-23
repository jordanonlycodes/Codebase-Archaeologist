/* Deterministic presentation of retained evidence. No new entities or analysis. */
(function(root){
 'use strict';
 const cmp=(a,b)=>a<b?-1:a>b?1:0;
 const finite=p=>p&&['x','y','z'].every(k=>Number.isFinite(p[k]));
 function owner(node,ix){
  if(node.type==='repository')return null;
  if(node.type==='directory')return node;
  let current=node,seen=new Set();
  while(current&&!seen.has(current.id)){
   seen.add(current.id);if(current.type==='directory')return current;
   current=ix.nodes.get(ix.hierarchy?.parent.get(current.id));
  }
  return null;
 }
 function grouping(view,ix){
  const groups=new Map(),membership=new Map();
  for(const node of view.nodes){
   if(node.type==='repository')continue;
   const directory=owner(node,ix),path=directory?.path??(node.path?node.path.split('/').slice(0,-1).join('/'):null);
   const key=directory?'directory:'+directory.id:path===null?'unplaced':'path:'+path;
   const label=directory?(directory.path||directory.name):path===null?'Location unavailable':path||'Repository root';
   if(!groups.has(key))groups.set(key,{key,label,directoryId:directory?.id||null,basis:directory?'Retained directory ownership':path===null?'Missing location metadata':'Relative path grouping',ids:[]});
   groups.get(key).ids.push(node.id);membership.set(node.id,key);
  }
  const ordered=[...groups.values()].sort((a,b)=>cmp(a.label,b.label)||cmp(a.key,b.key));
  ordered.forEach(g=>g.ids.sort(cmp));return{groups:ordered,membership};
 }
 function constellation(view,ix){
  const {groups,membership}=grouping(view,ix),positions=new Map();
  // Each directory has its own nonoverlapping orbital cell. File/function ownership
  // determines internal rings. Angles/order are fixed by stable IDs, never randomness.
  const cols=Math.max(1,Math.ceil(Math.sqrt(groups.length))),radii=groups.map(g=>Math.max(70,Math.sqrt(g.ids.length)*24));
  const cell=Math.max(240,...radii.map(r=>r*2+110));
  groups.forEach((g,index)=>{
   const row=Math.floor(index/cols),col=index%cols,rows=Math.ceil(groups.length/cols);
   const center={x:(col-(cols-1)/2)*cell,y:((rows-1)/2-row)*cell*.72,z:(index%3-1)*55};
   g.center=center;g.radius=radii[index];
   const ids=new Set(g.ids),anchor=g.directoryId&&ids.has(g.directoryId)?g.directoryId:null;
   if(anchor)positions.set(anchor,{...center});
   const files=g.ids.filter(id=>ix.nodes.get(id)?.type==='file'),placed=new Set(anchor?[anchor]:[]);
   files.forEach((id,i)=>{
    const angle=(i/files.length)*Math.PI*2-.5,radius=Math.max(55,Math.sqrt(files.length)*30),p={x:center.x+Math.cos(angle)*radius,y:center.y+Math.sin(angle)*radius,z:center.z+(i%2?15:-15)};
    positions.set(id,p);placed.add(id);
    const functions=g.ids.filter(child=>ix.nodes.get(child)?.type==='function'&&ix.hierarchy?.parent.get(child)===id);
    functions.forEach((child,j)=>{const a=j/functions.length*Math.PI*2+.4,r=28+Math.sqrt(functions.length)*10;positions.set(child,{x:p.x+Math.cos(a)*r,y:p.y+Math.sin(a)*r,z:p.z+(j%3-1)*20});placed.add(child);});
   });
   const remaining=g.ids.filter(id=>!placed.has(id));
   remaining.forEach((id,i)=>{const angle=i*Math.PI*(3-Math.sqrt(5)),radius=34+Math.sqrt(i+1)*18;positions.set(id,{x:center.x+Math.cos(angle)*radius,y:center.y+Math.sin(angle)*radius,z:center.z+(i%5-2)*19});});
  });
  view.nodes.filter(n=>n.type==='repository').sort((a,b)=>cmp(a.id,b.id)).forEach((n,i)=>positions.set(n.id,{x:i*45,y:groups.length?Math.ceil(groups.length/cols)*cell*.42:0,z:90}));
  // Fixed occupancy grid separates real nodes without adding artificial links.
  const occupied=new Map();
  for(const id of [...positions.keys()].sort(cmp)){
   const p=positions.get(id);let key;
   do{key=[Math.round(p.x/18),Math.round(p.y/18),Math.round(p.z/18)].join(':');if(!occupied.has(key))break;p.z+=19;}while(true);
   occupied.set(key,id);
  }
  return{positions,groups,membership};
 }
 function illumination(view,id,direction='both'){
  const incoming=new Set(),outgoing=new Set(),edgeRoles=new Map();
  for(const e of view.edges){
   const a=typeof e.source==='object'?e.source.id:e.source,b=typeof e.target==='object'?e.target.id:e.target;
   let role='dim';
   if(id&&b===id&&direction!=='out'){incoming.add(a);role='incoming';}
   if(id&&a===id&&direction!=='in'){outgoing.add(b);role=role==='incoming'?'both':'outgoing';}
   edgeRoles.set(e.id,id?role:'normal');
  }
  const nodes=new Map(view.nodes.map(n=>[n.id,!id?'normal':n.id===id?'selected':incoming.has(n.id)&&outgoing.has(n.id)?'both':incoming.has(n.id)?'incoming':outgoing.has(n.id)?'outgoing':'dim']));
  return{nodes,edges:edgeRoles,incoming,outgoing};
 }
 function framing(nodes,camera,target,width,height,{fov=50,padding=1.18,minRadius=24}={}){
  const valid=nodes.filter(finite);if(!valid.length||!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)return null;
  const bounds=['x','y','z'].map(k=>[Math.min(...valid.map(n=>n[k])),Math.max(...valid.map(n=>n[k]))]);
  const center=Object.fromEntries(bounds.map(([a,b],i)=>[['x','y','z'][i],(a+b)/2]));
  const vertical=Math.tan((Number.isFinite(fov)&&fov>0&&fov<175?fov:50)*Math.PI/360),horizontal=vertical*width/height;
  let delta=finite(camera)&&finite(target)?{x:camera.x-target.x,y:camera.y-target.y,z:camera.z-target.z}:{x:0,y:0,z:1};
  let length=Math.hypot(delta.x,delta.y,delta.z);if(length<1e-6){delta={x:0,y:0,z:1};length=1;}
  const forward={x:delta.x/length,y:delta.y/length,z:delta.z/length};
  let right={x:forward.z,y:0,z:-forward.x},side=Math.hypot(right.x,right.z);if(side<1e-6){right={x:1,y:0,z:0};side=1;}right={x:right.x/side,y:0,z:right.z/side};
  const up={x:forward.y*right.z-forward.z*right.y,y:forward.z*right.x-forward.x*right.z,z:forward.x*right.y-forward.y*right.x};
  const dot=(a,b)=>a.x*b.x+a.y*b.y+a.z*b.z;
  // Fit perspective extents in camera coordinates; a bounding sphere wastes much
  // of a wide viewport. Include real marker padding and depth from every node.
  let distance=minRadius/Math.min(vertical,horizontal);
  for(const n of valid){const relative={x:n.x-center.x,y:n.y-center.y,z:n.z-center.z},depth=dot(relative,forward);distance=Math.max(distance,depth+(Math.abs(dot(relative,right))+16)/horizontal,depth+(Math.abs(dot(relative,up))+16)/vertical);}
  distance*=padding;
  const position=Object.fromEntries(['x','y','z'].map(k=>[k,center[k]+forward[k]*distance]));
  return finite(position)&&finite(center)?{position,target:center}:null;
 }
 function scenes(view,ix){
  if(!view.nodes.length)return[];
  const {groups}=grouping(view,ix),result=[{kind:'overview',title:'The repository universe',description:`${view.nodes.length} visible retained entities and ${view.edges.length} actual relationships. This is the current bounded view.`}];
  const major=[...groups].sort((a,b)=>b.ids.length-a.ids.length||cmp(a.label,b.label)||cmp(a.key,b.key))[0];
  if(groups.length>1&&major)result.push({kind:'cluster',key:major.key,title:major.label,description:`Largest visible directory grouping: ${major.ids.length} retained entities. Prominence means visible membership, not defect risk.`});
  const degree=new Map(view.nodes.map(n=>[n.id,0])),semantic=new Map(degree);
  for(const e of view.edges){degree.set(e.source,(degree.get(e.source)||0)+1);degree.set(e.target,(degree.get(e.target)||0)+1);if(['CALLS','IMPORTS','INCLUDES'].includes(e.type)){semantic.set(e.source,(semantic.get(e.source)||0)+1);semantic.set(e.target,(semantic.get(e.target)||0)+1);}}
  const connected=[...view.nodes].sort((a,b)=>(semantic.get(b.id)||0)-(semantic.get(a.id)||0)||(degree.get(b.id)||0)-(degree.get(a.id)||0)||cmp(a.id,b.id))[0];
  if(connected&&degree.get(connected.id)>0)result.push({kind:'relationships',id:connected.id,title:'Follow the evidence',description:`${connected.name}: ${degree.get(connected.id)} incident relationships in this view. Arrows show recorded direction; hierarchy and dependency types remain distinct.`});
  const entity=[...view.nodes].filter(n=>n.type==='function'||n.type==='file').sort((a,b)=>(a.type==='function'?0:1)-(b.type==='function'?0:1)||(degree.get(b.id)||0)-(degree.get(a.id)||0)||cmp(a.id,b.id))[0];
  if(entity)result.push({kind:'entity',id:entity.id,title:entity.name,description:`Inspect the retained ${entity.type} identity, source location and available evidence. Structural connections do not establish confirmed defects.`});
  if(result.length>1)result.push({kind:'return',title:'The full picture',description:'Return to the current graph view. Continue with search, directory framing or manual navigation.'});
  return result;
 }
 class Tour{
  constructor({env=root,onScene=()=>{},onStatus=()=>{},onCancel=()=>{}}={}){Object.assign(this,{env,onScene,onStatus,onCancel});this.status='idle';this.items=[];this.index=0;this.generation=0;this.clean=[];}
  snapshot(){return{status:this.status,index:this.index,total:this.items.length,scene:this.items[this.index]||null,manual:this.reduced()};}
  reduced(){return !!this.env.matchMedia?.('(prefers-reduced-motion: reduce)').matches;}
  start(items){
   this.stop();if(!items.length)return false;this.items=items;this.index=0;this.status=this.reduced()?'paused':'playing';
   const media=this.env.matchMedia?.('(prefers-reduced-motion: reduce)'),preference=()=>{if(media.matches)this.pause();};
   const visibility=()=>{if(this.env.document?.hidden)this.pause();},leave=()=>this.stop('Navigation ended the tour.');
   media?.addEventListener?.('change',preference);this.env.document?.addEventListener?.('visibilitychange',visibility);this.env.addEventListener?.('pagehide',leave);
   this.clean.push(()=>media?.removeEventListener?.('change',preference),()=>this.env.document?.removeEventListener?.('visibilitychange',visibility),()=>this.env.removeEventListener?.('pagehide',leave));
   this.show();return true;
  }
  cancelTimer(){this.generation++;this.env.clearTimeout(this.timer);this.timer=null;}
  show(){
   this.cancelTimer();if(!['playing','paused'].includes(this.status))return;
   this.onScene(this.items[this.index]);this.onStatus(this.snapshot());
   if(this.status==='playing'&&!this.reduced()){const version=this.generation;this.timer=this.env.setTimeout(()=>{if(version===this.generation&&this.status==='playing')this.next();},3800);}
  }
  next(){if(!['playing','paused'].includes(this.status))return;if(this.index+1>=this.items.length){this.stop('Tour complete.');return;}this.index++;this.show();}
  pause(){if(this.status!=='playing')return;this.cancelTimer();this.status='paused';this.onCancel();this.onStatus(this.snapshot());}
  resume(){if(this.status!=='paused')return;this.status=this.reduced()?'paused':'playing';this.show();}
  stop(message=''){this.cancelTimer();const active=['playing','paused'].includes(this.status);this.status='idle';this.clean.forEach(f=>f());this.clean=[];if(active)this.onCancel();this.onStatus({...this.snapshot(),message});}
  destroy(){this.stop();this.items=[];}
 }
 const api={grouping,constellation,illumination,framing,scenes,Tour,finite};root.ArchaeologistUniverse=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
