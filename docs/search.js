(function(root){
'use strict';
const fold=s=>String(s||'').toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const words=q=>fold(q).split(/[^a-z0-9]+/).filter(Boolean);
function search(index,query,limit){
const terms=words(query);if(!terms.length)return [];
const hits=[];
for(const e of (index&&Array.isArray(index.entries)?index.entries:[])){
const title=fold(e.title),rest=fold([e.text,e.section,e.source].join(' '));let score=0,ok=true;
for(const t of terms){const inTitle=title.includes(t),inRest=rest.includes(t);if(!inTitle&&!inRest){ok=false;break;}score+=inTitle?3:1;}
if(ok)hits.push({e,score});
}
hits.sort((a,b)=>b.score-a.score||(b.e.date||0)-(a.e.date||0));
return hits.slice(0,limit||50).map(h=>h.e);
}
if(typeof module!=='undefined'&&module.exports)module.exports={search,fold};
if(!root.document)return;
const doc=root.document,input=doc.getElementById('q'),out=doc.getElementById('results'),status=doc.getElementById('status');
if(!input||!out)return;
let index=null;
const safe=u=>/^https?:\/\//i.test(u)||/^[A-Za-z0-9_\-\/.]+$/.test(u);
function render(){
const query=input.value.trim();out.replaceChildren();
if(!index){return;}
if(!query){status.textContent=index.entries.length+' Einträge durchsuchbar.'+(index.truncated?' (ältere Einträge nicht im Index)':'');return;}
const found=search(index,query);status.textContent=found.length+' Treffer';
for(const e of found){const li=doc.createElement('li');
const a=doc.createElement('a');a.textContent=e.title;if(safe(e.url)){a.href=e.url;if(/^https?:/i.test(e.url))a.rel='noopener noreferrer';}li.append(a);
const meta=doc.createElement('span');meta.className='block-meta';
meta.textContent=(e.k==='b'?'Sendung':'Beitrag')+(e.section?' · '+e.section:'')+(e.source?' · '+e.source:'')+(e.date?' · '+new Date(e.date*1000).toLocaleDateString('de-AT'):'');
li.append(meta);if(e.text){const p=doc.createElement('p');p.textContent=e.text;li.append(p);}out.append(li);}
}
fetch('search-index.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('x');return r.json();}).then(d=>{index=d;render();}).catch(()=>{status.textContent='Der Suchindex ist derzeit nicht verfügbar.';});
input.addEventListener('input',render);
})(typeof window!=='undefined'?window:globalThis);
