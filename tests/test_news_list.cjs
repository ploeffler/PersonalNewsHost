const assert=require('node:assert/strict');
const {visibleArticles,labels}=require('../docs/news-list.js');
const now=2000000;
const items=[{id:'new',published_at:now-1},{id:'old',published_at:now-86400},{id:'future',published_at:now+1},{id:'undated',first_seen_at:now-10}];
assert.deepEqual(visibleArticles({articles:items},now).map(a=>a.id),['new','undated']);
assert.deepEqual(labels({broadcast_id:'last',broadcast_position:3,short_update_at:now-1},{id:'last',created_at:now-100}),['Letzte Sendung · Beitrag 3','Kurzupdate seit letzter Sendung']);
assert.deepEqual(labels({broadcast_id:'old',short_update_at:now-200},{id:'last',created_at:now-100}),[]);
console.log('News overview: age, sort order and both membership badges: OK');
