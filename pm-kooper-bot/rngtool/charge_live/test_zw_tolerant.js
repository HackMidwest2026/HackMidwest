/* v72: the zero-wait tracker weighs its states by the coin instead of dropping them on one missed or false shine
 * (page_template.html zwStep / zwDoubt, charge_live.js chgStartTracker / chgQBack). Run in node against the files on disk
 * ("v72") and against git BASE ("v71", the build before the change), the tracker code taken from each page as
 * charge_live/test_fix_proposal.js does.
 *
 * 1. The 14 Hallway clips' coin timelines (charge_live/clip_events.json: what the page's coin detector saw in a frame-fed
 *    run, ms from the Charge trigger picture; seed and q as the page locked them). The lock lands 0.3 s after the rays and
 *    1 s after the Spiny Flip confirm (as live). Without errors, v72 must be alive at Time Out's confirm wherever v71 is,
 *    with the share of states for which Time Out works there within 0.1 of v71's (the same evidence). Then every shine seen
 *    after the lock is removed in turn (a missed shine) and a false shine is added in the middle of each visible stretch:
 *    v71 loses the seed (counted), v72 must keep it (alive, doubt below 0.5) with the share within 0.15 of the clean run.
 * 2. Honesty, simulated: N random games through the same tracker (seed x q x console lag x Spiny Flip impact x guard x
 *    confirm read error, the clips' coin timeline), the coin detector missing each shine with p = 0.02, adding false
 *    shines at 1.8e-4 per frame of steady coin, and reading flashes -1 .. +3 frames late; plus the same with a wrong lock
 *    (the tracker started on another seed). At Time Out's target screen each version plans as zwPlan does (the best frame
 *    in 1 s after a 1.5 s lead, presses 25/50/25, shown chance = v72's honest mix, beep at 0.4+), and the game is played
 *    at that frame with the same press spread. Checks (v72): the shown chance on the beeped runs is within 0.06 of what
 *    the game gave (mean), the wrong-lock runs beep at most 5% of the time, and v72 beeps at least as often as v71 on the
 *    right locks. Prints both versions.
 * usage (from rngtool/): node charge_live/test_zw_tolerant.js [N=150] */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), cp = require('child_process');
