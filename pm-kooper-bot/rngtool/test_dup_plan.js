/* Duplighosts, Charge-lock route (v71): the route option, the lock -> plan model, the no-lock text, leaving the step, and
 * the arena check on real console frames. Through the built standalone page in headless Chromium.
 *  1. Route selector: RTA (default, the turn as before) vs Charge lock (step 0 becomes the Do Nothing step with the dup
 *     Charge profile); both routes have the same steps after the Duplighosts.
 *  2. Model: dup_charge/plan_cases.json (dc_fixture.py, from the emulator-checked dc_model.py: dc_check.py matched 60/60
 *     emulator runs frame by frame). Per case the page's tracker is started as a Charge lock starts it (seed and first
 *     coin q at the rays' frame 0, console lag 0 / 1 after the rays), and
 *       - the copies the page predicts for Do Nothing on every clock frame 117..316 (lag 0) and 118..317 (lag 1) must equal
 *         the model's on the same game frame (all of them, every case);
 *       - the plan (Strategies screen on clock frame 150, lead 1.5 s, max extra wait 1 s, best chance) is scored against the
 *         model with the press 1 frame early 25%, on time 50%, late 25%, for the true lag 0: 3+ and 4 copies, against the
 *         page's own claim and the blind 47% / 13%.
 *  3. No lock on the Charge-lock step: Plan press says to play it blind (47%); the Charge panel says so too.
 *  4. Leaving the step (the Do Nothing confirm moves the route on) turns the tracker off, so the Hallway's walk tracker
 *     can start; switching back to RTA drops the Charge step.
 *  5. Arena (chgArena, the colour boxes at a bar hide) on real 1280x720 console frames when the clips are here: the
 *     Duplighost fight (aad978a3, the Surge route: same room and camera), two Hallway clips, the FB2 clip.
 * usage (from rngtool/, after python3 build_page.py): node test_dup_plan.js [PAGE] */
'use strict';
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'dup_charge', 'plan_cases.json'), 'utf8'));
const U = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887/';
const ARENA = [['dup', 'aad978a3-2026-11-02_14-44-21.mkv', [0, 120, 504]], ['hw', '63e6e3da-2026-11-02_15-15-06.mkv', [240, 360, 960]],
  ['hw', '70665d2d-2026-11-03_20-53-09.mkv', [330, 720]], ['fb', '6c9e1375-2026-11-02_14-47-09.mkv', [600, 870]]];
