//@ Final Bowser phase 2, T1 -> T4 (and the carry to T6), live (charge_live/README.md, v74; fb2_route/README.md section 7).
//@ Inlined into page_template.html after fb2_live.js; //@ lines are dropped. Needs the page globals R, FRAME, $, num, slog,
//@ st, V, CHG, chgRate, beepAt, cancelBeeps, playBeeps, nBeeps, earliestPress, pressDist, PRESS_ERR, zwChoose, render,
//@ isRoute, RT, routeStep, setStep, fb2Patterns, FB2_P130, FB2_P220, the ZW_* constants and chgSearch.
/* ---------- Final Bowser phase 2, T1-T4: the aura Charge lock, Bowser's misses, and the carry into T6 ----------
 * The route: T1 Super Charge, Cloud Nine; T2 Super Charge, Lakilester Do Nothing; T3 Jammin' Jelly, Do Nothing; T4 Super
 * Charge, Do Nothing (the Draining Shockwave, blocked); T5 Peach Beam; T6 Super Charge, the popup A; T7 Power Bounce.
 * Bowser's star aura draws 16 rand_int(359) per 20 frames, so the Hallway's Charge model does not fit these Charges:
 * the profile 'fb1' (charge_live.js) scores the rays with the aura, the lightning and the coin as unknown extra draws
 * (kernel.c fb1score: the best monotone path), then fits the fight's 20-frame aura pattern, the lightning pattern and
 * the first coin (fb1struct) and keeps every fit within FB14_TOL of the best. Each fit, with every lightning phase pair
 * behind its pattern and console lag 0 / 1 after the rays, is a state of the tracker below.
 * From the lock the turn is a closed model (fb2_route/t14model.py, emulator logs exact to the dodge test 64 / 64, and
 * through the next menu after every miss): per frame the bolts, the script draws (the Charge rays' creations on Mario's
 * confirm M + 13 / + 16, the Jelly's sparkles on M + 118, Cloud Nine's puffs on P + 200 .. 209, Bowser's AI on P + 13
 * after Do Nothing / P + 332 after Cloud Nine, the dodge test on AI + 52 / 62 / 55 / 72 by attack, the wave's own draws),
 * the coin, the aura, the rays' respawns, the wave's particles, the step. The lever is the partner's confirm P (the
 * runner waits on that screen): Bowser misses when the test is < 50 (Cloud Nine); on T4 the wave must also come.
 * The coin on every menu weighs the states (the v72 tracker's likelihood, ZW_*); each later Charge (T2, T4) is locked
 * again and checked against the carried states. The states are carried through T4 into T5's menu up to the Peach Beam
 * confirm; the beam itself is not modelled, but it takes 8654-9351 more random numbers than frames to T6's Charge
 * (fb2_route/t5_steps.py, 120 emulator runs), so the T6 Charge is searched only on that stretch of the carried stream
 * (charge_live.js chgSearch opts.cands) instead of all 2^32 seeds: no slow fresh lock at T6. */
const FB14_TOL = 0.008, FB14_SIG = 0.004, FB14_COMBOS = 1200, FB14_MAXH = 8000, FB14_LAGS = [[0, 0.75], [1, 0.25]];
const FB14_DELTA = { slam: 52, claw: 62, fire: 55, wave: 72 }, FB14_AIAFTER = { cn: 332, nothing: 13 }, FB14_JELLY = 118;
const FB14_WAVE_POST = (() => { const o = { 66: 1, 68: 2, 70: 3, 72: 4, 74: 5, 76: 6, 78: 7, 80: 8, 126: 8, 128: 7, 130: 6, 132: 5, 134: 4, 136: 3, 138: 2, 140: 1 }; for (let d = 82; d <= 124; d += 2) o[d] = 9; return o; })();
// blind chances per lever frame (fb2_route/README.md section 3: route_build miss strings and the 20000-window study)
const FB14_BLIND = { 1: 0.495, 2: 0.495, 3: 0.495, 4: 0.39 };
// the Peach Beam confirm -> the T6 Charge's rays frame 0: random numbers drawn = frames + this (t5_steps.py: Close Call
// 8654-8764, Bowser's hit 9116-9351; with margin for lag frames)
const FB14_T5 = [8540, 9420];
// the bar hiding after a confirm: the first picture without it shows confirm + 2 (Glide64 renders of the Charge and the
// Jelly, fb2_route/t14_log.py with SHOTS; the Peach Beam assumed the same); read to +-1 frame (FB14_JSHIFTS)
// the lever's screen: the first picture without its box shows the confirm + 1 (Cloud Nine's target, the マリオ name box) /
// + 2 (Lakilester's Strategies panel) in the same renders (the page's VAN, from console clips of other fights, says 2 / 3)
const FB14_VAN = { M: 1, S: 2 };
const FB14_HIDE = { jelly: 2, peach: 2 }, FB14_JSHIFTS = [[-1, 0.25], [0, 0.5], [1, 0.25]];
var FB14 = { on: false };
function fb14Reset(why) { Object.assign(FB14, { on: false, why: why || null, states: [], t0: null, rate: null, taps: [], vis: [], visFrom: null, turn: 0, M: {}, P: {}, plan: null, lockN: 0, log: [], pb: null, t6: null, hideWatch: null, doubt: 0, bg: 0, p4t: null, pend: [], pT: {}, charges: [], inputs: [] }); }
fb14Reset();
/* ---- the random numbers (fast, no arrays) ---- */
let FBV = 0;
const fbAdv = s => (Math.imul(s, 0x5D588B65) + 1) >>> 0;
function fbRi(s, mx) {
  const m = mx === 1 ? 1000 : mx === 100 ? 1009 : mx, d = Math.floor(0xFFFFFFFF / (m + 1)) || 1; let v;
  do { s = fbAdv(s); v = Math.floor(s / d); } while (v > m);
  FBV = mx === 1 ? (v >= 501 ? 1 : 0) : mx === 100 ? Math.floor(v / 10) : v; return s;
}
const fbBolts = (f, ph) => { const m1 = (f + ph[0]) % 130, m2 = (f + ph[1]) % 220; return (m1 === 78 || m1 === 83 || m1 === 113 || m1 === 118 ? 1 : 0) + (m2 === 18 || m2 === 78 || m2 === 88 || m2 === 178 ? 1 : 0); };
/* ---- one state: { s, nc, f (the next logic frame to run), c (aura counts by f mod 20), ph (lightning phases, absolute,
 * 0 <= ph), l (console lag: logic frame = clock frame - l), w, resp (ray respawns, a 64-frame ring), ev (script events,
 * sorted by frame), wv (the frame of Bowser's AI when it chose the wave), prev (Bowser's last attack), out (per turn:
 * attack, test value, miss, ok), sh (logic frames of the predicted shines), from (the state's first frame) } ---- */