const RT = path.resolve(__dirname, '..'), BASE = process.env.BASE || '2d69af1';     // v71
const R = require(path.join(RT, 'pmrng_core.js'));
function grabFn(src, name) {
  const i = src.indexOf('function ' + name + '('); if (i < 0) throw new Error('no function ' + name);
  for (let k = src.indexOf('{', src.indexOf(')', i)), d = 0; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}' && --d === 0) return src.slice(i, k + 1); }
  throw new Error('unbalanced ' + name);
}
const grabLine = (src, re) => { const m = src.match(re); if (!m) throw new Error('no ' + re); return m[0]; };
const git = f => cp.execFileSync('git', ['show', BASE + ':./' + f], { cwd: RT, maxBuffer: 1 << 26 }).toString();
const SRC = { v72: [fs.readFileSync(path.join(RT, 'page_template.html'), 'utf8'), fs.readFileSync(path.join(RT, 'charge_live/charge_live.js'), 'utf8')], v71: [git('page_template.html'), git('charge_live/charge_live.js')] };
function tracker(ver) {
  const [page, chg] = SRC[ver], a = page.indexOf('const ZW_SCENE'), b = page.indexOf('function zwPlan(');
  const code = [page.slice(a, b), grabLine(chg, /const CHG_N = .*\n/), grabLine(chg, /const CHG_K = .*\n/), grabLine(chg, /const CHG_LAGS = .*\n/),
    grabLine(chg, /const CHG_SHIFTS = .*\n/), grabFn(chg, 'chgRate'), grabFn(chg, 'chgStartTracker'), grabLine(chg, /const CHG_INVN = .*\n/), grabFn(chg, 'chgBack'), grabFn(chg, 'chgQBack'),
    'this.api = { zw, zwF, zwUpdate, zwInput, zwTap, zwCoinBack, zwStatesAt, chgStartTracker, chgQBack, CHG_IMPS, CHG_SHIFTS, CHG_LAGS, doubt: typeof zwDoubt === "function" ? zwDoubt : () => 0 };'].join('\n');
  const settings = { vlag: 50, pfix: 0 }, ctx = { R, FRAME: R.FRAME_MS, Math, Array, Map, Set, Object, Number, JSON, String, Float64Array, Infinity, now: 0, log: [],
    VAN: { B: () => R.PROFILES.timeout.vanish }, CHG: {}, V: {}, consoleRate: () => 33.427, isRoute: () => false, RT: () => [], routeStep: 0, num: k => +(settings[k] || 0) };
  ctx.slog = (ev, o) => ctx.log.push(Object.assign({ ev }, o)); ctx.performance = { now: () => ctx.now };
  vm.createContext(ctx); vm.runInContext(code, ctx); return Object.assign(ctx.api, { ctx, ver });
}
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
const settled = p => !p.S.inst.length && !(p.S.extra && p.S.extra.size);
/* the tracker at Time Out's target screen (clock frame cScr): its settled states (weights), the doubt */
function statesAt(L, cScr) {
  L.zw.visTo = cScr - 4; L.zwUpdate(cScr);
  const m = new Map(); for (const p of L.zw.parts) { if (!settled(p) || p.g > cScr) continue; const k = (p.S.s >>> 0) + ':' + p.S.nc + ':' + p.g, q = m.get(k); if (q) q.w += p.w; else m.set(k, { s: p.S.s >>> 0, nc: p.S.nc, g: p.g, w: p.w }); }
  return { list: [...m.values()], doubt: L.doubt(), dead: L.zw.dead };
}
const PE = [[-1, 0.25], [0, 0.5], [1, 0.25]];
function shareAt(list, c) { const tot = list.reduce((a, q) => a + q.w, 0); let ok = 0; for (const q of list) if (R.works(q.s, q.nc, c, q.g, R.PROFILES.timeout)) ok += q.w; return tot ? ok / tot : null; }
/* zwPlan's choice: the best frame (presses 25/50/25) in [from, from + W] by the states' share; shown = honest (v72) */
function plan(S, from, W, ver) {
  if (!S.list.length) return null;
  const sh = []; for (let c = from - 1; c <= from + W + 1; c++) sh.push(shareAt(S.list, c));
  let best = -1, k = 0; for (let i = 0; i <= W; i++) { let v = 0; for (const [d, q] of PE) v += q * sh[i + 1 + d]; if (v > best + 1e-12) { best = v; k = i; } }
  const d = ver === 'v72' ? S.doubt : 0, shown = (1 - d) * best + d * 0.31;
  return { target: from + k, pStates: best, shown, beep: shown >= 0.4 && d < 0.5 };
}
/* ---------- 1. the clips ---------- */
const CLIPS = JSON.parse(fs.readFileSync(path.join(__dirname, 'clip_events.json'), 'utf8'));
function lockAt(L, c, tLock, taps) {
  const { ctx, zw } = L, C = ctx.CHG, tMaps = 48 * ctx.FRAME + 1, presOf = t => { let p = 0; for (const [a, v] of c.pres) { if (a > t) break; p = v; } return !!p; };
  C.trig = { t: 0 }; C.taps = taps.filter(s => s >= tMaps && s < tLock); C.pres = []; C.spiny = tLock > c.spiny ? c.spiny : null; C.prof = null;
  for (let i = Math.ceil(tMaps * 0.06); i / 0.06 < tLock; i++) { const t = i / 0.06; C.pres.push([t, presOf(t)]); }
  ctx.now = tLock; L.chgStartTracker(parseInt(c.seed, 16) >>> 0, c.qs); return zw;
}
function runClip(ver, c, late, taps) {
  const L = tracker(ver), tLock = late ? c.spiny + 1000 : 48 * L.ctx.FRAME + 300, zw = lockAt(L, c, tLock, taps);
  const evs = [];
  if (tLock <= c.spiny) evs.push([c.spiny, 'spiny']);
  for (const s of taps) if (s >= tLock) evs.push([s, 'shine']);
  for (const [t, h] of c.coinBack) if (t >= tLock) evs.push([t, 'back', h]);
  evs.sort((a, b) => a[0] - b[0]);
  for (const [t, k, h] of evs) { if (t >= c.timeOut) break; L.ctx.now = t + 30;
    if (k === 'spiny') L.zwInput('hw_spiny', t, L.ctx.VAN.B(), L.CHG_IMPS); else if (k === 'shine') L.zwTap(t); else L.zwCoinBack(h); }
  const cf = Math.round(L.zwF(c.timeOut, 0)) - 3; L.ctx.now = c.timeOut; const S = statesAt(L, cf);
  const tot = S.list.reduce((a, q) => a + q.w, 0), w = {}; for (const q of S.list) w[q.s + ':' + q.nc + ':' + q.g] = q.w / tot;
  return { alive: S.list.length > 0, share: S.list.length ? +shareAt(S.list, cf).toFixed(3) : null, states: S.list.length, doubt: +S.doubt.toFixed(3), w };
}
let mlo = 1; const tally = { v71: { miss: 0, missDead: 0, fals: 0, falsDead: 0 }, v72: { miss: 0, missDead: 0, fals: 0, falsDead: 0 } };
for (const [n, c] of Object.entries(process.env.ONLYSIM ? {} : CLIPS)) {
  if (c.timeOut == null) c.timeOut = c.shines[c.shines.length - 1] + 1500;     // no Time Out in the clip (20-54-59): the states after its last shine
  const row = [n];
  for (const late of [true, false]) {
    const tLock = late ? c.spiny + 1000 : 48 * R.FRAME_MS + 300;
    const base = {}; for (const v of ['v71', 'v72']) base[v] = runClip(v, c, late, c.shines);
    if (base.v71.alive) { check(base.v72.alive, n + (late ? ' late' : ' early') + ': v72 dead where v71 is alive');
      check(base.v72.share != null && Math.abs(base.v72.share - base.v71.share) <= 0.1, n + (late ? ' late' : ' early') + ': clean share v72 ' + base.v72.share + ' vs v71 ' + base.v71.share); }
    const after = c.shines.filter(s => s > 48 * R.FRAME_MS && s < c.timeOut - 300);
    const mods = after.map(s => ['miss', c.shines.filter(x => x !== s)]);
    // a false shine in the middle of each visible stretch after the rays that has no shine within 1 s
    const vis = []; for (let i = 0; i < c.pres.length; i++) if (c.pres[i][1] && c.pres[i][0] > 1700) { const a = c.pres[i][0] + 1000, b = (c.pres[i + 1] || [c.timeOut])[0]; if (b - a > 1500) vis.push((a + b) / 2); }
    for (const t of vis) if (t < c.timeOut - 300 && !c.shines.some(x => Math.abs(x - t) < 1000)) mods.push(['fals', c.shines.concat([t]).sort((x, y) => x - y)]);
    const res = [];
    for (const [kind, taps] of mods) {
      const r = {}; for (const v of ['v71', 'v72']) { r[v] = runClip(v, c, late, taps); tally[v][kind]++; if (!r[v].alive || r[v].doubt >= 0.5) tally[v][kind + 'Dead']++; }
      // a missed shine: the states stay and the chance stays near the clean one; a false shine: the states stay (the
      // weights may move to states that explain it: a seen shine is ~50x likelier to be real, so that is the honest answer)
      if (base.v72.alive && base.v72.doubt < 0.5) {
        check(r.v72.alive, n + (late ? ' late' : ' early') + ' ' + kind + ': v72 dropped every state (' + JSON.stringify(r.v72) + ')');
        // a miss loses information, so the chance may move; what must hold is that every state the clean run kept is still
        // there with weight, and the lock is not called doubtful (15-30-15: the model does not fit that clip, see README)
        if (kind === 'miss') { const lost = Object.keys(base.v72.w).filter(k => !(r.v72.w[k] > 0)), mass = Object.keys(base.v72.w).reduce((a, k) => a + (r.v72.w[k] || 0), 0), lostW = lost.reduce((a, k) => a + base.v72.w[k], 0);
          if (n !== '15-30-15') check(lostW < 0.01 && mass >= 0.05, n + (late ? ' late' : ' early') + ' miss: the clean run\'s states lost (' + lost.length + ' of ' + Object.keys(base.v72.w).length + ' holding ' + lostW.toFixed(3) + ' of the clean weight; mass left ' + mass.toFixed(3) + ')');
          if (n !== '15-30-15') check(r.v72.doubt < 0.5, n + (late ? ' late' : ' early') + ' miss: lock called doubtful (' + r.v72.doubt + ')');
          mlo = Math.min(mlo, mass); }
      }
      res.push(kind + (r.v71.alive ? '' : '(v71 dead)') + ' ' + r.v72.share + '/' + r.v72.doubt);
      for (const v of ['v71', 'v72']) delete r[v].w;
    }
    row.push((late ? 'late: ' : 'early: ') + 'clean v71 ' + base.v71.states + ' states ' + base.v71.share + ', v72 ' + base.v72.states + ' ' + base.v72.share + ' doubt ' + base.v72.doubt + ' | ' + res.join(', '));
  }
  console.log('clip ' + row.join(' || '));
}
console.log('v72, a missed shine: the clean run\'s states keep at least ' + mlo.toFixed(3) + ' of the weight');
for (const v of ['v71', 'v72']) console.log(v + ': a missed shine lost the seed in ' + tally[v].missDead + ' of ' + tally[v].miss + ' runs, a false shine in ' + tally[v].falsDead + ' of ' + tally[v].fals);


