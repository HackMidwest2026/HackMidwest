/* v86.1 regression test: Jr. Troopa (Ultra Boots, Charge-lock route) after a restart (console 2026-11-09, page v86, logs
 * 1794269702752 / 1794269850246; fixtures/console_1109.json: the events from t=680000, no pictures).
 * The clips (19-14-36, 19-17-03) show what the runner did: fight 1 died on T4 (Maple Syrup Close Call), then after the T5
 * Charge the runner reset, walked back in and started over from T1 (Jr. Troopa's speech, 10/10 HP, Super Charge, Bomb, his
 * hit to 3 HP, T2 Bomb), and did the same again at ~1015 s. The page (v86) jumped: the restart took the previous Charge as
 * T1, the battle entry's 400 ms bar flash as the T1 Bomb, and the real T1 Charge as T3 ("jrResync from 4 to 4"); the T1
 * Bomb was planned and read as T3's Close Call and the 10 HP of a full bar read as a death.
 * The replay: the status bar per video frame from the logged hides (each bar-up [at - upMs, at]), the runner's own route
 * clicks, the Charge bursts at their triggers (CHG.hideT = the hide before), Mario's tens place always showing "1" (the worst
 * case: 10 HP) from fight 1's T4 death on. Hides are read on the next video frame (+0..33 ms). Checks: the turn the page is on through both restarted fights is the clips' turn.
 * usage: node test_jr_restart.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1109.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [];
  const replay = async (opt) => {
  const p = await b.newPage({ viewport: { width: 1300, height: 1200 } }); p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(S => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify(S)); } catch (e) {} }, FIX.settings);
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(([F, opt]) => {
    const T = window.__tot, CHG = T.CHG, JRT = T.JRT, FRAME = T.R.FRAME_MS || 33.367;
    let now = 0; window.__jrTensTest = () => (now < 750000 ? 0 : 0.5);     // fight 1: T3 dodged, T4 died (762 s); then 10 HP (the full bar of a new fight)
    const s0 = T.SLOG.length, out = { version: T.VERSION, jrStep1: T.RT()[1] && T.RT()[1].jr, at: {} };
    const ups = F.events.filter(e => (e.ev === 'barHide' || e.ev === 'jrHide') && e.upMs != null && (opt.flash || e.upMs >= 600)).map(e => [e.at - e.upMs, e.at]);
    const hideBefore = t => Math.max(...F.events.filter(e => (e.ev === 'barHide' || e.ev === 'jrHide') && e.at < t).map(e => e.at));
    const sched = [];
    for (const s of F.manualSteps) if (opt.clicks || s.t < 845000) sched.push({ t: s.t, f: () => T.setStep(s.to) });
    for (const e of F.events) {
      if (e.ev === 'chargeTrigger') sched.push({ t: e.t, f: () => { T.chgReset(); Object.assign(CHG, { prof: T.CHG_PROF.jr, state: 'search', trig: { t: e.t }, hideT: hideBefore(e.t) }); } });
      if (e.ev === 'chargeLock') sched.push({ t: e.t, f: () => { CHG.state = 'locked'; } });
    }
    // snapshots: [name, t]
    const snaps = [['fight1 T5', 840000], ['after restart 1', 860000], ['A T1 Charge', 872000], ['A T1 Bomb', 880000], ['A T2 Bomb', 886000], ['after restart 2', 1010000], ['B T1 Charge', 1020000], ['B T1 Bomb', 1030000], ['B T2 Bomb', 1034500]];
    for (const [name, t] of snaps) sched.push({ t, f: () => { out.at[name] = { k: JRT.k, on: JRT.on, step: T.step(), stepT: (T.RT()[T.step()] || {}).t, inputs: JRT.inputs.map(x => x.k + ':' + Math.round(x.t)) }; } });
    sched.sort((a, b) => a.t - b.t);
    let i = 0;
    for (let t = 680000; t < 1041500; t += FRAME) {
      while (i < sched.length && sched[i].t <= t) sched[i++].f();
      now = t; const present = ups.some(([a, z]) => t >= a && t < z);
      T.jrFrame(t, present);
    }
    out.log = T.SLOG.slice(s0).filter(e => /^jr/.test(e.ev) || e.ev === 'step').map(e => Object.assign({}, e));
    return out;
  }, [FIX, opt]);
  await p.close(); return r;
  };
  const r = await replay({ clicks: true, flash: true });
  const L = r.log;
  for (const e of L) if (/^jr(Fight|Resync|BattleEntry|Restart|Outcome|HideHeld|HideDropped|ChargeBurst)$/.test(e.ev)) console.log('   ', JSON.stringify(e));
  // the confirms k:t, each within 40 ms of the logged hide
  const fits = (inputs, want) => inputs.length === want.length && inputs.every((x, i) => { const [k, t] = x.split(':').map(Number); return k === want[i][0] && t >= want[i][1] && t - want[i][1] < 40; });
  const ev = (name, f) => L.filter(e => e.ev === name && (!f || f(e)));
  const fights = ev('jrFight').map(e => e.at);
  check(r.version === 'v86.1', 'version v86.1');
  check(r.jrStep1 === 1, 'route step 1 is Jr. Troopa T1');
  // fight 1 (690-844 s): unchanged; T4 death, the T5 Charge (84 s of bar up after the death) anchored by its burst
  check(ev('jrOutcome', e => e.k === 7 && e.dodge === false).length === 1, 'fight 1: the T4 Maple Syrup Close Call read as a death');
  check(r.at['fight1 T5'] && fits(r.at['fight1 T5'].inputs.slice(-2), [[7, 743343], [8, 832043]]), 'fight 1: the T5 Charge (84016 ms bar up) counted as k8 (' + (r.at['fight1 T5'] || {}).inputs + ')');
  // restart 1 (the runner clicked T1 at 847.4 s): no stale fight from the T5 Charge; the battle entry's flash is no confirm
  check(!fights.some(t => t > 845000 && t < 869000), 'restart 1: no fight started from the previous Charge (v86: jrFight at 832476)');
  check(r.at['after restart 1'] && !r.at['after restart 1'].on && r.at['after restart 1'].step === 1, 'restart 1: waiting on T1 (' + JSON.stringify(r.at['after restart 1']) + ')');
  check(ev('jrBattleEntry', e => Math.abs(e.at - 867409) < 50).length === 1, 'restart 1: the 400 ms bar flash at 867.4 s read as the battle entry');
  check(!ev('jrHide', e => Math.abs(e.at - 867409) < 50).length, 'restart 1: the flash is not counted as a confirm');
  // fight A (clip 19-14-36): T1 Charge 869.3, T1 Bomb 873.3, T2 Bomb 883.3
  check(fights.some(t => Math.abs(t - 869780) < 50), 'fight A: the T1 Charge burst at 869.8 s starts the fight at T1 (v86: "jrResync from 3 to 4")');
  const A1 = r.at['A T1 Charge'], A2 = r.at['A T1 Bomb'], A3 = r.at['A T2 Bomb'];
  check(A1 && A1.k === 1 && A1.step === 1, 'fight A: after the T1 Charge, T1 Bomb next (' + JSON.stringify(A1) + ')');
  check(A2 && A2.k === 2 && A2.step === 2, 'fight A: after the T1 Bomb, T2 (' + JSON.stringify(A2) + ')');
  check(A3 && A3.k === 3 && A3.step === 2 && fits(A3.inputs, [[0, 869276], [1, 873309], [2, 883292]]), 'fight A: after the T2 Bomb, still T2 (Whacka next), not T4 (' + JSON.stringify(A3) + ')');
  const r1 = L.findIndex(e => e.ev === 'jrRestart'), after = L.slice(r1);
  check(r1 > 0 && !after.some(e => e.ev === 'jrOutcome') && !L.some(e => e.ev === 'jrResync'), 'after the restart: no Close Call outcome (v86: "HP 10" -> death on the T1 Bomb read as T3) and no resync');
  // restart 2: the long idle (104883 ms bar up) then a reset; the runner clicked T1 at 1001.4 s; battle entry at 1015.5 s
  check(ev('jrHideHeld', e => Math.abs(e.at - 992492) < 50).length === 1 && !ev('jrHide', e => Math.abs(e.at - 992492) < 50).length, 'restart 2: the hide after 104883 ms of bar up held, never counted (the runner\'s T1 click at 1001.4 s, then the bar gone 22 s: a reset)');
  check(ev('jrBattleEntry', e => Math.abs(e.at - 1015475) < 50).length === 1, 'restart 2: the 383 ms flash at 1015.5 s read as the battle entry');
  const B1 = r.at['B T1 Charge'], B2 = r.at['B T1 Bomb'], B3 = r.at['B T2 Bomb'];
  check(fights.some(t => Math.abs(t - 1017724) < 50), 'fight B (clip 19-17-03): the T1 Charge burst at 1017.7 s starts the fight at T1 (v86: "jrResync from 4 to 4")');
  check(B1 && B1.k === 1 && B1.step === 1, 'fight B: after the T1 Charge, T1 Bomb next (' + JSON.stringify(B1) + ')');
  check(B2 && B2.k === 2 && B2.step === 2, 'fight B: after the T1 Bomb, T2 (' + JSON.stringify(B2) + ')');
  check(B3 && B3.k === 3 && B3.step === 2 && fits(B3.inputs, [[0, 1017225], [1, 1021192], [2, 1031341]]), 'fight B: after the T2 Bomb, still T2 (' + JSON.stringify(B3) + ')');
  // the same with no click from the runner after fight 1 (the page alone), and also with the battle entries' flashes unseen
  // (the T1 Charge then fits T1 by the bar gone 22 s since the last Charge burst: jrResyncK)
  for (const opt of [{ clicks: false, flash: true }, { clicks: false, flash: false }]) {
    const q = await replay(opt), nm = opt.flash ? 'no clicks' : 'no clicks, no flashes';
    for (const e of q.log) if (/^jr(Fight|Resync|BattleEntry|Restart|End)$/.test(e.ev)) console.log('    ' + nm + ' ' + JSON.stringify(e));
    for (const [snap, k, step] of [['A T1 Charge', 1, 1], ['A T2 Bomb', 3, 2], ['B T1 Charge', 1, 1], ['B T1 Bomb', 2, 2], ['B T2 Bomb', 3, 2]]) {
      const x = q.at[snap]; check(x && x.on && x.k === k && x.step === step, nm + ': ' + snap + ' -> k ' + k + ', route T' + step + ' (' + JSON.stringify(x) + ')');
    }
    check(q.log.some(e => e.ev === 'jrFight' && Math.abs(e.at - 1017724) < 50), nm + ': fight B starts at T1 on its Charge');
    check(!q.log.slice(q.log.findIndex(e => e.ev === 'jrFight' && e.at > 845000)).some(e => e.ev === 'jrOutcome'), nm + ': no Close Call outcome in fights A and B');
  }
  check(!errs.length, 'no page errors ' + errs.join(' | '));
  await b.close();
  console.log(fails ? 'FAILED ' + fails : 'all ok');
  process.exit(fails ? 1 : 0);
})();
