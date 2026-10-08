# 首爾自由行手冊

手機網頁（PWA）：安全卡 + 每日路線 + 地鐵圖，可加到 iPhone 主畫面離線使用。

- 網址：https://wangty318.github.io/seoul-wh1317/seoul-pwa/ （短網址 https://wangty318.github.io/seoul-wh1317/ 會自動跳過去）
- 安裝：用 **Safari** 打開網址 → 等右上角出現「✓ 離線可用」→ 分享 → 加入主畫面。
- 更新：有網路時打開就是最新版；App 開著時若出現「↻ 有新版本」，點一下即可。頁面最底下可看版本與更新時間。
- 維護：見 [CLAUDE.md](CLAUDE.md)。重建 `python3 src/build.py`，測試 `NODE_PATH=$(npm root -g) node tests/pwa_test.js` 與 `tests/layout_test.js`。
