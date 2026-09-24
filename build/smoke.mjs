// Optional browser regression checks: PLAYWRIGHT_MODULE may point to an existing install.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve('site');
const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (!pathname.startsWith('/cspace/')) { res.writeHead(404).end(); return; }
  let file = path.resolve(root, pathname.slice('/cspace/'.length));
  if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file)) { res.writeHead(404).end(); return; }
  const ext = path.extname(file);
  res.setHeader('Content-Type', {'.html': 'text/html; charset=utf-8', '.png': 'image/png', '.pdf':'application/pdf'}[ext] || 'text/plain');
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
const errors = [];
try {
  browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const context = await browser.newContext({locale: 'en-US', reducedMotion: 'reduce'});
  const page = await context.newPage();
  let route = '';
  page.on('pageerror', e => errors.push(`${route}: ${e.message}`));
  page.on('response', r => { if (r.status() >= 400) errors.push(`${route}: HTTP ${r.status()} ${r.url()}`); });
  const langs = ['en','ko','ja','es','zh','fr','de','pt','it','vi','id'];
  const chapters = ['light','eye','mixing','wheel','space','harmony','spaces','interaction','practice','glossary','names','pigments','nature','practice2'];
  const routes = [...langs.map(l => l === 'en' ? '' : l + '/'), ...chapters.map(c => c + '/'), 'ko/light/', 'about/', 'cite/'];
  for (route of routes) {
    await page.goto(origin + '/cspace/' + route);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => {
      for (const input of document.querySelectorAll('input[type="range"]')) {
        input.value = String((Number(input.min || 0) + Number(input.max || 100)) / 2);
        input.dispatchEvent(new Event('input', {bubbles: true}));
      }
    });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    if (overflow) errors.push(`${route}: horizontal overflow`);
  }
  await page.goto(origin + '/cspace/ko/light/');
  await page.locator('#langTrigger').click();
  await page.locator('[data-lang="fr"]').click();
  await page.waitForURL('**/cspace/fr/light/');
  if (await page.locator('#langTriggerCode').textContent() !== 'FR') errors.push('Language selection did not preserve chapter/current code');
  await context.clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.setViewportSize({width: 390, height: 844});
  for (route of ['', 'ko/', 'fr/']) {
    await page.goto(origin + '/cspace/' + route);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    if (overflow) {
      const nodes = await page.evaluate(() => [...document.querySelectorAll('body *')].map(el => ({tag:el.tagName, id:el.id, cls:el.className?.baseVal ?? el.className, right:el.getBoundingClientRect().right, width:el.getBoundingClientRect().width})).filter(el => el.right > innerWidth + 1 && el.width > 0).slice(0, 12));
      errors.push(`${route}: mobile horizontal overflow ${JSON.stringify(nodes)}`);
    }
  }
  console.log(`Browser checked ${routes.length} routes, range controls, chapter-preserving language switch, and 3 mobile pages.`);
  if (errors.length) throw new Error([...new Set(errors)].join('\n'));
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
