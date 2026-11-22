/* Retained SVG scene: keyed elements, shared layouts and scheduled geometry updates. */
(function(root){
 'use strict';
 const NS='http://www.w3.org/2000/svg';
 function svg(tag,attrs={},text){const el=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,String(v));if(text!==undefined)el.textContent=text;return el;}
 class SVGGraph{
  constructor(host,onSelect){
   this.host=host;this.onSelect=onSelect;this.positions=new Map();this.nodes=new Map();this.edges=new Map();this.clean=[];this.frame=null;this.destroyed=false;this.hover=null;this.layoutRuns=0;
   this.svg=svg('svg',{class:'graph-svg',role:'group','aria-label':'Repository graph. Tab to nodes, Enter to inspect, arrows to pan, plus/minus to zoom.',tabindex:0});
   const defs=svg('defs'),marker=svg('marker',{id:'graph-arrow',viewBox:'0 0 10 10',refX:10,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});
   marker.append(svg('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#c3a0aa'}));defs.append(marker);
   this.lines=svg('g');this.entities=svg('g');this.svg.append(defs,this.lines,this.entities);host.replaceChildren(this.svg);
   this.box={x:0,y:0,w:1000,h:650};
   const listen=(name,fn,options)=>{this.svg.addEventListener(name,fn,options);this.clean.push(()=>this.svg.removeEventListener(name,fn,options));};
   listen('wheel',e=>{e.preventDefault();this.zoom(e.deltaY<0?1.12:1/1.12,{x:e.clientX,y:e.clientY});},{passive:false});
   listen('pointerdown',e=>{if(e.button!==0)return;const target=e.target.closest('[data-node]');this.drag={id:target?.dataset.node,x:e.clientX,y:e.clientY,distance:0};this.svg.setPointerCapture(e.pointerId);});
   listen('pointermove',e=>{
    const over=e.target.closest('[data-node]')?.dataset.node||null;if(over!==this.hover){this.hover=over;this.schedule();}
    if(!this.drag)return;const dx=e.clientX-this.drag.x,dy=e.clientY-this.drag.y,rect=this.svg.getBoundingClientRect();this.drag.distance+=Math.abs(dx)+Math.abs(dy);
    if(this.drag.id){const p=this.positions.get(this.drag.id);p.x+=dx*this.box.w/rect.width;p.y+=dy*this.box.h/rect.height;this.geometryDirty=true;}else{this.box.x-=dx*this.box.w/rect.width;this.box.y-=dy*this.box.h/rect.height;}
    this.drag.x=e.clientX;this.drag.y=e.clientY;this.schedule();
   });
   listen('pointerup',()=>{const drag=this.drag;this.drag=null;if(drag?.id&&drag.distance<5)this.onSelect(drag.id);});
   listen('pointercancel',()=>{this.drag=null;});listen('pointerleave',()=>{this.hover=null;this.schedule();});
   listen('keydown',e=>{const target=e.target.closest('[data-node]');if(target&&['Enter',' '].includes(e.key)){e.preventDefault();this.onSelect(target.dataset.node);return;}if(['+','=','-'].includes(e.key)){e.preventDefault();this.zoom(e.key==='-'?1/1.2:1.2);}const moves={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};if(moves[e.key]){e.preventDefault();this.box.x+=moves[e.key][0]*this.box.w*.08;this.box.y+=moves[e.key][1]*this.box.h*.08;this.schedule();}});
  }
  set(view,ix,state){
   const L=root.ArchaeologistLayouts,signature=L.signature(view,state),strategy=`${state.view}:${L.strategy(state)}`;
   const changed=signature!==this.signature,reset=strategy!==this.strategy;
   this.view=view;this.ix=ix;this.state={...state};this.em=L.emphasis(view,state);
   if(changed){
    if(reset||!this.positions.size){this.positions=L.layout(view,ix,state);this.layoutRuns++;}
    else if(view.nodes.some(n=>!this.positions.has(n.id))){const initial=L.layout(view,ix,state);this.layoutRuns++;for(const n of view.nodes)if(!this.positions.has(n.id))this.positions.set(n.id,initial.get(n.id));L.separate(this.positions,view.nodes);}
    this.signature=signature;this.strategy=strategy;this.reconcile();this.geometryDirty=true;
    if(reset)this.fit();
   }
   this.styleDirty=true;this.schedule();
  }
  reconcile(){
   const ids=new Set(this.view.nodes.map(n=>n.id)),edgeIds=new Set(this.view.edges.map(e=>e.id));
   for(const [id,item]of this.nodes)if(!ids.has(id)){item.group.remove();this.nodes.delete(id);}
   for(const [id,item]of this.edges)if(!edgeIds.has(id)){item.path.remove();this.edges.delete(id);}
   for(const e of this.view.edges)if(!this.edges.has(e.id)){const path=svg('path',{'marker-end':'url(#graph-arrow)',class:'graph-link'}),title=svg('title',{},`${e.type}: ${e.reference||''} · ${e.occurrences} occurrence(s)`);path.append(title);this.lines.append(path);this.edges.set(e.id,{path});}
   for(const n of this.view.nodes)if(!this.nodes.has(n.id)){
    const v=root.ArchaeologistGraph.overlay(n),group=svg('g',{'data-node':n.id,tabindex:0,role:'button'}),shape=svg(v.shape==='circle'?'circle':v.shape==='diamond'?'polygon':'rect'),title=svg('title'),label=svg('text',{y:28,'text-anchor':'middle',class:'graph-node-label'},n.name.length>23?n.name.slice(0,22)+'…':n.name);
    group.append(shape,title,label);this.entities.append(group);this.nodes.set(n.id,{group,shape,title,label});
   }
  }
  schedule(){if(this.destroyed||this.frame!==null)return;this.frame=requestAnimationFrame(()=>{this.frame=null;this.draw();});}
  draw(){
   if(!this.view||this.destroyed)return;const D=root.ArchaeologistGraph,L=root.ArchaeologistLayouts;
   if(this.geometryDirty){
    const pairs=new Map();for(const e of this.view.edges){const key=[e.source,e.target].sort().join('|');if(!pairs.has(key))pairs.set(key,[]);pairs.get(key).push(e.id);}
    for(const e of this.view.edges){const a=this.positions.get(e.source),b=this.positions.get(e.target),parallel=pairs.get([e.source,e.target].sort().join('|')),slot=parallel.indexOf(e.id),bend=parallel.length>1?28+slot*18:16;
     const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1,tx=b.x-dx/len*19,ty=b.y-dy/len*19;
     const path=e.source===e.target?`M ${a.x-8} ${a.y-8} C ${a.x-60} ${a.y-76},${a.x+60} ${a.y-76},${a.x+8} ${a.y-8}`:`M ${a.x} ${a.y} Q ${(a.x+b.x)/2-dy/len*bend} ${(a.y+b.y)/2+dx/len*bend} ${tx} ${ty}`;
     this.edges.get(e.id).path.setAttribute('d',path);
    }
    for(const n of this.view.nodes){const p=this.positions.get(n.id);this.nodes.get(n.id).group.setAttribute('transform',`translate(${p.x} ${p.y})`);}this.geometryDirty=false;
   }
   if(this.styleDirty){
    for(const e of this.view.edges){const v=L.edgeStyle(e,this.state,this.em),path=this.edges.get(e.id).path;path.setAttribute('stroke',v.color);path.setAttribute('opacity',v.opacity);path.setAttribute('stroke-width',v.width);path.setAttribute('stroke-dasharray',v.dash);}
    for(const n of this.view.nodes){const item=this.nodes.get(n.id),v=D.overlay(n,this.state.overlay),em=this.em.get(n.id);
     item.group.setAttribute('class',`graph-node ${em}`);item.group.setAttribute('aria-pressed',String(em==='selected'));item.group.setAttribute('aria-label',`${n.type}: ${n.name}. ${v.label}`);item.title.textContent=`${n.name}\n${n.path||''}\n${v.label}`;
     const attrs={fill:v.color,stroke:em==='selected'?'#F8E8EA':em==='incoming'?'#d7b17d':v.hotspot||em==='outgoing'?'#E54859':'#30151D','stroke-width':em==='selected'||v.hotspot||['incoming','outgoing'].includes(em)?2.5:1};
     if(v.shape==='circle')attrs.r=v.size;else if(v.shape==='diamond')attrs.points=`0,-${v.size} ${v.size},0 0,${v.size} -${v.size},0`;else Object.assign(attrs,{x:-v.size,y:-v.size*.7,width:v.size*2,height:v.size*1.4,rx:v.shape==='square'?2:4});
     for(const [k,val]of Object.entries(attrs))item.shape.setAttribute(k,val);
    }this.styleDirty=false;
   }
   this.transform();
  }
  transform(){
   if(!this.svg)return;this.svg.setAttribute('viewBox',`${this.box.x} ${this.box.y} ${this.box.w} ${this.box.h}`);
   const rect=this.svg.getBoundingClientRect(),scale=(rect.width||900)/this.box.w,projected=new Map();
   for(const n of this.view?.nodes||[]){const p=this.positions.get(n.id);projected.set(n.id,{x:(p.x-this.box.x)*scale,y:(p.y-this.box.y)*scale,hidden:p.x<this.box.x||p.x>this.box.x+this.box.w||p.y<this.box.y||p.y>this.box.y+this.box.h});}
   const labels=root.ArchaeologistLayouts.labels(this.view?.nodes||[],projected,this.state?.selected,this.hover,this.em||new Map(),scale,scale>1?70:32);
   for(const [id,item]of this.nodes)item.label.setAttribute('visibility',labels.has(id)?'visible':'hidden');
  }
  fit(){const values=(this.view?.nodes||[]).map(n=>this.positions.get(n.id)).filter(Boolean);const rect=this.svg.getBoundingClientRect(),aspect=(rect.width||900)/(rect.height||550);
   if(!values.length){this.box={x:0,y:0,w:1000,h:650};this.schedule();return;}const xs=values.map(p=>p.x),ys=values.map(p=>p.y),x=Math.min(...xs)-95,y=Math.min(...ys)-85,w=Math.max(260,Math.max(...xs)-x+95),h=Math.max(200,Math.max(...ys)-y+85),width=Math.max(w,h*aspect);this.box={x:x-(width-w)/2,y:y-(width/aspect-h)/2,w:width,h:width/aspect};this.schedule();}
  zoom(factor,anchor){const rect=this.svg.getBoundingClientRect(),ax=anchor?(anchor.x-rect.left)/rect.width:.5,ay=anchor?(anchor.y-rect.top)/rect.height:.5,w=Math.max(80,Math.min(40000,this.box.w/factor)),h=w*this.box.h/this.box.w;this.box={x:this.box.x+(this.box.w-w)*ax,y:this.box.y+(this.box.h-h)*ay,w,h};this.schedule();}
  focus(id){const p=this.positions.get(id);if(!p)return;const rect=this.svg.getBoundingClientRect(),aspect=(rect.width||900)/(rect.height||550);this.box={x:p.x-250,y:p.y-250/aspect,w:500,h:500/aspect};this.schedule();}
  reset(){this.positions=root.ArchaeologistLayouts.layout(this.view,this.ix,this.state);this.layoutRuns++;this.geometryDirty=true;this.fit();}
  resize(){const rect=this.svg.getBoundingClientRect(),aspect=(rect.width||900)/(rect.height||550),height=this.box.w/aspect;this.box.y+=(this.box.h-height)/2;this.box.h=height;this.schedule();}
  destroy(){if(this.destroyed)return;this.destroyed=true;cancelAnimationFrame(this.frame);this.clean.forEach(fn=>fn());this.positions.clear();this.nodes.clear();this.edges.clear();this.host.replaceChildren();}
 }
 root.ArchaeologistSVG=SVGGraph;
})(globalThis);