function fbClone(S) { return { mk: S.mk, s: S.s, nc: S.nc, f: S.f, c: S.c, ph: S.ph, l: S.l, w: S.w, resp: S.resp.slice(), ev: S.ev.slice(), wv: S.wv, prev: S.prev, out: Object.assign({}, S.out), sh: S.sh.slice(), from: S.from, key: S.key, lw: S.lw, err: S.err, tag: S.tag }; }
function fbNew(o) { return Object.assign({ resp: new Uint8Array(64), ev: [], wv: -1e9, prev: null, out: {}, sh: [], lw: 1, err: 0 }, o); }
function fbEv(S, e) { let i = S.ev.length; while (i > 0 && S.ev[i - 1].f > e.f) i--; S.ev.splice(i, 0, e); }
const mod20 = f => ((f % 20) + 20) % 20;
/* run frame S.f */
function fbStep(S) {
  const f = S.f; let s = S.s;
  const m1 = (f + S.ph[0]) % 130, m2 = (f + S.ph[1]) % 220;
  if (m1 === 78 || m1 === 83 || m1 === 113 || m1 === 118) s = fbRi(s, 359);
  if (m2 === 18 || m2 === 78 || m2 === 88 || m2 === 178) s = fbRi(s, 359);
  while (S.ev.length && S.ev[0].f <= f) {
    const e = S.ev.shift(); if (e.f !== f) continue;
    if (e.k === 'chg') { s = fbRi(s, 360); for (let i = 0; i < 10; i++) { s = fbRi(s, 10); s = fbRi(s, 10); for (let n = f + 9 + FBV; n < f + 45; n += 10) S.resp[n & 63]++; } }
    else if (e.k === 'jelly') { for (let i = 0; i < 10; i++) { s = fbRi(s, 359); s = fbRi(s, 10); s = fbRi(s, 10); } }
    else if (e.k === 'puff') { s = fbRi(s, 40); s = fbRi(s, 30); }
    else if (e.k === 'ai') {
      let atk = null;
      if (e.t4) { s = fbRi(s, 100); if (FBV < 75) atk = 'wave'; else { s = fbRi(s, 110); if (FBV < 20) atk = 'wave'; } }
      if (!atk) { s = fbRi(s, 80); if (FBV < 20 && S.prev !== 'slam') atk = 'slam'; else { s = fbRi(s, 60); atk = FBV < 20 && S.prev !== 'claw' ? 'claw' : 'fire'; } }
      S.out[e.turn] = { atk, ai: f }; S.prev = atk; fbEv(S, { k: 'test', f: f + FB14_DELTA[atk], turn: e.turn });
      if (atk === 'wave') S.wv = f;
    }
    else if (e.k === 'test') { s = fbRi(s, 100); const o = S.out[e.turn]; o.v = FBV; o.miss = FBV < 50; o.ok = o.miss && (e.turn !== 4 || o.atk === 'wave'); }
  }
  const dw = f - S.wv;
  if (dw === 29) s = fbRi(s, 7); else if (dw === 76) for (let i = 0; i < 8; i++) s = fbRi(s, 359);
  if (f === S.nc) { s = fbRi(s, 100); if (FBV >= 70) S.sh.push(f); S.nc = f + (FBV >= 70 ? 48 : 24); }
  for (let i = S.c[mod20(f)]; i; i--) s = fbRi(s, 359);
  const r = S.resp[f & 63]; if (r) { for (let i = r; i; i--) s = fbRi(s, 359); S.resp[f & 63] = 0; }
  if (dw > 0 && dw <= 140) { const k = FB14_WAVE_POST[dw] || 0; for (let i = 0; i < k; i++) { s = fbRi(s, 359); s = fbRi(s, 359); s = fbRi(s, 10); s = fbRi(s, 15); s = fbRi(s, 15); } }
  S.s = fbRi(s, 1); S.f = f + 1;
}
function fbRun(S, to) { while (S.f < to) fbStep(S); return S; }
/* ---- the clock: logic frame 0 = T1's Mario confirm; FB14.t0 = the time the picture of frame 0 would show ---- */
const fbRate = () => FB14.rate || (typeof chgRate === 'function' ? chgRate() : FRAME);
const fbPic = t => (t - FB14.t0) / fbRate();
// the press for clock frame F: as Time Out's and the FB2 popup's (1.7 frames before that frame's picture, the runner's
// beep offset, the capture delay)
const fbPressT = F => FB14.t0 + (F - 1.7 + num('off')) * fbRate() - num('vlag');
/* ---- the route: the Final Bowser steps (page_template.html ENDGAME) ---- */
const fb14Step = () => { const s = isRoute() && RT()[routeStep]; return s && s.fb14 ? s : null; };
/* ---- the lock (a Charge read with the aura profile): hypotheses -> states ---- */
function fb14Lock(res) {
  const H = res.fb1 && res.fb1.hyps, stp = fb14Step(), turn = FB14.trigTurn || (stp ? stp.fb14 : 1); FB14.trigTurn = null;
  if (!H || !H.hy.length) { FB14.why = 'no hypotheses from the rays'; fb14Show(); return; }
  const rate = chgRate(), P = fb2Patterns(), first = !FB14.on || FB14.t0 == null;
  FB14.menuT = CHG.menuSince || null;      // the bar up in Mario's menu before this Charge (charge_live.js chgFrame)
  const trigT = res.trigT != null ? res.trigT : CHG.trig.t;     // (the reader may have been reset for the next Charge meanwhile)
  if (first) { FB14.rate = rate; FB14.t0 = trigT - 16 * rate; }
  const M = first ? 0 : Math.round((trigT - FB14.t0) / fbRate() - 16) + (res.joint && res.joint.dM ? res.joint.dM : 0);   // (fb14Joint: the frame the Charges' rays agree on)
  FB14.t0 = trigT - (M + 16) * fbRate();            // the burst fixes the clock again (drift)
  let fresh = []; const seen = new Set();
  // the menu's coin before the Charge: back to 1 s after the bar came up for that menu (at most 15 s)
  const menuF = FB14.menuT != null ? Math.min(M, Math.max(M - 450, Math.ceil(fbPic(FB14.menuT) + 30))) : M;
  const back0 = (x0, F0, q, c, pa) => { const r = fbBackShines(x0, F0, q, c, pa, menuF); return { ok: r.ok, sh: r.sh.sort((a, b) => a - b), from: Math.min(menuF, F0) }; };
  // the fits x their aura splits, the likeliest FB14_COMBOS by weight (0.8% of the best keeps thousands of fits)
  const combos = [];
  const J = res.joint && res.joint.keep && res.joint.keep.size ? res.joint : null;
  // with the joint patterns: every kept pattern on its share of this Charge's best fits (a pattern the coin may still
  // prefer must not be crowded out by the joint score's favourite)
  const hyJ = J ? H.hy.filter(h => Math.abs(h.esc - h.sc) <= 2).sort((x, y) => y.sc - x.sc).slice(0, Math.max(4, Math.ceil(FB14_COMBOS / J.keep.size))) : null;
  if (J) for (const h of hyJ) { const sig = Math.max(1, FB14_SIG * H.best), wf = Math.exp((h.sc - H.best) / sig);
    for (const [k, d] of J.keep) { const aura = new Array(20); for (let j = 0; j < 20; j++) aura[j] = +k[mod20(M + 13 + j)]; combos.push([h, { aura, w: wf * Math.exp(d / Math.max(1, FB14_JSIG * J.tot)) }]); } }
  for (const h of (J ? [] : H.hy)) {
    if (Math.abs(h.esc - h.sc) > 2) continue;              // the second coin assumed by the fit is not the one the seed draws
    for (const AV of fbAuraVariants(h, H.best)) combos.push([h, AV]);
  }
  combos.sort((x, y) => y[1].w - x[1].w); const wTop = combos.length ? combos[0][1].w : 1;
  for (const [h, AV0] of (J ? combos : combos.slice(0, FB14_COMBOS))) {
    { const AV = { aura: AV0.aura, w: AV0.w / wTop };
    const c = new Uint8Array(20); for (let j = 0; j < 20; j++) c[mod20(M + 13 + j)] = AV.aura[j];
    for (const ph of P.list[h.p].ph) {
      const pa = [(((ph[0] - M) % 130) + 130) % 130, (((ph[1] - M) % 220) + 220) % 220];
      for (const [l, wl] of FB14_LAGS) {
        const key = h.s48 + ':' + h.nc48 + ':' + c.join('') + ':' + pa[0] + ':' + pa[1] + ':' + l; if (seen.has(key)) continue; seen.add(key);
        const F0 = M + 13; let x0 = Math.imul(((H.a >>> 0) - 1) >>> 0, 0x6A76AE6D) >>> 0;   // the seed before A's base-angle draw
        for (let i = fbBolts(F0, pa); i; i--) x0 = Math.imul((x0 - 1) >>> 0, 0x6A76AE6D) >>> 0;   // before frame 0's bolts
        const B = back0(x0, F0, F0 + h.q, c, pa);
        fresh.push(fbNew({ s: h.s48 >>> 0, nc: M + 13 + h.nc48, f: M + 61, c, ph: pa, l, w: wl * AV.w * (B.ok ? 1 : 1e-3), from: B.from, sh: B.sh, key, tag: turn }));
      }
    }
    }
  }
  // the aura pattern is the fight's: a fresh fit after an earlier lock keeps only the patterns the carried states still
  // hold (when any is among them)
  if (!J && !first && FB14.states.length) { const cs = new Set(FB14.states.map(S => S.c.join(''))), f2 = fresh.filter(S => cs.has(S.c.join(''))); if (f2.length) fresh = f2; slog('fb14AuraKeep', { turn, fits: fresh.length, of: seen.size }); }
  let keep = fresh, how = 'fresh';
  if (!first && FB14.states.length) {      // the carried states: those that drew these very rays
    const a = H.a >>> 0, match = [];
    const ends = new Set(H.hy.map(h => (h.s48 >>> 0) + ':' + (M + 13 + h.nc48)));
    for (const S of FB14.states) {
      const T = fbClone(S), m = (S.mk != null ? S.mk : M) - S.l; if (T.f > m + 13) continue;
      fbRun(T, m + 13); let x = T.s; for (let i = fbBolts(m + 13, T.ph); i; i--) x = fbRi(x, 359);
      if ((fbAdv(x) >>> 0) !== a) continue;
      fbRun(T, m + 61); if (!ends.has((T.s >>> 0) + ':' + (T.nc - m + M))) continue;
      T.sh = []; T.from = T.f; match.push(T);
    }
    if (match.length) { keep = match; how = 'carried';
      const by = {}; for (const T of match) by[T.mk] = (by[T.mk] || 0) + T.w; const Mt = +Object.keys(by).sort((x, y) => by[y] - by[x])[0];
      if (Mt !== M && Number.isFinite(Mt)) { slog('fb14ClockFix', { turn, M, Mt }); FB14.t0 = trigT - (Mt + 16) * fbRate(); }
    }
    slog('fb14Check', { turn, M, carried: FB14.states.length, matched: match.length, fresh: fresh.length });
  }
  const sum = keep.reduce((x, S) => x + S.w, 0); keep.forEach(S => { S.w /= sum; S.lw = 1; S.err = 0; });
  // the menu's coin before the Charge weighs the fits now (fbBackShines), before any are dropped for the cap: with the
  // weights all equal an even sample would lose the true one (T2 render: 1605 fits x their lightning phases x 2 lags)
  if (window.__fb14dbg) { const T = window.__fb14truth; window.__fb14dbg.push({ pre: true, turn, M, n: keep.length, truth: T ? keep.filter(S => S.s === T.s && (T.nc == null || S.nc === T.nc)).map(S => ({ c: Array.from(S.c).join(''), ph: S.ph, l: S.l, w: S.w, sh: S.sh })) : null }); }
  FB14.states = keep; let n0 = keep.length;
  if (how === 'fresh' && keep.length > 1) { const Wg = fb14Weigh(M + 61); if (Wg.list.length) keep = Wg.list; }
  keep.sort((x, y) => y.w * y.lw - x.w * x.lw);
  if (keep.length > FB14_MAXH) { const top = keep[0].w * keep[0].lw, eq = keep.filter(S => S.w * S.lw >= top * 0.999);
    keep = eq.length >= FB14_MAXH ? eq.filter((S, i) => i % Math.ceil(eq.length / FB14_MAXH) === 0) : keep.slice(0, FB14_MAXH); }
  FB14.states = keep; FB14.n0 = n0;
  Object.assign(FB14, { on: true, why: null, turn, lockN: FB14.lockN + 1, plan: null, bg: ZW_BG0 / (1 - ZW_BG0), bgFrom: Math.min(M + 61, menuF), how });
  FB14.M[turn] = M;
  if (res.joint && res.joint.cur) { res.joint.cur.M = M; FB14.charges = (FB14.charges || []).filter(c => c.M !== M).concat([res.joint.cur]).slice(-2); }
  // confirms the page saw before this lock landed (a slow lock): their frames from the clock the lock has just fixed
  // the inputs of this turn the page saw before this lock landed (a slow lock: the partner's confirm, T3's Jelly), onto
  // fresh states (carried ones have them already)
  if (how === 'fresh') for (const x of (FB14.inputs || []).map(x => Object.assign({}, x, { F: x.t != null ? Math.round(fbPic(x.t) - x.off) : x.F })).filter(x => x.F > M + 13 && x.turn >= turn).sort((a, b) => a.F - b.F)) { fb14Input(x.kind, x.F, x.turn, x.shifts, x.t, x.off); slog('fb14Replay', { kind: x.kind, F: x.F, turn: x.turn }); }
  const pend = (FB14.pend || []).filter(x => x.turn >= turn); FB14.pend = [];
  for (const x of pend) { const c = fbPic(x.tObs) - (FB14_VAN[x.cat] || 2) - num('pfix'), F = Math.round(c); FB14.P[x.turn] = F; fb14Input(fb14Kind(x.turn), F, x.turn, FB14_SHIFTS, x.tObs, (FB14_VAN[x.cat] || 2) + num('pfix')); slog('fb14LateConfirm', { turn: x.turn, F }); }
  if (window.__fb14dbg) { const T = window.__fb14truth; window.__fb14dbg.push({ turn, M, how, n: FB14.states.length, truth: T ? FB14.states.filter(S => S.s === T.s && (T.nc == null || S.nc === T.nc)).map(S => ({ c: Array.from(S.c).join(''), ph: S.ph, l: S.l, w: S.w, lw: S.lw })) : null }); }
  if (false) window.__fb14dbg.push({ turn, M, how, states: FB14.states.slice(0, 3000).map(S => ({ s: S.s >>> 0, nc: S.nc, f: S.f, l: S.l, c: Array.from(S.c).join(''), ph: S.ph, w: S.w, lw: S.lw, sh: S.sh })) });
  slog('fb14Lock', { turn, M, how, hyps: H.hy.length, n: H.n, fits: FB14.n0, states: FB14.states.length, best: Math.round(H.best), a: (H.a >>> 0).toString(16) });
  fb14Show();
}
/* The aura's split the rays cannot see: where a residue's frames have only faded or offscreen respawns (or none), the
 * counts of neighbouring residues trade with no change in the score, and the fit returns just one split (the end-to-end
 * render 1234abcd: '10110101201010201040' for the true '01110101021010201310'). The kernel lists every split of a fit
 * within the lock's tolerance (fb1alts); they are weighed by a star's chance to restart on a given frame (16 stars, 1/20
 * each: binomial) and the likeliest FB14_AV kept, each with its prior share. */
