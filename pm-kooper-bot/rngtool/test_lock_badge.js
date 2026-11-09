/* v81: the lock badge beside the strip and the route panel's order.
 *  1. The badge: red NOT LOCKED with no seed; green LOCKED on a shine lock and on a Charge-lock tracker; amber DOUBTFUL at
 *     doubt 50%+ and on a Jr. Troopa seed rebuilt / found again and not yet confirmed; red NOT LOCKED once the tracker is
 *     dead; Final Bowser T1-T4 (FB14) and T6 (FB2) steps follow their own trackers. Its box and the strip's never move.
 *  2. The route panel: Restart route (with the step buttons) on top, the route list directly below, then "Details" with
 *     the Zero-wait instructions, chg-status, fb14-status, fb2-status, walk-counter, walk-last and carry-note; its
 *     open / closed state is remembered over a reload.
 * usage: node test_lock_badge.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0, n = 0; const check = (ok, msg) => { n++; if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const errs = [];
  const p = await b.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1 }); p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  // 1. the badge
  const r = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, out = { version: T.VERSION, states: [] };
    const raf = () => new Promise(r => requestAnimationFrame(r));
    const box = id => { const q = document.getElementById(id).getBoundingClientRect(); return [q.left, q.top, q.width, q.height].map(x => Math.round(x * 10) / 10).join(','); };
    const snap = async name => { await raf(); await raf(); const el = document.getElementById('lock-badge'), cs = getComputedStyle(el);
      out.states.push({ name, state: el.dataset.state, cls: el.className, text: document.getElementById('lock-badge-text').textContent, why: document.getElementById('lock-badge-why').textContent,
        badge: box('lock-badge'), strip: box('strip'), bg: cs.backgroundColor, ink: cs.color }); };
    await snap('fresh');
    // a shine lock (as test_strip_geometry makes one)
    let s = 0x2468ace0, f = 0; const taps = [], now = performance.now();
    while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
    const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
    const t1 = performance.now(); while (!T.st.lock && performance.now() - t1 < 60000) await new Promise(r => setTimeout(r, 100));
    await snap('shine lock');
    // the endgame route: the Hallway Charge-lock tracker
    document.getElementById('s-prof').value = 'endgame'; document.getElementById('s-prof').dispatchEvent(new Event('change'));
    T.st.lock = null; T.st.clock = null;
    const hi = T.RT().findIndex(x => x.turn === 'hw_spiny'); T.setStep(hi); T.hwTrackerAt(0x13579bdf, [7], 100000);
    await snap('charge lock');
    const zw = T.zw, sw = zw.parts.reduce((a, q) => a + q.w, 0), bg0 = zw.bg;
    zw.bg = sw * 1.2; await snap('doubt 55%');
    zw.bg = bg0; zw.dead = true; await snap('tracker dead');
    zw.dead = false;
    // Jr. Troopa: a rebuilt state not yet confirmed by the coin, then a seed found again from the coin
    const fight0 = zw.fight; zw.fight = 'jr';
    const JRT = T.JRT; JRT.recon = { k: 3, taps0: 1e9, at: performance.now() }; await snap('jr rebuilt');
    JRT.recon = null; JRT.shineRec = { pos: 0, n: 1, taps: 6, at: performance.now(), taps0: 1e9 }; await snap('jr found again');
    JRT.shineRec = null; zw.fight = fight0; await snap('charge lock again');
    zw.on = false; await snap('tracker off');
    // Final Bowser T1-T4 and T6 follow their own trackers
    const { FB14, FB2 } = T.lockFB(), fb = T.RT().findIndex(x => x.fb14 === 2); T.setStep(fb);
    FB14.on = false; await snap('fb14 no lock');
    Object.assign(FB14, { on: true, states: [{}, {}, {}], doubt: 0.1 }); await snap('fb14 locked');
    FB14.doubt = 0.6; await snap('fb14 doubt');
    FB14.on = false; FB14.states = [];
    const f2 = T.RT().findIndex(x => x.turn === 'fb2_pb'); T.setStep(f2);
    FB2.on = false; await snap('fb2 no lock');
    FB2.on = true; FB2.hyps = [{}, {}]; await snap('fb2 locked');
    FB2.on = false; FB2.hyps = null;
    return out;
  });
  const S = Object.fromEntries(r.states.map(x => [x.name, x]));
  console.log(r.states.map(x => `${x.name}: ${x.text} (${x.why}) badge ${x.badge} strip ${x.strip} bg ${x.bg}`).join('\n'));
  const want = { 'fresh': 'no', 'shine lock': 'ok', 'charge lock': 'ok', 'doubt 55%': 'doubt', 'tracker dead': 'no', 'jr rebuilt': 'doubt', 'jr found again': 'doubt', 'charge lock again': 'ok',
    'tracker off': 'no', 'fb14 no lock': 'no', 'fb14 locked': 'ok', 'fb14 doubt': 'doubt', 'fb2 no lock': 'no', 'fb2 locked': 'ok' };
  const TEXT = { ok: 'LOCKED', no: 'NOT LOCKED', doubt: 'DOUBTFUL' };
  for (const k in want) check(S[k] && S[k].state === want[k] && S[k].text === TEXT[want[k]] && S[k].cls === 'lockb ' + want[k], `badge "${k}": ${S[k] && S[k].text} (want ${TEXT[want[k]]})`);
  check(r.version === 'v85', 'version v85');
  const badges = new Set(r.states.map(x => x.badge)), strips = new Set(r.states.map(x => x.strip));
  check(badges.size === 1, 'the badge never moves or resizes: ' + [...badges].join(' | '));
  check(strips.size === 1, 'the strip never moves: ' + [...strips].join(' | '));
  const [, , bw, bh] = r.states[0].badge.split(',').map(Number); check(bw >= 160 && bh >= 48, 'the badge is large (' + bw + 'x' + bh + ')');
  // colours: green / red / amber, high contrast with the text
  const rgb = c => c.match(/\d+/g).map(Number), lum = c => { const v = rgb(c).slice(0, 3).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const contrast = (a, c) => { const A = lum(a), B = lum(c); return (Math.max(A, B) + 0.05) / (Math.min(A, B) + 0.05); };
  for (const k of ['fresh', 'charge lock', 'doubt 55%']) { const x = S[k]; check(contrast(x.bg, x.ink) >= 4.5, `badge "${k}" contrast ${contrast(x.bg, x.ink).toFixed(2)}`); }
  { const [rr, gg] = rgb(S['charge lock'].bg); check(gg > rr + 60, 'LOCKED is green'); }
  { const [rr, gg, bb] = rgb(S['fresh'].bg); check(rr > gg + 80 && rr > bb + 80, 'NOT LOCKED is red'); }
  { const [rr, gg, bb] = rgb(S['doubt 55%'].bg); check(rr > 200 && gg > 130 && bb < 80, 'DOUBTFUL is amber'); }
  // 2. the panel's order, and the Details state remembered
  const order = async () => p.evaluate(() => {
    const route = document.getElementById('route'), kids = [...route.children], D = document.getElementById('route-details');
    const iOf = el => kids.indexOf(el.closest('#route > *'));
    const inD = ['chg-status', 'fb14-status', 'fb2-status', 'walk-counter', 'walk-last', 'carry-note'].map(id => [id, !!document.getElementById(id) && D.contains(document.getElementById(id))]);
    const zero = [...D.querySelectorAll('p.note')].find(x => /Zero-wait route/.test(x.textContent));
    const ids = [...D.querySelectorAll('[id]')].map(x => x.id);
    return { top: document.getElementById('side').children[1] === route, reset: iOf(document.getElementById('route-reset')), prev: iOf(document.getElementById('route-prev')), next: iOf(document.getElementById('route-next')),
      list: iOf(document.getElementById('route-list')), details: iOf(D), last: kids.length - 1, summary: D.querySelector('summary').textContent, inD, zero: !!zero,
      zeroFirst: !!zero && D.querySelector('p.note') === zero, idOrder: ids.filter(x => /status|walk|carry/.test(x)), open: D.open, nLi: document.querySelectorAll('#route-list [data-i]').length };
  });
  const o = await order();
  console.log('panel:', JSON.stringify(o));
  check(o.top, 'the route block comes right under the panel heading');
  check(o.reset === 0 && o.prev === 0 && o.next === 0, 'Restart route and the step buttons are the first row');
  check(o.list === 1, 'the route list directly below them');
  check(o.details === 2 && o.last === 2 && o.summary === 'Details', 'then Details, last');
  check(o.inD.every(x => x[1]), 'Details holds ' + o.inD.filter(x => !x[1]).map(x => x[0]).join(', ') + ' too');
  check(o.zero && o.zeroFirst, 'the Zero-wait instructions are in Details, first');
  check(JSON.stringify(o.idOrder) === JSON.stringify(['chg-status', 'fb14-status', 'fb2-status', 'walk-counter', 'walk-last', 'carry-note']), 'Details order ' + o.idOrder.join(', '));
  check(o.open === false && o.nLi > 10, 'Details closed by default, the route list filled (' + o.nLi + ' steps)');
  await p.click('#route-details > summary'); await p.waitForTimeout(50);
  await p.reload(); await p.waitForTimeout(200);
  check((await order()).open === true, 'Details open after a reload');
  await p.click('#route-details > summary'); await p.waitForTimeout(50);
  await p.reload(); await p.waitForTimeout(200);
  check((await order()).open === false, 'Details closed again after a reload');
  check(!errs.length, 'page errors: ' + errs.join(' | '));
  await b.close();
  console.log(fails ? `FAILED ${fails} of ${n} checks` : `OK: ${n} checks passed`); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('ERROR ' + e); process.exit(2); });
