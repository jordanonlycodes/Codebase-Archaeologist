/* Finite, progressive-enhancement motion. Evidence and interaction never wait for it. */
(function(root){
 'use strict';
 const TIMING={fast:160,normal:340,slow:560,stagger:45,ease:'cubic-bezier(0.22, 1, 0.36, 1)'};
 const STORAGE='archaeologist.motion.v1',MAX_SEEN=80,MAX_ACTIVE=24,MAX_BATCH=12;
 class Motion{
  constructor(env=root){this.env=env;this.doc=env.document;this.media=env.matchMedia('(prefers-reduced-motion: reduce)');this.active=false;this.animations=new Map();this.counters=new Map();this.pending=new Map();this.seen=[];this.clean=[];}
  begin(snapshot,page,expires){
   this.destroy();this.active=true;this.scope=String(snapshot)+':'+page;this.expires=expires;this.seen=[];
   try{const rows=JSON.parse(this.env.sessionStorage?.getItem(STORAGE)||'[]');if(Array.isArray(rows))this.seen=rows.filter(r=>typeof r?.key==='string'&&r.key.length<=400&&Number.isFinite(r.expires)&&r.expires>Date.now()).slice(-MAX_SEEN);}catch{/* Optional visual preference; data restoration is independent. */}
   const stop=()=>this.stop();const visible=()=>{this.doc.documentElement?.classList.toggle('motion-document-hidden',this.doc.hidden);if(this.doc.hidden)this.stop();};visible();
   this.media.addEventListener?.('change',stop);this.doc.addEventListener('visibilitychange',visible);
   this.clean.push(()=>this.media.removeEventListener?.('change',stop),()=>this.doc.removeEventListener('visibilitychange',visible));
  }
  enabled(el){return this.active&&!this.doc.hidden&&!this.media.matches&&!!el&&typeof el.animate==='function'&&!el.contains?.(this.doc.activeElement);}
  claim(key){
   if(!key)return true;const scoped=(this.scope+':'+key).slice(0,400);
   if(this.seen.some(r=>r.key===scoped))return false;
   this.seen.push({key:scoped,expires:Math.min(this.expires||Date.now()+7200000,Date.now()+7200000)});this.seen=this.seen.slice(-MAX_SEEN);
   try{this.env.sessionStorage?.setItem(STORAGE,JSON.stringify(this.seen));}catch{/* Blocked storage does not block the workspace. */}return true;
  }
  play(el,frames,{duration=TIMING.normal,delay=0}={}){
   if(!this.enabled(el))return false;
   this.cancel(el);for(const node of [...this.animations.keys()])if(node.isConnected===false)this.cancel(node);if(this.animations.size>=MAX_ACTIVE)return false;
   try{const animation=el.animate(frames,{duration,delay:Math.min(220,delay),easing:TIMING.ease,fill:'none'});
    this.animations.set(el,animation);const finish=()=>{if(this.animations.get(el)===animation)this.animations.delete(el);};animation.onfinish=finish;animation.oncancel=finish;return true;
   }catch{return false;}
  }
  opacity(el){const value=Number.parseFloat(this.env.getComputedStyle?.(el)?.opacity??'1');return Number.isFinite(value)?value:1;}
  reveal(el,{key,kind='rise',duration=TIMING.normal,delay=0}={}){
   if(!this.enabled(el)||!this.claim(key))return false;
   const distance=this.env.matchMedia('(max-width: 650px)').matches?3:6,opacity=this.opacity(el),frames=kind==='fade'?[{opacity:opacity*.35},{opacity}]:[{opacity:opacity*.45,transform:`translateY(${distance}px)`},{opacity,transform:'translateY(0)'}];
   return this.play(el,frames,{duration,delay});
  }
  batch(elements,{key,kind='fade',duration=TIMING.slow}={}){
   const nodes=Array.from(elements).slice(0,MAX_BATCH);
   if(!nodes.some(n=>this.enabled(n))||!this.claim(key))return;
   nodes.forEach((el,i)=>this.reveal(el,{kind,duration,delay:i*(this.env.matchMedia('(max-width: 650px)').matches?25:TIMING.stagger)}));
  }
  watch(elements,{key}={}){
   const nodes=Array.from(elements).slice(0,MAX_BATCH);if(!nodes.some(n=>this.enabled(n)))return;
   if(!this.env.IntersectionObserver){this.batch(nodes,{key,kind:'rise',duration:TIMING.normal});return;}
   if(!this.observer)this.observer=new this.env.IntersectionObserver(entries=>{
    for(const e of entries)if(e.isIntersecting){const options=this.pending.get(e.target);this.pending.delete(e.target);this.observer.unobserve(e.target);if(options)this.reveal(e.target,options);}
   },{threshold:.08});
   nodes.forEach((el,i)=>{this.pending.set(el,{key:key+':'+i,delay:Math.min(180,i*(this.env.matchMedia('(max-width: 650px)').matches?25:TIMING.stagger))});this.observer.observe(el);});
  }
  trace(elements,{key}={}){
   const paths=Array.from(elements).slice(0,MAX_BATCH);if(!paths.some(p=>this.enabled(p))||!this.claim(key))return;
   paths.forEach((path,i)=>{try{const length=path.getTotalLength();if(!Number.isFinite(length)||length<=0||length>100000)return;
    const opacity=this.opacity(path);this.play(path,[{strokeDasharray:`${length} ${length}`,strokeDashoffset:length,opacity:opacity*.35},{strokeDasharray:`${length} ${length}`,strokeDashoffset:0,opacity}],{duration:TIMING.slow,delay:i*30});
   }catch{/* A missing path metric simply leaves the original relationship visible. */}});
  }
  count(el,value,{key,format=String}={}){
   if(!this.enabled(el)||!Number.isSafeInteger(value)||value<0||!this.claim(key))return;
   this.finishCounter(el);if(this.counters.size>=4)return;
   const final=format(value),spoken=this.doc.createElement('span'),visual=this.doc.createElement('span');
   spoken.className='sr-only';spoken.textContent=final;visual.setAttribute('aria-hidden','true');visual.textContent=final;el.replaceChildren(spoken,visual);
   const now=()=>this.env.performance?.now?.()??Date.now(),counter={final,visual,frame:null,start:now()};this.counters.set(el,counter);
   const tick=time=>{if(this.counters.get(el)!==counter)return;if(!this.active||this.media.matches||this.doc.hidden||el.isConnected===false||!el.contains(visual)){this.finishCounter(el);return;}
    const progress=Math.max(0,Math.min(1,(time-counter.start)/TIMING.slow));visual.textContent=format(Math.round(value*(1-(1-progress)**3)));
    if(progress===1)this.finishCounter(el);else counter.frame=this.env.requestAnimationFrame(tick);
   };counter.frame=this.env.requestAnimationFrame(tick);
  }
  finishCounter(el){const counter=this.counters.get(el);if(!counter)return;this.env.cancelAnimationFrame(counter.frame);if(el.contains(counter.visual))el.textContent=counter.final;this.counters.delete(el);}
  cancel(el){const animation=this.animations.get(el);if(animation){this.animations.delete(el);animation.onfinish=null;animation.oncancel=null;animation.cancel();}}
  busy(el,pending){if(!el)return;el.setAttribute('aria-busy',String(!!pending));el.setAttribute('data-pending',String(!!pending));}
  stop(){for(const el of [...this.animations.keys()])this.cancel(el);for(const el of [...this.counters.keys()])this.finishCounter(el);this.observer?.disconnect();this.observer=null;this.pending.clear();}
  destroy(){this.stop();this.clean.forEach(fn=>fn());this.clean=[];this.doc.documentElement?.classList.remove('motion-document-hidden');this.active=false;}
 }
 if(root.document)root.WorkspaceMotion=new Motion(root);
 if(typeof module!=='undefined'&&module.exports)module.exports={Motion,TIMING,MAX_ACTIVE,MAX_BATCH};
})(globalThis);
