# 首爾自由行手冊（PWA）— 維護手冊

給之後任何 Claude session 看的操作說明。使用者說「改行程／改安全卡／同步」時，照「更新流程」做。

## 這是什麼
- 5 天首爾自由行（10/13–10/17）的手機網頁，給使用者（汪泰右）的女友與她的閨蜜用，兩人都用 **iPhone**，住 Ever8 Serviced Residence（梨大站旁）。
- 兩個大分頁：**安全卡**（預設）與**路線**（D1–D5 + 總覽 + 地鐵圖）。可「加入主畫面」離線使用。
- 線上網址（正式）：https://wangty318.github.io/seoul-wh1317/seoul-pwa/ （GitHub Pages，`main` / `/(root)`）。短網址 https://wangty318.github.io/seoul-wh1317/ 只是導向頁，會自動跳到正式網址。**使用者已把連結傳給她們**，兩個網址都必須持續可用。
- **公開 repo**：不要放護照號碼、電話、訂房編號。緊急電話與勾選狀態由她們在手機上自己填（localStorage），不進 repo。
- 使用者偏好：繁體中文、簡潔直接、客觀不一味附和。行程不要時間／班次細節（她們自己動態查），每日路線只畫到商圈，文字要少、現場好讀。

## 更新流程
1. **取得推送權限**：`add_repo(owner="wangty318", repo="seoul-wh1317", access="push")`，照回傳指示 clone 後 `register_repo_root`。前提有兩個：使用者已在 claude.ai 連結 GitHub，且已在他的 GitHub 帳號安裝 Claude GitHub App 並授權這個 repo（https://github.com/apps/claude/installations/select_target）。若回傳 `push_check: refused`，代表第二項還沒做，推送會被拒絕，請使用者先完成。
2. **改來源**（見「來源在哪」）。**不要手改**根目錄的 `index.html`（導向頁）與整個 `seoul-pwa/`（`index.html`、`sw.js`、`manifest.webmanifest`、`version.json`、`icons/`、`seoul-metro-map.jpg`），它們都是 build 產物。
3. **重建**：`python3 src/build.py`（輸出到 `seoul-pwa/` 並更新根目錄導向頁；內容沒變時輸出完全相同，不會產生多餘的 git 變更）。
4. **測試**：`NODE_PATH=$(npm root -g) node tests/pwa_test.js`（27 項）與 `NODE_PATH=$(npm root -g) node tests/layout_test.js`（8 項，兩個網址都能開），必須全過。再用 Playwright 手機尺寸（390×844）截圖看改到的畫面。
5. **提交並推到 `main`**，commit 訊息用中文簡述改了什麼，結尾附上 session 規定的 attribution。
6. **確認上線**：等 1–3 分鐘，WebFetch `https://wangty318.github.io/seoul-wh1317/seoul-pwa/version.json`，其中 `build` 要和本機 `seoul-pwa/version.json` 一致。
7. **回報使用者**：改了什麼（白話）、版本號與更新時間、她們怎麼拿到（見下）。

## 她們怎麼拿到更新
- 有網路時打開 App 就是最新版：頁面請求會強制向伺服器重新驗證（避開 GitHub Pages 約 10 分鐘的 HTTP 快取）。
- App 一直開著或從背景回來：回到前景會檢查更新。有新版時頂部右側出現綠色「↻ 有新版本」，點一下重新載入。
- 沒有網路：顯示上一次存好的版本。頁面最底下有「版本 xxxxxxx · 更新於 MM/DD HH:MM」，可請她們回報來核對有沒有拿到最新版。
- 頂部右側的「✓ 離線可用」是 service worker 實際檢查快取後的結果；「! 未存好」表示有檔案沒存成功，連上網點一下重試。
- 頁面與圖片資源分開快取：只改行程不會重新下載 1.7 MB 的地鐵圖。

## 來源在哪（全在 `src/`）
| 要改什麼 | 去哪改 |
|---|---|
| 路線 D1–D5、總覽、怎麼認方向 | `gen_site.py`：`# ===== D1` … `# ===== overview` 各區塊（`dN_nodes` 是站點，`dN` 是整頁） |
| 安全卡內容 | `seoul-safety.html`（原始），加上 `gen_site.py` 的 `sub(舊字串, 新字串)` 替換與 `DOCS`（證件與護照清單） |
| 地鐵圖按鈕與縮放全螢幕 | `gen_site.py` 的 `MAPBLOCK`；圖檔 `seoul-metro-map.jpg`（全尺寸）、`metro-thumb.jpg`（縮圖，內嵌進頁面） |
| 兩個大分頁與 hash 路由 | `gen_site.py` 的 `TOP_OPEN`、`TOPSCRIPT`、`EXTRA3` |
| 共用的卡片／路線圖繪製函式 | `gen_v3_backup.py` 前半（`strip`、`card`、`head`…；只被 `exec` 前半段，後面是被改寫的舊外殼）；`seoul-routes-v2.html` 提供舊版 CSS |
| PWA 外殼、離線與更新提示 | `make_pwa.py`、`pwa.js`、`pwa.css`、`sw.template.js` |
| 圖示（一般不用動） | `make_icons.py`（要 Pillow 與 Noto Sans CJK TC 字型）→ `src/icons/` |

`gen_site.py` 是層層補丁出來的，改動時先用 `grep` 找到要改的字串，一次只改一處，改完 build 並看輸出。

## 不要踩的地方
- `sw.template.js` 裡頁面請求的 `cache: 'no-cache'` **不能拿掉**；測試有負向對照（拿掉後 4 項會失敗）。
- 全部使用**相對路徑**，網站放在 `/<repo>/seoul-pwa/` 子路徑下才會運作；不要改成 `/` 開頭的絕對路徑。
- 離線時網路字型不可靠，PWA 版刻意用系統字型（iPhone 是蘋方-繁）。
- 從沒在 iPhone 實機測過（沙盒只有 Chromium、沒有 WebKit）；不要宣稱「iPhone 已驗證」。實機驗證方法：用主畫面圖示開啟 → 看到「✓ 離線可用」→ 開飛航模式並滑掉 App → 重開。
- 同一個網址在 Safari 分頁與「加入主畫面」的 App 是兩份獨立儲存空間（勾選與填寫的緊急電話不互通）。
- **站點固定放在 `seoul-pwa/`，不要搬到根目錄或改資料夾名稱**：連結已經傳給她們，已安裝的主畫面圖示綁定的是安裝當下的網址，搬了她們就收不到更新。根目錄的 `index.html` 只是導向頁。

## 待使用者決定（截至 2026-10-08）
- D2 術後那晚 新沙 → 聖水 / 梨大 怎麼走：安全卡寫「一律叫 Kakao T」，路線頁把地鐵畫成備案，兩邊尚未統一。外國遊客能否註冊 Kakao T 各來源說法不一，建議寫成「Kakao T / k.ride / Uber 擇一，出發前先註冊並綁卡」。
- D5 返程日行程（12:00 退房、23:00 班機）。
- apM 20:00 是入場時間還是約會時間。
- iPhone 的 Apple Wallet T-money 只收 Mastercard / AmEx / 銀聯（Visa 不行，資料到 2026/4）；用 Visa 的人要買實體 T-money 卡。
