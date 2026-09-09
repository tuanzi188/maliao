// node 音频回归：mock AudioContext，记录真正落到 AudioParam 的排音事件，
// 验证「选曲表被消费 / 鼓组 pattern / 换曲归零 / stinger / 参数守卫 / 静音」六件事。
const fs = require('fs');
const src = fs.readFileSync('index.html', 'utf8');
const js = src.match(/<script>([\s\S]*?)<\/script>/)[1];

let voices = [];                       // 每个 voice = 一次发声：{kind,wave,f0,f1,cutoff,ftype,vol,at,dur}
let ACTX = null;

function P() {                         // AudioParam 桩：记录 setValueAtTime / ramp 的目标值
  return {
    value: 0, _v0: null, _v1: null,
    setValueAtTime(v) { this.value = v; this._v0 = v; },
    linearRampToValueAtTime(v) { this._v1 = v; },
    exponentialRampToValueAtTime(v) { this._v1 = v; },
  };
}
function node(kind) { return { _kind: kind, _out: null, connect(d) { this._out = d; } }; }
function chainOf(n) {                  // 沿 connect 链找“本声部的”滤波与音量（找到第一个 gain 即停，别走到总线）
  let g = null, f = null, x = n;
  while (x) {
    if (!g && x._kind === 'gain') g = x;
    if (!f && x._kind === 'filter') f = x;
    if (g && f) break;
    x = x._out;
  }
  return { g, f };
}
function makeActx() {
  const A = {
    sampleRate: 48000, currentTime: 0, state: 'running', destination: node('dest'),
    resume() {},
    createGain() { const n = node('gain'); n.gain = P(); return n; },
    createBiquadFilter() { const n = node('filter'); n.type = 'lowpass'; n.frequency = P(); return n; },
    createBuffer(ch, len, sr) { const d = new Float32Array(len); return { length: len, sampleRate: sr, numberOfChannels: ch, getChannelData: () => d }; },
    createOscillator() {
      const n = node('osc'); n.type = 'sine'; n.frequency = P(); n._t0 = 0;
      n.start = t => { n._t0 = t; };
      n.stop = t => {
        const { g } = chainOf(n);
        voices.push({ kind: 'osc', wave: n.type, f0: n.frequency._v0,
                      f1: n.frequency._v1 === null ? n.frequency._v0 : n.frequency._v1,
                      vol: g ? g.gain._v0 : 0, at: n._t0, dur: t - n._t0 });
      };
      return n;
    },
    createBufferSource() {
      const n = node('src'); n.buffer = null; n.loop = false; n._t0 = 0;
      n.start = t => { n._t0 = t; };
      n.stop = t => {
        const { g, f } = chainOf(n);
        voices.push({ kind: 'noise', wave: f ? f.type : '', cutoff: f ? f.frequency.value : 0,
                      ftype: f ? f.type : '', vol: g ? g.gain._v0 : 0, at: n._t0, dur: t - n._t0 });
      };
      return n;
    },
  };
  return A;
}
function AudioContextMock() { if (!ACTX) ACTX = makeActx(); return ACTX; }   // 单例：脚本可推进 currentTime

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
  addEventListener() {}, removeEventListener() {}, appendChild() {}, setAttribute() {}, getAttribute: () => null,
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 960, height: 544 }),
  classList: (() => { const s = new Set(); return { add: c => s.add(c), remove: c => s.delete(c), contains: c => s.has(c),
    toggle: (c, on) => { on === undefined ? (s.has(c) ? s.delete(c) : s.add(c)) : (on ? s.add(c) : s.delete(c)); return s.has(c); } }; })(),
  querySelector: () => elStub(), querySelectorAll: () => [],
  focus() {}, click() {},
});
const documentStub = { getElementById: () => elStub(), createElement: () => elStub(), addEventListener() {}, removeEventListener() {}, body: elStub(), documentElement: elStub(), querySelector: () => elStub(), querySelectorAll: () => [], hidden: false, visibilityState: 'visible' };
const win = { AudioContext: AudioContextMock, document: documentStub, addEventListener() {}, removeEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }), requestAnimationFrame: () => 0, performance: { now: () => 0 }, localStorage: { getItem: () => null, setItem() {}, removeItem() {} }, location: { href: 'x', reload() {} }, devicePixelRatio: 1, innerWidth: 960, innerHeight: 544, setTimeout, setInterval, clearTimeout, clearInterval, console };

