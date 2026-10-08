"""把 src/seoul-routes.html（gen_site.py 的輸出）包成可離線的 PWA。
輸出：index.html、sw.js、manifest.webmanifest、version.json、seoul-metro-map.jpg、icons/
預設輸出到 repo 的 seoul-pwa/ 資料夾（正式網址 https://wangty318.github.io/seoul-wh1317/seoul-pwa/），
並在 repo 根目錄放一個導向它的 index.html，讓短網址也能用；測試時用 --out 指到暫存資料夾（不會動根目錄）。
冪等：內容沒變就不會換「更新時間」，所以重建不會產生多餘的 git 變更。
"""
import argparse, datetime, hashlib, json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
DEFAULT_OUT = os.path.join(REPO, 'seoul-pwa')
ap.add_argument('--out', default=DEFAULT_OUT)
ap.add_argument('--stamp', help='覆寫「更新於」字樣（測試用），例如 "10/08 23:30"')
args = ap.parse_args()
OUT = os.path.abspath(args.out)


def rd(name, mode='r'):
    p = os.path.join(HERE, name)
    return open(p, mode, **({} if 'b' in mode else {'encoding': 'utf-8'})).read()


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else p.encode('utf-8'))
    return h.hexdigest()


# ---------- 1. 頁面（index.html 範本，含三個待填欄位） ----------
src = rd('seoul-routes.html')
m = re.search(r'<title>(.*?)</title>', src)
title = m.group(1)
src = src.replace(m.group(0), '', 1)
# 離線時網路字型不可靠 → 改用系統字型（iPhone 有蘋方-繁），線上線下外觀一致
src = re.sub(r'<link rel="preconnect" href="https://fonts\.[^>]*>\s*', '', src)
src = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\s*', '', src)
src = src.replace('--font-body: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif;',
                  '--font-body: "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;')
src = src.replace('--font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;',
                  '--font-mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, "IBM Plex Mono", monospace;')
assert 'fonts.g' not in src, 'still references Google Fonts'

HEAD = f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="build-id" content="__BUILD_ID__">
<meta name="robots" content="noindex,nofollow">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="首爾手冊">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#f2f6f3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0e1613" media="(prefers-color-scheme: dark)">
<style>:root{{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}html{{scroll-padding-top:env(safe-area-inset-top,0px);-webkit-text-size-adjust:100%}}body{{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#f2f6f3;color:#14231d}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}</style>
</head>
<body>
'''
index_tpl = (HEAD + src
             + '<p class="buildinfo">版本 __BUILD_ID7__ · 更新於 __STAMP__</p>\n'
             + '<style>\n' + rd('pwa.css') + '</style>\n'
             + '<script>\n' + rd('pwa.js') + '</script>\n</body>\n</html>\n')

# ---------- 2. manifest ----------
manifest = json.dumps({
    'name': title, 'short_name': '首爾手冊', 'lang': 'zh-Hant',
    'start_url': './', 'scope': './', 'display': 'standalone',
    'background_color': '#f2f6f3', 'theme_color': '#007d3f',
    'icons': [
        {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        {'src': 'icons/icon-512-maskable.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
    ],
}, ensure_ascii=False, indent=2)

# ---------- 3. 版本：build = 頁面內容雜湊；stamp 只在內容真的變了才更新 ----------
build = sha(index_tpl, manifest)[:12]
prev = {}
try:
    prev = json.load(open(os.path.join(OUT, 'version.json'), encoding='utf-8'))
except Exception:
    pass
tz = datetime.timezone(datetime.timedelta(hours=8))                       # 台北時間
stamp = args.stamp or (prev['stamp'] if prev.get('build') == build and prev.get('stamp')
                       else datetime.datetime.now(tz).strftime('%m/%d %H:%M'))
index = index_tpl.replace('__BUILD_ID__', build).replace('__BUILD_ID7__', build[:7]).replace('__STAMP__', stamp)

icons = sorted(os.listdir(os.path.join(HERE, 'icons')))
asset_bytes = [rd('seoul-metro-map.jpg', 'rb')] + [rd('icons/' + n, 'rb') for n in icons]
asset_v = sha(*asset_bytes)[:10]
sw_tpl = rd('sw.template.js')
page_v = sha(index, manifest, sw_tpl)[:10]
sw = sw_tpl.replace('__PAGE_V__', page_v).replace('__ASSET_V__', asset_v).replace('__BUILD_ID__', build)
version = {'build': build, 'stamp': stamp, 'page': page_v, 'assets': asset_v}

# ---------- 4. 寫出 ----------
os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)
for stale in os.listdir(os.path.join(OUT, 'icons')):
    os.remove(os.path.join(OUT, 'icons', stale))
for n in icons:
    shutil.copy(os.path.join(HERE, 'icons', n), os.path.join(OUT, 'icons', n))
shutil.copy(os.path.join(HERE, 'seoul-metro-map.jpg'), os.path.join(OUT, 'seoul-metro-map.jpg'))
for name, text in [('index.html', index), ('manifest.webmanifest', manifest), ('sw.js', sw),
                   ('version.json', json.dumps(version, ensure_ascii=False, indent=2) + '\n')]:
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n').write(text)

# ---------- 5. 根目錄導向頁：短網址 https://wangty318.github.io/seoul-wh1317/ 會自動跳到 seoul-pwa/ ----------
# 站點固定放在 seoul-pwa/：連結已經傳出去，已安裝的主畫面圖示綁定的是安裝當下的網址，不能再搬。
if OUT == DEFAULT_OUT:
    stub = ('<!doctype html>\n<html lang="zh-Hant"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + title + '</title><meta name="robots" content="noindex,nofollow">'
            '<meta http-equiv="refresh" content="0; url=seoul-pwa/">'
            "<script>location.replace('seoul-pwa/' + location.search + location.hash);</script>"
            '</head><body><p><a href="seoul-pwa/">開啟 ' + title + '</a></p></body></html>\n')
    open(os.path.join(REPO, 'index.html'), 'w', encoding='utf-8', newline='\n').write(stub)

print('build', build, '| stamp', stamp, '| page', page_v, '| assets', asset_v, '| out', OUT)
