# -*- coding: utf-8 -*-
# 生成原版 SMB 精灵/图块字符画 -> _assets_gen.js
# 来源：sprites_raw（原版精灵站素材）+ D:/a工作空间/ref_1_1_mk.png（原版全景截图）
import os, hashlib
from PIL import Image, ImageSequence

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites_raw")
PANO = "D:/a工作空间/ref_1_1_mk.png"

# NES 色 -> 字符（精灵用）
CHAR = {
    (0x88, 0x70, 0x00): 'H',   # 棕（马里奥头发/衫/鞋）
    (0xd8, 0x28, 0x00): 'R',   # 红（帽/背带裤）
    (0xfc, 0x98, 0x38): 'S',   # 肤/橙
    (0x00, 0x00, 0x00): 'K',   # 黑
    (0xfc, 0xfc, 0xfc): 'W',   # 白
    (0xff, 0xff, 0xff): 'W',
    (0x00, 0xa8, 0x00): 'G',   # 绿（乌龟/1UP）
    (0xc8, 0x4c, 0x0c): 'B',   # 砖棕（栗子怪身/砖）
    (0xfc, 0xbc, 0xb0): 'P',   # 浅粉（栗子怪脸/砖高光）
    (0xfc, 0xd8, 0xa8): 'F',   # 火力白
    (0x7c, 0x08, 0x00): 'D',   # 暗红
    (0x64, 0xb0, 0xff): 'L',   # 云影蓝
    (0x80, 0xd0, 0x10): 'E',   # 亮绿（云/灌木同形）
}

def frames_of(name):
    im = Image.open(os.path.join(DIR, name))
    out, seen = [], set()
    for fr in ImageSequence.Iterator(im):
        fr = fr.convert('RGBA')
        rows = []
        px = fr.load()
        for y in range(fr.height):
            rows.append(''.join('.' if px[x, y][3] < 128 else CHAR.get(px[x, y][:3], '?')
                                for x in range(fr.width)))
        hsh = hashlib.md5('\n'.join(rows).encode()).hexdigest()
        if hsh not in seen:
            seen.add(hsh); out.append(rows)
    return out

# 全景图提取（16px 图块 -> 字符）
PANO_PAL = {
    (0x99, 0x4e, 0x00): 'A',   # 砖底棕
    (0xff, 0xcc, 0xc5): 'B',   # 高光粉
    (0x00, 0x00, 0x00): 'C',   # 黑
    (0x88, 0xd8, 0x00): 'D',   # 管/灌木亮绿
    (0x0d, 0x93, 0x00): 'E',   # 管/灌木暗绿
    (0xff, 0xff, 0xff): 'W',   # 云白
    (0x64, 0xb0, 0xff): 'L',   # 云影
    (0x92, 0x90, 0xff): '.',   # 天空(透明)
}
def pano(x0, y0, w, h):
    im = Image.open(PANO).convert('RGB')
    rows = []
    for y in range(y0, y0 + h):
        rows.append(''.join(PANO_PAL.get(im.getpixel((x, y)), '?') for x in range(x0, x0 + w)))
    return rows

out = []
def emit(name, rows):
    out.append("const %s = [" % name)
    for r in rows:
        out.append("  '%s'," % r)
    out.append("];")

# ---- 马里奥（小） ----
emit('SMALL_STAND', frames_of('MarioStanding.png')[0])
walk = frames_of('Mario.gif')           # 3 帧走路
for i, f in enumerate(walk): emit('SMALL_WALK%d' % (i + 1), f)
emit('SMALL_JUMP', frames_of('MarioJumping.png')[0])
emit('SMALL_SKID', frames_of('MarioSkidding.png')[0])
# ---- 马里奥（大） ----
emit('BIG_STAND', frames_of('SuperMarioStanding.png')[0])
bwalk = frames_of('SuperMario.gif')
for i, f in enumerate(bwalk): emit('BIG_WALK%d' % (i + 1), f)
emit('BIG_JUMP', frames_of('SuperMarioJumping.png')[0])
emit('BIG_SKID', frames_of('SuperMarioSkidding.png')[0])
emit('BIG_CROUCH', frames_of('SuperMarioCrouching.png')[0])
# ---- 敌人/道具 ----
emit('GOOMBA_MAP', frames_of('LittleGoomba.gif')[0])
kp = frames_of('KoopaTroopaGreen.gif')
emit('KOOPA_MAP', kp[0]); emit('KOOPA_RUN2', kp[1])
emit('SHELL_MAP', frames_of('KoopaTroopaShellGreen.png')[0])
emit('MUSH_MAP', frames_of('MagicMushroom.png')[0])
for i, f in enumerate(frames_of('FireFlower.gif')): emit('FLW%d' % (i + 1), f)
for i, f in enumerate(frames_of('Starman.gif')): emit('STAR%d' % (i + 1), f)
coin = frames_of('CoinForBlueBG.gif')
for i, f in enumerate(coin): emit('COIN%d' % (i + 1), f)
qb = frames_of('QuestionBlock.gif')
for i, f in enumerate(qb): emit('QB%d' % (i + 1), f)
emit('BRICK_MAP', frames_of('BrickBlockBrown.png')[0])
emit('USED_MAP', frames_of('EmptyBlock.png')[0])
fb = frames_of('FireBall.gif')
for i, f in enumerate(fb): emit('FIRE%d' % (i + 1), f)
emit('FLAG_MAP', frames_of('FlagFromPole.png')[0])
# ---- 全景图：地砖/硬块/水管/云/灌木/山丘/城堡 ----
emit('TILE_GROUND', pano(0, 208, 16, 16))
emit('TILE_HARD', pano(2928, 160, 16, 16))
emit('PIPE_CAP_L', pano(448, 176, 16, 16))
emit('PIPE_CAP_R', pano(464, 176, 16, 16))
emit('PIPE_BODY_L', pano(448, 192, 16, 16))
emit('PIPE_BODY_R', pano(464, 192, 16, 16))
emit('CLOUD_MAP', pano(448, 48, 48, 24))
emit('BUSH_MAP', pano(192, 192, 48, 16))
h = pano(0, 160, 80, 48)   # 山丘（自动修掉天空列）
emit('HILL_MAP', h)
emit('CASTLE_MAP', pano(3232, 128, 80, 80))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_assets_gen.js'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('frames: small_walk=%d big_walk=%d koopa=%d flower=%d star=%d coin=%d qblock=%d fire=%d'
      % (len(walk), len(bwalk), len(kp), len(frames_of('FireFlower.gif')), len(frames_of('Starman.gif')),
         len(coin), len(qb), len(fb)))
print('OK -> _assets_gen.js, %d lines' % len(out))
