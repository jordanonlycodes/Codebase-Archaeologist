'use strict';
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
require('../../app/static/graph/data.js');const L=require('../../app/static/graph/layouts.js'),A=require('../../app/static/architecture/data.js');
const metrics=(files,lines,functions,score=null)=>({files,source_files:files,physical_lines:lines,bytes:lines*4,functions,max_complexity:functions?3:null,total_complexity:functions?functions*3:null,hotspots:functions==null?null:0,max_c_function_score:score,scored_functions:score==null?0:1,measured_files:{functions:functions==null?0:files,max_complexity:functions?files:0,hotspots:functions==null?0:files,max_c_function_score:score==null?0:1}});
function fixture(){return {heatmap:[
 {id:'root',parent_id:null,type:'directory',name:'Repository',path:'.',metrics:metrics(3,40,2,.7)},
 {id:'src',parent_id:'root',type:'directory',name:'src',path:'src',metrics:metrics(2,30,2,.7)},
 {id:'a',parent_id:'src',type:'file',name:'a.c',path:'src/a.c',component_id:'component-src',language:'C',metrics:metrics(1,20,1,.7),ml_status:'scored',graph_id:'a'},
 {id:'b',parent_id:'src',type:'file',name:'b.py',path:'src/b.py',component_id:'component-src',language:'Python',metrics:metrics(1,10,1),ml_status:'unsupported',graph_id:'b'},
 {id:'c',parent_id:'root',type:'file',name:'c.js',path:'c.js',component_id:'component-root',language:'JavaScript',metrics:metrics(1,10,null),structural_status:'unsupported',ml_status:'unsupported'}],
 components:[{id:'component-src',name:'src',path:'src',metrics:metrics(2,30,2,.7),file_ids:['a','b'],function_ids:[],incoming_components:[],outgoing_components:['component-root'],unresolved_ids:['missing'],unresolved_count:1,intra_component_edges:0,intra_component_occurrences:0,graph_id:'src'},
 {id:'component-root',name:'(root files)',path:'.',metrics:metrics(1,10,null),file_ids:['c'],function_ids:[],incoming_components:['component-src'],outgoing_components:[],unresolved_ids:[],unresolved_count:0,intra_component_edges:0,intra_component_occurrences:0}],
 edges:[{id:'edge',source:'component-src',target:'component-root',type:'CALLS',graph_edges:1,occurrences:2,edge_ids:['original']}],
 dependency_cycles:[],findings:[{title:'Observed functions',component_id:'component-src',text:'src has 2 measured functions.'}],summary:{aggregate_edges:1},coverage:{inventory_files:3,retained_files:3,structural_measured_files:2,graph_mapped_files:2,graph_complete:false,issues:[],unmapped_semantic_edges:0,omitted_component_edges:0}};}

test('indexes, memberships, breadcrumbs and full retained search',()=>{
 const ix=A.index(fixture());assert.equal(ix.nodes.size,5);assert.equal(ix.outgoing.get('component-src')[0].target,'component-root');
 assert.deepEqual(A.breadcrumbs(ix,'a').map(n=>n.id),['root','src','a']);assert.deepEqual(A.filesUnder(ix,'src').map(n=>n.id),['a','b']);assert.equal(A.search(ix,'B.PY')[0].id,'b');assert.equal(A.filesUnder(ix,'src'),A.filesUnder(ix,'src'));
});

test('metric states distinguish zero, missing, unsupported, unscored and partial',()=>{
 const ix=A.index(fixture());assert.equal(A.metric(ix.nodes.get('b'),'max_c_function_score').state,'unsupported');assert.equal(A.metric(ix.nodes.get('c'),'functions').state,'unsupported');
 assert.equal(A.metric(ix.nodes.get('a'),'hotspots').value,0);assert.equal(A.metric(ix.root,'max_c_function_score').state,'partial');assert.equal(A.metric(ix.root,'max_c_function_score').covered,1);
 const unscored={metrics:metrics(1,0,0),ml_status:'unscored'};assert.equal(A.metric(unscored,'max_c_function_score').state,'unscored');
 assert.equal(A.tone(unscored,'max_c_function_score',1).fill,'url(#architecture-unscored)');assert.notEqual(A.tone(ix.nodes.get('a'),'max_c_function_score',1).fill,'url(#architecture-unscored)');
});

test('treemap is deterministic, nested, bounded and cached independently of color',()=>{
 const ix=A.index(fixture()),map=A.treemap(ix,'root','physical_lines');assert.equal(map,A.treemap(ix,'root','physical_lines'));assert(map.regions.length<=A.LIMITS.regions);
 const directory=map.regions.find(r=>r.node.id==='src'),a=map.regions.find(r=>r.node.id==='a');assert(a.x>=directory.x&&a.y>=directory.y+25);assert(a.x+a.w<=directory.x+directory.w);
 for(const r of map.regions)assert(r.x>=0&&r.y>=0&&r.x+r.w<=1000&&r.y+r.h<=600);
 assert.equal(A.treemap(ix,'src','bytes').entries,2);assert.equal(A.treemap(ix,'root','physical_lines'),map);
});

test('partition reflects documented weights, including zero-entry floor',()=>{
 const a={id:'a',metrics:{bytes:3}},b={id:'b',metrics:{bytes:1}},parts=A.partition([a,b],{x:0,y:0,w:100,h:100},'bytes');
 assert.equal(parts.find(p=>p.node.id==='a').w*parts.find(p=>p.node.id==='a').h,7500);
 const zero=A.partition([{metrics:{bytes:0}},{metrics:{bytes:0}}],{x:0,y:0,w:100,h:100},'bytes');assert.equal(zero[0].w*zero[0].h,5000);
});

