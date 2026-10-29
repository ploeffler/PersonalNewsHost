'use strict';
(()=>{
const $=id=>document.getElementById(id);let report=null,signature='';
const issues={unsupported_headline:'Überschrift ist nicht durch die angegebene Quelle gedeckt.',no_supported_prose:'Kein ausreichend belegter Nachrichtentext vorhanden.',unverified_rendered_text:'Der ausgegebene Text enthält ungeprüfte Änderungen.',invalid_source_reference:'Ungültiger Quellenbezug.',conflicting_source_values:'Quellen nennen abweichende Zahlen.',event_membership_not_supported:'Die gemeinsame Ereigniszuordnung ist nicht ausreichend belegt.'};
const text=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el;};
function render(){
if(!report)return;const groups=report.groups||[],approved=groups.filter(g=>g.verification.status==='approved'),chosen=groups.filter(g=>g.selected);
$('report-mode').textContent=(report.mode==='preview'?'Vorschau – noch nicht als Sendung produziert':'Produktionsprüfung')+' · '+new Date(report.generated_at*1000).toLocaleString('de-AT');
$('report-summary').textContent=groups.length+' Ereignisgruppen · '+approved.length+' mit bestandenem Quellenabgleich · '+(groups.length-approved.length)+' zurückgestellt · '+chosen.length+' ausgewählt';
const mode=$('report-filter').value,query=$('report-search').value.toLocaleLowerCase('de');const container=$('report-groups');container.replaceChildren();
for(const group of groups){if(mode==='selected'&&!group.selected||mode==='held'&&group.verification.status!=='held'||mode==='approved'&&group.verification.status!=='approved')continue;
if(query&&!((group.draft.headline||'')+' '+(group.draft.text||'')).toLocaleLowerCase('de').includes(query))continue;
const card=document.createElement('article');card.className='report-card';const badges=document.createElement('div');badges.className='badges';
badges.append(text('span',group.verification.status==='approved'?'Quellenabgleich bestanden':'Zurückgestellt','badge'+(group.verification.status==='held'?' held':'')));if(group.selected)badges.append(text('span','Für Produktion ausgewählt','badge selected'));
card.append(badges,text('h2',group.draft.headline),text('p',group.draft.text,'draft'),text('p',group.member_ids.length+' gespeicherte Quelle(n) · '+(group.used_source_ids||[]).length+' Quelle(n) im gemeinsamen Text','meta'));
if(group.attempts.length>1)card.append(text('p','Nach einer Korrektur erneut geprüft.','meta'));
for(const issue of group.verification.issues)card.append(text('p',issue.startsWith('unsupported_claim:')?'Ein Satz ist nicht vollständig durch seine Quelle gedeckt.':issues[issue]||issue));
for(const conflict of group.verification.conflicts||[])card.append(text('p','Abweichende Zahlen ('+(conflict.metric==='injured'?'Verletzte':'Tote')+'): '+conflict.values.map(v=>(report.sources[v.source_id]?.publisher||v.source_id)+': '+v.value).join(' / ')));
const evidence=document.createElement('details');evidence.append(text('summary','Satzbelege und gespeicherte Quellen anzeigen'));
for(const claim of group.verification.claims){const source=report.sources[claim.source_id];evidence.append(text('p','Satz '+(claim.claim_index+1)+' · '+(claim.supported?'Beleg vorhanden':'Nicht belegt')+' · '+(source?.publisher||claim.source_id),'meta'),text('p',claim.quote||'','quote'));}
for(const id of group.member_ids){const source=report.sources[id];if(!source)continue;const block=document.createElement('div');block.className='source';block.append(text('h3',source.title),text('p',source.text||'Kein Nachrichtentext gespeichert.'));
if(/^https?:\/\//i.test(source.url||'')){const link=text('a',source.publisher||source.url);link.href=source.url;link.rel='noopener noreferrer';block.append(link);}evidence.append(block);}
card.append(evidence);container.append(card);
}
if(!container.children.length)container.append(text('p','Keine Ereignisgruppen für diese Auswahl.'));
}
async function load(){try{const response=await fetch('editorial-report.json',{cache:'no-cache'});if(!response.ok)throw Error('Unavailable');const next=await response.json();if(!Array.isArray(next.groups)||!next.sources)throw Error('Invalid');const hash=JSON.stringify(next);if(hash===signature)return;signature=hash;report=next;render();}catch{$('report-summary').textContent='Noch kein lesbarer redaktioneller Prüfbericht veröffentlicht.';}}
$('report-filter').addEventListener('change',render);$('report-search').addEventListener('input',render);load();setInterval(load,60000);
})();
