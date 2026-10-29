(function(root){
'use strict';
const age=a=>a.published_at&&a.first_seen_at?Math.min(a.published_at,a.first_seen_at):(a.published_at||a.first_seen_at);
function visibleArticles(data,now){return (Array.isArray(data.articles)?data.articles:[]).filter(a=>{
const t=age(a);return Number.isFinite(t)&&t<=now&&(!a.published_at||a.published_at<=now)&&t>now-86400;
}).sort((a,b)=>age(b)-age(a));}
function labels(article,latest){const result=[];
if(latest.id && article.broadcast_id===latest.id)result.push('Letzte Sendung · Beitrag '+article.broadcast_position);
if(latest.created_at && article.short_update_at>latest.created_at)result.push('Kurzupdate seit letzter Sendung');
return result;}
if(typeof module!=='undefined'&&module.exports)module.exports={visibleArticles,labels};
if(!root.document)return;
const doc=root.document,container=doc.getElementById('news-articles');if(!container)return;
let data={articles:[],feeds:[],latest_broadcast:{}},signature=null;
const date=t=>new Date(t*1000).toLocaleString('de-AT',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
function link(url,title){const a=doc.createElement('a');a.href=url;a.rel='noopener noreferrer';a.textContent=title;return a;}
function render(){
const articles=visibleArticles(data,Date.now()/1000),next=JSON.stringify([articles,data.feeds,data.latest_broadcast]);if(next===signature)return;signature=next;
container.replaceChildren();doc.getElementById('news-count').textContent=articles.length+' Meldungen · letzte 24 Stunden';
const names=new Map((data.feeds||[]).map(f=>[f.url,f.name]));
for(const article of articles){
const card=doc.createElement('article');card.className='news-card';
const flags=doc.createElement('div');flags.className='news-badges';
for(const label of labels(article,data.latest_broadcast||{})){const badge=doc.createElement('span');badge.className='news-badge'+(label.startsWith('Kurzupdate')?' news-badge-update':'');badge.textContent=label;flags.append(badge);}
const title=doc.createElement('h3');if(/^https?:\/\//i.test(article.url||''))title.append(link(article.url,article.title));else title.textContent=article.title;
const body=doc.createElement('p');body.className='news-text';body.textContent=article.text || 'Zu dieser Meldung ist kein Nachrichtentext gespeichert.';
const meta=doc.createElement('p');meta.className='news-meta';meta.textContent=(article.published_at?'Veröffentlicht: ':'Erfasst: ')+date(article.published_at||article.first_seen_at);
const feeds=[...new Set((article.feed_urls||[]).map(url=>names.get(url)).filter(Boolean))];if(feeds.length)meta.textContent+=' · '+feeds.join(' · ');
card.append(flags,title,body,meta);container.append(card);
}
if(!articles.length){const p=doc.createElement('p');p.className='news-empty';p.textContent='Keine gespeicherten Nachrichten aus den letzten 24 Stunden.';container.append(p);}
const list=doc.getElementById('rss-source-list');list.replaceChildren();
for(const feed of [...(data.feeds||[])].sort((a,b)=>String(a.name).localeCompare(String(b.name),'de'))){const li=doc.createElement('li');if(/^https?:\/\//i.test(feed.url||''))li.append(link(feed.url,feed.name||feed.url));else li.textContent=feed.name||'';list.append(li);}
}
async function refresh(){try{const response=await fetch('news-store.json',{cache:'no-cache'});if(!response.ok)throw Error('Unavailable');data=await response.json();render();doc.getElementById('news-status').textContent='';}catch{doc.getElementById('news-status').textContent='Die Nachrichtenübersicht ist derzeit nicht verfügbar.';render();}}
refresh();setInterval(refresh,60000);setInterval(render,30000);
})(typeof window!=='undefined'?window:globalThis);
