# -*- coding: utf-8 -*-
# 进度存档：解锁 + 每关最高分 + 选关界面锁/星标
import io

src = io.open('index.html').read()
edits = []

# 1) 存档系统（挂在前面的状态区）
edits.append(("""let titleSel = 0;                      // 标题界面选关指针（↑↓ 切换）
const TITLE_MENU = { x0: 0, w: 380, h: 42, y0: 292, gap: 46 };   // 选关菜单几何（原版文字菜单风，x0 绘制时按 VIEW_W 居中）""",
"""let titleSel = 0;                      // 标题界面选关指针（↑↓ 切换）
const TITLE_MENU = { x0: 0, w: 380, h: 42, y0: 292, gap: 46 };   // 选关菜单几何（原版文字菜单风，x0 绘制时按 VIEW_W 居中）
/* ---- 进度存档：解锁关卡数 + 每关最高分（localStorage 持久化） ---- */
let progress = { unlocked: 1, best: {} };
try {
  const saved = JSON.parse(localStorage.getItem('pmario_progress') || 'null');
  if (saved && saved.unlocked >= 1) progress = saved;
} catch (_) {}
function saveProgress() { try { localStorage.setItem('pmario_progress', JSON.stringify(progress)); } catch (_) {} }
const levelLocked = i => i >= progress.unlocked;      // 第 i 关是否未解锁
let levelStartScore = 0;                              // 本关起始分（算单关得分用）"""))

# 2) startLevel 记录起始分
edits.append(("  checkpoint = { x: SPAWN.x, y: SPAWN.y };\n  respawn();",
              "  levelStartScore = score;                         // 记录本关起始分（过关时算单关得分入档）\n"
              "  checkpoint = { x: SPAWN.x, y: SPAWN.y };\n  respawn();"))

# 3) completeLevel：保分换关前先存档（解锁下一关 + 单关最高分）
edits.append(("""function completeLevel() {
  if (levelIdx < LEVELS.length - 1) { startLevel(levelIdx + 1); sfx('win'); }
  else { gameState = 'win'; saveHi(); sfx('win'); }
}""",
"""function completeLevel() {
  const gained = score - levelStartScore;            // 本关单关得分（含时间加成）
  progress.best[levelIdx] = Math.max(progress.best[levelIdx] || 0, gained);
  progress.unlocked = Math.max(progress.unlocked, Math.min(LEVELS.length, levelIdx + 2));
  saveProgress();
  if (levelIdx < LEVELS.length - 1) { startLevel(levelIdx + 1); sfx('win'); }
  else { gameState = 'win'; saveHi(); sfx('win'); }
}"""))

# 4) 键盘选关：跳过未解锁关
edits.append(("""  if (gameState === 'title') {                     // 标题：↑↓/W S 选关，空格/回车/J 或任意其他键开始
    if (e.code === 'ArrowUp' || e.code === 'KeyW') { titleSel = (titleSel + LEVELS.length - 1) % LEVELS.length; sfx('coin'); return; }
    if (e.code === 'ArrowDown' || e.code === 'KeyS') { titleSel = (titleSel + 1) % LEVELS.length; sfx('coin'); return; }
    startGame(); return;
  }""",
"""  if (gameState === 'title') {                     // 标题：↑↓/W S 选关（自动跳过未解锁），其余键开始
    if (e.code === 'ArrowUp' || e.code === 'KeyW' || e.code === 'ArrowDown' || e.code === 'KeyS') {
      const dir = (e.code === 'ArrowUp' || e.code === 'KeyW') ? -1 : 1;
      let n = titleSel;
      for (let k = 0; k < LEVELS.length; k++) {
        n = (n + dir + LEVELS.length) % LEVELS.length;
        if (!levelLocked(n)) break;
      }
      if (n !== titleSel) { titleSel = n; sfx('coin'); }
      return;
    }
    if (!levelLocked(titleSel)) startGame(); else sfx('bump');
    return;
  }"""))

