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
const FB14_TOL = 0.008, FB14_SIG = 0.004, FB14_COMBOS = 1200, FB14_MAXH = 12000, FB14_LAGS = [[0, 0.75], [1, 0.25]];
const FB14_DELTA = { slam: 52, claw: 62, fire: 55, wave: 72, lightning: 99 }, FB14_AIAFTER = { cn: 332, nothing: 13 }, FB14_JELLY = 118;
const FB14_WAVE_POST = (() => { const o = { 66: 1, 68: 2, 70: 3, 72: 4, 74: 5, 76: 6, 78: 7, 80: 8, 126: 8, 128: 7, 130: 6, 132: 5, 134: 4, 136: 3, 138: 2, 140: 1 }; for (let d = 82; d <= 124; d += 2) o[d] = 9; return o; })();
// blind chances per lever frame (fb2_route/README.md section 3: route_build miss strings and the 20000-window study)
/* v87 (debug-core chain log of e2e 13579bdf, T4 popup left alone): 1 of 13 T4 waves split its e00742fc particles over odd
 * and even frames, which changes T4's test. Carried as a second hypothesis (FB14_WAVEB_P of the weight) from T4's Charge on. */
const FB14_WAVE_POST_B = { 67: 1, 68: 1, 69: 1, 70: 2, 71: 1, 72: 2, 73: 2, 74: 3, 75: 2, 76: 4, 77: 2, 78: 5, 79: 2, 80: 6, 81: 2, 82: 7, 83: 2, 84: 8, 85: 1, 86: 8, 87: 1, 88: 7, 89: 2, 90: 8, 91: 1, 92: 8, 93: 1, 94: 7, 95: 2, 96: 7, 97: 2, 98: 7, 99: 2, 100: 7, 101: 2, 102: 7, 103: 2, 104: 7, 105: 2, 106: 8, 107: 1, 108: 8, 109: 1, 110: 7, 111: 2, 112: 8, 113: 1, 114: 8, 115: 1, 116: 7, 117: 2, 118: 7, 119: 2, 120: 7, 121: 2, 122: 7, 123: 2, 124: 7, 125: 2, 126: 6, 127: 2, 128: 6, 129: 1, 130: 5, 131: 1, 132: 4, 133: 1, 134: 4, 136: 3, 138: 2, 140: 1 };
const FB14_WAVEB_P = 0.08;
/* v87: a T2 / T4 Charge's frame on the clock, read off its burst: -2 .. +2 (the e2e T2 Charge read 2 frames off), and the
 * narrowed search's fit tolerance on the carried stream (fb1Stage2) */
const FB14_CHGD = [[-2, 0.08], [-1, 0.22], [0, 0.4], [1, 0.22], [2, 0.08]], FB14_NTOL = 0.03;
const FB14_BLIND = { 1: 0.495, 2: 0.495, 3: 0.495, 4: 0.39 };
// the Peach Beam confirm -> the T6 Charge's rays frame 0: random numbers drawn = frames + this (t5_steps.py: Close Call
// 8654-8764, Bowser's hit 9116-9351; with margin for lag frames)
const FB14_T5 = [8540, 9420];
// the bar hiding after a confirm: the first picture without it shows confirm + 2 (Glide64 renders of the Charge and the
// Jelly, fb2_route/t14_log.py with SHOTS; the Peach Beam assumed the same); read to +-1 frame (FB14_JSHIFTS)
// the lever's screen: the first picture without its box shows the confirm + 1 (Cloud Nine's target, the マリオ name box) /
// + 2 (Lakilester's Strategies panel) in the same renders (the page's VAN, from console clips of other fights, says 2 / 3)
const FB14_VAN = { M: 1, S: 2 };
// a Charge burst this long after the last one, on that turn's lever step, is the next turn's Charge (Bowser's turn alone
// takes 15 s+ on console: T1 Cloud Nine -> T2 menu 18 s in the 2026-11-07 clip)
const FB14_NEXTCHG = 8000, FB14_NEWATTEMPT = 120000;
const FB14_MISSW = 0.01;     // v86: a state whose Bowser hit Mario on a turn the bar showed a miss (the HP read can be wrong: not 0)
const FB14_HIDE = { jelly: 2, peach: 2 }, FB14_JSHIFTS = [[-1, 0.25], [0, 0.5], [1, 0.25]];
var FB14 = { on: false };
function fb14Reset(why) { Object.assign(FB14, { on: false, why: why || null, states: [], t0: null, rate: null, taps: [], vis: [], visFrom: null, turn: 0, M: {}, P: {}, plan: null, lockN: 0, log: [], pb: null, t6: null, hideWatch: null, doubt: 0, bg: 0, p4t: null, pend: [], pT: {}, charges: [], inputs: [], lastBurst: null, gone: false, allOutLogged: false, prevPlan: null, hit: null, hp: null, hpw: null, missed: null, prior: null, earlyMsg: null }); }
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
function fbClone(S) { return { mk: S.mk, s: S.s, nc: S.nc, f: S.f, c: S.c, ph: S.ph, l: S.l, w: S.w, resp: S.resp.slice(), ev: S.ev.slice(), wv: S.wv, prev: S.prev, lv: S.lv, rg: S.rg, out: Object.assign({}, S.out), sh: S.sh.slice(), from: S.from, key: S.key, lw: S.lw, err: S.err, tag: S.tag, ca: S.ca && Object.assign({}, S.ca), wb: S.wb }; }
function fbNew(o) { return Object.assign({ resp: new Uint8Array(64), ev: [], wv: -1e9, lv: -1e9, rg: 0, prev: null, out: {}, sh: [], lw: 1, err: 0 }, o); }
function fbEv(S, e) { let i = S.ev.length; while (i > 0 && S.ev[i - 1].f > e.f) i--; S.ev.splice(i, 0, e); }
const mod20 = f => ((f % 20) + 20) % 20;
/* v86: Bowser's actor vars before his turn `turn` (TurnCount after the increment), from the attacks the state already
 * has on turns 1 .. turn - 1 (the phase-2 start: TurnCount 0, TurnsSinceShockwave / StarBeam / Recover 0, ClawSwipe /
 * BodySlam 3, RecoversLeft 3; final_bowser_2.c EVS_Init). The Star Rod aura is up from the start to the Peach Beam
 * (T5), and Mario has a jump charge from T1's Super Charge on (the wave would drain it: off the route then). */
function fbVars(S, turn) {
  const last = k => { let u = 0; for (let i = 1; i < turn; i++) if (S.out[i] && S.out[i].atk === k) u = i; return u; };
  const since = (k, base) => { const u = last(k); return u ? turn - u : base + turn; };
  let rec = 0; for (let i = 1; i < turn; i++) if (S.out[i] && S.out[i].atk === 'recover') rec++;
  return { turn, sinceShock: since('wave', 0), sinceStar: since('starrod', 0), sinceClaw: since('claw', 3), sinceSlam: since('slam', 3), sinceRecover: since('recover', 0), recovers: 3 - rec, enchanted: true, charged: true };
}
/* v86: the Recover check (Settings: Bowser's HP entering phase 2; Mario at 10 HP on T1-T4): 'hi' = never, 'lo' = always,
 * 'any' = both, half each (the coin and the turns' outcomes tell them apart) */
