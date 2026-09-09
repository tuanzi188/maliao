# -*- coding: utf-8 -*-
"""v4：dump col 20-25 r9、col 94-103 r9、col 105-119 r9 原始像素"""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
IMG = Image.open(r'D:\a工作空间\ref_1_1_mk.png').convert('RGB')
px = IMG.load()

PAL = {
    'Q': (234, 158, 34),
    'B': (153, 78, 0),
    'H': (255, 204, 197),
    'K': (0, 0, 0),
    'G': (136, 216, 0),
    'E': (13, 147, 0),
}

def near(c, t, tol=40):
    return abs(c[0]-t[0])<=tol and abs(c[1]-t[1])<=tol and abs(c[2]-t[2])<=tol

def dump(cols, rows):
    for cy in rows:
        for cx in cols:
            print(f'-- col {cx} row {cy} --')
            for y in range(cy*16, cy*16+16):
                row = ''
                for x in range(cx*16, cx*16+16):
                    c = px[x, y]
                    ch = '.'
                    for k, t in PAL.items():
                        if near(c, t): ch = k; break
                    row += ch
                print('   ' + row)

dump(range(20, 26), [9])
dump(range(93, 104), [9])
dump(range(104, 120), [9])
