# 照片 → 像素字符画（改造版 _sprite2art.py）
# 用法: python photo2art.py <照片路径> [宽度=32] [颜色数=16] [背景色阈值=0]
# 示例: python photo2art.py my_photo.jpg 48 16
# 背景抠图: 如果照片是纯色背景(如绿幕/白墙), 传第4个参数为容差(如 30),
#           会把与左上角像素颜色接近的背景变透明('.')
import sys, os
from PIL import Image

def photo_to_art(path, target_w=32, colors=16, bg_tol=0):
    im = Image.open(path).convert("RGBA")
    # 1) 缩放: 按比例缩到目标宽度, 用 NEAREST 保持像素感(或 LANCZOS 更平滑)
    target_h = max(1, round(im.height * target_w / im.width))
    im = im.resize((target_w, target_h), Image.NEAREST)
    # 2) 颜色量化: 把百万色压到 N 色(中位数切分, 比默认均衡更适合照片)
    q = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = q.convert("RGBA")
    px = q.load()
    # 3) 背景抠图: 以左上角像素为背景色, 容差内变透明
    if bg_tol > 0:
        br, bg, bb, ba = px[0, 0]
        for y in range(q.height):
            for x in range(q.width):
                r, g, b, a = px[x, y]
                if abs(r-br) <= bg_tol and abs(g-bg) <= bg_tol and abs(b-bb) <= bg_tol:
                    px[x, y] = (0, 0, 0, 0)
    # 4) 动态颜色→字母映射: 收集实际用到的颜色, 按出现频率分配字母
    from collections import Counter
    cnt = Counter()
    for y in range(q.height):
        for x in range(q.width):
            r, g, b, a = px[x, y]
            if a >= 128:
                cnt[(r, g, b)] += 1
    # 字母表: 大写+小写+数字, 最多 62 色(和现有 CHAR 不冲突也没关系, 独立 PAL)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    pal = {}
    for i, (color, _) in enumerate(cnt.most_common()):
        if i >= len(alphabet): break
        pal[color] = alphabet[i]
    # 生成字符画
    rows = []
    for y in range(q.height):
        row = ""
        for x in range(q.width):
            r, g, b, a = px[x, y]
            row += '.' if a < 128 else pal.get((r, g, b), '?')
        rows.append(row)
    return rows, pal, q.size

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python photo2art.py <照片路径> [宽度=32] [颜色数=16] [背景容差=0]")
        sys.exit(1)
    path = sys.argv[1]
    tw = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    colors = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    bg = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    rows, pal, size = photo_to_art(path, tw, colors, bg)
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"/* {path} -> {size[0]}x{size[1]}, {len(pal)} 色 */")
    print(f"const {name.upper()}_MAP = [")
    for r in rows:
        print(f"  '{r}',")
    print("];")
    print()
    print(f"const {name.upper()}_PAL = {{")
    for (r, g, b), ch in pal.items():
        print(f"  '{ch}': '#{r:02X}{g:02X}{b:02X}',")
    print("};")
