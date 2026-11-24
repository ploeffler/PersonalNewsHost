// Clientseitige Suche (T031): Treffer ohne Serveraufruf, Umlaute/Groß-Kleinschreibung, Gewichtung.
const assert=require('node:assert/strict');
const {search}=require('../docs/search.js');
const index={entries:[
 {k:'a',title:'Inflation sinkt',text:'Die Preise',section:'Wirtschaft',source:'news.example',url:'a.html',date:1},
 {k:'a',title:'Bürgermeister gewählt',text:'Inflation im Rathaus',section:'Lokales',source:'x.at',url:'b.html',date:2},
 {k:'b',title:'Nachrichten 7 Uhr',text:'Inflation sinkt',section:'main',source:'',url:'v.mp4',date:3}]};
assert.deepEqual(search(index,'inflation').map(e=>e.url),['a.html','v.mp4','b.html']);
assert.deepEqual(search(index,'BUERGERMEISTER').map(e=>e.url),['b.html']);
assert.deepEqual(search(index,'bürgermeister rathaus').map(e=>e.url),['b.html']);
assert.deepEqual(search(index,'nichtvorhanden'),[]);
assert.deepEqual(search(index,'   '),[]);
assert.deepEqual(search(null,'x'),[]);
assert.equal(search(index,'inflation',1).length,1);
console.log('search ok');
