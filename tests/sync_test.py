"""安全卡與路線兩個分頁的內容同步檢查（讀 repo 目前建好的 seoul-pwa/index.html，唯讀，不需要瀏覽器）。
用法：  python3 tests/sync_test.py
背景：兩個分頁的每日地點曾經各改各的而漂移。現在 src/gen_site.py 的 PLACES 是共用來源，這個測試確認建出來的兩邊真的一致。
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
page = open(os.path.join(HERE, '..', 'seoul-pwa', 'index.html'), encoding='utf-8').read()

a = page.index('<template id="safety-tpl">')
safety = page[a:page.index('</template>', a)]
routes = page[page.index('<div id="top-routes"'):]


def plain(h):
    h = re.sub(r'<(script|style|svg)\b.*?</\1>', ' ', h, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h)))


def norm(label):
    """路線頁 chip 標籤 → 安全卡寫法：去掉「晚餐：」前綴與「（Naver）」後綴"""
    return re.sub(r'（Naver）$', '', re.sub(r'^晚餐：', '', html.unescape(label))).strip()


results = []


def ok(name, cond, extra=''):
    results.append((cond, name, extra))


# ---- 每天的卡片 ----
cards = re.split(r'<article class="day">', safety)[1:]          # D1..D5
ok('安全卡有 D1–D5 五張每日卡', len(cards) == 5, len(cards))

for i, day in enumerate(['d1', 'd2', 'd3', 'd4']):
    panel = re.search(r'id="p-%s".*?(?=id="p-d\d"|id="p-ov"|<details|$)' % day, routes, re.S).group(0)
    r_labels = [norm(m) for m in re.findall(r'<a href="[^"]*" target="_blank" rel="noopener">(.*?)</a>', panel)]
    r_labels = [l for l in r_labels if not re.match(r'\d{1,2}:\d{2}', l)]   # 「18:30 新沙站 3 號口」是時間點，不是地點
    card_text = plain(cards[i])
    s_chips = [html.unescape(m) for m in re.findall(r'<span class="chip">(.*?)</span>', cards[i])]
    missing = [l for l in r_labels if l not in card_text]
    extra = [c for c in s_chips if c not in r_labels]
    ok('%s 路線頁的每個地點，安全卡這天都有' % day.upper(), r_labels and not missing, '缺：' + '、'.join(missing))
    ok('%s 安全卡這天沒有路線頁沒有的地點' % day.upper(), not extra, '多：' + '、'.join(extra))

# ---- 日期、固定資訊兩邊都要有 ----
for d in ['10/13（二）', '10/14（三）', '10/15（四）', '10/16（五）', '10/17（六）']:
    ok('兩個分頁都有日期 ' + d, d in plain(safety) and d in plain(routes))
for fact in ['314 m', '15:00', '12:00', '23:00', 'Kakao T', '18:30', '20:00', '汗蒸幕']:
    ok('兩個分頁都提到「%s」' % fact, fact in plain(safety) and fact in plain(routes))

fails = [r for r in results if not r[0]]
for good, name, extra in results:
    print('%s | %s%s' % ('PASS' if good else 'FAIL', name, (' | ' + str(extra)) if (not good and extra) else ''))
print('\n%d/%d passed' % (len(results) - len(fails), len(results)))
sys.exit(1 if fails else 0)
