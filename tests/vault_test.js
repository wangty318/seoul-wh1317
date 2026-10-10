/* 「Hsuan的入境卡」測試：按鈕位置、密碼、匯入、重開後仍在、自動上鎖、刪除；以及 repo 裡沒有入境卡。
 * 用法：  NODE_PATH=$(npm root -g) node tests/vault_test.js [截圖輸出資料夾]
 * 直接服務 repo 目前的 seoul-pwa/（唯讀）。測試用的「入境卡」是現場畫出來的假圖，絕不使用真正的入境卡。 */
let chromium;
try { ({ chromium } = require('playwright')); } catch (_) { ({ chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright')); }
const http = require('http'), fs = require('fs'), os = require('os'), path = require('path');
const { spawnSync } = require('child_process');

const REPO = path.resolve(__dirname, '..'), SITE = path.join(REPO, 'seoul-pwa');
const SHOT = process.argv[2] || fs.mkdtempSync(path.join(os.tmpdir(), 'seoul-vault-test-'));
const PORT = 8767, PREFIX = '/seoul/';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x');
  if (!u.pathname.startsWith(PREFIX)) { res.writeHead(404); return res.end(); }
  let rel = u.pathname.slice(PREFIX.length) || 'index.html'; if (rel.endsWith('/')) rel += 'index.html';
  const f = path.join(SITE, rel);
  fs.readFile(f, (e, buf) => { if (e || !f.startsWith(SITE)) { res.writeHead(404); return res.end('nf'); } res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); res.end(buf); });
});
const results = [], ok = (n, c, x) => results.push([c ? 'PASS' : 'FAIL', n, x === undefined ? '' : String(x)]);
const PIN = '0517';
const MINI_PDF = Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R/Size 4>>\n%%EOF\n');

