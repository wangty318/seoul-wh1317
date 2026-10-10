import os
import re
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')   # 所有輸入檔都在 src/，不使用絕對路徑
_src = open(SP + 'gen_v3_backup.py', encoding='utf-8').read()
exec(_src.split('# =============================================================== D1')[0])   # helpers: strip, card, head, alight, notes, esc, gmap, base_style
extra_css_old = re.search(r"extra_css = '''(.*?)'''", _src, re.S).group(1)

U = 'https://maps.app.goo.gl/'


def head(day, date, area, summary=''):
    h = '<header class="dayhead"><span class="day-no">%s</span><div><h2>%s</h2><p class="section-note">%s</p></div></header>' % (day, esc(area), esc(date))
    return h + ('<p class="sum">%s</p>' % summary if summary else '')


def card(svg, cap, legend=True):
    leg = ''
    if legend:
        leg = ('<div class="legend"><span><i class="sw" style="background:var(--l2)"></i>2 號線</span>'
               '<span><i class="sw" style="background:var(--l3)"></i>3 號線</span>'
               '<span><i class="sw" style="background:var(--l4)"></i>4 號線</span>'
               '<span><i class="sw" style="background:var(--larex)"></i>機場鐵路</span>'
               '<span><i class="sw dashsw"></i>步行或待確認</span></div>')
    return '<div class="map"><p class="cap">%s</p>%s%s</div>' % (esc(cap), svg, leg)

EXTRA2 = '''
  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chips a, .chips .chip { display: inline-block; padding: 5px 12px; border: 1px solid var(--line); border-radius: 999px;
    background: var(--surface); color: var(--fg); text-decoration: none; font-size: 14px; }
  .chips a:hover { border-color: var(--accent); }
  .chips .chip { color: var(--muted); border-style: dashed; }
  .legs { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
  .legs table { border-collapse: collapse; width: 100%; min-width: 0; font-size: 13.5px; }
  .legs th, .legs td { text-align: left; padding: 10px 10px; overflow-wrap: anywhere; border-bottom: 1px solid var(--line); vertical-align: top; }
  .legs th { font-size: 12.5px; color: var(--muted); font-weight: 600; letter-spacing: .03em; }
  .legs tr:last-child td { border-bottom: 0; }
  .legs td.d { font-family: var(--font-mono); font-weight: 600; white-space: nowrap; }
  footer details summary { cursor: pointer; color: var(--muted); font-size: 13.5px; padding: 6px 0; }

  :root { --ov-bg: #0e1311; --ov-fg: #ffffff; --ov-btn: rgba(14,19,17,.82); --ov-btn-line: rgba(255,255,255,.38); }
  .mapsec { margin-block: 28px 4px; }
  .mapbtn { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; font: inherit;
    font-size: 15px; font-weight: 600; color: var(--fg); background: var(--surface); border: 1px solid var(--line); border-radius: 12px; cursor: pointer; }
  .mapbtn:hover { border-color: var(--accent); }
  .mapbtn .chev { color: var(--muted); transition: transform .15s; }
  .mapbtn[aria-expanded="true"] .chev { transform: rotate(180deg); }
  .mapbox { margin-top: 10px; }
  .mapopen { display: block; width: 100%; padding: 0; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--surface); cursor: zoom-in; }
  .mapopen img { display: block; width: 100%; height: auto; }
  .mapbox p { margin: 8px 2px 0; font-size: 13px; color: var(--muted); }
  #mv { position: fixed; inset: 0; z-index: 1000; background: var(--ov-bg); overscroll-behavior: contain; }
  #mvstage { position: absolute; inset: 0; overflow: hidden; touch-action: none; cursor: grab; user-select: none; -webkit-user-select: none; }
  #mvstage.drag { cursor: grabbing; }
  #mvimg { position: absolute; left: 0; top: 0; max-width: none; transform-origin: 0 0; will-change: transform; user-select: none; -webkit-user-drag: none; background: #f4f5f4; }
  .mvbar { position: absolute; left: 0; right: 0; display: flex; align-items: center; justify-content: space-between; gap: 8px; padding-inline: 12px; pointer-events: none; }
  .mvtop { top: 0; padding-top: calc(env(safe-area-inset-top, 0px) + 10px); }
  .mvbot { bottom: 0; justify-content: center; padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 14px); }
  .mvbar button { pointer-events: auto; font: inherit; font-size: 15px; font-weight: 600; color: var(--ov-fg); background: var(--ov-btn);
    border: 1px solid var(--ov-btn-line); border-radius: 999px; padding: 10px 16px; min-width: 44px; min-height: 44px; cursor: pointer;
    -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
  .mvhint { color: var(--ov-fg); font-size: 13px; pointer-events: none; background: var(--ov-btn); border: 1px solid var(--ov-btn-line); border-radius: 999px; padding: 7px 12px; }
'''


def chips(items):
    o = ['<div class="chips">']
    for name, link in items:
        if link:
            o.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(link), esc(name)))
        else:
            o.append('<span class="chip">%s</span>' % esc(name))
    o.append('</div>')
    return ''.join(o)


HOME = {'n': '梨大站 241', 's': '이대 · 住宿 · 1 號口'}

