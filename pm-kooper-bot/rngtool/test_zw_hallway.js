/* Zero-wait Hallway Bowser through the page (zerowait/README.md): the walk after Jr. Troopa gives a lock from one look,
 * then the coin is gone through the hallway scene (B held: 124 x rand_int(15) on the measured frames) and the battle
 * intro, with a console lag of L frames before the scene; the bar comes back in battle 450 frames after the scene
 * starts. T1's menu shows the coin for M1 frames, Charge and Spiny Flip are confirmed (impact frame and guard hidden),
 * T2's menu shows it for M2 frames, then the page plans on Time Out's target screen. The game is simulated
 * independently here (clock frames, the lag as frames with no game step); the press lands 1 frame early 25%, on the
 * frame 50%, 1 late 25%. Reports P(Time Out) against a blind press on reaching the target screen, the beep rate and
 * shown vs real. usage: node test_zw_hallway.js [N] [ERR] [LOOK seconds]
 * ERR: none | miss (one T1-menu shine not seen) | false (an extra shine) | lag (12 frames, outside the model) |
 *      scene (20 extra draws in the scene: text not held with B) | turn (3 unmodelled draws in T1) */
const { chromium } = require('playwright');
(async () => {
  const N = +process.argv[2] || 20, ERR = process.argv[3] || 'none', LOOK = +process.argv[4] || 60;
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  let rs = 4242; const rnd = () => ((rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296);
  const sum = { real: 0, blind: 0, n: 0, beeps: 0, shown: 0, realB: 0, modes: {} };
  for (let i = 0; i < N; i++) {
    const cfg = { seed0: (rnd() * 4294967296) >>> 0, L: ERR === 'lag' ? 12 : Math.floor(rnd() * 7), imp: 138 + Math.floor(rnd() * 33), guard: rnd() < 0.7,
      M1: 150, M2: 90, ERR, LOOK, nc0: Math.floor(rnd() * 24), walkIn: 60 + Math.floor(rnd() * 60) };
    const out = await p.evaluate(async (cfg) => {
      const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
      document.getElementById('s-zwwin').value = '1'; document.getElementById('s-zwedge').value = '0.4'; document.getElementById('s-lead').value = '0.5';
      document.getElementById('reset').click();
      const vlag = num('vlag'), pfix = num('pfix'), T0 = performance.now() + 1000;
      const setNow = c => { window.__dt += T0 + c * FR - performance.now(); };
      const wait = async c => { for (let i = 0; i < 900 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      const SCENE = { 138: 7, 139: 11, 140: 12, 141: 2, 147: 10, 152: 12, 153: 11, 158: 12, 159: 10, 199: 5, 286: 12, 287: 12, 288: 8 };
      // ---- the game, in clock frames ----
      const LOOKF = Math.round(cfg.LOOK * 30), sceneC = LOOKF + cfg.walkIn + cfg.L, Fup = sceneC + 450;
      const cC = Fup + cfg.M1, cS = cC + 260, m2a = cS + 760, m2b = m2a + cfg.M2;
      const evs = [{ f: cC, id: 'hw_charge' }, { f: cS, id: 'hw_spiny', imp: cfg.imp, guard: cfg.guard }];
      const ev = R.buildEv(evs);
      for (const o in SCENE) { const e = ev.get(sceneC + +o) || { pre: [], post: [], eio: [] }; e.pre.push(...Array(SCENE[o] + (cfg.ERR === 'scene' && o === '199' ? 20 : 0)).fill(15)); ev.set(sceneC + +o, e); }
      if (cfg.ERR === 'turn') { const e = ev.get(cS + 200) || { pre: [], post: [], eio: [] }; e.pre.push(359, 359, 359); ev.set(cS + 200, e); }
      const S = { s: cfg.seed0, nc: cfg.nc0, inst: [] }, shines = []; let state = null;
      for (let c = 0; c < m2b + 600; c++) {
        if (c >= sceneC - cfg.L && c < sceneC) { S.nc++; continue; }          // console lag: no game frame
        if (c === m2b - 5) state = { s: S.s, nc: S.nc, f: c };
        const r = R.frameEv(S, c, ev); if (r) shines.push(c);
      }
      const visible = (a, z) => shines.filter(c => c >= a && c < z);
      const tap = c => T.addShine(T0 + (c + 6) * FR + vlag, true);
      // ---- walk: one look of LOOK s, then the coin is gone ----
      for (const c of visible(30, LOOKF - 4)) { setNow(c + 7); tap(c); }
      setNow(LOOKF); await wait(() => T.st.lock || (T.st.cands && !T.st.searching)); await wait(() => !T.st.searching);
      const source = T.st.lock ? 'lock' : T.st.cands ? 'cands ' + T.st.cands.length : 'nothing';
      T.setStep(T.RT().findIndex(s => s.turn === 'hw_spiny'));
      // ---- battle: the bar comes back (reported 1 s after it is steady) ----
      const tBack = T0 + (Fup + 2) * FR + vlag; setNow(Fup + 2 + 30); T.coinBack(tBack - (T0 + (LOOKF + 2) * FR + vlag));
      if (!T.zw.on) return { mode: 'tracker not started (' + source + ')' };
      let t1 = visible(Fup + 32, cC - 4); if (cfg.ERR === 'miss' && t1.length) t1 = t1.slice(1);
      if (cfg.ERR === 'false') { t1 = t1.concat([cC - 30]).sort((a, b) => a - b); }
      for (const c of t1) { setNow(c + 7); tap(c); }
      setNow(cC + 4); T.preConfirm({ cat: 'M', id: 'hw_charge' }, T0 + (cC + R.PROFILES.jrcc_syrup.vanish + pfix) * FR + vlag);
      setNow(cS + 4); T.checkPress(T0 + (cS + R.PROFILES.timeout.vanish + pfix) * FR + vlag);
      setNow(m2a + 2 + 30); T.coinBack((m2a - cC) * FR);
      for (const c of visible(m2a + 32, m2b - 4)) { setNow(c + 7); tap(c); }
      setNow(m2b); T.st.msg = null; T.makePlan(); const plan = T.st.plan;
      const w = c => R.works(state.s, state.nc, c, state.f, R.PROFILES.timeout) ? 1 : 0, pr = c => 0.25 * w(c - 1) + 0.5 * w(c) + 0.25 * w(c + 1);
      const blind = pr(m2b);
      if (!plan || !plan.mix) return { source, blind, real: blind, mode: (T.st.msg || 'no plan').slice(0, 70), parts: T.zw.parts.length };
      const gT = Math.round((plan.tLast - T0) / FR) + plan.target;
      return { source, blind, real: pr(gT), shown: plan.mix.p, mode: 'beep', parts: plan.mix.groups, delay: gT - m2b };
    }, cfg);
    const m = out.mode.replace(/[0-9.]+/g, '#').slice(0, 50); sum.modes[m] = (sum.modes[m] || 0) + 1;
    if (out.blind != null) { sum.n++; sum.real += out.real; sum.blind += out.blind; if (out.mode === 'beep') { sum.beeps++; sum.shown += out.shown; sum.realB += out.real; } }
    console.log(cfg.seed0.toString(16), 'L', cfg.L, JSON.stringify(out));
  }
  console.log(`ERR=${ERR} LOOK=${LOOK}s | runs ${sum.n} | P(Time Out) ${(sum.real / sum.n).toFixed(3)} | blind ${(sum.blind / sum.n).toFixed(3)} | beeped ${sum.beeps} | shown ${(sum.shown / (sum.beeps || 1)).toFixed(3)} real ${(sum.realB / (sum.beeps || 1)).toFixed(3)} when beeped`);
  console.log('modes', JSON.stringify(sum.modes));
  const ok = ERR !== 'none' || (sum.n && sum.real / sum.n > sum.blind / sum.n + 0.2);
  console.log(ok ? 'PASS' : 'FAIL', 'errors', errs); await b.close();
})();
