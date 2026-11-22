/* Real WebGL adapter for locally installed 3d-force-graph 1.73.3 (bundled Three.js). */
(function(root){
  'use strict';
  const ASSET='/static/vendor/3d-force-graph-1.73.3.min.js';
  let pending=null;
  function webgl() {
    try {
      const canvas=document.createElement('canvas');
      const context=canvas.getContext('webgl2',{antialias:false,depth:false,stencil:false,alpha:false})||canvas.getContext('webgl',{antialias:false,depth:false,stencil:false,alpha:false});
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
    constructor(host,onSelect,reducedMotion=false,onQualityChange=()=>{}){
      this.host=host;this.reduced=reducedMotion;this.onQualityChange=onQualityChange;this.quality=new root.ArchaeologistQuality.Policy();this.destroyed=false;this.visible=true;this.frame=null;this.sleep=null;this.positions=new Map();this.labels=new Map();this.clean=[];this.layoutRuns=0;this.dataUpdates=0;this.curves=new Map();
      try{
        this.graph=root.ForceGraph3D({controlType:'orbit',rendererConfig:{antialias:false,powerPreference:'low-power'}})(host);
        this.graph.backgroundColor('#0b0c0e').showNavInfo(false).nodeId('id')
          .nodeLabel(n=>{const el=document.createElement('span');el.textContent=`${n.record.name} · ${n.record.path||n.record.type}`;return el;})
          .linkLabel(e=>{const el=document.createElement('span');el.textContent=`${e.type}: ${e.reference||''} · ${e.occurrences} occurrence(s)`;return el;})
          .linkWidth(0).linkDirectionalArrowLength(3).linkDirectionalArrowRelPos(1).linkOpacity(1)
          .linkCurvature(e=>this.curves.get(e.id)||.12)
          .enableNodeDrag(true).onNodeClick(n=>onSelect(n.id)).onBackgroundClick(()=>onSelect(null))
          .onNodeHover(n=>{this.hover=n?.id||null;this.updateArrows();this.syncLabels();this.wake();})
          .onNodeDragEnd(n=>{n.fx=n.x;n.fy=n.y;n.fz=n.z;this.positions.set(n.id,{x:n.x/.45,y:-n.y/.45,z:0,spatialZ:n.z});this.wake();})
          .warmupTicks(0).cooldownTicks(0).cooldownTime(0);
        this.graph.controls().enableDamping=false;
        this.contextAntialias=this.graph.renderer().getContext?.()?.getContextAttributes?.()?.antialias;
        this.graph.linkDirectionalArrowResolution?.(3);
        this.labelLayer=document.createElement('div');this.labelLayer.className='graph-spatial-labels';host.append(this.labelLayer);
        this.applyQuality();this.resize();
        for(const event of ['pointerdown','pointermove','pointerup','wheel','keydown']){const listener=()=>this.wake();host.addEventListener(event,listener,{capture:true,passive:true});this.clean.push(()=>host.removeEventListener(event,listener,{capture:true}));}
        this.observer=new IntersectionObserver(entries=>{this.visible=entries[0].isIntersecting;if(this.visible)this.wake();else this.pause();});this.observer.observe(host);
      }catch(error){this.destroy();throw error;}
    }
    set(view,ix,state){
      const D=root.ArchaeologistGraph,L=root.ArchaeologistLayouts,signature=L.signature(view,state),strategy=`${state.view}:${L.strategy(state)}`;
      const changed=signature!==this.signature;
      this.ix=ix;this.state={...state};this.view=view;this.em=L.emphasis(view,state);
      if(this.quality.setMode(state.quality||'auto'))this.applyQuality();
      const parallel=new Map();this.curves.clear();
      for(const edge of view.edges){const key=[edge.source,edge.target].sort().join('|'),slot=parallel.get(key)||0;parallel.set(key,slot+1);this.curves.set(edge.id,edge.source===edge.target ? .5+slot*.12 : .10+slot*.07);}
      this.visuals=new Map(view.nodes.map(n=>[n.id,D.overlay(n,state.overlay)]));
      this.edgeVisuals=new Map(view.edges.map(e=>[e.id,L.edgeStyle(e,state,this.em)]));
      if(signature!==this.signature){
        if(strategy!==this.strategy||!this.positions.size){this.positions=L.layout(view,ix,state);this.layoutRuns++;}
        else if(view.nodes.some(n=>!this.positions.has(n.id))){const positions=L.layout(view,ix,state);this.layoutRuns++;for(const n of view.nodes)if(!this.positions.has(n.id))this.positions.set(n.id,positions.get(n.id));L.separate(this.positions,view.nodes);}
        const previous=new Map((this.data?.nodes||[]).map(n=>[n.id,n]));
        this.data=D.forceData(view);
        this.data.nodes=this.data.nodes.map(n=>{
          const node=previous.get(n.id)||n,p=this.positions.get(n.id);node.record=n.record;
          // Shared 2D layouts extend into type-separated spatial planes, with fixed
          // coordinates. Selection never restarts physics or changes the layout.
          const z=this.positions.get(n.id)?.spatialZ??D.TYPES.indexOf(n.record.type)*22;
          Object.assign(node,{x:p.x*.45,y:-p.y*.45,z,fx:p.x*.45,fy:-p.y*.45,fz:z});return node;
        });
        this.graph.graphData(this.data);this.dataUpdates++;this.signature=signature;this.strategy=strategy;
      }
      if(changed)this.graph.nodeVal(n=>{const v=this.visuals.get(n.id);return (v.size/5)**3*(v.hotspot?1.4:1);});
      this.graph.nodeColor(n=>this.em.get(n.id)==='selected'?'#F8E8EA':this.em.get(n.id)==='dim'?'#30232d':this.visuals.get(n.id).color)
        .linkColor(e=>{const v=this.edgeVisuals.get(e.id);return v.color+Math.round(v.opacity*255).toString(16).padStart(2,'0');});
      this.styleMaterials();
      this.updateArrows();this.syncLabels();this.wake();
    }
    styleMaterials(){
      // Reuse existing materials: no new geometry, lights or postprocessing passes.
      const performance=this.quality.profile===root.ArchaeologistQuality.PROFILES.performance;
      this.graph.scene().traverse(object=>{if(object.geometry?.type!=='SphereGeometry')return;for(const material of Array.isArray(object.material)?object.material:[object.material])if(material?.emissive?.copy&&material.color){material.emissive.copy(material.color);material.emissiveIntensity=performance?0:.12;}});
    }
    updateArrows(){
      this.graph.linkDirectionalArrowLength(edge=>{
        if(this.quality.profile.arrows==='all')return 3;
        const source=typeof edge.source==='object'?edge.source.id:edge.source,target=typeof edge.target==='object'?edge.target.id:edge.target;
        return [this.state?.selected,this.hover].some(id=>id&&(source===id||target===id))||(this.state?.focus&&(this.edgeVisuals?.get(edge.id)?.opacity||0)>.5)?3:0;
      });
    }
    applyQuality(){
      const profile=this.quality.profile;
      if(this.profile===profile)return;
      this.profile=profile;
      this.graph.renderer().setPixelRatio?.(Math.min(root.devicePixelRatio||1,profile.pixelRatio));
      this.graph.nodeResolution(profile.resolution);this.styleMaterials();
      this.updateArrows();this.syncLabels();this.labelDirty=true;this.onQualityChange();
    }
    qualityDescription(){
      const actual=this.contextAntialias===undefined?'unavailable':this.contextAntialias?'on':'off';
      return `${this.quality.mode==='auto'?this.quality.downgraded?'Auto reduced quality after sustained slow active frame intervals. ':'Auto monitors active frame intervals; this is not GPU profiling. ':''}${this.profile.name} · pixel ratio cap ${this.profile.pixelRatio} · node resolution ${this.profile.resolution} · ${this.profile.labels} normal labels · ${this.profile.arrows} arrowheads. MSAA not requested; context antialias: ${actual}.`;
    }
    syncLabels(){
      if(!this.data)return;
      const priority=[...this.data.nodes].sort((a,b)=>a.id===this.state.selected?-1:b.id===this.state.selected?1:a.id===this.hover?-1:b.id===this.hover?1:(this.em.get(a.id)==='dim')-(this.em.get(b.id)==='dim')).slice(0,this.quality.profile.candidates),ids=new Set(priority.map(n=>n.id));
      for(const [id,label]of this.labels)if(!ids.has(id)){label.remove();this.labels.delete(id);}
      for(const n of priority)if(!this.labels.has(n.id)){const label=document.createElement('span');label.textContent=n.record.name;label.title=n.record.name;this.labelLayer.append(label);this.labels.set(n.id,label);}
      this.labelDirty=true;
    }
    placeLabels(){
      if(!this.data)return;const camera=this.graph.camera(),cameraKey=[camera.position.x,camera.position.y,camera.position.z,camera.quaternion?.x,camera.quaternion?.y,camera.quaternion?.z,camera.quaternion?.w,this.host.clientWidth,this.host.clientHeight].join('|');
      if(!this.labelDirty&&cameraKey===this.cameraKey)return;this.cameraKey=cameraKey;this.labelDirty=false;
      const projected=new Map(),width=this.host.clientWidth,height=this.host.clientHeight;
      this.vector=this.vector||camera.position.clone();
      for(const n of this.data.nodes){
        if(!this.labels.has(n.id))continue;
        const p=this.vector.set(n.x||0,n.y||0,n.z||0),distance=p.distanceTo(camera.position);p.project(camera);
        projected.set(n.id,{x:(p.x+1)*width/2,y:(1-p.y)*height/2,hidden:p.z< -1||p.z>1||Math.abs(p.x)>1||Math.abs(p.y)>1||(distance>1400&&n.id!==this.state.selected&&n.id!==this.hover)});
      }
      const visible=root.ArchaeologistLayouts.labels(this.view.nodes,projected,this.state.selected,this.hover,this.em,1,this.quality.profile.labels);
      for(const [id,label]of this.labels){const p=projected.get(id);label.hidden=!visible.has(id);if(!label.hidden){label.style.left=`${p.x}px`;label.style.top=`${p.y}px`;}}
    }
    wake(duration=220){
      if(this.destroyed||!this.visible||document.hidden)return;
      this.labelDirty=true;if(!this.awake){this.awake=true;this.graph.resumeAnimation();}clearTimeout(this.sleep);
      this.sleep=setTimeout(()=>this.pause(),duration);
      if(this.frame!==null)return;
      const tick=time=>{this.frame=null;if(this.destroyed||!this.visible)return;if(document.hidden){this.pause();return;}if(this.quality.frame(time))this.applyQuality();if(!this.lastLabelTime||time-this.lastLabelTime>=this.quality.profile.labelMs){this.placeLabels();this.lastLabelTime=time;}this.frame=requestAnimationFrame(tick);};this.frame=requestAnimationFrame(tick);
    }
    pause(){clearTimeout(this.sleep);cancelAnimationFrame(this.frame);this.frame=null;this.awake=false;this.quality?.pause();this.graph?.pauseAnimation();}
    focus(id){const n=this.data?.nodes.find(n=>n.id===id);if(!n)return;const camera=this.graph.camera(),delta=camera.position.clone().sub(this.graph.controls().target).normalize().multiplyScalar(150);this.graph.cameraPosition({x:n.x+delta.x,y:n.y+delta.y,z:n.z+delta.z},n,this.reduced?0:300);this.wake(450);}
    fit(){this.graph.zoomToFit(this.reduced?0:250,45);this.wake(400);}
    zoom(factor){const target=this.graph.controls().target,next=this.graph.camera().position.clone().sub(target).multiplyScalar(1/factor).add(target);this.graph.cameraPosition(next,target,0);this.wake();}
    reset(){this.signature=null;this.strategy=null;this.set(this.view,this.ix,this.state);this.graph.cameraPosition({x:0,y:0,z:650},{x:0,y:0,z:0},0);this.fit();}
    resize(){this.graph.width(this.host.clientWidth||800).height(this.host.clientHeight||580);this.labelDirty=true;this.wake();}
    destroy(){
      if(this.destroyed)return;this.pause();this.destroyed=true;this.observer?.disconnect();this.clean.forEach(fn=>fn());this.clean=[];
      const g=this.graph;if(!g){this.host.replaceChildren();return;}
      g.onNodeClick(null).onBackgroundClick(null).onNodeDragEnd(null).onNodeHover(null);
      const geometries=new Set(),materials=new Set(),textures=new Set();
      g.scene().traverse(object=>{if(object.geometry)geometries.add(object.geometry);for(const material of Array.isArray(object.material)?object.material:[object.material]){if(!material)continue;materials.add(material);for(const value of Object.values(material))if(value?.isTexture)textures.add(value);}});
      g.controls()?.dispose();g.graphData({nodes:[],links:[]});if(typeof g._destructor==='function')g._destructor();
      for(const texture of textures)texture.dispose();for(const material of materials)material.dispose?.();for(const geometry of geometries)geometry.dispose();
      g.renderer().renderLists?.dispose();g.renderer().dispose();g.renderer().forceContextLoss();
      this.labels.clear();this.positions.clear();this.data=null;this.host.replaceChildren();this.graph=null;
    }
  }
  root.ArchaeologistThree={webgl,load,Adapter:ThreeGraph};
})(globalThis);
