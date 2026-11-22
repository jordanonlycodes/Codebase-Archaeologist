/* Small dependency-free analytical adapter: deterministic layout, no force simulation. */
(function(root){
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  function svg(tag,attrs={},text) {
    const el=document.createElementNS(NS,tag);
    for(const [key,value] of Object.entries(attrs)) el.setAttribute(key,String(value));
    if(text!==undefined) el.textContent=text;
    return el;
  }
  class SVGGraph {
    constructor(host,onSelect) {
      this.host=host; this.onSelect=onSelect; this.positions=new Map(); this.clean=[];
      this.svg=svg('svg',{class:'graph-svg',role:'group','aria-label':'2D repository graph. Tab to select nodes; use arrow keys to pan, plus or minus to zoom.',tabindex:0});
      const defs=svg('defs'), marker=svg('marker',{id:'graph-arrow',viewBox:'0 0 10 10',refX:10,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});
      marker.append(svg('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#c3a0aa'})); defs.append(marker);
      this.scene=svg('g'); this.svg.append(defs,this.scene); host.replaceChildren(this.svg);
      const listen=(target,name,fn,opts)=>{target.addEventListener(name,fn,opts);this.clean.push(()=>target.removeEventListener(name,fn,opts));};
      listen(this.svg,'wheel',e=>{e.preventDefault();this.zoom(e.deltaY<0?1.15:1/1.15);},{passive:false});
      listen(this.svg,'pointerdown',e=>{
        if(e.button!==0) return;
        const element=e.target.closest('[data-node]');
        this.drag={id:element?.dataset.node,x:e.clientX,y:e.clientY,moved:false};
        this.svg.setPointerCapture(e.pointerId);
      });
      listen(this.svg,'pointermove',e=>{
        if(!this.drag) return;
        const rect=this.svg.getBoundingClientRect();
        const dx=e.clientX-this.drag.x,dy=e.clientY-this.drag.y;
        if(Math.abs(dx)+Math.abs(dy)>2) this.drag.moved=true;
        if(this.drag.id) {
          const p=this.positions.get(this.drag.id); p.x+=dx*this.box.w/rect.width; p.y+=dy*this.box.h/rect.height; this.draw();
        } else {this.box.x-=dx*this.box.w/rect.width;this.box.y-=dy*this.box.h/rect.height;this.transform();}
        this.drag.x=e.clientX;this.drag.y=e.clientY;
      });
      listen(this.svg,'pointerup',()=>{const drag=this.drag;this.drag=null;if(drag?.id&&!drag.moved)this.onSelect(drag.id);});
      listen(this.svg,'pointercancel',()=>{this.drag=null;});
      listen(this.svg,'keydown',e=>{
        const target=e.target.closest('[data-node]');
        if(target && ['Enter',' '].includes(e.key)){e.preventDefault();this.onSelect(target.dataset.node);return;}
        if(e.key==='+'||e.key==='='){e.preventDefault();this.zoom(1.2);}
        if(e.key==='-'){e.preventDefault();this.zoom(1/1.2);}
        const deltas={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
        if(deltas[e.key]){e.preventDefault();this.box.x+=deltas[e.key][0]*this.box.w*.08;this.box.y+=deltas[e.key][1]*this.box.h*.08;this.transform();}
      });
      this.box={x:0,y:0,w:1000,h:650};
    }
    set(view,ix,state) {
      this.view=view;this.ix=ix;this.state=state;
      const missing=view.nodes.some(n=>!this.positions.has(n.id));
      if(missing || !this.positions.size) this.layout();
      this.draw();
    }
    layout() {
      this.positions.clear();
      const nodes=this.view?.nodes || [], columns=Math.max(1,Math.ceil(Math.sqrt(nodes.length*1.6)));
      nodes.forEach((n,i)=>this.positions.set(n.id,{x:90+(i%columns)*160,y:70+Math.floor(i/columns)*100}));
      this.fit();
    }
    fit() {
      const positions=(this.view?.nodes || []).map(n=>this.positions.get(n.id)).filter(Boolean);
      if(!positions.length){this.box={x:0,y:0,w:1000,h:650};this.transform();return;}
      const xs=positions.map(p=>p.x),ys=positions.map(p=>p.y);
      const x=Math.min(...xs)-90,y=Math.min(...ys)-65,w=Math.max(260,Math.max(...xs)-x+100),h=Math.max(180,Math.max(...ys)-y+80);
      const aspect=(this.host.clientWidth||800)/(this.host.clientHeight||580);
      this.box={x,y,w:Math.max(w,h*aspect),h:Math.max(h,w/aspect)};this.transform();
    }
    transform() {
      if(!this.svg) return;
      this.svg.setAttribute('viewBox',`${this.box.x} ${this.box.y} ${this.box.w} ${this.box.h}`);
      // Labels disappear when many nodes would make them illegible; title remains available.
      this.svg.classList.toggle('hide-labels',this.box.w/(this.host.clientWidth||800)>2.8);
    }
    zoom(factor) {
      const w=Math.max(80,Math.min(30000,this.box.w/factor)),h=w*this.box.h/this.box.w;
      this.box={x:this.box.x+(this.box.w-w)/2,y:this.box.y+(this.box.h-h)/2,w,h};this.transform();
    }
    focus(id) {
      const p=this.positions.get(id);if(!p)return;
      const aspect=(this.host.clientWidth||800)/(this.host.clientHeight||580);
      this.box={x:p.x-220,y:p.y-220/aspect,w:440,h:440/aspect};this.transform();
    }
    reset(){this.layout();this.draw();}
    resize(){this.transform();}
    draw() {
      if(!this.view)return;
      const active=document.activeElement?.closest?.('[data-node]')?.dataset.node;
      const D=root.ArchaeologistGraph,group=svg('g');
      for(const e of this.view.edges) {
        const a=this.positions.get(e.source),b=this.positions.get(e.target);
        const out=e.source===this.state.selected&&this.state.direction!=='in',inc=e.target===this.state.selected&&this.state.direction!=='out';
        const linked=this.state.selected && (out||inc);
        const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1;
        const tx=b.x-dx/len*17,ty=b.y-dy/len*17;
        const path=e.source===e.target ? `M ${a.x-7} ${a.y-6} C ${a.x-65} ${a.y-70},${a.x+65} ${a.y-70},${a.x+7} ${a.y-6}` : `M ${a.x} ${a.y} Q ${(a.x+b.x)/2-dy*.09} ${(a.y+b.y)/2+dx*.09} ${tx} ${ty}`;
        const edge=svg('path',{d:path,class:`graph-link ${this.state.selected&&!linked?'is-dim':''} ${linked?'is-linked':''} ${inc&&!out?'is-incoming':''}`,'marker-end':'url(#graph-arrow)'});
        edge.append(svg('title',{},`${e.type}: ${e.reference || ''} · ${e.occurrences} occurrence(s)`));group.append(edge);
      }
      for(const n of this.view.nodes) {
        const p=this.positions.get(n.id),v=D.overlay(n,this.state.overlay),em=D.emphasis(this.ix,n.id,this.state.selected,this.state.direction,this.state.relations);
        const g=svg('g',{transform:`translate(${p.x} ${p.y})`,class:`graph-node ${em} ${v.hotspot?'has-hotspot':''}`,'data-node':n.id,tabindex:0,role:'button','aria-label':`${n.type}: ${n.name}. ${v.label}`});
        const attrs={fill:v.color,stroke:em==='selected'?'#ffffff':v.hotspot?'#E54859':'#30151D','stroke-width':em==='selected'||v.hotspot?3:1};
        if(v.shape==='circle')g.append(svg('circle',{...attrs,r:v.size}));
        else if(v.shape==='diamond')g.append(svg('polygon',{...attrs,points:`0,-${v.size} ${v.size},0 0,${v.size} -${v.size},0`}));
        else g.append(svg('rect',{...attrs,x:-v.size,y:-v.size*.7,width:v.size*2,height:v.size*1.4,rx:v.shape==='square'?2:4}));
        const text=n.name.length>22?n.name.slice(0,21)+'…':n.name;
        g.append(svg('title',{},`${n.name}\n${n.path||''}\n${v.label}`),svg('text',{y:29,'text-anchor':'middle',class:'graph-node-label'},text));group.append(g);
      }
      this.scene.replaceChildren(group);this.transform();
      if(active)for(const element of group.querySelectorAll('[data-node]'))if(element.dataset.node===active)element.focus();
    }
    destroy(){this.clean.forEach(fn=>fn());this.clean=[];this.positions.clear();this.host.replaceChildren();this.svg=null;}
  }
  root.ArchaeologistSVG=SVGGraph;
})(globalThis);
