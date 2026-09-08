# 演示：原版 MarioStanding.png → 字符画 → 与代码 SMALL_STAND 对比
import os, re
from PIL import Image

BASE = r"D:\a工作空间\像素马里奥"
CHAR = {
    (0x88,0x70,0x00):'H', (0xd8,0x28,0x00):'R', (0xfc,0x98,0x38):'S',
    (0x00,0x00,0x00):'K', (0xfc,0xfc,0xfc):'W', (0x00,0xa8,0x00):'G',
    (0xc8,0x4c,0x0c):'B', (0xfc,0xbc,0xb0):'P', (0xfc,0xd8,0xa8):'F',
}

# 1) 原版 PNG → 字符画（与 _sprite2art.py 完全相同的逻辑）
im = Image.open(os.path.join(BASE, "sprites_raw", "MarioStanding.png")).convert("RGBA")
px = im.load()
converted = []
for y in range(im.height):
    row = ""
    for x in range(im.width):
        r,g,b,a = px[x,y]
        row += '.' if a < 128 else CHAR.get((r,g,b), '?')
    converted.append(row)

# 2) 从 index.html 提取 SMALL_STAND
html = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
m = re.search(r"const SMALL_STAND = \[\n((?:  '[^']*',\n)+)\];", html)
code_rows = re.findall(r"'([^']*)'", m.group(1))

print("=" * 70)
print("原版 MarioStanding.png 尺寸:", im.width, "x", im.height)
print("=" * 70)
print(f"{'原版PNG转出来的字符画':<22} | {'代码里的 SMALL_STAND':<22}")
print("-" * 70)
identical = True
for i, (a, b) in enumerate(zip(converted, code_rows)):
    mark = "✓" if a == b else "✗"
    if a != b: identical = False
    print(f"{a:<22} | {b:<22} {mark}")
print("-" * 70)
print("完全一致:", identical)
print()
print("颜色对照表（原版 RGB → 字符）:")
for (r,g,b),ch in CHAR.items():
    print(f"  #{r:02X}{g:02X}{b:02X}  →  '{ch}'")
print("  透明(alpha<128) → '.'")
