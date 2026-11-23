'use strict';
const assert=require('node:assert/strict'),test=require('node:test');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const D=require('../../app/static/graph/data.js');
const L=require('../../app/static/graph/layouts.js');
const Q=require('../../app/static/graph/quality.js');
const n=(id,type='function',metadata={})=>({id,type,name:id,path:`src/${id}.c`,metadata});
const e=(id,source,target,type='CALLS')=>({id,source,target,type,status:'resolved_internal',occurrences:1,evidence:[]});
const fixture=()=>({nodes:[n('repo','repository'),n('file','file'),n('a'),n('b'),n('c'),n('other')],edges:[e('d','file','a','DEFINES'),e('ab','a','b'),e('ba','b','a'),e('bc','b','c')],references:[{source:'a',reference:'external',type:'CALLS',status:'unresolved',evidence:{path:'src/a.c',line:1}}]});

test('conversion preserves backend identities and rejects dangling/unresolved edges',()=>{
 const graph=fixture();graph.edges.push(e('missing','a','missing'),{...e('unresolved','a','b'),status:'unresolved'});
 const ix=D.index(graph);assert.equal(ix.nodes.get('a'),graph.nodes[2]);assert.equal(ix.edges.length,4);
 assert.equal(ix.incoming.get('a').length,2);assert.equal(ix.outgoing.get('a').length,1);assert.equal(ix.references.get('a').length,1);
 const view=D.subset(ix,D.initial()),force=D.forceData(view);force.links[0].source={id:'mutated'};force.nodes[0].x=100;
 assert.equal(typeof ix.edges[0].source,'string');assert.equal(graph.nodes[0].x,undefined);
});

test('perspectives, node/edge/language filters',()=>{
 const ix=D.index(fixture()),s=D.initial();s.view='calls';assert(D.subset(ix,s).nodes.every(n=>n.type==='function'));
 s.relations=['DEFINES'];assert.equal(D.subset(ix,s).edges.length,0);
 s.view='dependencies';assert.equal(D.subset(ix,s).nodes.length,1);
 s.view='knowledge';s.types=['repository'];assert.equal(D.subset(ix,s).nodes.length,1);
 s.language='Python';assert.equal(D.subset(ix,s).nodes.length,0);
});

test('search spans full retained graph beyond bounded initial view and active filters',()=>{
 const graph={nodes:Array.from({length:600},(_,i)=>n('function-'+String(i).padStart(4,'0'))),edges:[]},ix=D.index(graph),s=D.initial();
 assert.equal(D.subset(ix,s).nodes.length,D.LIMITS.nodes);assert(D.subset(ix,s).truncated);
 s.types=['file'];assert.equal(D.subset(ix,s).nodes.length,0);
 assert.equal(D.search(ix,'function-0599').nodes[0].id,'function-0599');assert.equal(D.search(ix,'SRC/').total,600);
 s.types=['function'];s.selected='function-0599';assert(D.subset(ix,s).nodes.some(n=>n.id===s.selected));
});

test('bounded neighborhoods are cycle safe and direction/filter aware',()=>{
 const ix=D.index(fixture()),s=D.initial();s.view='calls';
 assert.deepEqual([...D.neighborhood(ix,'a',1,'out',s).ids],['a','b']);
 assert.deepEqual([...D.neighborhood(ix,'a',2,'out',s).ids],['a','b','c']);
 assert.deepEqual([...D.neighborhood(ix,'c',2,'in',s).ids],['c','b','a']);
 const limited=D.neighborhood(ix,'a',2,'both',s,2);assert(limited.truncated);assert.equal(limited.ids.size,2);
 s.relations=[];assert.equal(D.neighborhood(ix,'a',2,'both',s).ids.size,1);
 assert.equal(D.neighborhood(ix,'absent',2,'both',s).ids.size,0);
});

test('bounded edge output and explicit empty/truncated graphs',()=>{
 const empty=D.index(null);assert.equal(D.subset(empty,D.initial()).nodes.length,0);
 const graph=fixture();graph.coverage={truncated:true};graph.edges=Array.from({length:900},(_,i)=>e('e'+i,'a','b'));
 const v=D.subset(D.index(graph),D.initial());assert.equal(v.edges.length,D.LIMITS.edges);assert(v.truncated);assert.equal(v.matchingEdges,900);
});

