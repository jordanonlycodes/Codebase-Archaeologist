/* Optional presentation only. Repository loading never depends on this module. */
(function(root){
 'use strict';
 const BOOT_KEY='archaeologist.intro.v1',STATS_KEY='archaeologist.statistics.v1';
 const numeric=value=>typeof value==='number'&&Number.isFinite(value)&&Math.abs(value)<=Number.MAX_SAFE_INTEGER;
 class Boot{
  constructor(env=root){this.env=env;this.doc=env.document;this.media=env.matchMedia('(prefers-reduced-motion: reduce)');this.timers=new Set();this.played=false;this.overlay=null;this.clean=[];}
  initialize(){
   if(this.initialized)return;this.initialized=true;
   const click=e=>{if(e.target.closest?.('[data-replay-intro]'))this.play(true);};
   const key=e=>{if(this.overlay&&['Escape','Tab'].includes(e.key)){if(e.key==='Tab')e.preventDefault();this.finish();}};
   const reduced=()=>{if(this.media.matches)this.finish();};
   const hidden=()=>{if(this.doc.hidden)this.finish(false);};
   const leave=()=>this.finish(false);
   this.doc.addEventListener('click',click);this.doc.addEventListener('keydown',key,true);this.doc.addEventListener('visibilitychange',hidden);
   this.media.addEventListener?.('change',reduced);this.env.addEventListener('pagehide',leave);
   this.clean.push(()=>this.doc.removeEventListener('click',click),()=>this.doc.removeEventListener('keydown',key,true),()=>this.doc.removeEventListener('visibilitychange',hidden),()=>this.media.removeEventListener?.('change',reduced),()=>this.env.removeEventListener('pagehide',leave));
   this.play();
  }
  later(fn,ms){const id=this.env.setTimeout(()=>{this.timers.delete(id);try{fn();}catch{this.finish();}},ms);this.timers.add(id);}
  play(replay=false){
   if(this.overlay)return false;
   let seen=this.played,storage;
   try{storage=this.env.sessionStorage;if(!storage)throw Error('No session storage');seen=seen||storage.getItem(BOOT_KEY)==='played';}catch{if(!replay)return false;}
   if(!replay&&seen)return false;
   this.played=true;try{storage?.setItem(BOOT_KEY,'played');}catch{if(!replay)return false;}
   if(this.media.matches||this.doc.hidden)return false;
   this.returnFocus=this.doc.activeElement;
   try{
    const el=this.doc.createElement('section');this.overlay=el;el.className='cinematic-boot';el.dataset.phase='dark';el.setAttribute('role','dialog');el.setAttribute('aria-modal','false');el.setAttribute('aria-label','Codebase Archaeologist introduction');
    const light=this.doc.createElement('div');light.className='boot-light';light.setAttribute('aria-hidden','true');
    const scan=this.doc.createElement('div');scan.className='boot-scan';scan.setAttribute('aria-hidden','true');
    const center=this.doc.createElement('div');center.className='boot-center';
    const logo=this.doc.createElement('img');logo.src='/static/brand/relic-dark.svg';logo.width=100;logo.height=114;logo.alt='';logo.className='boot-relic';
    const name=this.doc.createElement('p');name.className='boot-name';name.textContent='CODEBASE ARCHAEOLOGIST';
    const subtitle=this.doc.createElement('p');subtitle.className='boot-subtitle';subtitle.textContent='EVERY REPOSITORY HAS A STORY.';
    const note=this.doc.createElement('p');note.className='boot-note';note.textContent='REPOSITORY INTELLIGENCE';
    const skip=this.doc.createElement('button');skip.type='button';skip.className='boot-skip';skip.textContent='Skip Intro';skip.addEventListener('click',()=>this.finish());
    center.append(logo,name,subtitle,note);el.append(light,scan,center,skip);this.doc.body.append(el);skip.focus({preventScroll:true});
    // Arm recovery first; all timers are cleared on every exit path.
    this.later(()=>this.finish(),4600);
    for(const [ms,phase]of [[500,'relic'],[1400,'intelligence'],[2400,'reveal']])this.later(()=>{
     el.dataset.phase=phase;
     if(phase==='reveal')this.revealAnimation=this.doc.querySelector('main')?.animate?.([{opacity:.8,transform:'translateY(4px)'},{opacity:1,transform:'none'}],{duration:640,easing:'cubic-bezier(.22,1,.36,1)'});
    },ms);
    this.later(()=>this.finish(),3600);return true;
   }catch{this.finish();return false;}
  }
  finish(restore=true){
   for(const id of this.timers)this.env.clearTimeout(id);this.timers.clear();
   this.revealAnimation?.cancel();this.revealAnimation=null;
   const el=this.overlay;if(!el)return;this.overlay=null;el.remove();
   if(restore){const prior=this.returnFocus;let target=prior?.isConnected&&prior!==this.doc.body?prior:this.doc.querySelector('main');
    if(target){const temporary=!target.hasAttribute('tabindex')&&target.tagName==='MAIN';if(temporary)target.setAttribute('tabindex','-1');target.focus({preventScroll:true});if(temporary)target.removeAttribute('tabindex');}}
   this.returnFocus=null;
  }
  destroy(){this.finish(false);this.clean.forEach(fn=>fn());this.clean=[];this.initialized=false;}
 }
 class Statistics{
  constructor(env=root){this.env=env;this.doc=env.document;this.media=env.matchMedia('(prefers-reduced-motion: reduce)');this.active=new Map();this.values=new WeakMap();this.records=[];
   try{const rows=JSON.parse(env.sessionStorage?.getItem(STATS_KEY)||'[]');if(Array.isArray(rows))this.records=rows.filter(r=>typeof r.key==='string'&&r.key.length<=300&&numeric(r.value)&&Number.isFinite(r.expires)&&r.expires>Date.now()).slice(-128);}catch{/* No dependency on optional storage. */}
   this.stop=()=>{for(const el of [...this.active.keys()])this.finish(el);};this.visibility=()=>{if(this.doc.hidden)this.stop();};
   this.media.addEventListener?.('change',this.stop);this.doc.addEventListener('visibilitychange',this.visibility);this.env.addEventListener('pagehide',this.stop);
  }
  set(el,value,{scope='overview',key=el?.id||'',precision=0,suffix='',format,duration=760}={}){
   if(!el)return;
   const old=this.active.get(el),previous=old?.current??this.values.get(el)??this.records.findLast(r=>r.metric===key)?.value??0;
   this.finish(el);const valid=numeric(value),digits=Math.max(0,Math.min(6,Number.isInteger(precision)?precision:0));
   const formatter=new Intl.NumberFormat(undefined,{minimumFractionDigits:digits,maximumFractionDigits:digits});
   const render=format||(n=>formatter.format(n)+suffix);
   if(!valid){el.textContent='—';this.values.delete(el);return;}
   const final=render(value),identity=(scope+':'+key).slice(0,300),seen=this.records.some(r=>r.key===identity&&r.value===value);
   this.values.set(el,value);this.records=this.records.filter(r=>r.key!==identity);this.records.push({key:identity,metric:String(key).slice(0,100),value,expires:Date.now()+7200000});this.records=this.records.slice(-128);
   try{this.env.sessionStorage?.setItem(STATS_KEY,JSON.stringify(this.records));}catch{/* Final values remain readable. */}
   el.textContent=final;
   for(const node of [...this.active.keys()])if(node.isConnected===false)this.finish(node);
   if(seen||this.media.matches||this.doc.hidden||previous===value||this.active.size>=16||!this.env.requestAnimationFrame)return;
   const spoken=this.doc.createElement('span'),visual=this.doc.createElement('span');spoken.className='sr-only';spoken.textContent=final;visual.setAttribute('aria-hidden','true');visual.textContent=render(previous);el.replaceChildren(spoken,visual);
   const item={final,visual,current:previous,from:previous,start:this.env.performance.now(),frame:null};this.active.set(el,item);
   const tick=time=>{if(this.active.get(el)!==item)return;if(this.media.matches||this.doc.hidden||el.isConnected===false||!el.contains(visual)){this.finish(el);return;}
    const t=Math.max(0,Math.min(1,(time-item.start)/Math.max(500,Math.min(1200,duration))));item.current=item.from+(value-item.from)*(1-(1-t)**3);visual.textContent=render(item.current);
    if(t===1)this.finish(el);else item.frame=this.env.requestAnimationFrame(tick);
   };
   try{item.frame=this.env.requestAnimationFrame(tick);}catch{this.finish(el);}
  }
  finish(el){const item=this.active.get(el);if(!item)return;this.env.cancelAnimationFrame(item.frame);if(el.contains(item.visual))el.textContent=item.final;this.active.delete(el);}
  destroy(){this.stop();this.media.removeEventListener?.('change',this.stop);this.doc.removeEventListener('visibilitychange',this.visibility);this.env.removeEventListener('pagehide',this.stop);}
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={Boot,Statistics,BOOT_KEY,STATS_KEY};
 if(root.document&&!root.CinematicBoot){try{root.LivingStatistics=new Statistics(root);root.CinematicBoot=new Boot(root);root.CinematicBoot.initialize();}catch{root.CinematicBoot?.destroy();}}
})(globalThis);
