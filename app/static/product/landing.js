/* Procedural light study, not repository analytics. Bounded 2D canvas, 24 Hz, idle offscreen. */
(function(){
 'use strict';
 const canvas=document.getElementById('hero-light'),context=canvas.getContext('2d'),reduced=matchMedia('(prefers-reduced-motion: reduce)'),abort=new AbortController();
 let paused=false,frame=null,visible=true,last=0,phase=0,width=1,height=1,pointer=0;
 const point=(t,a,b,c,d)=>({x:(1-t)**3*a.x+3*(1-t)**2*t*b.x+3*(1-t)*t*t*c.x+t**3*d.x,y:(1-t)**3*a.y+3*(1-t)**2*t*b.y+3*(1-t)*t*t*c.y+t**3*d.y});
 function draw(){if(!context)return;context.clearRect(0,0,width,height);const x=width*.84+pointer*8,y=height*.47;
  const glow=context.createRadialGradient(x,y,0,x,y,width*.27);glow.addColorStop(0,'#e5d5b91c');glow.addColorStop(.35,'#d9b4a00b');glow.addColorStop(1,'#11121400');context.fillStyle=glow;context.fillRect(0,0,width,height);
  for(let i=0;i<18;i++){const offset=i-8.5,a={x:width*.28,y:height*(1.06+i*.005)},b={x:width*(.68+i*.002),y:height*(1.03-offset*.028)},c={x:width*(.54+i*.009),y:height*(-.12+offset*.012)+Math.sin(phase+i*.3)*8},d={x,y:y+offset*.8};
   const gradient=context.createLinearGradient(a.x,a.y,x,y);gradient.addColorStop(0,'#bc807000');gradient.addColorStop(.38,i%4===0?'#91575c40':'#b7a38b28');gradient.addColorStop(.85,'#d8c2a15c');gradient.addColorStop(1,'#f2e5c9a0');context.strokeStyle=gradient;context.lineWidth=i%3===0?.8:.4;context.beginPath();context.moveTo(a.x,a.y);context.bezierCurveTo(b.x,b.y,c.x,c.y,d.x,d.y);context.stroke();
   const t=((phase*.015+i*.053)%1),q=point(t,a,b,c,d),r=point(Math.min(1,t+.045),a,b,c,d);const light=context.createLinearGradient(q.x,q.y,r.x,r.y);light.addColorStop(0,'#e7c2a000');light.addColorStop(1,'#e7d3b078');context.strokeStyle=light;context.lineWidth=.9;context.beginPath();context.moveTo(q.x,q.y);context.lineTo(r.x,r.y);context.stroke();
  }
  const orb=context.createRadialGradient(x-3,y-3,0,x,y,21);orb.addColorStop(0,'#fff6df');orb.addColorStop(.18,'#f0dcaf');orb.addColorStop(.4,'#b6a78baf');orb.addColorStop(1,'#c5af8800');context.fillStyle=orb;context.beginPath();context.ellipse(x,y,25,25,0,0,Math.PI*2);context.fill();
 }
 function tick(time){frame=null;if(!visible||document.hidden||reduced.matches)return;if(time-last>=1000/24){phase+=.045;draw();last=time;}frame=requestAnimationFrame(tick);}
 function start(){cancelAnimationFrame(frame);frame=null;draw();if(!paused&&context&&visible&&!document.hidden&&!reduced.matches)frame=requestAnimationFrame(tick);}
 const resize=new ResizeObserver(()=>{const rect=canvas.getBoundingClientRect();width=rect.width;height=rect.height;const ratio=Math.min(devicePixelRatio||1,1.25);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);start();});resize.observe(canvas);
 const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;start();});observer.observe(canvas);
 document.addEventListener('visibilitychange',start,{signal:abort.signal});reduced.addEventListener('change',start,{signal:abort.signal});canvas.parentElement.addEventListener('pointermove',event=>{pointer=(event.clientX/innerWidth-.5);},{passive:true,signal:abort.signal});
 const reveal=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){entry.target.classList.add('is-visible');reveal.unobserve(entry.target);}},{threshold:.08});if(!reduced.matches)for(const section of document.querySelectorAll('.landing-section')){section.classList.add('reveal-ready');reveal.observe(section);}
 addEventListener('pagehide',event=>{paused=true;cancelAnimationFrame(frame);frame=null;if(event.persisted)return;resize.disconnect();observer.disconnect();reveal.disconnect();abort.abort();});
 addEventListener('pageshow',event=>{if(event.persisted){paused=false;start();}});
})();
