import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';

const root = path.resolve(process.argv[2] || 'site');
const base = new URL((process.argv[3] || 'https://yalkongs.github.io/cspace').replace(/\/$/, '') + '/');
const files = fs.readdirSync(root, {recursive: true}).filter(p => p.endsWith('.html'));
const checkedScripts = new Set();
const errors = [];
for (const file of files) {
  const html = fs.readFileSync(path.join(root, file), 'utf8');
  const fail = message => errors.push(`${file}: ${message}`);
  if (html.includes('cspace-beryl.vercel.app')) fail('Legacy site URL remains');
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const key = crypto.createHash('sha256').update(m[0]).digest('hex');
    if (checkedScripts.has(key)) continue;
    checkedScripts.add(key);
    try {
      if (m[1].includes('ld+json')) JSON.parse(m[2]);
      else new vm.Script(m[2], {filename: file});
    } catch (e) { fail(e.message); }
  }
  const canonicals = [...html.matchAll(/<link rel="canonical" href="([^"]+)"/g)];
  if (file !== '404.html') {
    const relative = file.replace(/index\.html$/, '').replace(/^en\//, '');
    const expected = new URL(relative, base).href;
    if (canonicals.length !== 1 || canonicals[0][1] !== expected) fail(`Expected canonical ${expected}`);
  }
  const langs = [...html.matchAll(/hreflang="([^"]+)"/g)].map(m => m[1]);
  if (new Set(langs).size !== langs.length) fail('Duplicate hreflang');
  for (const m of html.matchAll(/\b(?:href|src)=("|')([^"']*)\1/g)) {
    const value = m[2];
    if (!value || /^(data:|mailto:|javascript:|#)/.test(value)) continue;
    const url = new URL(value, new URL(file, base));
    if (url.origin !== base.origin) continue;
    if (!url.pathname.startsWith(base.pathname)) { fail(`Link escapes project path: ${value}`); continue; }
    const target = path.join(root, decodeURIComponent(url.pathname.slice(base.pathname.length)));
    if (!fs.existsSync(target)) fail(`Missing link target: ${value}`);
    else if (fs.statSync(target).isDirectory() && !fs.existsSync(path.join(target, 'index.html'))) fail(`Missing directory index: ${value}`);
  }
}
const sitemap = path.join(root, 'sitemap.xml');
if (fs.existsSync(sitemap)) {
  for (const m of fs.readFileSync(sitemap, 'utf8').matchAll(/<loc>(.*?)<\/loc>/g)) {
    const url = new URL(m[1]);
    const target = path.join(root, url.pathname.slice(base.pathname.length), 'index.html');
    if (!url.href.startsWith(base.href) || !fs.existsSync(target)) errors.push(`sitemap: missing ${url.href}`);
  }
}
if (errors.length) {
  console.error([...new Set(errors)].join('\n'));
  process.exit(1);
}
console.log(`Validated ${files.length} HTML pages, ${checkedScripts.size} unique scripts/JSON-LD blocks, internal assets and routes.`);
