// Run from repo root; uses the same optional Playwright install as smoke.mjs.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve('site'),issues=[];
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 if(!p.startsWith('/cspace/'))return res.writeHead(404).end();
 let f=path.resolve(root,p.slice(8));
 if(!f.startsWith(root+path.sep)&&f!==root)return res.writeHead(403).end();
 if(fs.existsSync(f)&&fs.statSync(f).isDirectory())f=path.join(f,'index.html');
 if(!fs.existsSync(f))return res.writeHead(404).end();
 res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');fs.createReadStream(f).pipe(res);
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1360,height:1000},reducedMotion:'reduce'});
 page.on('pageerror',e=>issues.push(e.message));
 page.on('response',r=>{if(r.status()>=400)issues.push(`${r.status()} ${r.url()}`);});
 const origin=`http://127.0.0.1:${server.address().port}/cspace/`;
 // Keep canonical navigation local without modifying generated HTML.
 await page.route('https://yalkongs.github.io/cspace/**',async route=>{
  const response=await page.request.get(route.request().url().replace('https://yalkongs.github.io/cspace/',origin));
  await route.fulfill({response});
 });
 const slugs=['xyz','gamma','delta-e','rendering','gamut-mapping','appearance','halftone','thin-film'];
 fs.mkdirSync('/tmp/cspace-labs-review',{recursive:true});
 let controls=0;
 for(const lang of ['','ko/'])for(const slug of slugs){
  const route=`${lang}labs/${slug}/`;await page.goto(origin+route);
  await page.locator('#results .readout, #results .swatches, #results canvas').first().waitFor();
  const initial=await page.locator('#results').innerHTML();
  const inputs=page.locator('#controls input, #controls select');
  for(let i=0;i<await inputs.count();i++){
   const input=inputs.nth(i),tag=await input.evaluate(el=>el.tagName),type=await input.getAttribute('type');
   if(tag==='SELECT')await input.selectOption({index:1});
   else if(type==='color'){await input.fill('#258bc4');await input.dispatchEvent('input');}
   else for(const edge of ['min','max']){await input.fill(await input.getAttribute(edge));await input.dispatchEvent('input');}
   controls++;
   assert.ok(!/NaN|Infinity|undefined/.test(await page.locator('#results').innerText()),`${route} non-finite result`);
  }
  assert.notEqual(await page.locator('#results').innerHTML(),initial,`${route} did not react`);
  await page.locator('button[type=reset]').click();
  await page.waitForFunction(html=>document.getElementById('results').innerHTML===html,initial);
  const slider=page.locator('input[type=range]').first();
  await slider.focus();const old=await slider.inputValue();await page.keyboard.press(old===await slider.getAttribute('max')?'ArrowLeft':'ArrowRight');assert.notEqual(await slider.inputValue(),old);
  assert.ok(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),`${route} desktop overflow`);
  if(lang==='ko/'&&['gamma','thin-film','appearance'].includes(slug))await page.screenshot({path:`/tmp/cspace-labs-review/${slug}-desktop.png`,fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.ok(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),`${route} mobile overflow`);
  if(lang==='ko/'&&['gamma','rendering'].includes(slug))await page.screenshot({path:`/tmp/cspace-labs-review/${slug}-mobile.png`,fullPage:true});
  await page.setViewportSize({width:1360,height:1000});
 }
 await page.goto(origin+'ko/labs/');assert.equal(await page.locator('.card').count(),8);
 await page.screenshot({path:'/tmp/cspace-labs-review/hub.png',fullPage:true});
 await page.locator('.card').first().click();await page.waitForURL('**/ko/labs/xyz/');
 await page.locator('.masthead a[lang=en]').click();await page.waitForURL('**/labs/xyz/');
 await page.goto(origin+'ko/spaces/');assert.equal(await page.locator('.lab-related a[href*="/labs/"]').count(),5);
 await page.goto(origin+'ko/');await page.screenshot({path:'/tmp/cspace-labs-review/book-entry.png'});
 await page.locator('.reading-choices a[href$="/labs/"]').click();await page.waitForURL('**/ko/labs/');
 assert.deepEqual(issues,[]);
 console.log(`Labs: 16 bilingual experiment routes, ${controls} controls at boundaries, reset, keyboard, 16 mobile layouts, hub and chapter navigation passed.`);
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