const FB14_AV = 48, FB14_BIN = [0.440, 0.371, 0.146, 0.036, 0.0061];
// each split weighed by its prior and by its score: exp((score - best) / (FB14_SIG x best)). The true fit scores within a
// few tenths of a percent of the best but not always inside 0.2% (render e2e 1234abcd: 7316 against 7354, the noise of
// one frame's respawns is ~200), so the lock keeps every fit within FB14_TOL (0.8%) and lets the score weigh them.
function fbAuraVariants(h, best) {
  const sig = Math.max(1, FB14_SIG * best), L = (h.alts && h.alts.length ? h.alts.map((aura, i) => [aura, h.altSc[i]]) : [[h.aura, h.sc]])
    .map(([aura, sc]) => ({ aura, w: aura.reduce((x, c) => x * (FB14_BIN[c] || 1e-4), 1) * Math.exp((sc - best) / sig) }));
  L.sort((x, y) => y.w - x.w); return L.slice(0, FB14_AV);
}
/* The coin before the Charge (Mario's menu): from a hypothesis' seed at the rays' frame 0 the earlier coin draws follow
 * backwards, as chgQBack does on the Hallway, now with the aura's and the lightning's draws of each frame known from the
 * hypothesis: the coin before the first one (q) came 24 frames earlier after a value < 70, 48 after one >= 70, and only
 * one of the two fits the stream (both: stop there). The rays leave the aura's split between neighbouring frames and the
 * first coin's frame partly open (T2 render 9e3779b9: 1600 states within 0.2%, the true coin frame in a minority); the
 * shines of the menu before the Charge then tell them apart. Returns the shine frames from fromF on, and whether the
 * walk was consistent. */
