# 定量评估：代码字符画精灵 vs 原版素材的形状/颜色保真度
import re, os
from PIL import Image

BASE = r"D:\a工作空间\像素马里奥"
RAW  = os.path.join(BASE, "sprites_raw")
HTML = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()

pat = re.compile(r"const\s+(\w+)\s*=\s*\[\n((?:\s*'[A-Za-z.]+',\n)+)\s*\];")
sprites = {}
for m in pat.finditer(HTML):
    sprites[m.group(1)] = re.findall(r"'([^']*)'", m.group(2))

PAL = { 'R':'#d82800','H':'#887000','S':'#fc9838' }
PAL_GOOMBA = { 'B':'#c84c0c','P':'#fcbcb0','K':'#000000' }
PAL_KOOPA  = { 'G':'#00a800','S':'#fc9838','W':'#fcfcfc' }
PAL_ITEM   = { 'S':'#fc9838','R':'#d82800','W':'#fcfcfc','G':'#00a800','B':'#c84c0c',
               'K':'#000000','P':'#fcbcb0','F':'#fcd8a8','D':'#7c0800','H':'#887000' }
PAL_PLANT  = { 'K':'#202020','R':'#e02020','r':'#a01818','W':'#ffffff',
               'C':'#22ac38','L':'#7ae048','c':'#0e6a24' }
MUSH_PAL   = { 'S':'#fc9838','R':'#d82800','W':'#fcfcfc','G':'#00a800' }
def h2rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def render1x(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new('RGBA', (w, h), (0,0,0,0)); px = im.load()
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            c = pal.get(ch)
            if c: px[x,y] = h2rgb(c) + (255,)
    return im

def bbox(im):
    a = im.getchannel('A')
    b = a.getbbox()
    return im.crop(b) if b else im

def raw1x(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p): return None
    im = Image.open(p); im.seek(0); im = im.convert('RGBA')
    # 尝试识别缩放倍数：原版宽度应约等于字符画宽 × 整数
    return im

def match(name, arr, pal, rawfile):
    rows = sprites.get(arr)
    if not rows: return None
    code = bbox(render1x(rows, pal))
    raw  = raw1x(rawfile)
    if raw is None: return None
    best = None
    for scale in (1,2,3,4):
        if raw.width % scale: continue
        r1 = raw.resize((raw.width//scale, raw.height//scale), Image.NEAREST)
        r1 = bbox(r1)
        # 对齐：尝试 (0,0) 与中心对齐，取 IoU 最大
        for dx,dy in ((0,0),((r1.width-code.width)//2,(r1.height-code.height)//2)):
            if dx < 0 or dy < 0: continue
            W = max(r1.width, code.width+dx); H = max(r1.height, code.height+dy)
            a = r1.getchannel('A').point(lambda v: 255 if v>0 else 0)
            b = Image.new('L', (W,H), 0); b.paste(code.getchannel('A').point(lambda v: 255 if v>0 else 0), (dx,dy))
            inter = 0; union = 0
            pa, pb = a.load(), b.load()
            for y in range(H):
                for x in range(W):
                    va = pa[x,y] if x<a.width and y<a.height else 0
                    vb = pb[x,y]
                    if va or vb: union += 1
                    if va and vb: inter += 1
            iou = inter/union if union else 0
            if best is None or iou > best[0]: best = (iou, scale, dx, dy)
    return best

PAIRS = [
    ("小马里奥·站立", "SMALL_STAND", PAL, "MarioStanding.png"),
    ("小马里奥·跳跃", "SMALL_JUMP", PAL, "MarioJumping.png"),
    ("小马里奥·滑行", "SMALL_SKID", PAL, "MarioSkidding.png"),
    ("大马里奥·站立", "BIG_STAND", PAL, "SuperMarioStanding.png"),
    ("大马里奥·跳跃", "BIG_JUMP", PAL, "SuperMarioJumping.png"),
    ("大马里奥·蹲伏", "BIG_CROUCH", PAL, "SuperMarioCrouching.png"),
    ("板栗仔", "GOOMBA_MAP", PAL_GOOMBA, "LittleGoomba.gif"),
    ("绿乌龟", "KOOPA_MAP", PAL_KOOPA, "KoopaTroopaGreen.gif"),
    ("龟壳", "SHELL_MAP", PAL_KOOPA, "KoopaTroopaShellGreen.png"),
    ("蘑菇", "MUSH_MAP", MUSH_PAL, "MagicMushroom.png"),
    ("1UP", "MUSH_MAP", MUSH_PAL, "1upMushroom.png"),
    ("火之花", "FLW1", PAL_ITEM, "FireFlower.gif"),
    ("无敌星", "STAR1", PAL_ITEM, "Starman.gif"),
    ("金币", "COIN1", PAL_ITEM, "CoinForBlueBG.gif"),
    ("火球", "FIRE1", PAL_ITEM, "FireBall.gif"),
]

print(f"{'角色':<14}{'形状IoU':>8} {'原版缩放':>7} {'代码宽x高':>10} {'原版1x宽x高':>12}")
for title, arr, pal, raw in PAIRS:
    r = match(title, arr, pal, raw)
    rows = sprites[arr]
    code_bbox = bbox(render1x(rows, pal))
    raw_im = raw1x(raw)
    raw1 = None
    if raw_im is not None:
        for scale in (1,2,3,4):
            if raw_im.width % scale == 0:
                raw1 = bbox(raw_im.resize((raw_im.width//scale, raw_im.height//scale), Image.NEAREST))
                break
    if r:
        iou, scale, dx, dy = r
        rw = raw1.width if raw1 else 0
        print(f"{title:<14}{iou*100:>7.1f}% {scale:>7}x  {code_bbox.width}x{code_bbox.height:>5}  {rw}x{raw1.height if raw1 else 0}")
    else:
        print(f"{title:<14}  N/A")
