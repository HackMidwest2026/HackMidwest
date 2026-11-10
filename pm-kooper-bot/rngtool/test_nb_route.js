/* v84 (v85: the Close Calls beeped, Final Bowser's one Power Bounce step): the Boots setting and the Normal Boots route (charge_live/README.md v84).
 *  1. The setting: at the top of the route panel (the Restart route row), Ultra Boots by default, remembered across reloads
 *     (tot-settings), and switching it switches all four fights' routes (the route list, the steps) and keeps the fight.
 *  2. Ultra Boots is v83's route exactly (step labels, profiles, Charge profiles).
 *  3. Normal Boots: the turns of the runner's spec (Kooper not in it: Goombario's Charge), every step's beep or its
 *     honest "No beeps" (the turns not modelled say why and give the blind odds; nothing is beeped there), the Duplighosts'
 *     T1 beep kept (the same Charge lock) with the goal "4 first" by default (Auto), Hallway T2 Time Out from a shine lock
 *     (the Time Out profile, no Charge tracker), no Charge reader on the Normal Boots steps but the Duplighosts'.
 *  4. The odds per fight for both routes, shown under the setting; Final Bowser's from the attack-choice model.
 *  5. No page errors; no horizontal scroll at phone width.
 * usage (from rngtool/, after python3 build_page.py): node test_nb_route.js [PAGE] */
