/* Replay a saved session log through the page: shines and coin gaps at their recorded times (fake clock), hidden time
 * per gap estimated from the shine timing (not in v1 logs). Reports when and on what the page locks. */
const { chromium } = require('playwright'); const log = require(require('path').resolve(process.argv[2]));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html'); if (process.env.NOEDGES) await p.evaluate(() => { window.__noedges = true; });
  const out = await p.evaluate(async (events) => {
    const T = window.__tot; document.getElementById('reset').click(); if (window.__noedges) T.EDGES.on = false;
    const setNow = t => { window.__dt += t - performance.now(); };
    const wait = async () => { for (let i = 0; i < 1200 && T.st.searching; i++) await new Promise(r => setTimeout(r, 50)); };
    const res = []; let lastShine = null, locked = null;
    for (let i = 0; i < events.length; i++) {
      const e = events[i];
      if (e.ev === 'shine') { setNow(e.at + 200); T.addShine(e.at, true); lastShine = e.at; await wait(); }
      if (e.ev === 'coinBack') {
        const next = events.slice(i + 1).find(x => x.ev === 'shine'); const gap = next && lastShine ? next.at - lastShine : 0;
        const hid = e.hiddenMs != null ? e.hiddenMs : gap < 6000 ? 800 : 6000;                     // estimate: short gaps were dropouts, long ones C-up closed
        setNow(e.t); T.coinBack(hid); await wait();
      }
      if (T.st.lock && !locked) { locked = { atShineTime: (lastShine / 1000).toFixed(1), seed: (T.st.lock.seed >>> 0).toString(16) }; res.push(locked); }
    }
    return { firstLock: locked, finalLock: T.st.lock && (T.st.lock.seed >>> 0).toString(16), chainSearches: window.__tot.st.chain.length };
  }, log.events);
  console.log(JSON.stringify(out)); console.log('errors', errs); await b.close();
})();
