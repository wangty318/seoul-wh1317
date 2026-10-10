/* 首爾自由行手冊 service worker —— 由 src/make_pwa.py 從本檔產生 ../sw.js，請改這個檔，不要直接改 sw.js。
 * 快取分兩個：
 *   頁面快取（index.html、manifest）：每次改行程都會換新。
 *   資源快取（圖示、1.7MB 地鐵圖）：圖不變就不會重新下載。
 * 策略：頁面（navigate）網路優先、強制向伺服器重新驗證，3 秒沒回應就用快取；其餘靜態檔快取優先。 */
const PAGE_V = 'dabbd8486a';
const ASSET_V = '9570e085c2';
const BUILD_ID = '19e86fcfeade';
const PAGE_CACHE = 'seoul-page-' + PAGE_V;
const ASSET_CACHE = 'seoul-assets-' + ASSET_V;
const PAGE_FILES = ['./', './index.html', './manifest.webmanifest'];
const ASSET_FILES = ['./icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png', './seoul-metro-map.jpg'];
const NAV_TIMEOUT = 3000;

async function precachePages() {
  const c = await caches.open(PAGE_CACHE);
  await c.addAll(PAGE_FILES.map(u => new Request(u, { cache: 'reload' })));   // 頁面檔案失敗 → 安裝失敗，舊版繼續服務
}
async function precacheAssets() {
  const c = await caches.open(ASSET_CACHE);
  await Promise.all(ASSET_FILES.map(async u => {
    if (await c.match(u)) return;                                              // 已經有就不重抓
    try { await c.add(new Request(u, { cache: 'reload' })); } catch (_) {}     // 圖片失敗不擋安裝，狀態會顯示「未存好」
  }));
}
const precache = async () => { await precachePages(); await precacheAssets(); };

self.addEventListener('install', e => { e.waitUntil((async () => { await precache(); await self.skipWaiting(); })()); });

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('seoul-') && k !== PAGE_CACHE && k !== ASSET_CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

function withTimeout(p, ms) {
  return new Promise((resolve, reject) => { const t = setTimeout(() => reject(new Error('timeout')), ms); p.then(v => { clearTimeout(t); resolve(v); }, e => { clearTimeout(t); reject(e); }); });
}

async function navigate(req) {
  const cache = await caches.open(PAGE_CACHE);
  try {
    // no-cache：每次都向伺服器確認，避開 GitHub Pages 預設約 10 分鐘的 HTTP 快取，改完行程馬上拿得到
    const res = await withTimeout(fetch(req.url, { cache: 'no-cache', redirect: 'manual', credentials: 'same-origin' }), NAV_TIMEOUT);
    if (res.type === 'opaqueredirect') return res;
    if (!res.ok) throw new Error('bad status ' + res.status);                  // 例如 Pages 部署中暫時 404 → 改用快取
    cache.put('./index.html', res.clone());
    return res;
  } catch (_) {
    return (await cache.match('./index.html')) || (await cache.match('./')) || Response.error();
  }
}

async function asset(req) {
  const opt = { ignoreSearch: true };
  const hit = (await (await caches.open(ASSET_CACHE)).match(req, opt)) || (await (await caches.open(PAGE_CACHE)).match(req, opt));
  return hit || fetch(req);
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(req.mode === 'navigate' ? navigate(req) : asset(req));
});

async function status() {
  const pc = await caches.open(PAGE_CACHE), ac = await caches.open(ASSET_CACHE);
  const missing = [];
  for (const u of PAGE_FILES) if (!(await pc.match(u))) missing.push(u);
  for (const u of ASSET_FILES) if (!(await ac.match(u))) missing.push(u);
  return { ok: missing.length === 0, missing, build: BUILD_ID, page: PAGE_V, assets: ASSET_V };
}

self.addEventListener('message', e => {
  const port = e.ports && e.ports[0];
  if (!port) return;
  const type = (e.data || {}).type;
  if (type === 'status') e.waitUntil(status().then(s => port.postMessage(s)));
  else if (type === 'precache') e.waitUntil(precache().then(() => port.postMessage({ done: true }), err => port.postMessage({ done: false, error: String(err) })));
});