'use strict';
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), ctx = await b.newContext({ viewport: { width: 390, height: 844 } }), p = await ctx.newPage(), errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  await p.evaluate(() => { localStorage.clear(); }); await p.reload();
  const steps = () => p.evaluate(() => window.__tot.RT().map(s => ({ t: s.t, label: s.label, cat: s.cat, prof: s.prof || null, chg: s.chg || null, nb: !!s.nb, nomodel: s.nomodel || null, blind: s.blind || null })));
  const r0 = await p.evaluate(() => { const T = window.__tot, sel = document.getElementById('s-boots'), row = document.getElementById('route-reset').parentElement;
    return { v: sel && sel.value, inRow: !!sel && row.contains(sel), opts: sel ? Array.from(sel.options).map(o => o.value + '=' + o.textContent) : [], ver: T.VERSION, odds: document.getElementById('route-odds').textContent, goal: document.getElementById('s-dupgoal').value }; });
  console.log(JSON.stringify(r0).slice(0, 600));
  check(r0.ver === 'v86.1', 'version v86.1');
  check(r0.v === 'ultra' && r0.inRow && r0.opts.join() === 'ultra=Ultra Boots,normal=Normal Boots', 'Boots setting in the Restart route row, Ultra Boots by default');
  check(r0.goal === 'auto', 'Duplighosts goal: Auto by default');
  const U = await steps();
  check(!U.some(s => s.nb), 'Ultra Boots: no Normal Boots step');
  check(U.some(s => s.chg === 'jr') && U.some(s => s.chg === 'fb1') && U.some(s => s.prof === 'timeout'), 'Ultra Boots: the v83 route (Jr. Charge lock, Final Bowser T1-T4, Time Out)');
  const uDupGoal = await p.evaluate(() => { window.__tot.setStep(0); const sel = document.getElementById('s-duproute'); sel.value = 'charge'; sel.dispatchEvent(new Event('change')); return window.__tot.dupGoalNow(); });
  const U1 = await steps();
  check(uDupGoal === 'free', 'Ultra Boots, Auto: the Duplighosts goal is "4 when it\'s free" (v80 / v83)');
  // switch to Normal Boots on the Jr. Troopa fight: the route keeps the fight
  const sw = await p.evaluate(() => { const T = window.__tot, i = T.RT().findIndex(s => /^Jr\. Troopa/.test(s.t)); T.setStep(i + 2); const sel = document.getElementById('s-boots'); sel.value = 'normal'; sel.dispatchEvent(new Event('change'));
    return { step: T.RT()[T.step()].t, list: document.getElementById('route-list').innerText, goal: T.dupGoalNow() }; });
  console.log(sw.list.slice(0, 1400));
  check(/^Jr\. Troopa T1/.test(sw.step), 'switching keeps the fight (now ' + sw.step + ')');
  check(sw.goal === 'four', 'Normal Boots, Auto: the Duplighosts goal is "4 first"');
  const N = await steps();
  const want = [/^Duplighosts T1/, /^Jr\. Troopa T1/, /^Jr\. Troopa T2/, /^Jr\. Troopa T3/, /^Jr\. Troopa T4/, /^Jr\. Troopa T5/, /^Jr\. Troopa T6/, /^Jr\. Troopa T7/, /^Hallway Bowser T1/, /^Hallway Bowser T2/, /^Hallway Bowser T5/,
    /^Final Bowser Phase 2 Power Bounce/];     // v85: one Final Bowser step, the phase-2 Power Bounce (whichever turn)
  check(N.length === want.length && N.every((s, i) => want[i].test(s.t)), 'Normal Boots steps: one per turn of the spec (' + N.map(s => s.t).join(', ') + ')');
  check(N.every(s => s.nb) && N[0].prof === 'dup3' && N[0].chg === 'dup', 'Normal Boots: the Duplighosts T1 beep kept (dup3, the Charge lock)');
  check(N.filter(s => s.chg).map(s => s.chg).join() === 'dup,jr,jr,jr,jr,jr,jr,jr,nbhw', 'v85 Normal Boots Charge readers: the Duplighosts\', Jr. Troopa\'s (every step) and Hallway T1\'s (' + N.filter(s => s.chg).map(s => s.chg).join() + ')');
  check(N.find(s => /^Hallway Bowser T2/.test(s.t)).prof === 'timeout' && !N.find(s => /^Hallway Bowser T2/.test(s.t)).nomodel, 'Hallway T2: Time Out planned (shine lock)');
  check(/Kooper/.test(sw.list) === false && /Goombario/.test(N.map(s => s.label).join()) , 'Goombario\'s Charge, no Kooper');
  for (const s of N.filter(x => x.nomodel)) check(!s.prof, s.t + ': not modelled, so no profile to beep (' + s.nomodel.slice(0, 60) + ')');
  check(N.map(x => x.prof || '-').join() === 'dup3,-,jrcc_gch,jrcc_gch,jrcc_gch,jrcc_hb,-,jrpb5n,hwcc_gch,timeout,hwpb6n,-' && N.filter(x => x.nomodel).length === 1, 'v85 beeped on Normal Boots: Duplighosts T1, Jr. T2-T5 Close Calls, T7, Hallway T1 Close Call, T2 and T5; only Final Bowser not modelled (' + N.map(x => x.prof || '-').join() + ')');
  check(/Phase 1 \(not tracked\)/.test(sw.list), 'Final Bowser phase 1 shown as not tracked');
  // every Normal Boots step: what Plan says
  const msgs = await p.evaluate(() => { const T = window.__tot, out = []; for (let i = 0; i < T.RT().length; i++) { T.setStep(i); T.st.plan = null; T.st.msg = null; T.makePlan(); out.push({ t: T.RT()[i].t, msg: T.st.msg || '', plan: !!T.st.plan, beeps: T.beepsPending ? T.beepsPending() : null }); } return out; });
  for (const m of msgs) console.log('  ' + m.t + ': ' + (m.plan ? 'PLAN' : m.msg.slice(0, 150)));
  check(msgs.every(m => !m.plan), 'no lock: nothing planned on any Normal Boots step');
  for (const m of msgs.filter((m, i) => N[i].nomodel)) check(/^No beeps this turn \(Normal Boots\)/.test(m.msg), m.t + ': says "No beeps" and why');
  for (const m of msgs.filter((m, i) => N[i].nomodel && N[i].blind)) check(/Play it blind/.test(m.msg), m.t + ': gives the blind odds');
  { const fb = N.find(x => x.nomodel); check(/not beeped yet \(v86\)/.test(fb.nomodel) && /AI 16 frames later/.test(fb.nomodel) && /every 26 frames from your target A \+ 70/.test(fb.nomodel) && /6\+ 92%, 7\+ 32%, 8\+ 3%/.test(fb.nomodel), 'v86: Final Bowser\'s Power Bounce step gives the measured turn and the locked odds, and why it is still not beeped'); }
  check(/play it blind/i.test(msgs[0].msg) && /47%/.test(msgs[0].msg), 'Duplighosts T1 without a lock: play it blind (47%)');
  for (const re of [/^Hallway Bowser T2/, /^Hallway Bowser T5/, /^Jr\. Troopa T7/]) { const h = msgs.find(m => re.test(m.t)); check(/show a few shines/.test(h.msg) && /press normally/.test(h.msg), h.t + ' without a lock: show a few shines in this menu, else press normally'); }
  check(N.find(s => /^Jr\. Troopa T7/.test(s.t)).prof === 'jrpb5n' && N.find(s => /^Hallway Bowser T5/.test(s.t)).prof === 'hwpb6n', 'Normal Boots Power Bounce profiles on Jr. T7 (5+, aims at 6) and Hallway T5 (6+)');
  // a shine lock on the Normal Boots Power Bounce steps plans on a frame the profile says works (as test_plan_keep locks)
  for (const [re, pid] of [[/^Hallway Bowser T5/, 'hwpb6n'], [/^Jr\. Troopa T7/, 'jrpb5n']]) {
    await p.reload();     // a fresh page (Normal Boots remembered) for each lock
    const pb = await p.evaluate(async ({ src, pid }) => {
      const T = window.__tot, R = T.R, F = 33.43, i = T.RT().findIndex(s => new RegExp(src).test(s.t)); T.setStep(i);
      let s = 0x2468ace0 ^ pid.length, f = 0; const sh = [];
      while (sh.length < 30) { s = R.adv(s); const x = s >= R.SHINE_MIN; if (x) sh.push(f); for (let k = 0; k < (x ? 48 : 24); k++) s = R.adv(s); f += x ? 48 : 24; }
      const t0 = performance.now() - sh[19] * F - 10 * F;
      for (let k = 0; k < 20; k++) T.addShine(t0 + sh[k] * F + 6 * F, true);
      const tq = performance.now(); while (!T.st.lock && performance.now() - tq < 60000) await new Promise(r => setTimeout(r, 100));
      if (!T.st.lock) return { none: 'no lock' };
      T.st.msg = null; T.makePlan(); const P = T.st.plan; if (!P) return { none: T.st.msg };
      return { prof: P.prof, target: P.target, works: R.works(P.seedBL, 0, P.target, 0, R.PROFILES[pid]), w: P.w.length };
    }, { src: re.source, pid });
    console.log('  ' + re.source + ' plan from a shine lock: ' + JSON.stringify(pb));
    check(pb.prof === pid && pb.works === true, re.source + ' (Normal Boots): planned from a shine lock on a frame where ' + pid + ' works');
  }
  // the odds
  const odds = await p.evaluate(() => document.getElementById('route-odds').textContent);
  console.log(odds);
  check(/Ultra Boots:/.test(odds) && /Normal Boots:/.test(odds) && ['Duplighosts', 'Jr. Troopa', 'Hallway Bowser', 'Final Bowser'].every(f => odds.split(f).length === 3), 'odds per fight for both routes');
  check(/blind cap 4\+ 72%, 5\+ 31%, 6\+ 8\.1%, 7\+ 1\.3%/.test(odds) && /Jr\. Troopa - T2-T4 Close Calls/.test(odds), 'v85 odds: Normal Boots Jr. Troopa Close Calls beeped, Final Bowser blind cap odds');
  // persisted
  await p.reload();
  const r1 = await p.evaluate(() => ({ v: document.getElementById('s-boots').value, nb: window.__tot.RT().every(s => s.nb) }));
  check(r1.v === 'normal' && r1.nb, 'Normal Boots remembered across a reload');
  const sw2 = await p.evaluate(() => { const T = window.__tot, i = T.RT().findIndex(s => /^Final Bowser/.test(s.t)); T.setStep(i); const sel = document.getElementById('s-boots'); sel.value = 'ultra'; sel.dispatchEvent(new Event('change')); return { step: T.RT()[T.step()].t, nb: T.RT().some(s => s.nb) }; });
  check(/^Final Bowser T1/.test(sw2.step) && !sw2.nb, 'back to Ultra Boots, still on Final Bowser (' + sw2.step + ')');
  const U2 = await steps();
  check(JSON.stringify(U2) === JSON.stringify(U1), 'Ultra Boots route unchanged after a round trip');
  const sc = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  check(sc.sw <= sc.cw + 1, 'no horizontal scroll at 390 px (' + sc.sw + ' / ' + sc.cw + ')');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