test('overlays preserve missing metrics and actual C-only predictions',()=>{
 const py=n('py','function',{language:'Python',ml:{status:'analyzed',predicted_class:0}});
 assert.equal(D.overlay(py,'ml').label,'Unscored');assert.equal(D.overlay(n('unknown'),'complexity').label,'Complexity unavailable');
 assert.equal(D.overlay(n('low','function',{complexity_band:'low'}),'complexity').label,'low complexity');
 const c=n('c','function',{language:'C',ml:{status:'analyzed',predicted_class:1,model_probability:.6},hotspots:[{}]});
 assert.equal(D.overlay(c,'ml').color,'#E54859');assert(D.overlay(c).hotspot);assert.equal(D.overlay(n('repo','repository')).shape,'diamond');
 c.metadata.ml.predicted_class=0;assert.match(D.overlay(c,'ml').label,/non-defect/);
 c.metadata.ml.status='unavailable';assert.equal(D.overlay(c,'ml').label,'Unscored');
});

test('incoming/outgoing selection highlighting',()=>{
 const ix=D.index(fixture());assert.equal(D.emphasis(ix,'a','a'),'selected');assert.equal(D.emphasis(ix,'b','a'),'outgoing');assert.equal(D.emphasis(ix,'other','a'),'dim');
 assert.equal(D.emphasis(ix,'b','c','in'),'incoming');assert.equal(D.emphasis(ix,'b','c','out'),'dim');
 assert.equal(D.emphasis(ix,'b','a','both',[]),'dim');
});

// A small DOM harness tests actual shared controller lifecycle and safe text rendering,
// without claiming browser geometry or GPU verification.
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.listeners={};this.dataset={};this.attrs={};this.style={};this.value='';this.hidden=false;this.clientWidth=900;this.clientHeight=550;this.checked=false;this.className='';this._text='';this.classList={add:()=>{},remove:()=>{},contains:()=>false,toggle:()=>false};}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent||'').join('');}
 set innerHTML(value){throw Error('Unsafe innerHTML assignment: '+value);}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[...nodes];this._text='';}
 setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k];}
 addEventListener(k,fn){this.listeners[k]=fn;}removeEventListener(k){delete this.listeners[k];}
 querySelectorAll(selector){let result=[];for(const c of this.children){if(c.tagName==='input'&&(selector!=='input:checked'||c.checked))result.push(c);result.push(...(c.querySelectorAll?.(selector)||[]));}return result;}
 focus(){this.focused=true;}remove(){}getBoundingClientRect(){return {width:900,height:550};}
}
function controller(){
 const elements=new Map();let created=0,destroyed=0;const loads=[];
 const document={getElementById:id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement:t=>new Element(t),addEventListener(){}};
 class Adapter{constructor(){created++;this.graph=null;}set(v,ix,s){this.view=v;this.state=s;}fit(){}focus(){}zoom(){}reset(){}resize(){}destroy(){destroyed++;}}
 const context={ArchaeologistGraph:D,ArchaeologistSVG:Adapter,ArchaeologistThree:{webgl:()=>true,Adapter,load:()=>new Promise((resolve,reject)=>loads.push({resolve,reject}))},document,matchMedia:()=>({matches:false}),ResizeObserver:class{observe(){}},IntersectionObserver:class{observe(){}},Option:class extends Element{constructor(t,v){super('option');this.textContent=t;this.value=v;}},clearTimeout,setTimeout,console};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/explorer.js'),'utf8'),context);
 return {context,explorer:context.graphExplorer,elements,loads,counts:()=>({created,destroyed})};
}

test('renderer switching preserves shared state; stale asynchronous loads do not attach',async()=>{
 const h=controller(),x=h.explorer;x.setGraph(fixture());
 Object.assign(x.state,{selected:'a',query:'a',view:'calls',overlay:'complexity',focus:'a',hops:2,direction:'out',language:'C',layout:'radial',quality:'performance'});
 const state=x.state;await x.switchMode('2d');const p=x.switchMode('3d');await x.switchMode('2d');h.loads[0].resolve();await p;
 assert.equal(x.state,state);assert.equal(x.state.selected,'a');assert.equal(x.state.overlay,'complexity');assert.equal(x.state.hops,2);assert.equal(x.state.mode,'2d');
 const next=x.switchMode('3d');h.loads[1].resolve();await next;assert.equal(x.state.mode,'3d');assert.equal(x.state.query,'a');assert.equal(x.state.layout,'radial');assert.equal(x.state.quality,'performance');
 assert.equal(h.counts().created,3);assert.equal(h.counts().destroyed,2);
});