function fb14RgList() { const v = typeof $ === 'function' && $('s-fbhp') ? $('s-fbhp').value : 'hi'; return v === 'lo' ? [[1, 1]] : v === 'any' ? [[0, 0.5], [1, 0.5]] : [[0, 1]]; }
/* run frame S.f */
function fbStep(S) {
  const f = S.f; let s = S.s;
  // v87: the seed and coin on the frame after this Charge's rays (its M + 61), kept for a lock that lands after the state
  // has run past them (a late T2 lock: v86 skipped every carried state then, "matched 0 of 8000")
  if (S.ca && S.ca.s61 == null && f === S.ca.f61) { S.ca.s61 = s >>> 0; S.ca.nc61 = S.nc; }
  const m1 = (f + S.ph[0]) % 130, m2 = (f + S.ph[1]) % 220;
  if (m1 === 78 || m1 === 83 || m1 === 113 || m1 === 118) s = fbRi(s, 359);
  if (m2 === 18 || m2 === 78 || m2 === 88 || m2 === 178) s = fbRi(s, 359);
  while (S.ev.length && S.ev[0].f <= f) {
    const e = S.ev.shift(); if (e.f !== f) continue;
    if (e.k === 'chg') { if (!S.ca || S.ca.mk !== S.mk) S.ca = { mk: S.mk, a: fbAdv(s) >>> 0, f61: f + 48, s61: null, nc61: null };
      s = fbRi(s, 360); for (let i = 0; i < 10; i++) { s = fbRi(s, 10); s = fbRi(s, 10); for (let n = f + 9 + FBV; n < f + 45; n += 10) S.resp[n & 63]++; } }
    else if (e.k === 'jelly') { for (let i = 0; i < 10; i++) { s = fbRi(s, 359); s = fbRi(s, 10); s = fbRi(s, 10); } }
    else if (e.k === 'puff') { s = fbRi(s, 40); s = fbRi(s, 30); }
    else if (e.k === 'ai') {
      // v86: Bowser's whole EVS_TakeTurn_Inner (final_bowser_2.c; as pmrng_core.js fbnbAi, emulator-checked), from the
      // state's own history: the Recover check (S.rg: Mario's HP % more than 25 over Bowser's), the Star Rod (not while
      // the aura is up: T1-T4), the wave / Lightning Blast branches, the normal attacks
      const V = fbVars(S, e.turn); let atk = null;
      if (S.rg && V.recovers) { s = fbRi(s, 100); if (FBV < 75) { if (V.sinceRecover > 1) atk = 'recover'; else s = fbRi(s, 100); } }
      if (!atk && V.turn > 1 && !V.enchanted) { s = fbRi(s, 100); if (FBV < (V.sinceStar === 1 || V.sinceStar === 2 ? 0 : V.sinceStar === 3 ? 15 : 75)) atk = 'starrod'; }
      if (!atk && !(V.sinceShock < 3 || V.turn <= 3)) {
        if (V.sinceShock >= 6) { s = fbRi(s, 30); atk = FBV < 20 ? 'wave' : 'lightning'; }
        else { s = fbRi(s, 100); if (FBV < 75 && V.charged) atk = 'wave'; else { s = fbRi(s, 110); if (FBV < 30) atk = FBV < 20 ? 'wave' : 'lightning'; } }
      }
      if (!atk) { s = fbRi(s, 80); if (FBV < 20 && V.sinceSlam >= 2) atk = 'slam'; else { s = fbRi(s, 60); atk = FBV < 20 && V.sinceClaw >= 2 ? 'claw' : 'fire'; } }
      S.out[e.turn] = { atk, ai: f }; S.prev = atk;
      if (FB14_DELTA[atk] != null) fbEv(S, { k: 'test', f: f + FB14_DELTA[atk], turn: e.turn });
      else Object.assign(S.out[e.turn], { v: null, miss: false, ok: false, off: true });     // Recover / Star Rod: off the route (not modelled further)
      if (atk === 'wave') S.wv = f; else if (atk === 'lightning') S.lv = f;
    }
    else if (e.k === 'test') { s = fbRi(s, 100); const o = S.out[e.turn]; o.v = FBV; o.miss = FBV < 50; o.ok = o.miss && (e.turn !== 4 || o.atk === 'wave');
      if (o.atk === 'lightning') for (let i = 0; i < 3; i++) s = fbRi(s, 359); }   // v86: the blast's bolt, 3 x rand_int(359) right after the test
  }
  // v86: the Lightning Blast (fb2_route/lb_log.py, lb_model.py: 12 + 20 emulator runs exact): its energy effect on AI + 19
  // (1 x 360, 10 x (10, 20); each part respawns on + 19 + p, then every 20 frames while under + 50), rand_int(7) on AI + 69
  const dl = f - S.lv;
  if (dl === 19) { s = fbRi(s, 360); for (let i = 0; i < 10; i++) { s = fbRi(s, 10); s = fbRi(s, 20); for (let n = f + 19 + FBV; n < f + 50; n += 20) S.resp[n & 63]++; } }
  else if (dl === 69) s = fbRi(s, 7);
  const dw = f - S.wv;
  if (dw === 29) s = fbRi(s, 7); else if (dw === 76) for (let i = 0; i < 8; i++) s = fbRi(s, 359);
  if (f === S.nc) { s = fbRi(s, 100); if (FBV >= 70) S.sh.push(f); S.nc = f + (FBV >= 70 ? 48 : 24); }
  for (let i = S.c[mod20(f)]; i; i--) s = fbRi(s, 359);
  const r = S.resp[f & 63]; if (r) { for (let i = r; i; i--) s = fbRi(s, 359); S.resp[f & 63] = 0; }
  if (dw > 0 && dw <= 160) { const k = (S.wb ? FB14_WAVE_POST_B : FB14_WAVE_POST)[dw] || 0; for (let i = 0; i < k; i++) { s = fbRi(s, 359); s = fbRi(s, 359); s = fbRi(s, 10); s = fbRi(s, 15); s = fbRi(s, 15); } }
  S.s = fbRi(s, 1); S.f = f + 1;
}
function fbRun(S, to) { while (S.f < to) fbStep(S); return S; }
/* ---- the clock: logic frame 0 = T1's Mario confirm; FB14.t0 = the time the picture of frame 0 would show ---- */
const fbRate = () => FB14.rate || (typeof chgRate === 'function' ? chgRate() : FRAME);
const fbPic = t => (t - FB14.t0) / fbRate();
// the press for clock frame F: as Time Out's and the FB2 popup's (1.7 frames before that frame's picture, the runner's
// beep offset, the capture delay)
/* v86: the lever presses on console came 2.2 and 2.5 frames before the beeped frame (logs 1794169517521 / 1794170840652, T2's
 * Do Nothing, both read from the Strategies panel vanishing; the input display in the clips confirms the panel read: the
 * panel goes 11 video frames after the A shows there, as the Charge bar does 13 and the Cloud Nine list 10, i.e. the read
 * matches the emulator's P + 2). The runner's other presses (Jr. Troopa, Hallway) are near 0 on the same offset setting,
 * so this one is the Final Bowser lever's own: the beeps come later by minus the mean of the last 8 lever presses (these two
 * to start with; clamped to 3 frames). Kept in this browser (tot-fb14press). */
/* v87: one of the per-lever corrections (page_template.html leverBias: Final Bowser, Duplighosts); each press is kept as the
 * runner's own error against the beep (the measured error minus the correction the beeps had), so the correction does not
 * decay to 0 as the presses come in on time (v86 kept the error against the target) */
function fb14PressList() { return typeof leverList === 'function' ? leverList('fb14') : [-2.54, -2.2]; }
function fb14Bias() { return typeof leverBias === 'function' ? leverBias('fb14') : 0; }
function fb14PressAdd(err) { return typeof leverAdd === 'function' ? leverAdd('fb14', err) : []; }
const fbPressT = F => FB14.t0 + (F - 1.7 + num('off') + fb14Bias()) * fbRate() - num('vlag');
/* ---- the route: the Final Bowser steps (page_template.html ENDGAME) ---- */
const fb14Step = () => { const s = isRoute() && RT()[routeStep]; return s && s.fb14 ? s : null; };
/* ---- the lock (a Charge read with the aura profile): hypotheses -> states ---- */
/* v82: the doubt a lock starts with. A read that only just clears the lock (ratio under 3.5: the Final Bowser locks of these
 * logs read 2.3-2.6, the Jr. Troopa / Hallway ones 3-5), whose placement one frame off scores almost as well (within 10%),
 * or that contradicts the carried states (none of them drew its rays: one of the two reads is wrong, or the turn went off
 * the model) starts doubtful; the coin then confirms it (or not) as for any lock. 50%+ = no beeps until it has. */
