/* GPU-independent quality policy. Frame intervals are a coarse signal, not GPU profiling. */
(function(root){
 'use strict';
 const PROFILES=Object.freeze({
  performance:Object.freeze({name:'Performance',pixelRatio:1,resolution:4,candidates:20,labels:12,labelMs:100,arrows:'focused'}),
  balanced:Object.freeze({name:'Balanced',pixelRatio:1.5,resolution:6,candidates:40,labels:24,labelMs:50,arrows:'all'}),
  automatic:Object.freeze({name:'Auto · conservative',pixelRatio:1.25,resolution:6,candidates:28,labels:16,labelMs:75,arrows:'all'})
 });
 class Policy{
  constructor(){this.mode=null;this.samples=[];this.slowWindows=0;this.previous=null;this.medianMs=null;this.downgraded=false;this.setMode('auto');}
  setMode(mode){
   mode=['auto','performance','balanced'].includes(mode)?mode:'auto';
   if(this.mode===mode)return false;
   this.mode=mode;this.samples=[];this.slowWindows=0;this.previous=null;this.medianMs=null;this.downgraded=false;return true;
  }
  get profile(){return this.mode==='performance'||this.downgraded?PROFILES.performance:this.mode==='balanced'?PROFILES.balanced:PROFILES.automatic;}
  pause(){this.previous=null;}
  frame(time){
   const previous=this.previous;this.previous=time;
   if(this.mode!=='auto'||this.downgraded||previous===null)return false;
   const elapsed=time-previous;
   // Ignore nonpositive samples; pause() excludes sleep/hidden intervals.
   if(elapsed<=0)return false;
   this.samples.push(elapsed);
   if(this.samples.length<24)return false;
   const sorted=[...this.samples].sort((a,b)=>a-b);this.medianMs=(sorted[11]+sorted[12])/2;this.samples=[];
   this.slowWindows=this.medianMs>28?this.slowWindows+1:0;
   if(this.slowWindows<2)return false;
   this.downgraded=true;return true;
  }
 }
 const api={PROFILES,Policy};root.ArchaeologistQuality=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