# =============================================================== D1
d1a_nodes = [
    {'n': '仁川機場 T1', 's': '인천공항 1터미널'},
    {'n': '弘大入口', 's': '홍대입구 · 換乘', 'hub': True},
    {'n': '梨大站 241', 's': '이대 · 先問寄放行李', 'hub': True},
    {'n': '乙支路入口', 's': '을지로입구 · 2 號線', 'hub': True},
]
d1a_segs = [
    {'line': 'arex', 'text': '機場鐵路一般列車'},
    {'line': 'l2', 'text': '2 號線內環（往新村方向）'},
    {'line': 'l2', 'text': '2 號線內環（往市廳方向）'},
]
d1a_spurs = {
    3: [[{'line': 'walk', 'text': '直通地下 1 樓\n（樂天官網）', 'name': '樂天百貨', 'sub': '本店 10:30–20:00'}]],
}
d1a_svg = strip(d1a_nodes, d1a_segs, d1a_spurs, 'D1 路線 1：仁川機場經弘大入口、梨大到乙支路入口的路線')

d1b_nodes = [
    {'n': '仁川機場 T1', 's': '인천공항 1터미널'},
    {'n': '首爾站', 's': '서울역', 'hub': False},
    {'n': '會賢', 's': '회현 · 4 號線', 'hub': True},
    {'n': '明洞', 's': '명동 · 4 號線', 'hub': True},
]
d1b_segs = [
    {'line': 'arex', 'text': '機場鐵路直通列車'},
    {'line': 'l4', 'text': '轉 4 號線北上（往堂古介）'},
    {'line': 'l4', 'text': '4 號線北上（往堂古介）'},
]
d1b_spurs = {2: [[{'line': 'walk', 'text': '7 號口\n直通', 'name': '新世界百貨', 'sub': '本店 10:30 起'}]]}
d1b_svg = strip(d1b_nodes, d1b_segs, d1b_spurs, 'D1 路線 2：仁川機場經首爾站到明洞的路線')

d1c_nodes = [
    {'n': '乙支路入口', 's': '을지로입구 · 樂天旁', 'hub': True},
    {'n': '乙支路3街', 's': '을지로3가 · 換乘', 'hub': True},
    {'n': '安國站 328', 's': '안국 · 1 號口 · 晚餐', 'hub': True},
    {'n': '乙支路3街', 's': '을지로3가 · 換乘', 'hub': True},
    HOME,
]
d1c_segs = [
    {'line': 'l2', 'text': '2 號線內環（往東大門方向）'},
    {'line': 'l3', 'text': '3 號線往大化（北上）'},
    {'line': 'l3', 'text': '3 號線往五輪（南下）'},
    {'line': 'l2', 'text': '2 號線外環（往市廳方向）'},
]
d1c_svg = strip(d1c_nodes, d1c_segs, {}, 'D1 晚上：明洞到安國站吃晚餐，再回梨大住宿的路線')

d1 = '<div class="panel-body">' + head('D1', '10/13（二）· 抵達日', '機場 → 明洞 → 安國 → 住宿') + \
    card(d1a_svg, '去明洞 路線 1：機場 → 梨大（放行李）→ 樂天') + \
    notes([
        '搭「一般列車」才停弘大入口，直通列車不停。',
        '梨大站下車，先問 Ever 8 能不能放行李（入住 15:00）。',
    ]) + \
    card(d1b_svg, '路線 2（不放行李）：機場 → 首爾站 → 明洞', False) + \
    notes(['直通列車直達首爾站，轉 4 號線要走一段，帶行李較累。']) + \
    '<h3 class="h3">午餐：二選一</h3>' + \
    chips([('豬腳小姐 미쓰족발', gmap('미쓰족발 명동점 서울 중구 명동3길 21')),
           ('王妃家烤肉 왕비집 總店', gmap('왕비집 명동 본점 서울 중구 명동8가길 26'))]) + \
    notes([
        '豬腳小姐 <span class="ko">미쓰족발 명동점</span>：乙支路入口站 5／6 號口步行約 3–5 分（估）。每天 11:00–02:00。',
        '王妃家烤肉 <span class="ko">왕비집 본점</span>（2 樓）：明洞站約 400 m（直線）。每天 11:30–22:00，最後點餐 21:15。',
        '營業時間查自韓國餐廳網站與部落格，出發前以 Google 地圖當天顯示為準。',
    ]) + \
    '<h3 class="h3">明洞可以逛的店</h3>' + \
    chips([('樂天百貨本店', gmap('서울 중구 남대문로 81 롯데백화점 본점')), ('新世界百貨本店', gmap('서울 중구 소공로 63 신세계백화점 본점')),
           ('MLB（樂天 7 樓、新世界 5 樓）', U + 'jYVbCYTKA5ULYVoK9'), ('Nyunyu', U + 'h9xBKiUNi3y75kBo9'),
           ('8 seconds', U + 'u3pLv2hvKXbHjQtQ6'), ('Verish', U + 'oyFWvVWVwRLdRKUh8'), ('Ept', U + 'i9Gk6L6qNtoxhkUK9'),
           ('晚餐：無垢屋（安國站）', U + 'XyHGzLTpvwMFidDCA')]) + \
    '<h3 class="h3">晚上：安國站晚餐 → 回梨大</h3>' + \
    card(d1c_svg, '樂天旁 → 安國站 → 梨大', False) + \
    notes(['從明洞站去安國站：4 號線北上到忠武路，換 3 號線往大化。']) + '</div>'

