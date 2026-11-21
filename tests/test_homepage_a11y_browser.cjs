// Start page: automated accessibility check (axe-core) in light and dark mode, keyboard theme switch (T021).
// Usage: SITE_DIR=<docs copy refreshed by scripts/homepage.py> node tests/test_homepage_a11y_browser.cjs
const {chromium}=require('playwright-core'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const axeSource=fs.readFileSync(require.resolve('axe-core/axe.min.js'),'utf8');
const root=path.resolve(process.env.SITE_DIR||path.join(__dirname,'../docs'));
const types={html:'text/html',js:'application/javascript',json:'application/json',css:'text/css',png:'image/png',svg:'image/svg+xml'};
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
  const failures=[];
  for(const colorScheme of ['light','dark']){
    const page=await browser.newPage({viewport:{width:1280,height:1000},colorScheme});
    await page.route('**/*',route=>{
      const url=new URL(route.request().url());
      if(url.hostname==='raw.githubusercontent.com')return route.fulfill({body:fs.readFileSync(path.join(__dirname,'..','assets','logo.png')),contentType:'image/png'});
      if(url.hostname!=='site.test')return route.abort();
      if(/\.(mp4|wav)$/.test(url.pathname))return route.fulfill({body:Buffer.alloc(0),contentType:'video/mp4'});
      const file=path.join(root,url.pathname==='/'?'index.html':decodeURIComponent(url.pathname));
      if(!file.startsWith(root)||!fs.existsSync(file))return route.fulfill({status:404,body:'missing'});
      return route.fulfill({body:fs.readFileSync(file),contentType:types[file.split('.').pop()]||'text/plain'});
    });
    await page.goto('https://site.test/');
    await page.waitForLoadState('networkidle');
    for(const selector of ['#bulletin-video','#ressorts','#latest-posts','#breaking-banner','#news-overview'])
      assert.equal(await page.locator(selector).count(),1,selector+' missing');
    await page.addScriptTag({content:axeSource});
    const result=await page.evaluate(async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}}));
    for(const v of result.violations){
      const line=`${colorScheme}: ${v.impact} ${v.id} (${v.nodes.length}) ${v.nodes.slice(0,3).map(n=>n.target.join(' ')).join(' | ')}`;
      console.log(line);
      if(v.impact==='critical'||v.impact==='serious')failures.push(line);
    }
    await page.screenshot({path:path.join(require('node:os').tmpdir(),`pnh-home-${colorScheme}.png`),fullPage:true});
    // Keyboard: the theme switch is reachable and works with Enter.
    const toggle=page.locator('#theme-toggle');
    await toggle.focus();
    const before=await page.evaluate(()=>getComputedStyle(document.body).backgroundColor);
    await page.keyboard.press('Enter');
    const after=await page.evaluate(()=>getComputedStyle(document.body).backgroundColor);
    assert.notEqual(before,after,'theme switch has no effect');
    await page.close();
  }
  await browser.close();
  assert.deepEqual(failures,[],'axe: critical or serious violations');
  console.log('Start page accessibility: no critical or serious violations');
})().catch(e=>{console.error(e);process.exit(1);});
