'use strict';
const $=id=>document.getElementById(id);
const number=value=>new Intl.NumberFormat().format(value);
const bytes=value=>value<1024?`${number(value)} B`:value<1048576?`${(value/1024).toFixed(1)} KiB`:`${(value/1048576).toFixed(1)} MiB`;
function node(tag,text,css){const element=document.createElement(tag);if(text!==undefined)element.textContent=String(text);if(css)element.className=css;return element;}
const workspaceStore=(()=>{try{return new ArchaeologistStore.Store({records:new ArchaeologistStore.BrowserRecords(window.indexedDB),tab:window.sessionStorage});}catch{const unavailable=async()=>{throw new Error('Browser workspace storage is unavailable. Enable site storage to preserve analysis between pages.');};return {load:unavailable,save:unavailable,forget:unavailable,view:()=>null,handoff:()=>null};}})();
const workspacePages=new Set(['overview','risk','structure','graph','architecture','heatmaps','blast-radius']);
window.WorkspaceNavigation={open(page,id){if(!workspacePages.has(page))return false;if(id)workspaceStore.handoff({page,id});location.assign('/workspace/'+page);return true;}};
function riskBars(id,entries){const container=$(id);container.replaceChildren();const maximum=Math.max(1,...entries.map(e=>e[1]));for(const [label,count]of entries){const row=node('div',undefined,'risk-bar'),title=node('div'),bar=node('progress');title.append(node('span',label),node('strong',number(count)));bar.max=maximum;bar.value=count;bar.setAttribute('aria-label',`${label}: ${count}`);row.append(title,bar);container.append(row);}if(!entries.length)container.append(node('p','No measured functions to display.','risk-chart-empty'));}
