/* Zero-wait Time Out simulation: what P(Time Out) does a runner get when the page only sees the coin during time the run
 * spends anyway (no standing), and the page picks the confirm frame that is best over whatever candidates remain?
 *
 * Timeline (game frames), all generated with the real LCG:
 *   walk after Jr. Troopa (clean rooms, C-up re-pressed: looks of ~220 frames, dropouts, room loads with 0-6 frames of
 *   console lag, item-get messages) -> hallway scene + battle intro, coin hidden (H frames; X extra RNG steps at random
 *   frames, measured 55-110 depending on A pace) -> T1 menu visible m1 frames -> Charge + Spiny Flip (impact 138..170,
 *   guard or not; Bowser's AI and attack draws: R.buildEv / R.frameEv) -> T2 menu visible m2 frames -> target screen ready ->
 *   confirm frame chosen in [ready + LEAD, ready + LEAD + WMAX] -> Time Out roll (R.works, the verified profile).
 *
 * What the page knows: every visible shine / non-shine (shines count after the coin is steady 30 frames; draws in the
 * last 4 visible frames are not seen), the frame clock (room loads add 0-6 unknown frames), the confirm frames of its
 * own turns. Unknown: the seed, load lags, the scene's extra steps X and hidden length (+-), impact frame, guard.
 *
 * Page model:
 *  1. Walk: evidence bits B (pattern bits + look-edge non-shines - gap costs, as the page counts them). Wrong
 *     trajectories that fit the walk are random seeds; their expected number is 2^(32 - B). If that exceeds CAP the page
 *     carries nothing (diffuse). Otherwise candidates = the true one (if the model held) + Poisson decoys.
 *  2. After the scene: each candidate is re-synced by R.resync over the step range the scene allows (frames +-, coin
 *     draws, X in [XLO, XHI]), anchored at the first shine seen in the T1 menu (no shine there: the T2 menu, with the T1
 *     turn's steps folded into a wider range).
 *  3. T1: every surviving hypothesis x 66 Spiny Flip candidates, simulated; T2 menu draws filter them; same RNG state = merged.
 *  4. Choose the confirm frame maximising sum_k w_k * sum_d press(d) * works_k(f + d). If there are no candidates, or
 *     the best score is under EDGE, the page says "no edge, press normally" and the runner confirms at `ready`.
 * Realised success = the true trajectory's works() at the chosen frame, averaged over the press error.
 *
 * usage: node zw_sim.js RUNS [key=value ...]   e.g. node zw_sim.js 100 WALK=45 ERR=none */
const R = require('../pmrng_core.js');
const A = Object.fromEntries(process.argv.slice(3).map(x => x.split('=')).map(([k, v]) => [k, isNaN(+v) ? v : +v]));
const RUNS = +process.argv[2] || 50;
const P = Object.assign({ WALK: 45, M1: 60, M2: 60, LEAD: 15, WMAX: 30, CAP: 64, EDGE: 0.40, XLO: 45, XHI: 125, XT_LO: 55, XT_HI: 110,
  HID: 650, GUARD: 'unknown', ERR: 'none', SEED: 1, PRESS: 'normal' }, A);
const FR = 30;                                   // frames per second (game frames ~ 29.97)
const BITS_S = -Math.log2(310 / 1010), BITS_N = -Math.log2(700 / 1010);
let rs = (P.SEED * 2654435761) >>> 0; const rnd = () => ((rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296);
const ri = (a, b) => a + Math.floor(rnd() * (b - a + 1));
function poisson(l) { if (l > 50) return Math.max(0, Math.round(l + Math.sqrt(l) * gauss())); let L = Math.exp(-l), k = 0, p = 1; do { k++; p *= rnd(); } while (p > L); return k - 1; }
function gauss() { return Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd()); }
const PRESS = P.PRESS === 'wide' ? [[-2, 0.1], [-1, 0.2], [0, 0.4], [1, 0.2], [2, 0.1]] : P.PRESS === 'exact' ? [[0, 1]] : [[-1, 0.25], [0, 0.5], [1, 0.25]];

/* plain coin process: S = {s: seed before frame f's draws, nc}; extra: Map frame -> steps (script phase) */
function plainFrame(S, f, extra) {
  const x = extra && extra.get(f); if (x) for (let i = 0; i < x; i++) S.s = R.adv(S.s);
  let r = null; if (f === S.nc) { const q = R.randInt(S.s, 100); S.s = q[0]; r = q[1] >= 70; S.nc = f + (r ? 48 : 24); }
  S.s = R.adv(S.s); return r;
}

