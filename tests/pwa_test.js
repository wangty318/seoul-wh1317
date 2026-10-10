/* PWA 離線與更新測試（Chromium + Playwright，真的把伺服器關掉來模擬斷網）
 * 用法：  NODE_PATH=$(npm root -g) node tests/pwa_test.js [截圖輸出資料夾]
 * 需要：python3、playwright（含 chromium）。測試會從 src/ 複製出暫存副本、改一小段內容再 build，
 * 所以同時驗證了「真實的 build 流程」與「舊版 → 新版」的更新體驗；不會動到 repo 裡任何檔案。 */
let chromium;
try { ({ chromium } = require('playwright')); } catch (_) { ({ chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright')); }
const http = require('http'), fs = require('fs'), os = require('os'), path = require('path');
const { spawnSync } = require('child_process');

const REPO = path.resolve(__dirname, '..');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'seoul-pwa-test-'));
const SHOT = process.argv[2] || TMP;
const PORT = 8765, PREFIX = '/seoul/';            // 放在子路徑，模擬 GitHub Pages 的 /<repo>/
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const sleep = ms => new Promise(r => setTimeout(r, ms));

function build(tag, patch, stamp) {
  const src = path.join(TMP, 'src-' + tag), out = path.join(TMP, 'site-' + tag);
  fs.cpSync(path.join(REPO, 'src'), src, { recursive: true });
  if (patch) {
    const f = path.join(src, 'seoul-safety.html');
    const s = fs.readFileSync(f, 'utf8');
    if (!s.includes('首爾五日行程安全卡')) throw new Error('patch anchor missing');
    fs.writeFileSync(f, s.split('首爾五日行程安全卡').join('首爾五日行程安全卡' + patch));
  }
  const r = spawnSync('python3', [path.join(src, 'build.py'), '--out', out, '--stamp', stamp], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('build failed: ' + r.stderr);
  return out;
}

let ROOT, slowMs = 0, blockMap = false, hits = [], server;
function mk() {
  return http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    hits.push(u.pathname.slice(PREFIX.length));
    if (!u.pathname.startsWith(PREFIX)) { res.writeHead(404); return res.end('nf'); }
    let rel = u.pathname.slice(PREFIX.length) || 'index.html';
    if (rel.endsWith('/')) rel += 'index.html';
    if (blockMap && rel === 'seoul-metro-map.jpg') { res.writeHead(404); return res.end('blocked'); }
    const f = path.join(ROOT, rel);
    const go = () => fs.readFile(f, (e, buf) => {
      if (e) { res.writeHead(404); return res.end('nf'); }
      // 跟 GitHub Pages 一樣帶 10 分鐘的 HTTP 快取：確認我們的更新機制不會被它擋住
      res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'public, max-age=600' });
      res.end(buf);
    });
    if (slowMs && rel === 'index.html') setTimeout(go, slowMs); else go();
  });
}
const start = () => new Promise(r => { server = mk(); server.listen(PORT, '127.0.0.1', r); });
const stop = () => new Promise(r => { server.closeAllConnections(); server.close(r); });
const results = [];
const ok = (name, cond, extra) => results.push([cond ? 'PASS' : 'FAIL', name, extra === undefined ? '' : String(extra)]);