test('missing 3D asset falls back honestly; repository switch disposes previous instance',async()=>{
 const h=controller(),x=h.explorer;x.setGraph(fixture());await x.switchMode('2d');const p=x.switchMode('3d');h.loads[0].reject(new Error('local bundle missing'));await p;
 assert.equal(x.state.mode,'2d');assert.match(x.notice,/local bundle missing/);assert.equal(h.counts().destroyed,1);
 x.state.selected='a';x.setGraph({nodes:[n('new')],edges:[]});assert.equal(h.counts().destroyed,2);assert.equal(x.state.selected,null);assert.equal(x.ix.nodes.has('a'),false);
});

test('WebGL fallback, search selection beyond filters, and safe labels',async()=>{
 const h=controller(),x=h.explorer,graph=fixture();graph.nodes[2].name='<img src=x onerror=alert(1)>';x.setGraph(graph);x.supports3D=false;await x.switchMode('3d');assert.equal(x.state.mode,'2d');
 x.state.types=['file'];x.state.view='dependencies';x.choose('a');assert.equal(x.state.selected,'a');assert.equal(x.state.view,'knowledge');assert(x.view.nodes.some(n=>n.id==='a'));
 assert(h.elements.get('graph-inspection').textContent.includes('<img src=x onerror=alert(1)>'));
 assert.equal(x.ix.nodes.get('a').name,'<img src=x onerror=alert(1)>');
});