function oneRun() {
  /* ---------- truth ---------- */
  const s0 = (rnd() * 4294967296) >>> 0; const T = { s: s0, nc: ri(0, 23) };
  const WALKF = Math.round(P.WALK * FR);
  // looks: [a, b) visible; gaps: plain dropout / room load / item message
  const looks = []; let f = 0, lag = 0; const gaps = [];
  while (f < WALKF) {
    const a = f, b = Math.min(WALKF, f + 220); looks.push([a, b]); f = b; if (f >= WALKF) break;
    const u = rnd(); let hid, kind, l = 0;
    if (u < 0.5) { hid = ri(18, 35); kind = 'drop'; } else if (u < 0.9) { hid = ri(45, 75); kind = 'load'; l = ri(0, 6); } else { hid = ri(55, 70); kind = 'item'; }
    gaps.push({ kind, hid, l }); f += hid;
  }
  const draws = [];                                  // {f, sh, before}
  const runTo = (S, from, to, extra, ev) => { for (let g = from; g < to; g++) { const before = S.s, isDraw = g === S.nc; const r = ev ? R.frameEv(S, g, ev) : plainFrame(S, g, extra); if (isDraw) draws.push({ f: g, sh: r, before }); } };
  runTo(T, 0, WALKF);
  // scene: hidden HID +-60 frames, X extra steps spread over it
  const H = P.HID + ri(-60, 60), X = P.ERR === 'scene_x' ? P.XHI + ri(10, 40) : ri(P.XT_LO, P.XT_HI);
  const extra = new Map(); for (let i = 0; i < X; i++) { const g = WALKF + ri(30, H - 30); extra.set(g, (extra.get(g) || 0) + 1); }
  runTo(T, WALKF, WALKF + H, extra);
  const m1a = WALKF + H, m1b = m1a + P.M1;
  runTo(T, m1a, m1b);
  // T1: Charge confirm at m1b, Spiny Flip confirm 260 later (frames the page reads from the video)
  const cF = m1b, sF = m1b + 260;
  let imp = ri(138, 170), guard = rnd() < 0.7; if (P.ERR === 'impact') imp = 175;
  const evOf = (im, gd) => R.buildEv([{ f: cF, id: 'hw_charge' }, { f: sF, id: 'hw_spiny', imp: im, guard: gd }]);
  const evT = evOf(imp, guard);
  if (P.ERR === 'turn_steps') { const g = sF + 200; const e = evT.get(g) || { pre: [], post: [], eio: [] }; e.pre.push(...Array(ri(1, 5)).fill(359)); evT.set(g, e); }
  const Sx = { s: T.s, nc: T.nc, inst: [] };
  // run the turns until all events are done and a coin draw frame comes (T2 menu opens there)
  let g = m1b; const lastEv = Math.max(...evT.keys()) + 300;
  for (; g < lastEv || g !== Sx.nc || Sx.inst.length || (Sx.extra && Sx.extra.size); g++) { const before = Sx.s, isDraw = g === Sx.nc; const r = R.frameEv(Sx, g, evT); if (isDraw) draws.push({ f: g, sh: r, before }); if (g > lastEv + 2000) break; }
  const m2a = g, m2b = m2a + P.M2; const T2 = { s: Sx.s, nc: Sx.nc };
  runTo(T2, m2a, m2b - 5); const stateReady = { s: T2.s, nc: T2.nc, f: m2b - 5 }; runTo(T2, m2b - 5, m2b);
  const ready = m2b;
  const worksAt = (st, c) => R.works(st.s, st.nc, c, st.f);

  /* ---------- what the page sees ---------- */
  const visible = (lo, hi) => draws.filter(d => d.f >= lo + 30 && d.f < hi - 4);
  // walk evidence (page-style): per look the pattern first tap..last tap, up to 4 non-shine edges each side; gap costs
  let B = 0, nTaps = 0;
  const walkLooks = looks.map(([a, b]) => visible(a, b));
  const errDraw = P.ERR === 'walk_miss' || P.ERR === 'walk_false';
  walkLooks.forEach((v, i) => {
    const taps = v.filter(d => d.sh); nTaps += taps.length;
    if (taps.length) { const i0 = v.indexOf(taps[0]), i1 = v.indexOf(taps[taps.length - 1]);
      for (let k = i0; k <= i1; k++) B += v[k].sh ? BITS_S : BITS_N;
      B += (Math.min(4, i0) + Math.min(4, v.length - 1 - i1)) * BITS_N; }
    else B += Math.min(4, v.length) * BITS_N;
    if (i) { const gp = gaps[i - 1]; const hidS = gp.hid / FR; B -= hidS <= 1.2 ? Math.log2(14 / 24 + 1) : hidS <= 3.5 ? Math.log2(22 / 24 + 1) : Math.log2(90 / 24 + 1); }
  });
  B -= 0;  // the first tapped shine anchors the start (no alignment cost)
  const lastWalk = [...walkLooks].reverse().find(v => v.length); const anchor = lastWalk[lastWalk.length - 1];   // last visible walk draw
  // decoys and whether the truth is among the walk candidates
  const lam = Math.pow(2, 32 - B);
  const truthIn = !errDraw; let walkCands = null;
  if (lam <= P.CAP) { const D = poisson(lam); walkCands = []; if (truthIn) walkCands.push(anchor.before); for (let i = 0; i < D; i++) walkCands.push((rnd() * 4294967296) >>> 0); }

  /* ---------- page: resync after the scene ---------- */
  const out = { B: +B.toFixed(1), lam, walkK: walkCands ? walkCands.length : null, X, imp, guard };
  const blind = PRESS.reduce((a, [d, p]) => a + p * (worksAt(stateReady, ready + d) ? 1 : 0), 0);
  out.blind = blind;
  const finish = (cands, why) => {           // cands: [{st:{s,nc,f}, w}]
    if (!cands || !cands.length) { out.mode = why || 'no candidates'; out.P = blind; out.shown = null; out.delay = 0; return out; }
    const W = P.WMAX, f0 = ready + P.LEAD; const tw = cands.reduce((a, c) => a + c.w, 0);
    let best = -1, bf = f0; const tabs = cands.map(c => { const t = []; for (let k = -2; k <= W + 2; k++) t.push(worksAt(c.st, f0 + k) ? 1 : 0); return t; });
    for (let k = 0; k <= W; k++) { let sc = 0; cands.forEach((c, i) => { for (const [d, p] of PRESS) sc += c.w * p * tabs[i][k + d + 2]; }); sc /= tw; if (sc > best + 1e-9) { best = sc; bf = f0 + k; } }
    out.shown = +best.toFixed(3); out.K = cands.length;
    if (best < P.EDGE) { out.mode = 'no edge (score ' + best.toFixed(2) + ')'; out.P = blind; out.delay = 0; return out; }
    out.mode = 'beep'; out.delay = bf - ready; out.P = PRESS.reduce((a, [d, p]) => a + p * (worksAt(stateReady, bf + d) ? 1 : 0), 0); return out;
  };
  if (!walkCands) return finish(null, 'diffuse walk (2^' + Math.log2(lam).toFixed(1) + ' fits)');
  if (!walkCands.length) return finish(null, 'no seed fits the walk');
  // anchor: candidates are seeds before the last walk draw at frame anchor.f; one draw then plain to the scene
  const v1 = visible(m1a, m1b), taps1 = v1.filter(d => d.sh);
  const v2 = visible(m2a, m2b);
  const hidE = m1a - anchor.f;                         // what the clock says (no load inside the scene here)
  const nDrawsLo = Math.floor(hidE / 48), nDrawsHi = Math.ceil(hidE / 24) + 1;
  if (taps1.length) {
    const t0 = taps1[0]; const pat = v1.slice(v1.indexOf(t0)).map(d => d.sh ? 'S' : '.').join('');
    const span = t0.f - anchor.f;                      // frames from the anchor draw to the first T1-menu tap
    const nlo = span - 20 + nDrawsLo + P.XLO, nhi = span + 8 + nDrawsHi + P.XHI;
    let hyps = [];
    for (const c of walkCands) {
      const a2 = R.randInt(c, 100)[0];                     // seed after the anchor draw
      for (const r of R.resync(a2, pat, nhi, 4096, nlo)) hyps.push(r.seed);
    }
    out.h1 = hyps.length;
    if (!hyps.length) return finish(null, 'inconsistent after the scene (no hypothesis fits the T1 menu)');
    if (hyps.length > 512) return finish(null, 'diffuse after the scene (' + hyps.length + ')');
    // forward through T1 with the 66 Spiny candidates; filter by the T2 menu's draws; merge same states
    const gks = P.GUARD === 'known' ? [guard] : [true, false];
    const groups = new Map();
    for (const hs of hyps) for (let im = 138; im <= 170; im++) for (const gd of gks) {
      const ev = evOf(im, gd); const S = { s: hs >>> 0, nc: t0.f, inst: [] }; let ok = true, gg = t0.f;
      for (; gg < m2a; gg++) R.frameEv(S, gg, ev);
      if (S.nc < m2a || S.inst.length || (S.extra && S.extra.size)) ok = false;   // turn not over by the time the truth's menu opens
      if (!ok) continue;
      const S2 = { s: S.s, nc: S.nc }; let seen = 0;
      let Sm = null;
      for (gg = m2a; gg < m2b; gg++) { if (gg === m2b - 5) Sm = { s: S2.s, nc: S2.nc }; const isD = gg === S2.nc; const r = plainFrame(S2, gg); if (isD && gg >= m2a + 30 && gg < m2b - 4) { seen++; const td = v2.find(d => d.f === gg); if (!td || td.sh !== r) { ok = false; break; } } }
      if (!ok || seen !== v2.length) continue;           // same draws seen, same outcomes
      const k = S2.s + ':' + S2.nc; const gr = groups.get(k); if (gr) gr.w++; else groups.set(k, { st: { s: Sm.s, nc: Sm.nc, f: m2b - 5 }, w: 1 });
    }
    // drop groups whose draws do not cover every visible truth draw (checked above only one way)
    out.groups = groups.size;
    if (!groups.size) return finish(null, 'inconsistent in T2 (no candidate fits)');
    return finish([...groups.values()]);
  }
  // no shine in the T1 menu: re-sync at the first shine in the T2 menu over a wider step range (scene + the T1 turn,
  // whose steps beyond 1/frame are 206..256 in the model: Charge sparkles, Spiny Flip impact, Bowser's attack)
  const taps2 = v2.filter(d => d.sh);
  if (!taps2.length) return finish(null, 'no shine in either battle menu (not re-synced)');
  { const t0 = taps2[0]; const pat = v2.slice(v2.indexOf(t0)).map(d => d.sh ? 'S' : '.').join('');
    const span = t0.f - anchor.f, dlo = Math.floor(span / 48), dhi = Math.ceil(span / 24) + 1;
    const nlo = span - 20 + dlo + P.XLO + 200, nhi = span + 8 + dhi + P.XHI + 265;
    const groups = new Map();
    for (const c of walkCands) for (const r of R.resync(R.randInt(c, 100)[0], pat, nhi, 4096, nlo)) {
      const S2 = { s: r.seed, nc: t0.f }; for (let gg = t0.f; gg < m2b - 5; gg++) plainFrame(S2, gg);
      const k = S2.s + ':' + S2.nc; const gr = groups.get(k); if (gr) gr.w++; else groups.set(k, { st: { s: S2.s, nc: S2.nc, f: m2b - 5 }, w: 1 });
    }
    out.groups = groups.size; out.path = 'T2';
    if (!groups.size) return finish(null, 'inconsistent in T2 (no candidate fits)');
    if (groups.size > 512) return finish(null, 'diffuse in T2 (' + groups.size + ')');
    return finish([...groups.values()]); }
}

