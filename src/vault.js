/* 「Hsuan的入境卡」：放在她手機本機的小保險箱。改這裡之前先看 CLAUDE.md 的「入境卡」一節。
   1. 入境卡本身絕對不進 repo（repo 是公開的）。檔案由 Hsuan 在自己手機上匯入，只存在這支手機的 IndexedDB，不會上傳。
   2. 密碼只是畫面上的鎖：擋手機被旁人瞄到、隨手點開。程式碼是公開的，所以它不是加密，也不能當成保護。
   3. 看完卡片、切到別的 App 或鎖屏時自動關閉（回到密碼畫面）。 */
(function () {
  var host = document.getElementById('pane-safety');
  var ov = document.getElementById('vault');
  if (!host || !host.shadowRoot || !ov) return;
  var openBtn = host.shadowRoot.getElementById('vault-open');
  if (!openBtn) return;

  var DB = 'seoul-vault', STORE = 'files', KEY = 'hsuan-arrival';
  var PIN_HASH = 613358874656359, MAX_BYTES = 15 * 1024 * 1024;
  function $(id) { return document.getElementById(id); }
  var el = {
    close: $('vault-close'), pinForm: $('vault-pin'), pinIn: $('vault-pin-in'), pinMsg: $('vault-pin-msg'),
    imp: $('vault-import'), impMsg: $('vault-imp-msg'), pick: $('vault-pick'), file: $('vault-file'),
    view: $('vault-view'), stage: $('vault-stage'), viewMsg: $('vault-view-msg'), pdfHelp: $('vault-pdf-help'),
    pdfLink: $('vault-pdf-link'), swap: $('vault-swap'), del: $('vault-del')
  };
  var st = 'closed', tok = 0, url = '', mem = null, armTimer = 0, pinTimer = 0;

  /* ---- 密碼檢查（cyrb53；不依賴 crypto.subtle，所以在任何環境都能用） ---- */
  function h53(str, seed) {
    var h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
    for (var i = 0, ch; i < str.length; i++) {
      ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return 4294967296 * (2097151 & h2) + (h1 >>> 0);
  }

  /* ---- IndexedDB：存 ArrayBuffer + 檔案類型（比直接存 Blob 在 iOS 上穩） ---- */
  function idb() {
    return new Promise(function (res, rej) {
      if (!window.indexedDB) { rej(new Error('no indexedDB')); return; }
      var r;
      try { r = indexedDB.open(DB, 1); } catch (e) { rej(e); return; }
      r.onupgradeneeded = function () { r.result.createObjectStore(STORE); };
      r.onsuccess = function () { res(r.result); };
      r.onerror = function () { rej(r.error || new Error('idb open')); };
      r.onblocked = function () { rej(new Error('idb blocked')); };
    });
  }
  function run(mode, fn) {
    return idb().then(function (db) {
      return new Promise(function (res, rej) {
        var req;
        try { req = fn(db.transaction(STORE, mode).objectStore(STORE)); } catch (e) { db.close(); rej(e); return; }
        var t = req.transaction;
        t.oncomplete = function () { db.close(); res(req.result); };
        t.onerror = t.onabort = function () { db.close(); rej(t.error || new Error('idb tx')); };
      });
    });
  }
  function loadRec() {
    return run('readonly', function (s) { return s.get(KEY); }).then(function (r) { return r || mem; }, function () { return mem; });
  }
  function saveRec(rec) { return run('readwrite', function (s) { return s.put(rec, KEY); }); }
  function delRec() { return run('readwrite', function (s) { return s.delete(KEY); }); }
  function persist() { try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function () {}); } catch (e) {} }

  /* ---- 畫面狀態：pin → import（還沒存卡）或 view（已存卡） ---- */
  function show(name) {
    st = name;
    el.pinForm.hidden = name !== 'pin';
    el.imp.hidden = name !== 'import';
    el.view.hidden = name !== 'view';
  }
  function say(node, text) { node.textContent = text || ''; }
  function disarm() { clearTimeout(armTimer); el.del.removeAttribute('data-armed'); el.del.textContent = '刪除'; }
  function dropUrl(delay) {
    var u = url; url = '';
    if (!u) return;
    if (delay) setTimeout(function () { URL.revokeObjectURL(u); }, delay); else URL.revokeObjectURL(u);
  }

  function openVault() {
    tok++;
    document.documentElement.classList.add('vault-on');
    ov.hidden = false;
    el.pinIn.value = '';
    say(el.pinMsg, ''); say(el.impMsg, ''); say(el.viewMsg, '');
    show('pin');
    setTimeout(function () { try { el.pinIn.focus(); } catch (e) {} }, 40);
  }
  function closeVault() {
    tok++; clearTimeout(pinTimer); disarm();
    dropUrl(60000);                                  // 晚一點再釋放：「用瀏覽器開啟」的新分頁可能還在讀它
    el.stage.textContent = '';
    ov.hidden = true;
    document.documentElement.classList.remove('vault-on');
    el.pinIn.value = '';
    show('pin'); st = 'closed';
    try { openBtn.focus(); } catch (e) {}
  }

  function showCard(rec) {
    dropUrl(0); disarm();
    say(el.viewMsg, '');
    el.stage.textContent = '';
    var isPdf = rec.type === 'application/pdf';
    url = URL.createObjectURL(new Blob([rec.buf], { type: rec.type }));
    if (isPdf) {
      var f = document.createElement('iframe');
      f.title = 'Hsuan的入境卡（PDF）'; f.src = url;
      el.stage.appendChild(f);
      el.pdfLink.href = url;
    } else {
      var img = new Image();
      img.alt = 'Hsuan的入境卡';
      img.onerror = function () { el.stage.textContent = ''; say(el.viewMsg, '這個檔案顯示不出來。按「換一張」，改選入境卡的截圖。'); };
      img.src = url;
      el.stage.appendChild(img);
    }
    el.pdfHelp.hidden = !isPdf;
    show('view');
  }

  function tryPin() {
    if (st !== 'pin') return;
    clearTimeout(pinTimer);
    var v = el.pinIn.value;
    if (v.length !== 4) { say(el.pinMsg, '請輸入 4 位數字'); return; }
    el.pinIn.value = '';
    if (h53('seoul-vault|' + v, 7) !== PIN_HASH) {
      say(el.pinMsg, '密碼不對，再試一次');
      el.pinIn.classList.remove('vault-shake'); void el.pinIn.offsetWidth; el.pinIn.classList.add('vault-shake');
      el.pinIn.focus();
      return;
    }
    say(el.pinMsg, '');
    var my = ++tok;
    loadRec().then(function (rec) {
      if (my !== tok || ov.hidden) return;
      if (rec) showCard(rec); else show('import');
    });
  }

  function readBuf(file) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(r.result); };
      r.onerror = function () { rej(r.error); };
      r.readAsArrayBuffer(file);
    });
  }
  function onFile() {
    var f = el.file.files && el.file.files[0];
    el.file.value = '';                              // 讓同一個檔案可以再選一次
    if (!f || ov.hidden) return;
    var msg = st === 'view' ? el.viewMsg : el.impMsg;
    var type = f.type || (/\.pdf$/i.test(f.name) ? 'application/pdf' : '');
    if (!/^image\//.test(type) && type !== 'application/pdf') { say(msg, '這不是圖片或 PDF，請再選一次'); return; }
    if (f.size > MAX_BYTES) { say(msg, '檔案太大（上限 15 MB），請改用截圖'); return; }
    say(msg, '存入中…');
    var my = ++tok;
    readBuf(f).then(function (buf) {
      var rec = { buf: buf, type: type, name: f.name, at: Date.now() };
      mem = rec;
      return saveRec(rec).then(function () { persist(); return true; }, function () { return false; }).then(function (saved) {
        if (my !== tok || ov.hidden) return;
        showCard(rec);
        if (!saved) say(el.viewMsg, '這個瀏覽器存不進去（可能是無痕模式或空間不足）。這次先顯示，關掉頁面後要重選。');
      });
    }).catch(function () { say(msg, '讀不到這個檔案，請再選一次'); });
  }

  function onDelete() {
    if (!el.del.hasAttribute('data-armed')) {
      el.del.setAttribute('data-armed', '1'); el.del.textContent = '再按一次確認刪除';
      armTimer = setTimeout(disarm, 4000);
      return;
    }
    disarm(); mem = null;
    var my = ++tok;
    delRec().catch(function () {}).then(function () {
      if (my !== tok || ov.hidden) return;
      dropUrl(0); el.stage.textContent = '';
      show('import'); say(el.impMsg, '已從這支手機刪除');
    });
  }

  function trapTab(e) {
    var list = [].slice.call(ov.querySelectorAll('button, input, a[href], iframe')).filter(function (n) { return !n.closest('[hidden]') && !n.disabled && n.offsetParent !== null; });
    if (!list.length) return;
    var first = list[0], last = list[list.length - 1], a = document.activeElement;
    if (e.shiftKey && (a === first || !ov.contains(a))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (a === last || !ov.contains(a))) { e.preventDefault(); first.focus(); }
  }

  openBtn.addEventListener('click', openVault);
  el.close.addEventListener('click', closeVault);
  el.pinForm.addEventListener('submit', function (e) { e.preventDefault(); tryPin(); });
  el.pinIn.addEventListener('input', function () {
    el.pinIn.value = el.pinIn.value.replace(/\D/g, '').slice(0, 4);
    say(el.pinMsg, '');
    clearTimeout(pinTimer);
    if (el.pinIn.value.length === 4) pinTimer = setTimeout(tryPin, 150);
  });
  el.pick.addEventListener('click', function () { el.file.click(); });
  el.swap.addEventListener('click', function () { el.file.click(); });
  el.file.addEventListener('change', onFile);
  el.del.addEventListener('click', onDelete);
  ov.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeVault(); return; }
    if (e.key === 'Tab') trapTab(e);
  });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden' && st === 'view') closeVault(); });
  window.addEventListener('pagehide', function () { if (st === 'view') closeVault(); });
})();
