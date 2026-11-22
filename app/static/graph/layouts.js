/* Bounded deterministic layouts and shared presentation; no source analysis. */
(function(root){
 'use strict';
 const D=root.ArchaeologistGraph;
 function strategy(state){if(state.layout==='hierarchy')return state.view==='knowledge'?'hierarchy':'directed';return state.layout&&state.layout!=='auto'?state.layout:state.view==='knowledge'?'hierarchy':state.view==='calls'?'directed':'clusters';}
 function signature(view,state){return JSON.stringify([state.view,strategy(state),view.nodes.map(n=>n.id),view.edges.map(e=>e.id)]);}
 function hierarchy(ix){
   const parent=new Map(),children=new Map();
   for(const e of ix.edges)if(['CONTAINS','DEFINES'].includes(e.type)){
     if(!children.has(e.source))children.set(e.source,[]);
     children.get(e.source).push(e.target);parent.set(e.target,e.source);
   }
   for(const ids of children.values())ids.sort();
   return {parent,children};
 }
 function descendants(ix,seed,cap=D.LIMITS.nodes){
   const h=ix.hierarchy||hierarchy(ix),ids=new Set(),queue=[seed];let cursor=0,truncated=false;
   while(cursor<queue.length){const id=queue[cursor++];if(ids.has(id))continue;if(ids.size>=cap){truncated=true;break;}ids.add(id);for(const child of h.children.get(id)||[])if(!ids.has(child))queue.push(child);}
   return {ids,truncated};
 }
 function tree(view,ix){
   const ids=new Set(view.nodes.map(n=>n.id)),h=ix.hierarchy||hierarchy(ix),children=new Map(),parent=new Map();
   // Connect to the nearest *evidenced* visible ancestor if filters hid containers.
   for(const n of view.nodes){let p=h.parent.get(n.id),visited=new Set();while(p&&!ids.has(p)&&!visited.has(p)){visited.add(p);p=h.parent.get(p);}if(p&&p!==n.id){parent.set(n.id,p);if(!children.has(p))children.set(p,[]);children.get(p).push(n.id);}}
   const positions=new Map(),sizes=new Map(),roots=view.nodes.filter(n=>!parent.has(n.id)).map(n=>n.id);
   const stack=roots.map(id=>[id,false]),seen=new Set();
   while(stack.length){
     const [id,done]=stack.pop(),kids=children.get(id)||[];
     if(done){
       const cols=Math.min(4,Math.max(1,Math.ceil(Math.sqrt(kids.length)))),widths=Array(cols).fill(170),heights=Array(Math.ceil(kids.length/cols)).fill(85);
       kids.forEach((child,i)=>{const size=sizes.get(child)||{w:170,h:85};widths[i%cols]=Math.max(widths[i%cols],size.w);heights[Math.floor(i/cols)]=Math.max(heights[Math.floor(i/cols)],size.h);});
       sizes.set(id,{w:Math.max(170,widths.reduce((a,b)=>a+b,0)+(cols-1)*55),h:kids.length?125+heights.reduce((a,b)=>a+b,0)+(heights.length-1)*65:85,cols,widths,heights});continue;
     }
     if(seen.has(id))continue;seen.add(id);stack.push([id,true]);for(const child of kids)stack.push([child,false]);
   }
   const tasks=[];let offset=0;for(const id of roots){tasks.push([id,offset,0]);offset+=(sizes.get(id)?.w||170)+140;}
   seen.clear();while(tasks.length){const [id,x,y]=tasks.pop();if(seen.has(id))continue;seen.add(id);const size=sizes.get(id)||{w:170};positions.set(id,{x:x+size.w/2,y,z:0});
     const kids=children.get(id)||[];kids.forEach((child,i)=>{const col=i%size.cols,row=Math.floor(i/size.cols),left=size.widths.slice(0,col).reduce((a,b)=>a+b,0)+col*55,top=size.heights.slice(0,row).reduce((a,b)=>a+b,0)+row*65;tasks.push([child,x+left,y+125+top]);});
   }
   return positions;
 }
 function directed(view){
   // Iterative Kosaraju SCC condensation makes recursive/cyclic static calls safe.
   const adj=new Map(view.nodes.map(n=>[n.id,[]])),rev=new Map(view.nodes.map(n=>[n.id,[]]));
   for(const e of view.edges){adj.get(e.source)?.push(e.target);rev.get(e.target)?.push(e.source);}
   const seen=new Set(),order=[];
   for(const n of view.nodes){if(seen.has(n.id))continue;const stack=[[n.id,false]];while(stack.length){const [id,done]=stack.pop();if(done){order.push(id);continue;}if(seen.has(id))continue;seen.add(id);stack.push([id,true]);for(const child of adj.get(id)||[])if(!seen.has(child))stack.push([child,false]);}}
   const component=new Map(),groups=[];
   for(const id of order.reverse()){if(component.has(id))continue;const group=[],stack=[id],index=groups.length;component.set(id,index);while(stack.length){const current=stack.pop();group.push(current);for(const child of rev.get(current)||[])if(!component.has(child)){component.set(child,index);stack.push(child);}}groups.push(group.sort());}
   const links=groups.map(()=>new Set()),indegree=groups.map(()=>0),level=groups.map(()=>0);
   for(const e of view.edges){const a=component.get(e.source),b=component.get(e.target);if(a!==b&&!links[a].has(b)){links[a].add(b);indegree[b]++;}}
   const queue=indegree.map((d,i)=>d===0?i:null).filter(i=>i!==null);
   for(let cursor=0;cursor<queue.length;cursor++){const a=queue[cursor];for(const b of links[a]){level[b]=Math.max(level[b],level[a]+1);if(--indegree[b]===0)queue.push(b);}}
   const positions=new Map(),rows=new Map();
   groups.forEach((group,i)=>{let row=rows.get(level[i])||0;for(const id of group){positions.set(id,{x:level[i]*270,y:row*100,z:0});row++;}rows.set(level[i],row+1);});
   return positions;
 }
 function clusters(view){
   const groups=new Map();for(const n of view.nodes){const directory=(n.path||'').split('/').slice(0,-1).join('/')||'(root)';if(!groups.has(directory))groups.set(directory,[]);groups.get(directory).push(n);}
   const positions=new Map();let x=0;
   for(const [,nodes]of [...groups].sort(([a],[b])=>a.localeCompare(b))){const cols=Math.max(1,Math.ceil(Math.sqrt(nodes.length)));nodes.forEach((n,i)=>positions.set(n.id,{x:x+(i%cols)*195,y:Math.floor(i/cols)*110,z:0}));x+=cols*195+160;}
   return positions;
 }
 function radial(view){const positions=new Map();let cursor=0,ring=0;while(cursor<view.nodes.length){const capacity=ring===0?1:Math.max(6,Math.floor(2*Math.PI*ring*150/190)),count=Math.min(capacity,view.nodes.length-cursor);for(let i=0;i<count;i++){const angle=2*Math.PI*i/count-Math.PI/2;positions.set(view.nodes[cursor++].id,{x:Math.cos(angle)*ring*165,y:Math.sin(angle)*ring*165,z:0});}ring++;}return positions;}
 function separate(positions,nodes){
   // Bounded grid occupancy avoids coincident nodes, including incremental additions.
   const buckets=new Map();
   for(const n of nodes){const p=positions.get(n.id);if(!p)continue;
     let x,y,collision;
     do{x=Math.floor(p.x/175);y=Math.floor(p.y/85);collision=false;
       for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(const other of buckets.get(`${x+dx},${y+dy}`)||[])
         if(Math.abs(p.x-other.x)<165&&Math.abs(p.y-other.y)<78)collision=true;
       if(collision)p.y+=95;
     }while(collision);
     const key=`${x},${y}`;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(p);
   }
   return positions;
 }
 function layout(view,ix,state){
   const mode=strategy(state),positions=mode==='hierarchy'?tree(view,ix):mode==='directed'?directed(view):mode==='radial'?radial(view):clusters(view);
   for(const [i,n]of view.nodes.entries())if(!positions.has(n.id))positions.set(n.id,{x:i*195,y:0,z:0});
   return separate(positions,view.nodes);
 }
 function emphasis(view,state){
   const outgoing=new Set(),incoming=new Set();
   if(!state.selected)return new Map(view.nodes.map(n=>[n.id,'normal']));
   const walk=(direction,result)=>{let frontier=[state.selected];const visited=new Set(frontier);for(let depth=0;depth<(state.focus?state.hops:1);depth++){const next=[];for(const id of frontier)for(const e of view.edges){const target=direction==='out'?(e.source===id?e.target:null):(e.target===id?e.source:null);if(target&&!visited.has(target)){visited.add(target);result.add(target);next.push(target);}}frontier=next;}};
   if(state.direction!=='in')walk('out',outgoing);if(state.direction!=='out')walk('in',incoming);
   return new Map(view.nodes.map(n=>[n.id,n.id===state.selected?'selected':outgoing.has(n.id)?'outgoing':incoming.has(n.id)?'incoming':'dim']));
 }
 const EDGE_COLORS={CONTAINS:'#665467',DEFINES:'#a684a3',CALLS:'#d49ba6',IMPORTS:'#88b9a9',INCLUDES:'#d7b17d'};
 function edgeStyle(edge,state,em){
   const out=state.direction!=='in'&&(edge.source===state.selected||(state.focus&&em.get(edge.source)==='outgoing'&&em.get(edge.target)==='outgoing'));
   const incoming=state.direction!=='out'&&(edge.target===state.selected||(state.focus&&em.get(edge.source)==='incoming'&&em.get(edge.target)==='incoming'));
   return {color:out?'#E54859':incoming?'#d7b17d':EDGE_COLORS[edge.type],opacity:state.selected?(out||incoming ? .95 : .12):(['CONTAINS','DEFINES'].includes(edge.type) ? .35 : .65),width:out||incoming?1.8:1,dash:['CONTAINS','DEFINES'].includes(edge.type)?'4 5':edge.type==='INCLUDES'?'8 3':''};
 }
 function labels(nodes,positions,selected,hover,em,scale=1,max=32){
   const result=new Set(),boxes=[];
   const ordered=[...nodes].sort((a,b)=>(a.id===selected?-1:b.id===selected?1:a.id===hover?-1:b.id===hover?1:(em.get(a.id)==='dim')-(em.get(b.id)==='dim')));
   for(const n of ordered){const p=positions.get(n.id);if(!p||p.hidden)continue;const forced=n.id===selected||n.id===hover;
     if(!forced&&(result.size>=max||scale<.25||(em.get(n.id)==='dim'&&scale<1.5)))continue;
     const width=Math.min(150,n.name.length*6+12),box={x:p.x-width/2,y:p.y+16,w:width,h:18};
     if(!forced&&boxes.some(b=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y))continue;
     result.add(n.id);boxes.push(box);
   }return result;
 }
 const api={strategy,signature,hierarchy,descendants,layout,separate,emphasis,edgeStyle,labels,EDGE_COLORS};
 root.ArchaeologistLayouts=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
