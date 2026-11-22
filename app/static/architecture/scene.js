/* Event-driven SVG viewport with keyboard pan/zoom; no animation loop. */
(function(root){
 'use strict';
 const NS='http://www.w3.org/2000/svg';
 function svg(tag,attrs={},value){const el=document.createElementNS(NS,tag);for(const [key,v]of Object.entries(attrs))el.setAttribute(key,String(v));if(value!==undefined)el.textContent=String(value);return el;}
 class Scene{
  constructor(host,onPick,onEdge,namespace='architecture'){
   this.host=host;this.onPick=onPick;this.box={x:-30,y:-30,w:1100,h:650};this.frame=null;this.clean=[];
   this.svg=svg('svg',{class:'architecture-svg',role:'group',tabindex:0,'aria-label':'Architecture canvas. Use Tab and Enter to inspect, arrow keys to pan, plus/minus to zoom.'});
   const defs=svg('defs'),marker=svg('marker',{id:namespace+'-arrow',viewBox:'0 0 10 10',refX:10,refY:5,markerWidth:6,markerHeight:6,orient:'auto'});marker.append(svg('path',{d:'M0,0 L10,5 L0,10 Z',fill:'#b58f9c'}));
   const pattern=svg('pattern',{id:namespace+'-unscored',width:9,height:9,patternUnits:'userSpaceOnUse'});pattern.append(svg('rect',{width:9,height:9,fill:'#26212b'}),svg('path',{d:'M-2,2 L2,-2 M0,9 L9,0 M7,11 L11,7',stroke:'#51404c','stroke-width':1}));defs.append(marker,pattern);
   this.content=svg('g');this.svg.append(defs,this.content);host.replaceChildren(this.svg);
   const listen=(name,fn,options)=>{this.svg.addEventListener(name,fn,options);this.clean.push(()=>this.svg.removeEventListener(name,fn,options));};
   listen('wheel',e=>{e.preventDefault();const r=this.svg.getBoundingClientRect();this.zoom(e.deltaY<0?1.12:1/1.12,(e.clientX-r.left)/r.width,(e.clientY-r.top)/r.height);},{passive:false});
   listen('pointerdown',e=>{if(e.button===0){this.drag={x:e.clientX,y:e.clientY,distance:0,target:e.target.closest('[data-entity]')?.dataset.entity,edge:e.target.closest('[data-edge]')?.dataset.edge};this.svg.setPointerCapture(e.pointerId);}});
   listen('pointermove',e=>{if(!this.drag)return;const r=this.svg.getBoundingClientRect(),dx=e.clientX-this.drag.x,dy=e.clientY-this.drag.y;this.drag.distance+=Math.abs(dx)+Math.abs(dy);if(this.drag.distance>5){this.box.x-=dx*this.box.w/r.width;this.box.y-=dy*this.box.h/r.height;this.schedule();}this.drag.x=e.clientX;this.drag.y=e.clientY;});
   listen('pointerup',()=>{const drag=this.drag;this.drag=null;if(drag&&drag.distance<5){if(drag.edge)onEdge?.(drag.edge);else if(drag.target)onPick(drag.target);}});listen('pointercancel',()=>this.drag=null);
   listen('keydown',e=>{const target=e.target.closest('[data-entity]'),edge=e.target.closest('[data-edge]');if(['Enter',' '].includes(e.key)&&(target||edge)){e.preventDefault();edge?onEdge?.(edge.dataset.edge):onPick(target.dataset.entity);return;}const moves={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};if(moves[e.key]){e.preventDefault();this.box.x+=moves[e.key][0]*this.box.w*.08;this.box.y+=moves[e.key][1]*this.box.h*.08;this.schedule();}if(['+','=','-'].includes(e.key)){e.preventDefault();this.zoom(e.key==='-'?1/1.2:1.2);}});
   this.observer=new ResizeObserver(()=>this.schedule());this.observer.observe(host);
  }
  schedule(){if(this.frame!==null)return;this.frame=requestAnimationFrame(()=>{this.frame=null;this.svg.setAttribute('viewBox',`${this.box.x} ${this.box.y} ${this.box.w} ${this.box.h}`);this.svg.classList.toggle('is-distant',this.host.clientWidth/this.box.w<.5);});}
  zoom(factor,x=.5,y=.5){const w=Math.max(250,Math.min(16000,this.box.w/factor)),h=w*this.box.h/this.box.w;this.box={x:this.box.x+(this.box.w-w)*x,y:this.box.y+(this.box.h-h)*y,w,h};this.schedule();}
  fit(bounds){this.bounds=bounds;const aspect=(this.host.clientWidth||900)/(this.host.clientHeight||560),w=Math.max(bounds.w,bounds.h*aspect);this.box={x:bounds.x-(w-bounds.w)/2,y:bounds.y-(w/aspect-bounds.h)/2,w,h:w/aspect};this.schedule();}
  reset(){if(this.bounds)this.fit(this.bounds);}
  destroy(){cancelAnimationFrame(this.frame);this.clean.forEach(fn=>fn());this.observer.disconnect();this.host.replaceChildren();}
 }
 root.ArchitectureScene={Scene,svg};
})(globalThis);