# 5) 点击选关：未解锁拒绝
edits.append(("""  if (i < 0 || i >= LEVELS.length || x < M.x0 - 12 || x > M.x0 + M.w + 12 || (y - (M.y0 - 8)) > M.h * LEVELS.length + (LEVELS.length - 1) * (M.gap - M.h) + 16) return;
  ensureAudio();
  if (i === titleSel) startGame(); else { titleSel = i; sfx('coin'); }""",
"""  if (i < 0 || i >= LEVELS.length || x < M.x0 - 12 || x > M.x0 + M.w + 12 || (y - (M.y0 - 8)) > M.h * LEVELS.length + (LEVELS.length - 1) * (M.gap - M.h) + 16) return;
  ensureAudio();
  if (levelLocked(i)) { sfx('bump'); return; }       // 未解锁：闷响拒绝
  if (i === titleSel) startGame(); else { titleSel = i; sfx('coin'); }"""))

# 6) 标题绘制：锁图标 / 星标 / 每关最高分
edits.append(("""    ctx.textAlign = 'left';
    for (let i = 0; i < n; i++) {
      const rowMid = M.y0 + i * M.gap + M.h / 2, sel = i === titleSel;
      if (sel) ctx.drawImage(SP.run[Math.floor(coinT * 8) % 3], M.x0 + 10, rowMid - 16, 21, 32);   // 光标：原地跑的小马里奥
      shadowText(LEVELS[i].name, M.x0 + 52, rowMid + 6, 20, sel ? '#ffffff' : '#7e93ba');
      shadowText(LEVELS[i].under ? '地下奖励房' : '地上', M.x0 + M.w - 40, rowMid + 5, 13, sel ? '#9ff0a8' : '#5f7194');
    }
    ctx.textAlign = 'center';""",
"""    ctx.textAlign = 'left';
    for (let i = 0; i < n; i++) {
      const rowMid = M.y0 + i * M.gap + M.h / 2, sel = i === titleSel, locked = levelLocked(i);
      if (sel && !locked) ctx.drawImage(SP.run[Math.floor(coinT * 8) % 3], M.x0 + 10, rowMid - 16, 21, 32);   // 光标：原地跑的小马里奥
      shadowText(LEVELS[i].name, M.x0 + 52, rowMid + 6, 20, locked ? '#54607a' : (sel ? '#ffffff' : '#7e93ba'));
      const best = progress.best[i] || 0;
      if (locked) {                                   // 像素锁：未解锁
        const lx = M.x0 + M.w - 52, ly = rowMid - 10;
        ctx.fillStyle = '#54607a';
        ctx.fillRect(lx + 1, ly, 8, 3); ctx.fillRect(lx, ly + 2, 10, 8);
        ctx.fillStyle = '#12121e';
        ctx.fillRect(lx + 4, ly + 4, 2, 4);
        shadowText('通关上一关解锁', lx - 108, rowMid + 5, 12, '#54607a');
      } else {
        if (progress.best[i] !== undefined) {         // 通关星标 + 单关最高分
          const sx = M.x0 + M.w - 96;
          ctx.fillStyle = '#ffd23f';
          ctx.fillRect(sx + 3, rowMid - 9, 2, 2); ctx.fillRect(sx + 8, rowMid - 9, 2, 2);
          ctx.fillRect(sx, rowMid - 6, 13, 3); ctx.fillRect(sx + 2, rowMid - 3, 9, 2);
          ctx.fillRect(sx + 4, rowMid - 1, 5, 2);
          shadowText('最高 ' + best, sx + 20, rowMid + 5, 13, sel ? '#ffd23f' : '#b8a23f');
        } else {
          shadowText(LEVELS[i].under ? '地下奖励房' : '地上', M.x0 + M.w - 40, rowMid + 5, 13, sel ? '#9ff0a8' : '#5f7194');
        }
      }
    }
    ctx.textAlign = 'center';"""))

# 7) startGame 兜底守卫（防止锁定关被其他入口启动）
edits.append(("""function startGame() {
  if (gameState !== 'title') return;
  resetGame();
}""",
"""function startGame() {
  if (gameState !== 'title') return;
  if (levelLocked(titleSel)) { sfx('bump'); return; }   // 未解锁关不允许启动
  resetGame();
}"""))

for old, new in edits:
    n = src.count(old)
    assert n >= 1, 'MISSING: ' + old[:60]
    src = src.replace(old, new)

io.open('index.html', 'w', encoding='utf-8', newline='\n').write(src)
print('progress-save patches ok')
