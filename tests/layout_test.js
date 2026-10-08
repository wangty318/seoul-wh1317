/* 網址配置測試：短網址（根目錄導向頁）與正式網址（seoul-pwa/）都要能開，且 hash 路由與離線都正常。
 * 用法：  NODE_PATH=$(npm root -g) node tests/layout_test.js
 * 直接服務 repo 目前的內容（唯讀），放在 /seoul-wh1317/ 子路徑下，跟 GitHub Pages 一樣。 */
let chromium;
try { ({ chromium } = require('playwright')); } catch (_) { ({ chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright')); }
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), PORT = 8766, PREFIX = '/seoul-wh1317/';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
let server;
const start = () => new Promise(r => { server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x');
  if (!u.pathname.startsWith(PREFIX)) { res.writeHead(404); return res.end(); }
  let rel = u.pathname.slice(PREFIX.length); if (rel === '' || rel.endsWith('/')) rel += 'index.html';
  const f = path.join(ROOT, rel);
  if (!f.startsWith(ROOT) || rel.startsWith('src/') || rel.startsWith('.git')) { res.writeHead(404); return res.end(); }
  fs.readFile(f, (e, b) => { if (e) { res.writeHead(404); return res.end('nf'); } res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'public, max-age=600' }); res.end(b); });
}); server.listen(PORT, '127.0.0.1', r); });
const stop = () => new Promise(r => { server.closeAllConnections(); server.close(r); });
const results = [], ok = (n, c, x) => results.push([c ? 'PASS' : 'FAIL', n, x === undefined ? '' : String(x)]);

(async () => {
  await start();
  const b = await chromium.launch();
  const base = `http://127.0.0.1:${PORT}${PREFIX}`;
  for (const [label, url] of [['短網址（根目錄導向頁）', base + '?from=link#routes-d2'], ['正式網址 seoul-pwa/', base + 'seoul-pwa/#routes-d2']]) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    const p = await ctx.newPage();
    await p.goto(url);
    await p.waitForFunction(() => document.querySelector('.offl') && document.querySelector('.offl').textContent.includes('✓'), null, { timeout: 15000 }).catch(() => {});
    ok(label + '：最後停在 seoul-pwa/ 且帶著 #routes-d2', new URL(p.url()).pathname === PREFIX + 'seoul-pwa/' && new URL(p.url()).hash.startsWith('#routes-d2'), p.url());
    ok(label + '：顯示 D2 路線頁', await p.evaluate(() => { const e = document.getElementById('p-d2'); return !!e && !e.hidden; }));
    ok(label + '：出現「✓ 離線可用」', (await p.locator('.offl').innerText().catch(() => '')).includes('✓'));
    await stop();
    await p.goto(base + 'seoul-pwa/', { waitUntil: 'load' }).catch(() => {});
    ok(label + '：斷網後重新開啟 seoul-pwa/ 仍可用', (await p.title().catch(() => '')) === '首爾自由行手冊');
    await start(); await ctx.close();
  }
  console.log(results.map(r => r.join(' | ')).join('\n'));
  const fails = results.filter(r => r[0] === 'FAIL').length;
  console.log(`\n${results.length - fails}/${results.length} passed`);
  await b.close(); await stop().catch(() => {});
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