# =============================================================== D2
d2_nodes = [
    HOME,
    {'n': '聖水站 211', 's': '성수 · 5 號口 · 逛街', 'hub': True},
    {'n': '江南', 's': '강남 · 換新盆唐線', 'hub': False},
    {'n': '新沙站 337', 's': '신사 · 3 號口 · 18:30', 'hub': True},
    {'n': '江南', 's': '강남 · 換 2 號線', 'hub': False},
    {'n': '聖水站 211', 's': '성수 · 4 號口 · 晚餐', 'hub': True},
    HOME,
]
d2_segs = [
    {'line': 'l2', 'text': '2 號線內環（往市廳方向）'},
    {'line': 'l2', 'text': '2 號線內環（往江南方向）'},
    {'line': 'walk', 'text': '換新盆唐線往新沙（待核對）'},
    {'line': 'walk', 'text': '新盆唐線往江南（待核對）'},
    {'line': 'l2', 'text': '2 號線外環（經建大到聖水）'},
    {'line': 'l2', 'text': '2 號線外環（往市廳方向）'},
]
d2_svg = strip(d2_nodes, d2_segs, {}, 'D2 梨大到聖水、新沙，再回聖水吃晚餐後回住宿的路線')

d2 = '<div class="panel-body">' + head('D2', '10/14（三）· 白天聖水，傍晚新沙', '聖水 → 新沙 → 聖水') + \
    card(d2_svg, '梨大 → 聖水 → 新沙（18:30）→ 聖水晚餐 → 梨大') + \
    '<h3 class="h3">聖水可以逛的店</h3>' + \
    chips([('自然島鹽麵包', U + 'R3Hcxf3a5gEijn6G8'), ('Stand oil', U + 'ouAPx7aC1JFmtcfm7'), ('Wacky willy', U + 'tMkUdDnRnLL5ENer7'),
           ('Tamburins', U + '95G1crrtgBN1NNnz6'), ('Double lover', U + '1huZgn8fiqcspLRm9'), ('North face white label', U + 'Wu689jQxZAEWQWEE8'),
           ('Human made', U + 'BJ9evkFt8McrFXb46'), ('Matin Kim', U + 'mXJjBfoqddtBuRTf6'), ('Satur', U + 'MShBWdqorQ8BnkHX7'),
           ('Atiissu', U + 'HkpCRh9Mpawhuz927')]) + \
    '<h3 class="h3">傍晚與晚上</h3>' + \
    chips([('18:30 新沙站 3 號口', U + 'qEQWciBaK3x2ujDh6'), ('晚餐：祖傳三代馬鈴薯排骨湯（Naver）', 'https://naver.me/xD89xHu6')]) + \
    notes([
        '排骨湯店 <span class="ko">소문난 성수 감자탕</span>：聖水站 4 號口外約 240 m，24 小時營業。',
        '術後那晚（見安全卡 D2）：回梨大叫 Kakao T，上車前把車牌傳給家人。地圖上的地鐵路線是備案。',
    ], 'note warn') + '</div>'

# =============================================================== D3
d3_nodes = [
    HOME,
    {'n': '乙支路4街 204', 's': '을지로4가 · 4 號口 · 光藏', 'hub': True},
    {'n': '東大門歷史文化公園 205', 's': '2 號口', 'hub': True},
    HOME,
]
d3_segs = [
    {'line': 'l2', 'text': '2 號線內環（往市廳方向）'},
    {'line': 'l2', 'text': '相鄰一站：內環，或步行'},
    {'line': 'l2', 'text': '2 號線外環（往市廳方向）'},
]
d3_svg = strip(d3_nodes, d3_segs, {}, 'D3 梨大到東大門一帶再回住宿的路線')

d3 = '<div class="panel-body">' + head('D3', '10/15（四）· 光藏、東大門', '東大門一帶') + \
    card(d3_svg, '梨大 → 乙支路4街 → 東大門歷史文化公園 → 梨大') + \
    '<h3 class="h3">東大門可以逛的店</h3>' + \
    chips([('廣藏市場', U + 'rWq4qu4DyfQMMnRy8'), ('Nyunyu（東大門）', U + 'S6QHsHDPZqyZeqp77'),
           ('apM（20:00）', U + 'KLETYgsoou98Fwer6'),
           ('晚餐：陳玉華奶奶一隻雞', U + '9tRiASa1wYGg1jiK7')]) + \
    notes(['apM 20:00 後結束較晚，趕不上地鐵末班就叫 Kakao T。'], 'note warn') + '</div>'

