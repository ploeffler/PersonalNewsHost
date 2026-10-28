const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {selections, publicUrl, regionOf, catalogueEntries, matches, sourceLogo} = require('../docs/feed-picker.js');
const selected = new Set(['https://example.org/old']);
assert.deepEqual(selections('https://example.org\nhttps://example.org/\n\nhttps://own.example/rss'), ['https://example.org/','https://own.example/rss']);
for (const url of ['javascript:alert(1)','https://user:secret@example.org/rss','http://example.org/rss','https://localhost/rss']) assert.equal(publicUrl(url),null);
assert.equal(regionOf({url:'https://rss.orf.at/steiermark.xml'}),'Steiermark');
assert.equal(regionOf({url:'https://www.tagesschau.de/inland/regional/bayern/index~rss2.xml',publisher_country:'DE'}),'Bayern');
assert.equal(regionOf({url:'https://example.org/rss',region:'Berlin/Brandenburg'}),'Berlin/Brandenburg');
const rows = catalogueEntries({feeds:[{url:'https://example.org/warn',requires_warning_adapter:true},{url:'javascript:alert(1)'}], non_feed_sources:[{url:'https://example.org/portal'}]},'authorities');
assert.equal(rows.length,2);assert.ok(rows.every(r=>r.blocked));
assert.equal(matches({url:'https://example.org/old',status:'review',region:'Steiermark'}, {review:false},selected),true);
assert.equal(matches({url:'https://example.org/new',status:'review',region:'Steiermark'}, {review:false},selected),false);
assert.equal(matches({url:'https://example.org/rss',region:'Berlin/Brandenburg'}, {region:'Berlin'},new Set()),true);
const docs = path.resolve(__dirname,'../docs');
for (const [file,group] of [['feed-catalog.json','news'],['police-feed-catalog.json','authorities']]) {
  const entries = catalogueEntries(JSON.parse(fs.readFileSync(path.join(docs,file),'utf8')),group);
  assert.ok(entries.length>100);
  assert.ok(entries.every(e=>e.region && e.url.startsWith('https://')));
}
const icons=JSON.parse(fs.readFileSync(path.join(docs,'assets/regions/index.json'),'utf8'));
assert.equal(Object.keys(icons.AT).length,9);assert.equal(Object.keys(icons.DE).length,16);
for(const regions of Object.values(icons))for(const asset of Object.values(regions))assert.ok(fs.existsSync(path.join(docs,asset.icon)));
console.log('Feed picker: URL safety, selection preservation, region matching, warning restrictions and all 25 icon files verified.');

assert.equal(sourceLogo({url:'https://example.org/rss'},{'example.org':{status:'cached',icon:'assets/source-logos/abcd.png'}}).host,'example.org');
assert.equal(sourceLogo({url:'https://example.org/rss'},{'example.org':{status:'cached',icon:'https://external.example/icon.png'}}),null);
assert.equal(sourceLogo({url:'https://own.example/rss'},{}),null);
assert.equal(sourceLogo({source_page:'https://publisher.example/',url:'https://rss.example/rss'},{'publisher.example':{status:'cached',icon:'assets/source-logos/1234.ico'}}).host,'publisher.example');
console.log('Local publisher favicon selection and missing-icon fallback verified.');