function fbBackShines(sR0, F0, q, c, ph, fromF) {
  const back = (x, n) => { for (let i = 0; i < n; i++) x = Math.imul((x - 1) >>> 0, 0x6A76AE6D) >>> 0; return x; };
  const per = f => fbBolts(f, ph) + c[mod20(f)] + 1;     // a menu frame's draws besides the coin
  let X = sR0, f = F0, nc = q, isR0 = true; const sh = [];
  for (let k = 0; k < 40; k++) {
    let found = null, n = 0;
    for (const gap of [24, 48]) {
      const f1 = nc - gap; if (f1 >= F0 || f1 < fromF) continue;
      // draws from just before the coin on f1 to X: the coin, f1's aura and step, the frames between, and (X just
      // before a coin draw) that frame's bolts
      let d = 1 + c[mod20(f1)] + 1; for (let g = f1 + 1; g < f; g++) d += per(g); if (!isR0) d += fbBolts(f, ph);
      const Y = back(X, d); fbRi(Y, 100); if ((FBV >= 70) === (gap === 48)) { found = [f1, Y, FBV]; n++; }
    }
    if (n !== 1) return { sh, ok: n === 2 || nc - 24 < fromF };
    f = found[0]; X = found[1]; nc = f; isR0 = false; if (found[2] >= 70) sh.push(f);
  }
  return { sh, ok: true };
}
/* a Charge's trigger with the tracker on (T2, T4): the carried states get that Charge's rays (their creations), so the
 * new lock can be checked against them; T3's Jelly and the partner confirms come in the same way */
function fb14Input(kind, Fc, turn, shifts, tRef, off) {
  if (kind !== 'chg') { FB14.inputs = (FB14.inputs || []).filter(x => !(x.kind === kind && x.turn === turn)).concat([{ kind, F: Fc, turn, shifts, t: tRef, off }]); }   // (replayed onto a lock that lands later)
  if (!FB14.on) return;
  const out = [];
  for (const S of FB14.states) for (const [d, wd] of (shifts || [[0, 1]])) {
    const F = Fc + d - S.l; if (S.f > F + (kind === 'chg' ? 13 : kind === 'jelly' ? FB14_JELLY : 13)) continue;   // too late for this state (should not happen: the horizon trails the inputs)
    const T = shifts ? fbClone(S) : S; T.w = S.w * wd; if (kind === 'chg') T.mk = Fc + d;
    fbInputEv(T, kind, F, turn);
    out.push(T);
  }
  if (shifts) FB14.states = fb14Cap(out);
  slog('fb14Input', { kind, F: Fc, turn, states: FB14.states.length });
}
function fbInputEv(T, kind, F, turn) {
  if (kind === 'chg') { fbEv(T, { k: 'chg', f: F + 13 }); fbEv(T, { k: 'chg', f: F + 16 }); }
  else if (kind === 'jelly') fbEv(T, { k: 'jelly', f: F + FB14_JELLY });
  else if (kind === 'cn') { for (let i = 200; i < 210; i++) fbEv(T, { k: 'puff', f: F + i }); fbEv(T, { k: 'ai', f: F + FB14_AIAFTER.cn, turn, t4: false }); }
  else if (kind === 'nothing') fbEv(T, { k: 'ai', f: F + FB14_AIAFTER.nothing, turn, t4: turn === 4 });
}
function fb14Cap(L) {
  const by = new Map(); for (const S of L) { const k = S.s + ':' + S.nc + ':' + S.f + ':' + S.l + ':' + S.ph.join(',') + ':' + S.c.join('') + ':' + S.wv + ':' + S.prev + ':' + S.resp.join('') + ':' + S.ev.map(e => e.k + e.f).join(','); const o = by.get(k); if (o) o.w += S.w; else by.set(k, S); }
  const A = [...by.values()].sort((x, y) => y.w - x.w); return A.length > FB14_MAXH ? A.slice(0, FB14_MAXH) : A;
}
/* ---- the coin: shines (clock frame of the draw) and the stretches the coin was watched ---- */
// the coin is kept in page time (ms) and read on the clock when the states are weighed: a lock re-anchors the clock, and
// the shines of the menu the lock was searched in still count
function fb14Tap(t) { FB14.taps.push(t); if (FB14.taps.length > 400) FB14.taps.shift(); }
function fb14Frame(t, present) {
  FB14.lastT = t;
  if (FB14.pendChg && !['armed', 'capture'].includes(CHG.state)) { const { M, turn } = FB14.pendChg; FB14.pendChg = null; fb14Advance(Math.min(fb14Horizon(performance.now()), M + 11)); fb14Input('chg', M, turn, [[-1, 0.25], [0, 0.5], [1, 0.25]]); }
  if (FB14.rearm && !FB14.refining && ['locked', 'nolock', 'failed'].includes(CHG.state)) { const n = fb14Step(); if (n && n.fb14 === FB14.rearm && n.chg === 'fb1') { slog('fb14ReaderRearmed', { turn: n.fb14 }); chgReset(); } FB14.rearm = null; }
  if (!FB14.on && !fb14Step()) return;
  if (present && FB14.visFrom == null) FB14.visFrom = t;
  if (!present && FB14.visFrom != null) { FB14.vis.push([FB14.visFrom, t]); if (FB14.vis.length > 200) FB14.vis.shift(); FB14.visFrom = null; }
  fb14HideWatch(t, present);
  if (FB14.on && (!FB14.tickT || t - FB14.tickT > 250)) { FB14.tickT = t; fb14Tick(t); }
}
/* the bar hiding: T3's Jelly confirm (Mario's turn of T3), T5's Peach Beam confirm (after T4's Do Nothing) */
function fb14HideWatch(t, present) {
  const W = FB14.hideWatch || (FB14.hideWatch = { up: 0, gone: 0 });
  if (present) { if (!W.up) W.up = t; W.gone = 0; return; }
  if (!W.gone) W.gone = t; if (t - W.gone < 8 * FRAME) return;              // gone for 8 frames: not a flicker
  if (!W.up) return; const upMs = W.gone - W.up; W.up = 0; t = W.gone; if (upMs < 600 || FB14.t0 == null) return;
  const stp = fb14Step(), F = fbPic(t);
  if (stp && stp.fb14 === 3 && FB14.M[3] == null && FB14.pT && FB14.pT[2] != null && t - FB14.pT[2] > 3000) { FB14.M[3] = Math.round(F - FB14_HIDE.jelly); fb14Input('jelly', FB14.M[3], 3, FB14_JSHIFTS, t, FB14_HIDE.jelly); slog('fb14Jelly', { M: FB14.M[3] }); }
  else if (FB14.p4t != null && !FB14.pb && t - FB14.p4t > 5000) { FB14.pb = { F: Math.round(F - FB14_HIDE.peach), t }; slog('fb14Peach', { F: FB14.pb.F }); if (!['search', 'maps', 'idle'].includes(CHG.state)) chgReset(); fb14Peach(); }   // nothing before the T6 menu is the T6 Charge
}
/* the states' weights from the coin since their lock (as fb2Prune / zwUpdate): a seen shine a state has, a predicted
 * shine inside a watched stretch that was not seen (missed), a seen shine it does not have (false) */