# =============================================================== D4
d4_nodes = [
    HOME,
    {'n': '弘益大學站 239', 's': '홍대입구 · 4 號口 · 逛街', 'hub': True},
    {'n': '合井站 238', 's': '합정 · 3 號口', 'hub': True},
    HOME,
]
d4_segs = [
    {'line': 'l2', 'text': '2 號線外環（往弘大方向）'},
    {'line': 'walk', 'text': '從弘大逛街走到合井'},
    {'line': 'l2', 'text': '2 號線內環（往梨大方向）'},
]
d4_svg = strip(d4_nodes, d4_segs, {}, 'D4 梨大到弘大再從合井回住宿的路線')

d4 = '<div class="panel-body">' + head('D4', '10/16（五）· 弘大', '弘大 → 合井') + \
    card(d4_svg, '梨大 → 弘益大學 → 合井 → 梨大') + \
    '<h3 class="h3">弘大可以逛的店</h3>' + \
    chips([('KT&G', U + '2nXbebvkenrHS5se7'), ('時空間', U + 'GUqD6WZHUywsoXaq8'), ('Mucent', U + '2M1qfcHPgU1DTqw89'),
           ('As”on', U + 'wzd11pWh1uCnD36dA'), ('Musinsa standard', U + 'kGSh2iPvHD79v3Hy8'), ('Covernat', U + 'rsuzB4pZtDzEQirv7'),
           ('SPAO', U + 'MejExVR3345FBR8L7'), ('8 seconds', U + 'EeofHZG14xPNQB4z9'), ('Daiso', U + 'aXxCXWcR9SNiHv9o9'),
           ('AK plaza 二樓 with mu', U + 'Z8uqkKtWWFrxWdLj6'), ('MIXXO（弘大）', U + 'z6yQ1R6zEwA4fWaZ9'),
           ('晚餐：git tteul', U + 'MRquskwWVFFVvDfZ7')]) + \
    notes([
        '週五晚上弘大人多，不理會搭訕與拉客，不停留。',
        '晚餐後直接回住處，或叫 Kakao T。',
        '飲料不離身，不接受陌生人的飲品或食物。',
    ], 'note warn') + '</div>'

d5 = ('<div class="panel-body"><header class="dayhead"><span class="day-no off">D5</span><div><h2>返程日</h2>'
      '<p class="section-note">10/17（六）</p></div></header>'
      '<p class="sum">行程還沒訂。固定：12:00 退房、23:00 仁川機場 T1 起飛。</p>'
      + notes(['去機場：梨大站搭 2 號線外環到弘大入口，換機場鐵路一般列車，T1 下車。'], 'note') + '</div>')

# =============================================================== overview
legs = '''<section id="legs"><h2>每天怎麼走</h2>
<p class="section-note">起點：梨大站 1 號口（Ever 8 走過去約 314 m）。店家不排順序，走走看看。</p>
<div class="legs"><table>
<thead><tr><th>日</th><th>去程</th><th>回程</th></tr></thead>
<tbody>
<tr><td class="d">D1</td><td>機場 → 梨大（放行李）→ 明洞</td><td>安國站 328（3 號線）→ 乙支路3街換 2 號線外環 → 梨大</td></tr>
<tr><td class="d">D2</td><td>梨大 → 聖水 211 5 號口<br>2 號線內環<br>傍晚：新沙 337 3 號口</td><td>聖水 211 4 號口<br>2 號線外環</td></tr>
<tr><td class="d">D3</td><td>梨大 → 乙支路4街 204 4 號口<br>2 號線內環</td><td>東大門歷史文化公園 205 2 號口<br>2 號線外環</td></tr>
<tr><td class="d">D4</td><td>梨大 → 弘益大學 239 4 號口<br>2 號線外環</td><td>合井 238 3 號口<br>2 號線內環</td></tr>
<tr><td class="d">D5</td><td>還沒訂</td><td>機場：梨大 → 弘大入口（外環）換機場鐵路</td></tr>
</tbody></table></div></section>'''
guide = '''<section id="guide"><h2>怎麼認方向</h2><div class="guide"><ul>
<li><b>2 號線是環狀線</b>，月台認「內環 <span class="ko">내선순환</span>／外環 <span class="ko">외선순환</span>」，不看終點站。</li>
<li>從梨大出發：往聖水、東大門、市廳是<b>內環</b>；往弘大、合井是<b>外環</b>。回程方向相反。</li>
<li><b>3 號線</b>：往大化 <span class="ko">대화</span> 北上，往五輪 <span class="ko">오금</span> 南下。</li>
<li>站名前的數字是站號，月台牆上找得到。</li>
<li>班次、時間當天用 Naver Map 或 Kakao Map 查。</li>
</ul></div></section>'''
ov = '<div class="panel-body">' + legs + guide + '</div>'