const res = []; for (let i = 0; i < RUNS; i++) res.push(oneRun());
const Ps = res.map(r => r.P).sort((a, b) => a - b), q = p => Ps[Math.min(Ps.length - 1, Math.floor(p * Ps.length))];
const mean = a => a.reduce((x, y) => x + y, 0) / (a.length || 1);
const beeps = res.filter(r => r.mode === 'beep'), modes = {};
for (const r of res) { const m = r.mode.replace(/\(.*\)/, '').trim(); modes[m] = (modes[m] || 0) + 1; }
console.log(JSON.stringify(P));
console.log('runs', RUNS, '| mean P(Time Out)', mean(Ps).toFixed(3), '| blind (same runs)', mean(res.map(r => r.blind)).toFixed(3),
  '| quartiles', [q(0.1), q(0.25), q(0.5), q(0.75), q(0.9)].map(x => x.toFixed(2)).join(' '));
console.log('beeped', beeps.length, '| mean shown P when beeped', mean(beeps.map(r => r.shown)).toFixed(3), '| realised when beeped', mean(beeps.map(r => r.P)).toFixed(3),
  '| mean delay (frames)', mean(beeps.map(r => r.delay)).toFixed(1), '| walk bits median', res.map(r => r.B).sort((a, b) => a - b)[RUNS >> 1]);
console.log('modes', JSON.stringify(modes));
if (A.V) for (const r of res) console.log(JSON.stringify(r));
