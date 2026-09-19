# -*- coding: utf-8 -*-
# 第 2 步：敌人/道具精灵区替换（原版字符画）；金币程序帧改原版帧
import io, re

F = 'index.html'
src = io.open(F, encoding='utf-8').read()
gen = io.open('_assets_gen.js', encoding='utf-8').read()

def block(name):
    m = re.search(r"const %s = \[(.*?)\];" % name, gen, re.S)
    return "const %s = [%s];" % (name, m.group(1))

def splice(old_start, old_end, new_text, label):
    global src
    i = src.find(old_start)
    j = src.find(old_end, i)
    assert i >= 0 and j >= 0, 'anchor missing: %s' % label
    j += len(old_end)
    src = src[:i] + new_text + src[j:]
    print('spliced:', label)

ENEMY_NAMES = ['GOOMBA_MAP', 'KOOPA_MAP', 'KOOPA_RUN2', 'SHELL_MAP', 'MUSH_MAP',
               'FLW1', 'FLW2', 'FLW3', 'FLW4', 'STAR1', 'STAR2', 'STAR3', 'STAR4',
               'COIN1', 'COIN2', 'COIN3', 'FIRE1', 'FIRE2', 'FIRE3', 'FIRE4']
enemy_maps = '\n'.join(block(n) for n in ENEMY_NAMES)

ENEMY_NEW = '''/* ---- 敌人 / 道具精灵：原版 NES 字符画（sprites_raw 提取） ----
 * 栗子怪 B=#c84c0c 身 P=#fcbcb0 脸 K 黑；乌龟 G=#00a800 壳 S=#fc9838 身 W 白；
 * 金币/问号砖/星星/火花为原版多帧调色循环 */
const PAL_GOOMBA = { B: '#c84c0c', P: '#fcbcb0', K: '#000000' };
const PAL_KOOPA  = { G: '#00a800', S: '#fc9838', W: '#fcfcfc' };
const PAL_ITEM   = { S: '#fc9838', R: '#d82800', W: '#fcfcfc', G: '#00a800', B: '#c84c0c',
                     K: '#000000', P: '#fcbcb0', F: '#fcd8a8', D: '#7c0800', H: '#887000' };
''' + enemy_maps + '''
const EG_SPR   = makeSprite(GOOMBA_MAP, PAL_GOOMBA);
const EK_SPR   = makeSprite(KOOPA_MAP, PAL_KOOPA);
const KOOPA_RUN = [EK_SPR, makeSprite(KOOPA_RUN2, PAL_KOOPA)];
const ES_SPR   = makeSprite(SHELL_MAP, PAL_KOOPA);
const MUSH_SPR = makeSprite(MUSH_MAP, { R: '#d82800', S: '#fc9838', W: '#fcfcfc' });
const ONEUP_SPR = makeSprite(MUSH_MAP, { R: '#00a800', S: '#fc9838', W: '#fcfcfc' });   // 1UP：绿蘑菇
const FLW_SPRS = [makeSprite(FLW1, PAL_ITEM), makeSprite(FLW2, PAL_ITEM), makeSprite(FLW3, PAL_ITEM), makeSprite(FLW4, PAL_ITEM)];
const STAR_SPRS = [makeSprite(STAR1, PAL_ITEM), makeSprite(STAR2, PAL_ITEM), makeSprite(STAR3, PAL_ITEM), makeSprite(STAR4, PAL_ITEM)];
const COIN_SPRS = [makeSprite(COIN1, PAL_ITEM), makeSprite(COIN2, PAL_ITEM), makeSprite(COIN3, PAL_ITEM)];
const FIRE_SPRS = [makeSprite(FIRE1, PAL_ITEM), makeSprite(FIRE2, PAL_ITEM), makeSprite(FIRE3, PAL_ITEM), makeSprite(FIRE4, PAL_ITEM)];
const coinFrames = COIN_SPRS;                              // 兼容旧引用（瓦片金币/金币弹出动效）
const CAP_SPR = makeSprite(['..RRRR..', '.RRRRRR.', 'HHHHHHHH'], PAL);   // 受击飞走的帽子
const PAL_PLANT = { K: '#202020', R: '#e02020', r: '#a01818', W: '#ffffff',
                    C: '#22ac38', L: '#7ae048', c: '#0e6a24' };            // 食人花配色保持不变
const PLANT_SPR  = makeSprite(PLANT_MAP, PAL_PLANT);       // 食人花（红苞白点·黑描边）'''

# A：敌人区整段（从区注释到旧实例化 PLANT_SPR 行）；PLANT_MAP 原样保留搬入新块
pm = re.search(r"/\* 食人花（16×32 = 32×64）.*?const PLANT_MAP = \[(.*?)\];", src, re.S)
assert pm, 'PLANT_MAP not found'
plant_block = pm.group(0)
ENEMY_NEW = ENEMY_NEW.replace("const PAL_PLANT = {",
                              plant_block + "\nconst PAL_PLANT = {")
splice("/* ---- 敌人 / 道具精灵 ---- */",
       "const PLANT_SPR  = makeSprite(PLANT_MAP, PAL_PLANT);       // 食人花（红苞白点·黑描边）",
       ENEMY_NEW, 'enemy section')

# B：删旧程序金币帧（drawEllipse 保留给潜在引用，先查）
if 'drawEllipse(' not in src.replace('function drawEllipse', '', 1):
    i = src.find('/* ---- 金币：4 帧旋转')
    j = src.find('const coinFrames = [makeCoinFrame(12), makeCoinFrame(8), makeCoinFrame(3), makeCoinFrame(8)];')
    if i >= 0 and j >= 0:
        j += len('const coinFrames = [makeCoinFrame(12), makeCoinFrame(8), makeCoinFrame(3), makeCoinFrame(8)];')
        src = src[:i] + src[j:]
        print('removed old coin frame block')

io.open(F, 'w', encoding='utf-8', newline='\n').write(src)
print('OK step2')
