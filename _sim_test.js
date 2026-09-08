// node 仿真回归：DOM 桩 + 直接驱动 update()，验证摔坑直达 Game Over / 变身定格
const fs = require('fs');
const src = fs.readFileSync('index.html', 'utf8');
const js = src.match(/<script>([\s\S]*?)<\/script>/)[1];

function makeCtx() {
  return new Proxy({}, {
    get(t, k) {
      if (k === 'canvas') return { width: 960, height: 544 };
      if (!(k in t)) t[k] = () => makeCtx();
      return t[k];
    },
    set() { return true; },
  });
}
const elStub = () => ({
  width: 32, height: 32, style: {}, textContent: '',
  getContext: () => makeCtx(),
  addEventListener() {}, removeEventListener() {},
  appendChild() {}, setAttribute() {}, getAttribute: () => null,
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 960, height: 544 }),
  classList: { add() {}, remove() {}, toggle() {} },
  querySelector: () => elStub(), querySelectorAll: () => [],
  focus() {}, click() {},
});
const documentStub = {
  getElementById: () => elStub(),
  createElement: () => elStub(),
  addEventListener() {}, removeEventListener() {},
  body: elStub(), documentElement: elStub(),
  querySelector: () => elStub(), querySelectorAll: () => [],
  hidden: false, visibilityState: 'visible',
};
const win = {
  document: documentStub,
  addEventListener() {}, removeEventListener() {},
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  requestAnimationFrame: () => 0,
  performance: { now: () => 0 },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  location: { href: 'x', reload() {} },
  devicePixelRatio: 1, innerWidth: 960, innerHeight: 544,
  setTimeout, setInterval, clearTimeout, clearInterval, console,
};
let fail = 0;
function check(name, cond) { console.log((cond ? 'PASS' : 'FAIL') + ' ' + name); if (!cond) fail++; }