function fb14Weigh(h) {
  // a stretch counts from 1 s after the bar came up to 4 frames before it went (a shine drawn later never showed)
  const vis = FB14.vis.concat(FB14.visFrom != null ? [[FB14.visFrom, null]] : []).map(([a, b]) => [fbPic(a) + 30, Math.min(b == null ? h - 4 : fbPic(b) - 4, h - 4)]).filter(([a, b]) => b > a);
  const tapF = FB14.taps.map(t => fbPic(t) - 4.8);
  // the match window: -2 .. +4.5 frames (the capture shows a flash up to ~3 frames after the console calibration in the
  // emulator renders, and a dropped picture reads it later still; v72's Duplighost tracker takes 4)
  const Wd = 6.5 * (ZW_RHO + ZW_FALSE), Lm = (1 - ZW_PMISS) / Wd, Lf = ZW_FALSE / (ZW_RHO + ZW_FALSE), near = (x, f) => x - f >= -2 && x - f <= 4.5;
  let mx = 0, tot0 = 0; const out = [];
  for (const S of FB14.states) {
    tot0 += S.w; const sh = S.sh.map(f => f + S.l), taps = tapF.filter(x => x < h && x >= S.from + S.l); let lw = 1, err = 0;
    for (const x of taps) if (sh.some(f => near(x, f))) lw *= Lm; else { lw *= Lf; err++; }
    for (const f of sh) if (f < h - 6 && vis.some(([a, b]) => f >= a && f <= b) && !taps.some(x => near(x, f))) { lw *= ZW_PMISS; err++; }
    S.lw = lw; S.err = err; if (err > ZW_MAXERR) continue; out.push(S); mx = Math.max(mx, S.w * lw);
  }
  const keep = out.filter(S => S.w * S.lw >= mx * ZW_CUT), sum = keep.reduce((a, S) => a + S.w * S.lw, 0);
  if (!keep.length && FB14.states.length && !FB14.allOutLogged) { FB14.allOutLogged = true; slog('fb14AllOut', { h, taps: tapF.filter(x => x < h).map(x => +x.toFixed(1)).slice(-20), vis: vis.map(v => v.map(x => +x.toFixed(1))).slice(-8), sample: FB14.states.slice(0, 4).map(S => ({ f: S.f, l: S.l, from: S.from, sh: S.sh.slice(-12), err: S.err })) }); }
  let nVis = 0; for (const [a, b] of vis) nVis += Math.max(0, b - Math.max(a, FB14.bgFrom || 0));
  const bg = tot0 * FB14.bg * Math.exp(-ZW_RHO * nVis);
  return { list: keep, doubt: keep.length ? bg / (bg + sum) : 1, sum };
}
/* every state to the horizon (frames whose shines have had time to be read) */
// (from the newest picture's time: the same as now live; a capture that lags must not move the states past inputs not yet seen)
function fb14Horizon(now) { return Math.floor(fbPic(Math.min(now, FB14.lastT || now) - num('vlag')) - 10); }
function fb14Advance(h) { for (const S of FB14.states) fbRun(S, h - S.l); }
/* ---- the plan: the partner's confirm frame (the lever) ---- */
// share[F - a] = the weighted share of the states for which a confirm on clock frame F gives Bowser's miss (T4: the wave,
// missed). The states are stepped once along the window; each frame's outcome is simulated from its own state.
function fb14Share(L, a, b, turn, kind) {
  const sh = new Float64Array(Math.max(0, b - a + 1)), tot = L.reduce((x, S) => x + S.w * S.lw, 0) || 1, lead = kind === 'cn' ? 200 : 0;
  for (const S0 of L) {
    // the frames before the first event of a confirm on F draw the same whatever F is: one state is stepped along them
    // and each F's outcome is simulated from its own copy (T1: from F + 200, the first puff)
    const B = fbClone(S0); fbRun(B, a - B.l + lead); const wt = S0.w * S0.lw / tot;
    for (let F = a; F <= b; F++) {
      const T = fbClone(B), P = F - T.l; fbInputEv(T, kind, P, turn);
      const end = P + (kind === 'cn' ? FB14_AIAFTER.cn : FB14_AIAFTER.nothing) + 80;
      while (T.f < end && !(T.out[turn] && T.out[turn].v != null)) fbStep(T);
      if (T.out[turn] && T.out[turn].ok) sh[F - a] += wt;
      fbStep(B);
    }
  }
  return sh;
}
function fb14Sample(L, n) { if (L.length <= n) return L; const k = Math.ceil(L.length / n); return L.filter((S, i) => i % k === 0); }
function fb14Kind(turn) { return turn === 1 ? 'cn' : 'nothing'; }
function fb14Blind(turn) { return FB14_BLIND[turn] || 0.5; }
function fb14Goal(turn) { return turn === 4 ? 'the wave, and it misses Mario' : 'Bowser misses'; }
function fb14BlindText(turn) { return 'play it blind: ' + (turn === 1 ? 'Cloud Nine' : 'Do Nothing') + ' whenever you like (' + fb14Goal(turn) + ' about ' + Math.round(100 * fb14Blind(turn)) + '%; T1-T4 all blind about 5%)'; }
function fb14Plan(cAt) {      // cAt (tests): plan as if the screen showed on clock frame cAt, no beeps
  const stp = fb14Step(), turn = stp && stp.fb14;
  if (!turn || stp.fb14role !== 'lever') return false;
  if (!FB14.on) { st.msg = 'No Final Bowser lock: ' + fb14BlindText(turn) + '.'; FB14.plan = { none: 'no lock', turn }; fb14Show(); if (cAt == null) render(); return true; }
  const now = performance.now(), h = cAt != null ? cAt : fb14Horizon(now); fb14Advance(h);
  const Wg = fb14Weigh(h); FB14.doubt = Wg.doubt;
  if (!Wg.list.length || Wg.doubt >= 0.5) { st.msg = 'No edge: the coin no longer fits the Final Bowser lock (' + Math.round(100 * Wg.doubt) + '% none of the states is the game\'s). ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; FB14.plan = { none: 'doubt', turn, doubt: Wg.doubt }; slog('fb14NoEdge', { turn, doubt: +Wg.doubt.toFixed(3), states: Wg.list.length }); fb14Show(); if (cAt == null) { cancelBeeps(); render(); } return true; }
  const rate = fbRate(), W = Math.max(0, Math.round(num('zwwin') * 1000 / rate));
  let from = cAt != null ? Math.ceil(cAt + num('lead') * 1000 / rate + 1) : Math.max(h + 1, Math.ceil(fbPic(now) + 1));
  if (cAt == null) for (let i = 0; i < 600 && fbPressT(from) < earliestPress(now); i++) from++;
  const L = fb14Sample(Wg.list, 150), PD = cAt != null ? PRESS_ERR : pressDist(), D = Math.max(...PD.map(x => Math.abs(x[0]))), X = 10;
  const t1 = performance.now(), share = fb14Share(L, from - D, from + W + X + D, turn, fb14Kind(turn)), ms = Math.round(performance.now() - t1);
  const prof = { id: 'fb14', share: (a, b) => (a === from - D ? share : share.slice(a - (from - D), b - (from - D) + 1)) };
  const C = zwChoose(L, from, W, PD, prof, { d: Wg.doubt, b3: fb14Blind(turn), b4: 0 });
  if (C.none) { const pl = { none: C.none, turn, best: C.p }; FB14.plan = pl; if (cAt != null) return pl;
    st.msg = 'No edge: ' + Wg.list.length + ' possible states and no frame in the next ' + num('zwwin') + ' s works for enough of them (best ' + Math.round(100 * (C.p || 0)) + '%). ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; slog('fb14NoEdge', { turn, best: C.p }); cancelBeeps(); fb14Show(); render(); return true; }
  const pl = { turn, target: C.target, p: C.p, pStates: C.pStates, doubt: +Wg.doubt.toFixed(3), states: Wg.list.length, ms, from, W, w: C.w, tPress: fbPressT(C.target), blind: fb14Blind(turn) };
  FB14.plan = pl; if (cAt != null) return pl;
  cancelBeeps(); playBeeps(pl.tPress);
  const tLast = FB14.t0 - 1.2 * rate - num('vlag');      // pressTime(tLast, rate, F) = fbPressT(F)
  const a = C.a, tab = []; for (let F = from - 30; F <= from + W + 30; F++) tab.push(F >= a && F <= C.b ? C.share[F - a] >= 0.5 : false);
  st.plan = { tMade: now, w: C.w, target: C.target, tPress: pl.tPress, tLast, rate, carried: true, from, to: from + W, first: from - 30, prof: 'fb14', tab, tab4: null, type: C.type, beeps: nBeeps(),
    mix: { p: C.p, pStates: C.pStates, doubt: pl.doubt, groups: Wg.list.length, zw: true, fb14: turn }, PD, zwAbs: C.target, fb14: turn };
  st.msg = null; slog('fb14Plan', pl); fb14Show(); render(); return true;
}
/* about 4 times a second with a plan running: the coin may have moved the weights; a planned frame that no longer works
 * for enough of the states stops its beeps (and replans while the beeps still fit) */
function fb14Tick(t) {
  const P = st.plan; if (!P || !P.fb14 || P.stopped || P.tPress < performance.now() - 300) return;
  const h = fb14Horizon(performance.now()); if (FB14.tickH === h) return; FB14.tickH = h;
  fb14Advance(h); const Wg = fb14Weigh(h), D = 1, sh = fb14Share(fb14Sample(Wg.list, 100), P.target - D, P.target + D, P.fb14, fb14Kind(P.fb14));
  let v = 0; for (const [d, q] of (P.PD || PRESS_ERR)) v += q * (sh[d + D] || 0);
  const p = (1 - Wg.doubt) * v + Wg.doubt * fb14Blind(P.fb14); P.mix.pNow = +p.toFixed(3);
  if (Wg.doubt < 0.5 && p >= num('zwedge') && p >= P.mix.p - 0.15) return;
  if (P.tPress - (nBeeps() - 1) * num('gapms') > performance.now() + 200) { slog('fb14Replan', { from: P.target, p: +p.toFixed(3) }); st.plan = null; fb14Plan(); return; }
  cancelBeeps(); P.stopped = true; slog('beepsStopped', { from: P.target, why: 'fb14', p: +p.toFixed(3), doubt: +Wg.doubt.toFixed(3) });
  st.msg = 'Beeps stopped: the coin no longer supports the planned frame. ' + fb14BlindText(P.fb14)[0].toUpperCase() + fb14BlindText(P.fb14).slice(1) + '.'; render();
}
/* the step's screen closed: the partner's confirm (the lever), read off the video to about +-2 frames */
const FB14_SHIFTS = [[-2, 0.1], [-1, 0.25], [0, 0.4], [1, 0.2], [2, 0.05]];
function fb14Confirm(tObs, stp) {
  if (!stp || !stp.fb14) return;
  const turn = stp.fb14;
  if (stp.fb14role !== 'lever') return;
  if (turn === 4) FB14.p4t = tObs; FB14.pT = FB14.pT || {}; FB14.pT[turn] = tObs;
  if (FB14.t0 == null || !FB14.on) { FB14.pend = (FB14.pend || []).concat([{ tObs, turn, cat: stp.cat }]); slog('fb14ConfirmBeforeLock', { turn }); return; }   // the lock comes later: applied then
  const c = fbPic(tObs) - (FB14_VAN[stp.cat] || 2) - num('pfix'), F = Math.round(c);
  FB14.P[turn] = F; if (turn === 4) FB14.p4t = tObs; const P = st.plan && st.plan.fb14 === turn ? st.plan : null;
  slog('fb14Confirm', { turn, F, c: +c.toFixed(2), planned: P ? P.target : null, err: P ? +(c - P.target).toFixed(2) : null });
  if (FB14.on) { const h = fb14Horizon(performance.now()); fb14Advance(Math.min(h, F - 3)); fb14Input(fb14Kind(turn), F, turn, FB14_SHIFTS, tObs, (FB14_VAN[stp.cat] || 2) + num('pfix')); }
  fb14Show();
}
/* ---- T5: the Peach Beam confirm; T6: the Charge searched on the carried stream ---- */
function fb14Peach() {
  if (!FB14.on || !FB14.pb) return;
  const F = FB14.pb.F, out = []; fb14Advance(Math.min(fb14Horizon(performance.now()), F));
  const Wg = fb14Weigh(F); if (!Wg.list.length) { FB14.why = 'no state left at the Peach Beam'; fb14Show(); return; }
  for (const S of Wg.list.slice(0, 200)) { const T = fbClone(S); fbRun(T, F - T.l); out.push({ s: T.s >>> 0, w: T.w * T.lw, l: T.l, F: F - T.l }); }
  FB14.t6 = { at: F, bases: out, doubt: Wg.doubt };
  slog('fb14T6Ready', { F, bases: out.length, doubt: +Wg.doubt.toFixed(3) });
  fb14Show();
}
/* the T6 Charge's candidates: every seed FB14_T5 random numbers (plus the frames) after a carried Peach Beam seed. The
 * bases are merged where their stretches overlap (they are points on the same LCG stream a few steps apart). Returns
 * the seeds before A's base-angle draw, or null (no carry). */
function fb14T6Cands() {
  const T6 = FB14.t6; if (!T6 || !CHG.trig || T6.doubt >= 0.5) return null;
  const M6 = Math.round(fbPic(CHG.trig.t) - 16), out = new Set();
  const groups = [];
  for (const b of T6.bases) {
    const n0 = (M6 - b.l) + 13 - b.F, lo = n0 + FB14_T5[0], hi = n0 + FB14_T5[1];
    if (lo < 0) continue;
    let g = groups.find(G => { let x = G.s; for (let i = 0; i < 400; i++) { if (x === b.s) { G.lo = Math.min(G.lo, lo + i); G.hi = Math.max(G.hi, hi + i); return true; } x = fbAdv(x); } return false; });
    if (!g) groups.push({ s: b.s, lo, hi });
  }
  for (const G of groups) { let x = G.s; for (let i = 0; i < G.lo; i++) x = fbAdv(x); for (let n = G.lo; n <= G.hi; n++) { out.add(x >>> 0); x = fbAdv(x); } }
  if (window.__fb14truthT6 != null) { let x = window.__fb14truthT6 >>> 0, hit = -1; for (let k = 0; k < 3; k++) { if (out.has(x >>> 0)) hit = k; x = fbAdv(x); } slog('fb14T6Truth', { inCands: hit >= 0, bolts: hit }); }
  slog('fb14T6Cands', { M6, groups: groups.length, cands: out.size });
  return out.size ? [...out] : null;
}
/* ---- route glue ---- */
/* a T2 / T4 Charge's burst: its Mario confirm on the fight's clock, and its rays' creations into the carried states */
function fb14Trigger() {
  const stp0 = fb14Step(); FB14.trigTurn = stp0 ? stp0.fb14 : null;
  if (FB14.t0 == null || !CHG.trig) return;
  const M = Math.round(fbPic(CHG.trig.t) - 16), stp = stp0, turn = stp ? stp.fb14 : null;
  if (!FB14.on || turn == null || turn === 1 || FB14.M[turn] != null) return;
  // the burst places the confirm on the clock to about a frame (the trigger picture's time, dropped pictures): every
  // carried state gets the Charge at M - 1, M and M + 1; the lock keeps the ones that drew these rays
  // (applied once the pictures of the rays are captured: tripling thousands of states at the trigger stalled the page's
  // thread and dropped half the rays' pictures in the end-to-end run)
  FB14.M[turn] = M; FB14.pendChg = { M, turn };
}
/* the FB2 profile (T6) arms on any bar hide: not during T4's Bowser turn and T5's Peach Beam turn (the wave and the beam
 * flash the arena), only from the T6 menu on: 20 s after the Peach Beam confirm (its turn takes 22 s+), or 45 s after
 * T4's confirm when the Peach Beam was not seen */
function fb14ArmOk(P, t) {
  if (!P || P.id !== 'fb2' || FB14.p4t == null) return true;
  if (FB14.pb) return t - FB14.pb.t > 20000;
  return t - FB14.p4t > 45000;
}
/* a step change: the next turn's Charge needs the Charge reader armed again (it stays 'locked' after T1's) */
function fb14StepChange(was) {
  const W = RT()[was], N = RT()[routeStep];
  if (N && N.fb14 && N.chg === 'fb1' && (!W || W.fb14 !== N.fb14) && typeof CHG !== 'undefined' && !['search', 'maps', 'armed', 'capture'].includes(CHG.state) && CHG.state !== 'idle') chgReset();
  // a search still running for the last turn's Charge (a slow lock): the reader is armed again once it has finished
  if (N && N.fb14 && N.chg === 'fb1' && (!W || W.fb14 !== N.fb14) && typeof CHG !== 'undefined' && ['search', 'maps'].includes(CHG.state)) FB14.rearm = N.fb14;
  if (N && N.fb14 === 1 && N.fb14role === 'charge' && (!W || !W.fb14)) fb14Reset();      // a new attempt at the fight
  // from T4 on to the T6 Charge (the FB2 step): a reader left 'locked' / 'nolock' by T4's Charge must arm again
  if (W && W.fb14 && N && N.turn === 'fb2_pb' && typeof CHG !== 'undefined' && !['search', 'maps', 'armed', 'capture', 'idle'].includes(CHG.state)) chgReset();
}
function fb14Show() {
  const el = $('fb14-status'); if (!el) return;
  const stp = fb14Step(), turn = stp ? stp.fb14 : null, P = FB14.plan, pc = x => Math.round(100 * x) + '%';
  if (!FB14.on) { el.innerHTML = '<b>FB2 T1 → T4:</b> ' + (FB14.why ? FB14.why : 'waiting for the T1 Super Charge lock') + (turn ? '<br>No lock: ' + fb14BlindText(turn) + '.' : ''); return; }
  el.innerHTML = '<b>FB2 T1 → T4</b> (' + FB14.states.length + ' RNG states, ' + (FB14.how === 'carried' ? 'the carried seed fits the last Charge' : 'from the last Charge') + (FB14.doubt ? ', doubt ' + pc(FB14.doubt) : '') + ')' +
    (P && !P.none && P.turn ? '<br>T' + P.turn + ': ' + (P.turn === 1 ? 'Cloud Nine' : 'Do Nothing') + ' on the beep (+' + P.target + '): ' + fb14Goal(P.turn) + ' ' + pc(P.p) + ' (blind ' + pc(P.blind) + ')' : P && P.none ? '<br>T' + P.turn + ': no edge (' + P.none + '): ' + fb14BlindText(P.turn) : '') +
    (FB14.t6 ? '<br>T6: the Charge is searched on the carried stream (' + FB14.t6.bases.length + ' seeds at the Peach Beam)' : '');
}
/* The burst places its pictures on game frames by brightness (CHG_BRIGHT_FB1), but over this arena it varies from run to
 * run by a few levels (the stars, the lightning, Lakilester): on the end-to-end render 1234abcd frame 2 read +6.5 above
 * the menu where the curve has 3.4, so the trigger picture (6.1) was taken as frame 3 and every picture sat one frame
 * late. The seed still locked (7101 at 2.7x), but the aura fit bent to absorb the frame (the true pattern was in none of
 * the 21312 states) and the clock ran a frame off. With the seed known, the pictures one frame earlier and later are
 * scored too (the same seed, every aura / lightning / coin path: fb1score); the best of the three placements is kept, its
 * fit redone, and the trigger time moved with it. */
/* the pictures of a placement one frame earlier (d = -1) or later (d = +1): game frame n gets the picture placed on n + d
 * (G: frames 0 .. CHG_N + 1, then frames -2, -1) */
function fbShiftG(G, d) {
  const N = CHG_N, at = m => (m >= 0 && m < N + 2 ? G[m] : m === -1 ? G[N + 3] : m === -2 ? G[N + 2] : null), out = new Array(G.length).fill(null);
  for (let n = 0; n < N + 2; n++) out[n] = at(n + d); out[N + 2] = at(-2 + d); out[N + 3] = at(-1 + d); return out;
}
/* The fight's aura pattern from every Charge so far: the rays of one Charge leave it open where its respawns are faint or
 * missing and a frame's noise (~200) can outscore the true split (the end-to-end render: the true pattern 0.5% below the
 * best fit of T1, outside every T1 fit kept). Each Charge sees the pattern at another rotation (its confirm's frame mod
 * 20), so a pattern scored on the earlier Charges' rays and this one's together is far better pinned. The candidates: the
 * carried states' patterns and this Charge's fits' splits; each is scored as the best over the top fits of every Charge
 * (kernel fb1cscore); returned: the patterns within FB14_JTOL of the best sum, with their joint score. */
const FB14_JTOL = 0.025, FB14_JSIG = 0.01, FB14_JC = 600, FB14_JH = 20;
async function fb14Joint(res, maps, one) {
  const H = res.fb1 && res.fb1.hyps; if (!H || !H.hy.length || res.trigT == null) return null;
  const M = FB14.t0 == null ? 0 : Math.round((res.trigT - FB14.t0) / fbRate() - 16);
  const cur = { maps, a: H.a >>> 0, M, hyps: H.hy.slice().sort((x, y) => y.sc - x.sc).slice(0, FB14_JH).map(h => [h.p, h.q, h.br]), best: H.best };
  const prev = (FB14.charges || []).filter(c => c.M !== M).slice(-2);
  if (!FB14.on || !prev.length) return { cur };
  const cand = new Map(), add = (k, w) => { if (!cand.has(k) || cand.get(k) < w) cand.set(k, w); };
  for (const S of FB14.states.slice().sort((x, y) => y.w * y.lw - x.w * x.lw).slice(0, FB14_JC)) add(S.c.join(''), S.w * S.lw);
  // (this Charge's fits at each of the three frames its confirm may be on: M - 1, M, M + 1)
  for (const dM of [0, -1, 1]) for (const h of H.hy.slice(0, 200)) for (const AV of fbAuraVariants(h, H.best)) { const c = new Array(20); for (let j = 0; j < 20; j++) c[mod20(M + dM + 13 + j)] = AV.aura[j]; add(c.join(''), AV.w); }
  // and their neighbours: one count moved to a residue 1-2 frames away (all), two moves (the likeliest few): the true pattern
  // sat 2-3 such moves from every T1 fit in the end-to-end run
  const base = [...cand.entries()].sort((x, y) => y[1] - x[1]).map(([k]) => k);
  const moves = k => { const out = [], p = k.split('').map(Number); for (let j = 0; j < 20; j++) if (p[j] > 0) for (const dj of [-2, -1, 1, 2]) { const i = (j + dj + 20) % 20; if (p[i] >= 4) continue; const q = p.slice(); q[j]--; q[i]++; out.push(q.join('')); } return out; };
  const all = new Set(base); for (const k of base) for (const k2 of moves(k)) all.add(k2);
  for (const k of base.slice(0, 4)) for (const k2 of moves(k)) for (const k3 of moves(k2)) all.add(k3);
  const keys = [...all], tot = prev.concat([cur]).reduce((x, c) => x + c.best, 0);
  const scoreOf = async (ch, dM) => { const B = new Uint8Array(keys.length * 20); keys.forEach((k, i) => { for (let j = 0; j < 20; j++) B[i * 20 + j] = +k[mod20(ch.M + dM + 13 + j)]; });
    const r = await one(ch.maps, [{ type: 'cscore', a: ch.a, hyps: ch.hyps, cands: B }]); return Array.from(r[0].out, x => x - ch.best); };
  const sp = new Float64Array(keys.length);
  for (const ch of prev) (await scoreOf(ch, 0)).forEach((x, i) => { sp[i] += x; });
  // this Charge's confirm on the clock is good to a frame (the trigger picture): each of M - 1, M, M + 1 is tried
  let bestD = 0, bestMx = -1e30, bestS = null;
  for (const dM of [0, -1, 1]) { const sc = await scoreOf(cur, dM), S = sc.map((x, i) => x + sp[i]), mx = Math.max(...S); if (mx > bestMx + 1e-6) { bestMx = mx; bestD = dM; bestS = S; } }
  const keep = new Map(); keys.forEach((k, i) => { if (bestS[i] >= bestMx - FB14_JTOL * tot) keep.set(k, bestS[i] - bestMx); });
  if (keep.size > 64) { const top = [...keep.entries()].sort((x, y) => y[1] - x[1]).slice(0, 64); keep.clear(); for (const [k, v] of top) keep.set(k, v); }
  slog('fb14Joint', { charges: prev.length + 1, cands: keys.length, kept: keep.size, best: Math.round(bestMx), dM: bestD });
  if (window.__fb14truthAura) { const i = keys.indexOf(window.__fb14truthAura); slog('fb14JointTruth', { inCands: i >= 0, rel: i >= 0 ? Math.round(bestS[i] - bestMx) : null, tot: Math.round(tot), perCharge: i >= 0 ? Math.round(bestS[i] - sp[i]) + ' / ' + Math.round(sp[i]) : null }); }
  return { cur, keep, tot, dM: bestD };
}
async function fb14Refine(res, G) {
  FB14.refining = true;
  try { return await fb14Refine1(res, G); } finally { FB14.refining = false; }
}
async function fb14Refine1(res, G) {
  res.trigT = CHG.trig ? CHG.trig.t : null;
  try {
    const top = res.top && res.top[0]; if (!top || !G || !CHG.cen || !chgSearch.mod) return res;
    const shifted = d => fbShiftG(G, d);
    const one = (maps, msgs) => new Promise((resolve, reject) => {
      const w = new Worker(chgSearch.url), out = []; let k = -1;
      const next = () => { k++; if (k >= msgs.length) { w.terminate(); resolve(out); return; } w.postMessage(msgs[k]); };
      w.onmessage = e => { if (e.data.type === 'error') { w.terminate(); reject(new Error(e.data.msg)); return; } if (e.data.type !== 'ready') out.push(e.data); next(); };
      w.onerror = e => { w.terminate(); reject(new Error(e.message || 'worker')); };
      w.postMessage({ type: 'init', mod: chgSearch.mod, S: maps.S, C: maps.C, N: CHG_N, ND: CHG_ND, K: 16, pat: fb2Patterns().bytes });
    });
    const t0 = performance.now(), sc = { 0: top.sc }, alt = {};
    for (const d of [-1, 1]) { const M = chgMaps(shifted(d), CHG.cen, CHG_N); alt[d] = M; const r = await one(M, [{ type: 'fb1', seeds: [top.seed], v: null }]); sc[d] = r[0].out[0].sc; }
    let best = 0; for (const d of [-1, 1]) if (sc[d] > sc[best] * 1.03) best = d;
    slog('fb14Placement', { scores: { '-1': Math.round(sc[-1]), 0: Math.round(sc[0]), '+1': Math.round(sc[1]) }, kept: best, ms: Math.round(performance.now() - t0) });
    let out = res, maps = best ? alt[best] : chgMaps(G, CHG.cen, CHG_N);
    if (best) {
      const r = await one(alt[best], [{ type: 'fb1h', s0: top.seed, tol: FB14_TOL, max: 4000 }]);
      if (CHG.trig) { CHG.trig.t += best * FRAME; CHG.trig.n = (CHG.trig.n || 3) - best; }     // the trigger picture was frame 3 - best
      res.trigT += best * FRAME;
      CHG.info.placementShift = best;
      out = Object.assign({}, res, { fb1: Object.assign({}, res.fb1, { hyps: r[0] }) }); out.trigT = res.trigT;
    }
    out.maps0 = maps; out.joint = await fb14Joint(out, maps, one).catch(e => { slog('fb14JointError', { msg: String(e && e.message || e) }); return null; });
    return out;
  } catch (e) { slog('fb14PlacementError', { msg: String(e && e.message || e) }); return res; }
}
/* FB2 profile 'fb1' stage 2 (charge_live.js chgSearch): the relaxed score of every candidate, then the structured fit of
 * the best one */
async function fb1Stage2(W, call, top, times, t3) {
  const ps = [];
  const V = top.v && top.v.every(x => x != null) ? top.v : null;
  for (let k = 0; k < W.length; k++) { const idx = top.map((x, i) => i).filter(i => i % W.length === k), sd = idx.map(i => top[i]); if (sd.length) ps.push(call(W[k], { type: 'fb1', seeds: sd, v: V ? idx.map(i => V[i]) : null }, 'fb1').then(r => r.out.map((o, i) => ({ seed: sd[i], sc: o.sc })))); }
  let all = [].concat(...(await Promise.all(ps))).sort((a, b) => b.sc - a.sc);
  // a candidate on the best one's stream a few steps away shares B's rays and every respawn (B's creation is 24 + v steps
  // after A's base draw for any v), so it scores all but A's initial rays: the same seed, not a rival (T1 render: the true
  // seed 5853, the one 1 step off 4645). The runner-up for the lock's ratio is the best candidate off that stream.
  if (all.length > 1) { const b0 = all[0].seed >>> 0, near = new Set(); let x = b0, y = b0; for (let k = 0; k <= 48; k++) { near.add(x >>> 0); near.add(y >>> 0); x = fbAdv(x); y = Math.imul((y - 1) >>> 0, 0x6A76AE6D) >>> 0; }
    const same = all.filter((o, i) => i > 0 && near.has(o.seed >>> 0)); all = [all[0]].concat(all.slice(1).filter(o => !near.has(o.seed >>> 0))); times.sameStream = same.length; }
  times.stage2 = Math.round(performance.now() - t3); const t4 = performance.now();
  const hy = all.length ? await call(W[0], { type: 'fb1h', s0: all[0].seed, tol: FB14_TOL, max: 4000 }, 'fb1h') : null;
  times.hyps = Math.round(performance.now() - t4);
  return { top: all.slice(0, 5), fb1: { hyps: hy, times } };
}
window.__fb14 = { FB14, fbStep, fbRun, fbClone, fbRi, fbAdv, plan: c => fb14Plan(c), weigh: h => fb14Weigh(h), input: (k, F, turn, sh) => fb14Input(k, F, turn, sh), lock: r => fb14Lock(r), reset: () => fb14Reset(), confirm: (t, s) => fb14Confirm(t, s), pic: t => fbPic(t), pressT: F => fbPressT(F), t6cands: () => fb14T6Cands(), peach: () => fb14Peach(), fbNew: o => fbNew(o),
  sample: (b, w, h) => sample(b, w, h), reloadTargets: () => { targets = JSON.parse(localStorage.getItem('tot-targets') || '{}'); useTarget(); } };   // for tests