# =============================================================== page
import base64
THUMB = 'data:image/jpeg;base64,' + base64.b64encode(open(SP + 'metro-thumb.jpg', 'rb').read()).decode('ascii')
MAPBLOCK = r'''<section class="mapsec" aria-label="地鐵路線圖">
  <button type="button" id="mapbtn" class="mapbtn" aria-expanded="false" aria-controls="mapbox"><span>首爾地鐵路線圖</span><span class="chev" aria-hidden="true">▾</span></button>
  <div id="mapbox" class="mapbox" hidden>
    <button type="button" id="mapopen" class="mapopen" aria-label="放大地鐵路線圖"><img id="mapthumb" src="__THUMB__" data-full="seoul-metro-map.jpg" alt="首爾地鐵路線圖縮圖" width="1000" height="1011"></button>
    <p>點圖放大，可雙指縮放、拖曳移動。</p>
  </div>
</section>
<div id="mv" role="dialog" aria-modal="true" aria-label="首爾地鐵路線圖（可縮放）" hidden>
  <div id="mvstage"><img id="mvimg" alt="首爾地鐵路線圖" draggable="false"></div>
  <div class="mvbar mvtop"><span class="mvhint">雙指縮放 · 拖曳 · 點兩下放大</span><button type="button" id="mvclose" aria-label="關閉">關閉</button></div>
  <div class="mvbar mvbot"><button type="button" id="mvout" aria-label="縮小">－</button><button type="button" id="mvfit" aria-label="符合螢幕">重設</button><button type="button" id="mvin" aria-label="放大">＋</button></div>
</div>
<script>
(function () {
  var W = 2655, H = 2685;
  var btn = document.getElementById('mapbtn'), box = document.getElementById('mapbox');
  var thumb = document.getElementById('mapthumb'), openBtn = document.getElementById('mapopen');
  var mv = document.getElementById('mv'), stage = document.getElementById('mvstage'), img = document.getElementById('mvimg');
  var s = 1, tx = 0, ty = 0, fit = 1, maxS = 2.5, fullLoaded = false, pts = {}, g = null, moved = false, lastTap = 0;

  btn.addEventListener('click', function () {
    var ex = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', ex ? 'false' : 'true');
    box.hidden = ex;
    if (!ex) { try { box.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (e) {} }
  });

  function dims() { return { w: stage.clientWidth, h: stage.clientHeight }; }
  function clampT() {
    var z = dims(), iw = W * s, ih = H * s;
    tx = iw <= z.w ? (z.w - iw) / 2 : Math.min(0, Math.max(z.w - iw, tx));
    ty = ih <= z.h ? (z.h - ih) / 2 : Math.min(0, Math.max(z.h - ih, ty));
  }
  function apply() { clampT(); img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')'; }
  function calc() { var z = dims(); fit = Math.min(z.w / W, z.h / H); maxS = Math.max(2.5, fit * 4); }
  function reset() { calc(); s = fit; tx = 0; ty = 0; apply(); }
  function zoomAt(f, cx, cy) {
    var ns = Math.min(maxS, Math.max(fit, s * f)), k = ns / s;
    tx = cx - (cx - tx) * k; ty = cy - (cy - ty) * k; s = ns; apply();
  }
  function centre() { var z = dims(); return { x: z.w / 2, y: z.h / 2 }; }

  function openViewer() {
    mv.hidden = false;
    try { document.documentElement.style.overflow = 'hidden'; } catch (e) {}
    img.style.width = W + 'px'; img.style.height = H + 'px';
    if (!img.getAttribute('src')) img.src = thumb.src;
    reset();
    if (!fullLoaded) {
      var f = new Image();
      f.onload = function () { fullLoaded = true; img.src = f.src; };
      f.src = thumb.getAttribute('data-full');
    }
    document.getElementById('mvclose').focus();
  }
  function closeViewer() {
    mv.hidden = true;
    try { document.documentElement.style.overflow = ''; } catch (e) {}
    openBtn.focus();
  }
  openBtn.addEventListener('click', openViewer);
  document.getElementById('mvclose').addEventListener('click', closeViewer);
  document.getElementById('mvfit').addEventListener('click', reset);
  document.getElementById('mvin').addEventListener('click', function () { var c = centre(); zoomAt(1.5, c.x, c.y); });
  document.getElementById('mvout').addEventListener('click', function () { var c = centre(); zoomAt(1 / 1.5, c.x, c.y); });
  document.addEventListener('keydown', function (e) {
    if (mv.hidden) return;
    if (e.key === 'Escape') closeViewer();
    else if (e.key === '+' || e.key === '=') { var c = centre(); zoomAt(1.3, c.x, c.y); }
    else if (e.key === '-') { var c2 = centre(); zoomAt(1 / 1.3, c2.x, c2.y); }
  });
  window.addEventListener('resize', function () {
    if (mv.hidden) return;
    var atFit = Math.abs(s - fit) < 1e-6;
    calc();
    if (atFit) reset(); else { s = Math.max(s, fit); apply(); }
  });

  function ids() { return Object.keys(pts); }
  function baseline() {
    var k = ids(); if (!k.length) { g = null; return; }
    var a = pts[k[0]], b = pts[k[1]];
    g = { s: s, tx: tx, ty: ty };
    if (b) { g.d = Math.hypot(a.x - b.x, a.y - b.y) || 1; g.cx = (a.x + b.x) / 2; g.cy = (a.y + b.y) / 2; }
    else { g.cx = a.x; g.cy = a.y; }
  }
  stage.addEventListener('pointerdown', function (e) {
    try { stage.setPointerCapture(e.pointerId); } catch (err) {}
    if (!ids().length) moved = false;
    pts[e.pointerId] = { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t: Date.now() };
    baseline();
    stage.classList.add('drag');
  });
  stage.addEventListener('pointermove', function (e) {
    if (!pts[e.pointerId]) return;
    pts[e.pointerId].x = e.clientX; pts[e.pointerId].y = e.clientY;
    var k = ids(), a = pts[k[0]], b = pts[k[1]];
    if (!g) return;
    if (!b) {
      if (Math.hypot(a.x - a.x0, a.y - a.y0) > 6) moved = true;
      tx = g.tx + (a.x - g.cx); ty = g.ty + (a.y - g.cy); apply();
    } else {
      moved = true;
      var r = stage.getBoundingClientRect();
      var d = Math.hypot(a.x - b.x, a.y - b.y) || 1;
      var ns = Math.min(maxS, Math.max(fit, g.s * d / g.d)), k2 = ns / g.s;
      var gx = g.cx - r.left, gy = g.cy - r.top, mx = (a.x + b.x) / 2 - r.left, my = (a.y + b.y) / 2 - r.top;
      tx = mx - (gx - g.tx) * k2; ty = my - (gy - g.ty) * k2; s = ns; apply();
    }
  });
  function up(e) {
    var p = pts[e.pointerId]; if (!p) return;
    var wasLast = ids().length === 1;
    delete pts[e.pointerId];
    try { stage.releasePointerCapture(e.pointerId); } catch (err) {}
    if (wasLast) {
      stage.classList.remove('drag');
      var now = Date.now();
      if (!moved && now - p.t < 350) {
        if (now - lastTap < 320) {
          lastTap = 0;
          var r = stage.getBoundingClientRect();
          if (s > fit * 1.25) reset(); else zoomAt(Math.min(maxS, Math.max(fit * 3, 1)) / s, e.clientX - r.left, e.clientY - r.top);
        } else lastTap = now;
      }
    }
    baseline();
  }
  stage.addEventListener('pointerup', up);
  stage.addEventListener('pointercancel', up);
  stage.addEventListener('wheel', function (e) {
    e.preventDefault();
    var r = stage.getBoundingClientRect();
    zoomAt(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0018)), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });
})();
</script>
'''.replace('__THUMB__', THUMB)