(async () => {
  await new Promise(r => server.listen(PORT, '127.0.0.1', r));
  const b = await chromium.launch();
  const URL0 = `http://127.0.0.1:${PORT}${PREFIX}`;
  const errs = [];
  const mk = (scheme = 'light') => b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2, colorScheme: scheme });
  const watch = p => { p.on('pageerror', e => errs.push('pageerror:' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console:' + m.text()); }); };
  const vis = (p, sel) => p.locator(sel).isVisible();
  const typePin = async (p, v) => { await p.locator('#vault-pin-in').fill(v); await sleep(450); };
  const openVault = async p => { await p.locator('#vault-open').scrollIntoViewIfNeeded(); await p.locator('#vault-open').click(); await sleep(150); };
  const state = p => p.evaluate(() => ({
    ov: !document.getElementById('vault').hidden, pin: !document.getElementById('vault-pin').hidden, imp: !document.getElementById('vault-import').hidden,
    view: !document.getElementById('vault-view').hidden, stage: document.getElementById('vault-stage').innerHTML.slice(0, 40),
    msg: document.getElementById('vault-pin-msg').textContent + '|' + document.getElementById('vault-imp-msg').textContent + '|' + document.getElementById('vault-view-msg').textContent
  }));
  const dummyPng = p => p.evaluate(() => {      // 假的「入境卡」：一張 300×400、寫著 TEST 的圖
    const c = document.createElement('canvas'); c.width = 300; c.height = 400; const g = c.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, 300, 400); g.fillStyle = '#000'; g.font = '40px sans-serif'; g.fillText('TEST CARD', 30, 100); g.fillRect(60, 160, 180, 180);
    return c.toDataURL('image/png').split(',')[1];
  });

  const ctx = await mk(); const p = await ctx.newPage(); watch(p);
  await p.goto(URL0); await sleep(800);

  // ---- 按鈕 ----
  const btn = await p.evaluate(() => {
    const r = document.getElementById('pane-safety').shadowRoot, b = r.getElementById('vault-open'), wrap = r.querySelector('.wrap');
    return { text: b.textContent.replace(/\s+/g, ''), last: wrap.lastElementChild.contains(b), afterFooter: !!(r.querySelector('footer').compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) };
  });
  ok('1 安全卡最下面有「Hsuan的入境卡」按鈕（在頁尾之後、整張卡的最後一個區塊）', btn.text === 'Hsuan的入境卡' && btn.last && btn.afterFooter, JSON.stringify(btn));
  ok('2 沒按之前，入境卡視窗是關著的', !(await state(p)).ov);
  await p.locator('#vault-open').scrollIntoViewIfNeeded(); await sleep(200);
  await p.screenshot({ path: path.join(SHOT, 'v1-button.png') });

  // ---- 密碼 ----
  await openVault(p);
  let s = await state(p);
  ok('3 按下去先出現密碼畫面，輸入框已聚焦', s.ov && s.pin && !s.imp && !s.view && await p.evaluate(() => document.activeElement && document.activeElement.id === 'vault-pin-in'));
  const mask = await p.evaluate(() => { const cs = getComputedStyle(document.getElementById('vault-pin-in')); return cs.webkitTextSecurity || cs.getPropertyValue('-webkit-text-security'); });
  ok('4 密碼欄位是遮蔽顯示（不是明碼）', mask === 'disc', mask);
  await p.screenshot({ path: path.join(SHOT, 'v2-pin.png') });
  await typePin(p, '1234');
  s = await state(p);
  ok('5 輸入錯誤密碼：不打開、顯示「密碼不對」、輸入框清空', s.pin && !s.imp && !s.view && /密碼不對/.test(s.msg) && (await p.locator('#vault-pin-in').inputValue()) === '', s.msg);
  await p.locator('#vault-pin-in').fill('12ab'); await sleep(300);
  ok('6 輸入框只收數字、最多 4 碼', (await p.locator('#vault-pin-in').inputValue()) === '12');
  await p.locator('#vault-pin-in').fill(''); await typePin(p, PIN);
  s = await state(p);
  ok('7 輸入正確密碼，且這支手機還沒存卡 → 出現匯入畫面', s.imp && !s.pin && !s.view, JSON.stringify(s));
  await p.screenshot({ path: path.join(SHOT, 'v3-import.png') });

  // ---- 匯入檔案 ----
  await p.setInputFiles('#vault-file', { name: 'notes.txt', mimeType: 'text/plain', buffer: Buffer.from('hello') });
  await sleep(300); s = await state(p);
  ok('8 選到不是圖片／PDF 的檔案 → 拒絕並提示，仍停在匯入畫面', s.imp && /不是圖片或 PDF/.test(s.msg), s.msg);
  await p.setInputFiles('#vault-file', { name: 'big.png', mimeType: 'image/png', buffer: Buffer.alloc(16 * 1024 * 1024) });
  await sleep(300); s = await state(p);
  ok('9 超過 15 MB → 拒絕並提示', s.imp && /太大/.test(s.msg), s.msg);
  const png = Buffer.from(await dummyPng(p), 'base64');
  await p.setInputFiles('#vault-file', { name: 'card.png', mimeType: 'image/png', buffer: png });
  await sleep(700); s = await state(p);
  const img = await p.evaluate(() => { const i = document.querySelector('#vault-stage img'); return i && { ok: i.complete && i.naturalWidth === 300 && i.naturalHeight === 400, src: i.src.slice(0, 5), w: Math.round(i.getBoundingClientRect().width) }; });
  ok('10 匯入圖片後直接顯示，且寬度撐滿手機螢幕', s.view && img && img.ok && img.src === 'blob:' && img.w === 390, JSON.stringify(img));
  await p.screenshot({ path: path.join(SHOT, 'v4-view.png') });
  const store = await p.evaluate(() => new Promise(res => { const r = indexedDB.open('seoul-vault', 1); r.onsuccess = () => { const g = r.result.transaction('files').objectStore('files').get('hsuan-arrival'); g.onsuccess = () => { res(g.result && { bytes: g.result.buf.byteLength, type: g.result.type }); r.result.close(); }; }; }));
  ok('11 檔案存在這支手機的 IndexedDB（大小、類型正確）', store && store.bytes === png.length && store.type === 'image/png', JSON.stringify(store));
  const noNet = await p.evaluate(() => performance.getEntriesByType('resource').filter(e => /card|vault|upload/i.test(e.name) && !/^blob:/.test(e.name)).length);
  ok('12 匯入過程沒有任何網路上傳請求', noNet === 0, noNet);

  // ---- 重新整理後仍在、要再輸入密碼 ----
  await p.reload(); await sleep(900);
  await openVault(p);
  s = await state(p);
  ok('13 重新整理後再開：先要密碼（不會直接露出卡片）', s.pin && !s.view && s.stage === '', JSON.stringify(s));
  await typePin(p, PIN); await sleep(300); s = await state(p);
  const img2 = await p.evaluate(() => { const i = document.querySelector('#vault-stage img'); return i && i.complete && i.naturalWidth === 300; });
  ok('14 輸入密碼後直接看到上次存的卡片', s.view && img2, JSON.stringify(s));

  // ---- 自動上鎖 ----
  await p.evaluate(() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); document.dispatchEvent(new Event('visibilitychange')); });
  await sleep(200); s = await state(p);
  ok('15 切到別的 App／鎖屏（頁面被隱藏）→ 自動關閉並清掉畫面上的卡片', !s.ov && s.stage === '', JSON.stringify(s));
  await p.evaluate(() => { delete document.visibilityState; });
  await openVault(p); s = await state(p);
  ok('16 再打開又要重新輸入密碼', s.pin && !s.view);
  await p.keyboard.press('Escape'); await sleep(150);
  ok('17 Esc 可以關閉', !(await state(p)).ov);
  await openVault(p); await p.locator('#vault-close').click(); await sleep(150);
  ok('18 「關閉」按鈕可以關閉，且 App 本身的頁面沒被改動（仍在安全卡）', !(await state(p)).ov && await p.evaluate(() => !document.getElementById('top-safety').hidden));

  // ---- 換成 PDF ----
  await openVault(p); await typePin(p, PIN); await sleep(300);
  await p.setInputFiles('#vault-file', { name: 'card.pdf', mimeType: 'application/pdf', buffer: MINI_PDF });
  await sleep(600); s = await state(p);
  const pdf = await p.evaluate(() => { const f = document.querySelector('#vault-stage iframe'); return f && { src: f.src.slice(0, 5), help: !document.getElementById('vault-pdf-help').hidden, link: document.getElementById('vault-pdf-link').href.slice(0, 5) }; });
  ok('19 匯入 PDF：用內嵌框顯示，並提供「用瀏覽器開啟」備案', s.view && pdf && pdf.src === 'blob:' && pdf.help && pdf.link === 'blob:', JSON.stringify(pdf));
  await p.setInputFiles('#vault-file', { name: 'card.png', mimeType: 'image/png', buffer: png }); await sleep(600);
  ok('20 「換一張」可換回圖片，PDF 備案提示隱藏', await p.evaluate(() => !!document.querySelector('#vault-stage img') && !document.querySelector('#vault-stage iframe') && document.getElementById('vault-pdf-help').hidden));

  // ---- 刪除（要按兩次） ----
  await p.locator('#vault-del').click(); await sleep(100);
  const armed = await p.locator('#vault-del').innerText();
  ok('21 刪除要按兩次：第一次只是要你確認', /再按一次/.test(armed) && (await state(p)).view, armed);
  await p.locator('#vault-del').click(); await sleep(500); s = await state(p);
  ok('22 第二次才真的刪除，回到匯入畫面', s.imp && !s.view && /已從這支手機刪除/.test(s.msg), s.msg);
  await p.reload(); await sleep(900); await openVault(p); await typePin(p, PIN); await sleep(300); s = await state(p);
  ok('23 刪除後重新整理，儲存裡真的沒有了', s.imp && !s.view);
  const layout = await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
  ok('24 手機寬度沒有橫向捲動', layout);
  await p.keyboard.press('Escape');

  // ---- 深色模式 ----
  const ctxD = await mk('dark'); const pd = await ctxD.newPage(); watch(pd);
  await pd.goto(URL0); await sleep(800);
  await pd.locator('#vault-open').scrollIntoViewIfNeeded(); await sleep(150);
  await pd.screenshot({ path: path.join(SHOT, 'v5-button-dark.png') });
  await openVault(pd); await pd.screenshot({ path: path.join(SHOT, 'v6-pin-dark.png') });
  const bg = await pd.evaluate(() => getComputedStyle(document.getElementById('vault')).backgroundColor);
  ok('25 深色模式：入境卡視窗用深色底（跟 App 一致）', bg === 'rgb(14, 22, 19)', bg);
  await typePin(pd, PIN); await pd.setInputFiles('#vault-file', { name: 'card.png', mimeType: 'image/png', buffer: png }); await sleep(600);
  await pd.screenshot({ path: path.join(SHOT, 'v7-view-dark.png') });
  await ctxD.close();

  // ---- repo 衛生：入境卡與密碼不能出現在公開 repo ----
  const tracked = spawnSync('git', ['ls-files'], { cwd: REPO, encoding: 'utf8' }).stdout.split('\n');
  const bad = tracked.filter(f => /\.pdf$/i.test(f) || /arrival/i.test(f));
  ok('26 repo 沒有追蹤任何 PDF 或檔名含 arrival 的檔案', bad.length === 0, bad.join(','));
  const built = ['index.html', 'sw.js'].map(f => fs.readFileSync(path.join(SITE, f), 'utf8')).join('\n');
  ok('27 建好的網站裡沒有內嵌 PDF／入境卡資料，也沒有明文密碼', !/application\/pdf;base64|%PDF-|JVBERi0/.test(built) && !built.includes(PIN));

  await ctx.close();
  console.log(results.map(r => r.join(' | ')).join('\n'));
  const badErr = errs.filter(e => !/Failed to load resource|404/.test(e));
  console.log('PAGE ERRORS:', JSON.stringify(badErr));
  const fails = results.filter(r => r[0] === 'FAIL').length;
  console.log(`\n${results.length - fails}/${results.length} passed  (screenshots: ${SHOT})`);
  await b.close(); server.closeAllConnections(); server.close();
  process.exit(fails || badErr.length ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
