# 将原版 SMB 精灵 PNG/GIF 转为字符画数组（JS 可直接粘贴）
# 用法: python _sprite2art.py
import os
from PIL import Image

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites_raw")

# 全局调色板：颜色 -> 字符
CHAR = {
    (0x88, 0x70, 0x00): 'H',   # 棕色（头发/鞋）
    (0xd8, 0x28, 0x00): 'R',   # 红
    (0xfc, 0x98, 0x38): 'S',   # 肤色/橙
    (0x00, 0x00, 0x00): 'K',   # 黑
    (0xfc, 0xfc, 0xfc): 'W',   # 白
    (0x00, 0xa8, 0x00): 'G',   # 绿
    (0xc8, 0x4c, 0x0c): 'B',   # 砖棕
    (0xfc, 0xbc, 0xb0): 'P',   # 浅粉
    (0xfc, 0xd8, 0xa8): 'F',   # 浅肤（火力白）
    (0xff, 0x7a, 0x1e): 'O',
}

def to_art(name, transparent_is=None):
    im = Image.open(os.path.join(DIR, name)).convert("RGBA")
    px = im.load()
    print("/* %s %dx%d */" % (name, im.width, im.height))
    for y in range(im.height):
        row = ""
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                row += '.'
            else:
                row += CHAR.get((r, g, b), '?')
        print("  '%s'," % row)
    print()

for n in ["MarioStanding.png", "MarioJumping.png", "MarioSkidding.png",
          "SuperMarioStanding.png", "SuperMarioJumping.png", "SuperMarioCrouching.png",
          "SuperMarioSkidding.png", "FieryMarioStanding.png",
          "LittleGoomba.gif", "KoopaTroopaGreen.gif", "KoopaTroopaShellGreen.png",
          "MagicMushroom.png", "FireFlower.gif", "Starman.gif",
          "CoinForBlueBG.gif", "BrickBlockBrown.png", "EmptyBlock.png",
          "QuestionBlock.gif", "FireBall.gif"]:
    to_art(n)