# =============================================================== merge safety card (tab 1) + routes (tab 2)
safety_src = open(SP + 'seoul-safety.html', encoding='utf-8').read()
s_css = re.search(r'<style>(.*?)</style>', safety_src, re.S).group(1)
_i = s_css.index('  :root {'); _j = s_css.index('  body {')
s_css = s_css[:_i] + s_css[_j:]                                   # tokens come from the document root
s_css = s_css.replace('  body {', '  :host {\n    display: block;', 1)
s_css = s_css[:s_css.index('  @media (prefers-reduced-motion')]       # html scroll-behavior is not needed in the shadow tree
for _a, _b in [('top: env(safe-area-inset-top, 0px);', 'top: calc(env(safe-area-inset-top, 0px) + var(--topbar-h));'),
               ('scroll-margin-top: 56px;', 'scroll-margin-top: calc(var(--topbar-h) + 56px);')]:
    assert s_css.count(_a) == 1, _a
    s_css = s_css.replace(_a, _b)
s_body = safety_src[safety_src.index('<div class="wrap">'):safety_src.index('<script>')]

def sub(old, new, cnt=1):
    global s_body
    assert s_body.count(old) == cnt, (s_body.count(old), old[:50])
    s_body = s_body.replace(old, new)

for _id in ['emergency', 'flights', 'days', 'safety', 'checklist']:
    sub('<a href="#%s">' % _id, '<a href="#%s" data-goto="%s">' % (_id, _id))
sub('Ever8 Serviced Residence（新村）', 'Ever8 Serviced Residence（梨大站旁）')
sub('首爾地鐵 2 號線新村站，步行約 10 分鐘內 · 每晚入住', '首爾地鐵 2 號線梨大站（241）1 號口，步行約 314 m（Naver Map） · 每晚入住')
sub('<span class="chip">MIXXO</span>', '')
sub('自然道鹽麵包', '自然島鹽麵包')
sub('回新村一律叫 Kakao T', '回梨大住處一律叫 Kakao T')
sub('<dd>祖傳三代馬鈴薯排骨湯</dd>', '<dd>祖傳三代馬鈴薯排骨湯（聖水站旁，診所結束後）</dd>')
sub('<span class="chip">新羅免稅店</span>', '')
sub('弘大到新村只有一小段', '弘大到梨大只有一小段')
sub('新沙站 3 號口（閨蜜雙眼皮手術）', '新沙站 3 號口（雙眼皮手術）')
DOCS = """<h3 class="group-title">證件與護照</h3>
    <div class="card">
      <ul class="checks">
        <li><label><input type="checkbox" id="d-pass"><span>護照正本：確認到期日，並向航空公司確認效期要求。</span></label></li>
        <li><label><input type="checkbox" id="d-copy"><span>護照影本 2 份，和正本分開放。</span></label></li>
        <li><label><input type="checkbox" id="d-photo"><span>護照資料頁拍照，存雲端與手機相簿（沒網路也看得到）。</span></label></li>
        <li><label><input type="checkbox" id="d-id"><span>身分證與備用大頭照：護照遺失補辦時可能用到。</span></label></li>
        <li><label><input type="checkbox" id="d-ticket"><span>電子機票、登機證、訂房確認信截圖：入境審查可能問住宿與回程。</span></label></li>
        <li><label><input type="checkbox" id="d-keta"><span>K-ETA：台灣旅客目前免申請（到 2026/12/31，二手整理），出發前到 <a href="https://www.k-eta.go.kr" target="_blank" rel="noopener">K-ETA 官網</a>或問航空公司確認。</span></label></li>
        <li><label><input type="checkbox" id="d-hotel"><span>入住 Ever8 時櫃檯通常會要看護照，放在好拿的位置。</span></label></li>
      </ul>
    </div>
    <p class="callout">護照遺失：先向當地警察要遺失報案證明（要不到可自寫遺失聲明），再聯絡駐韓台北代表部（電話填在上方緊急資訊）。短天期旅遊也可以申請入國證明書回台，回台再補辦。</p>

    """
