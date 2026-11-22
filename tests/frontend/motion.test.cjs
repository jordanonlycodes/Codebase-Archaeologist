'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {Motion,TIMING,MAX_ACTIVE,MAX_BATCH}=require('../../app/static/product/motion.js');
class Element{
 constructor(){this.children=[];this.attrs={};this.calls=[];this.value='';this.isConnected=true;}
 set textContent(v){this.value=String(v);this.children=[];}get textContent(){return this.value+this.children.map(c=>c.textContent).join('');}
 setAttribute(k,v){this.attrs[k]=v;}contains(el){return this===el||this.children.includes(el);}
 replaceChildren(...children){this.value='';this.children=children;}
 animate(frames,options){const a={frames,options,cancelled:false,cancel(){this.cancelled=true;this.oncancel?.();}};this.calls.push(a);return a;}
 getTotalLength(){return 100;}
}
function harness(storage=new Map()){
 const listeners=new Map(),mediaListeners=new Set(),frames=new Map(),observers=[];let id=0,now=0;
 const media={matches:false,addEventListener(_,f){mediaListeners.add(f);},removeEventListener(_,f){mediaListeners.delete(f);}};
 const classes=new Set(),doc={hidden:false,activeElement:null,documentElement:{classList:{toggle(k,v){v?classes.add(k):classes.delete(k);},remove:k=>classes.delete(k)}},createElement:()=>new Element(),addEventListener(k,f){listeners.set(k,f);},removeEventListener(k){listeners.delete(k);}};
 const env={document:doc,matchMedia:()=>media,sessionStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},performance:{now:()=>now},requestAnimationFrame:f=>{frames.set(++id,f);return id;},cancelAnimationFrame:i=>frames.delete(i),IntersectionObserver:class{constructor(cb){this.cb=cb;this.targets=new Set();observers.push(this);}observe(el){this.targets.add(el);}unobserve(el){this.targets.delete(el);}disconnect(){this.targets.clear();}}};
 const motion=new Motion(env);motion.begin('snapshot-a','overview',Date.now()+10000);
 return {motion,env,doc,media,frames,classes,observers,listeners,mediaListeners,storage,advance(time){now=time;const callbacks=[...frames.values()];frames.clear();callbacks.forEach(f=>f(time));},reduce(){media.matches=true;mediaListeners.forEach(f=>f());},hide(){doc.hidden=true;listeners.get('visibilitychange')();}};
}
test('finite animations release slots and never alter final text or block interaction',()=>{
 const h=harness(),el=new Element();el.textContent='Verified evidence';assert(h.motion.reveal(el,{key:'panel'}));
 const a=el.calls[0];assert.equal(a.options.duration,TIMING.normal);assert.equal(a.options.fill,'backwards');assert.equal(el.textContent,'Verified evidence');a.onfinish();assert.equal(h.motion.animations.size,0);assert.equal(h.motion.reveal(el,{key:'panel'}),false);
});
test('same-element updates cancel previous animation; initialization cleans listeners',()=>{
 const h=harness(),el=new Element();h.motion.reveal(el);h.motion.reveal(el);assert(el.calls[0].cancelled);assert.equal(h.motion.animations.size,1);
 h.motion.begin('new-snapshot','graph',Date.now()+10000);assert(el.calls[1].cancelled);assert.equal(h.listeners.size,1);assert.equal(h.mediaListeners.size,1);h.motion.destroy();h.motion.destroy();assert.equal(h.listeners.size,0);assert.equal(h.mediaListeners.size,0);
});
test('metric animation exposes exact final accessible value and finishes with original formatting',()=>{
 const h=harness(),el=new Element();el.textContent='1,234';h.motion.count(el,1234,{key:'files',format:n=>n.toLocaleString('en-US')});
 assert.equal(el.children[0].textContent,'1,234');assert.equal(el.children[1].attrs['aria-hidden'],'true');h.advance(100);assert.notEqual(el.children[1].textContent,'1,234');h.advance(TIMING.slow);
 assert.equal(el.textContent,'1,234');assert.equal(h.frames.size,0);assert.equal(h.motion.counters.size,0);
});
test('reduced motion before start bypasses all animations and counters',()=>{
 const h=harness(),el=new Element();el.textContent='12';h.reduce();h.motion.reveal(el);h.motion.count(el,12);h.motion.trace([el]);h.motion.watch([el],{key:'cards'});assert.equal(el.calls.length,0);assert.equal(el.textContent,'12');assert.equal(h.frames.size,0);assert.equal(h.observers.length,0);
});
test('live preference change and hidden document cancel work with final counters',()=>{
 for(const action of ['reduce','hide']){const h=harness(),el=new Element(),card=new Element();h.motion.count(el,99);h.motion.reveal(card);h.motion.watch([card],{key:'card'});h[action]();assert.equal(el.textContent,'99');assert.equal(h.frames.size,0);assert.equal(h.motion.animations.size,0);assert.equal(h.observers[0].targets.size,0);assert.equal(h.motion.pending.size,0);if(action==='hide')assert(h.classes.has('motion-document-hidden'));h.motion.destroy();assert.equal(h.classes.size,0);}
});
test('counts ignore missing, negative, fractional values and never overwrite replaced data',()=>{
 const h=harness(),el=new Element();el.textContent='Unavailable';for(const v of [null,undefined,NaN,-1,.5,'7'])h.motion.count(el,v);assert.equal(el.textContent,'Unavailable');assert.equal(h.frames.size,0);
 h.motion.count(el,9);el.textContent='New repository';h.advance(300);assert.equal(el.textContent,'New repository');assert.equal(h.frames.size,0);h.motion.count(el,0);h.motion.destroy();assert.equal(el.textContent,'0');
});
test('bounded batches, active slots and path traces restore original style',()=>{
 const h=harness(),nodes=Array.from({length:100},()=>new Element());h.motion.batch(nodes,{key:'batch'});assert.equal(nodes.filter(n=>n.calls.length).length,MAX_BATCH);
 for(const el of nodes)h.motion.reveal(el);assert.equal(h.motion.animations.size,MAX_ACTIVE);h.motion.stop();assert.equal(h.motion.animations.size,0);
 h.motion.trace(nodes,{key:'edges'});assert.equal(h.motion.animations.size,MAX_BATCH);assert.equal(nodes[0].calls.at(-1).frames[0].strokeDashoffset,100);assert.equal(nodes[0].calls.at(-1).options.fill,'backwards');
});
test('one-shot visibility observation leaves content accessible before intersection',()=>{
 const h=harness(),el=new Element();el.textContent='Already available';h.motion.watch([el],{key:'cards'});assert.equal(el.textContent,'Already available');assert.equal(el.calls.length,0);const ob=h.observers[0];ob.cb([{target:el,isIntersecting:true}]);assert.equal(el.calls.length,1);assert.equal(ob.targets.size,0);ob.cb([{target:el,isIntersecting:true}]);assert.equal(el.calls.length,1);
});
test('same-tab seen scope persists, repository changes isolate and cache is bounded',()=>{
 const store=new Map(),h=harness(store),el=new Element();h.motion.reveal(el,{key:'entry'});h.motion.destroy();const next=harness(store);assert.equal(next.motion.reveal(new Element(),{key:'entry'}),false);next.motion.begin('snapshot-b','overview',Date.now()+10000);assert(next.motion.reveal(new Element(),{key:'entry'}));for(let i=0;i<200;i++)next.motion.claim('key'+i);assert(next.motion.seen.length<=80);assert([...store.values()][0].length<40000);
});
test('unsupported Web Animations, blocked storage and focused content degrade immediately',()=>{
 const h=harness(),el=new Element();el.animate=undefined;el.textContent='24';h.motion.count(el,24);assert.equal(el.textContent,'24');h.env.sessionStorage.setItem=()=>{throw Error('blocked');};assert.doesNotThrow(()=>h.motion.claim('new'));const focused=new Element();h.doc.activeElement=focused;assert.equal(h.motion.reveal(focused),false);
});
test('busy status follows genuine state and remains usable without animation support',()=>{
 const h=harness(),el=new Element();h.motion.busy(el,true);assert.equal(el.attrs['aria-busy'],'true');assert.equal(el.attrs['data-pending'],'true');h.motion.busy(el,false);assert.equal(el.attrs['aria-busy'],'false');assert.equal(el.attrs['data-pending'],'false');
});
test('fades and traces preserve dimmed relationship emphasis',()=>{
 const h=harness(),el=new Element();h.env.getComputedStyle=()=>({opacity:'.2'});h.motion.reveal(el,{kind:'fade'});assert.equal(el.calls[0].frames[1].opacity,.2);h.motion.trace([el]);assert.equal(el.calls[1].frames[1].opacity,.2);
});
test('removed view effects are pruned and detached computed styles do not hide new content',()=>{
 const h=harness(),old=new Element(),next=new Element();h.motion.reveal(old);old.isConnected=false;h.env.getComputedStyle=()=>({opacity:''});h.motion.reveal(next,{kind:'fade'});assert(old.calls[0].cancelled);assert.equal(h.motion.animations.size,1);assert.equal(next.calls[0].frames[1].opacity,1);
});
test('narrow viewports use shorter travel and bounded stagger',()=>{
 const h=harness(),el=new Element();h.env.matchMedia=query=>query.includes('650px')?{matches:true}:h.media;h.motion.reveal(el);assert.equal(el.calls[0].frames[0].transform,'translateY(3px)');const nodes=[new Element(),new Element()];h.motion.batch(nodes);assert.equal(nodes[1].calls[0].options.delay,25);
});