function fb14Prior(res, contra) {
  const top = res && res.top, a = top && top[0], b = top && top[1], ratio = a && b && b.sc > 0 ? a.sc / b.sc : (CHG.info && CHG.info.best ? CHG.info.best.ratio : 9);
  const ps = res && res.placeScores, sc = ps ? [ps[0], ps[-1], ps[1]].filter(x => x != null).sort((x, y) => y - x) : null, close = sc && sc.length > 1 && sc[1] / sc[0] > 0.9;
  let d = ZW_BG0; if (ratio < 3.5) d = Math.max(d, Math.min(0.42, 0.05 + (3.5 - ratio) * 0.3)); if (close) d = Math.min(0.49, d + 0.1); if (contra) d = Math.max(d, 0.5);
  return { d: +d.toFixed(3), ratio: +(+ratio).toFixed(2), close: !!close, contra: !!contra };
}
function fb14Lock(res) {
  const H = res.fb1 && res.fb1.hyps, stp = fb14Step(), turn = FB14.trigTurn || (stp ? stp.fb14 : 1); FB14.trigTurn = null;
  if (!H || !H.hy.length) { FB14.why = 'no hypotheses from the rays'; fb14Show(); return; }
  const rate = chgRate(), P = fb2Patterns(), first = !FB14.on || FB14.t0 == null;
  FB14.menuT = CHG.menuSince || null;      // the bar up in Mario's menu before this Charge (charge_live.js chgFrame)
  const trigT = res.trigT != null ? res.trigT : CHG.trig.t;     // (the reader may have been reset for the next Charge meanwhile)
  if (first) { FB14.rate = rate; FB14.t0 = trigT - 16 * rate; }
  const M = first ? 0 : Math.round((trigT - FB14.t0) / fbRate() - 16) + (res.joint && res.joint.dM ? res.joint.dM : 0);   // (fb14Joint: the frame the Charges' rays agree on)
  FB14.t0 = trigT - (M + 16) * fbRate();            // the burst fixes the clock again (drift)
  const seen = new Set(); const hadCarry = !first && FB14.states.length > 0;
  // the menu's coin before the Charge: back to 1 s after the bar came up for that menu (at most 15 s)
  const menuF = FB14.menuT != null ? Math.min(M, Math.max(M - 450, Math.ceil(fbPic(FB14.menuT) + 30))) : M;
  const back0 = (x0, F0, q, c, pa) => { const r = fbBackShines(x0, F0, q, c, pa, menuF); return { ok: r.ok, sh: r.sh.sort((a, b) => a - b), from: Math.min(menuF, F0) }; };
  // v87: the fresh fits are built only when no carried state drew these rays (about 1 s on the page's thread)
  const buildFresh = () => {
  let fresh = [];
  // the fits x their aura splits, the likeliest FB14_COMBOS by weight (0.8% of the best keeps thousands of fits)
  const combos = [];
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
        for (const [rg, wr] of fb14RgList()) fresh.push(fbNew({ s: h.s48 >>> 0, nc: M + 13 + h.nc48, f: M + 61, c, ph: pa, l, rg, w: wr * wl * AV.w * (B.ok ? 1 : 1e-3), from: B.from, sh: B.sh, key: key + ':' + rg, tag: turn }));
      }
    }
    }
  }
  // the aura pattern is the fight's: a fresh fit after an earlier lock keeps only the patterns the carried states still
  // hold (when any is among them)
  if (!J && !first && FB14.states.length) { const cs = new Set(FB14.states.map(S => S.c.join(''))), f2 = fresh.filter(S => cs.has(S.c.join(''))); if (f2.length) fresh = f2; slog('fb14AuraKeep', { turn, fits: fresh.length, of: seen.size }); }
  return fresh; };
  const J = res.joint && res.joint.keep && res.joint.keep.size ? res.joint : null;
  // v87: a T2 / T4 Charge held for the narrowed search (fb14ChgCands): the carried states get it now, at the shifts whose
  // stream drew these very rays (all of FB14_CHGD when none did)
  let held = null; const N14 = typeof CHG !== 'undefined' ? CHG.narrow14 : null;
  if (!first && FB14.pendChg && N14 && N14.M === FB14.pendChg.M) {
    const pc = FB14.pendChg, a = H.a >>> 0; N14.used = true; FB14.pendChg = null;
    const ds = new Set(); for (const [x, set] of N14.dmap) if ((fbAdv(x) >>> 0) === a) for (const d of set) ds.add(d);
    const dsel = ds.size ? FB14_CHGD.filter(([d]) => ds.has(d)) : FB14_CHGD;
    held = [];
    for (const S of FB14.states) for (const [d, wd] of dsel) { const F = pc.M + d - S.l; if (S.f > F + 13) continue; const T = fbClone(S); T.w = S.w * wd; T.mk = pc.M + d; fbInputEv(T, 'chg', F, pc.turn); held.push(T); }
    if (pc.turn === 4) held = fb14WaveSplit(held);
    slog('fb14Held', { turn: pc.turn, M: pc.M, d: dsel.map(x => x[0]), states: held.length });
  }
  let keep = null, how = 'fresh', fresh = [];
  const carriedL = held || FB14.states;
  if (!first && carriedL.length) {      // the carried states: those that drew these very rays
    const a = H.a >>> 0, match = [];
    // v87: the seed on the frame after the rays only (v86 also asked for the coin's phase: the game's state was among the
    // fits with its coin 11 frames off, and the first v87 build dropped it and planned T2 at 99.85% on a frame Bowser hit)
    const ends = new Set(H.hy.map(h => String(h.s48 >>> 0)));
    for (const S of carriedL) {
      const m = (S.mk != null ? S.mk : M) - S.l;
      if (S.f > m + 13) {       // v87: a lock that landed after the state ran past the rays: the seeds it kept then
        const ca = S.ca; if (!ca || ca.mk !== S.mk || ca.a !== a) continue;
        if (ca.s61 != null) { if (ends.has(String(ca.s61))) match.push(S); continue; }
        continue;
      }
      const T = fbClone(S);
      fbRun(T, m + 13); let x = T.s; for (let i = fbBolts(m + 13, T.ph); i; i--) x = fbRi(x, 359);
      if ((fbAdv(x) >>> 0) !== a) continue;
      fbRun(T, m + 61); if (!ends.has(String(T.s >>> 0))) continue;
      match.push(T);       // (v87: the matched states keep their coin history)
    }
    if (match.length) { keep = match; how = 'carried';
      // v87: the clock follows the Charge frame the matched states vote for, weighed by the coin so far, and only when
      // 60%+ of that weight agrees
      const sv = [FB14.states, FB14.gone, FB14.allOutLogged]; FB14.states = match; fb14Weigh(M + 61); [FB14.states, FB14.gone, FB14.allOutLogged] = sv;
      const by = {}; let tot = 0; for (const T of match) { const v = T.w * (T.lw == null ? 1 : T.lw); by[T.mk] = (by[T.mk] || 0) + v; tot += v; }
      const Mt = +Object.keys(by).sort((x, y) => by[y] - by[x])[0], share = tot > 0 ? by[Mt] / tot : 0;
      if (Mt !== M && Number.isFinite(Mt)) { if (share >= 0.6) { slog('fb14ClockFix', { turn, M, Mt, share: +share.toFixed(3) }); FB14.t0 = trigT - (Mt + 16) * fbRate(); } else slog('fb14ClockKept', { turn, M, Mt, share: +share.toFixed(3) }); }
    }
    slog('fb14Check', { turn, M, carried: carriedL.length, matched: match.length, held: held ? held.length : null });
    if (!match.length && held) FB14.states = fb14Cap(held);
  }
  if (!keep) { fresh = buildFresh(); keep = fresh; }
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
  // v82: the prior doubt of a lock (the background's share before the coin has spoken). v81 started every lock at 5%: log
  // 1794170840652's T2 lock (2.5x) replaced a carry that matched none of its rays and planned at doubt 0.7% (70%, wrong)
  const d0 = how === 'carried' ? { d: ZW_BG0, carried: true } : fb14Prior(res, hadCarry); FB14.prior = d0;
  Object.assign(FB14, { on: true, why: null, turn, lockN: FB14.lockN + 1, plan: null, bg: d0.d / (1 - d0.d), bgFrom: Math.min(M + 61, menuF), how });
  FB14.doubt = d0.d; if (d0.d > ZW_BG0) slog('fb14Prior', d0);
  FB14.M[turn] = M;
  if (res.joint && res.joint.cur) { res.joint.cur.M = M; FB14.charges = (FB14.charges || []).filter(c => c.M !== M).concat([res.joint.cur]).slice(-2); }
  // confirms the page saw before this lock landed (a slow lock): their frames from the clock the lock has just fixed
  // the inputs of this turn the page saw before this lock landed (a slow lock: the partner's confirm, T3's Jelly), onto
  // fresh states (carried ones have them already)
  if (how === 'fresh') for (const x of (FB14.inputs || []).map(x => Object.assign({}, x, { F: x.t != null ? Math.round(fbPic(x.t) - x.off) : x.F })).filter(x => x.F > M + 13 && x.turn >= turn).sort((a, b) => a.F - b.F)) { fb14Input(x.kind, x.F, x.turn, x.shifts, x.t, x.off); slog('fb14Replay', { kind: x.kind, F: x.F, turn: x.turn }); }
  const pend = (FB14.pend || []).filter(x => x.turn >= turn); FB14.pend = [];
  for (const x of pend) { const c = fbPic(x.tObs) - (FB14_VAN[x.cat] || 2) - num('pfix'), F = Math.round(c); FB14.P[x.turn] = F; fb14Input(fb14Kind(x.turn), F, x.turn, x.shifts || FB14_SHIFTS, x.tObs, (FB14_VAN[x.cat] || 2) + num('pfix')); slog('fb14LateConfirm', { turn: x.turn, F }); }
  if (window.__fb14dbg) { const T = window.__fb14truth; window.__fb14dbg.push({ turn, M, how, n: FB14.states.length, truth: T ? FB14.states.filter(S => S.s === T.s && (T.nc == null || S.nc === T.nc)).map(S => ({ c: Array.from(S.c).join(''), ph: S.ph, l: S.l, w: S.w, lw: S.lw })) : null }); }
  if (false) window.__fb14dbg.push({ turn, M, how, states: FB14.states.slice(0, 3000).map(S => ({ s: S.s >>> 0, nc: S.nc, f: S.f, l: S.l, c: Array.from(S.c).join(''), ph: S.ph, w: S.w, lw: S.lw, sh: S.sh })) });
  if (turn === 4) FB14.states = fb14WaveSplit(FB14.states);     // v87: the T4 wave's second particle order
  slog('fb14Lock', { turn, M, how, hyps: H.hy.length, n: H.n, fits: FB14.n0, states: FB14.states.length, best: Math.round(H.best), a: (H.a >>> 0).toString(16) });
  if (window.__fb14seeds) fb14Truth('lock' + turn);
  fb14Show(); return how;
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
  if (shifts) FB14.states = fb14Cap(kind === 'chg' && turn === 4 ? fb14WaveSplit(out) : out);
  slog('fb14Input', { kind, F: Fc, turn, states: FB14.states.length });
}
function fbInputEv(T, kind, F, turn) {
  if (kind === 'chg') { fbEv(T, { k: 'chg', f: F + 13 }); fbEv(T, { k: 'chg', f: F + 16 }); }
  else if (kind === 'jelly') fbEv(T, { k: 'jelly', f: F + FB14_JELLY });
  else if (kind === 'cn') { for (let i = 200; i < 210; i++) fbEv(T, { k: 'puff', f: F + i }); fbEv(T, { k: 'ai', f: F + FB14_AIAFTER.cn, turn }); }
  else if (kind === 'nothing') fbEv(T, { k: 'ai', f: F + FB14_AIAFTER.nothing, turn });
}
/* v87: the true state ranked 3000-7000 by prior and was cut after the x5 Do Nothing shifts: the cap keeps the likeliest by
 * prior and coin together (w x lw), FB14_MAXH 12000 */