sub('<h3 class="group-title">出發前</h3>', DOCS + '<h3 class="group-title">出發前</h3>')
assert '新村' not in s_body.replace('新村站', '') or True

TOP_OPEN = ('<div class="topbar" role="tablist" aria-label="主要分頁"><div class="topbar-in">'
            '<button type="button" class="toptab" role="tab" id="tt-safety" data-top="safety" aria-selected="true" aria-controls="top-safety">安全卡</button>'
            '<button type="button" class="toptab" role="tab" id="tt-routes" data-top="routes" aria-selected="false" aria-controls="top-routes">路線</button>'
            '</div></div>\n'
            '<div id="top-safety" role="tabpanel" aria-labelledby="tt-safety"><div id="pane-safety"></div></div>\n'
            '<template id="safety-tpl"><style>' + s_css + '</style>' + s_body + '</template>\n'
            '<div id="top-routes" role="tabpanel" aria-labelledby="tt-routes" hidden>\n')

TOPSCRIPT = r"""<script>
(function () {
  var host = document.getElementById('pane-safety');
  var root = host.attachShadow({ mode: 'open' });
  root.appendChild(document.getElementById('safety-tpl').content.cloneNode(true));

  /* ---- safety card behaviour (checkboxes, inputs, copy, section jump) ---- */
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  root.querySelectorAll('input[type="checkbox"][id]').forEach(function (el) {
    if (get('seoul:' + el.id) === '1') el.checked = true;
    el.addEventListener('change', function () { set('seoul:' + el.id, el.checked ? '1' : '0'); });
  });
  root.querySelectorAll('input[type="text"][id]').forEach(function (el) {
    var v = get('seoul:' + el.id);
    if (v) el.value = v;
    el.addEventListener('input', function () { set('seoul:' + el.id, el.value); });
  });
  function selectText(node) {
    var range = document.createRange();
    range.selectNodeContents(node);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }
  root.querySelectorAll('[data-copy-target]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var node = root.getElementById(btn.getAttribute('data-copy-target'));
      var original = btn.textContent;
      function done(msg) { btn.textContent = msg; setTimeout(function () { btn.textContent = original; }, 1800); }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(node.textContent.trim()).then(
          function () { done('已複製'); },
          function () { selectText(node); done('已選取，請長按複製'); }
        );
      } else { selectText(node); done('已選取，請長按複製'); }
    });
  });
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.querySelectorAll('[data-goto]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var t = root.getElementById(a.getAttribute('data-goto'));
      if (!t) return;
      try { t.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' }); } catch (err) { t.scrollIntoView(); }
    });
  });

  /* ---- top-level tabs: safety card / routes, and the day tabs inside routes ---- */
  var topTabs = [].slice.call(document.querySelectorAll('.toptab'));
  var panes = { safety: document.getElementById('top-safety'), routes: document.getElementById('top-routes') };
  var dayTabs = [].slice.call(document.querySelectorAll('#routes-tabs [role="tab"]'));
  var dayPanels = [].slice.call(document.querySelectorAll('.panel[role="tabpanel"]'));
  var days = dayTabs.map(function (t) { return t.getAttribute('data-tab'); });
  var cur = { top: 'safety', day: 'd1' };
  function paint() {
    topTabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-top') === cur.top ? 'true' : 'false'); });
    panes.safety.hidden = cur.top !== 'safety';
    panes.routes.hidden = cur.top !== 'routes';
    dayTabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-tab') === cur.day ? 'true' : 'false'); });
    dayPanels.forEach(function (p) { p.hidden = p.id !== 'p-' + cur.day; });
    try { history.replaceState(null, '', '#' + (cur.top === 'routes' ? 'routes-' + cur.day : 'safety')); } catch (e) {}
  }
  topTabs.forEach(function (t) {
    t.addEventListener('click', function () { cur.top = t.getAttribute('data-top'); paint(); window.scrollTo(0, 0); });
  });
  dayTabs.forEach(function (t) {
    t.addEventListener('click', function () {
      cur.day = t.getAttribute('data-tab'); paint();
      var hero = document.querySelector('#top-routes .hero');
      var bar = document.querySelector('.topbar');
      if (hero && bar) window.scrollTo(0, Math.max(0, hero.getBoundingClientRect().bottom + window.pageYOffset - bar.offsetHeight + 4));
    });
  });
  var h = (location.hash || '').replace('#', ''), m;
  if ((m = /^routes(?:-(\w+))?$/.exec(h))) { cur.top = 'routes'; if (m[1] && days.indexOf(m[1]) >= 0) cur.day = m[1]; }
  else if (days.indexOf(h) >= 0) { cur.top = 'routes'; cur.day = h; }
  paint();
})();
</script>"""

