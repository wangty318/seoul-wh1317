/* 首爾自由行手冊 service worker
 * 版本號 = 所有檔案內容的雜湊；任何檔案變動都會換新快取、清掉舊快取。
 * 策略：頁面（navigate）網路優先、3 秒逾時就用快取；其餘靜態檔快取優先。 */
const VERSION = 'bde84eec58';
const CACHE = 'seoul-' + VERSION;
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
const EXTRA = ['./seoul-metro-map.jpg'];          // 1.7 MB 的全尺寸地鐵圖
const ALL = CORE.concat(EXTRA);
const NAV_TIMEOUT = 3000;

async function precache() {
  const cache = await caches.open(CACHE);
  await cache.addAll(CORE.map(u => new Request(u, { cache: 'reload' })));          // 核心檔案失敗 → 安裝失敗
  await Promise.all(EXTRA.map(u => cache.add(new Request(u, { cache: 'reload' })).catch(() => {})));  // 地圖失敗不擋安裝，狀態會顯示「未存好」
}

self.addEventListener('install', e => { e.waitUntil(precache().then(() => self.skipWaiting())); });

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('seoul-') && k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

function withTimeout(p, ms) {
  return new Promise((resolve, reject) => { const t = setTimeout(() => reject(new Error('timeout')), ms); p.then(v => { clearTimeout(t); resolve(v); }, e => { clearTimeout(t); reject(e); }); });
}

async function navigate(req) {
  const cache = await caches.open(CACHE);
  try {
    const res = await withTimeout(fetch(req), NAV_TIMEOUT);
    if (res && res.ok) { const c = res.clone(); cache.put('./index.html', c); }
    return res;
  } catch (_) {
    return (await cache.match('./index.html')) || (await cache.match('./')) || Response.error();
  }
}

async function assetFirst(req) {
  const hit = await caches.match(req, { ignoreSearch: true });
  if (hit) return hit;
  const res = await fetch(req);
  if (res && res.ok) (await caches.open(CACHE)).put(req, res.clone());
  return res;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.mode === 'navigate') e.respondWith(navigate(req));
  else e.respondWith(assetFirst(req));
});

self.addEventListener('message', e => {
  const port = e.ports && e.ports[0];
  if (!port) return;
  const d = e.data || {};
  if (d.type === 'status') {
    e.waitUntil((async () => {
      const cache = await caches.open(CACHE);
      const missing = [];
      for (const u of ALL) if (!(await cache.match(u))) missing.push(u);
      port.postMessage({ ok: missing.length === 0, missing, version: VERSION });
    })());
  } else if (d.type === 'precache') {
    e.waitUntil(precache().then(() => port.postMessage({ done: true }), err => port.postMessage({ done: false, error: String(err) })));
  }
});
