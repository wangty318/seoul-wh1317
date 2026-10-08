/* 離線與更新狀態：向 service worker 問「該存的檔案是不是都在快取裡、頁面是不是最新版」，結果顯示在頂部列。
   「↻ 有新版本」＝ service worker 已拿到新版，但目前畫面還是舊的，點一下重新載入即可。 */
(function () {
  var bar = document.querySelector('.topbar-in');
  if (!bar || !('serviceWorker' in navigator) || !window.caches || !/^https?:$/.test(location.protocol)) return;
  var meta = document.querySelector('meta[name="build-id"]');
  var PAGE_BUILD = meta ? meta.getAttribute('content') : '';
  var pill = document.createElement('button');
  pill.type = 'button'; pill.className = 'offl'; pill.hidden = true;
  bar.classList.add('has-offl'); bar.appendChild(pill);
  var reg = null, hadCtl = !!navigator.serviceWorker.controller, lastPoke = 0;

  function show(state, txt, label) { pill.hidden = false; pill.dataset.state = state; pill.textContent = txt; pill.setAttribute('aria-label', label); }
  function ask(worker, msg) {
    return new Promise(function (res) {
      var ch = new MessageChannel(), t = setTimeout(function () { res(null); }, 10000);
      ch.port1.onmessage = function (e) { clearTimeout(t); res(e.data); };
      worker.postMessage(msg, [ch.port2]);
    });
  }
  function bad() { show('bad', '! 未存好', '離線資料還沒存好，連上網路後點一下重試'); }
  function check() {
    var timeout = new Promise(function (_, rej) { setTimeout(function () { rej(new Error('sw timeout')); }, 6000); });
    return Promise.race([navigator.serviceWorker.ready, timeout]).then(function (r) {
      reg = r; return ask(r.active, { type: 'status' });
    }).then(function (s) {
      if (!s || !s.ok) bad();
      else if (s.build && PAGE_BUILD && s.build !== PAGE_BUILD) show('update', '↻ 有新版本', '有新版本，點一下更新');
      else show('ok', '✓ 離線可用', '資料已存好，沒網路也能開');
    }).catch(bad);
  }
  function poke() {            // 回到前景、恢復連線、定時：問一次有沒有新版（只會下載很小的 sw.js）
    if (!reg || document.visibilityState !== 'visible') return;
    var now = Date.now();
    if (now - lastPoke < 60000) return;
    lastPoke = now;
    reg.update().then(function () { setTimeout(check, 400); }).catch(function () {});
  }

  pill.addEventListener('click', function () {
    var st = pill.dataset.state;
    if (st === 'update') { location.reload(); return; }
    if (st === 'ok' || !reg || !reg.active) { check(); return; }
    show('wait', '存檔中…', '正在存離線資料');
    ask(reg.active, { type: 'precache' }).then(check);
  });
  navigator.serviceWorker.addEventListener('controllerchange', function () {
    if (hadCtl) setTimeout(check, 300); else hadCtl = true;
  });
  document.addEventListener('visibilitychange', poke);
  window.addEventListener('online', poke);
  setInterval(poke, 10 * 60 * 1000);

  show('wait', '存檔中…', '正在存離線資料');
  navigator.serviceWorker.register('sw.js', { scope: './' }).then(function (r) { reg = r; }).catch(function () {}).then(check);
})();
