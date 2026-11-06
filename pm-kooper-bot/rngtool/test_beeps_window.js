/* Exactly the set number of beeps, and the window-type picker (feedback items 6 and 7).
 *  A. pickRun on hand-made tables: the first run of the kind that starts at or after `from`, aimed at its middle,
 *     none when the only such run is past `to` or runs off the table.
 *  B. In the page (a shine lock on the Time Out step): for every beep count 1-5, beep offsets -5 / -3.5 / 0 / +2 and
 *     plans made at random moments, the plan schedules exactly that many beeps (oscillators created, none in the past);
 *     v69 dropped the first one whenever the earliest frame came within ~5 frames of the lead (3 or 4 at random).
 *  C. Window types green / yellow / red with a long max wait: the plan's window has that length (3+ / 2 / 1), starts
 *     no earlier than the earliest frame, is the first such run after it, and the target is its middle frame; with a
 *     max wait of 0 s and no such run at the earliest frame, the page says there is none and plans nothing.
 * usage: node test_beeps_window.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
async function locked(b, settings) {
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => {     // count the beeps really scheduled (beepAt drops one whose time is past)
    window.__osc = 0; const AC = window.AudioContext; if (!AC) return;
    const orig = AC.prototype.createOscillator; AC.prototype.createOscillator = function () { window.__osc++; return orig.call(this); };
  });
  await p.goto('file://' + PAGE); await p.evaluate(s => localStorage.setItem('tot-settings', JSON.stringify(s)), settings); await p.goto('file://' + PAGE);
  await p.evaluate(async () => {
    const T = window.__tot, R = T.R; let s = 0x2468ace0, f = 0; const taps = [], now = performance.now();
    while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
    const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
    while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
    T.setStep(T.RT().findIndex(x => x.prof === 'timeout'));
  });
  return { p, errs };
}
(async () => {
  const b = await chromium.launch(); const allErrs = [];
  // A
  { const p = await b.newPage(); await p.goto('file://' + PAGE);
    const r = await p.evaluate(() => { const T = window.__tot, t = s => s.split('').map(c => c === '1');
      return {
        g1: T.pickRun(t('0011101111000110'), 100, 100, 200, 'green'),       // runs 102-104 (3), 106-109 (4)
        g2: T.pickRun(t('0011101111000110'), 100, 103, 200, 'green'),       // the 3-run starts before `from`: the 4-run, aimed at 107 or 108
        g2s: T.pickRun(t('0011101111000110'), 100, 103, 200, 'green', f => (f === 108 ? 1 : 0.5)),
        y: T.pickRun(t('0011101111000110'), 100, 100, 200, 'yellow'),       // 113-114
        r: T.pickRun(t('0100110'), 100, 100, 200, 'red'),                    // 101
        rNone: T.pickRun(t('0110110'), 100, 100, 200, 'red'),
        late: T.pickRun(t('0000000111'), 100, 100, 105, 'green'),            // runs off the table
        past: T.pickRun(t('00000001110'), 100, 100, 105, 'green') };         // aimed at 108 > to
    });
    check(r.g1 && r.g1.target === 103 && r.g1.w.length === 3, 'pickRun green first run ' + JSON.stringify(r.g1));
    check(r.g2 && r.g2.w.start === 106 && r.g2.target === 107, 'pickRun green after from ' + JSON.stringify(r.g2));
    check(r.g2s && r.g2s.target === 108, 'pickRun even run: the middle frame more states agree on ' + JSON.stringify(r.g2s));
    check(r.y && r.y.w.start === 113 && r.y.w.length === 2, 'pickRun yellow ' + JSON.stringify(r.y));
    check(r.r && r.r.target === 101, 'pickRun red ' + JSON.stringify(r.r));
    check(r.rNone === null && r.late === null && r.past === null, 'pickRun none ' + JSON.stringify([r.rNone, r.late, r.past]));
    console.log('A. pickRun:', JSON.stringify(r)); await p.close(); }
  // B
  const counts = {};
  for (const nb of [1, 2, 3, 4, 5]) for (const off of [-5, -3.5, 0, 2]) {
    const { p, errs } = await locked(b, { beeps: String(nb), off: String(off), lead: '1.5', gapms: '500', wtype: 'best' });
    const r = await p.evaluate(async () => {
      const T = window.__tot, out = [];
      for (let k = 0; k < 6; k++) {
        await new Promise(r => setTimeout(r, 37 + 113 * k));
        const o0 = window.__osc; T.makePlan(); const P = T.st.plan;
        out.push({ n: window.__osc - o0, firstIn: P ? Math.round(P.tPress - (T.nBeeps() - 1) * 500 - performance.now()) : null, msg: T.st.msg });
      }
      return out;
    });
    counts[nb + '@' + off] = r.map(x => x.n).join('');
    check(r.every(x => x.n === nb && x.firstIn >= 0), `beeps ${nb}, offset ${off}: ${JSON.stringify(r)}`);
    allErrs.push(...errs); await p.close();
  }
  console.log('B. oscillators per plan (6 plans each), by beeps@offset:', JSON.stringify(counts));
  // C
  for (const type of ['green', 'yellow', 'red']) {
    const { p, errs } = await locked(b, { beeps: '3', off: '-5', lead: '1.5', wtype: type, zwwin: '20' });
    const r = await p.evaluate(() => { const T = window.__tot, R = T.R; T.makePlan(); const P = T.st.plan; if (!P) return { msg: T.st.msg };
      const tab = R.timeOutTable(P.seedBL, P.from, P.w.end + 2, R.PROFILES.timeout), runs = [];
      for (let i = 0, s = -1; i <= tab.length; i++) { if (i < tab.length && tab[i]) { if (s < 0) s = i; } else if (s >= 0) { runs.push({ start: P.from + s, length: i - s }); s = -1; } }
      return { w: P.w, target: P.target, from: P.from, runs, type: P.type }; });
    const want = { green: L => L >= 3, yellow: L => L === 2, red: L => L === 1 }[type];
    check(r.w && want(r.w.length) && r.w.start >= r.from, `${type}: window ${JSON.stringify(r)}`);
    if (r.runs) { const first = r.runs.find(x => x.start >= r.from && want(x.length)); check(first && first.start === r.w.start, `${type}: not the first such run after the earliest frame: ${JSON.stringify(r)}`);
      const mids = r.w.length % 2 ? [r.w.start + (r.w.length - 1) / 2] : [r.w.start + r.w.length / 2 - 1, r.w.start + r.w.length / 2]; check(mids.includes(r.target), `${type}: target not in the middle ${JSON.stringify(r)}`); }
    console.log(`C. ${type}: window ${JSON.stringify(r.w)} target ${r.target} (earliest ${r.from})`);
    allErrs.push(...errs); await p.close();
  }
  { // none in a zero wait (red needs an isolated frame right at the earliest frame: try a few moments, expect at least one "No ... window")
    const { p, errs } = await locked(b, { beeps: '3', off: '0', lead: '1.5', wtype: 'red', zwwin: '0' });
    const r = await p.evaluate(async () => { const T = window.__tot, out = []; for (let k = 0; k < 8; k++) { await new Promise(r => setTimeout(r, 70)); T.st.plan = null; T.makePlan(); out.push(T.st.plan ? 'plan' : (T.st.msg || '').slice(0, 60)); } return out; });
    check(r.some(x => /^No red/.test(x)) && r.every(x => x === 'plan' || /^No red/.test(x)), 'zero wait: ' + JSON.stringify(r));
    console.log('C. red with no extra wait:', JSON.stringify(r)); allErrs.push(...errs); await p.close();
  }
  console.log('errors', JSON.stringify(allErrs)); console.log(fails || allErrs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || allErrs.length ? 1 : 0);
})();
