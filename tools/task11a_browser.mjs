// Native CDP acceptance against a dedicated temporary Chromium profile. No UI mockups.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {connect} from './chromium_cdp.mjs';
process.env.CHROME_DEBUG_URL??='http://127.0.0.1:9226';
process.env.BASE_URL??='http://127.0.0.1:8013';
const c=await connect(),checks=[];
const record=(name,details={})=>{checks.push({name,pass:true,...details});console.log('PASS',name);};
const click=async selector=>{
 await c.evaluate(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({behavior:'instant',block:'center'})`);
 const p=await c.evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 await c.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...p});await c.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...p});
};
try{
 await c.call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});
 await c.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await c.go('/');await c.evaluate(`CinematicBoot.finish(false);sessionStorage.clear()`);
 await c.call('Page.reload');await c.wait(`document.querySelector('.cinematic-boot')?.dataset.phase==='relic'`);record('first session relic phase');
 await c.wait(`document.querySelector('.cinematic-boot')?.dataset.phase==='intelligence'`);
 assert.equal(await c.evaluate(`document.activeElement.textContent`),'Skip Intro');
 await c.wait(`Number(getComputedStyle(document.querySelector('.boot-name')).opacity)>.95`);
 fs.mkdirSync('reports/ui/task11a',{recursive:true});await c.shot('reports/ui/task11a/boot.png');record('actual brand/title and accessible skip focus');
 await c.wait(`!document.querySelector('.cinematic-boot')`);
 assert.equal(await c.evaluate(`CinematicBoot.timers.size`),0);record('automatic finite completion and timer cleanup');
 await c.go('/explore');assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);record('same session navigation does not replay');
 await c.call('Page.reload');await c.wait(`document.readyState==='complete'`);assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);record('reload does not replay');
 await click('[data-replay-intro]');await c.wait(`!!document.querySelector('.cinematic-boot')`);await click('.boot-skip');assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);assert.equal(await c.evaluate(`document.activeElement.hasAttribute('data-replay-intro')`),true);record('pointer replay/skip and trigger focus restoration');
 await click('[data-replay-intro]');await c.call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await c.call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);record('Escape dismissal');
 await click('[data-replay-intro]');await c.call('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});await c.call('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);record('Tab dismisses without trapping background focus');
 const d=await c.call('DOM.getDocument'),q=await c.call('DOM.querySelector',{nodeId:d.root.nodeId,selector:'#file-input'});
 await c.call('DOM.setFileInputFiles',{nodeId:q.nodeId,files:[process.env.DEMO_ZIP||'/tmp/task11a-demo.zip']});await click('#analyze-zip');
 await c.wait(`location.pathname==='/workspace/overview'&&!!activeAnalysis&&!document.getElementById('workspace-content').hidden`);
 await c.wait(`LivingStatistics.active.size===0`);
 const metrics=await c.evaluate(`({files:document.getElementById('stat-files').textContent,lines:document.getElementById('stat-lines').textContent,summary:activeAnalysis.summary,predictions:activeAnalysis.defect_risk.analyzed_functions})`);
 assert.equal(metrics.files,new Intl.NumberFormat().format(metrics.summary.files));assert.equal(metrics.lines,new Intl.NumberFormat().format(metrics.summary.source_lines));assert.equal(metrics.predictions,3);record('real ZIP summary and genuine C predictions unchanged',metrics);
 assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);record('analysis completion does not replay intro');
 await c.shot('reports/ui/task11a/overview.png');
 await c.evaluate(`window.statProbe=document.createElement('strong');statProbe.id='task11a-probe';document.querySelector('.stats-grid').append(statProbe);LivingStatistics.set(statProbe,12.75,{scope:'probe',key:'percentage',precision:2,suffix:'%'})`);
 const intermediate=await c.evaluate(`({accessible:statProbe.querySelector('.sr-only').textContent,visual:statProbe.querySelector('[aria-hidden]').textContent})`);assert.equal(intermediate.accessible,'12.75%');assert.notEqual(intermediate.visual,'12.75%');record('decimal counter accessible final value and actual intermediate frame',intermediate);
 await c.evaluate(`LivingStatistics.set(statProbe,42.25,{scope:'probe',key:'percentage',precision:2,suffix:'%'})`);assert.equal(await c.evaluate('LivingStatistics.active.size'),1);await c.wait(`statProbe.textContent==='42.25%'&&LivingStatistics.active.size===0`);record('stale decimal animation cancelled and exact percentage final value');
 await c.evaluate(`LivingStatistics.set(statProbe,0);LivingStatistics.stop()`);assert.equal(await c.evaluate('statProbe.textContent'),'0');await c.evaluate(`LivingStatistics.set(statProbe,null)`);assert.equal(await c.evaluate('statProbe.textContent'),'—');record('zero and missing numeric presentation');await c.evaluate('statProbe.remove()');
 await c.go('/workspace/structure');await c.wait('!!activeAnalysis');await c.go('/workspace/overview');await c.wait('!!activeAnalysis');assert.equal(await c.evaluate('LivingStatistics.active.size'),0);record('restored snapshot does not count again');
 await click('[data-replay-intro]');assert.equal(await c.evaluate(`!!activeAnalysis&&document.getElementById('stat-files').textContent===new Intl.NumberFormat().format(activeAnalysis.summary.files)`),true);record('data remains loaded during replay');
 await c.call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await c.wait(`!document.querySelector('.cinematic-boot')`);
 await c.evaluate(`sessionStorage.removeItem('archaeologist.intro.v1')`);await c.call('Page.reload');await c.wait('!!window.activeAnalysis');assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')||LivingStatistics.active.size>0`),false);record('reduced motion on load and mid-intro displays final content');
 await c.call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});
 for(const width of [1440,1024,768,390]){
  await c.call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500});
  await click('[data-replay-intro]');
  const size=await c.evaluate(`({document:document.documentElement.scrollWidth,viewport:innerWidth,overlay:document.querySelector('.cinematic-boot').getBoundingClientRect().width,skip:document.querySelector('.boot-skip').getBoundingClientRect().width})`);
  assert(size.document<=size.viewport+1);assert(size.overlay<=size.viewport+1);assert(size.skip>=44);await click('.boot-skip');record('responsive intro and statistics',{width,...size});
 }
 await c.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await click('[data-replay-intro]');await c.evaluate(`for(const id of CinematicBoot.timers)clearTimeout(id);CinematicBoot.timers.clear()`);
 await c.wait(`getComputedStyle(document.querySelector('.cinematic-boot')).visibility==='hidden'`,6500);assert.equal(await c.evaluate(`getComputedStyle(document.querySelector('.cinematic-boot')).pointerEvents`),'none');record('independent CSS failsafe releases pointer interaction if JS timers stop');await c.evaluate('CinematicBoot.finish()');
 await c.call('Emulation.setCPUThrottlingRate',{rate:4});await c.evaluate(`window.cpuProbe=document.createElement('span');document.querySelector('main').append(cpuProbe);LivingStatistics.set(cpuProbe,activeAnalysis.summary.source_lines,{scope:'cpu-probe',key:'source-lines'})`);await c.wait('LivingStatistics.active.size===0');assert.equal(await c.evaluate('cpuProbe.textContent'),new Intl.NumberFormat().format(metrics.summary.source_lines));record('finite counter completes under4x CPU throttling');await c.call('Emulation.setCPUThrottlingRate',{rate:1});await c.evaluate('cpuProbe.remove()');
 const injected=await c.call('Page.addScriptToEvaluateOnNewDocument',{source:`Object.defineProperty(window,'sessionStorage',{get(){throw new DOMException('Storage blocked','SecurityError')}})`});
 await c.go('/');assert.equal(await c.evaluate(`!!document.querySelector('.cinematic-boot')`),false);await click('[data-replay-intro]');await c.wait(`!!document.querySelector('.cinematic-boot')`);await click('.boot-skip');record('blocked session storage skips automatic intro and keeps manual replay usable');
 await c.call('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.identifier});
 const exceptions=c.events.filter(e=>e.method==='Runtime.exceptionThrown');assert.equal(exceptions.length,0);record('no uncaught JavaScript exceptions');
 const version=await(await fetch(process.env.CHROME_DEBUG_URL+'/json/version')).json();
 const source_sha256=Object.fromEntries(['app/static/product/cinematic.js','app/static/product/cinematic.css','app/static/product/overview.js','app/static/product/workspace.js','app/templates/public_base.html','app/templates/workspace_base.html','app/templates/cinematic_assets.html'].map(path=>[path,createHash('sha256').update(fs.readFileSync(path)).digest('hex')]));
 fs.writeFileSync('reports/ui/task11a/browser.json',JSON.stringify({browser:version.Browser,captured_at:new Date().toISOString(),base_url:process.env.BASE_URL,fixture:'tests/fixtures/university_demo',source_sha256,checks,scope:'Real sandboxed headless Chromium/CDP; no physical GPU FPS, screen-reader or full WCAG certification.'},null,2)+'\n');
}finally{await c.call('Emulation.setCPUThrottlingRate',{rate:1});c.close();}
