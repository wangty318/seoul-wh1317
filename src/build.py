"""一個指令重建整個網站：  python3 src/build.py [--out DIR] [--stamp "MM/DD HH:MM"]
1) gen_site.py  把行程內容產生成 src/seoul-routes.html
2) make_pwa.py  包成 PWA，輸出到 repo 根目錄（或 --out）
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(HERE, 'gen_site.py')], check=True, cwd=HERE)
subprocess.run([sys.executable, os.path.join(HERE, 'make_pwa.py')] + sys.argv[1:], check=True, cwd=HERE)
