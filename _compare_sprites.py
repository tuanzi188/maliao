# 渲染"原版素材 vs 代码字符画精灵"对比图（用于评估复刻质量）
import re, os
from PIL import Image

BASE = r"D:\a工作空间\像素马里奥"
RAW  = os.path.join(BASE, "sprites_raw")
HTML = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()

# 1) 提取代码中的字符画数组（纯字符串行组成的 const 数组）
pat = re.compile(r"const\s+(\w+)\s*=\s*\[\n((?:\s*'[A-Za-z.]+',\n)+)\s*\];")
sprites = {}
for m in pat.finditer(HTML):
    name, body = m.group(1), m.group(2)
    rows = re.findall(r"'([^']*)'", body)
    sprites[name] = rows

# 2) 代码配色表（与 index.html 中 PAL/PAL_ITEM 等一致）
PAL = { 'R':'#d82800','H':'#887000','S':'#fc9838' }
PAL_GOOMBA = { 'B':'#c84c0c','P':'#fcbcb0','K':'#000000' }
PAL_KOOPA  = { 'G':'#00a800','S':'#fc9838','W':'#fcfcfc' }
PAL_ITEM   = { 'S':'#fc9838','R':'#d82800','W':'#fcfcfc','G':'#00a800','B':'#c84c0c',
               'K':'#000000','P':'#fcbcb0','F':'#fcd8a8','D':'#7c0800','H':'#887000' }
PAL_PLANT  = { 'K':'#202020','R':'#e02020','r':'#a01818','W':'#ffffff',
               'C':'#22ac38','L':'#7ae048','c':'#0e6a24' }
MUSH_PAL   = { 'S':'#fc9838','R':'#d82800','W':'#fcfcfc','G':'#00a800' }

def hex2rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def render_code(rows, pal, scale=2):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new('RGBA', (w*scale, h*scale), (0,0,0,0))
    px = im.load()
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            c = pal.get(ch)
            if c:
                for dy in range(scale):
                    for dx in range(scale):
                        px[x*scale+dx, y*scale+dy] = hex2rgb(c) + (255,)
    return im

def open_raw(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p): return None
    im = Image.open(p)
    im.seek(0)
    return im.convert('RGBA')

def fit(im, max_h):
    if im is None: return None
    if im.height > max_h:
        nh = max_h
        nw = max(1, round(im.width * nh / im.height))
        return im.resize((nw, nh), Image.NEAREST)
    return im

# 3) 对比表：(标题, 代码数组名, 配色, 原版文件名, 说明)
PAIRS = [
    ("小马里奥·站立",   "SMALL_STAND", PAL, "MarioStanding.png", "原版提取"),
    ("小马里奥·跳跃",   "SMALL_JUMP",  PAL, "MarioJumping.png",  "原版提取"),
    ("小马里奥·滑行",   "SMALL_SKID",  PAL, "MarioSkidding.png", "原版提取"),
    ("大马里奥·站立",   "BIG_STAND",   PAL, "SuperMarioStanding.png", "原版提取"),
    ("大马里奥·跳跃",   "BIG_JUMP",    PAL, "SuperMarioJumping.png",  "原版提取"),
    ("大马里奥·蹲伏",   "BIG_CROUCH",  PAL, "SuperMarioCrouching.png","原版提取"),
    ("火力马里奥·站立", "BIG_STAND",   PAL, "FieryMarioStanding.png", "原版提取·换色"),
    ("板栗仔",          "GOOMBA_MAP",  PAL_GOOMBA, "LittleGoomba.gif", "原版提取"),
    ("绿乌龟",          "KOOPA_MAP",   PAL_KOOPA,  "KoopaTroopaGreen.gif", "原版提取"),
    ("龟壳",            "SHELL_MAP",   PAL_KOOPA,  "KoopaTroopaShellGreen.png", "原版提取"),
    ("蘑菇",            "MUSH_MAP",    MUSH_PAL,   "MagicMushroom.png", "原版提取"),
    ("1UP 绿蘑菇",      "MUSH_MAP",    MUSH_PAL,   "1upMushroom.png", "原版提取·换色"),
    ("火之花",          "FLW1",        PAL_ITEM,   "FireFlower.gif", "原版提取"),
    ("无敌星",          "STAR1",       PAL_ITEM,   "Starman.gif", "原版提取"),
    ("金币",            "COIN1",       PAL_ITEM,   "CoinForBlueBG.gif", "原版提取"),
    ("火球",            "FIRE1",       PAL_ITEM,   "FireBall.gif", "原版提取"),
    ("死亡帧",          "DEAD_MAP",    PAL,        None, "手绘（原版无现成素材）"),
    ("食人花",          "PLANT_MAP",   PAL_PLANT,  None, "手绘（SMB3 风格）"),
    ("公主",            "PRINCESS_MAP",PAL,        None, "手绘"),
    ("城堡旗",          "FLAGC_MAP",   PAL,        None, "手绘"),
]

scale = 2
cell_w, cell_h, pad = 150, 150, 12
n = len(PAIRS)
W_img = cell_w*2 + pad*3
H_img = cell_h*n + pad*(n+1)
canvas = Image.new('RGBA', (W_img, H_img), (24,24,40))
from PIL import ImageDraw
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont if False else None
    from PIL import ImageFont
    f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
except Exception:
    f = None

y = pad
for title, arr, pal, raw, note in PAIRS:
    rows = sprites.get(arr)
    if not rows:
        y += cell_h + pad; continue
    code_im = render_code(rows, pal, scale)
    raw_im = open_raw(raw) if raw else None
    c_im = fit(code_im, cell_h-16); r_im = fit(raw_im, cell_h-16)
    # 画到底色块上
    canvas.paste((36,36,56), (pad, y, cell_w+pad, y+cell_h))
    canvas.paste((36,36,56), (cell_w+pad*2, y, cell_w*2+pad*2, y+cell_h))
    if r_im:
        canvas.paste(r_im, (pad + (cell_w-r_im.width)//2, y + (cell_h-r_im.height)//2), r_im)
    if c_im:
        canvas.paste(c_im, (cell_w+pad*2 + (cell_w-c_im.width)//2, y + (cell_h-c_im.height)//2), c_im)
    if f:
        d.text((pad+2, y+2), "原版: " + (raw or "（无素材）"), font=f, fill=(180,200,230))
        d.text((cell_w+pad*2+2, y+2), "代码: " + note, font=f, fill=(180,200,230))
        d.text((pad, y+cell_h-16), title, font=f, fill=(255,210,63))
    y += cell_h + pad

canvas.convert('RGB').save(os.path.join(BASE, "mario_sprite_compare.png"))
print("saved, pairs:", n)
