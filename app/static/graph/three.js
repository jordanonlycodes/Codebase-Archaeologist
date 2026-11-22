/* Real WebGL adapter for locally installed 3d-force-graph 1.73.3 (bundled Three.js). */
(function(root){
  'use strict';
  const ASSET='/static/vendor/3d-force-graph-1.73.3.min.js';
  let pending=null;
  function webgl() {
    try {
      const canvas=document.createElement('canvas');
      const context=canvas.getContext('webgl2')||canvas.getContext('webgl');
      if(!context)return false;
      context.getExtension('WEBGL_lose_context')?.loseContext();return true;
    }catch{return false;}
  }
  function load() {
    if(root.ForceGraph3D)return Promise.resolve();
    if(pending)return pending;
    pending=new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src=ASSET;
      script.onload=()=>root.ForceGraph3D?resolve():reject(new Error('The local 3D asset did not expose ForceGraph3D.'));
      script.onerror=()=>{script.remove();reject(new Error('3D assets are unavailable. Run: python tools/install_graph_assets.py, then reload. 2D remains available.'));};
      document.head.append(script);
    }).catch(error=>{pending=null;throw error;});return pending;
  }
  class ThreeGraph {
    constructor(host,onSelect,reducedMotion=false) {
      this.host=host;this.reduced=reducedMotion;this.frame=null;this.destroyed=false;this.ix=null;
      try {
      this.graph=root.ForceGraph3D({controlType:'orbit',rendererConfig:{antialias:true}})(host);
      this.graph.backgroundColor('#0A0A0D').showNavInfo(false).nodeId('id').nodeResolution(10)
        .nodeLabel(n=>{const label=document.createElement('span');label.textContent=`${n.record.name} · ${n.record.path || n.record.type}`;return label;})
        .linkLabel(e=>{const label=document.createElement('span');label.textContent=`${e.type} · ${e.reference || ''} · ${e.occurrences} occurrence(s)`;return label;})
        .linkDirectionalArrowLength(4).linkDirectionalArrowRelPos(1).linkOpacity(.6)
        .linkCurvature(e=>e.source===e.target || e.source?.id===e.target?.id ? .5 : .08)
        .enableNodeDrag(true).onNodeClick(n=>onSelect(n.id)).onBackgroundClick(()=>onSelect(null))
        .onNodeDragEnd(n=>{n.fx=n.x;n.fy=n.y;n.fz=n.z;})
        .warmupTicks(0).cooldownTicks(reducedMotion?0:80).cooldownTime(reducedMotion?0:2200);
      this.graph.controls().enableDamping=!reducedMotion;
      this.labelLayer=document.createElement('div');this.labelLayer.className='graph-spatial-labels';host.append(this.labelLayer);
      this.labels=new Map();this.resize();
      this.visible=true;
      this.observer=new IntersectionObserver(entries=>{if(this.destroyed)return;this.visible=entries[0].isIntersecting;this.visible?this.graph.resumeAnimation():this.graph.pauseAnimation();});
      this.observer.observe(host);
      const tick=()=>{if(this.destroyed)return;if(this.visible&&!document.hidden)this.placeLabels();this.frame=requestAnimationFrame(tick);};
      this.frame=requestAnimationFrame(tick);
      } catch(error) {this.destroy();throw error;}
    }
    set(view,ix,state) {
      this.ix=ix;this.state=state;
      const D=root.ArchaeologistGraph,data=D.forceData(view);
      // Fixed deterministic initial positions avoid synchronous force-layout warmup.
      data.nodes.forEach((n,i)=>{
        const cached=this.positions?.get(n.id),angle=i*2.399963229728653;
        Object.assign(n,cached || {x:Math.cos(angle)*Math.sqrt(i+1)*16,y:(i%13-6)*14,z:Math.sin(angle)*Math.sqrt(i+1)*16});
      });
      const em=n=>D.emphasis(ix,n.id,state.selected,state.direction,state.relations);
      this.graph.nodeVal(n=>{const v=D.overlay(n.record,state.overlay);return (v.size/4)**3*(v.hotspot?1.4:1)*(em(n)==='selected'?2:1);})
        .nodeColor(n=>em(n)==='dim'?'#30232d':D.overlay(n.record,state.overlay).color)
        .linkColor(e=>{const a=typeof e.source==='object'?e.source.id:e.source,b=typeof e.target==='object'?e.target.id:e.target;return state.selected?(a===state.selected&&state.direction!=='in'?'#E54859':b===state.selected&&state.direction!=='out'?'#d7b17d':'#30232d'):'#875465';})
        .linkWidth(e=>state.selected&&(e.source?.id===state.selected||e.target?.id===state.selected||e.source===state.selected||e.target===state.selected)?1.8:.5)
        .graphData(data);
      this.data=data;this.positions=new Map();this.labelLayer.replaceChildren();this.labels.clear();
      // At most 30 real labels plus selected entity. Remaining names are available on hover/details.
      const labelled=data.nodes.filter(n=>n.id===state.selected).concat(data.nodes.filter(n=>n.id!==state.selected).slice(0,30));
      for(const n of labelled){const label=document.createElement('span');label.textContent=n.record.name;this.labels.set(n.id,label);this.labelLayer.append(label);}
    }
    placeLabels() {
      if(!this.data)return;
      const camera=this.graph.camera();
      for(const n of this.data.nodes) {
        this.positions.set(n.id,{x:n.x,y:n.y,z:n.z,fx:n.fx,fy:n.fy,fz:n.fz});
        const label=this.labels.get(n.id);if(!label)continue;
        const point=camera.position.clone().set(n.x||0,n.y||0,n.z||0);
        const distance=point.distanceTo(camera.position);point.project(camera);
        const visible=point.z>=-1&&point.z<=1&&Math.abs(point.x)<=1&&Math.abs(point.y)<=1&&(distance<900||n.id===this.state.selected);
        label.hidden=!visible;
        if(visible){label.style.left=`${(point.x+1)*this.host.clientWidth/2}px`;label.style.top=`${(-point.y+1)*this.host.clientHeight/2}px`;}
      }
    }
    focus(id) {
      const n=this.data?.nodes.find(n=>n.id===id);if(!n)return;
      const camera=this.graph.camera(),controls=this.graph.controls();
      const delta=camera.position.clone().sub(controls.target).normalize().multiplyScalar(110);
      this.graph.cameraPosition({x:n.x+delta.x,y:n.y+delta.y,z:n.z+delta.z},n,this.reduced?0:450);
    }
    fit(){this.graph.zoomToFit(this.reduced?0:350,40);}
    zoom(factor){const camera=this.graph.camera(),target=this.graph.controls().target;const next=camera.position.clone().sub(target).multiplyScalar(1/factor).add(target);this.graph.cameraPosition(next,target,0);}
    reset(){this.graph.cameraPosition({x:0,y:0,z:600},{x:0,y:0,z:0},0);this.fit();}
    resize(){this.graph.width(this.host.clientWidth||800).height(this.host.clientHeight||580);}
    destroy(){
      if(this.destroyed)return;this.destroyed=true;cancelAnimationFrame(this.frame);this.observer?.disconnect();
      const g=this.graph;if(!g){this.host.replaceChildren();return;}
      g.pauseAnimation();g.onNodeClick(null).onBackgroundClick(null).onNodeDragEnd(null);
      const geometries=new Set(),materials=new Set(),textures=new Set();
      g.scene().traverse(object=>{
        if(object.geometry)geometries.add(object.geometry);
        for(const material of Array.isArray(object.material)?object.material:[object.material]){
          if(!material)continue;materials.add(material);
          for(const value of Object.values(material))if(value?.isTexture)textures.add(value);
        }
      });
      g.controls()?.dispose();g.graphData({nodes:[],links:[]});
      // Pinned component teardown cancels its pointer/resize/render machinery.
      if(typeof g._destructor==='function')g._destructor();
      for(const texture of textures)texture.dispose();
      for(const material of materials)material.dispose?.();
      for(const geometry of geometries)geometry.dispose();
      g.renderer().renderLists?.dispose();g.renderer().dispose();g.renderer().forceContextLoss();
      this.labels?.clear();this.data=null;this.host.replaceChildren();this.graph=null;
    }
  }
  root.ArchaeologistThree={webgl,load,Adapter:ThreeGraph};
})(globalThis);
