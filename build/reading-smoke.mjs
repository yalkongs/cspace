import {createRequire} from 'node:module';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve('site'),errors=[];
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 if(!p.startsWith('/cspace/'))return res.writeHead(404).end();
 let file=path.resolve(root,p.slice(8));
 if(!file.startsWith(root+path.sep)&&file!==root)return res.writeHead(403).end();
 if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
 if(!fs.existsSync(file))return res.writeHead(404).end();
 res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}/cspace/`;
let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const context=await browser.newContext({viewport:{width:1360,height:1000},reducedMotion:'reduce'});
 context.setDefaultTimeout(15000);context.setDefaultNavigationTimeout(20000);
 async function localRoutes(ctx){await ctx.route('https://yalkongs.github.io/cspace/**',async route=>{const response=await ctx.request.get(route.request().url().replace('https://yalkongs.github.io/cspace/',origin));await route.fulfill({response});});}
 await localRoutes(context);
 const page=await context.newPage();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 fs.mkdirSync('/tmp/cspace-reading-review',{recursive:true});
 const langs=['','ko/','ja/','es/','zh/','fr/','de/','pt/','it/','vi/','id/'];
 const slugs=['light','eye','mixing','wheel','space','harmony','spaces','interaction','practice','glossary','names','pigments','nature','practice2'];
 const overflow=()=>page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
 for(const lang of langs){
  await page.goto(origin+lang);assert.equal(await page.locator('section.chapter').count(),0);assert.equal(await page.locator('.reading-choices a').count(),3);assert.ok(!await overflow(),`${lang} cover overflow`);
  if(lang==='ko/')await page.screenshot({path:'/tmp/cspace-reading-review/cover-desktop.png'});
  await page.goto(origin+lang+'book/');assert.equal(await page.locator('section.chapter').count(),16);
  await page.goto(origin+lang+'spaces/');assert.equal(await page.locator('section.chapter').count(),1);assert.equal(await page.locator('.reading-sections nav a').count(),5);
  await page.setViewportSize({width:390,height:844});
  for(const menu of ['.reading-menu:first-child','.reading-sections']){
   await page.locator(menu+' summary').click();assert.ok(!await overflow(),`${lang} open menu overflow`);
   const bounds=await page.locator(menu+' nav').boundingBox();assert.ok(bounds.x>=0&&bounds.x+bounds.width<=391,`${lang} menu outside viewport`);
   await page.keyboard.press('Escape');
  }
  await page.setViewportSize({width:1360,height:1000});
 }
 for(const slug of slugs){await page.goto(origin+slug+'/');assert.equal(await page.locator('section.chapter').count(),1);assert.equal(await page.locator('h1').count(),1);assert.equal(await page.locator('.reading-pager a').count(),2);}
 await page.goto(origin+'ko/');await page.locator('.reading-start').click();await page.waitForURL('**/ko/light/');
 await page.locator('.reading-next').click();await page.waitForURL('**/ko/eye/');
 await page.locator('.reading-prev').click();await page.waitForURL('**/ko/light/');
 await page.locator('.reading-menu:first-child summary').click();await page.locator('.reading-menu:first-child a[href$="/spaces/"]').click();await page.waitForURL('**/ko/spaces/');
 await page.locator('.reading-sections summary').focus();await page.keyboard.press('Enter');
 await page.locator('.reading-sections a[href="#fig-gamut"]').click();await page.waitForURL('**/#fig-gamut');
 const assertAnchor=async()=>{await page.waitForFunction(()=>{const target=document.getElementById(location.hash.slice(1));return target&&target.getBoundingClientRect().top>=document.getElementById('reading-tools').getBoundingClientRect().bottom-2&&target.getBoundingClientRect().top<innerHeight;});};
 await assertAnchor();await page.reload();await assertAnchor();
 await page.goBack();await page.waitForURL('**/ko/spaces/');
 await page.locator('#langTrigger').click();await page.locator('[data-lang=fr]').click();await page.waitForURL('**/fr/spaces/');
 await page.goto(origin+'ko/spaces/');await page.screenshot({path:'/tmp/cspace-reading-review/chapter-desktop.png'});
 console.log('Reading route and mini-contents checks passed; checking mode switching.');
 await page.locator('.reading-mode-switch').click();await page.waitForURL('**/ko/book/#spaces');
 await page.locator('#langTrigger').click();await page.locator('[data-lang=en]').click();await page.waitForURL('**/book/#spaces');
 await page.waitForFunction(()=>document.getElementById('reading-chapter-switch').href.endsWith('/spaces/')).catch(async error=>{console.error(await page.evaluate(()=>({url:location.href,switch:document.getElementById('reading-chapter-switch').href,y:scrollY,top:document.getElementById('spaces').getBoundingClientRect().top})));throw error;});
 await page.locator('#reading-chapter-switch').click();await page.waitForURL('**/spaces/');
 // Old chapter, figure, appendix links retain their destination; no cover loop.
 for(const [hash,target] of [['spaces','ko/spaces/#spaces'],['fig-prism','ko/light/#fig-prism'],['chronology','ko/book/#chronology'],['coda','ko/book/#coda']]){
  await page.goto(origin+'ko/#'+hash);await page.waitForURL('**/'+target);
 }
 await page.setViewportSize({width:390,height:844});await page.goto(origin+'ko/');await page.screenshot({path:'/tmp/cspace-reading-review/cover-mobile.png',fullPage:true});
 await page.goto(origin+'ko/spaces/');await page.locator('.reading-sections summary').click();await page.screenshot({path:'/tmp/cspace-reading-review/menu-mobile.png'});
 await page.locator('.reading-sections a[href="#fig-gamut"]').click();await assertAnchor();await page.screenshot({path:'/tmp/cspace-reading-review/figure-mobile.png'});
 await page.locator('.reading-next').scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/cspace-reading-review/pager-mobile.png'});
 assert.ok(!await overflow());
 // Native links and <details> remain usable without JavaScript.
 const nojs=await browser.newContext({javaScriptEnabled:false,reducedMotion:'reduce',viewport:{width:390,height:844}});nojs.setDefaultTimeout(15000);await localRoutes(nojs);const staticPage=await nojs.newPage();
 await staticPage.goto(origin+'ko/');await staticPage.locator('.reading-start').click();await staticPage.waitForURL('**/ko/light/');
 await staticPage.locator('.reading-sections summary').click();await staticPage.locator('.reading-sections a[href="#fig-prism"]').click();await staticPage.waitForURL('**/#fig-prism');
 // Without JavaScript the native disclosure stays open until the reader closes it.
 await staticPage.locator('.reading-sections summary').click();
 await staticPage.locator('.reading-next').click();await staticPage.waitForURL('**/ko/eye/');
 assert.deepEqual(errors,[]);
 console.log('Reading: 11 language covers/books/chapters, 14 chapter routes, mobile menus, mini-contents, previous/next, refresh/back, mode-preserving language switch, legacy links and no-JS navigation passed.');
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
