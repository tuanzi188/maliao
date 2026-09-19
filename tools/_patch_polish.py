# -*- coding: utf-8 -*-
# 四项体验改进：星星预警 / 城堡升旗+通关画面 / 大形态防穿模 / 打击顿帧
import io
from PIL import Image

def art(name):
    im = Image.open('sprites_raw/' + name).convert('RGBA')
    px = im.load()
    M = {(0xfc, 0xfc, 0xfc): 'W', (0xd8, 0x28, 0x00): 'R', (0xfc, 0x98, 0x38): 'S'}
    rows = []
    for y in range(im.height):
        rows.append(''.join('.' if px[x, y][3] < 128 else M.get(px[x, y][:3], '?') for x in range(im.width)))
    assert all('?' not in r for r in rows)
    return rows

PRINCESS_ROWS = art('Princess.png')
FLAGC_ROWS = art('FlagOnCastle.png')

src = io.open('index.html').read()
princess_js = "const PRINCESS_MAP = [\n" + ''.join("  '%s',\n" % r for r in PRINCESS_ROWS) + "];"
flagc_js = "const FLAGC_MAP = [\n" + ''.join("  '%s',\n" % r for r in FLAGC_ROWS) + "];"

edits = []
edits.append(("const CAP_SPR = makeSprite(['..RRRR..', '.RRRRRR.', 'HHHHHHHH'], PAL);   // 受击飞走的帽子",
              "const CAP_SPR = makeSprite(['..RRRR..', '.RRRRRR.', 'HHHHHHHH'], PAL);   // 受击飞走的帽子\n"
              + princess_js + "\n"
              + flagc_js + "\n"
              "const PRINCESS_SPR = makeSprite(PRINCESS_MAP, PAL);   // 通关画面：公主（原版三色系）\n"
              "const FLAGC_SPR   = makeSprite(FLAGC_MAP, PAL);       // 城堡升旗"))
edits.append(("let deathByPit = false;                // 本次死亡是否摔坑（摔坑直接 Game Over）",
              "let deathByPit = false;                // 本次死亡是否摔坑（摔坑直接 Game Over）\n"
              "let castleFlagT = -1;                  // 城堡升旗进度（<0 未激活；进城堡后升起）\n"
              "let hitStopT = 0;                      // 打击顿帧（踩敌/碎砖瞬间微冻结，增强打击感）"))
edits.append(("  comboStreak = 0; seqT = 0; fwLeft = 0; fwTotal = 0; morphT = 0; hurry = false; deathByPit = false;",
              "  comboStreak = 0; seqT = 0; fwLeft = 0; fwTotal = 0; morphT = 0; hurry = false; deathByPit = false;\n"
              "  castleFlagT = -1;"))
edits.append(("    p.vx = 0;\n    gameState = 'flagup'; seqT = 0; fwT = 0;",
              "    p.vx = 0;\n    gameState = 'flagup'; seqT = 0; fwT = 0; castleFlagT = 0;   // 城堡升旗开始"))
edits.append(("function updateFlagUp(dt) {\n  seqT += dt;",
              "function updateFlagUp(dt) {\n  seqT += dt;\n  castleFlagT += dt;"))
edits.append(("  drawCastle();                                   // 城堡盖在角色上：走进门洞即“没入”",
              "  drawCastleFlag();                               // 城堡升旗（画在城堡前：塔身遮挡未升出部分）\n"
              "  drawCastle();                                   // 城堡盖在角色上：走进门洞即“没入”"))
edits.append(("""  let set;                                               // 无敌星：红绿槽三循环（原版换色闪）
  if (p.starT > 0) {
    const cyc = p.mode === 'small' ? SP_STAR : p.mode === 'fire' ? SPF_STAR : SPB_STAR;
    set = cyc[Math.floor(p.starT * 10) % 3];
  } else set = p.mode === 'small' ? SP : p.mode === 'fire' ? SPF : SPB;""",
              """  let set;                                               // 无敌星：红绿槽三循环（原版换色闪）
  if (p.starT > 0) {
    const cyc = p.mode === 'small' ? SP_STAR : p.mode === 'fire' ? SPF_STAR : SPB_STAR;
    set = cyc[Math.floor(p.starT * 10) % 3];
    if (p.starT < 3 && Math.floor(p.starT * 8) % 2 === 0)             // 结束前3秒：普通/星色急促交替 = 到时预警
      set = p.mode === 'small' ? SP : p.mode === 'fire' ? SPF : SPB;
  } else set = p.mode === 'small' ? SP : p.mode === 'fire' ? SPF : SPB;"""))
