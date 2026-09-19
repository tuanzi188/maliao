# -*- coding: utf-8 -*-
# 并行安全小步替换：只动角色/敌人/道具精灵区（对方会话管环境区，不碰）
import io, re, sys

F = 'index.html'
src = io.open(F, encoding='utf-8').read()
gen = io.open('_assets_gen.js', encoding='utf-8').read()

def block(name):
    m = re.search(r"const %s = \[(.*?)\];" % name, gen, re.S)
    return "const %s = [%s];" % (name, m.group(1))

def splice(old_start, old_end, new_text, label):
    """把 [old_start, old_end] 闭区间锚点之间的内容替换为 new_text（含两端锚点行）。"""
    global src
    i = src.find(old_start)
    j = src.find(old_end, i)
    assert i >= 0 and j >= 0, 'anchor missing: %s' % label
    j += len(old_end)
    src = src[:i] + new_text + src[j:]
    print('spliced:', label, '(old %d chars -> new %d chars)' % (j - i, len(new_text)))

# ============ 第 1 步：马里奥区（PAL..SPB_STAR 整段） ============
mario_maps = '\n'.join(block(n) for n in [
    'SMALL_STAND', 'SMALL_WALK1', 'SMALL_WALK2', 'SMALL_WALK3',
    'SMALL_JUMP', 'SMALL_SKID',
    'BIG_STAND', 'BIG_WALK1', 'BIG_WALK2', 'BIG_WALK3',
    'BIG_JUMP', 'BIG_SKID', 'BIG_CROUCH',
])

MARIO_NEW = '''/* ---- 角色：原版 NES 精灵字符画（sprites_raw 提取，2px 缩放） ----
 * 原版三色：R=#d82800 红(帽/背带裤) H=#887000 棕(发/衫/鞋) S=#fc9838 肤；
 * 火力形态=原版换色（原棕槽→红、原红槽→奶白），无敌星=红绿槽循环闪 */
const PAL = { R: '#d82800', H: '#887000', S: '#fc9838' };
const PAL_FIRE = { R: '#fcd8a8', H: '#d82800', S: '#fc9838' };
const PAL_SG = { R: '#00a800', H: '#d82800', S: '#fc9838' };
const PAL_SR = { R: '#d82800', H: '#00a800', S: '#fc9838' };
''' + mario_maps + '''
/* 死亡帧（原版无此素材文件，按原版造型手绘：正面举手张嘴） */
const DEAD_MAP = [
  '..S.RRRR.S..',
  '.SSRRRRRRSS.',
  '..SSHSSHSS..',
  '..SSSSSSSS..',
  '..SSSKKSSS..',
  '..SSSKKSSS..',
  '...SSSSSS...',
  '.SHHOOOOHHS.',
  '.HHHOOOOHHH.',
  '..OOOOOOOO..',
  '..OOO..OOO..',
  '..OOO..OOO..',
  '..OOO..OOO..',
  '..HHH..HHH..',
  '.HHHH..HHHH.',
  '............',
];
function mkSmall(p) {
  return {
    idle: makeSprite(SMALL_STAND, p),
    run:  [makeSprite(SMALL_WALK1, p), makeSprite(SMALL_WALK2, p), makeSprite(SMALL_WALK3, p)],
    jump: makeSprite(SMALL_JUMP, p),
    skid: makeSprite(SMALL_SKID, p),
    dead: makeSprite(DEAD_MAP, p),
  };
}
function mkBig(p) {
  return {
    idle: makeSprite(BIG_STAND, p),
    run:  [makeSprite(BIG_WALK1, p), makeSprite(BIG_WALK2, p), makeSprite(BIG_WALK3, p)],
    jump: makeSprite(BIG_JUMP, p),
    skid: makeSprite(BIG_SKID, p),
    crouch: makeSprite(BIG_CROUCH, p),
  };
}
const SP  = mkSmall(PAL);
const SPB = mkBig(PAL);
const SPF = mkBig(PAL_FIRE);
/* 无敌星：原版红绿槽三循环闪（普通/火力形态同构换色） */
const SP_STAR  = [mkSmall(PAL), mkSmall(PAL_SG), mkSmall(PAL_SR)];
const SPB_STAR = [mkBig(PAL),   mkBig(PAL_SG),   mkBig(PAL_SR)];
const SPF_STAR = [mkBig(PAL_FIRE), mkBig(PAL_SG), mkBig(PAL_SR)];'''

splice("/* ---- 角色：字符画像素图（12 列 × 2px 缩放），小/大/火力三套 ---- */",
       "  crouch: makeSprite(CROUCH_B, PAL_STAR),\n};",
       MARIO_NEW, 'mario section')

io.open(F, 'w', encoding='utf-8', newline='\n').write(src)
print('OK step1')