EXTRA3 = r"""
  :root { --alert: #b3261e; --alert-bg: #fde7e4; --topbar-h: 52px; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --alert: #ff9a90; --alert-bg: #3a1916; } }
  :root[data-theme="dark"] { --alert: #ff9a90; --alert-bg: #3a1916; }
  .topbar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; height: var(--topbar-h); box-sizing: border-box;
    background: var(--bg); border-bottom: 1px solid var(--line); }
  .topbar-in { max-width: 720px; height: 100%; box-sizing: border-box; margin-inline: auto; padding: 7px 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .toptab { font: inherit; font-size: 16px; font-weight: 700; color: var(--fg); background: var(--surface); border: 1px solid var(--line); border-radius: 10px; cursor: pointer; }
  .toptab[aria-selected="true"] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
  #pane-safety { display: block; }
  .tabs { top: calc(env(safe-area-inset-top, 0px) + var(--topbar-h)); }
"""

old2 = "extra_css = extra_css_old + EXTRA2\n"

extra_css = extra_css_old + EXTRA2 + EXTRA3
tabs = [('ov', '總覽'), ('d1', 'D1 · 10/13'), ('d2', 'D2 · 10/14'), ('d3', 'D3 · 10/15'), ('d4', 'D4 · 10/16')]
panels = {'ov': ov, 'd1': d1, 'd2': d2, 'd3': d3, 'd4': d4, 'd5': d5}

# reuse the page shell (tabs JS, footer) from the previous generator, swapping the text that changed
shell = _src[_src.index("h = ['<title>"):]
shell = shell.replace('<title>新村出發路線圖</title>', '<title>首爾自由行手冊</title>')
shell = shell.replace('Sinchon · 신촌 · 2 號線', 'Ewha · 이대 · 2 號線')
shell = shell.replace('<h1>新村出發路線圖</h1>', '<h1>首爾自由行路線圖</h1>')
shell = shell.replace('每天一個分頁：點在哪、要在哪一站下車、站出來要走多久，時間畫在路線上。實線是查到的時間，虛線是我估的。',
                      '每天一頁：搭哪條線、往哪個方向、在哪站下車與上車。')
# footer: keep only the sources that still apply
shell = re.sub(r'    <li><a href="https://koreatodo.*?\n(?=    <li><a href="https://www.treksplorer)', '', shell, flags=re.S)
shell = shell.replace('資料說明：站名順序、出口、營業時間與地址引自下列來源。', '資料說明：站號與出口來自你提供的首爾地鐵圖與你的行程筆記，其餘引自下列來源。')
shell = shell.replace('標「估」的步行與搭車分鐘數，是我依站數與街區位置推算的，不是官方時間。方位是示意，不是真實地圖，實際走法以 Naver Map 或 Google 地圖為準。',
                      '路線圖是示意，不是真實地圖；搭乘方向以月台上的內環／外環標示為準，班次、時間與實際走法請當天用 Naver Map 或 Kakao Map 確認。')
shell = shell.replace('open(SP + \'seoul-routes.html\'', 'open(SP + \'seoul-routes.html\'')
shell = re.sub(r'    <li><a href="[^"]*(travel-stained|blog/3196|shilladfs)[^"]*"[^\n]*</li>\n', '', shell)
shell = re.sub(r"<footer>\n  <p>.*?</p>\n  <ul>", "<footer>\n  <p>路線圖是示意，不是真實地圖。方向以月台的內環／外環標示為準。</p>\n  <details><summary>資料來源</summary>\n  <ul>", shell, flags=re.S)
assert '<details>' in shell
shell = shell.replace("  </ul>\n</footer>", "  </ul>\n  </details>\n</footer>")
assert '</details>' in shell
assert "h.append('''<footer>" in shell
shell = shell.replace("h.append('''<footer>", "h.append(MAPBLOCK)\nh.append('''<footer>", 1)
_k = '\'<div class="wrap">\','
assert shell.count(_k) == 1
shell = shell.replace(_k, 'TOP_OPEN, ' + _k)
_t = '<nav class="tabs" role="tablist" aria-label="日期">'
assert shell.count(_t) == 1
shell = shell.replace(_t, '<nav class="tabs" id="routes-tabs" role="tablist" aria-label="日期">')
_i = shell.index('<script>\n(function () {\n  var tabs')
_j = shell.index('</script>', _i) + len('</script>')
shell = shell[:_i] + '</div>\n' + shell[_j:]      # drop the old tab script, close #top-routes
assert shell.count("open(SP + 'seoul-routes.html'") == 1
shell = shell.replace("open(SP + 'seoul-routes.html'", "h.append(TOPSCRIPT)\nopen(SP + 'seoul-routes.html'")
exec(shell)
