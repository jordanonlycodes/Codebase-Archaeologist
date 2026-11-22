'use strict';
const assert=require('node:assert/strict'),test=require('node:test');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const D=require('../../app/static/graph/data.js');
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
 Object.assign(x.state,{selected:'a',query:'a',view:'calls',overlay:'complexity',focus:'a',hops:2,direction:'out',language:'C'});
 const state=x.state;await x.switchMode('2d');const p=x.switchMode('3d');await x.switchMode('2d');h.loads[0].resolve();await p;
 assert.equal(x.state,state);assert.equal(x.state.selected,'a');assert.equal(x.state.overlay,'complexity');assert.equal(x.state.hops,2);assert.equal(x.state.mode,'2d');
 const next=x.switchMode('3d');h.loads[1].resolve();await next;assert.equal(x.state.mode,'3d');assert.equal(x.state.query,'a');
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
 const context={ArchaeologistGraph:D,document};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/svg.js'),'utf8'),context);
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
 const calls={},host=new Element(),controls={target:{x:0,y:0,z:0},dispose(){disposed++;}};
 const graph={};
 const methods=['backgroundColor','showNavInfo','nodeId','nodeResolution','nodeLabel','linkLabel','linkDirectionalArrowLength','linkDirectionalArrowRelPos','linkOpacity','linkCurvature','enableNodeDrag','onNodeClick','onBackgroundClick','onNodeDragEnd','warmupTicks','cooldownTicks','cooldownTime','nodeVal','nodeColor','linkColor','linkWidth','width','height','cameraPosition','zoomToFit'];
 for(const method of methods)graph[method]=(...args)=>{calls[method]=args;return graph;};
 graph.controls=()=>controls;graph.graphData=data=>{calls.graphData=data;return graph;};
 graph.pauseAnimation=()=>{calls.paused=true;};graph.resumeAnimation=()=>{};
 graph.scene=()=>({traverse:fn=>fn({geometry:{dispose(){disposed++;}},material:{dispose(){disposed++;}}})});
 graph.renderer=()=>({renderLists:{dispose(){disposed++;}},dispose(){disposed++;},forceContextLoss(){contextLost++;}});
 graph._destructor=()=>{destructed++;};
 const document={createElement:tag=>new Element(tag)};
 const context={ArchaeologistGraph:D,document,ForceGraph3D:()=>()=>graph,requestAnimationFrame:()=>++raf,cancelAnimationFrame:()=>{cancelled++;},IntersectionObserver:class{observe(){}disconnect(){disconnected++;}}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/graph/three.js'),'utf8'),context);
 const adapter=new context.ArchaeologistThree.Adapter(host,()=>{},true),fixtureGraph=fixture();fixtureGraph.nodes[2].name='<img onerror=alert(1)>';
 const ix=D.index(fixtureGraph),s=D.initial();s.selected='a';adapter.set(D.subset(ix,s),ix,s);
 assert.equal(calls.cooldownTicks[0],0);assert.equal(calls.warmupTicks[0],0);assert.equal(controls.enableDamping,false);
 assert.equal(calls.nodeLabel[0]({record:fixtureGraph.nodes[2]}).textContent,'<img onerror=alert(1)> · src/a.c');
 assert.equal(calls.graphData.nodes[0].record.id,D.subset(ix,s).nodes[0].id);
 adapter.destroy();adapter.destroy();assert.equal(destructed,1);assert.equal(contextLost,1);assert.equal(cancelled,1);assert.equal(disconnected,1);assert(disposed>=4);
});