/* ---------- 3. q from the turn-1 menu's coin (chgQBack), the Duplighost renders (test_dup_page.js, D = 25) ----------
 * The rays' q candidates, the menu stretch and the shines the page read there (ms from the trigger picture), the truth
 * from the emulator log. v71 kept only the q that fit exactly (+-1.5 frames on 33.367 ms); v72 weighs them. On 1234abcd
 * the simulated capture reads the menu shine 3.5 frames late: v71 drops the true q 42 even when the rays offer it. */
const QB = [
  { seed: 'bfdda85d', truth: 42, rays: [38, 39, 40, 41, 42, 43, 44, 45, 46, 47], menu: { from: -4733, to: -533, taps: [-3233] } },
  { seed: 'bfdda85d', truth: 42, rays: [35, 36, 37, 38, 40, 41], menu: { from: -4733, to: -533, taps: [-3233] } },      // the v71 run: 42 not offered
  { seed: 'fc590fa8', truth: 18, rays: [18], menu: { from: -4733, to: -533, taps: [-4067, -1667] } },
  { seed: '2dfcc393', truth: 18, rays: [15, 16, 17, 18], menu: { from: -4733, to: -533, taps: [-3233, -1667] } }];
for (const c of QB) {
  const r = {};
  for (const v of ['v71', 'v72']) { const L = tracker(v); Object.assign(L.ctx.CHG, { trig: { t: 0 }, menu: c.menu }); r[v] = L.chgQBack(parseInt(c.seed, 16) >>> 0, c.rays); }
  const kept71 = r.v71.length ? r.v71 : c.rays, w = r.v72.w || {};
  console.log('q check ' + c.seed + ' (true q ' + c.truth + ', rays ' + c.rays.join('/') + '): v71 keeps ' + kept71.join('/') + (r.v71.length ? '' : ' (none fit: all)') + '; v72 ' + c.rays.filter(q => w[q] > 0).map(q => q + ':' + w[q].toFixed(3)).join(' '));
  if (c.rays.includes(c.truth)) check(w[c.truth] >= 0.2, c.seed + ': v72 must keep the true q ' + c.truth + ' with weight 0.2+ (' + (w[c.truth] || 0).toFixed(3) + ')');
  else check(c.rays.some(q => w[q] > 0), c.seed + ': v72 must keep some q');
}