edits.append(("""  const dx = Math.round((p.w - spr.width) / 2), dy = p.h - spr.height;   // 底部对齐+水平居中（镜像安全）
  ctx.translate(Math.round(p.x - camX) + (p.facing < 0 ? p.w : 0), Math.round(p.y));
  if (p.facing < 0) ctx.scale(-1, 1);
  if (gameState === 'pipeIn') ctx.globalAlpha = Math.max(0, 1 - seqT / 0.65);   // 入管渐隐
  ctx.drawImage(spr, dx, dy);
  ctx.globalAlpha = 1;
  ctx.restore();""",
              """  const dx = Math.round((p.w - spr.width) / 2), dy = p.h - spr.height;   // 底部对齐+水平居中（镜像安全）
  /* 大形态精灵比碰撞盒高出 ~12px：探进实心砖的部分源裁剪（头顶被砖遮住，脚不离地） */
  let cropTop = 0;
  const over = spr.height - p.h;
  if (over > 0) {
    const sprTop = p.y - over;
    const c0 = Math.floor((p.x + 3) / TILE), c1 = Math.floor((p.x + p.w - 3) / TILE);
    for (let r = Math.max(0, Math.floor(sprTop / TILE)); r * TILE < p.y; r++)
      for (let c = c0; c <= c1; c++)
        if (isSolid(c, r)) cropTop = Math.max(cropTop, Math.min(over, (r + 1) * TILE - sprTop));
  }
  ctx.translate(Math.round(p.x - camX) + (p.facing < 0 ? p.w : 0), Math.round(p.y));
  if (p.facing < 0) ctx.scale(-1, 1);
  if (gameState === 'pipeIn') ctx.globalAlpha = Math.max(0, 1 - seqT / 0.65);   // 入管渐隐
  if (cropTop > 0) ctx.drawImage(spr, 0, cropTop, spr.width, spr.height - cropTop,
                                 dx, dy + cropTop, spr.width, spr.height - cropTop);
  else ctx.drawImage(spr, dx, dy);
  ctx.globalAlpha = 1;
  ctx.restore();"""))
edits.append(("""  while (acc >= STEP && n < 8) {                       // 固定步长推进物理（标题/暂停冻结）
    if (gameState !== 'pause' && gameState !== 'title') update(STEP);
    else coinT += STEP;                                // 标题下金币动画照常闪烁
    acc -= STEP; n++;
  }""",
              """  while (acc >= STEP && n < 8) {                       // 固定步长推进物理（标题/暂停/顿帧冻结）
    if (hitStopT > 0) hitStopT -= STEP;                // 打击顿帧：世界微冻结，画面不糊
    else if (gameState !== 'pause' && gameState !== 'title') update(STEP);
    else coinT += STEP;                                // 标题下金币动画照常闪烁
    acc -= STEP; n++;
  }"""))
edits.append(("sfx('stomp');", "sfx('stomp'); hitStopT = 0.035;"))
edits.append(("""function breakBrick(tx, row) {
  map[row][tx] = T_EMPTY;
  addScore(PTS_BRICK, tx * TILE, row * TILE - 8);""",
              """function breakBrick(tx, row) {
  map[row][tx] = T_EMPTY;
  hitStopT = 0.035;
  addScore(PTS_BRICK, tx * TILE, row * TILE - 8);"""))
