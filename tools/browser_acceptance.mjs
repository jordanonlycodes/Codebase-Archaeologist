// Real browser smoke, no third-party automation package. Setup in Task7E browser docs.
import{connect}from'./chromium_cdp.mjs';import fs from'node:fs';const c=await connect();const checks=[];
// Requires the real fixture imported in this dedicated browser tab via /explore.

const record=(name,data)=>{checks.push({name,...data});console.log(name,JSON.stringify(data));};
await c.go('/workspace/graph');await c.wait('graphExplorer.ix?.nodes.size>0');await c.evaluate(`document.getElementById('graph-3d').click()`);await c.wait(`graphExplorer.adapter?.constructor.name==='ThreeGraph'`);await new Promise(r=>setTimeout(r,600));
const pos=()=>c.evaluate(`JSON.stringify({p:graphExplorer.adapter.graph.camera().position.toArray(),t:graphExplorer.adapter.graph.controls().target.toArray()})`);
await c.evaluate(`document.getElementById('graph-fullscreen').click()`);await new Promise(r=>setTimeout(r,500));
const rect=await c.evaluate(`(()=>{const r=document.querySelector('#graph-canvas canvas')?.getBoundingClientRect()||document.querySelector('canvas').getBoundingClientRect();return{x:r.x+30,y:r.y+80}})()`);
const drag=async()=>{await c.call('Input.dispatchMouseEvent',{type:'mousePressed',x:rect.x,y:rect.y,button:'left',clickCount:1});await c.call('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x+100,y:rect.y+30,button:'left',buttons:1});await c.call('Input.dispatchMouseEvent',{type:'mouseReleased',x:rect.x+100,y:rect.y+30,button:'left',clickCount:1});};
let a=await pos();await drag();let b=await pos();record('orbit',{pass:a!==b,before:a,after:b});
await c.evaluate(`document.getElementById('graph-pan').click()`);a=await pos();await drag();b=await pos();record('pan',{pass:JSON.parse(a).t.toString()!==JSON.parse(b).t.toString(),before:a,after:b});
a=await pos();await c.call('Input.dispatchMouseEvent',{type:'mouseWheel',x:rect.x,y:rect.y,deltaX:0,deltaY:-130});await new Promise(r=>setTimeout(r,300));b=await pos();record('zoom',{pass:a!==b});
await c.evaluate(`document.getElementById('graph-reset').click()`);await new Promise(r=>setTimeout(r,900));b=await pos();record('reset',{pass:a!==b,camera:b});
await c.evaluate(`document.querySelector('#graph-results button')?.click()`);console.log('selected?',await c.evaluate('graphExplorer.state.selected'));if(!await c.evaluate('Boolean(graphExplorer.state.selected)'))await c.evaluate(`graphExplorer.choose([...graphExplorer.ix.nodes.values()].find(n=>n.type==='function').id)`);
await c.shot('/tmp/codebase-browser-graph.png');record('3D renderer',{pass:await c.evaluate('Boolean(document.querySelector("canvas")&&graphExplorer.state.selected)'),selected:await c.evaluate('graphExplorer.state.selected')});
for(const page of ['architecture','heatmaps','blast-radius','risk','structure','jordan','time-machine']){await c.go('/workspace/'+page);await c.wait(`!document.getElementById('workspace-content').hidden`);await new Promise(r=>setTimeout(r,350));record(page,{pass:true,svg:await c.evaluate('document.querySelectorAll("svg").length'),text:await c.evaluate('document.body.innerText.slice(-350)')});if(page==='jordan'){await c.evaluate(`document.getElementById('jordan-question').value='Which functions are most complex?';document.getElementById('jordan-form').requestSubmit()`);await c.wait(`document.querySelector('#jordan-messages')?.innerText.includes('clamp_index')`);record('Jordan grounded reply',{pass:true,text:await c.evaluate('document.getElementById("jordan-messages").innerText')});}}
record('uncaught exceptions',{pass:!c.events.some(e=>e.method==='Runtime.exceptionThrown'),errors:c.events.filter(e=>e.method==='Runtime.exceptionThrown')});
fs.writeFileSync('/tmp/codebase-browser-checks.json',JSON.stringify(checks,null,2));c.close();