test('large component/heatmap subsets remain navigable without inventing regions',()=>{
 const data=fixture();for(let i=0;i<300;i++){data.heatmap.push({id:'f'+i,parent_id:'root',name:'f'+i,path:'f'+i,type:'file',metrics:metrics(1,1,0)});data.components.push({...data.components[0],id:'component-'+i,name:'component-'+i,path:'component-'+i});}
 const ix=A.index(data),s=A.initial();s.component='component-299';const view=A.componentView(ix,s);assert.equal(view.components.length,A.LIMITS.components);assert(view.components.some(c=>c.id===s.component));assert(view.truncated);
 const map=A.treemap(ix,'root','bytes');assert(map.regions.length<=A.LIMITS.regions);assert(map.truncated);assert.equal(A.search(ix,'f299')[0].id,'f299');
});

test('component layouts and dependency filters handle cycles deterministically',()=>{
 const data=fixture();data.edges.push({...data.edges[0],id:'reverse',source:'component-root',target:'component-src',type:'IMPORTS'});const ix=A.index(data),state=A.initial(),view=A.componentView(ix,state);
 assert.deepEqual([...A.componentPositions(view)],[...A.componentPositions(view)]);state.relationship='dependencies';assert.equal(A.componentView(ix,state).edges[0].type,'IMPORTS');state.relationship='calls';assert.equal(A.componentView(ix,state).edges[0].occurrences,2);
});

test('empty data and empty folders remain explicit',()=>{const ix=A.index(null);assert.equal(A.componentView(ix,A.initial()).components.length,0);assert.equal(A.search(ix,'x').length,0);assert.equal(A.treemap(ix,'unknown','bytes').regions.length,0);});

class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.attrs={};this.listeners={};this.style={};this.value='';this.hidden=false;this.clientWidth=900;this.clientHeight=560;this._text='';this.classList={toggle(){}};}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}set innerHTML(v){throw Error('unsafe HTML');}
 setAttribute(k,v){this.attrs[k]=String(v);}append(...items){this.children.push(...items);}replaceChildren(...items){this.children=items;this._text='';}remove(){}addEventListener(k,fn){this.listeners[k]=fn;}removeEventListener(k){delete this.listeners[k];}
 querySelector(selector){for(const child of this.children){if(selector.startsWith('.')&&(child.attrs.class||child.className||'').split(' ').includes(selector.slice(1)))return child;const found=child.querySelector(selector);if(found)return found;}return null;}
 getBoundingClientRect(){return {x:0,y:0,left:0,top:0,width:900,height:560};}scrollIntoView(){}
}
function controller(){const elements=new Map(),create=tag=>new Element(tag),document={getElementById:id=>{if(!elements.has(id))elements.set(id,create('div'));return elements.get(id);},createElement:create,createElementNS:(ns,tag)=>create(tag)};
 const frames=new Map();let id=0;const context={ArchaeologistArchitecture:A,ArchaeologistLayouts:L,document,Option:class extends Element{constructor(text,value){super('option');this.textContent=text;this.value=value;}},matchMedia:()=>({matches:true}),ResizeObserver:class{observe(){}disconnect(){}},IntersectionObserver:class{observe(){}disconnect(){}},requestAnimationFrame:fn=>{frames.set(++id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id),setTimeout,clearTimeout};
 vm.createContext(context);for(const script of ['scene.js','explorer.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../../app/static/architecture',script),'utf8'),context);
 return {context,explorer:context.architectureExplorer,elements,frames};}

test('real controller preserves context across views and metric changes without reanalysis',()=>{
 const h=controller(),x=h.explorer;x.visible=true;x.set(fixture(),{nodes:[],edges:[],references:[]});x.selectComponent('component-src');const scene=x.scene,key=x.key,item=x.items.get('component-src');x.selectComponent('component-root');assert.equal(x.items.get('component-src'),item);
 x.openDirectory('src');assert.equal(x.state.view,'heatmap');assert.equal(x.state.component,'component-src');const regions=x.items;
 x.state.metric='bytes';x.draw();assert.equal(x.scene,scene);assert.equal(x.items,regions);assert.equal(x.state.directory,'src');
 x.state.view='architecture';x.key=null;x.draw();assert.equal(x.state.component,'component-src');assert(h.elements.get('ai-inspector').textContent.includes('src'));assert(x.scene);
});

test('safe text, source evidence and repository replacement cleanup',()=>{
 const h=controller(),x=h.explorer,data=fixture();data.components[0].name='<img src=x onerror=alert(1)>';x.visible=true;x.set(data,{nodes:[],edges:[{id:'original',type:'CALLS',reference:'<script>',occurrences:2,evidence:[{path:'src/a.c',line:2,column:3}]}],references:[]});
 x.selectComponent('component-src');assert(h.elements.get('ai-inspector').textContent.includes('<img src=x onerror=alert(1)>'));x.inspectEdge('edge');assert(h.elements.get('ai-inspector').textContent.includes('src/a.c:2:3'));
 const svg=x.scene.svg;x.set(fixture(),null);assert.equal(Object.keys(svg.listeners).length,0);assert.equal(x.state.selected,null);assert.equal(x.state.directory,'root');
});