try {
  const fn = new Function('document', 'window', 'localStorage', 'performance',
    'requestAnimationFrame', 'addEventListener', 'matchMedia', 'location',
    'devicePixelRatio', 'innerWidth', 'innerHeight', 'navigator', js + `
  ;return { startGame, update, render, enemies: () => enemies, player: () => player, completeLevel,
            getProgress: () => progress, isLocked: levelLocked, setTitleSel: v => titleSel = v,
            getGS: () => gameState, addScoreFn: (v) => addScore(v, 0, 0), levelName: () => LEVEL_NAME, input: () => input, gameState: () => gameState,
            setMode, die, getLives: () => lives, getMorphT: () => morphT,
            setState: s => gameState = s, setX: x => player.x = x, setY: y => player.y = y,
            startLevel, headBump, getMap: () => map, getItems: () => items,
            starUsed: () => starBricks, getCamX: () => camX, setCamX: v => camX = v,
            getLifts: () => lifts, getPlants: () => plants, getUnders: () => underMaps,
            getWorld: () => world, getRoomIdx: () => roomIdx,
            getTheme: () => cur.theme, multiBricks,
            bossRoom: () => bossRoom, T_SHOP: () => T_SHOP, BR_SHOP: () => BR_SHOP,
            getCoins: () => coins, setCoins: v => coins = v, setLives: v => lives = v,
            getRoomType: () => (cur.unders[roomIdx] || {}).type,
            buyShopItem, buildBossRoomMap, settleRoomCoins, spawnCoinRain,
            getFireballs: () => fireballs, shootFireball };`);
  const G = fn(documentStub, win, win.localStorage, win.performance, win.requestAnimationFrame,
    win.addEventListener, win.matchMedia, win.location, 1, 960, 544,
    { userAgent: 'node', maxTouchPoints: 0 });

  // --- 用例0：渲染冒烟（含隐藏砖在视野内的完整 render 路径） ---
  G.startGame();
  G.render();
  check('render 无异常(含隐藏砖)', true);

  // --- 用例1：摔坑 → 直接 gameover，不扣命 ---
  G.startGame();
  G.setX(69.5 * 32); G.setY(12 * 32);          // 第一个坑上方
  const livesBefore = G.getLives();
  for (let i = 0; i < 60 * 3; i++) G.update(1 / 60);
  check('摔坑后进入 gameover', G.gameState() === 'gameover');
  check('摔坑不扣命(命数不变)', G.getLives() === livesBefore);

  // --- 用例2：变身定格存在且随时间消退，期间形态已切换 ---
  G.setState('play'); G.startGame();
  G.setMode('big');
  check('变身触发定格 morphT>0', G.getMorphT() > 0);
  check('形态立即切换为 big', G.player().mode === 'big' && G.player().h === 52);
  for (let i = 0; i < 60; i++) G.update(1 / 60);
  check('定格1秒内消退', G.getMorphT() <= 0);

  // --- 用例3：敌人碰到死（非摔坑）→ 正常扣命重生 ---
  G.setState('play');
  const lives3 = G.getLives();
  G.die();
  for (let i = 0; i < 60 * 2.5; i++) G.update(1 / 60);
  check('非摔坑死亡扣1命', G.getLives() === lives3 - 1);
  check('非摔坑死亡后回 play', G.gameState() === 'play');

  // --- 用例4：小怪到坑边自动折返不掉坑 ---
  G.setState('play');
  G.startGame();
  const ens = G.enemies();
  ens.length = 0;
  const g = { kind: 'goomba', x: 67.5 * 32, y: G.player().y, w: 24, h: 24,
              vx: -60, vy: 0, onGround: false, squashT: 0, dead: false, runT: 0 };
  ens.push(g);                                     // 摆在第一个坑(69-70)左侧向左走? 不:向右走向坑
  g.x = 68.2 * 32; g.vx = 60;
  g.y = 15 * 32 - 24;
  for (let i = 0; i < 60 * 8; i++) G.update(1 / 60);
  const inPit = g.y > 15 * 32;                     // 掉到地面线以下 = 掉坑
  check('板栗怪坑边折返不掉坑', !inPit && Math.abs(g.vx) > 0);
  const k = { kind: 'koopa', x: 68.2 * 32, y: 15 * 32 - 30, w: 24, h: 30,
              vx: 60, vy: 0, onGround: false, squashT: 0, dead: false, runT: 0 };
  ens.length = 0; ens.push(k);
  for (let i = 0; i < 60 * 8; i++) G.update(1 / 60);
  check('乌龟坑边折返不掉坑', k.y <= 15 * 32 && Math.abs(k.vx) > 0);

  // --- 用例5：进度存档（解锁 + 单关最高分 + 锁定不可启动） ---
  G.setState('play');
  G.startGame();                                      // 从 1-1 开始
  G.addScoreFn(500);
  G.completeLevel();                                  // 通关 1-1 → 存档 + 解锁 1-2
  check('通关后解锁下一关', G.getProgress().unlocked >= 2);
  check('单关最高分入档', (G.getProgress().best[0] || 0) >= 500);
  G.setTitleSel(1);
  check('已解锁关可进入', G.levelName() === 'World 1-2' || (() => { G.startGame(); return G.levelName() === 'World 1-2'; })());
  G.startGame();
  check('选中的 1-2 正常启动', G.levelName() === 'World 1-2' && G.getGS() === 'play');

  // --- 用例6：星星砖（col101 普通砖）→ 顶出星星不碎 / 不重复出货 / 出货后大形态可碎 ---
  G.setState('title');
  G.setTitleSel(0);                                     // 用例5把选关停在1-2，回标题选回1-1
  G.startGame();                                        // 1-1
  const map = G.getMap();
  check('星星藏于 col101 普通砖', map[11][101] === 2 && map[11][109] === 3);   // T_BRICK=2 / T_QBLOCK=3
  G.setX(101 * 32 + 4);                                 // 站到星星砖正下方
  G.headBump(11, 101, 101);
  check('顶星星砖弹出星星', G.getItems().length === 1 && G.getItems()[0].kind === 'star');
  check('出星砖不碎裂', map[11][101] === 2);
  check('已出货标记入档', G.starUsed().has('101,11'));
  G.headBump(11, 101, 101);                             // 小形态再顶：普通砖弹跳，不再出货
  check('星星不重复出货', G.getItems().length === 1);
  G.setMode('big');
  for (let i = 0; i < 60; i++) G.update(1 / 60);        // 定格消退
  G.setX(101 * 32 + 4);
  G.headBump(11, 101, 101);                             // 出货后还原普通砖：大形态可碎
  check('出货后大形态可碎', map[11][101] === 0);        // T_EMPTY=0

  // --- 用例7：1-3 高空关（机制对齐原版）：数据展开 / camX 归位 / 红龟生成 / 渲染冒烟 / 末关 win ---
  G.setCamX(5000);                                      // 模拟上一关残留相机位
  G.startLevel(2);
  check('1-3 载入', G.levelName() === 'World 1-3');
  check('换关相机归位(防残位错生成)', G.getCamX() === 0);
  const m3 = G.getMap();
  check('深渊与起终点地面', m3[15][30] === 0 && m3[15][5] === 1 && m3[15][110] === 1);
  check('浮空岛链展开', m3[11][13] === 2 && m3[9][18] === 2 && m3[7][30] === 2 && m3[7][101] === 2);
  check('?块/踏步/终点楼梯展开', m3[11][34] === 3 && m3[9][27] === 2 && m3[9][145] === 1 && m3[14][140] === 1);
  check('空中金币展开', m3[6][29] === 4 && m3[8][41] === 4 && m3[6][56] === 4);
  check('升降台两座就位', G.getLifts().length === 2 && G.getLifts()[0].x === 38 * 32);
  for (let i = 0; i < 40; i++) G.update(1 / 60);        // 首屏敌人实体化并落台
  const redK = G.enemies().find(e => e.kind === 'koopa' && Math.abs(e.x - 23 * 32) < 60);
  check('首屏红龟生成并站上岛', !!redK && redK.red === true && Math.abs(redK.y + redK.h - 11 * 32) < 8 && redK.onGround);
  const g13 = G.enemies().find(e => e.kind === 'goomba' && Math.abs(e.x - 13 * 32) < 60);
  check('高台板栗怪 row11 就位', !!g13 && Math.abs(g13.y + g13.h - 11 * 32) < 8);
  check('升降台往复巡航', G.getLifts()[0].x > 38 * 32);
  G.render();
  check('1-3 渲染冒烟', true);
  G.completeLevel();
  check('末关通关进入 win', G.getGS() === 'win');
  check('通关解锁 1-3 入档', G.getProgress().unlocked >= 3);

  // --- 用例8：跳跳龟 + 升降台机制 ---
  G.setState('play'); G.startLevel(2);
  const p8 = G.player();
  p8.x = 73 * 32 + 8; p8.y = 11 * 32 - p8.h; p8.invulnT = 99;   // 站到 I7 岛右端并开无敌，避免干扰
  const ens8 = G.enemies(); ens8.length = 0;
  const para = { kind:'para', x:71*32, y:11*32-30, w:24, h:30, vx:-86, vy:0,
                 onGround:false, squashT:0, dead:false, runT:0, red:true };
  ens8.push(para);
  let bounced = false, minY = 1e9, minX = 1e9, maxX = -1e9;
  for (let i = 0; i < 60 * 6; i++) {
    G.update(1 / 60);
    if (para.vy < -100) bounced = true;
    minY = Math.min(minY, para.y); minX = Math.min(minX, para.x); maxX = Math.max(maxX, para.x);
  }
  check('跳跳龟周期性弹跳', bounced);
  check('跳跳龟弹跳高度≈2格', 322 - minY >= 48 && 322 - minY <= 88);
  check('跳跳龟不越岛不掉坑', minX >= 69 * 32 - 4 && maxX <= 73 * 32 + 28 && para.y < 11 * 32);
  p8.x = para.x; p8.y = para.y - p8.h + 6; p8.vy = 200; p8.onGround = false;
  G.update(1 / 60);                                     // 从上方落到跳跳龟背上
  check('踩跳跳龟折翼变红乌龟', para.kind === 'koopa' && para.red === true);
  const L2 = G.getLifts()[1];                           // 台2（row8）
  p8.standLift = null;
  p8.x = L2.x + 40; p8.y = L2.y - p8.h - 6; p8.vy = 150; p8.onGround = false;
  for (let i = 0; i < 3; i++) G.update(1 / 60);
  check('下落吸附到升降台', p8.standLift === L2 && Math.abs(p8.y + p8.h - L2.y) < 1);
  const px0 = p8.x, lx0 = L2.x;
  for (let i = 0; i < 30; i++) G.update(1 / 60);
  check('站立随台横移不脱台', p8.standLift === L2 && Math.abs((p8.x - px0) - (L2.x - lx0)) < 2);

  // --- 用例9：1-2 地下关（机制对齐原版）：天花板/吊管倒挂食人花/金币房入出管全流程/星星砖/十金币砖 ---
  G.setState('play'); G.startLevel(1);
  const m2 = G.getMap();
  check('1-2 载入且地下主题', G.levelName() === 'World 1-2' && G.getTheme() === 'under');
  check('天花板砖层铺开且旗杆前留空', m2[0][40] === 2 && m2[1][40] === 2 && m2[0][160] === 0);
  check('吊管自 row2 下挂', m2[2][18] === 5 && m2[3][18] === 5 && m2[4][18] === 0);
  const dp = G.getPlants().find(p => p.col === 18);
  check('倒挂食人花生成(管口朝下)', !!dp && dp.down === true && dp.mouthY === 4 * 32);
  check('三座金币房地图就位', G.getUnders().length === 3 && G.getUnders()[2][15][10] === 1);
  const p9 = G.player(), inp = G.input();
  p9.x = 113 * 32 - p9.w / 2; p9.y = (15 - 2) * 32 - p9.h; p9.vy = 0; p9.onGround = true;
  inp.down = true;
  for (let i = 0; i < 8; i++) G.update(1 / 60);
  check('管口按↓进入管道', G.getGS() === 'pipeIn');
  for (let i = 0; i < 70; i++) G.update(1 / 60);
  check('落入金币房(索引0)', G.getWorld() === 'under' && G.getRoomIdx() === 0 && G.getGS() === 'play');
  inp.down = false;
  p9.x = 26 * 32 + 12; p9.y = 15 * 32 - p9.h; p9.onGround = true; inp.right = true;
  for (let i = 0; i < 8; i++) G.update(1 / 60);
  check('房内右行触发出管', G.getGS() === 'pipeOut');
  for (let i = 0; i < 120 && G.getWorld() === 'under'; i++) G.update(1 / 60);   // 回到地上立刻停输入
  inp.right = false; p9.vx = 0;
  check('出管回到地上 exitCol116', G.getWorld() === 'over' && Math.abs(p9.x - (117 * 32 - p9.w / 2)) < 40);
  G.startLevel(1);
  const m2b = G.getMap();
  G.setX(68 * 32 + 4); G.headBump(11, 68, 68);
  check('1-2 星星砖出星不碎', G.getItems().some(it => it.kind === 'star') && m2b[11][68] === 2);
  G.headBump(7, 31, 31);
  check('1-2 十金币砖计数', G.multiBricks.has('31,7'));
  G.render();
  check('1-2 渲染冒烟', true);

  // --- 用例10：通关走向城堡播放走路动画（修复：tohouse 沿用抓杆 onGround=false → 全程跳姿） ---
  G.setState('play'); G.startLevel(0);
  G.setX(198 * 32); G.setY(13 * 32);                  // 跳到旗杆触发 checkFlag
  for (let i = 0; i < 200 && G.getGS() !== 'tohouse'; i++) G.update(1 / 60);
  check('抓杆下滑后进入走城堡状态', G.getGS() === 'tohouse');
  const p10 = G.player();
  const r0 = p10.runT;
  for (let i = 0; i < 10; i++) G.update(1 / 60);
  check('走向城堡播放走路动画', p10.onGround === true && p10.vx === 96 && p10.runT > r0);
  for (let i = 0; i < 200 && G.getGS() !== 'flagup'; i++) G.update(1 / 60);
  check('走进门洞后开始升旗', G.getGS() === 'flagup');

  /* ================= 资源管理 Boss 奖励房（用例 11~13） ================= */
  const TS = G.T_SHOP(), TQ = 6;                     // T_QUSED=6
  const enterRoom11 = (p, inp) => {                  // 站到 col46 四格管口按 ↓ 入房
    p.x = 46.5 * 32; p.y = 11 * 32 - p.h; p.vy = 0; p.onGround = true; p.invulnT = 0;
    inp.down = true;
    for (let i = 0; i < 8; i++) G.update(1 / 60);
    for (let i = 0; i < 70; i++) G.update(1 / 60);
    inp.down = false;
  };
  // --- 用例11：地图展开 / 入房规则 / 商店与四件能力 / Boss 战 / 胜利结算 ---
  G.setState('play'); G.startLevel(0);
  const u11 = G.getUnders(), m11 = u11[1];            // u11=房间数组，m11=Boss 房 map[row][col]
  check('1-1 第二间房为 Boss 房', u11.length === 2 && m11[11][6] === TS && m11[11][15] === TS);
  check('Boss 房封闭：天花板+地面+右墙', m11[0][20] === 2 && m11[1][20] === 2 && m11[15][20] === 1 && m11[7][39] === 1);
  check('过渡区三级平台且台上带金币', m11[12][18] === 2 && m11[11][18] === 4 && m11[10][21] === 2 && m11[9][21] === 4 && m11[8][23] === 2);
  check('竞技场两高台就位', m11[11][29] === 2 && m11[9][35] === 2 && m11[14][36] === 0);
  const p11 = G.player(), inp11 = G.input();
  G.setMode('big');
  for (let i = 0; i < 50; i++) G.update(1 / 60);       // 变身定格消退
  enterRoom11(p11, inp11);
  const B11 = G.bossRoom();
  check('落入 Boss 房(索引1)', G.getWorld() === 'under' && G.getRoomIdx() === 1 && G.getRoomType() === 'boss' && G.getGS() === 'play');
  check('房内余额 100 且强制小形态', B11.active && B11.coins === 100 && p11.mode === 'small' && p11.h === 30);
  check('入房存档原形态 big', B11.origMode === 'big');
  check('库巴就位 5 血', !!B11.boss && B11.boss.hp === 5 && Math.abs(B11.boss.x - 36 * 32) < 1);
  G.render();
  check('Boss 房渲染冒烟(商店阶段)', true);
  p11.x = 6 * 32 + 4;
  B11.coins = 10;
  G.headBump(11, 6, 6);
  check('买不起：不扣钱、货架不变、价格闪红', B11.coins === 10 && G.getMap()[11][6] === TS && B11.shop[6].flashT > 0);
  B11.coins = 100;
  G.headBump(11, 6, 6);
  check('顶商店砖=购买二段跳(-50)', B11.coins === 50 && B11.buffs.doubleJump === true && G.getMap()[11][6] === TQ);
  G.headBump(11, 9, 9);                                // 余额只剩 50，买 100 的无敌 → 仍不足
  check('余额不足第二件也不扣钱', B11.coins === 50 && B11.buffs.invincible === 0);
  B11.coins = 100;
  G.headBump(11, 9, 9);
  check('无敌砖购买给 8 秒并进恢复冷却', B11.buffs.invincible === 8 && B11.shop[9].respawnT === 10 && G.getMap()[11][9] === TQ);
  for (let i = 0; i < 60 * 11; i++) G.update(1 / 60);
  check('10 秒后无敌砖恢复可购', G.getMap()[11][9] === TS && B11.shop[9].bought === false);
  B11.buffs.canDoubleJump = true;
  p11.x = 3 * 32; p11.y = 9 * 32; p11.vy = 200; p11.onGround = false; p11.coyote = 0; p11.invulnT = 5;
  inp11.jumpQueued = 0.1;
  G.update(1 / 60);
  check('二段跳：空中追加一次起跳', p11.vy < 0 && B11.buffs.canDoubleJump === false);
  inp11.jumpQueued = 0.1;
  for (let i = 0; i < 3; i++) G.update(1 / 60);
  check('二段跳单次起跳后不可连跳', p11.vy > 0 || B11.buffs.canDoubleJump === false);
  for (let i = 0; i < 150 && !p11.onGround; i++) G.update(1 / 60);
  check('落地恢复二段跳次数', p11.onGround === true && B11.buffs.canDoubleJump === true);
  B11.buffs.speedBoost = true;
  p11.x = 3 * 32; p11.y = 15 * 32 - p11.h; p11.vx = 0; p11.onGround = true; p11.invulnT = 5;
  inp11.right = true;
  for (let i = 0; i < 70; i++) G.update(1 / 60);
  check('加速跑上限 ×1.3(>250)', p11.vx > 250 && p11.vx <= 330);
  inp11.right = false; B11.buffs.speedBoost = false;
  const fbBefore = G.getFireballs().length;
  G.shootFireball();
  check('小形态无火球术 buff 不能发射', G.getFireballs().length === fbBefore);
  B11.buffs.fireball = true;
  G.shootFireball();
  check('小形态 + 火球术可扔火球', G.getFireballs().length === fbBefore + 1);
  G.getFireballs().length = 0;
  B11.buffs.invincible = 999;                          // 免伤，避免战斗中误判为失败结算
  p11.x = 26 * 32; p11.y = 15 * 32 - p11.h; p11.vy = 0; p11.onGround = true;
  for (let i = 0; i < 10; i++) G.update(1 / 60);
  check('激活后开场 0.5 秒站立观察', B11.state === 'boss' && B11.boss.state === 'idle' && B11.boss.vx === 0);
  for (let i = 0; i < 50; i++) G.update(1 / 60);
  check('越过竞技场列激活 Boss 战', B11.state === 'boss' && B11.boss.state !== 'dead');
  B11.drops.length = 0;
  for (let i = 0; i < 6; i++) G.spawnCoinRain();
  const dcols = B11.drops.map(d => Math.floor(d.x / 32));
  check('金币雨只落在竞技场列 26~38', dcols.length > 0 && dcols.every(c => c >= 26 && c <= 38));
  let sawDrops = 0, sawHammer = false;
  for (let i = 0; i < 60 * 6; i++) { G.update(1 / 60); if (B11.drops.length) sawDrops = Math.max(sawDrops, B11.drops.length); if (B11.hammers.length) sawHammer = true; }
  check('战斗期金币雨(3-5 枚)', sawDrops >= 3);
  check('库巴扔锤子', sawHammer);
  const b11 = B11.boss, lives11 = G.getLives();
  G.setCoins(0); B11.coins = 40; B11.dropT = -1e9; B11.drops.length = 0;   // 归零口径 + 暂停金币雨，使结算断言确定
  for (let k = 0; k < 5; k++) {
    b11.x = 30 * 32; b11.y = 15 * 32 - b11.h; b11.stunT = 0; b11.act = 0; b11.state = 'chase';
    p11.x = b11.x + 4; p11.y = b11.y - p11.h + 8; p11.vy = 300; p11.onGround = false; p11.invulnT = 0; p11.starT = 0;
    G.update(1 / 60);
  }
  check('踩头 5 次清空血量并进入死亡动画', B11.boss.hp === 0 && B11.boss.state === 'dead');
  for (let i = 0; i < 60 * 2.2; i++) G.update(1 / 60);
  check('死亡动画 2 秒后进入 clear 结算', B11.state === 'clear');
  check('胜利结算：余额×2 入全局 + 1UP', G.getCoins() === 80 && G.getLives() === lives11 + 1 && B11.coins === 0);
  for (let i = 0; i < 60 * 4; i++) G.update(1 / 60);
  check('clear 3 秒后自动出房回地上', G.getWorld() === 'over' && B11.active === false);
  check('出房恢复原形态尺寸(52)', p11.h === 52 && p11.mode !== 'small');
  check('房内能力全部清除', B11.buffs.doubleJump === false && B11.buffs.fireball === false &&
        B11.buffs.speedBoost === false && B11.buffs.invincible === 0);
  check('稀有奖励已发放(火之花或星星)', p11.mode === 'fire' || p11.starT > 0);

  // --- 用例12：房内死亡 → 花费不退、余额 50% 折算、扣命回地上、小形态重生 ---
  const p12 = G.player(), inp12 = G.input();
  enterRoom11(p12, inp12);
  const B12 = G.bossRoom();
  check('可重复挑战：再入房货架复原余额 100', B12.active && B12.coins === 100 && G.getMap()[11][6] === TS && B12.boss.hp === 5);
  const c12 = (G.setCoins(0), G.getCoins()), l12 = G.getLives();
  B12.coins = 60;                                      // 模拟已花 40（花费不退还）
  G.die();
  for (let i = 0; i < 200; i++) G.update(1 / 60);
  check('房内死亡后回地上重生(play)', G.getWorld() === 'over' && B12.active === false && G.getGS() === 'play');
  check('余额 50% 折算 30 枚入全局', G.getCoins() === c12 + 30);
  check('死亡照常扣 1 命', G.getLives() === l12 - 1);
  check('已花费不退还(余额清零)', B12.coins === 0 && p12.mode === 'small');

  // --- 用例13：主动退出（入口按↓）与激活后回巢回血惩罚 ---
  G.startLevel(0);
  const p13 = G.player(), inp13 = G.input();
  enterRoom11(p13, inp13);
  const B13 = G.bossRoom();
  const c13 = G.getCoins();
  p13.x = 2 * 32 + 8; p13.y = 15 * 32 - p13.h; p13.vx = 0; p13.onGround = true;
  for (let i = 0; i < 10; i++) G.update(1 / 60);       // 先松开 ↓ 解除 downArmed
  inp13.down = true;
  for (let i = 0; i < 40; i++) G.update(1 / 60);
  check('入口按住 ↓ 0.5s 触发主动退出', B13.state === 'leave' || G.getWorld() === 'over');
  for (let i = 0; i < 60 && G.getWorld() === 'under'; i++) G.update(1 / 60);
  check('主动退出余额折半 50 枚', G.getWorld() === 'over' && G.getCoins() === c13 + 50);
  check('主动退出不触发 Boss 战', B13.boss === null && B13.active === false);
  enterRoom11(p13, inp13);
  B13.buffs.invincible = 999;
  p13.x = 26 * 32; p13.y = 15 * 32 - p13.h; p13.onGround = true; p13.vy = 0;
  for (let i = 0; i < 20; i++) G.update(1 / 60);
  check('再入房可激活 Boss', B13.state === 'boss');
  B13.boss.hp = 3;
  p13.x = 20 * 32; p13.y = 15 * 32 - p13.h; p13.onGround = true; p13.vx = 0;
  for (let i = 0; i < 5; i++) G.update(1 / 60);
  check('退回商店区 → Boss 回巢并回血 1 格', Math.abs(B13.boss.x - 36 * 32) < 2 && B13.boss.hp === 4);
  for (let i = 0; i < 60; i++) G.update(1 / 60);
  check('回巢后不逐帧反复回血', B13.boss.hp === 4 && B13.state === 'boss');
  G.render();
  check('Boss 房渲染冒烟(战斗态)', true);
} catch (e) {
  console.error('HARNESS ERROR:', e.message);
  console.error(e.stack.split('\n').slice(0, 3).join('\n'));
  process.exit(1);
}
process.exit(fail ? 1 : 0);
