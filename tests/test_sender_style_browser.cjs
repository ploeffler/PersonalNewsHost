// End-to-end against a real local server; no AI calls or public website traffic.
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),net=require('node:net');
(async()=>{
 const root=path.resolve(__dirname,'..');const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pnh-style-browser-'));
 const port=await new Promise(resolve=>{const server=net.createServer();server.listen(0,'127.0.0.1',()=>{const p=server.address().port;server.close(()=>resolve(p));});});
 const child=spawn(process.env.PYTHON||'python3',['scripts/sender_style_server.py','--state',temp,'--port',String(port)],{cwd:root,env:{...process.env,PNH_STYLE_ADMIN_PASSWORD:'browser-fixture-password-123',PNH_STYLE_IMAGE_PROVIDER:'none'}});
 let output='';child.stdout.on('data',b=>output+=b);child.stderr.on('data',b=>output+=b);
 let browser;
 try{
  const base='http://127.0.0.1:'+port;
  for(let i=0;i<100;i++){try{const r=await fetch(base);if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error('Server did not start: '+output);}
  browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1280,height:950}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(base);await page.locator('#password').fill('browser-fixture-password-123');await page.locator('#login_form button').click();await page.waitForSelector('#workspace:not([hidden])');
  assert.ok(await page.locator('#editor').isVisible());await page.locator('#name').fill('Wiesenfunk');await page.locator('#audience').fill('Menschen aus der Region');await page.locator('#visual_direction').fill('Warme Holzfarben und ruhige Bildsprache');await page.locator('#colors').fill('#214f43, #e9b94a, #f4f1e8');
  await page.route(base+'/api/research',route=>route.fulfill({json:{suggested_patch:{colors:['#214f43','#e9b94a','#f4f1e8'],font_family:'Georgia, serif'},sources:[{url:'https://fixture.example',retrieved_at:1700000000}],findings:[],warnings:[],note:'Quoted website research'}}));
  await page.locator('#website').fill('https://fixture.example');await page.locator('#research').click();await page.waitForSelector('#apply_research:not([hidden])');await page.locator('#apply_research').click();assert.equal(await page.locator('#font_family').inputValue(),'Georgia, serif');assert.match(await page.locator('#active_info').textContent(),/Noch kein Basisstil/);
  await page.locator('#save').click();await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Entwurf gespeichert'));
  await page.reload();await page.waitForSelector('#workspace:not([hidden])');assert.equal(await page.locator('#name').inputValue(),'Wiesenfunk');
  await page.locator('#adopt').click();await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Basisstil übernommen'));
  await page.waitForSelector('#batches .tile');assert.equal(await page.locator('#batches .tile').count(),14);assert.match(await page.locator('#active_info').textContent(),/Aktive CI/);
  await page.locator('#editor').evaluate(e=>e.hidden=true);await page.locator('#edit').click();assert.ok(await page.locator('#editor').isVisible());
  assert.ok(await page.locator('#export').isEnabled());
  if(process.env.PNH_STYLE_SCREENSHOT){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:process.env.PNH_STYLE_SCREENSHOT.replace('.png','-desktop.png'),fullPage:false});}
  // Repeated unchanged adoption must reuse the same series.
  await page.locator('#adopt').click();await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Basisstil übernommen'));assert.equal(await page.locator('#batches .batch').count(),1);
  // Polling must not reset dirty form or silently upgrade its CAS revision.
  await page.locator('#name').fill('Ungespeicherter Entwurf');await page.locator('#refresh').click();await page.waitForTimeout(300);assert.equal(await page.locator('#name').inputValue(),'Ungespeicherter Entwurf');
  const sessionState=await page.evaluate(async()=>await (await fetch('/api/state')).json());
  await page.evaluate(async s=>{await fetch('/api/draft',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':s.csrf},body:JSON.stringify({revision:s.revision,draft:{...s.draft,name:'Anderes Fenster'}})});},sessionState);
  await page.locator('#refresh').click();await page.waitForTimeout(300);await page.locator('#save').click();await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('anderweitig'));
  await page.setViewportSize({width:390,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(process.env.PNH_STYLE_SCREENSHOT)await page.screenshot({path:process.env.PNH_STYLE_SCREENSHOT,fullPage:true});
  assert.deepEqual(errors,[]);await page.locator('#logout').click();await page.waitForSelector('#login:not([hidden])');
  console.log('Sender style browser: login/setup, draft/reload, 14 automatic jobs, idempotency, editor button, CAS conflict, mobile, logout: OK');
 }finally{if(browser)await browser.close();child.kill('SIGTERM');await new Promise(r=>child.once('exit',r));fs.rmSync(temp,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exit(1);});