function fb14Cap(L) {
  const by = new Map(); for (const S of L) { const k = S.s + ':' + S.nc + ':' + S.f + ':' + S.l + ':' + S.ph.join(',') + ':' + S.c.join('') + ':' + S.wv + ':' + S.lv + ':' + S.rg + ':' + (S.wb ? 1 : 0) + ':' + Object.keys(S.out).map(k => k + S.out[k].atk).join('') + ':' + S.resp.join('') + ':' + S.ev.map(e => e.k + e.f).join(','); const o = by.get(k); if (o) o.w += S.w; else by.set(k, S); }
  const A = [...by.values()].sort((x, y) => y.w * (y.lw || 1) - x.w * (x.lw || 1)); return A.length > FB14_MAXH ? A.slice(0, FB14_MAXH) : A;
}
/* v87: T4's wave in its second particle order (FB14_WAVE_POST_B): each state not yet split becomes both */
function fb14WaveSplit(L) {
  const out = [];
  for (const S of L) { if (S.wb != null) { out.push(S); continue; } const B = fbClone(S); S.wb = 0; S.w *= 1 - FB14_WAVEB_P; B.wb = 1; B.w *= FB14_WAVEB_P; out.push(S, B); }
  return out;
}
/* v87 (e2e 1234abcd / 9e3779b9): the T2 full search took 4-9 s and landed after the Do Nothing confirm. With the seed carried
 * the T2 / T4 Charge is searched on the carried stream instead (charge_live.js chgSearch opts.cands, as T6): every carried
 * state at each Charge frame FB14_CHGD gives the seed before A's base-angle draw (14-22 distinct seeds in the runs). The
 * Charge's input is held meanwhile (fb14Held), so the states have not run past it when the narrowed lock lands. */
