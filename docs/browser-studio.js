"use strict";
(() => {
 const canvas=document.getElementById("stage"),ctx=canvas.getContext("2d");
 const status=document.getElementById("status"),play=document.getElementById("play"),exportButton=document.getElementById("export"),stop=document.getElementById("stop");
 const W=1280,H=720,INTRO=5,STORY=7,OUTRO=5,FPS=30;
 let stories=[],frame=0,recorder=null,stream=null,chunks=[],running=false,finishRequested=false;
 const audio=new Audio("latest.mp4");audio.preload="metadata";
 let audioContext=null,audioDestination=null;
 const setStatus=s=>{status.textContent=s;};
 async function prepareAudio(){
   if(!audioContext){
     const AC=window.AudioContext||window.webkitAudioContext;
     if(!AC)throw Error("Web Audio wird nicht unterstützt");
     audioContext=new AC();
     const source=audioContext.createMediaElementSource(audio);
     audioDestination=audioContext.createMediaStreamDestination();
     source.connect(audioContext.destination);
     source.connect(audioDestination);
   }
   await audioContext.resume();
   if(audio.readyState<1)await new Promise((resolve,reject)=>{
     audio.addEventListener("loadedmetadata",resolve,{once:true});
     audio.addEventListener("error",()=>reject(Error("MP4-Audio konnte nicht geladen werden")),{once:true});
   });
   if(!Number.isFinite(audio.duration)||audio.duration<=0)throw Error("Ungültige Audio-Laufzeit");
 }
 function sceneTiming(){
   const total=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:INTRO+stories.length*STORY+OUTRO;
   const intro=Math.min(8,total/3),outro=Math.min(8,total/3);
   return {total,intro,outro,storyLength:Math.max(0,total-intro-outro)/Math.max(1,stories.length)};
 }
 function parseTranscript(raw){
   const sections=raw.trim().split(/\n\s*\n/).map(s=>s.trim()).filter(Boolean);
   return sections.slice(2,-1).map(section=>{const [title,...description]=section.split("\n");return {title:title||"",description:description.join(" ")};}).filter(x=>x.title).slice(0,10);
 }
 function wrap(text,maxWidth,font,maxLines=3){
   ctx.font=font;const words=String(text).split(/\s+/),lines=[];let line="";
   for(const word of words){const next=line?line+" "+word:word;if(ctx.measureText(next).width>maxWidth&&line){lines.push(line);line=word;}else line=next;}
   if(line)lines.push(line);
   return lines.slice(0,maxLines);
 }
 function draw(time){
   const {total,intro,outro,storyLength}=sceneTiming();
   const t=Math.min(time,total),isIntro=t<intro,isOutro=t>=total-outro;
   ctx.fillStyle="#071425";ctx.fillRect(0,0,W,H);
   const glow=ctx.createRadialGradient(900,250,0,900,250,780);
   glow.addColorStop(0,"#0e4b68");glow.addColorStop(1,"#071425");
   ctx.fillStyle=glow;ctx.fillRect(0,0,W,H);
   const shift=(t*22)%80;ctx.strokeStyle="rgba(71,211,255,.13)";ctx.lineWidth=1;
   for(let x=-80+shift;x<W+80;x+=80){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
   for(let y=-80+shift;y<H+80;y+=80){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
   ctx.fillStyle="#35d9ff";ctx.fillRect(0,0,W,9);ctx.font="bold 24px system-ui";ctx.fillText("PERSONAL / NEWS / HOST",56,65);
   ctx.fillStyle="#9ddfed";ctx.font="19px monospace";ctx.fillText("BROWSER RENDER ENGINE  //  LOCAL",56,101);
   if(isIntro||isOutro){
     const scale=1+Math.sin(t*2)*.015;
     ctx.save();ctx.translate(W/2,H/2);ctx.scale(scale,scale);ctx.textAlign="center";
     ctx.fillStyle="#ffffff";ctx.font="bold 75px system-ui";ctx.fillText("PersonalNewsHost",0,-20);
     ctx.fillStyle="#49dfff";ctx.font="26px monospace";ctx.fillText(isIntro?"TECH / KI / NEWS":"ENDE DER SENDUNG",0,47);
     ctx.font="20px system-ui";ctx.fillText(isIntro?"Nachrichten in Bewegung":"Quellen und Transkript auf der Webseite",0,99);
     ctx.restore();
   }else{
     const idx=Math.min(stories.length-1,Math.floor((t-intro)/Math.max(.001,storyLength)));
     const item=stories[idx];const progress=((t-intro)%Math.max(.001,storyLength))/Math.max(.001,storyLength);
     ctx.fillStyle="rgba(3,15,30,.82)";ctx.fillRect(42,180,1196,395);
     ctx.fillStyle="#27d4f5";ctx.fillRect(42,180,Math.max(0,1196*progress),5);
     ctx.fillStyle="#4ce0ff";ctx.font="bold 23px monospace";ctx.fillText("MELDUNG "+String(idx+1).padStart(2,"0")+" / "+String(stories.length).padStart(2,"0"),76,240);
     ctx.fillStyle="#fff";const lines=wrap(item.title,1090,"bold 47px system-ui",3);
     ctx.font="bold 47px system-ui";lines.forEach((line,i)=>ctx.fillText(line,76,320+i*62));
     ctx.fillStyle="#b4d6e8";ctx.font="24px system-ui";
     const summary=wrap(item.description,1080,"24px system-ui",2);
     summary.forEach((line,i)=>ctx.fillText(line,76,520+i*33));
   }
   ctx.fillStyle="#7aa9bf";ctx.font="18px monospace";ctx.fillText("PERSONALNEWSHOST  /  LOKAL GERENDERT",56,675);
   ctx.textAlign="right";ctx.fillText(Math.floor(t)+"s / "+total+"s",W-56,675);ctx.textAlign="left";
 }
 function reset(){
   running=false;cancelAnimationFrame(frame);audio.pause();audio.currentTime=0;
   play.disabled=!stories.length;exportButton.disabled=!stories.length;stop.disabled=true;
   if(stream){stream.getTracks().forEach(track=>track.stop());stream=null;}
   draw(0);
 }
 function complete(){
   if(finishRequested)return;
   finishRequested=true;running=false;cancelAnimationFrame(frame);audio.pause();
   if(recorder&&recorder.state==="recording")recorder.stop();
   else {reset();setStatus("Wiedergabe beendet.");}
 }
 function tick(){
   if(!running)return;
   draw(audio.currentTime);
   if(audio.ended||audio.currentTime>=sceneTiming().total-.04){complete();return;}
   frame=requestAnimationFrame(tick);
 }
 async function begin(save){
   if(!stories.length||running)return;
   play.disabled=true;exportButton.disabled=true;stop.disabled=false;
   try{
     await prepareAudio();audio.currentTime=0;finishRequested=false;
     if(save){
       if(!canvas.captureStream||typeof MediaRecorder==="undefined")throw Error("WebM-Export wird nicht unterstützt");
       const mime=["video/webm;codecs=vp9,opus","video/webm;codecs=vp8,opus","video/webm"].find(x=>MediaRecorder.isTypeSupported(x));
       if(!mime)throw Error("Kein kompatibler WebM-Codec verfügbar");
       chunks=[];stream=canvas.captureStream(FPS);
       for(const track of audioDestination.stream.getAudioTracks())stream.addTrack(track);
       recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2500000});
       recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
       recorder.onstop=()=>{
         const data=chunks.slice();reset();
         if(data.length){
           const blob=new Blob(data,{type:mime}),url=URL.createObjectURL(blob),a=document.createElement("a");
           a.href=url;a.download="personalnewshost-mit-ton.webm";a.click();
           setTimeout(()=>URL.revokeObjectURL(url),60000);
           setStatus("WebM mit Ton lokal erzeugt und zum Download angeboten.");
         }else setStatus("Keine Videodaten aufgezeichnet.");
       };
       recorder.start(1000);
     }
     await audio.play();
     running=true;setStatus(save?"Video und Ton werden lokal aufgezeichnet …":"Nachrichtensendung mit Ton läuft.");
     frame=requestAnimationFrame(tick);
   }catch(e){
     if(recorder&&recorder.state==="recording")recorder.stop();
     reset();setStatus("Start fehlgeschlagen: "+e.message);
   }
 }
 audio.addEventListener("ended",()=>{if(running)complete();});
 play.addEventListener("click",()=>begin(false));
 exportButton.addEventListener("click",()=>begin(true));
 stop.addEventListener("click",()=>{
   if(recorder&&recorder.state==="recording"){complete();setStatus("Aufzeichnung wird abgeschlossen …");}
   else {reset();setStatus("Gestoppt.");}
 });
 fetch("transcript.txt",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("Transkript nicht verfügbar");return r.text();}).then(raw=>{
   stories=parseTranscript(raw);
   if(!stories.length)throw Error("Keine Meldungen im Transkript gefunden");
   draw(0);setStatus(stories.length+" Meldungen geladen. Audio aus latest.mp4; Schlagzeilen näherungsweise verteilt.");
 }).catch(e=>{setStatus("Fehler: "+e.message);play.disabled=true;exportButton.disabled=true;});
})();
