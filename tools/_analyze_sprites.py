# 分析已下载的 SMB 原版精灵：尺寸、调色板、逐行像素
import os, sys
from PIL import Image

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites_raw")

def analyze(name):
    p = os.path.join(DIR, name)
    if not os.path.exists(p):
        print("MISSING", name); return
    im = Image.open(p).convert("RGBA")
    print("=== %s  size=%s" % (name, im.size))
    px = im.load()
    cols = {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 128:
                cols[(r, g, b)] = cols.get((r, g, b), 0) + 1
    for c, n in sorted(cols.items(), key=lambda kv: -kv[1]):
        print("   #%02x%02x%02x x%d" % (c[0], c[1], c[2], n))

for n in ["MarioStanding.png", "MarioJumping.png", "SuperMarioStanding.png",
          "SuperMarioCrouching.png", "FieryMarioStanding.png",
          "LittleGoomba.gif", "KoopaTroopaGreen.gif", "KoopaTroopaShellGreen.png",
          "MagicMushroom.png", "1upMushroom.png", "FireFlower.gif", "Starman.gif",
          "CoinForBlueBG.gif", "BrickBlockBrown.png", "EmptyBlock.png",
          "QuestionBlock.gif", "Mario.gif", "SuperMario.gif", "FireBall.gif"]:
    analyze(n)