let fail = 0;
function check(name, cond) { console.log((cond ? 'PASS' : 'FAIL') + ' ' + name); if (!cond) fail++; }
const midi2f = n => 440 * Math.pow(2, (n - 69) / 12);

try {
  const fn = new Function('document', 'window', 'localStorage', 'performance',
    'requestAnimationFrame', 'addEventListener', 'matchMedia', 'location',
    'devicePixelRatio', 'innerWidth', 'innerHeight', 'navigator', js + `
  ;return { ensureAudio, get actx() { return actx; }, bgmTick, stinger, noiseHit, startLevel, update,
            player: () => player, input: () => input, bossRoom: () => bossRoom,
            BGM_TRACKS: () => BGM_TRACKS, DRUM_KITS: () => DRUM_KITS,
            get track() { return bgmTrack; }, get gs() { return gameState; }, set gs(v) { gameState = v; },
            set audioOn(v) { audioOn = !!v; }, get world() { return world; } };`);
  const G = fn(documentStub, win, win.localStorage, win.performance, win.requestAnimationFrame,
    win.addEventListener, win.matchMedia, win.location, 1, 960, 544,
    { userAgent: 'node', maxTouchPoints: 0 });

  G.startLevel(0); G.gs = 'play'; G.ensureAudio();
  const A = G.actx;
  check('AudioContext 已建（含白噪缓冲）', !!A && A.currentTime === 0);

  let allVoices = [];
  /** 以 50ms 为粒度推进虚拟时间并排音 */
  function pump(sec) {
    const n = Math.round(sec / 0.05);
    for (let i = 0; i < n; i++) { A.currentTime += 0.05; G.bgmTick(); }
    allVoices = allVoices.concat(voices);
  }
  const melVoices = () => voices.filter(v => v.kind === 'osc' && v.wave === 'square');
  const noiseVoices = () => voices.filter(v => v.kind === 'noise');

  // --- 1. 地上主题：旋律表按序被消费 + 三件鼓都在 ---
  voices = []; pump(4);
  check('1-1 选曲 over', G.track === 'over');
  const expOver = G.BGM_TRACKS().over.mel.filter(n => n).slice(0, 8).map(n => Math.round(midi2f(n)));
  const gotOver = melVoices().slice(0, 8).map(v => Math.round(v.f0));
  check('地上旋律表按序排音（前 8 音逐音比对）', JSON.stringify(expOver) === JSON.stringify(gotOver));
  check('鼓组三件齐：底鼓/军鼓/踩镲',
        voices.some(v => v.kind === 'osc' && v.wave === 'sine' && v.f0 > 140 && v.f1 < 60) &&
        noiseVoices().some(v => v.ftype === 'bandpass') && noiseVoices().some(v => v.ftype === 'highpass'));

  // --- 2. 1-3 高空主题：换表 + 时值放慢（rate>1 → 同墙钟时间内音符更少） ---
  const denseOver = melVoices().length;
  G.startLevel(2); voices = []; pump(4);
  check('1-3 选曲 sky（关卡 music 字段驱动）', G.track === 'sky');
  const expSky = G.BGM_TRACKS().sky.mel.filter(n => n).slice(0, 6).map(n => Math.round(midi2f(n)));
  const gotSky = melVoices().slice(0, 6).map(v => Math.round(v.f0));
  check('高空旋律表按序排音（高音区宽跳）', JSON.stringify(expSky) === JSON.stringify(gotSky) && Math.min(...expSky) >= midi2f(70));
  check('高空主题更慢（同时间音符数下降）', melVoices().length < denseOver);
  check('高空鼓组稀疏（无军鼓）', !noiseVoices().some(v => v.ftype === 'bandpass'));

  // --- 3. 1-2 地下：由 theme:'under' 推导选曲，不新增冗余字段 ---
  G.startLevel(1); voices = []; pump(3);
  check('1-2 由 theme 推导为 under', G.track === 'under');
  const expU = G.BGM_TRACKS().under.mel.filter(n => n).slice(0, 6).map(n => Math.round(midi2f(n)));
  check('地下旋律表被消费', JSON.stringify(G.BGM_TRACKS().under.mel.filter(n => n).slice(0, 6).map(n => Math.round(midi2f(n)))) === JSON.stringify(expU));

  // --- 4. Boss 战：入房 → 激活 → 换曲归零 + 驱动型鼓 + 音量抬升 ---
  G.startLevel(0); G.gs = 'play';
  const p = G.player(), inp = G.input();
  p.x = 46.5 * 32; p.y = 11 * 32 - p.h; p.vy = 0; p.onGround = true; inp.down = true;
  for (let i = 0; i < 8; i++) G.update(1 / 60);
  for (let i = 0; i < 70; i++) G.update(1 / 60);
  inp.down = false;
  const B = G.bossRoom();
  check('已进入 Boss 房', G.world === 'under' && B.active);
  voices = []; pump(2);
  check('商店阶段仍用地下曲', G.track === 'under');
  p.x = 26 * 32; p.y = 15 * 32 - p.h; p.onGround = true; p.vy = 0;
  for (let i = 0; i < 40; i++) G.update(1 / 60);
  check('竞技场已激活', B.state === 'boss' && !B.atHome);
  voices = []; pump(3);
  check('激活后切到 Boss 曲', G.track === 'boss');
  const expBoss = G.BGM_TRACKS().boss.mel.filter(n => n).slice(0, 8).map(n => Math.round(midi2f(n)));
  const gotBoss = melVoices().slice(0, 8).map(v => Math.round(v.f0));
  check('Boss 旋律表按序排音（换曲从第 0 步起）', JSON.stringify(expBoss) === JSON.stringify(gotBoss));
  const hats = noiseVoices().filter(v => v.ftype === 'highpass').length;
  const kicks = voices.filter(v => v.kind === 'osc' && v.wave === 'sine').length;
  check('Boss 鼓组为驱动型（八分密镲+四分底鼓）', hats > 10 && kicks > 3);
  check('Boss 曲音量高于探索曲', melVoices().every(v => v.vol <= 0.05 + 1e-9) && melVoices().some(v => v.vol > 0.042));

  // --- 5. 参数守卫与静音 ---
  voices = []; G.noiseHit(NaN, 7600, 0.03, 0, 'highpass'); G.noiseHit(0.03, NaN, 0.03, 0); G.noiseHit(0.03, 7600, 0, 0);
  check('noiseHit 非法参数不出声（NaN/零音量守卫）', voices.length === 0);
  voices = []; G.noiseHit(0.03, 7600, 0.03, 0, 'highpass');
  check('noiseHit 正常参数出声且滤波生效', voices.length === 1 && voices[0].kind === 'noise' && voices[0].ftype === 'highpass');
  voices = []; G.audioOn = false; pump(2); G.audioOn = true;
  check('静音时不排 BGM', voices.length === 0);

  // --- 6. stinger 一次性动机 ---
  voices = []; G.stinger('bossWin');
  const winNotes = voices.filter(v => v.kind === 'osc' && v.wave === 'square').map(v => Math.round(v.f0));
  check('击破 stinger：6 音琶音 + 长顶音 + 低音', winNotes.length === 7 && Math.max(...winNotes) >= Math.round(midi2f(83)));
  voices = []; G.stinger('bossLose');
  const loseNotes = voices.filter(v => v.kind === 'osc').map(v => v.f0);
  check('失败 stinger：半音下行且整体走低', loseNotes.length === 5 && loseNotes.slice(0, 4).every((f, i, a) => i === 0 || f < a[i - 1]));
  voices = []; G.stinger('unknown');
  check('未知 stinger 名不排音', voices.length === 0);

  // --- 7. 全部排音事件的数值健康检查（NaN 会整条链路抛错） ---
  const bad = allVoices.filter(v => {
    if (!(v.vol > 0)) return true;
    if (v.kind === 'noise') return !(v.cutoff >= 40 && v.cutoff <= 20000);
    return !isFinite(v.f0) || !isFinite(v.f1) || !(v.f0 >= 20 && v.f0 <= 20000);
  });
  // 四段主题累计约 120 个发声事件（≈14s 虚拟时间、八分步进），下限只作“确实排过音”的哨兵
  check('四主题累计排音无数值非法（样本 ' + allVoices.length + '）', allVoices.length > 100 && bad.length === 0);
} catch (e) {
  console.error('HARNESS ERROR:', e.message);
  console.error(e.stack.split('\n').slice(0, 4).join('\n'));
  process.exit(1);
}
process.exit(fail ? 1 : 0);
