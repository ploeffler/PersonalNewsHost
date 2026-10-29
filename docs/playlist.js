(function (root) {
  'use strict';
  const asset = (path, kind) => typeof path === 'string' && (kind === 'broadcast'
    ? /^broadcasts\/\d{8}T\d{6}Z\.(mp4|vtt|srt|txt)$/ : /^short-update-audio\/[a-f0-9]{24}\.wav$/).test(path);
  function buildItems(broadcasts, updates, now) {
    const longs = broadcasts.filter(b => b && Number.isFinite(b.created_at) && b.created_at <= now && asset(b.video, 'broadcast'))
      .sort((a,b) => a.created_at-b.created_at).slice(-2);
    const shorts = updates.filter(u => u && Number.isFinite(u.created_at) && u.created_at <= now && u.created_at > now-86400 &&
      (!longs.length || u.created_at >= longs[0].created_at) && /^[a-f0-9]{24}$/.test(u.id))
      .sort((a,b) => b.created_at-a.created_at).slice(0,5);
    return [...longs.map((b,i) => ({...b,kind:'broadcast',label:i === longs.length-1 ? 'Neueste Sendung' : 'Vorherige Sendung'})),
      ...shorts.map(u => ({...u,kind:'update',label:'Kurzupdate'}))]
      .sort((a,b) => b.created_at-a.created_at || (a.kind === 'broadcast' ? -1 : 1));
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {buildItems, asset};
  if (!root.document) return;
  const document = root.document;
  const list = document.getElementById('playlist-items');
  if (!list) return;
  const video = document.getElementById('bulletin-video');
  const audio = document.getElementById('update-audio');
  const text = document.getElementById('update-text');
  const status = document.getElementById('playlist-status');
  let broadcasts = [], updates = [], items = [], selected = null, signature = '';
  const date = timestamp => new Date(timestamp*1000).toLocaleString('de-AT', {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
  const key = item => item.kind + ':' + item.id;
  const sources = document.getElementById('bulletin-sources');
  function sourceList(entries) {
    sources.replaceChildren();
    for (const source of entries || []) {
      if (!/^https?:\/\//i.test(source.url || '')) continue;
      const li=document.createElement('li'), a=document.createElement('a');
      a.href=source.url; a.textContent=source.title || source.url; a.rel='noopener noreferrer'; li.append(a);sources.append(li);
    }
    if (!sources.children.length) {const li=document.createElement('li');li.textContent='Keine direkte Quellenverknüpfung verfügbar.';sources.append(li);}
  }
  function select(item, play) {
    selected=key(item);video.pause();audio.pause();
    document.getElementById('playing-title').textContent=item.title;
    document.getElementById('bulletin-timestamp').textContent='Stand: '+date(item.created_at);
    const isLong=item.kind==='broadcast';
    const hasAudio=!isLong && asset(item.audio,'update');
    video.hidden=!isLong;audio.hidden=!hasAudio;text.hidden=isLong;
    const transcript=document.getElementById('bulletin-transcript');
    const subtitles=document.getElementById('bulletin-subtitles');
    if (transcript) {transcript.hidden=!isLong || !asset(item.transcript,'broadcast');if(!transcript.hidden) transcript.href=item.transcript;}
    if (subtitles) {subtitles.hidden=!isLong || !asset(item.subtitle_download,'broadcast');if(!subtitles.hidden) subtitles.href=item.subtitle_download;}
    document.getElementById('playing-kind').textContent=isLong?'Sendung · Video':hasAudio?'Kurzupdate · Audio':'Kurzupdate · Text';
    if (isLong) {
      video.querySelectorAll('track').forEach(track=>track.remove());
      video.src=item.video;
      if(asset(item.subtitles,'broadcast')) {const track=document.createElement('track');track.kind='subtitles';track.src=item.subtitles;track.srclang='de';track.label='Deutsch';track.default=true;video.append(track);}
      sourceList(item.sources);video.load();
    } else {
      text.textContent=item.text || item.title;
      audio.removeAttribute('src');if(hasAudio){audio.src=item.audio;audio.load();}
      sourceList([{url:item.url,title:item.source || item.title}]);
    }
    for (const button of list.querySelectorAll('button'))button.setAttribute('aria-current',String(button.dataset.key===selected));
    if(play && (isLong || hasAudio))(isLong?video:audio).play().catch(()=>{status.textContent='Zum Abspielen bitte die Wiedergabetaste drücken.';});
  }
  function render() {
    const next=buildItems(broadcasts,updates,Date.now()/1000), nextSignature=JSON.stringify(next);
    if(nextSignature===signature)return;
    signature=nextSignature;items=next;
    const focusKey=document.activeElement?.dataset?.key;
    list.replaceChildren();
    document.getElementById('playlist-count').textContent=items.length+' Beiträge';
    for(const item of items){
      const li=document.createElement('li');li.className='playlist-row';
      const button=document.createElement('button');button.type='button';button.className='playlist-button';button.dataset.key=key(item);button.setAttribute('aria-current',String(selected===key(item)));
      const preview=document.createElement('span');preview.className='playlist-preview';preview.setAttribute('aria-hidden','true');preview.textContent=item.kind==='broadcast'?'▶':asset(item.audio,'update')?'♪':'≡';
      const type=document.createElement('small');type.textContent=item.kind==='broadcast'?'VIDEO':asset(item.audio,'update')?'AUDIO':'TEXT';preview.append(type);
      const copy=document.createElement('span');copy.className='playlist-copy';
      for(const [cls,value] of [['playlist-label',item.label],['playlist-title',item.title],['playlist-time',date(item.created_at)]]){const el=document.createElement('span');el.className=cls;el.textContent=value;copy.append(el);}
      button.append(preview,copy);button.addEventListener('click',()=>{status.textContent='';select(item,true);});li.append(button);list.append(li);
    }
    if(!items.length){const li=document.createElement('li');li.className='playlist-empty';li.textContent='Noch keine gespeicherten Beiträge.';list.append(li);}
    const current=items.find(item=>key(item)===selected);
    if(!current){const latest=items.find(i=>i.kind==='broadcast');if(latest)select(latest,false);else if(selected){video.pause();audio.pause();audio.hidden=true;text.hidden=false;text.textContent='Dieses Kurzupdate ist abgelaufen.';selected=null;}}
    if(focusKey){const button=[...list.querySelectorAll('button')].find(b=>b.dataset.key===focusKey);if(button)button.focus({preventScroll:true});}
  }
  async function refresh(){
    const results=await Promise.allSettled(['broadcasts.json','short-updates.json'].map(async url=>{const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error('Unavailable');return response.json();}));
    if(results[0].status==='fulfilled') broadcasts=Array.isArray(results[0].value.broadcasts) ? results[0].value.broadcasts : [];
    if(results[1].status==='fulfilled') updates=Array.isArray(results[1].value.updates) ? results[1].value.updates : [];
    status.textContent=results.some(r=>r.status==='rejected')?'Ein Teil der Playlist ist derzeit nicht verfügbar.':'';
    render();
  }
  refresh();setInterval(refresh,60000);setInterval(render,30000);
})(typeof window!=='undefined'?window:globalThis);
