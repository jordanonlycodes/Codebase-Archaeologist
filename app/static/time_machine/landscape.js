/* Shared nested spatial map for measured historical paths and exact revision trees. */
(function(root){
 'use strict';
 const D=root.TimeMachineData,make=(tag,attrs={},value)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(value!==undefined)n.textContent=String(value);return n;};
 class Landscape{
  constructor(host){this.host=host;this.nodes=new Map();}
  draw(rows,directory,metric,open,inspect,more){this.host.replaceChildren();this.nodes.clear();let groups=D.groups(rows,directory,metric),visible=groups.slice(0,239);const omitted=groups.slice(239);if(omitted.length)visible.push({name:`${omitted.length} more groups`,path:null,directory:false,files:omitted.reduce((s,n)=>s+n.files,0),weight:omitted.reduce((s,n)=>s+n.weight,0),value:null,more:true});
   const max=Math.max(1,...groups.map(n=>n.value||0)),canvas=make('svg',{viewBox:'0 0 1000 480',role:'group','aria-label':`Nested historical path map. ${metric}; ${directory||'repository root'}.`,'class':'tm-landscape'});this.canvas=canvas;
   const defs=make('defs'),pattern=make('pattern',{id:'tm-unmeasured',patternUnits:'userSpaceOnUse',width:9,height:9});pattern.append(make('rect',{width:9,height:9,fill:'#24262a'}),make('path',{d:'M0 9L9 0',stroke:'#55505a','stroke-width':1}));defs.append(pattern);canvas.append(defs);
   const draw=(items,x,y,w,h,nested=false)=>{for(const tile of D.partition(items,x,y,w,h)){const g=make('g',{tabindex:0,role:'button','aria-label':`${tile.path||tile.name}: ${tile.value==null?'unmeasured':tile.value} ${metric}`,'class':'tm-map-cell'}),gap=nested?2:4,width=Math.max(0,tile.w-gap*2),height=Math.max(0,tile.h-gap*2),color=tile.value==null?'url(#tm-unmeasured)':tile.value===0?'#292c30':`hsl(350 19% ${16+Math.min(1,tile.value/max)*22}%)`;g.append(make('title',{},`${tile.path||tile.name}\n${tile.value==null?'Unavailable / partial':tile.value} ${metric}\n${tile.files} observed file paths`),make('rect',{x:tile.x+gap,y:tile.y+gap,width,height,fill:color,rx:nested?1:3}));
    if(width>65&&height>28){const chars=Math.max(4,Math.floor((width-20)/7)),label=tile.name.length>chars?tile.name.slice(0,chars-1)+'…':tile.name;g.append(make('text',{x:tile.x+gap+10,y:tile.y+gap+21,'class':tile.directory?'tm-directory-label':'tm-map-label'},label));if(height>57&&width>90)g.append(make('text',{x:tile.x+gap+10,y:tile.y+gap+42,'class':'tm-map-value'},tile.value==null?'unmeasured':`${tile.value.toLocaleString()} ${metric}`));}
    const act=()=>{if(tile.more)more(omitted);else if(tile.directory)open(tile.path);else{for(const n of this.nodes.values())n.classList.remove('is-selected');g.classList.add('is-selected');inspect(tile.path);}};
    g.addEventListener('click',e=>{e.stopPropagation?.();act();});g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation?.();act();}});this.nodes.set(tile.path||'@more',g);canvas.append(g);
    if(!nested&&tile.directory&&width>190&&height>135){const children=D.groups(rows,tile.path,metric).slice(0,8);draw(children,tile.x+gap+6,tile.y+gap+62,width-12,height-68,true);}
   }};
   draw(visible,0,0,1000,480);this.host.append(canvas);if(!groups.length){const p=document.createElement('p');p.textContent='No historical paths match this directory and range.';this.host.append(p);}return {shown:visible.length,total:groups.length,max};
  }
  destroy(){this.host.replaceChildren();this.nodes.clear();this.canvas=null;}
 }
 root.TimeMachineLandscape=Landscape;
})(globalThis);
