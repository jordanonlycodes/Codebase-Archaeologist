/* Immutable-response indexes and bounded spatial view models. */
(function(root){
 'use strict';
 const LIMITS=Object.freeze({components:24,edges:100,regions:160,depth:2,list:25,search:30});
 const METRICS={physical_lines:{label:'Physical lines',rule:'Inventory lines including code, comments and blanks.'},functions:{label:'Observed functions',rule:'Valid analyzed functions; coverage may be partial.'},max_complexity:{label:'Maximum function complexity',rule:'Maximum valid function complexity, not a sum or quality score.'},hotspots:{label:'Structural hotspot functions',rule:'Count of existing threshold-based structural review indicators.'},bytes:{label:'File size · bytes',rule:'Inventoried UTF-8 file bytes.'},max_c_function_score:{label:'Max observed C-function score',rule:'Maximum actual estimated C-function score. Not a file/directory defect probability; unscored regions remain unscored.'}};
 const initial=()=>({view:'architecture',selected:null,component:null,directory:null,metric:'max_complexity',area:'physical_lines',relationship:'all',query:'',page:0,focus:false});
 function index(data,graph){
  const nodes=new Map((data?.heatmap||[]).map(n=>[n.id,n])),components=new Map((data?.components||[]).map(c=>[c.id,c])),children=new Map(),incoming=new Map(),outgoing=new Map();
  for(const n of nodes.values()){if(!children.has(n.parent_id))children.set(n.parent_id,[]);children.get(n.parent_id).push(n);}
  for(const list of children.values())list.sort((a,b)=>a.type.localeCompare(b.type)||a.path.localeCompare(b.path));
  for(const e of data?.edges||[]){if(!incoming.has(e.target))incoming.set(e.target,[]);if(!outgoing.has(e.source))outgoing.set(e.source,[]);incoming.get(e.target).push(e);outgoing.get(e.source).push(e);}
  const graphNodes=new Map((graph?.nodes||[]).map(n=>[n.id,n])),graphEdges=new Map((graph?.edges||[]).map(e=>[e.id,e])),refs=new Map((graph?.references||[]).map(r=>[r.id,r]));
  const rootNode=[...nodes.values()].find(n=>n.parent_id===null),paths=new Map([...nodes.values()].map(n=>[n.path,n]));
  return {data,nodes,components,children,incoming,outgoing,graphNodes,graphEdges,refs,root:rootNode,paths,treeCache:new Map(),fileCache:new Map()};
 }
 function componentView(ix,state){
  const allowed=e=>state.relationship==='all'||(state.relationship==='calls'?e.type==='CALLS':['IMPORTS','INCLUDES'].includes(e.type));
  let components=[...ix.components.values()];
  const neighbor=new Set([state.component]);
  if(state.focus&&state.component){for(const e of [...ix.incoming.get(state.component)||[],...ix.outgoing.get(state.component)||[]])if(allowed(e)){neighbor.add(e.source);neighbor.add(e.target);}components=components.filter(c=>neighbor.has(c.id));}
  if(state.query.trim()){const q=state.query.toLowerCase();components=components.filter(c=>`${c.name} ${c.path}`.toLowerCase().includes(q));}
  components.sort((a,b)=>(b.incoming_components.length+b.outgoing_components.length)-(a.incoming_components.length+a.outgoing_components.length)||b.metrics.bytes-a.metrics.bytes||a.path.localeCompare(b.path));
  const total=components.length,shown=components.slice(0,LIMITS.components),selected=components.find(c=>c.id===state.component);
  if(selected&&!shown.includes(selected))shown[shown.length-1]=selected;
  const ids=new Set(shown.map(c=>c.id)),edges=(ix.data?.edges||[]).filter(e=>ids.has(e.source)&&ids.has(e.target)&&allowed(e));
  return {components:shown,edges:edges.slice(0,LIMITS.edges),matching:total,matchingEdges:edges.length,truncated:shown.length<total||edges.length>LIMITS.edges};
 }
 function componentPositions(view){
  const nodes=view.components.map(c=>({id:c.id,name:c.name,type:'function',path:c.path}));
  const positions=root.ArchaeologistLayouts.layout({nodes,edges:view.edges},null,{view:'calls',layout:'auto'});
  const levels=new Map();for(const p of positions.values()){const level=Math.round(p.x/270);if(!levels.has(level))levels.set(level,[]);levels.get(level).push(p);}
  const ordered=[...levels.keys()].sort((a,b)=>a-b),bandHeights=[];
  ordered.forEach((level,i)=>{const band=Math.floor(i/4);bandHeights[band]=Math.max(bandHeights[band]||0,levels.get(level).length*166+80);});
  ordered.forEach((level,i)=>{const band=Math.floor(i/4),offset=bandHeights.slice(0,band).reduce((a,b)=>a+b,0);levels.get(level).sort((a,b)=>a.y-b.y).forEach((p,row)=>Object.assign(p,{x:(i%4)*286,y:offset+row*166}));});
  return positions;
 }
 function edgeRoutes(view,positions){
  const groups=new Map(),routes=new Map();for(const edge of view.edges){const key=[edge.source,edge.target].sort().join('|');if(!groups.has(key))groups.set(key,[]);groups.get(key).push(edge);}
  for(const list of groups.values()){list.sort((a,b)=>a.id.localeCompare(b.id));list.forEach((edge,i)=>{const a=positions.get(edge.source),b=positions.get(edge.target),offset=(i-(list.length-1)/2)*12;let path;
   if(b.x>a.x){path=`M${a.x+232},${a.y+64+offset} C${a.x+278},${a.y+64+offset} ${b.x-48},${b.y+64+offset} ${b.x},${b.y+64+offset}`;}
   else if(b.x===a.x){const rail=a.x+285+i*14;path=`M${a.x+232},${a.y+64+offset} C${rail},${a.y+64+offset} ${rail},${b.y+64+offset} ${b.x+232},${b.y+64+offset}`;}
   else{const rail=Math.min(a.y,b.y)-40-i*16;path=`M${a.x+116+offset},${a.y} C${a.x+116+offset},${rail} ${b.x+116+offset},${rail} ${b.x+116+offset},${b.y}`;}routes.set(edge.id,path);
  });}return routes;
 }
 function metric(node,key){
  const value=node.metrics[key],covered=['bytes','physical_lines'].includes(key)?node.metrics.files:node.metrics.measured_files[key]||0;
  const state=value==null?(key==='max_c_function_score'?(node.ml_status==='unsupported'?'unsupported':'unscored'):node.structural_status==='unsupported'?'unsupported':'unavailable'):covered<node.metrics.files?'partial':'measured';
  return {value,covered,total:node.metrics.files,state};
 }
 function tone(node,key,maximum){
  const m=metric(node,key);if(m.value==null)return {fill:'url(#architecture-unscored)',...m};
  const ratio=key==='max_c_function_score'?m.value:maximum?Math.sqrt(m.value/maximum):0;
  const low=[47,51,53],high=['max_c_function_score','hotspots'].includes(key)?[181,87,100]:[151,131,103],clamped=Math.max(0,Math.min(1,ratio));
  return {fill:`rgb(${low.map((c,i)=>Math.round(c+(high[i]-c)*clamped)).join(',')})`,...m};
 }
 function partition(items,rect,area){
  const result=[];const tasks=[{items,rect}];
  while(tasks.length){const {items:list,rect:r}=tasks.pop();if(!list.length)continue;if(list.length===1){result.push({node:list[0],...r});continue;}
   const weights=list.map(n=>Math.max(1,n.metrics[area]||0)),total=weights.reduce((a,b)=>a+b,0);let sum=0,split=1,best=Infinity;
   for(let i=0;i<list.length-1;i++){sum+=weights[i];const error=Math.abs(total/2-sum);if(error<best){best=error;split=i+1;}}
   const fraction=weights.slice(0,split).reduce((a,b)=>a+b,0)/total,vertical=r.w>=r.h;
   const first=vertical?{x:r.x,y:r.y,w:r.w*fraction,h:r.h}:{x:r.x,y:r.y,w:r.w,h:r.h*fraction};
   const second=vertical?{x:r.x+first.w,y:r.y,w:r.w-first.w,h:r.h}:{x:r.x,y:r.y+first.h,w:r.w,h:r.h-first.h};
   tasks.push({items:list.slice(split),rect:second},{items:list.slice(0,split),rect:first});
  }return result;
 }
 function treemap(ix,directory,area){
  const key=directory+'|'+area;if(ix.treeCache.has(key))return ix.treeCache.get(key);
  const regions=[],stack=[{id:directory,rect:{x:12,y:12,w:976,h:576},depth:0}],rootChildren=ix.children.get(directory)||[];let truncated=false;
  while(stack.length){const {id,rect,depth}=stack.pop(),children=[...ix.children.get(id)||[]].sort((a,b)=>(b.metrics[area]||0)-(a.metrics[area]||0)||a.path.localeCompare(b.path));
   const remaining=LIMITS.regions-regions.length,retained=children.slice(0,remaining);if(retained.length<children.length)truncated=true;
   for(const item of partition(retained,rect,area)){
    const region={...item,x:item.x+3,y:item.y+3,w:Math.max(0,item.w-6),h:Math.max(0,item.h-6),depth};regions.push(region);
    if(item.node.type==='directory'&&depth<LIMITS.depth-1&&region.w>100&&region.h>85)stack.push({id:item.node.id,rect:{x:region.x+5,y:region.y+30,w:region.w-10,h:region.h-35},depth:depth+1});
   }
  }
  const value={regions,truncated,entries:rootChildren.length};ix.treeCache.set(key,value);return value;
 }
 function filesUnder(ix,id){if(ix.fileCache.has(id))return ix.fileCache.get(id);const found=[],seen=new Set(),stack=[id];while(stack.length){const current=stack.pop();if(seen.has(current))continue;seen.add(current);const n=ix.nodes.get(current);if(n?.type==='file')found.push(n);else for(const child of ix.children.get(current)||[])stack.push(child.id);}found.sort((a,b)=>a.path.localeCompare(b.path));ix.fileCache.set(id,found);return found;}
 function search(ix,query){const q=query.trim().toLowerCase();return [...ix.nodes.values()].filter(n=>n.path.toLowerCase().includes(q)||n.name.toLowerCase().includes(q)).slice(0,LIMITS.search);}
 function breadcrumbs(ix,id){const result=[],seen=new Set();while(id&&!seen.has(id)){seen.add(id);const n=ix.nodes.get(id);if(!n)break;result.push(n);id=n.parent_id;}return result.reverse();}
 const api={LIMITS,METRICS,initial,index,componentView,componentPositions,edgeRoutes,metric,tone,partition,treemap,filesUnder,search,breadcrumbs};root.ArchaeologistArchitecture=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
