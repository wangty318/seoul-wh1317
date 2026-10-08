import re, html, math, urllib.parse

SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')   # 所有輸入檔都在 src/，不使用絕對路徑
old = open(SP + 'seoul-routes-v2.html', encoding='utf-8').read()
base_style = re.search(r'<style>(.*?)</style>', old, re.S).group(1)


def section(sid):
    return re.search(r'  <section id="%s">.*?\n  </section>' % sid, old, re.S).group(0)


def esc(s):
    return html.escape(s, quote=True)


def wl(s, fs=11.5):
    return sum((fs if ord(c) > 0x2E80 else fs * 0.56) for c in s)


def gmap(q):
    return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(q)


# ---------------------------------------------------------------- strip
def strip(nodes, segs, spurs, label):
    X = 40
    y = 28
    ys = []
    layout = []
    for i, nd in enumerate(nodes):
        ys.append(y)
        sp = spurs.get(i, [])
        rows = []
        for k, ch in enumerate(sp):
            rows.append(y + 52 + 80 * k)
        layout.append(rows)
        last = rows[-1] if rows else y
        y = last + 96
    allrows = [r for rows in layout for r in rows]
    H = max(ys[-1] + 34, (max(allrows) + 60) if allrows else 0)
    o = []
    o.append('<svg viewBox="0 0 400 %d" role="img" aria-label="%s">' % (H, esc(label)))
    # main segments
    for i, sg in enumerate(segs):
        y1, y2 = ys[i], ys[i + 1]
        cls = 'sg ' + sg['line'] + (' dash' if sg['line'] == 'walk' else '')
        o.append('<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (cls, X, y1, X, y2))
    # spurs
    for i, sp in enumerate(spurs.items() if False else []):
        pass
    for i, chains in spurs.items():
        for k, ch in enumerate(chains):
            ry = layout[i][k]
            n = len(ch)
            xs = [210] if n == 1 else [150, 300]
            # elbow from main line
            px = X
            for j, hop in enumerate(ch):
                nx = xs[j]
                cls = 'sg ' + hop['line'] + (' dash' if (hop.get('est') or hop['line'] == 'walk') else '')
                o.append('<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (cls, px, ry, nx, ry))
                mid = (px + nx) / 2
                lines = hop['text'].split('\n')
                for t, ln in enumerate(lines):
                    ty = ry - 9 - 13 * (len(lines) - 1 - t)
                    o.append('<text class="tm mid" x="%.0f" y="%d">%s</text>' % (mid, ty, esc(ln)))
                px = nx
            o.append('<circle class="spurdot" cx="%d" cy="%d" r="4"/>' % (X, ry))
            for j, hop in enumerate(ch):
                nx = xs[j]
                if hop.get('dest', True):
                    o.append('<circle class="dest" cx="%d" cy="%d" r="7"/>' % (nx, ry))
                else:
                    o.append('<circle class="st %s" cx="%d" cy="%d" r="6"/>' % (hop['line'], nx, ry))
                o.append('<text class="tb mid" x="%d" y="%d">%s</text>' % (nx, ry + 22, esc(hop['name'])))
                if hop.get('sub'):
                    o.append('<text class="tm mid" x="%d" y="%d">%s</text>' % (nx, ry + 35, esc(hop['sub'])))
    # nodes
    for i, nd in enumerate(nodes):
        col = segs[i]['line'] if i < len(segs) else segs[i - 1]['line']
        cls = 'st ' + col
        r = 8 if nd.get('hub') else 7
        o.append('<circle class="%s" cx="%d" cy="%d" r="%d"/>' % (cls, X, ys[i], r))
        t = '<text x="%d" y="%d"><tspan class="tb">%s</tspan>' % (X + 18, ys[i] + 4, esc(nd['n']))
        if nd.get('s'):
            t += '<tspan class="tm" dx="7">%s</tspan>' % esc(nd['s'])
        t += '</text>'
        o.append(t)
    # seg pills
    for i, sg in enumerate(segs):
        ty = ys[i + 1] - 36
        txt = sg['text']
        w = wl(txt) + 18
        o.append('<rect class="pill %s" x="%d" y="%d" width="%.0f" height="20" rx="10"/>' % (sg['line'], X + 10, ty - 13, w))
        o.append('<text class="tx" x="%d" y="%d">%s</text>' % (X + 19, ty + 1, esc(txt)))
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- radial
def radial(hub, hub_sub, spots, label, H=384):
    cx, cy = 200, 192
    R = lambda m: 34 + 12 * m
    o = ['<svg viewBox="0 0 400 %d" role="img" aria-label="%s">' % (H, esc(label))]
    for m in (5, 10):
        o.append('<circle class="ring" cx="%d" cy="%d" r="%d"/>' % (cx, cy, R(m)))
        o.append('<text class="tm" x="%d" y="%d">%d 分</text>' % (cx + 4, cy + R(m) + 13, m))
    pts = []
    for s in spots:
        a = math.radians(s['a'])
        rr = R(float(s['mt']))
        x = cx + rr * math.sin(a)
        y = cy - rr * math.cos(a)
        pts.append((x, y))
        cls = 'rl' + (' dash' if s['est'] else '')
        o.append('<line class="%s" x1="%d" y1="%d" x2="%.1f" y2="%.1f"/>' % (cls, cx, cy, x, y))
    for s, (x, y) in zip(spots, pts):
        # minute pill on the line
        mx = cx + (x - cx) * 0.6
        my = cy + (y - cy) * 0.6
        txt = ('約 %s 分' if s['est'] else '%s 分') % s['mt']
        w = wl(txt, 10.5) + 12
        o.append('<rect class="mp" x="%.1f" y="%.1f" width="%.0f" height="17" rx="8.5"/>' % (mx - w / 2, my - 8.5, w))
        o.append('<text class="tm mid" x="%.1f" y="%.1f">%s</text>' % (mx, my + 4, esc(txt)))
    for s, (x, y) in zip(spots, pts):
        o.append('<circle class="nb" cx="%.1f" cy="%.1f" r="11"/><text class="nt" x="%.1f" y="%.1f">%d</text>' % (x, y, x, y + 4.5, s['n']))
        w = wl(s['short'], 11.5)
        if x > cx + 22 and x + 16 + w <= 396:
            o.append('<text class="tx" x="%.1f" y="%.1f">%s</text>' % (x + 16, y + 4, esc(s['short'])))
        elif x < cx - 22 and x - 16 - w >= 4:
            o.append('<text class="tx end" x="%.1f" y="%.1f">%s</text>' % (x - 16, y + 4, esc(s['short'])))
        else:
            lx = min(max(x, w / 2 + 4), 396 - w / 2)
            o.append('<text class="tx mid" x="%.1f" y="%.1f">%s</text>' % (lx, y - 18, esc(s['short'])))
    o.append('<circle class="hubc" cx="%d" cy="%d" r="15"/>' % (cx, cy))
    o.append('<text class="tb mid halo" x="%d" y="%d">%s</text>' % (cx, cy + 36, esc(hub)))
    if hub_sub:
        o.append('<text class="tm mid halo" x="%d" y="%d">%s</text>' % (cx, cy + 50, esc(hub_sub)))
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- spot list
def spot_list(spots):
    o = ['<ul class="spots">']
    for s in spots:
        tag = ('約 %s 分（估）' if s['est'] else '%s 分') % s['mt']
        meta = []
        if s.get('exit'):
            meta.append(s['exit'])
        if s.get('hours'):
            meta.append(s['hours'])
        o.append('<li class="spot"><span class="num">%d</span><div class="sb"><b>%s</b>'
                 '<span class="ko">%s</span><span class="sm">%s</span>%s</div>'
                 '<div class="st2"><b>%s</b><a href="%s" target="_blank" rel="noopener">地圖</a></div></li>'
                 % (s['n'], esc(s['name']), esc(s['ko']), esc(' · '.join(meta)),
                    ('<span class="sm">' + esc(s['note']) + '</span>') if s.get('note') else '',
                    esc(tag), esc(gmap(s['q']))))
    o.append('</ul>')
    return '\n'.join(o)


def unconfirmed(title, items):
    o = ['<div class="todo"><b>%s</b><ul>' % esc(title)]
    for it in items:
        o.append('<li>%s</li>' % it)
    o.append('</ul></div>')
    return '\n'.join(o)


def head(day, date, area, summary):
    return ('<header class="dayhead"><span class="day-no">%s</span><div><h2>%s</h2><p class="section-note">%s</p></div></header>'
            '<p class="sum">%s</p>' % (day, esc(area), esc(date), summary))


def alight(title, lines):
    o = ['<div class="alight"><b>%s</b><ul>' % esc(title)]
    for l in lines:
        o.append('<li>%s</li>' % l)
    o.append('</ul></div>')
    return '\n'.join(o)


def card(svg, cap, legend=True):
    leg = ''
    if legend:
        leg = ('<div class="legend"><span><i class="sw" style="background:var(--l2)"></i>2 號線</span>'
               '<span><i class="sw" style="background:var(--l3)"></i>3 號線</span>'
               '<span><i class="sw" style="background:var(--l4)"></i>4 號線</span>'
               '<span><i class="sw" style="background:var(--larex)"></i>機場鐵路</span>'
               '<span><i class="sw dashsw"></i>步行或估算</span></div>')
    return '<div class="map"><p class="cap">%s</p>%s%s</div>' % (esc(cap), svg, leg)


def notes(items, cls='note'):
    return '<ul class="%s">%s</ul>' % (cls, ''.join('<li>%s</li>' % i for i in items))


# =============================================================== D1
# 路線 1：樂天官網建議（機場鐵路一般列車 → 弘大入口 → 2 號線 → 乙支路入口）
d1a_nodes = [
    {'n': '仁川機場 T1', 's': '인천공항 1터미널'},
    {'n': '弘大入口', 's': '홍대입구 · 換乘', 'hub': True},
    {'n': '乙支路入口', 's': '을지로입구 · 2 號線', 'hub': True},
]
d1a_segs = [
    {'line': 'arex', 'text': '一般列車 約 50 分（估）'},
    {'line': 'l2', 'text': '2 號線內環 6 站 約 13 分（估）'},
]
d1a_spurs = {
    1: [[{'line': 'l2', 'est': True, 'text': '2 號線 1 站\n約 3 分（估）', 'name': '新村', 'sub': '寄行李（先問可否）', 'dest': False}]],
    2: [
        [{'line': 'walk', 'text': '直通地下 1 樓\n（樂天官網）', 'name': '樂天百貨', 'sub': '本店 10:30–20:00'}],
        [{'line': 'walk', 'est': True, 'text': '步行約 10–12 分\n（估）', 'name': '新世界百貨', 'sub': '本店 10:30 起'}],
    ],
}
d1a_svg = strip(d1a_nodes, d1a_segs, d1a_spurs, 'D1 路線 1：仁川機場經弘大入口到乙支路入口的路線與時間')

# 路線 2：直通列車 → 首爾站 → 4 號線（先逛新世界、明洞街）
d1_nodes = [
    {'n': '仁川機場 T1', 's': '인천공항 1터미널'},
    {'n': '首爾站', 's': '서울역', 'hub': False},
    {'n': '會賢', 's': '회현 · 4 號線', 'hub': True},
    {'n': '明洞', 's': '명동 · 4 號線', 'hub': True},
]
d1_segs = [
    {'line': 'arex', 'text': '直通列車 約 43 分'},
    {'line': 'l4', 'text': '轉 4 號線北行 1 站（轉乘約 8 分，估）'},
    {'line': 'l4', 'text': '1 站 約 3 分（估）'},
]
d1_spurs = {
    2: [[{'line': 'walk', 'text': '7 號口\n直通', 'name': '新世界百貨', 'sub': '本店 10:30 起'}]],
    3: [
        [{'line': 'walk', 'text': '5 號口\n步行約 5 分', 'name': '新世界百貨', 'sub': '另一個走法'}],
        [{'line': 'walk', 'est': True, 'text': '約 5 分\n（估）', 'name': 'NyuNyu', 'sub': '명동4길 22'}],
        [{'line': 'walk', 'est': True, 'text': '步行約 8–10 分\n（估）', 'name': '樂天百貨', 'sub': '本店至 20:00'}],
    ],
}
d1_svg = strip(d1_nodes, d1_segs, d1_spurs, 'D1 路線 2：仁川機場經首爾站到明洞的路線與時間')

d1 = '<div class="panel-body">' + head('D1', '10/13（二）· 抵達日', '機場到明洞百貨',
    '凌晨 05:30 落地，百貨 10:30 才開門，早上留給機場汗蒸幕。出機場有三種走法：樂天官網建議的機場鐵路轉 2 號線、直通列車轉 4 號線，以及機場巴士。你的行程是先樂天再新世界，所以先畫樂天官網的路線。') + \
    alight('建議下車站', [
        '<b>樂天百貨：乙支路入口站（2 號線）</b>。樂天官網寫出站可直接通到百貨地下 1 樓賣場。',
        '<b>新世界百貨：會賢站（4 號線）7 號口直通</b>。從樂天走過去約 10–12 分（估）。',
        '<b>明洞街（NyuNyu 等）：明洞站（4 號線）</b>，站在購物街中心。',
    ]) + \
    card(d1a_svg, '路線 1：機場 → 乙支路入口 → 樂天（樂天官網建議）') + \
    notes([
        '搭<b>一般列車（일반열차）</b>才會停弘大入口；直通列車不停，直接開到首爾站。月台看到「直通」字樣先別上。',
        '到弘大入口後換 2 號線，要搭<b>往新村方向（內環）</b>，6 站到乙支路入口。',
        '拖著行李不想逛：同樣到弘大入口，換 2 號線 1 站到新村，先把行李寄在 Ever 8（入住 15:00，要先問能不能寄），再搭內環 5 站到乙支路入口。',
    ]) + \
    card(d1_svg, '路線 2：機場 → 首爾站 → 明洞（想先逛新世界或明洞街）') + \
    '<h3 class="h3">機場巴士（樂天官網列出兩條）</h3>' + \
    notes([
        '<b>6701</b>：T1 一樓 3 號乘車處（T2 地下一樓 18 號），在<b>乙支路入口站（首爾樂天酒店）</b>下車，就在樂天百貨旁。有第三方資料把 T1 乘車處寫成 4 號，以現場看板為準。',
        '<b>6015</b>：T1 一樓 5 號乘車處（T2 地下一樓 28 號），在<b>明洞大使宜必思酒店</b>下車，離樂天還要再走一段（官網沒寫分鐘）。',
        '第三方資料：6015 首班約 05:25–05:47、末班約 22:55–23:18；6701 首班約 05:13、末班約 23:10。車資各來源寫法不同（15,000–17,000 韓元），車程寫約 75–90 分，視路況。這幾項我沒有官方來源，出發前請用 Naver Map、Kakao Map 或機場官網確認。',
        '樂天官網頁面上兩條路線的「車站編號」寫成同一組數字（92641、35612），可能是頁面複製錯誤，所以我沒有採用，請認乘車處號碼。',
    ]) + \
    '<h3 class="h3">怎麼選</h3>' + \
    notes([
        '<b>帶著行李直接逛樂天</b>：6701 最省事，不用轉乘，下車即樂天。代價是巴士受路況影響，時間不如鐵路穩。',
        '<b>先去寄行李</b>：路線 1 到弘大入口多搭 1 站就是新村，寄完再回頭，總繞路不多。',
        '<b>想先逛新世界、明洞街</b>：路線 2 的直通列車到首爾站只要 43 分，但首爾站轉 4 號線要走一段，帶行李較累。',
        '時間粗估（含轉乘，不含等車；皆為估算）：路線 1 到乙支路入口約 70 分，路線 2 到明洞約 57 分。路線 2 再從明洞走去樂天要 8–10 分，所以到樂天兩者差不多。',
    ]) + \
    '<h3 class="h3">地點</h3>' + spot_list([
        {'n': 1, 'name': '樂天百貨本店', 'ko': '서울 중구 남대문로 81', 'exit': '乙支路入口站 直通地下 1 樓', 'hours': '10:30–20:00', 'mt': '1', 'est': False,
         'note': '樂天官網確認營業時間與地鐵直通；從明洞站走約 8–10 分（估）', 'q': '서울 중구 남대문로 81 롯데백화점 본점'},
        {'n': 2, 'name': '新世界百貨本店', 'ko': '서울 중구 소공로 63', 'exit': '會賢站 7 號口直通', 'mt': '5', 'est': False,
         'note': '從明洞站 5 號口步行約 5 分', 'q': '서울 중구 소공로 63 신세계백화점 본점'},
        {'n': 3, 'name': 'NyuNyu 明洞店', 'ko': '서울 중구 명동4길 22 1–4층', 'hours': '10:00–23:00', 'mt': '5', 'est': True,
         'note': '從明洞站出發', 'q': '서울 중구 명동4길 22'},
    ]) + \
    unconfirmed('還沒定位的點（地圖上沒畫）', [
        'MLB、MIXXO、8 seconds、Verish、Ept：都在明洞商圈或百貨內，我查不到確切地址。把 Naver Map 連結或地址給我，我補上。',
        '晚餐「無垢屋」：查不到店址。',
    ]) + '</div>'

# =============================================================== D2
d2a_nodes = [
    {'n': '新村', 's': '신촌 · 住宿'},
    {'n': '市廳', 's': '시청'},
    {'n': '東大門歷史文化公園', 's': ''},
    {'n': '聖水', 's': '성수', 'hub': True},
]
d2a_segs = [
    {'line': 'l2', 'text': '內環 4 站 約 9 分（估）'},
    {'line': 'l2', 'text': '4 站 約 9 分（估）'},
    {'line': 'l2', 'text': '6 站 約 13 分（估）'},
]
d2a_svg = strip(d2a_nodes, d2a_segs, {}, 'D2 新村到聖水的 2 號線路線與時間')

d2_spots = [
    {'n': 1, 'name': 'Tamburins 聖水旗艦店', 'short': 'Tamburins', 'ko': '서울 성동구 연무장5길 8', 'exit': '4 號口', 'hours': '11:00–21:00',
     'mt': '5', 'est': True, 'note': '同巷的 Dior 步行約 5 分', 'q': '서울 성동구 연무장5길 8', 'a': 35},
    {'n': 2, 'name': 'Matin Kim 本店', 'short': 'Matin Kim 本店', 'ko': '서울 성동구 연무장3길 9', 'exit': '4 號口',
     'mt': '6', 'est': True, 'q': '서울 성동구 연무장3길 9', 'a': 80},
    {'n': 3, 'name': 'Matin Kim 旗艦店', 'short': 'Matin Kim 旗艦', 'ko': '서울 성동구 아차산로5길 24-33 1층', 'exit': '1 號口', 'hours': '約 11:00–20:00',
     'mt': '6', 'est': True, 'q': '서울 성동구 아차산로5길 24-33', 'a': 285},
    {'n': 4, 'name': 'Human Made', 'short': 'Human Made', 'ko': '서울 성동구 성수이로7길 39', 'hours': '11:00–20:00',
     'mt': '9', 'est': True, 'note': '2 樓有 Blue Bottle', 'q': '서울 성동구 성수이로7길 39', 'a': 235},
    {'n': 5, 'name': '自然道鹽麵包', 'short': '自然道鹽麵包', 'ko': '서울 성동구 연무장길 56-1 1층', 'hours': '9:00–22:00',
     'mt': '10', 'est': True, 'note': '只能外帶', 'q': '서울 성동구 연무장길 56-1', 'a': 125},
    {'n': 6, 'name': 'Stand Oil', 'short': 'Stand Oil', 'ko': '서울 성동구 연무장11길 19',
     'mt': '10', 'est': True, 'q': '서울 성동구 연무장11길 19', 'a': 165},
]
d2_svg = radial('聖水站', '2 號線', d2_spots, 'D2 聖水站周邊店家的步行距離示意圖')

d2b_nodes = [
    {'n': '聖水', 's': '17:15 前出發'},
    {'n': '江南', 's': '강남 · 2 號線轉乘'},
    {'n': '新沙', 's': '신사 · 3 號口'},
]
d2b_segs = [
    {'line': 'l2', 'text': '內環 11 站 約 25 分（估）'},
    {'line': 'walk', 'text': '新盆唐線 3 站 約 8 分（估）'},
]
d2b_svg = strip(d2b_nodes, d2b_segs, {}, 'D2 聖水到新沙站的路線')

d2 = '<div class="panel-body">' + head('D2', '10/14（三）· 白天聖水，傍晚新沙', '聖水洞 → 新沙',
    '白天從新村搭 2 號線直達聖水，不用換乘。店家集中在 3、4 號口外的連武場街（연무장길）一帶，走得完。傍晚 18:30 前要到新沙站。') + \
    alight('建議下車站', [
        '<b>聖水站（2 號線）3 或 4 號口</b>：兩個出口都進到主要街區，Tamburins、Matin Kim 本店、自然道都在這邊。',
        'Matin Kim 旗艦店在<b>1 號口</b>方向，與其他店分在不同側。',
    ]) + \
    card(d2a_svg, '路線圖 1：新村 → 聖水（一路 2 號線）') + \
    card(d2_svg, '步行圖：聖水站出來後（圈是步行時間；方位為示意）', legend=False) + \
    '<h3 class="h3">地點</h3>' + spot_list(d2_spots) + \
    unconfirmed('還沒定位的點（地圖上沒畫）', [
        'Wacky Willy：官方旗艦店在<b>弘大</b>（잔다리로 26），聖水有沒有店我查不到。你排在 D2，是不是指弘大那間？若是，可改排 D4。',
        'Satur、Atiissu、Double Lover 聖水旗艦店、The North Face White Label 聖水店：查不到地址。',
        '晚餐「祖傳三代馬鈴薯排骨湯」：查不到店址。',
    ]) + \
    '<h3 class="h3">傍晚去新沙</h3>' + \
    card(d2b_svg, '路線圖 2：聖水 → 新沙站 3 號口', legend=True) + \
    notes([
        '18:30 到診所，建議 <b>17:15 前</b>離開聖水，路上約 40 分加上找路與報到。',
        '新盆唐線的站序是我整理的，出發前用 Naver Map 核對；也可直接 Kakao T，白天車流不穩，預估時間先看 App。',
        '<b>夜間回程不搭地鐵</b>，Kakao T 叫車回新村，上車前把車牌傳給家人。',
    ], 'note warn') + '</div>'

# =============================================================== D3
d3_nodes = [
    {'n': '新村', 's': '신촌 · 住宿'},
    {'n': '市廳', 's': '시청'},
    {'n': '乙支路3街', 's': '을지로3가', 'hub': True},
    {'n': '乙支路4街', 's': '을지로4가', 'hub': True},
    {'n': '東大門歷史文化公園', 's': '', 'hub': True},
]
d3_segs = [
    {'line': 'l2', 'text': '內環 4 站 約 9 分（估）'},
    {'line': 'l2', 'text': '2 站 約 5 分（估）'},
    {'line': 'l2', 'text': '1 站 約 2 分（估）'},
    {'line': 'l2', 'text': '1 站 約 2 分（估）'},
]
d3_spurs = {
    2: [[{'line': 'l3', 'text': '3 號線往五輪\n2 站 約 5 分', 'name': '東國大入口', 'sub': '5 號口', 'dest': False},
         {'line': 'walk', 'est': True, 'text': '接駁車\n時間未查', 'name': '新羅免稅店', 'sub': '09:30–20:00'}]],
    3: [[{'line': 'walk', 'est': True, 'text': '4 號口\n步行約 5 分', 'name': '光藏市場', 'sub': '過清溪川'}]],
    4: [[{'line': 'walk', 'est': True, 'text': '14 號口\n步行約 3 分', 'name': 'APM', 'sub': '20:00'}]],
}
d3_svg = strip(d3_nodes, d3_segs, d3_spurs, 'D3 新村到東大門一帶的路線、支線與時間')

d3 = '<div class="panel-body">' + head('D3', '10/15（四）· 光藏、新羅、東大門', '東大門一帶',
    '三個點分在 2 號線上相鄰的兩站和 3 號線一站。建議順序：早上先去新羅免稅店（09:30 開，20:00 關）→ 光藏市場 → 晚上 APM。') + \
    alight('建議下車站', [
        '<b>新羅免稅店</b>：乙支路3街下車，換 3 號線 2 站到<b>東國大入口站 5 號口</b>，再搭新羅飯店接駁車。這間在獎忠洞，不在東大門。',
        '<b>光藏市場</b>：乙支路4街站 4 號口。',
        '<b>APM</b>：東大門歷史文化公園站 14 號口，離乙支路4街只有 1 站，也可以步行過去。',
    ]) + \
    card(d3_svg, '路線圖：新村 → 東大門一帶（左線是 2 號線，右側是各點的支線）') + \
    '<h3 class="h3">地點</h3>' + spot_list([
        {'n': 1, 'name': '新羅免稅店 首爾店', 'ko': '서울 중구 동호로 249', 'exit': '東國大入口站 5 號口 + 接駁車', 'hours': '09:30–20:00', 'mt': '—', 'est': True,
         'note': '2 號線到乙支路3街，再 3 號線 2 站', 'q': '서울 중구 동호로 249 신라면세점'},
        {'n': 2, 'name': '光藏市場', 'ko': '서울 종로구 창경궁로 88', 'exit': '乙支路4街站 4 號口（備案：鐘路5街站 8 號口）', 'mt': '5', 'est': True,
         'q': '서울 종로구 창경궁로 88 광장시장'},
        {'n': 3, 'name': 'APM', 'ko': 'apM Place 동대문', 'exit': '東大門歷史文化公園站 14 號口', 'mt': '3', 'est': True,
         'note': '20:00 進場後回程偏晚', 'q': 'apM Place 동대문'},
    ]).replace('<b>—</b>', '<b>接駁車時間未查</b>').replace('約 — 分（估）', '接駁車時間未查') + \
    unconfirmed('還沒定位的點（地圖上沒畫）', [
        '晚餐「陳玉華奶奶一隻雞」：我查不到確切地址與出口。',
        'NyuNyu 東大門店：地址是 서울 중구 마장로 34（1–3 樓，11:00 營業到隔天 05:00），但附近哪一站最近我沒查到。',
    ]) + \
    notes([
        '回程：東大門歷史文化公園站搭 2 號線<b>外環</b> 8 站回新村；新羅回程是 3 號線往大化到乙支路3街，換 2 號線外環 6 站。',
        'APM 20:00 後結束偏晚，先看地鐵末班，趕不上就叫 Kakao T。',
    ], 'note warn') + '</div>'

# =============================================================== D4
d4_nodes = [
    {'n': '新村', 's': '신촌 · 住宿'},
    {'n': '弘大入口', 's': '홍대입구 · 2 號線', 'hub': True},
]
d4_segs = [{'line': 'l2', 'text': '外環 1 站 約 3 分'}]
d4_svg_strip = strip(d4_nodes, d4_segs, {}, 'D4 新村到弘大入口站')

d4_spots = [
    {'n': 1, 'name': 'AK Plaza（2 樓 with mu）', 'short': 'AK Plaza', 'ko': 'AK&홍대', 'exit': '4 號口外即是', 'mt': '1', 'est': False,
     'q': 'AK&홍대 마포구', 'a': 300},
    {'n': 2, 'name': 'Musinsa Standard 弘大', 'short': 'Musinsa Standard', 'ko': '서울 마포구 양화로 144 B1–2F', 'exit': '9 號口 約 90 公尺', 'hours': '11:00–21:00',
     'mt': '2', 'est': False, 'q': '서울 마포구 양화로 144', 'a': 15},
    {'n': 3, 'name': 'SPAO 弘大店', 'short': 'SPAO', 'ko': '서울 마포구 양화로 153 2층', 'hours': '11:00–22:00',
     'mt': '3', 'est': True, 'note': '和 Musinsa 同一條路', 'q': '서울 마포구 양화로 153', 'a': 70},
    {'n': 4, 'name': 'Daiso 弘大入口店', 'short': 'Daiso', 'ko': '서울 마포구 홍익로 25 서교빌딩 B2', 'hours': '10:00–22:00',
     'mt': '3', 'est': True, 'q': '서울 마포구 홍익로 25', 'a': 120},
    {'n': 5, 'name': 'Wacky Willy 弘大旗艦店', 'short': 'Wacky Willy', 'ko': '서울 마포구 잔다리로 26', 'hours': '12:00–22:00',
     'mt': '9', 'est': True, 'q': '서울 마포구 잔다리로 26', 'a': 245},
    {'n': 6, 'name': 'KT&G 想像庭院 弘大', 'short': 'KT&G 想像庭院', 'ko': '서울 마포구 어울마당로 65', 'hours': '11:00–21:00',
     'mt': '10', 'est': True, 'note': '文具、雜貨', 'q': '서울 마포구 어울마당로 65 상상마당', 'a': 190},
]
d4_svg = radial('弘大入口站', '2 號線 · 機場鐵路', d4_spots, 'D4 弘大入口站周邊店家的步行距離示意圖')

d4 = '<div class="panel-body">' + head('D4', '10/16（五）· 弘大', '弘大',
    '最近的一天，新村搭 1 站就到。主要店家集中在 9 號口外的楊花路與弘益路一帶，AK Plaza 在 4 號口外。') + \
    alight('建議下車站', [
        '<b>弘大入口站（2 號線）9 號口</b>：連到主街 어울마당로 與 양화로，Musinsa Standard 約 90 公尺。',
        '<b>4 號口</b>出去就是 AK Plaza（2 樓 with mu）。',
    ]) + \
    card(d4_svg_strip, '路線圖：新村 → 弘大入口（外環 1 站）') + \
    card(d4_svg, '步行圖：弘大入口站出來後（圈是步行時間；方位為示意）', legend=False) + \
    '<h3 class="h3">地點</h3>' + spot_list(d4_spots) + \
    unconfirmed('還沒定位的點（地圖上沒畫）', [
        'Covernat、8 seconds、Mucent、As"on、時空間：查不到店址。',
        '晚餐「git tteul」：查不到店址。',
    ]) + \
    notes([
        '<b>週五晚上弘大人最多</b>，酒吧、夜店、拉客與搭訕集中在這裡，不理會、不停留。',
        '晚餐後直接回住處，不續攤。弘大到新村只有 1 站，晚上用 Kakao T 就好，白天可搭 2 號線<b>內環</b>。',
        '飲料不離身，不接受陌生人遞的飲品或食物。',
    ], 'note warn') + '</div>'

d5 = ('<div class="panel-body"><header class="dayhead"><span class="day-no off">D5</span><div><h2>返程日</h2>'
      '<p class="section-note">10/17（六）</p></div></header>'
      '<p class="sum">行程還沒訂下，先不畫。固定的是：12:00 公寓退房、23:00 仁川機場 T1 起飛。</p>'
      + notes(['去機場：新村站搭 2 號線<b>外環</b> 1 站到弘大入口，換機場鐵路<b>一般列車</b>往仁川機場2航廈方向，在 T1 下車，約 50 分（估）。',
               '建議 18:00 左右離開市區、19:30 前到機場，留時間退稅與託運。'], 'note') + '</div>')

# =============================================================== overview
ov_map = section('map')
ov_map = re.sub(r'<a href="#r\d">', '<g>', ov_map).replace('</a>', '</g>')
ov_map = ov_map.replace('圓圈裡的數字對應下面的路線卡，點數字可跳過去。', '圓圈裡的數字對應下面的對照表。每天的詳細路線在各天的分頁。')
ov = '<div class="panel-body">' + ov_map + section('guide') + section('table') + '</div>'

# =============================================================== page
extra_css = '''
  .tabs {
    position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5;
    background: var(--bg); border-bottom: 1px solid var(--line);
    margin-inline: -16px; padding: 8px 16px; display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none;
  }
  .tabs::-webkit-scrollbar { display: none; }
  .tabs button {
    flex: none; font: inherit; font-size: 14px; font-weight: 500; color: var(--fg);
    padding: 5px 14px; border: 1px solid var(--line); border-radius: 999px; background: var(--surface); cursor: pointer;
  }
  .tabs button[aria-selected="true"] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
  .tabs button:disabled { color: var(--muted); border-style: dashed; cursor: default; }
  .panel-body { display: flex; flex-direction: column; gap: 14px; padding-top: 22px; }
  .panel-body > section { padding-top: 6px; }
  .dayhead { display: flex; gap: 14px; align-items: center; }
  .dayhead h2 { font-size: 1.5rem; }
  .day-no { flex: none; font-family: var(--font-mono); font-weight: 600; font-size: 18px; background: var(--accent); color: var(--on-accent); border-radius: 8px; padding: 4px 12px; }
  .day-no.off { background: var(--line); color: var(--muted); }
  .sum { color: var(--muted); max-width: 36em; }
  .h3 { font-size: 1.05rem; font-weight: 700; margin-top: 6px; }
  .alight { background: var(--accent-soft); border-radius: 10px; padding: 12px 16px; display: grid; gap: 6px; }
  .alight ul { display: grid; gap: 6px; font-size: 14.5px; }
  .alight li { padding-left: 1em; position: relative; }
  .alight li::before { content: "·"; position: absolute; left: 0; font-weight: 700; }
  .cap { padding: 4px 8px 6px; font-size: 13px; color: var(--muted); }
  .sg { stroke-width: 6; stroke-linecap: round; fill: none; }
  .sg.l2 { stroke: var(--l2); } .sg.l3 { stroke: var(--l3); } .sg.l4 { stroke: var(--l4); } .sg.arex { stroke: var(--larex); }
  .sg.walk { stroke: var(--muted); stroke-width: 3; }
  .sg.dash { stroke-dasharray: 2 7; }
  .st { fill: var(--surface); stroke-width: 3; }
  .st.l2 { stroke: var(--l2); } .st.l3 { stroke: var(--l3); } .st.l4 { stroke: var(--l4); } .st.arex { stroke: var(--larex); } .st.walk { stroke: var(--muted); }
  .dest { fill: var(--fg); }
  .spurdot { fill: var(--fg); }
  .pill { fill: var(--surface); stroke-width: 1.5; }
  .pill.l2 { stroke: var(--l2); } .pill.l3 { stroke: var(--l3); } .pill.l4 { stroke: var(--l4); } .pill.arex { stroke: var(--larex); } .pill.walk { stroke: var(--muted); }
  .ring { fill: none; stroke: var(--line); stroke-width: 1.2; stroke-dasharray: 3 4; }
  .rl { stroke: var(--fg); stroke-width: 2; opacity: 0.75; }
  .rl.dash { stroke-dasharray: 4 5; opacity: 0.6; }
  .mp { fill: var(--surface); stroke: var(--line); stroke-width: 1; }
  .hubc { fill: var(--surface); stroke: var(--l2); stroke-width: 4.5; }
  .halo { paint-order: stroke; stroke: var(--surface); stroke-width: 4px; stroke-linejoin: round; }
  .dashsw { background: repeating-linear-gradient(90deg, var(--muted) 0 4px, transparent 4px 8px); height: 3px; }
  .spots { display: grid; gap: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 4px 14px; }
  .spot { display: grid; grid-template-columns: 28px minmax(0, 1fr) auto; gap: 12px; align-items: start; padding-block: 12px; border-bottom: 1px solid var(--line); }
  .spot:last-child { border-bottom: 0; }
  .spot .sb { display: flex; flex-direction: column; min-width: 0; gap: 1px; }
  .spot .sb b { font-weight: 700; }
  .spot .ko { font-size: 13px; overflow-wrap: anywhere; }
  .spot .sm { font-size: 13px; color: var(--muted); }
  .spot .st2 { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; font-size: 13.5px; text-align: right; }
  .spot .st2 b { font-weight: 700; font-variant-numeric: tabular-nums; }
  .spot .num { margin-top: 2px; }
  .todo { background: var(--warn-bg); border-radius: 10px; padding: 12px 16px; display: grid; gap: 6px; font-size: 14.5px; }
  .todo ul { display: grid; gap: 6px; }
  .todo li { padding-left: 1em; position: relative; }
  .todo li::before { content: "·"; position: absolute; left: 0; font-weight: 700; }
  ul.note { display: grid; gap: 8px; background: transparent; padding: 0; font-size: 14.5px; }
  ul.note li { padding-left: 1em; position: relative; }
  ul.note li::before { content: "·"; position: absolute; left: 0; font-weight: 700; }
  ul.note.warn { background: var(--warn-bg); padding: 12px 16px; border-radius: 10px; }
  .tx.end, .tb.end { text-anchor: end; }
  .tb.mid, .tx.mid, .tm.mid { text-anchor: middle; }
  .mid { text-anchor: middle; }
'''

tabs = [('ov', '總覽'), ('d1', 'D1 · 10/13'), ('d2', 'D2 · 10/14'), ('d3', 'D3 · 10/15'), ('d4', 'D4 · 10/16')]
panels = {'ov': ov, 'd1': d1, 'd2': d2, 'd3': d3, 'd4': d4, 'd5': d5}

h = ['<title>新村出發路線圖</title>',
     '<link rel="preconnect" href="https://fonts.googleapis.com">',
     '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
     '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap">',
     '<style>', base_style, extra_css, '</style>',
     '<div class="wrap">',
     '<header class="hero"><p class="eyebrow">Sinchon · 신촌 · 2 號線</p><h1>新村出發路線圖</h1>'
     '<p class="lede">每天一個分頁：點在哪、要在哪一站下車、站出來要走多久，時間畫在路線上。實線是查到的時間，虛線是我估的。</p></header>',
     '<nav class="tabs" role="tablist" aria-label="日期">']
for k, t in tabs:
    h.append('<button type="button" role="tab" id="t-%s" data-tab="%s" aria-controls="p-%s" aria-selected="false">%s</button>' % (k, k, k, t))
h.append('<button type="button" role="tab" id="t-d5" data-tab="d5" aria-controls="p-d5" aria-selected="false">D5 · 10/17</button>')
h.append('</nav>')
for k in ['ov', 'd1', 'd2', 'd3', 'd4', 'd5']:
    h.append('<div class="panel" role="tabpanel" id="p-%s" aria-labelledby="t-%s"%s>%s</div>' % (k, k, '' if k == 'd1' else ' hidden', panels[k]))

h.append('''<footer>
  <p>資料說明：站名順序、出口、營業時間與地址引自下列來源。標「估」的步行與搭車分鐘數，是我依站數與街區位置推算的，不是官方時間。方位是示意，不是真實地圖，實際走法以 Naver Map 或 Google 地圖為準。</p>
  <ul>
    <li><a href="https://en.wikipedia.org/wiki/Euljiro_1(il)-ga_station" target="_blank" rel="noopener">Euljiro 1-ga station</a></li>
    <li><a href="https://en.wikipedia.org/wiki/Hongik_University_station" target="_blank" rel="noopener">Hongik University station</a></li>
    <li><a href="https://world.nol.com/en/pois/c28e309d-8fa8-46a9-a1b0-0d10c20a7dd9?lang=en" target="_blank" rel="noopener">樂天百貨本店</a></li>
    <li><a href="https://koreatodo.com/shinsegae-department-store" target="_blank" rel="noopener">新世界百貨本店</a></li>
    <li><a href="https://blog.trazy.com/top-must-visit-shops-in-myeongdong/" target="_blank" rel="noopener">Trazy 明洞店家</a></li>
    <li><a href="https://shilladfs.com/comm/kr/en/storeMain?org_cd=01" target="_blank" rel="noopener">新羅免稅店</a></li>
    <li><a href="https://www.ivisitkorea.com/gwangjang-market-in-seoul/" target="_blank" rel="noopener">光藏市場</a></li>
    <li><a href="https://creatrip.com/en/blog/4867/Summary-of-Transportation-to-Dongdaemun" target="_blank" rel="noopener">東大門出口</a></li>
    <li><a href="https://www.ktriptips.com/eng/shopping/4030969" target="_blank" rel="noopener">Matin Kim 旗艦店</a></li>
    <li><a href="https://www.humanmade.jp/en/news/human-made-offline-store-seoul-2024-sep.html" target="_blank" rel="noopener">Human Made</a></li>
    <li><a href="https://creatrip.com/de/blog/11548" target="_blank" rel="noopener">聖水店家地址</a></li>
    <li><a href="https://creatrip.com/en/userblog/4965" target="_blank" rel="noopener">Musinsa Standard 弘大</a></li>
    <li><a href="https://www.ktriptips.com/eng/shopping/4030747" target="_blank" rel="noopener">SPAO 弘大</a></li>
    <li><a href="https://www.treksplorer.com/seoul-arex-airport-express-train/" target="_blank" rel="noopener">機場鐵路</a></li>
    <li>樂天百貨明洞本店官網「機場交通方式」頁（你提供的截圖）</li>
    <li><a href="https://travel-stained.com/incheon-airport-to-myeongdong-transport-guide/" target="_blank" rel="noopener">機場到明洞交通（巴士班次）</a></li>
    <li><a href="https://creatrip.com/en/blog/3196" target="_blank" rel="noopener">機場巴士一覽（6015、6701）</a></li>
  </ul>
</footer>
</div>
<script>
(function () {
  var tabs = [].slice.call(document.querySelectorAll('[role="tab"]'));
  var panels = [].slice.call(document.querySelectorAll('[role="tabpanel"]'));
  function show(id) {
    var found = false;
    tabs.forEach(function (t) { if (t.getAttribute('data-tab') === id) found = true; });
    if (!found) id = 'd1';
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-tab') === id ? 'true' : 'false'); });
    panels.forEach(function (p) { p.hidden = p.id !== 'p-' + id; });
    try { history.replaceState(null, '', '#' + id); } catch (e) {}
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      show(t.getAttribute('data-tab'));
      var bar = document.querySelector('.tabs');
      if (bar) window.scrollTo(0, bar.offsetTop > 0 ? Math.max(0, document.querySelector('.hero').offsetHeight + 8) : 0);
    });
  });
  var start = (location.hash || '').replace('#', '');
  show(start || 'd1');
})();
</script>''')

open(SP + 'seoul-routes.html', 'w', encoding='utf-8').write('\n'.join(h))
print('ok', len('\n'.join(h)))