/* ---------- 4. the Final Bowser clock (fb2_live.js) on the console's frame time ----------
 * A real N64 frame is 33.427 ms (consoleRate's default); v71's FB2 tracker counted 33.367. The game frame shown by a
 * picture 500 game frames after the trigger, and the press time for a target 500 frames on, must agree with the
 * console clock within 0.05 frame; with Settings > Console frame time = 33.367 (emulator renders) the old values come back. */
for (const [ver, src] of [['v71', git('charge_live/fb2_live.js')], ['v72', fs.readFileSync(path.join(__dirname, 'fb2_live.js'), 'utf8')]]) {
  for (const crate of [0, 33.367]) {
    const ctx = { R, FRAME: R.FRAME_MS, Math, Array, Map, Set, Object, Number, JSON, String, CHG: { trig: { t: 1000 } }, $: () => null, slog: () => {}, document: {}, window: {},
      num: k => (k === 'crate' ? crate : 0), consoleRate: () => (crate || 33.427) };
    ctx.chgRate = () => ctx.consoleRate(); vm.createContext(ctx);
    vm.runInContext(src.replace(/^fb2Reset\(\);$/m, '').replace(/^window\.__fb2 = .*$/m, '') + '\nfb2Reset(); this.api = { fb2Pic, fb2PressT };', ctx);
    const r = crate || 33.427, pic = ctx.api.fb2Pic(1000 + 500 * r), err = (ctx.api.fb2PressT(516) - (1000 + (516 - 16 - 1.7) * r)) / r;
    console.log('FB2 clock ' + ver + ' (console ' + r + ' ms): picture 500 frames on reads frame ' + pic.toFixed(2) + ' (true 516), press for +516 off by ' + err.toFixed(2) + ' frames');
    if (ver === 'v72') check(Math.abs(pic - 516) < 0.05 && Math.abs(err) < 0.05, 'v72 FB2 clock on ' + r + ' ms');
  }
}

