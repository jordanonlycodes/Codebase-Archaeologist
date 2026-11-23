'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const D=require('../../app/static/graph/data.js'),U=require('../../app/static/graph/universe.js');
const node=(id,type,path)=>({id,type,name:id,path,metadata:{}}),edge=(id,source,target,type='CALLS')=>({id,source,target,type,status:'resolved_internal'});
const graph=()=>({nodes:[node('r','repository',''),node('src','directory','src'),node('lib','directory','lib'),node('a','file','src/a.c'),node('b','function','src/a.c'),node('c','file','lib/b.py'),node('py','function','lib/b.py'),node('root','file','README.md')],edges:[edge('rs','r','src','CONTAINS'),edge('rl','r','lib','CONTAINS'),edge('sa','src','a','CONTAINS'),edge('ab','a','b','DEFINES'),edge('lc','lib','c','CONTAINS'),edge('cp','c','py','DEFINES'),edge('bp','b','py')]});
const fixture=()=>{const g=graph(),ix=D.index(g);return{g,ix,view:D.subset(ix,D.initial())};};
test('constellations use actual directory ownership and root paths, never create entities',()=>{
 const {g,ix,view}=fixture(),result=U.constellation(view,ix);assert.equal(result.positions.size,g.nodes.length);assert.equal(result.groups.length,3);
 assert.equal(result.membership.get('a'),result.membership.get('b'));assert.equal(result.membership.get('c'),result.membership.get('py'));assert.notEqual(result.membership.get('b'),result.membership.get('py'));assert(!result.membership.has('r'));
 assert.equal(result.groups.find(g=>g.directoryId==='src').basis,'Retained directory ownership');assert(result.groups.some(g=>g.label==='Repository root'));assert.deepEqual(g,graph());
});
test('stable IDs produce identical coordinates under reordered input and repeated layouts',()=>{
 const {ix,view}=fixture(),first=U.constellation(view,ix),next=U.constellation({...view,nodes:[...view.nodes].reverse()},ix);
 for(const [id,p]of first.positions)assert.deepEqual(next.positions.get(id),p);assert.equal(new Set([...first.positions.values()].map(p=>JSON.stringify(p))).size,view.nodes.length);
});
test('empty, single, disconnected, missing-location and cyclic ownership remain finite',()=>{
 for(const g of [{nodes:[],edges:[]},{nodes:[node('one','function')],edges:[]},{nodes:[node('a','function'),node('b','function')],edges:[edge('ab','a','b','DEFINES'),edge('ba','b','a','DEFINES')]}]){const ix=D.index(g),view=D.subset(ix,D.initial()),result=U.constellation(view,ix);assert.equal(result.positions.size,view.nodes.length);assert([...result.positions.values()].every(U.finite));}
 const ix=D.index({nodes:[node('unknown','file')],edges:[]});assert.equal(U.grouping(D.subset(ix,D.initial()),ix).groups[0].label,'Location unavailable');
});
test('large bounded view retains distinct positions and all disconnected visible nodes',()=>{
 const g={nodes:Array.from({length:500},(_,i)=>node('fn'+i,'function','src/a.c')),edges:[]},ix=D.index(g),view=D.subset(ix,D.initial()),result=U.constellation(view,ix);assert.equal(result.positions.size,180);assert(view.truncated);assert([...result.positions.values()].every(U.finite));assert.equal(new Set([...result.positions.values()].map(p=>JSON.stringify(p))).size,180);
});
test('illumination distinguishes incoming, outgoing, bidirectional and filtered relationships',()=>{
 const view={nodes:['a','b','c','d'].map(id=>node(id,'function','a.c')),edges:[edge('ab','a','b'),edge('ba','b','a'),edge('ca','c','a')]};const light=U.illumination(view,'a');assert.equal(light.nodes.get('a'),'selected');assert.equal(light.nodes.get('b'),'both');assert.equal(light.nodes.get('c'),'incoming');assert.equal(light.nodes.get('d'),'dim');assert.equal(light.edges.get('ab'),'outgoing');assert.equal(light.edges.get('ca'),'incoming');
 const out=U.illumination(view,'a','out');assert.equal(out.nodes.get('c'),'dim');assert.equal(out.edges.get('ca'),'dim');const filtered=U.illumination({...view,edges:[edge('ab','a','b')]},'a');assert.equal(filtered.nodes.get('c'),'dim');assert([...U.illumination(view,null).nodes.values()].every(v=>v==='normal'));
});
test('framing handles zero-distance vectors, invalid nodes and narrow viewports',()=>{
 const nodes=[{x:100,y:0,z:0},{x:200,y:50,z:10},{x:NaN,y:0,z:0}],camera={x:0,y:0,z:0};const wide=U.framing(nodes,camera,camera,1000,600),narrow=U.framing(nodes,camera,camera,200,600);assert(U.finite(wide.position));assert.equal(wide.target.x,150);assert(narrow.position.z>wide.position.z);assert.equal(U.framing([],camera,camera,100,100),null);assert.equal(U.framing(nodes,camera,camera,0,100),null);
});
test('framing retains marker padding from oblique views and avoids excessive node closeups',()=>{
 const nodes=[{x:-60,y:-20,z:20},{x:80,y:40,z:-70}],camera={x:200,y:80,z:300},target={x:0,y:0,z:0};
 const overview=U.framing(nodes,camera,target,800,500),focus=U.framing(nodes,camera,target,800,500,{minRadius:90});assert(U.finite(focus.position));assert(Math.hypot(focus.position.x-focus.target.x,focus.position.y-focus.target.y,focus.position.z-focus.target.z)>=Math.hypot(overview.position.x-overview.target.x,overview.position.y-overview.target.y,overview.position.z-overview.target.z));
});
test('tour targets are deterministic real evidence with explicit visible-membership prominence',()=>{
 const {ix,view}=fixture(),scenes=U.scenes(view,ix);assert.deepEqual(scenes.map(s=>s.kind),['overview','cluster','relationships','entity','return']);assert(scenes.every(s=>!s.id||ix.nodes.has(s.id)));assert.match(scenes[1].description,/visible directory grouping/);assert.deepEqual(U.scenes({...view,nodes:[...view.nodes].reverse()},ix),scenes);assert.deepEqual(U.scenes({nodes:[],edges:[]},ix),[]);
 const single={nodes:[node('one','repository','')],edges:[]};assert.equal(U.scenes(single,D.index(single)).length,1);
});
function harness(reduced=false){let id=0;const timers=new Map(),events=new Map(),mediaEvents=new Set(),shown=[],statuses=[];const listen=(k,f)=>{if(!events.has(k))events.set(k,new Set());events.get(k).add(f);},remove=(k,f)=>events.get(k)?.delete(f);const media={matches:reduced,addEventListener:(_,f)=>mediaEvents.add(f),removeEventListener:(_,f)=>mediaEvents.delete(f)},doc={hidden:false,addEventListener:listen,removeEventListener:remove};let cancels=0;
 const env={document:doc,matchMedia:()=>media,addEventListener:listen,removeEventListener:remove,setTimeout:f=>{timers.set(++id,f);return id;},clearTimeout:id=>timers.delete(id)};const tour=new U.Tour({env,onScene:s=>shown.push(s),onStatus:s=>statuses.push(s),onCancel:()=>cancels++});return{tour,timers,shown,statuses,media,mediaEvents,events,doc,cancels:()=>cancels,emit(k){for(const f of [...events.get(k)||[]])f();}};
}
const scenes=[{kind:'overview'},{kind:'entity',id:'real'},{kind:'return'}];
test('tour start, pause, resume, skip and exit own at most one finite timer',()=>{
 const h=harness();assert(h.tour.start(scenes));assert.equal(h.timers.size,1);h.tour.pause();assert.equal(h.timers.size,0);assert.equal(h.tour.status,'paused');h.tour.resume();assert.equal(h.timers.size,1);h.tour.next();assert.equal(h.tour.index,1);h.tour.next();h.tour.next();assert.equal(h.tour.status,'idle');assert.equal(h.timers.size,0);assert.equal(h.mediaEvents.size,0);assert([...h.events.values()].every(v=>v.size===0));
});
test('stale tour callbacks cannot act after pause, replacement, exit or destruction',()=>{
 const h=harness();h.tour.start(scenes);const stale=[...h.timers.values()][0];h.tour.pause();stale();assert.equal(h.tour.index,0);h.tour.start(scenes.slice(0,1));stale();assert.equal(h.tour.index,0);h.tour.destroy();stale();assert.equal(h.tour.status,'idle');assert.equal(h.timers.size,0);assert.equal(h.mediaEvents.size,0);
});
test('reduced-motion tours use manual scene advance and live preference pauses work',()=>{
 const h=harness(true);h.tour.start(scenes);assert.equal(h.tour.status,'paused');assert.equal(h.timers.size,0);h.tour.next();assert.equal(h.tour.index,1);h.tour.resume();assert.equal(h.timers.size,0);h.tour.stop();h.media.matches=false;h.tour.start(scenes);h.media.matches=true;h.mediaEvents.forEach(f=>f());assert.equal(h.tour.status,'paused');assert.equal(h.timers.size,0);h.tour.destroy();
});
test('hidden documents pause tours; pagehide and empty tours release all work',()=>{
 const h=harness();assert(!h.tour.start([]));h.tour.start(scenes);h.doc.hidden=true;h.emit('visibilitychange');assert.equal(h.tour.status,'paused');h.emit('pagehide');assert.equal(h.tour.status,'idle');assert.equal(h.timers.size,0);assert.equal(h.mediaEvents.size,0);
});
test('3D camera rejects invalid coordinates and cannot update after destruction',()=>{
 const queue=new Map();let id=0,last=null;const context={document:{},performance:{now:()=>0},requestAnimationFrame:fn=>{queue.set(++id,fn);return id;},cancelAnimationFrame:id=>queue.delete(id),matchMedia:()=>({matches:false})};vm.createContext(context);vm.runInContext(fs.readFileSync('app/static/graph/three.js','utf8'),context);const a=Object.create(context.ArchaeologistThree.Adapter.prototype);a.graph={camera:()=>({position:{x:0,y:0,z:10}}),controls:()=>({target:{x:0,y:0,z:0}}),cameraPosition:p=>{last=p;}};
 assert.equal(a.cameraMove({x:NaN,y:0,z:0},{x:0,y:0,z:0},500),false);assert.equal(queue.size,0);a.visible=false;a.cameraMove({x:4,y:5,z:6},{x:0,y:0,z:0},500);assert.equal(last.x,4);assert.equal(queue.size,0);a.visible=true;last=null;a.cameraMove({x:10,y:20,z:30},{x:0,y:0,z:0},500);const cb=[...queue.values()][0];a.destroyed=true;cb(500);assert.equal(last,null);assert.equal(a.cameraMove({x:1,y:2,z:3},{x:0,y:0,z:0},500),false);
});