function fb14ChgCands() {
  const pc = FB14.pendChg; if (!pc || !FB14.on || !FB14.states.length || typeof CHG === 'undefined') return null;
  const dmap = new Map(), ds = FB14_CHGD.map(x => x[0]).sort((a, b) => a - b);
  for (const S of FB14.states) {
    const B = fbClone(S);       // (no Charge in the state yet: one stream for every shift)
    for (const d of ds) { const m = pc.M + d - S.l; if (B.f > m + 13) continue; fbRun(B, m + 13); let x = B.s; for (let i = fbBolts(m + 13, B.ph); i; i--) x = fbRi(x, 359); x >>>= 0; let st = dmap.get(x); if (!st) dmap.set(x, st = new Set()); st.add(d); }
  }
  CHG.narrow14 = { M: pc.M, turn: pc.turn, done: false, n: dmap.size, dmap };
  slog('fb14ChgCands', { M: pc.M, turn: pc.turn, states: FB14.states.length, cands: dmap.size });
  return dmap.size ? [...dmap.keys()] : null;
}
/* v87: hold the pending Charge's input while its narrowed search may still lock on the carried stream */
function fb14Held() {
  const pc = FB14.pendChg; if (!pc || !FB14.on || typeof CHG === 'undefined' || typeof chgP !== 'function' || chgP().id !== 'fb1') return false;
  const N = CHG.narrow14;
  if (!N || N.M !== pc.M) return CHG.state === 'maps';
  if (!N.done) return CHG.state === 'maps' || CHG.state === 'search';
  return !!(N.ok && !N.used && (CHG.state === 'search' || FB14.refining));
}
/* v87 (tests only: window.__fb14seeds = { off, s: [true seeds], ... }): whether the game's state is among the states */
function fb14IsTrue(S) { const T = window.__fb14seeds; if (!T) return false; const i = S.f + S.l - T.off; return i >= 0 && i < T.s.length && (S.s >>> 0) === (T.s[i] >>> 0); }
function fb14Truth(at) { if (!window.__fb14seeds) return; const L = FB14.states, n = L.filter(fb14IsTrue).length; let tot = 0, tw = 0; for (const S of L) { const v = S.w * (S.lw || 1); tot += v; if (fb14IsTrue(S)) tw += v; } slog('fb14Truth', { at, states: L.length, trueStates: n, trueShare: tot ? +(tw / tot).toFixed(4) : 0 }); }
/* ---- the coin: shines (clock frame of the draw) and the stretches the coin was watched ---- */
// the coin is kept in page time (ms) and read on the clock when the states are weighed: a lock re-anchors the clock, and
// the shines of the menu the lock was searched in still count
function fb14Tap(t) { FB14.taps.push(t); if (FB14.taps.length > 400) FB14.taps.shift(); }
function fb14Frame(t, present) {
  FB14.lastT = t;
  if (FB14.pendChg && !['armed', 'capture'].includes(CHG.state) && !fb14Held()) { const { M, turn } = FB14.pendChg; FB14.pendChg = null; fb14Advance(Math.min(fb14Horizon(performance.now()), M + 10)); fb14Input('chg', M, turn, FB14_CHGD); if (window.__fb14seeds) fb14Truth('chg' + turn); }
  if (FB14.rearm && !FB14.refining && ['locked', 'nolock', 'failed'].includes(CHG.state)) { const n = fb14Step(); if (n && n.fb14 === FB14.rearm && n.chg === 'fb1') { slog('fb14ReaderRearmed', { turn: n.fb14 }); chgReset(); } FB14.rearm = null; }
  if (!FB14.on && !fb14Step()) return;
  if (present && FB14.visFrom == null) FB14.visFrom = t;
  if (!present && FB14.visFrom != null) { FB14.vis.push([FB14.visFrom, t]); if (FB14.vis.length > 200) FB14.vis.shift(); FB14.visFrom = null; }
  fb14HideWatch(t, present);
  fb14HpWatch(t, present);
  fb14EarlyPlan(t);
  if (FB14.on && (!FB14.tickT || t - FB14.tickT > 250)) { FB14.tickT = t; fb14Tick(t); }
}
/* v82 (logs 1794169517521 and 1794170840652, clips 15-24-14 / 15-46-32): Bowser's fire hit Mario after the lever (T2 of
 * the first, T1 of the second), HP 10 -> 0 and the Life Shroom. Neither the hit nor the revive is modelled, and the revive
 * ends the route (the first fight's carry died at T3; the second planned T2 at doubt 0.7% from a fresh lock and Bowser hit
 * again). Mario's HP tens place (jrTens, the Hallway's read, console-checked there): the "1" of 10 on the steady bar
 * before the lever, blank on the steady bar for 10 frames after it = a hit. From then on: no edge for this attempt. */
function fb14HpWatch(t, present) {
  /* v86: the watch follows the last lever confirmed (T1-T3), not the route's step: the step moves on at the confirm, so v82-v85
   * watched the next turn instead and never saw a hit on the turn just played (the hit is read 2-25 s after the confirm). It
   * also reads the miss: the "1" of 10 HP steady on the bar through Bowser's turn (30+ frames from 2 s after the confirm)
   * and no hit by the next turn's own action (its Charge or the Jelly) = Bowser missed. Each state's attack and test value
   * for that turn are then checked against it (fb14Weigh): on log 1794169517521's T1 (Bowser's fire breath missed) only
   * 36% of the weight predicted that, and with it the T2 shares are 93-99% or under 7% on almost every frame. */
  if (FB14.hit || typeof jrTens !== 'function') return;
  const stp = fb14Step(); if (!stp || !stp.fb14) return;
  const W = FB14.hpw || (FB14.hpw = { seen10: false, tenRun: 0, blankRun: 0, ok: {}, done: {} });
  const B = JRT.bar; if (!present || !B.since || t - B.since < 6 * FRAME) { W.tenRun = 0; W.blankRun = 0; return; }
  const v = jrTens(), one = v >= JR_TENS_MIN;
  W.tenRun = one ? W.tenRun + 1 : 0; W.blankRun = one ? 0 : W.blankRun + 1;
  const open = [3, 2, 1].find(k => FB14.pT && FB14.pT[k] != null && !W.done[k]);
  if (open == null || FB14.pT[open] > t) { if (W.tenRun >= 6) W.seen10 = true; return; }
  const pT = FB14.pT[open]; if (!W.seen10 || t < pT + 2000) return;
  if (t - pT > 25000) { W.done[open] = 'late'; return; }
  if (one) W.ok[open] = (W.ok[open] || 0) + 1;
  if (W.blankRun >= 10) { W.done[open] = 'hit'; FB14.hit = open; slog('fb14Hit', { turn: open, afterMs: Math.round(t - pT), tens: +v.toFixed(2) }); cancelBeeps(); if (st.plan && st.plan.fb14) st.plan = null; fb14CarryGone(); fb14Show(); render(); }
}
/* v86: the turn before `turn` is over (this turn's Charge burst, or the Jelly): Bowser missed it if the bar showed Mario's
 * 10 HP through his turn and no hit was read. Weighs the states from then on (fb14Weigh). */
function fb14TurnOver(turn) {
  const k = turn - 1, W = FB14.hpw; if (k < 1 || k > 3 || !W || W.done[k] || FB14.hit || !FB14.pT || FB14.pT[k] == null) return;
  if (W.seen10 && (W.ok[k] || 0) >= 30) { W.done[k] = 'miss'; FB14.missed = FB14.missed || {}; FB14.missed[k] = true; slog('fb14Missed', { turn: k, frames10: W.ok[k] }); }
  else { W.done[k] = 'unread'; slog('fb14MissUnread', { turn: k, seen10: W.seen10, frames10: W.ok[k] || 0 }); }
}
/* v82 (log 1794170840652: the T1 lock landed, then nothing for 21 s): on a lever step the plan is made as soon as the turn's
 * lock is in, without waiting for the target screen (whose picture may never have been saved: no plan and no confirm on
 * T1 in either log), and "No edge" / "being read" says so at once. Not before the partner's menu can be up (the Charge's
 * frame + 90), and not again once this lever was confirmed. */