test('real SVG adapter creates text safely and removes handlers on disposal',()=>{
 const nodes=[];const document={activeElement:null,createElementNS:(ns,tag)=>{const el=new Element(tag);el.closest=()=>null;nodes.push(el);return el;}};
 const context={ArchaeologistGraph:D,ArchaeologistLayouts:L,document,requestAnimationFrame:()=>1,cancelAnimationFrame:()=>{}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/svg.js'),'utf8'),context);
 const host=new Element(),adapter=new context.ArchaeologistSVG(host,()=>{}),graph=fixture();graph.nodes[2].name='<script>alert(1)</script>';
 const ix=D.index(graph);adapter.set(D.subset(ix,D.initial()),ix,D.initial());assert(nodes.some(n=>n.tagName==='text'&&n.textContent.includes('<script>')));
 const svg=adapter.svg;adapter.zoom(1.2);adapter.focus('a');assert(Number.isFinite(adapter.box.w));adapter.destroy();assert.equal(Object.keys(svg.listeners).length,0);assert.equal(host.children.length,0);
});

test('WebGL detection handles failures without throwing',()=>{
 const context={document:{createElement:()=>({getContext:()=>{throw Error('denied');}})}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 assert.equal(context.ArchaeologistThree.webgl(),false);
});

test('real 3D adapter uses isolated data, safe labels, bounded simulation and resource cleanup',()=>{
 let raf=0,cancelled=0,disconnected=0,disposed=0,contextLost=0,destructed=0;
 let updates=0;const options=[];const calls={},host=new Element(),controlEvents=new Map(),controls={target:{x:0,y:0,z:0},mouseButtons:{LEFT:0,RIGHT:2},listenToKeyEvents(el){calls.keyHost=el;},stopListenToKeyEvents(){calls.keysStopped=true;},addEventListener(type,fn){controlEvents.set(type,fn);},removeEventListener(type){controlEvents.delete(type);},dispose(){disposed++;}};
 const graph={};
 const methods=['backgroundColor','showNavInfo','nodeId','nodeResolution','nodeLabel','linkLabel','linkDirectionalArrowLength','linkDirectionalArrowRelPos','linkOpacity','linkCurvature','enableNodeDrag','onNodeClick','onBackgroundClick','onNodeDragEnd','onNodeHover','warmupTicks','cooldownTicks','cooldownTime','nodeVal','nodeColor','linkColor','linkWidth','width','height','cameraPosition','zoomToFit'];
 for(const method of methods)graph[method]=(...args)=>{calls[method]=args;return graph;};
 graph.controls=()=>controls;graph.graphData=data=>{updates++;calls.graphData=data;return graph;};
 graph.pauseAnimation=()=>{calls.paused=true;};graph.resumeAnimation=()=>{};
 const material={color:{},emissive:{copy(){}},dispose(){disposed++;}};graph.scene=()=>({traverse:fn=>fn({geometry:{type:'SphereGeometry',dispose(){disposed++;}},material})});
 graph.renderer=()=>({renderLists:{dispose(){disposed++;}},dispose(){disposed++;},forceContextLoss(){contextLost++;},setPixelRatio(value){calls.pixelRatio=value;},getContext(){return {getContextAttributes:()=>({antialias:false})};}});
 class Vector{constructor(x=0,y=0,z=650){Object.assign(this,{x,y,z});}clone(){return new Vector(this.x,this.y,this.z);}sub(v){this.x-=v.x;this.y-=v.y;this.z-=v.z;return this;}lengthSq(){return this.x**2+this.y**2+this.z**2;}set(x,y,z){Object.assign(this,{x,y,z});return this;}normalize(){return this.multiplyScalar(1/(Math.sqrt(this.lengthSq())||1));}multiplyScalar(s){this.x*=s;this.y*=s;this.z*=s;return this;}add(v){this.x+=v.x;this.y+=v.y;this.z+=v.z;return this;}}
 graph.camera=()=>({fov:50,position:new Vector()});
 graph._destructor=()=>{destructed++;};
 const document={createElement:tag=>new Element(tag)};
 const context={ArchaeologistGraph:D,ArchaeologistLayouts:L,ArchaeologistQuality:Q,setTimeout,clearTimeout,document,ForceGraph3D:config=>{options.push(config);return ()=>graph;},requestAnimationFrame:()=>++raf,cancelAnimationFrame:()=>{cancelled++;},IntersectionObserver:class{observe(){}disconnect(){disconnected++;}}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 const adapter=new context.ArchaeologistThree.Adapter(host,()=>{},true),fixtureGraph=fixture();fixtureGraph.nodes[2].name='<img onerror=alert(1)>';fixtureGraph.nodes.push(n('dependency','file'));fixtureGraph.edges.push(e('import','file','dependency','IMPORTS'),e('include','dependency','file','INCLUDES'));
 const ix=D.index(fixtureGraph),s=D.initial();s.selected='a';adapter.set(D.subset(ix,s),ix,s);
 assert.equal(options[0].rendererConfig.antialias,false);assert.equal(material.emissiveIntensity,.12);
 assert.equal(calls.cooldownTicks[0],0);assert.equal(calls.warmupTicks[0],0);assert.equal(controls.enableDamping,false);
 assert.equal(calls.nodeLabel[0]({record:fixtureGraph.nodes[2]}).textContent,'<img onerror=alert(1)> · src/a.c');
 assert.equal(calls.graphData.nodes[0].record.id,D.subset(ix,s).nodes[0].id);
 for(const view of ['knowledge','calls','dependencies']){
  s.view=view;s.selected=null;const subset=D.subset(ix,s);adapter.set(subset,ix,s);
  const count=updates,runs=adapter.layoutRuns,first=adapter.data.nodes[0],location=first?{x:first.x,y:first.y,z:first.z}:null;
  for(const overlay of ['entity','complexity','ml']){s.overlay=overlay;s.selected=first?.id;adapter.set(subset,ix,s);}
  assert.equal(updates,count,`3D ${view}: style-only updates must not resubmit graph data`);assert.equal(adapter.layoutRuns,runs);
  assert.equal(adapter.data.nodes[0],first);if(first)assert.deepEqual({x:first.x,y:first.y,z:first.z},location);
 }
 // Fit must work before library meshes exist, and include translated/disconnected nodes.
 adapter.data.nodes=[{x:1000,y:200,z:50},{x:1400,y:800,z:150}];adapter.fit();
 assert.deepEqual(JSON.parse(JSON.stringify(calls.cameraPosition[1])),{x:1200,y:500,z:100});
 assert(calls.cameraPosition[0].z>calls.cameraPosition[1].z);assert.equal(calls.keyHost,host);
 assert.equal(controls.enablePan,true);assert.equal(controls.screenSpacePanning,true);
 adapter.panMode(true);assert.equal(controls.mouseButtons.LEFT,2);adapter.panMode(false);assert.equal(controls.mouseButtons.LEFT,0);
 const firstDistance=calls.cameraPosition[0].z;host.clientWidth=400;adapter.resize();assert.equal(calls.width[0],400);assert(calls.cameraPosition[0].z>firstDistance);
 controlEvents.get('start')();assert.equal(adapter.autoFit,false);
 const previous=calls.cameraPosition;host.clientWidth=600;adapter.resize();assert.equal(calls.cameraPosition,previous,'resizing after panning must preserve camera');
 host.clientWidth=0;adapter.resize();assert.equal(calls.width[0],600,'hidden hosts must not get a fabricated width');
 host.clientWidth=900;adapter.resize();adapter.data.nodes=[{x:20,y:30,z:40}];adapter.reset();assert.deepEqual(JSON.parse(JSON.stringify(calls.cameraPosition[1])),{x:20,y:30,z:40});
 const layoutRuns=adapter.layoutRuns;adapter.reset();assert.equal(adapter.layoutRuns,layoutRuns,'reset camera must preserve node arrangement');
 adapter.width=0;adapter.fit();assert.equal(adapter.autoFit,true,'fit requested while hidden must resume when measured');host.clientWidth=800;adapter.resize();assert.equal(adapter.width,800);
 adapter.data.nodes=[];const emptyPosition=calls.cameraPosition;adapter.fit();adapter.reset();assert.equal(calls.cameraPosition,emptyPosition);
 const count=updates,runs=adapter.layoutRuns;
 s.quality='performance';adapter.set(D.subset(ix,s),ix,s);assert.equal(calls.nodeResolution[0],4);assert.equal(material.emissiveIntensity,0);assert.equal(calls.pixelRatio,1);assert.equal(updates,count);assert.equal(adapter.layoutRuns,runs);
 assert.match(adapter.qualityDescription(),/context antialias: off/);
 const arrow=calls.linkDirectionalArrowLength[0];assert.equal(arrow({source:s.selected,target:'other'}),3);assert.equal(arrow({source:'unrelated',target:'another'}),0);
 s.quality='balanced';adapter.set(D.subset(ix,s),ix,s);assert.equal(calls.nodeResolution[0],6);assert.equal(updates,count);
 adapter.pause();assert(calls.paused);assert.equal(calls.cooldownTime[0],0);

 adapter.destroy();adapter.destroy();assert.equal(destructed,1);assert.equal(contextLost,1);assert.equal(controlEvents.size,0);assert.equal(calls.keysStopped,true);assert.equal(Object.keys(host.listeners).length,0);assert(cancelled>=1);assert.equal(disconnected,1);assert(disposed>=4);
});

function hierarchyFixture(){return {nodes:[n('root','repository'),n('dir','directory'),n('file','file'),n('a'),n('b'),n('otherDir','directory'),n('otherFile','file')],edges:[e('rd','root','dir','CONTAINS'),e('df','dir','file','CONTAINS'),e('fa','file','a','DEFINES'),e('fb','file','b','DEFINES'),e('ro','root','otherDir','CONTAINS'),e('of','otherDir','otherFile','CONTAINS'),e('ab','a','b')]};}

test('automatic strategy is perspective-specific; layouts are deterministic and collision-aware',()=>{
 const ix=D.index(hierarchyFixture());
 assert.equal(L.strategy({...D.initial(),view:'knowledge'}),'hierarchy');assert.equal(L.strategy({...D.initial(),view:'calls'}),'directed');assert.equal(L.strategy({...D.initial(),view:'dependencies'}),'clusters');
 for(const view of ['knowledge','calls','dependencies'])for(const layout of ['auto','hierarchy','radial']){
  const state={...D.initial(),view,layout},subset=D.subset(ix,state),positions=L.layout(subset,ix,state);
  assert.deepEqual([...positions],[...L.layout(subset,ix,state)]);
  assert.equal(positions.size,subset.nodes.length);
  const values=[...positions.values()];assert(values.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
  for(let i=0;i<values.length;i++)for(let j=i+1;j<values.length;j++)assert(Math.abs(values[i].x-values[j].x)>50||Math.abs(values[i].y-values[j].y)>50);
 }
});

test('hierarchy grouping, group collapse and branch focus use actual containment',()=>{
 const ix=D.index(hierarchyFixture()),state=D.initial();
 assert.equal(ix.hierarchy.parent.get('a'),'file');assert.deepEqual([...L.descendants(ix,'file').ids].sort(),['a','b','file']);
 state.collapsed=['file'];const collapsed=D.subset(ix,state);assert.equal(collapsed.groupHidden,2);assert(!collapsed.nodes.some(n=>n.id==='a'));
 state.query='a';assert(D.subset(ix,state).nodes.some(n=>n.id==='a'));state.query='';state.collapsed=[];state.branch='dir';
 assert.deepEqual(D.subset(ix,state).nodes.map(n=>n.id).sort(),['a','b','dir','file']);
 state.branch=null;const positions=L.layout(D.subset(ix,state),ix,state);
 assert(positions.get('root').y<positions.get('dir').y);assert(positions.get('file').y<positions.get('a').y);
});

test('directed SCC layers retain recursion and upstream/downstream order',()=>{
 const graph={nodes:[n('up'),n('a'),n('b'),n('down')],edges:[e('up-a','up','a'),e('ab','a','b'),e('ba','b','a'),e('self','a','a'),e('b-down','b','down')]};
 const ix=D.index(graph),s={...D.initial(),view:'calls'},v=D.subset(ix,s),positions=L.layout(v,ix,s);
 assert(positions.get('up').x<positions.get('a').x);assert.equal(positions.get('a').x,positions.get('b').x);assert(positions.get('down').x>positions.get('b').x);assert.equal(v.edges.length,5);
 s.selected='up';s.focus='up';s.hops=2;const em=L.emphasis(v,s);assert.equal(em.get('a'),'outgoing');assert.equal(em.get('b'),'outgoing');
 s.selected='down';s.focus='down';const incoming=L.emphasis(v,s);assert.equal(incoming.get('b'),'incoming');assert.equal(incoming.get('a'),'incoming');
});

test('dependency direction and edge kinds remain distinct with cycles and occurrence counts',()=>{
 const graph={nodes:[n('py','file'),n('c','file')],edges:[e('imports','py','c','IMPORTS'),{...e('includes','c','py','INCLUDES'),occurrences:3}]};
 const ix=D.index(graph),s={...D.initial(),view:'dependencies',selected:'py'},v=D.subset(ix,s),em=L.emphasis(v,s);
 const outgoing=L.edgeStyle(v.edges[0],s,em),incoming=L.edgeStyle(v.edges[1],s,em);assert.notEqual(outgoing.color,incoming.color);assert.equal(v.edges[1].occurrences,3);
 const neutral={...s,selected:null};assert.notEqual(L.edgeStyle(v.edges[0],neutral,em).color,L.edgeStyle(v.edges[1],neutral,em).color);
 assert(L.edgeStyle(v.edges[1],neutral,em).dash);assert.equal(L.layout(v,ix,s).size,2);
});

test('contextual labels prioritize selected and hovered nodes without overlapping ordinary labels',()=>{
 const nodes=[n('selected'),n('hover'),n('near'),n('unrelated')],positions=new Map(nodes.map((n,i)=>[n.id,{x:i<3?0:200,y:0}])),em=new Map([['selected','selected'],['near','outgoing'],['unrelated','dim']]);
 const small=L.labels(nodes,positions,'selected','hover',em,.1,2);assert(small.has('selected'));assert(small.has('hover'));assert(!small.has('unrelated'));
 const larger=L.labels(nodes,positions,'selected',null,em,2,20);assert(larger.has('unrelated'));assert(!larger.has('near'));
});

test('perspective switching clears incompatible filters explicitly but preserves layout/overlay',()=>{
 const h=controller(),x=h.explorer;x.setGraph(hierarchyFixture());Object.assign(x.state,{selected:'a',focus:'a',layout:'radial',overlay:'ml',types:['function'],relations:['CALLS'],language:'C'});
 x.changeView('dependencies');assert.equal(x.state.selected,null);assert.equal(x.state.focus,null);assert.deepEqual([...x.state.types],D.TYPES);assert.equal(x.state.language,'');assert.equal(x.state.layout,'radial');assert.equal(x.state.overlay,'ml');assert.match(x.notice,/filters reset/);
 const panel=h.elements.get('graph-inspection');x.choose('dir');assert(!panel.textContent.includes('Cyclomatic complexity'));assert(!panel.textContent.includes('ML defect risk'));assert(panel.textContent.includes('Relative directory'));
});

test('SVG reuses keyed elements and positions through selection/overlay and batches pointer work',()=>{
 const queue=new Map();let next=0,cancelled=0;
 const document={createElementNS:(ns,tag)=>{const el=new Element(tag);el.closest=()=>null;return el;}};
 const context={ArchaeologistGraph:D,ArchaeologistLayouts:L,document,requestAnimationFrame:fn=>{queue.set(++next,fn);return next;},cancelAnimationFrame:id=>{queue.delete(id);cancelled++;}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/svg.js'),'utf8'),context);
 const adapter=new context.ArchaeologistSVG(new Element(),()=>{}),ix=D.index(hierarchyFixture()),s=D.initial(),view=D.subset(ix,s);
 const flush=()=>{const callbacks=[...queue.values()];queue.clear();for(const callback of callbacks)callback();};
 adapter.set(view,ix,s);flush();const node=adapter.nodes.get('a'),edge=adapter.edges.get('fa'),position={...adapter.positions.get('a')},runs=adapter.layoutRuns;
 s.selected='a';s.overlay='ml';adapter.set(view,ix,s);adapter.schedule();adapter.schedule();assert.equal(queue.size,1);flush();
 assert.equal(adapter.nodes.get('a'),node);assert.equal(adapter.edges.get('fa'),edge);assert.deepEqual(adapter.positions.get('a'),position);assert.equal(adapter.layoutRuns,runs);
 adapter.reset();assert.equal(adapter.layoutRuns,runs+1);
 for(const perspective of ['knowledge','calls','dependencies']){
  s.view=perspective;const subset=D.subset(ix,s);adapter.set(subset,ix,s);flush();
  const runs=adapter.layoutRuns,groups=[...adapter.nodes.values()].map(n=>n.group);
  s.overlay='complexity';s.selected=subset.nodes[0]?.id;adapter.set(subset,ix,s);flush();
  assert.equal(adapter.layoutRuns,runs,`2D ${perspective}: selection preserves layout`);assert.deepEqual([...adapter.nodes.values()].map(n=>n.group),groups);
 }
 adapter.destroy();assert(cancelled>=1);
});

test('collision spacing checks neighboring cells and large collapsed overviews remain searchable',()=>{
 const nodes=[n('left'),n('right')],positions=new Map([['left',{x:86,y:0}],['right',{x:88,y:0}]]);L.separate(positions,nodes);
 assert(Math.abs(positions.get('left').y-positions.get('right').y)>=78);
 const graph=hierarchyFixture();for(let i=0;i<250;i++){graph.nodes.push(n('func'+i));graph.edges.push(e('def'+i,'file','func'+i,'DEFINES'));}
 const h=controller();h.explorer.setGraph(graph);assert(h.explorer.state.collapsed.includes('file'));assert(h.explorer.view.groupHidden>=252);
 assert.equal(D.search(h.explorer.ix,'func249').total,1);h.explorer.choose('func249');assert(h.explorer.view.nodes.some(n=>n.id==='func249'));assert(h.explorer.view.nodes.length<=D.LIMITS.nodes);
});

test('automatic quality uses sustained active frame intervals and excludes idle gaps',()=>{
 const policy=new Q.Policy();let now=0;
 assert.equal(policy.profile,Q.PROFILES.automatic);
 policy.frame(now);for(let i=0;i<24;i++)assert.equal(policy.frame(now+=35),false);
 assert.equal(policy.slowWindows,1);policy.pause();now+=200000;assert.equal(policy.frame(now),false);
 for(let i=0;i<23;i++)assert.equal(policy.frame(now+=35),false);
 assert.equal(policy.frame(now+=35),true);assert.equal(policy.profile,Q.PROFILES.performance);assert.equal(policy.downgraded,true);
 for(let i=0;i<70;i++)policy.frame(now+=10);assert.equal(policy.profile,Q.PROFILES.performance); // no oscillation
 policy.setMode('balanced');assert.equal(policy.profile,Q.PROFILES.balanced);assert.equal(policy.downgraded,false);
});

test('quality policy does not downgrade on isolated stalls and preserves explicit choices',()=>{
 const policy=new Q.Policy();let now=0;policy.frame(now);
 for(let window=0;window<4;window++)for(let i=0;i<24;i++)policy.frame(now+=i===0?150:16);
 assert.equal(policy.downgraded,false);
 policy.setMode('performance');for(let i=0;i<100;i++)policy.frame(now+=45);assert.equal(policy.profile,Q.PROFILES.performance);
 policy.setMode('balanced');for(let i=0;i<100;i++)policy.frame(now+=45);assert.equal(policy.profile,Q.PROFILES.balanced);
 const h=controller();h.explorer.setGraph(fixture());h.explorer.state.quality='performance';h.explorer.clear();assert.equal(h.explorer.state.quality,'performance');h.explorer.setGraph(fixture());assert.equal(h.explorer.state.quality,'performance');
});

test('WebGL probe explicitly avoids requesting antialiasing and releases its context',()=>{
 const requests=[];let lost=0;
 const context={document:{createElement:()=>({getContext:(kind,options)=>{requests.push({kind,options});return {getExtension:()=>({loseContext(){lost++;}})};}})}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 assert.equal(context.ArchaeologistThree.webgl(),true);assert.equal(requests[0].options.antialias,false);assert.equal(lost,1);
});

test('3D pan control exposes pressed state and resets on renderer replacement',async()=>{
 const h=controller();h.explorer.setGraph(fixture());
 const switching=h.explorer.switchMode('3d');h.loads[0].resolve();await switching;
 const modes=[];h.explorer.adapter.panMode=value=>modes.push(value);
 const pan=h.elements.get('graph-pan');assert.equal(pan.hidden,false);
 pan.listeners.click();assert.equal(pan.getAttribute('aria-pressed'),'true');assert.equal(modes[0],true);
 h.explorer.syncControls();assert.equal(pan.getAttribute('aria-pressed'),'true');
 await h.explorer.switchMode('2d');assert.equal(pan.hidden,true);assert.equal(pan.getAttribute('aria-pressed'),'false');
});

test('camera transitions use the current reduced-motion preference without changing controls',()=>{
 const context={document:{}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 const duration=context.ArchaeologistThree.Adapter.prototype.duration;
 assert.equal(duration.call({reduced:true},450),0);
 context.matchMedia=()=>({matches:false});assert.equal(duration.call({reduced:true},450),450);
 context.matchMedia=()=>({matches:true});assert.equal(duration.call({reduced:false},450),0);
});

test('a later camera request wins; canceled callbacks cannot overwrite Fit and controls remain immediate',()=>{
 const queue=new Map();let next=0,last=null;
 const context={document:{},performance:{now:()=>0},requestAnimationFrame:fn=>{queue.set(++next,fn);return next;},cancelAnimationFrame:id=>queue.delete(id),matchMedia:()=>({matches:false})};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 const proto=context.ArchaeologistThree.Adapter.prototype;
 const adapter=Object.create(proto);adapter.graph={camera:()=>({position:{x:0,y:0,z:100}}),controls:()=>({target:{x:0,y:0,z:0}}),cameraPosition:(p,t,ms)=>{last={p,t,ms};}};
 adapter.cameraMove({x:1,y:2,z:3},{x:4,y:5,z:6},450);const stale=[...queue.values()][0];
 adapter.cameraMove({x:100,y:200,z:300},{x:10,y:20,z:30},340);const current=[...queue.values()][0];
 current(340);assert.equal(last.p.x,100);assert.equal(last.t.x,10);assert.equal(last.ms,0);
 stale(450);assert.equal(last.p.x,100,'old focus cannot overwrite fit');
 adapter.cameraMove({x:1,y:2,z:3},{x:0,y:0,z:0},450);const before=last;adapter.cancelCamera();[...queue.values()].forEach(fn=>fn(500));assert.equal(last,before);
 context.matchMedia=()=>({matches:true});adapter.cameraMove({x:8,y:9,z:10},{x:0,y:0,z:0},450);assert.equal(last.p.x,8);assert.equal(adapter.cameraFrame,null);
});