function frames() {     // [[expected arena, clip, frame, png base64]] for the clips that are here
  const out = [];
  for (const [want, clip, fs_] of ARENA) {
    if (!fs.existsSync(U + clip)) { console.log('(no clip ' + clip + ': its arena frames are skipped)'); continue; }
    for (const n of fs_) {
      const png = execFileSync('ffmpeg', ['-v', 'error', '-i', U + clip, '-vf', 'select=eq(n\\,' + n + ')', '-vsync', '0', '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], { maxBuffer: 64 << 20 });
      out.push([want, clip.slice(0, 8), n, png.toString('base64')]);
    }
  }
  return out;
}
(async () => {
  let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
  const b = await chromium.launch(), p = await b.newPage(), errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { localStorage.clear(); });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(async ({ FIX }) => {
    const T = window.__tot, sel = document.getElementById('s-duproute'), out = { version: T.VERSION };
    const setRoute = v => { sel.value = v; sel.dispatchEvent(new Event('change')); };
    // 1. the route option
    out.rta = { route: T.dupRoute(), step0: T.RT()[0].label, chg: T.RT()[0].chg || null, n: T.RT().length };
    setRoute('charge'); T.setStep(0);
    out.charge = { route: T.dupRoute(), step0: T.RT()[0].label, chg: T.RT()[0].chg || null, n: T.RT().length, prof: (T.chgProfNow() || {}).id,
      list: document.getElementById('route-list').innerText.slice(0, 400), note: document.getElementById('duproute-note').textContent };
    // 2. the model
    const res = [], cScr = 150, lo = 117, hi = 316;
    for (const c of FIX.cases) {
      T.setStep(0); const ok = T.dupTrackerAt(parseInt(c.seed, 16), [c.q], performance.now() - 2000);
      const byW = T.dupStatesAt(100).sort((x, y) => y.w - x.w), pl = T.dupPlanAt(cScr, 1.5, 1);
      const cls = byW.map(q => T.dupClasses(q.s, q.nc, q.g, lo, hi + 1).join(''));
      res.push({ ok, states: byW.length, w: byW.map(q => +q.w.toFixed(3)), g: byW.map(q => q.g), cls, target: pl.target, p3: pl.p3, p4: pl.p4, none: pl.none, from: pl.from, W: pl.W });
    }
    out.model = res;
    // 4. leaving the step
    T.setStep(0); T.dupTrackerAt(parseInt(FIX.cases[0].seed, 16), [FIX.cases[0].q], performance.now() - 2000);
    const on0 = T.zw.on; T.setStep(1); out.leave = { before: on0, after: T.zw.on, step: T.step() };
    // 3. no lock
    T.setStep(0); T.chgReset(); Object.assign(T.CHG, { state: 'nolock', why: 'no clear seed (best 1500, 1.05x the next)', prof: T.CHG_PROF.dup }); T.st.plan = null; T.makePlan();
    out.nolock = { msg: T.st.msg, panel: (() => { const el = document.getElementById('chg-status'); return el ? el.innerText : ''; })() };
    T.CHG.state = 'idle'; T.st.msg = null; T.makePlan(); out.noCharge = T.st.msg;
    setRoute('rta'); out.back = { chg: T.RT()[0].chg || null, prof: T.chgProfNow() && T.chgProfNow().id };
    return out;
  }, { FIX });
  console.log('version ' + r.version + ' | RTA step 0: ' + r.rta.step0 + ' | Charge step 0: ' + r.charge.step0 + ' (profile ' + r.charge.prof + ')');
  check(r.version === 'v78', 'version v78');
  check(r.rta.route === 'rta' && !r.rta.chg, 'RTA is the default and its step has no Charge profile');
  check(r.charge.route === 'charge' && r.charge.chg === 'dup' && r.charge.prof === 'dup' && r.charge.n === r.rta.n, 'Charge-lock route: step 0 has the dup profile, same number of steps');
  check(/Charge; Bombette Do Nothing/i.test(r.charge.list) && /Power Bomb/i.test(r.charge.list), 'route list shows the Charge-lock turns');
  // 2. model checks
  let exact = 0, frames_ = 0, bad = [], real3 = 0, real4 = 0, cl3 = 0, cl4 = 0, n = 0, waits = [];
  r.model.forEach((m, i) => {
    const c = FIX.cases[i], idx = (clk, lag) => clk + FIX.clock0 - lag - c.D0;
    if (!m.ok || m.states !== 2 || m.w[0] !== 0.75) { bad.push(i + ': tracker ' + JSON.stringify({ ok: m.ok, states: m.states, w: m.w })); return; }
    for (let lag = 0; lag <= 1; lag++) for (let k = 0; k < m.cls[lag].length; k++) {
      const want = c.copies[idx(117 + k, lag)]; if (want == null) continue; frames_++;
      if (want === m.cls[lag][k]) exact++; else if (bad.length < 8) bad.push(i + ' lag ' + lag + ' clock ' + (117 + k) + ': page ' + m.cls[lag][k] + ' model ' + want);
    }
    if (m.none || m.target == null) { bad.push(i + ': no plan (' + m.none + ')'); return; }
    let p3 = 0, p4 = 0; for (const [d, q] of [[-1, 0.25], [0, 0.5], [1, 0.25]]) { const v = +c.copies[idx(m.target + d, 0)]; if (v >= 3) p3 += q; if (v === 4) p4 += q; }
    real3 += p3; real4 += p4; cl3 += m.p3; cl4 += m.p4; n++; waits.push(m.target - m.from);
  });
  console.log('copies predicted: ' + exact + ' / ' + frames_ + ' frames equal the model (2 lags x ' + r.model.length + ' cases)');
  console.log('plans: ' + n + ' | true lag 0, press 25/50/25 over -1/0/+1: 3+ ' + (100 * real3 / n).toFixed(1) + '%, all 4 ' + (100 * real4 / n).toFixed(1) + '% | the page claimed (lag 0/1 mix): 3+ ' + (100 * cl3 / n).toFixed(1) + '%, all 4 ' + (100 * cl4 / n).toFixed(1) + '% | blind 47% / 13% | wait into the window: mean ' + (waits.reduce((a, x) => a + x, 0) / n).toFixed(1) + ' frames');
  bad.slice(0, 8).forEach(x => console.log('  ' + x));
  check(frames_ >= 40 * 2 * 190 && exact === frames_, 'every predicted copy count equals the model');
  check(n === FIX.cases.length, 'a plan for every case');
  check(real3 / n >= 0.9 && real4 / n >= 0.25, '3+ at least 90% and 4 at least 25% with +-1 presses (dc_odds.py, a 30-frame window, safe3: 97.3% / 44.6%; here the console-lag-1 state shares the choice: 400 model cases 95.5% / 34.9%)');
  check(Math.abs(real3 - cl3) / n < 0.1, 'the claimed 3+ chance is within 10 points of the model on average');
  console.log('leave: ' + JSON.stringify(r.leave) + ' | no lock: ' + (r.nolock.msg || '').slice(0, 120));
  check(r.leave.before && !r.leave.after && r.leave.step === 1, 'leaving the Duplighost step turns its tracker off');
  check(/^No Charge lock/.test(r.nolock.msg || '') && /play it blind/.test(r.nolock.msg) && /47%/.test(r.nolock.msg), 'no lock: play it blind, 47%');
  check(/play it blind/.test(r.nolock.panel) && /47%/.test(r.nolock.panel), 'the Charge panel says play it blind');
  check(/^No Charge lock/.test(r.noCharge || '') && /47%/.test(r.noCharge), 'no Charge seen: play it blind');
  check(!r.back.chg && r.back.prof == null, 'back on RTA: no Charge step');
  // 5. arena on console frames
  const F = frames();
  if (F.length) {
    const ar = await p.evaluate(async F => {
      const T = window.__tot, out = [];
      for (const [want, clip, n, b64] of F) {
        const blob = await (await fetch('data:image/png;base64,' + b64)).blob(), bm = await createImageBitmap(blob), vf = new VideoFrame(bm, { timestamp: 0 }); bm.close();
        T.V.src = vf; let a; try { a = T.chgArena(); } finally { T.V.src = null; vf.close(); }
        out.push({ want, clip, n, got: a.a, L: a.L, br: a.br, lbr: a.lbr });
      }
      return out;
    }, F);
    ar.forEach(x => { console.log('arena ' + x.clip + ' #' + x.n + ': ' + x.got + ' (want ' + x.want + '; L ' + x.L + ', top B-R ' + x.br + ', floor B-R ' + x.lbr + ')'); check(x.got === x.want, 'arena ' + x.clip + ' #' + x.n); });
  }
  check(!errs.length, 'page errors: ' + errs.slice(0, 3).join(' | '));
  console.log(fails ? fails + ' FAILED' : 'all passed'); await b.close(); process.exit(fails ? 1 : 0);
})();