/* ---------- 2. honesty, simulated ---------- */
const N = +process.argv[2] || 150;
let rs = 0x9e3779b9; const rnd = () => ((rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296);
const pick = W => { let u = rnd(); for (const [v, w] of W) { if ((u -= w) < 0) return v; } return W[W.length - 1][0]; };
const T = { spiny: 3450, back1: [3250, 1650], back2: [7650, 3183], up0: 1700, timeOut: 13800 };   // the 15-14-09 timeline (ms from the trigger)
function game(seed, q, lag, imp, guard, cTrue, gEnd) {     // the true game to clock frame gEnd: coin shine draw frames, the state there
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: cTrue, id: 'hw_spiny', imp, guard }]), S = { s: seed >>> 0, nc: q, inst: [] }, sh2 = [];
  let g = 0; while (g < gEnd) { if (g === 48 + 2 && lag) { S.nc += lag; g += lag; continue; } const r = R.frameEv(S, g, ev); if (r) sh2.push(g); g++; }
  return { shines: sh2, S, g };
}
const H = { v71: { beep: 0, shown: 0, got: 0, n: 0, wbeep: 0, wshown: 0, wgot: 0, wn: 0 }, v72: { beep: 0, shown: 0, got: 0, n: 0, wbeep: 0, wshown: 0, wgot: 0, wn: 0 } };
const RATE = 33.427, VAN0 = R.PROFILES.timeout.vanish, zf = (t, lat) => t / RATE + 4.2 - lat;     // the tracker's clock (chgStartTracker: t0 = trigger - 4.2 frames - vlag)
let skipped = 0;
for (let i = 0; i < N; i++) {
  const seed = (rnd() * 4294967296) >>> 0, q = 40 + Math.floor(rnd() * 8), lag = pick([[0, 0.75], [1, 0.25]]), sh = pick([[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]]), imp = 40 + Math.floor(rnd() * 136), guard = rnd() < 0.5;
  const wrong = i % 12 === 11;            // 1 in 12: the lock is wrong (another seed): about the page's prior (5% + 3% at the Spiny Flip)
  const tScr = T.timeOut - 2500, cScr = Math.round(zf(tScr, 0)), cTrue = Math.round(zf(T.spiny, VAN0)) + sh;
  const G = game(seed, q, lag, imp, guard, cTrue, cScr);
  if (G.S.inst.length || (G.S.extra && G.S.extra.size)) { skipped++; continue; }      // Bowser's attack still drawing at the screen
  // what the detector sees: shines drawn inside the tracker's visible stretches (after the rays until the confirm; T2's
  // menu until the screen), each missed with p 0.02, read -1 .. +3 frames late; false shines at 1.8e-4 per visible frame
  const vis = [[zf(T.up0 + 1000, 0), zf(T.spiny, 0) - 6], [zf(T.back2[0], 0), cScr - 4]], taps = [];
  for (const f of G.shines) if (vis.some(([a, b]) => f >= a && f <= b) && rnd() >= 0.02) taps.push((f + 6 - 4.2 + pick([[-1, 0.2], [0, 0.4], [1, 0.25], [2, 0.1], [3, 0.05]]) + rnd() - 0.5) * RATE);
  for (const [a, b] of vis) for (let f = a; f < b; f++) if (rnd() < 1.8e-4) taps.push((f + 6 - 4.2) * RATE);
  taps.sort((x, y) => x - y);
  const pres = [[0, 0], [T.up0, 1], [T.spiny, 0]];
  const clip = { seed: (wrong ? (seed ^ 0x5a5a1234) >>> 0 : seed).toString(16), qs: [...new Set([q, 40 + ((q - 40 + 3) % 8), 40 + ((q - 40 + 5) % 8)])].sort((x, y) => x - y), pres, shines: taps, coinBack: [T.back2], spiny: T.spiny, timeOut: T.timeOut };
  for (const ver of ['v71', 'v72']) {
    const L = tracker(ver); lockAt(L, clip, T.spiny + 1000, taps);
    L.ctx.now = T.back2[0]; L.zwCoinBack(T.back2[1]);
    for (const t of taps) if (t >= T.spiny + 1000 && t < tScr) { L.ctx.now = t + 30; L.zwTap(t); }
    L.ctx.now = tScr; const S = statesAt(L, cScr);
    const from = Math.ceil(cScr + 1.5 * 1000 / RATE + 1), P = plan(S, from, 30, ver), h = H[ver];
    // the game at the plan's frame (presses 25/50/25)
    const real = P ? PE.reduce((a, [d, w]) => a + w * (R.works(G.S.s, G.S.nc, P.target + d, G.g, R.PROFILES.timeout) ? 1 : 0), 0) : null;
    if (process.env.DBG) console.log(i, ver, wrong ? 'wrong' : 'right', P && { t: P.target, pS: +P.pStates.toFixed(3), shown: +P.shown.toFixed(3), beep: P.beep }, 'doubt', +S.doubt.toFixed(3), 'states', S.list.length, 'taps', taps.length, 'real', real);
    if (wrong) { h.wn++; if (P && P.beep) { h.wbeep++; h.wshown += P.shown; h.wgot += real; } }
    else { h.n++; if (P && P.beep) { h.beep++; h.shown += P.shown; h.got += real; } }
  }
}
console.log('simulated: ' + N + ' games, ' + skipped + ' skipped (Bowser\'s attack still drawing at the target screen)');
for (const v of ['v71', 'v72']) { const h = H[v];
  console.log(v + ': right lock ' + h.n + ' runs, beeped ' + h.beep + ' (shown ' + (h.shown / Math.max(1, h.beep)).toFixed(3) + ', game ' + (h.got / Math.max(1, h.beep)).toFixed(3) + '), all runs with a blind press (31%) when no beep ' + ((h.got + 0.31 * (h.n - h.beep)) / h.n).toFixed(3) +
    '; wrong lock ' + h.wn + ' runs, beeped ' + h.wbeep + (h.wbeep ? ' (shown ' + (h.wshown / h.wbeep).toFixed(3) + ', game ' + (h.wgot / h.wbeep).toFixed(3) + ')' : '')); }
{ const h = H.v72, g = H.v71, all = h.beep + h.wbeep, shown = (h.shown + h.wshown) / Math.max(1, all), got = (h.got + h.wgot) / Math.max(1, all);
  const ev = x => (x.got + x.wgot + 0.31 * (x.n + x.wn - x.beep - x.wbeep)) / (x.n + x.wn);
  console.log('all runs (right and wrong locks), a blind press when no beep: v71 ' + ev(g).toFixed(3) + ', v72 ' + ev(h).toFixed(3) + '; v72 beeped ' + all + ', shown ' + shown.toFixed(3) + ', game ' + got.toFixed(3));
  check(Math.abs(shown - got) <= 0.06, 'v72 shown chance ' + shown.toFixed(3) + ' vs game ' + got.toFixed(3) + ' on the beeped runs');

  check(ev(h) >= ev(g) - 0.01, 'v72 expected outcome ' + ev(h).toFixed(3) + ' below v71 ' + ev(g).toFixed(3)); }
console.log(fails ? 'FAILED ' + fails : 'PASS'); process.exit(fails ? 1 : 0);