(async () => {
  const dirs = { v1: build('v1', '', '10/08 23:00'), v2: build('v2', '（更新測試v2）', '10/09 08:00'), v3: build('v3', '（更新測試v3）', '10/10 09:30') };
  const sameAssets = JSON.parse(fs.readFileSync(path.join(dirs.v1, 'version.json'))).assets === JSON.parse(fs.readFileSync(path.join(dirs.v2, 'version.json'))).assets;
  ok('0 只改行程內容時，圖片資源版本號不變（改行程不會重下載地圖）', sameAssets);
  ROOT = dirs.v1;
  await start();
  const b = await chromium.launch();
  const mkctx = () => b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 });
  const errs = [];
  const URL0 = `http://127.0.0.1:${PORT}${PREFIX}`;
  const watch = p => { p.on('pageerror', e => errs.push('pageerror:' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console:' + m.text()); }); };
  const pillOf = p => async () => (await p.locator('.offl').innerText().catch(() => '(none)')).trim();
  const waitFor = async (get, want, ms = 12000) => { const t = Date.now(); while (Date.now() - t < ms) { if ((await get()).includes(want)) return true; await sleep(200); } return false; };
  const safetyText = p => p.evaluate(() => document.getElementById('pane-safety').shadowRoot.textContent.replace(/\s+/g, ' '));

  // ================= A/B/C：第一次安裝、斷網、慢網 =================
  const ctx = await mkctx(); const p = await ctx.newPage(); watch(p);
  const pill = pillOf(p);
  await p.goto(URL0);
  ok('A1 第一次載入後出現「✓ 離線可用」', await waitFor(pill, '✓'), await pill());
  const ck = await p.evaluate(async () => { const out = {}; for (const k of await caches.keys()) out[k] = (await (await caches.open(k)).keys()).map(r => new URL(r.url).pathname.replace('/seoul/', '')); return out; });
  const names = Object.keys(ck);
  ok('A2 兩個快取：頁面快取＋資源快取，且內容齊全（含全尺寸地鐵圖與航班截圖）',
    names.length === 2 && names.some(n => n.startsWith('seoul-page-') && ck[n].includes('index.html')) && names.some(n => n.startsWith('seoul-assets-') && ck[n].includes('seoul-metro-map.jpg') && ck[n].includes('flights.jpg')), JSON.stringify(ck));
  await p.reload(); await sleep(800);
  ok('A3 service worker 已接管頁面', await p.evaluate(() => !!navigator.serviceWorker.controller));
  const info = await p.locator('.buildinfo').innerText();
  ok('A4 頁面底部顯示版本與更新時間', /版本 [0-9a-f]{7} · 更新於 10\/08 23:00/.test(info), info);
  await p.screenshot({ path: SHOT + '/pwa2-online.png' });

  await stop();                                         // ← 真的沒網路
  await p.reload({ waitUntil: 'load' }); await sleep(800);
  ok('B1 斷網重新整理：頁面正常', (await p.title()) === '首爾自由行手冊');
  const full = await safetyText(p);
  ok('B2 斷網：安全卡內容在（含證件與護照、雙眼皮手術）', /證件與護照/.test(full) && /Ever8/.test(full) && /雙眼皮手術/.test(full) && !/閨蜜雙眼皮/.test(full));
  ok('B3 斷網：離線狀態仍顯示 ✓', await waitFor(pill, '✓', 8000), await pill());
  await p.tap('#tt-routes'); await sleep(300);
  await p.tap('#routes-tabs [data-tab="d2"]'); await sleep(300);
  ok('B4 斷網：可切到路線 → D2', await p.evaluate(() => !document.getElementById('top-routes').hidden && !document.getElementById('p-d2').hidden));
  await p.tap('#mapbtn'); await sleep(400); await p.tap('#mapopen'); await sleep(1500);
  const mv = await p.evaluate(() => ({ hidden: document.getElementById('mv').hidden, nat: document.getElementById('mvimg').naturalWidth }));
  ok('B5 斷網：全螢幕地鐵圖能開，且是 2655px 全尺寸', !mv.hidden && mv.nat === 2655, JSON.stringify(mv));
  await p.keyboard.press('Escape'); await sleep(200);
  for (const u of [URL0, URL0 + 'index.html', URL0 + '?utm=1#routes-d3']) {
    await p.goto(u, { waitUntil: 'load' }).catch(() => {});
    ok('B6 斷網直接開 ' + u.replace(URL0, '〈根〉'), (await p.title().catch(() => '')) === '首爾自由行手冊');
  }
  ok('B7 斷網：#routes-d3 直達 D3', await p.evaluate(() => !document.getElementById('p-d3').hidden));

  await start(); slowMs = 7000;
  const t0 = Date.now(); await p.goto(URL0, { waitUntil: 'load' }); const dt = Date.now() - t0;
  ok('C1 網路很慢（伺服器 7 秒才回）：約 3 秒就用快取開出來', dt > 2500 && dt < 5500, dt + ' ms');
  slowMs = 0; await sleep(8000);                        // 等那條 7 秒的舊請求結束，避免影響後面

  // ================= D：改了行程之後，她們怎麼拿到 =================
  ROOT = dirs.v2; hits = [];
  await p.goto(URL0, { waitUntil: 'load' }); await sleep(1500);   // （這裡直接線上開，等於「推上去之後她們冷啟動 App」）
  ok('D1 冷啟動：有網路時直接看到新版內容（不是舊快取）', /更新測試v2/.test(await safetyText(p)));
  ok('D2 冷啟動拿到新版後，不會多此一舉跳「有新版本」，最後是 ✓', await waitFor(pill, '✓', 8000), await pill());
  const mapHits = hits.filter(h => h === 'seoul-metro-map.jpg').length;
  ok('D3 只改行程：1.7MB 地鐵圖沒有被重新下載', mapHits === 0, 'map requests=' + mapHits);

  // 她們的 App 正開著（舊畫面），這時推上新版（v3）：回到前景 → 偵測到新版 → 顯示「↻ 有新版本」
  ROOT = dirs.v3; hits = [];
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  ok('D4 App 開著時推上新版：回到前景後出現「↻ 有新版本」', await waitFor(pill, '↻', 10000), await pill());
  await p.screenshot({ path: SHOT + '/pwa2-update-pill.png' });
  ok('D5 此時畫面仍是舊版（尚未重新載入）', /更新測試v2/.test(await safetyText(p)) && !/更新測試v3/.test(await safetyText(p)));
  await p.locator('.offl').click(); await sleep(1500);
  ok('D6 點一下後換成新版內容，且更新時間顯示新的', /更新測試v3/.test(await safetyText(p)) && /更新於 10\/10 09:30/.test(await p.locator('.buildinfo').innerText()));
  ok('D7 更新後狀態回到 ✓', await waitFor(pill, '✓', 8000), await pill());
  const keys = await p.evaluate(() => caches.keys());
  ok('D8 舊版快取已清掉，只剩一個頁面快取＋一個資源快取', keys.length === 2, JSON.stringify(keys));
  ok('D9 整個更新過程中地鐵圖仍沒有重新下載', hits.filter(h => h === 'seoul-metro-map.jpg').length === 0);
  await stop();
  await p.reload({ waitUntil: 'load' }); await sleep(600);
  ok('D10 更新後斷網：載到的是最新版（v3）', /更新測試v3/.test(await safetyText(p)));
  const shot0 = await p.evaluate(() => { const d = document.getElementById('pane-safety').shadowRoot.querySelector('details.shot'); const r = document.getElementById('pane-safety').shadowRoot.getElementById('flights'); return d && { open: d.open, inFlights: r.contains(d), label: d.querySelector('summary').textContent.replace(/\s+/g, '') }; });
  ok('D11 安全卡「航班」區塊下面有收合的「航班截圖」', shot0 && !shot0.open && shot0.inFlights && /航班截圖/.test(shot0.label), JSON.stringify(shot0));
  const shot1 = await p.evaluate(async () => {
    const d = document.getElementById('pane-safety').shadowRoot.querySelector('details.shot'); d.open = true;
    const i = d.querySelector('img'); i.scrollIntoView();
    await new Promise(r => { const t = setTimeout(r, 4000); const done = () => { clearTimeout(t); r(); }; if (i.complete && i.naturalWidth) done(); else { i.onload = done; i.onerror = done; } });
    return { open: d.open, w: i.naturalWidth, h: i.naturalHeight, shownW: Math.round(i.getBoundingClientRect().width) };
  });
  ok('D12 斷網狀態下展開，航班截圖載得出來（來自離線快取），且寬度撐滿卡片', shot1.open && shot1.w === 1080 && shot1.h === 938 && shot1.shownW > 300, JSON.stringify(shot1));
  await p.screenshot({ path: path.join(SHOT, 'd12-flight-shot-offline.png') });
  await ctx.close();

  // ================= F：第一次存檔時地圖失敗 → 顯示「未存好」→ 點一下重試 =================
  ROOT = dirs.v1; blockMap = true; await start();
  const ctx2 = await mkctx(); const p2 = await ctx2.newPage(); watch(p2); const pill2 = pillOf(p2);
  await p2.goto(URL0);
  ok('F1 地圖沒存成功時，狀態是「! 未存好」（不會假裝成功）', await waitFor(pill2, '!', 12000), await pill2());
  blockMap = false;
  await p2.locator('.offl').click();
  ok('F2 網路恢復後點一下重試 → 變成 ✓', await waitFor(pill2, '✓', 12000), await pill2());
  await ctx2.close();

  console.log(results.map(r => r.join(' | ')).join('\n'));
  const bad = errs.filter(e => !/ERR_INTERNET_DISCONNECTED|ERR_CONNECTION_REFUSED|Failed to load resource|404/.test(e));
  console.log('PAGE ERRORS:', JSON.stringify(bad));
  const fails = results.filter(r => r[0] === 'FAIL').length;
  console.log(`\n${results.length - fails}/${results.length} passed`);
  await b.close(); await stop().catch(() => {});
  fs.rmSync(TMP, { recursive: true, force: true });
  process.exit(fails || bad.length ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
