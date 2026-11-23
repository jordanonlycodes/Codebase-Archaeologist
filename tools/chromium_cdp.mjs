// Native Node26 WebSocket CDP helper. Use only a dedicated temporary browser profile.
import fs from 'node:fs';
export async function connect(){
 const targets=await(await fetch((process.env.CHROME_DEBUG_URL||'http://127.0.0.1:9224')+'/json')).json();
 const t=targets.find(t=>t.type==='page');const ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let seq=0;const pending=new Map(),events=[];ws.onmessage=e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);v.error?p.reject(Error(JSON.stringify(v.error))):p.resolve(v.result);}else {events.push(v);if(events.length>2000)events.shift();}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const wait=async(expression,ms=20000)=>{const end=Date.now()+ms;while(Date.now()<end){try{if(await evaluate(expression))return;}catch{}await new Promise(r=>setTimeout(r,150));}throw Error('Timed out: '+expression);};
 const go=async path=>{
  const url=(process.env.BASE_URL||'http://127.0.0.1:8000')+path,nav=await call('Page.navigate',{url});
  if(nav.errorText)throw Error('Browser navigation failed: '+nav.errorText);
  // The previous document can still report readyState=complete after navigate.
  // Observe the actual new main-frame commit before querying the destination UI.
  if(nav.loaderId){const end=Date.now()+20000;while(!events.some(e=>e.method==='Page.frameNavigated'&&e.params.frame.id===nav.frameId&&e.params.frame.loaderId===nav.loaderId)){if(Date.now()>end)throw Error('Main-frame navigation did not commit');await new Promise(r=>setTimeout(r,20));}}
  await wait(`document.readyState==='complete'&&location.href===${JSON.stringify(url)}`);
 };
 const shot=async path=>{const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path,Buffer.from(r.data,'base64'));};
 return{call,evaluate,wait,go,shot,events,close:()=>ws.close()};
}
