'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {Boot,Statistics,BOOT_KEY,STATS_KEY}=require('../../app/static/product/cinematic.js');
class Element{
 constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.attrs={};this.dataset={};this.isConnected=true;this.listeners=new Map();this.value='';}
 set textContent(v){this.value=String(v);this.children=[];}get textContent(){return this.value+this.children.map(c=>c.textContent).join('');}
 append(...c){this.children.push(...c);for(const e of c)e.parent=this;}replaceChildren(...c){this.value='';this.children=[];this.append(...c);}
 setAttribute(k,v){this.attrs[k]=v;}hasAttribute(k){return k in this.attrs;}removeAttribute(k){delete this.attrs[k];}
 addEventListener(k,f){this.listeners.set(k,f);}contains(el){return this===el||this.children.some(c=>c.contains(el));}
 remove(){this.parent.children=this.parent.children.filter(c=>c!==this);this.isConnected=false;}focus(){this.focused=true;}
}
function harness(store=new Map()){
 const listeners=new Map(),mediaListeners=new Set(),frames=new Map(),timers=new Map();let seq=0,time=0;
 const listen=(k,f)=>{if(!listeners.has(k))listeners.set(k,new Set());listeners.get(k).add(f);},unlisten=(k,f)=>listeners.get(k)?.delete(f);
 const media={matches:false,addEventListener:(_,f)=>mediaListeners.add(f),removeEventListener:(_,f)=>mediaListeners.delete(f)};
 const main=new Element('main'),body=new Element('body');body.append(main);
 const doc={body,activeElement:body,hidden:false,createElement:t=>new Element(t),querySelector:()=>main,addEventListener:listen,removeEventListener:unlisten};
 const env={document:doc,matchMedia:()=>media,performance:{now:()=>time},sessionStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},addEventListener:listen,removeEventListener:unlisten,setTimeout:(f,ms)=>{timers.set(++seq,{f,at:time+ms});return seq;},clearTimeout:id=>timers.delete(id),requestAnimationFrame:f=>{frames.set(++seq,f);return seq;},cancelAnimationFrame:id=>frames.delete(id)};
 return{env,doc,main,media,store,timers,frames,listeners,mediaListeners,emit(k,e={}){for(const f of listeners.get(k)||[])f(e);},advance(t){time=t;for(const [id,v]of [...timers])if(v.at<=t){timers.delete(id);v.f();}const callbacks=[...frames.values()];frames.clear();callbacks.forEach(f=>f(t));},reduce(){media.matches=true;mediaListeners.forEach(f=>f());}};
}
test('intro phases finish at3600ms and only play once per tab session',()=>{
 const h=harness(),b=new Boot(h.env);b.initialize();assert(b.overlay);assert.equal(h.store.get(BOOT_KEY),'played');assert.equal(b.overlay.dataset.phase,'dark');h.advance(500);assert.equal(b.overlay.dataset.phase,'relic');h.advance(1400);assert.equal(b.overlay.dataset.phase,'intelligence');h.advance(2400);assert.equal(b.overlay.dataset.phase,'reveal');h.advance(3600);assert.equal(b.overlay,null);assert.equal(h.timers.size,0);assert(h.main.focused);
 b.destroy();const next=new Boot(h.env);next.initialize();assert.equal(next.overlay,null);next.destroy();
});
test('skip, replay, duplicate initialization and restored trigger focus',()=>{
 const h=harness(),b=new Boot(h.env);b.initialize();b.initialize();assert.equal(h.doc.body.children.length,2);b.overlay.children.at(-1).listeners.get('click')();assert.equal(b.overlay,null);const trigger=new Element('button');h.doc.activeElement=trigger;assert(b.play(true));assert.equal(b.play(true),false);b.finish();assert(trigger.focused);assert.equal(h.timers.size,0);b.destroy();
});
test('keyboard exit avoids background focus traps and pagehide removes all timers',()=>{
 const h=harness(),b=new Boot(h.env);b.initialize();let prevented=false;h.emit('keydown',{key:'Tab',preventDefault(){prevented=true;}});assert(prevented);assert(!b.overlay);b.play(true);h.emit('keydown',{key:'Escape'});assert(!b.overlay);b.play(true);h.emit('pagehide');assert(!b.overlay);assert.equal(h.timers.size,0);b.destroy();assert([...h.listeners.values()].every(s=>s.size===0));assert.equal(h.mediaListeners.size,0);
});
test('reduced motion and hidden documents bypass playback and stop current work',()=>{
 const h=harness(),b=new Boot(h.env);h.reduce();b.initialize();assert(!b.overlay);assert(!b.play(true));h.media.matches=false;b.play(true);h.reduce();assert(!b.overlay);h.media.matches=false;h.doc.hidden=true;assert(!b.play(true));b.destroy();
});
test('storage denial and construction failure leave normal content usable',()=>{
 const h=harness();h.env.sessionStorage={getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}};const b=new Boot(h.env);b.initialize();assert(!b.overlay);assert(b.play(true));b.finish();assert(!b.play());h.doc.createElement=()=>{throw Error('unavailable');};assert.equal(b.play(true),false);assert.equal(h.doc.body.children.length,1);assert.equal(h.timers.size,0);b.destroy();
});
test('bounded recovery timeout works independently of normal phase completion',()=>{
 const h=harness(),b=new Boot(h.env);b.initialize();for(const [id,t]of h.timers)if(t.at!==4600)h.timers.delete(id);h.advance(4600);assert(!b.overlay);assert.equal(h.timers.size,0);b.destroy();
});
test('integer animation has exact accessible final value and no live announcements',()=>{
 const h=harness(),s=new Statistics(h.env),el=new Element();s.set(el,1234,{key:'files'});assert.equal(el.children[0].textContent,'1,234');assert.equal(el.children[1].attrs['aria-hidden'],'true');assert(!el.hasAttribute('aria-live'));h.advance(300);assert.notEqual(el.children[1].textContent,'1,234');h.advance(760);assert.equal(el.textContent,'1,234');assert.equal(h.frames.size,0);s.destroy();
});
test('decimal percentages retain precision and stale updates start from displayed value',()=>{
 const h=harness(),s=new Statistics(h.env),el=new Element();s.set(el,31.25,{key:'share',precision:2,suffix:'%'});h.advance(300);const before=el.children[1].textContent;s.set(el,42.75,{key:'share',precision:2,suffix:'%'});assert.equal(h.frames.size,1);assert.equal(el.children[1].textContent,before);h.advance(1060);assert.equal(el.textContent,'42.75%');assert.equal(h.frames.size,0);s.destroy();
});
test('zero, null, invalid, signed and large numeric values preserve meaning',()=>{
 const h=harness(),s=new Statistics(h.env),el=new Element();s.set(el,0);assert.equal(el.textContent,'0');assert.equal(h.frames.size,0);for(const n of [null,undefined,NaN,Infinity,'12']){s.set(el,n);assert.equal(el.textContent,'—');assert.equal(h.frames.size,0);}s.set(el,-2.5,{precision:1});h.advance(760);assert.equal(el.textContent,'-2.5');s.set(el,Number.MAX_SAFE_INTEGER);h.advance(1520);assert.equal(el.textContent,'9,007,199,254,740,991');s.destroy();
});
test('same snapshot return stays final, changed repository updates and storage is bounded',()=>{
 const h=harness(),s=new Statistics(h.env),el=new Element();s.set(el,12,{key:'files',scope:'a'});h.advance(760);s.destroy();const next=new Statistics(h.env),other=new Element();next.set(other,12,{key:'files',scope:'a'});assert.equal(h.frames.size,0);next.set(other,20,{key:'files',scope:'b'});assert.equal(h.frames.size,1);next.stop();h.media.matches=true;for(let i=0;i<200;i++)next.set(other,i,{key:'count'+i});assert.equal(JSON.parse(h.store.get(STATS_KEY)).length,128);next.destroy();
});
test('hidden/reduced/detached/replaced values cancel frames without overwriting new data',()=>{
 for(const action of ['hidden','reduce','detach','replace']){const h=harness(),s=new Statistics(h.env),el=new Element();s.set(el,99,{key:'files'});if(action==='hidden'){h.doc.hidden=true;h.emit('visibilitychange');}if(action==='reduce')h.reduce();if(action==='detach'){el.isConnected=false;h.advance(100);}if(action==='replace'){el.textContent='New snapshot';h.advance(100);}assert.equal(el.textContent,action==='replace'?'New snapshot':'99');assert.equal(h.frames.size,0);s.destroy();assert.equal(h.mediaListeners.size,0);assert([...h.listeners.values()].every(s=>s.size===0));}
});
test('reduced motion, invalid storage and missing RAF degrade to final values',()=>{
 const h=harness();h.store.set(STATS_KEY,'invalid JSON');h.env.requestAnimationFrame=null;h.env.sessionStorage.setItem=()=>{throw Error('blocked');};const s=new Statistics(h.env),el=new Element();s.set(el,2.75,{precision:2});assert.equal(el.textContent,'2.75');h.reduce();s.set(el,7);assert.equal(el.textContent,'7');s.destroy();
});
test('concurrent statistics are bounded and interface reveal cancels on preference change',()=>{
 const h=harness(),s=new Statistics(h.env);for(let i=0;i<50;i++)s.set(new Element(),i+1,{key:'metric'+i});assert.equal(s.active.size,16);assert.equal(h.frames.size,16);s.destroy();assert.equal(h.frames.size,0);
 let cancelled=false;h.main.animate=()=>({cancel(){cancelled=true;}});const b=new Boot(h.env);b.initialize();h.advance(2400);h.reduce();assert(cancelled);assert(!b.overlay);b.destroy();
});