function fb14EarlyPlan(t) {
  const stp = fb14Step(); if (!stp || stp.fb14role !== 'lever' || V.wasOn) return;
  const turn = stp.fb14, now = performance.now();
  if (FB14.pT && FB14.pT[turn] != null) { if (FB14.earlyMsg !== turn && !FB14.hit) { FB14.earlyMsg = turn; if (!(st.plan && st.plan.fb14 === turn)) { st.msg = 'T' + turn + ': ' + (turn === 1 ? 'Cloud Nine' : 'Do Nothing') + ' was confirmed' + (FB14.on ? '' : ' before the seed was read (blind)') + '. Next time wait on its screen for the beeps (they come about 4-5 s after the Charge), or "No edge".'; render(); } } return; }
  if (turn === 3 || (turn !== 1 && FB14.on && FB14.M[turn] == null && !['capture', 'maps', 'search'].includes(CHG.state))) return;   // T3: on its screen (no Charge to time it)
  if (FB14.on && FB14.M[turn] != null && fbPic(now) < FB14.M[turn] + 90) return;
  if (st.plan && now < st.plan.tPress + 600) return;
  if (st.planTry && now - st.planTry < 500) return; st.planTry = now;
  st.planEarly = true; try { makePlan(); } finally { st.planEarly = false; }
  if (st.plan && st.plan.fb14 === turn && st.plan.tMade >= now) st.plan.early = true;
}
/* the bar hiding: T3's Jelly confirm (Mario's turn of T3), T5's Peach Beam confirm (after T4's Do Nothing) */
function fb14HideWatch(t, present) {
  const W = FB14.hideWatch || (FB14.hideWatch = { up: 0, gone: 0 });
  if (present) { if (!W.up) W.up = t; W.gone = 0; return; }
  if (!W.gone) W.gone = t; if (t - W.gone < 8 * FRAME) return;              // gone for 8 frames: not a flicker
  if (!W.up) return; const upMs = W.gone - W.up; W.up = 0; t = W.gone; if (upMs < 600) return;
  // v82 (log 1794169517521, clip 15-24-14): T1's Cloud Nine confirm from the bar hiding when its target screen was not
  // read (the runner confirmed 0.27 s after the target hand showed, 0.25 s before the T1 lock; the screen never matched).
  // v81 then carried T1 without Cloud Nine (its puffs and Bowser's AI): T2's doubt 63% where the same states with it read
  // 1.5% (that lock replayed with the log's coin, test_console_1108b). The bar goes FB14_C9HIDE frames after the A, as
  // Lakilester's Spiny Flip in the Hallway (route clips, not measured for Cloud Nine): -2..+2 carried, the coin settles it
  // v86 (end-to-end run 1234abcd): with Mario's target screen saved (cat M: Cloud Nine's is the same screen) the T1 Super
  // Charge's own confirm closes it and moves the route to the Cloud Nine step before the Charge's bar hide: v82-v85 took that
  // hide as Cloud Nine's confirm (frame 0: before the rays, every state dropped, "No edge" for all of T1). Cloud Nine's bar
  // hide comes after the T1 Charge's burst (its partner menu opens 3 s later): only then.
  { const s1 = fb14Step(), lb = FB14.lastBurst; if (s1 && s1.fb14 === 1 && s1.fb14role === 'lever' && !(FB14.pT && FB14.pT[1] != null) && lb && lb.turn === 1 && t - lb.t > FB14_C9AFTER) { slog('fb14CloudNineByBar', { at: Math.round(t), upMs: Math.round(upMs) }); fb14Confirm(t - (FB14_C9HIDE - FB14_VAN.M) * FRAME, s1, FB14_C9SHIFTS, 'bar'); return; } }
  if (FB14.t0 == null) return;
  const stp = fb14Step(), F = fbPic(t);
  if (stp && stp.fb14 === 3 && FB14.M[3] == null && FB14.pT && FB14.pT[2] != null && t - FB14.pT[2] > 3000) { fb14TurnOver(3); FB14.M[3] = Math.round(F - FB14_HIDE.jelly); fb14Input('jelly', FB14.M[3], 3, FB14_JSHIFTS, t, FB14_HIDE.jelly); slog('fb14Jelly', { M: FB14.M[3] }); }
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
    if (FB14.missed) for (const k in FB14.missed) { const o = S.out[k]; if (o && (o.off || (o.v != null && !o.miss))) { lw *= FB14_MISSW; err++; } }   // v86: Bowser was seen to miss that turn
    S.lw = lw; S.err = err; if (err > ZW_MAXERR) continue; out.push(S); mx = Math.max(mx, S.w * lw);
  }
  const keep = out.filter(S => S.w * S.lw >= mx * ZW_CUT), sum = keep.reduce((a, S) => a + S.w * S.lw, 0);
  if (!keep.length && FB14.states.length && !FB14.allOutLogged) { FB14.allOutLogged = true; FB14.gone = true; slog('fb14AllOut', { h, taps: tapF.filter(x => x < h).map(x => +x.toFixed(1)).slice(-20), vis: vis.map(v => v.map(x => +x.toFixed(1))).slice(-8), sample: FB14.states.slice(0, 4).map(S => ({ f: S.f, l: S.l, from: S.from, sh: S.sh.slice(-12), err: S.err })) }); }
  let nVis = 0; for (const [a, b] of vis) nVis += Math.max(0, b - Math.max(a, FB14.bgFrom || 0));
  let bg = tot0 * FB14.bg * Math.exp(-ZW_RHO * nVis);
  if (FB14.missed) for (const k in FB14.missed) bg *= fb14Blind(+k);     // v86: a state off the model would have missed as often as blind
  return { list: keep, doubt: keep.length ? bg / (bg + sum) : 1, sum };
}
/* every state to the horizon (frames whose shines have had time to be read) */
// (from the newest picture's time: the same as now live; a capture that lags must not move the states past inputs not yet seen)
function fb14Horizon(now) { return Math.floor(fbPic(Math.min(now, FB14.lastT || now) - num('vlag')) - 10); }
// v86 (end-to-end run 1234abcd, T2): the Charge's input waits for the rays' capture (FB14.pendChg); a plan made meanwhile ran
// the states past the Charge's frame, its input then found none to take it (every state dropped, "No edge" for T2), and
// the plan beeped without the Charge's draws. No state runs past a pending Charge, and no plan is made before it is in.
function fb14Advance(h) { if (FB14.pendChg) h = Math.min(h, FB14.pendChg.M + 10); for (const S of FB14.states) fbRun(S, h - S.l); }
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
  if (FB14.hit) { st.msg = 'No edge: Mario was hit on T' + FB14.hit + ' (the Life Shroom revive is not modelled, and it ends the route\'s dodge). ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; FB14.plan = { none: 'hit', turn }; fb14Show(); if (cAt == null) { cancelBeeps(); render(); } return true; }
  if (!FB14.on && cAt == null && (['capture', 'maps', 'search'].includes(CHG.state) || FB14.refining)) { st.msg = 'No beeps yet: the Charge rays are being read (about 3-5 s after the Charge). Wait on ' + (turn === 1 ? 'Cloud Nine\'s target (hand on Mario)' : 'Lakilester\'s Do Nothing') + ': the beeps, or "No edge", come as soon as the seed is read.'; FB14.plan = { none: 'reading', turn }; fb14Show(); render(); return true; }
  if (!FB14.on) { st.msg = 'No Final Bowser lock: ' + fb14BlindText(turn) + '.'; FB14.plan = { none: 'no lock', turn }; fb14Show(); if (cAt == null) render(); return true; }
  if (FB14.pendChg && cAt == null) { st.msg = 'No beeps yet: this turn\'s Charge rays are being read. Wait on ' + (turn === 1 ? 'Cloud Nine\'s target (hand on Mario)' : 'Lakilester\'s Do Nothing') + '.'; FB14.plan = { none: 'reading', turn }; fb14Show(); render(); return true; }
  const now = performance.now(), h = cAt != null ? cAt : fb14Horizon(now); fb14Advance(h);
  const Wg = fb14Weigh(h); FB14.doubt = Wg.doubt;
  // v76: every state ruled out = the carried seed is gone (an off-route turn: an item instead of Charge / Cloud Nine, an
  // unblocked attack, a Life Shroom; or a carry from an earlier attempt). Say so once and let the next Charge lock afresh
  // (log 1794071163309, attempt A: no edge at doubt 1 for the rest of the fight).
  if (!Wg.list.length && FB14.gone) { fb14CarryGone(); st.msg = 'The carried seed is gone: what the page saw since the last lock does not fit the route (an item or Life Shroom instead of Charge / Cloud Nine, an unblocked attack, or a lock from an earlier attempt). The next Super Charge locks again. ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; FB14.plan = { none: 'gone', turn }; fb14Show(); if (cAt == null) render(); return true; }
  if (!Wg.list.length || Wg.doubt >= 0.5) { st.msg = 'No edge: the coin no longer fits the Final Bowser lock (' + Math.round(100 * Wg.doubt) + '% none of the states is the game\'s). ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; FB14.plan = { none: 'doubt', turn, doubt: Wg.doubt }; slog('fb14NoEdge', { turn, doubt: +Wg.doubt.toFixed(3), states: Wg.list.length }); fb14Show(); if (cAt == null) { cancelBeeps(); render(); } return true; }
  const rate = fbRate(), W = Math.max(0, Math.round(num('zwwin') * 1000 / rate));
  let from = cAt != null ? Math.ceil(cAt + num('lead') * 1000 / rate + 1) : Math.max(h + 1, Math.ceil(fbPic(now) + 1));
  if (cAt == null) for (let i = 0; i < 600 && fbPressT(from) < earliestPress(now); i++) from++;
  const L = fb14Sample(Wg.list, 150), PD = cAt != null ? PRESS_ERR : pressDist(), D = Math.max(...PD.map(x => Math.abs(x[0]))), X = 10;
  const t1 = performance.now(), share = fb14Share(L, from - D, from + W + X + D, turn, fb14Kind(turn)), ms = Math.round(performance.now() - t1);
  const prof = { id: 'fb14', share: (a, b) => (a === from - D ? share : share.slice(a - (from - D), b - (from - D) + 1)) };
  const C = zwChoose(L, from, W, PD, prof, { d: Wg.doubt, b3: fb14Blind(turn), b4: 0 });
  if (C.none) { const pl = { none: C.none, turn, best: C.pp, spread: C.p }; FB14.plan = pl; if (cAt != null) return pl;
    st.msg = 'No edge: ' + Wg.list.length + ' possible states and no frame in the next ' + num('zwwin') + ' s works for enough of them with a perfect press (best ' + Math.round(100 * (C.pp || 0)) + '%). ' + fb14BlindText(turn)[0].toUpperCase() + fb14BlindText(turn).slice(1) + '.'; slog('fb14NoEdge', { turn, best: C.pp, spread: C.p }); cancelBeeps(); fb14Show(); render(); return true; }
  const pl = { turn, target: C.target, p: C.p, pp: C.pp, win: C.w.length, pStates: C.pStates, doubt: +Wg.doubt.toFixed(3), states: Wg.list.length, ms, from, W, w: C.w, tPress: fbPressT(C.target), blind: fb14Blind(turn) };
  FB14.plan = pl; if (cAt != null) return pl;
  const prev = FB14.prevPlan, same = prev && prev.target === C.target && Math.abs(prev.tPress - pl.tPress) < 5;   // v76: a replan on the same frame keeps the beeps already scheduled
  if (!same) { cancelBeeps(); playBeeps(pl.tPress); } else slog('fb14SameTarget', { target: C.target });
  const tLast = FB14.t0 + (fb14Bias() - 1.2) * rate - num('vlag');      // pressTime(tLast, rate, F) = fbPressT(F)
  const a = C.a, tab = []; for (let F = from - 30; F <= from + W + 30; F++) tab.push(F >= a && F <= C.b ? C.share[F - a] >= 0.5 : false);
  st.plan = { tMade: now, w: C.w, target: C.target, tPress: pl.tPress, tLast, rate, carried: true, from, to: from + W, first: from - 30, prof: 'fb14', tab, tab4: null, type: C.type, beeps: nBeeps(),
    mix: { p: C.p, pStates: C.pStates, pp: C.pp, ppStates: C.ppStates, win: C.w.length, doubt: pl.doubt, groups: Wg.list.length, zw: true, fb14: turn }, PD, zwAbs: C.target, fb14: turn, bias: fb14Bias() };
  st.msg = null; slog('fb14Plan', pl); fb14Show(); render(); return true;
}
/* about 4 times a second with a plan running: the coin may have moved the weights; a planned frame that no longer works
 * for enough of the states stops its beeps (and replans while the beeps still fit) */
function fb14Tick(t) {
  const P = st.plan; if (!P || !P.fb14 || P.stopped || P.tPress < performance.now() - 300) return;
  if (FB14.pendChg) return;
  const h = fb14Horizon(performance.now()); if (FB14.tickH === h) return; FB14.tickH = h;
  // v76: re-score exactly as the plan scored (log 1794071163309, Final Bowser T2: 37 plans in 9 s). The tick summed the press
  // spread over -1..+1 only, while the plan's pressDist() reaches -4..+4 (the runner's spread, sd ~1.5): every re-score read
  // ~0.6 of the plan's 0.93 and replanned the same frame every 250 ms, so the beeps never played through. Same states sample
  // (150), same press spread.
  fb14Advance(h); const Wg = fb14Weigh(h); FB14.doubt = Wg.doubt; const PDt = P.PD || PRESS_ERR, D = Math.max(...PDt.map(x => Math.abs(x[0]))), sh = fb14Share(fb14Sample(Wg.list, 150), P.target - D, P.target + D, P.fb14, fb14Kind(P.fb14));
  let v = 0; for (const [d, q] of PDt) v += q * (sh[d + D] || 0);
  // v83: the plan is a perfect press: re-scored on the planned frame itself (the spread-weighted chance only logged)
  const pS = (1 - Wg.doubt) * v + Wg.doubt * fb14Blind(P.fb14), p = P.mix.pp != null ? (1 - Wg.doubt) * (sh[D] || 0) + Wg.doubt * fb14Blind(P.fb14) : pS; P.mix.pNow = +p.toFixed(3); P.mix.pSpreadNow = +pS.toFixed(3);
  if (Wg.doubt < 0.5 && p >= num('zwedge') && p >= (P.mix.pp != null ? P.mix.pp : P.mix.p) - 0.15) return;
  if (P.tPress - (nBeeps() - 1) * num('gapms') > performance.now() + 200) { slog('fb14Replan', { from: P.target, p: +p.toFixed(3) }); FB14.prevPlan = P; st.plan = null; fb14Plan(); FB14.prevPlan = null; return; }
  cancelBeeps(); P.stopped = true; slog('beepsStopped', { from: P.target, why: 'fb14', p: +p.toFixed(3), doubt: +Wg.doubt.toFixed(3) });
  st.msg = 'Beeps stopped: the coin no longer supports the planned frame. ' + fb14BlindText(P.fb14)[0].toUpperCase() + fb14BlindText(P.fb14).slice(1) + '.'; render();
}
/* the step's screen closed: the partner's confirm (the lever), read off the video to about +-2 frames */
const FB14_SHIFTS = [[-2, 0.1], [-1, 0.25], [0, 0.4], [1, 0.2], [2, 0.05]];
const FB14_C9AFTER = 2500, FB14_C9HIDE = 2, FB14_C9SHIFTS = [[-2, 0.1], [-1, 0.2], [0, 0.35], [1, 0.25], [2, 0.1]];
function fb14Confirm(tObs, stp, shifts, src) {
  if (!stp || !stp.fb14) return;
  const turn = stp.fb14;
  if (stp.fb14role !== 'lever') return;
  if (turn === 4) FB14.p4t = tObs; FB14.pT = FB14.pT || {}; FB14.pT[turn] = tObs;
  if (FB14.t0 == null || !FB14.on) { FB14.pend = (FB14.pend || []).concat([{ tObs, turn, cat: stp.cat, shifts }]); slog('fb14ConfirmBeforeLock', { turn, src }); return; }   // the lock comes later: applied then
  const c = fbPic(tObs) - (FB14_VAN[stp.cat] || 2) - num('pfix'), F = Math.round(c);
  FB14.P[turn] = F; if (turn === 4) FB14.p4t = tObs; const P = st.plan && st.plan.fb14 === turn ? st.plan : null;
  slog('fb14Confirm', { turn, F, c: +c.toFixed(2), planned: P ? P.target : null, err: P ? +(c - P.target).toFixed(2) : null, src });
  if (P && !P.stopped && src !== 'bar' && Math.abs(c - P.target) <= 5) { const L = fb14PressAdd(c - P.target - (P.bias || 0)); slog('fb14PressBias', { n: L.length, bias: +fb14Bias().toFixed(2) }); }
  if (FB14.on) { const h = fb14Horizon(performance.now()); fb14Advance(Math.min(h, F - 3)); fb14Input(fb14Kind(turn), F, turn, shifts || FB14_SHIFTS, tObs, (FB14_VAN[stp.cat] || 2) + num('pfix')); }
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
  // v76 (console 2026-11-07 11:55, log 1794070564756): the route waited on T1's Charge step for the Mario target screen to
  // close, and that screen was never saved, so the step never moved: no Cloud Nine step, and the reader stayed 'locked'
  // through T2's Charge (no T2 lock, no Do Nothing plan). A Charge burst is proof enough of where the fight is: on T1's
  // Charge step it is that Charge (the route goes to the Cloud Nine step); on a lever step after that turn's lock it is
  // the next Charge (T2 / T4: the lever went by unseen, the route goes to that turn's step).
  { let s = fb14Step(); const t = CHG.trig ? CHG.trig.t : performance.now(), lb = FB14.lastBurst, c1 = RT().findIndex(x => x.fb14 === 1 && x.fb14role === 'charge');
    // a Charge this long after the last one is a new attempt (T1-T4's Charges are 20-60 s apart): the old carry goes
    // (log 1794071163309, attempt A: a T1 lock from the attempt 5 minutes before was still carried and every state died)
    if (s && lb && t - lb.t > FB14_NEWATTEMPT && c1 >= 0) { slog('fb14NewAttempt', { from: routeStep, after: Math.round(t - lb.t) }); fb14Reset('new attempt'); setStep(c1); s = fb14Step(); }
    // v86 (clip 15-24-14 fed to the page): a saved Mario target screen matched twice in T1's menus before the Charge, the
    // route ran on to T2's Do Nothing step, the T1 lock was taken as T2's and T2's Charge as T4's. The first burst of an
    // attempt with no lock yet is T1's Charge whatever step the screens moved the route to: back to Cloud Nine's step, and
    // the confirms read before it dropped (Cloud Nine comes after the Charge)
    const c1l = RT().findIndex(x => x.fb14 === 1 && x.fb14role === 'lever');
    if (s && s.fb14 > 1 && !FB14.on && FB14.t0 == null && !FB14.lastBurst && c1l >= 0) { slog('fb14StepToT1', { from: routeStep, pend: (FB14.pend || []).length }); FB14.pend = []; FB14.pT = {}; setStep(c1l); s = fb14Step(); }
    const lb2 = FB14.lastBurst;
    if (s && s.fb14role === 'charge') { slog('fb14StepByBurst', { from: routeStep, turn: s.fb14 }); setStep(routeStep + 1); }
    else if (s && s.fb14role === 'lever' && (!s.chg || (lb2 && lb2.turn === s.fb14 && t - lb2.t > FB14_NEXTCHG))) {
      const j = RT().findIndex((x, i) => i > routeStep && x.fb14 && x.fb14 > s.fb14 && x.chg === 'fb1');
      if (j >= 0) { slog('fb14StepByBurst', { from: routeStep, to: j, turn: RT()[j].fb14 }); setStep(j); }
    }
    const s2 = fb14Step(); if (s2) FB14.lastBurst = { turn: s2.fb14, t }; }
  const stp0 = fb14Step(); FB14.trigTurn = stp0 ? stp0.fb14 : null;
  if (FB14.t0 == null || !CHG.trig) return;
  const M = Math.round(fbPic(CHG.trig.t) - 16), stp = stp0, turn = stp ? stp.fb14 : null;
  if (turn === 2 || turn === 4) fb14TurnOver(turn);
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
/* v76: the carry is gone (every state ruled out): the tracker off and its clock dropped, so the next Charge's lock is a
 * fresh one (the reader is armed again if a lock left it 'locked') */
function fb14CarryGone() {
  if (!FB14.on && FB14.t0 == null) return;
  slog('fb14CarryGone', { turn: (fb14Step() || {}).fb14 || null });
  Object.assign(FB14, { on: false, t0: null, states: [], M: {}, P: {}, charges: [], gone: false, allOutLogged: false, why: 'the carried seed is gone (an off-route turn); the next Super Charge locks again' });
  if (typeof CHG !== 'undefined' && ['locked', 'nolock', 'failed'].includes(CHG.state)) chgReset();
}
/* v76: after a T1-T4 lock the reader arms again at once, so the next turn's Charge is read even when no target screen moved
 * the route (the burst then moves it, fb14Trigger). Only real bar hides arm it (bar up 0.6 s+), so Bowser's turn does not. */
function fb14AfterLock() {
  const s = fb14Step(); if (!s || FB14.refining || typeof CHG === 'undefined' || CHG.state !== 'locked') return;
  slog('fb14ReaderRearmed', { turn: s.fb14, why: 'after the lock' }); chgReset();
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
  el.innerHTML = '<b>FB2 T1 → T4</b> (' + FB14.states.length + ' RNG states, ' + (FB14.how === 'carried' ? 'the carried seed fits the last Charge' : 'from the last Charge') + ', seed confidence ' + pc(1 - (FB14.doubt || 0)) + ')' +
    (P && !P.none && P.turn ? '<br>T' + P.turn + ': ' + (P.turn === 1 ? 'Cloud Nine' : 'Do Nothing') + ' on the beep (+' + P.target + '): ' + fb14Goal(P.turn) + '. ' + ppText({ pp: P.pp, ppStates: P.pp != null ? (P.pp - P.doubt * P.blind) / Math.max(1e-9, 1 - P.doubt) : null, win: P.win, p: P.p, doubt: P.doubt }, 'fb14') + ' (blind ' + pc(P.blind) + '; with your press spread ' + pc(P.p) + ')' : P && P.none ? '<br>T' + P.turn + ': no edge (' + P.none + '): ' + fb14BlindText(P.turn) : '') +
    '<br>Lever beeps ' + (fb14Bias() >= 0 ? 'later' : 'earlier') + ' by ' + Math.abs(fb14Bias()).toFixed(1) + ' frames: your Final Bowser lever presses so far came ' + (-fb14Bias()).toFixed(1) + ' frames off on average (last ' + fb14PressList().length + ').' + (FB14.t6 ? '<br>T6: the Charge is searched on the carried stream (' + FB14.t6.bases.length + ' seeds at the Peach Beam)' : '');
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
    res.placeScores = sc;
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
async function fb1Stage2(W, call, top, times, t3, narrow) {
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
  // v87: on the carried stream (T2 / T4 narrowed) the fits are kept wider: the carried states pick among them
  const hy = all.length ? await call(W[0], { type: 'fb1h', s0: all[0].seed, tol: narrow ? FB14_NTOL : FB14_TOL, max: narrow ? 20000 : 4000 }, 'fb1h') : null;
  times.hyps = Math.round(performance.now() - t4);
  return { top: all.slice(0, 5), fb1: { hyps: hy, times } };
}
window.__fb14 = { FB14, FB14_DELTA, FB14_JELLY, FB14_MAXH, FB14_CHGD, cap: L => fb14Cap(L), held: () => fb14Held(), chgCands: () => fb14ChgCands(), waveSplit: L => fb14WaveSplit(L), fbVars, trigger: () => fb14Trigger(), advance: h => fb14Advance(h), turnOver: k => fb14TurnOver(k), hpWatch: (t, pr) => fb14HpWatch(t, pr), fbStep, fbRun, fbClone, fbRi, fbAdv, plan: c => fb14Plan(c), weigh: h => fb14Weigh(h), input: (k, F, turn, sh) => fb14Input(k, F, turn, sh), lock: r => fb14Lock(r), reset: () => fb14Reset(), confirm: (t, s) => fb14Confirm(t, s), pic: t => fbPic(t), pressT: F => fbPressT(F), bias: () => fb14Bias(), pressAdd: e => fb14PressAdd(e), t6cands: () => fb14T6Cands(), peach: () => fb14Peach(), fbNew: o => fbNew(o),
  share: (h, a, b, turn) => { fb14Advance(h); const W = fb14Weigh(h); return { doubt: W.doubt, n: W.list.length, share: Array.from(fb14Share(fb14Sample(W.list, 300), a, b, turn, fb14Kind(turn))) }; },
  sample: (b, w, h) => sample(b, w, h), tick: t => { FB14.tickH = null; fb14Tick(t); }, carryGone: () => fb14CarryGone(), reloadTargets: () => { targets = JSON.parse(localStorage.getItem('tot-targets') || '{}'); useTarget(); } };   // for tests
