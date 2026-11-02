/* High Power Bounce Manipulator, synthetic end to end: a known seed in the Blooper (or Final Bowser phase 2) menu, shines
 * fed to the page at the times the capture would show them (draw + 6 frames + video lag), the page's lock and plan, and
 * the plan's count checked against the boss model run from the true seed on the absolute confirm frame. Then a try with
 * a press 1 frame late is logged and the implied offset must come out +1 (when the count pins it).
 * usage: node test_hpbm.js [blooper|fb2] [n seeds]   (env PAGE: another build) */
const { chromium } = require('playwright');
const BL = require('./powerbounce/blmodel.js'), FB = require('./powerbounce/fb2model.js');
const FIGHT = process.argv[2] || 'blooper', N = +(process.argv[3] || 3);
const MUL = 0x5D588B65, adv = s => (Math.imul(s, MUL) + 1) >>> 0;
function randInt(s, mx) { const m = mx === 100 ? 1009 : mx, dv = Math.floor(0xFFFFFFFF / (m + 1)); let v; do { s = adv(s); v = Math.floor(s / dv); } while (v > m); return [s, mx === 100 ? Math.floor(v / 10) : v]; }
const FMS = 1001 / 30, VLAG = 50;
(async () => {
  const b = await chromium.launch(); let fails = 0;
  for (let n = 0; n < N; n++) {
    const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
    await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
    await p.goto(process.env.PAGE || 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/hpbm/high_power_bounce_manipulator_standalone.html');
    const seed0 = (Math.random() * 4294967296) >>> 0, c0 = 5 + n * 3, p130 = (n * 7) % 26 * 5 + 2, p220 = (p130 + 5 * n) % 220;
    const ph = FIGHT === 'fb2' ? { p130, p220 } : null;
    // truth: per frame seed (start of frame), coin schedule, shines and bolts
    const seeds = [], shines = [], bolts = []; let s = seed0, nc = c0;
    for (let f = 0; f < 3600; f++) {
      seeds.push(s);
      if (ph) { const k = FB.lightAt(f, p130, p220); for (let i = 0; i < k; i++) s = randInt(s, 359)[0]; if ([18, 78, 88, 178].includes((f + p220) % 220)) bolts.push(f + 2); }
      if (f === nc) { const r = randInt(s, 100); s = r[0]; if (r[1] >= 70) { shines.push(f + 6); nc += 48; } else nc += 24; }
      s = adv(s);
    }
    const coinAt = f => { let x = c0; while (x < f) { let t = seeds[x]; if (ph) for (let i = FB.lightAt(x, p130, p220); i > 0; i--) t = randInt(t, 359)[0]; x += randInt(t, 100)[1] >= 70 ? 48 : 24; } return x; };
    await p.evaluate(({ FIGHT }) => { const el = document.getElementById('s-fight'); el.value = FIGHT; el.dispatchEvent(new Event('change')); document.getElementById('s-vlag').value = 50; document.getElementById('s-vlag').dispatchEvent(new Event('change')); }, { FIGHT });
    const T0 = await p.evaluate(() => performance.now() + 1000);
    // feed: per frame, set the clock; at shine and bolt display frames call the page
    let lockF = null, plan = null;
    const ev = []; shines.forEach(f => ev.push([f, 'shine'])); bolts.forEach(f => ev.push([f, 'bolt'])); ev.sort((a, c) => a[0] - c[0]);
    for (const [f, kind] of ev) {
      const r = await p.evaluate(async ({ t, kind }) => {
        window.__dt += t - performance.now(); const H = window.__hpbm;
        if (kind === 'bolt') H.st.bolts.push(t); else H.addShine(t, true);
        while (H.st.searching) { const a = performance.now(); await new Promise(r => setTimeout(r, 100)); window.__dt -= performance.now() - a; }
        return { lock: H.st.lock, plan: H.st.plan ? { d: H.st.plan.d, count: H.st.plan.count, tPress: H.st.plan.tPress, near: H.st.plan.near, baseT: H.st.plan.base.t, rate: H.st.plan.rate } : null };
      }, { t: T0 + f * FMS + VLAG, kind });
      if (r.lock && lockF === null) lockF = f;
      if (r.plan) { plan = r.plan; break; }
    }
    if (!plan) { console.log('seed', seed0.toString(16), 'NO PLAN', 'lock at', lockF, errs); fails++; await p.close(); continue; }
    // absolute confirm frame: tPress = baseT + (d - 0.5) * rate, baseT = T0 + F0 * FMS  (off 0)
    const Fc = Math.round((plan.tPress - T0) / FMS + 0.5);
    const o = { coinNext: coinAt(Fc) - Fc, dmg0: FIGHT === 'fb2' ? 13 : 1, kmax: FIGHT === 'fb2' ? 40 : 28 };
    const truth = e => ph ? Math.min(FB.fb2Bounces(seeds[Fc + e], 0, { p130: (p130 + Fc + e) % 130, p220: (p220 + Fc + e) % 220, coinNext: coinAt(Fc + e) - Fc - e, dmg0: 13 }), 99)
                          : Math.min(BL.blBounces(seeds[Fc + e], 0, { coinNext: coinAt(Fc + e) - Fc - e, dmg0: 1, kmax: 28 }), 30);
    const t0 = truth(0), tl = truth(1);
    const ok = t0 === plan.count && Object.keys(plan.near).every(e => truth(+e) === plan.near[e]);
    // log a try 1 frame late: actual = truth(+1); implied offsets must include +1
    const tr = await p.evaluate(({ actual, until }) => { window.__dt += until - performance.now(); const H = window.__hpbm; H.st.awaiting = H.st.plan; H.st.plan = null; H.logTry(actual); return H.st.tries[H.st.tries.length - 1]; }, { actual: tl, until: plan.tPress + 20000 });
    const okT = tr.implied.includes(1);
    console.log(FIGHT, 'seed', seed0.toString(16), 'lock after', lockF, 'frames, plan d', plan.d, 'count', plan.count, 'truth', t0, ok ? 'OK' : 'MISMATCH', '| late try', tl, 'implied', tr.implied.join(','), okT ? 'OK' : 'BAD', errs.length ? errs : '');
    if (!ok || !okT) fails++;
    await p.close();
  }
  await b.close(); console.log(fails ? 'FAIL ' + fails : 'PASS'); process.exit(fails ? 1 : 0);
})();
