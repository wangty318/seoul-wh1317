"""產生 PWA 圖示到 src/icons/（只有要改圖示設計時才需要重跑；需要 Pillow 與 Noto Sans CJK TC 字型）。"""
import math, os, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'icons')
os.makedirs(OUT, exist_ok=True)


def make_icon():
    S = 1024
    im = Image.new('RGB', (S, S), (0, 112, 58))            # 全版面不透明，iOS 自己切圓角
    d = ImageDraw.Draw(im)
    cx = cy = S // 2
    R, W = 330, 46                                          # 環狀線（2 號線是環線）
    d.ellipse([cx - R - W // 2, cy - R - W // 2, cx + R + W // 2, cy + R + W // 2], outline=(255, 255, 255), width=W)
    for i in range(6):                                      # 6 個站點圓點
        a = math.radians(-90 + i * 60)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        r = 42
        d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 112, 58), outline=(255, 255, 255), width=14)
    f = subprocess.run(['fc-match', '-f', '%{file}|%{index}', 'Noto Sans CJK TC:bold'], capture_output=True, text=True).stdout
    path, idx = f.split('|')
    font = ImageFont.truetype(path, 275, index=int(idx))
    d.text((cx, cy), '首爾', font=font, fill=(255, 255, 255), anchor='mm')
    return im


big = make_icon()
for name, px in [('apple-touch-icon.png', 180), ('icon-192.png', 192), ('icon-512.png', 512), ('icon-512-maskable.png', 512)]:
    big.resize((px, px), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
print('icons written to', OUT)