edits.append(("""  if (gameState === 'win') {
    ctx.fillStyle = 'rgba(10,10,30,.62)'; ctx.fillRect(0, 0, VIEW_W, VIEW_H);
    ctx.textAlign = 'center';
    shadowText('通 关 ！', VIEW_W / 2, VIEW_H / 2 - 56, 52, '#ffd23f');
    shadowText('高度加成 +' + poleBonus + ' ・ 时间加成 +' + timeBonus + '（×50）', VIEW_W / 2, VIEW_H / 2 - 12, 20, '#9ff0a8');
    shadowText('得分 ' + score + ' ・ 金币 ' + coins + ' ・ 用时 ' + gameTime.toFixed(1) + ' 秒',
               VIEW_W / 2, VIEW_H / 2 + 18, 20);
    shadowText('最高分 ' + hiScore + ' ・ 剩余生命 ' + lives,
               VIEW_W / 2, VIEW_H / 2 + 46, 16, '#ffd23f');
    if (blink) shadowText('按 R / 点击【Ⅱ】进入下一轮', VIEW_W / 2, VIEW_H / 2 + 82, 16, '#9fb4d0');
    ctx.textAlign = 'left';
  }""",
              """  if (gameState === 'win') {
    ctx.fillStyle = 'rgba(10,10,30,.62)'; ctx.fillRect(0, 0, VIEW_W, VIEW_H);
    ctx.textAlign = 'center';
    shadowText('通 关 ！', VIEW_W / 2, VIEW_H / 2 - 84, 52, '#ffd23f');
    /* 仪式感：马里奥与公主同框（原版通关构图，2x 整数缩放保持像素感） */
    const baseY = VIEW_H / 2 + 4;
    ctx.drawImage(PRINCESS_SPR, VIEW_W / 2 + 22, baseY - 96, 64, 96);
    ctx.drawImage(SP.idle, VIEW_W / 2 - 72, baseY - 64, 48, 64);
    shadowText('Mario ♥ 公主', VIEW_W / 2, VIEW_H / 2 - 12, 20, '#ff9de2');
    shadowText('高度加成 +' + poleBonus + ' ・ 时间加成 +' + timeBonus + '（×50）', VIEW_W / 2, VIEW_H / 2 + 22, 18, '#9ff0a8');
    shadowText('得分 ' + score + ' ・ 金币 ' + coins + ' ・ 最高分 ' + hiScore,
               VIEW_W / 2, VIEW_H / 2 + 50, 18);
    if (blink) shadowText('按 R / 点击【Ⅱ】返回标题', VIEW_W / 2, VIEW_H / 2 + 86, 16, '#9fb4d0');
    ctx.textAlign = 'left';
  }"""))
edits.append(("  if (e.code === 'KeyR') { resetGame(); return; }",
              "  if (e.code === 'KeyR') { if (gameState === 'win') gameState = 'title'; else resetGame(); return; }"))
edits.append(("  else if (gameState === 'win' || gameState === 'gameover') resetGame();   // 结算界面：下一轮/重开",
              "  else if (gameState === 'win') gameState = 'title';                     // 通关画面：回标题（可重选关卡）\n"
              "  else if (gameState === 'gameover') resetGame();"))

for old, new in edits:
    n = src.count(old)
    assert n >= 1, 'MISSING: ' + old[:60]
    src = src.replace(old, new)

# drawCastleFlag：城堡旗（塔身后升起）
old_c = "function drawCastle() {"
flag_fn = """/** 城堡升旗：进城堡后旗子从塔身后升起（画在城堡之前，塔身遮挡未升出部分） */
function drawCastleFlag() {
  if (castleFlagT < 0 || world !== 'over') return;
  const gy = GROUND_ROW * TILE, cx = CASTLE_COL * TILE;
  if (cx - camX < -220 || cx - camX > VIEW_W + 220) return;
  const prog = Math.min(1, castleFlagT / 1.2);
  const fy = (gy - 96) - 78 * prog;                      // 从塔身内升到塔顶上方
  ctx.drawImage(FLAGC_SPR, cx + 80 - 13, fy, 26, 32);
}
function drawCastle() {"""
assert src.count(old_c) == 1
src = src.replace(old_c, flag_fn)

io.open('index.html', 'w', encoding='utf-8', newline='\n').write(src)
print('all edits ok; stomp sites:', src.count('hitStopT = 0.035'))
