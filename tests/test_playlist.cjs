const assert=require('node:assert/strict');
const {buildItems,asset}=require('../docs/playlist.js');
const now=2000000;
const b=(id,t)=>({id,title:id,created_at:t,video:'broadcasts/20261029T093244Z.mp4'});
const u=(id,t)=>({id:id.repeat(24),title:id,created_at:t});
const rows=buildItems([b('earliest',now-80000),b('previous',now-5000),b('latest',now-1000)],
 [u('a',now-4000),u('b',now-500),u('c',now-86400),u('d',now-6000),u('e',now+1)],now);
assert.deepEqual(rows.map(r=>r.title),['previous','a','latest','b']);
assert.equal(rows[0].label,'Vorherige Sendung');assert.equal(rows[2].label,'Neueste Sendung');
assert.equal(buildItems([],Array.from({length:7},(_,i)=>u(String(i),now-i)),now).length,5);
assert.equal(asset('https://evil.test/file.mp4','broadcast'),false);
assert.equal(asset('broadcasts/../../config.json','broadcast'),false);
assert.equal(asset('short-update-audio/'+'a'.repeat(24)+'.wav','update'),true);
assert.equal(asset('short-update-audio/not-an-id.wav','update'),false);
console.log('Playlist ordering, retention, media-path safety: OK');
