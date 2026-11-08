/* v82: the main status card's buttons (Download session log, Reset) never move, whatever the status text says (the runner:
 * "the progress line jumps around and moves the buttons"). The buttons now sit above everything whose length changes.
 * Shortest and longest headline / detail the page shows, with and without the search's progress line, at phone and desktop
 * widths: the buttons' boxes must be identical. Also the page's name in the title and the header.
 * usage: node test_status_btns.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [];
  for (const [w, h] of [[390, 844], [1300, 900]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } }); p.on('pageerror', e => errs.push(String(e)));
    await p.goto('file://' + PAGE);
    const r = await p.evaluate(async () => {
      const raf = () => new Promise(r => requestAnimationFrame(() => r())), box = id => { const q = document.getElementById(id).getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(v => Math.round(v * 10) / 10).join(','); };
      const H = document.getElementById('headline'), D = document.getElementById('detail'), out = [];
      const long = 'No plain fit: searching all seeds with the torch-room model (about 2 minutes)… '.repeat(3), longD = 'The coin fits the tracked states badly (3 missed or extra shines on the best one). No beeps; press normally. '.repeat(4);
      const cases = [['', ''], ['Ok', ''], [long, ''], ['Searching all 4.3 billion seeds…', '7% · 1.2 s'], ['Searching all 4.3 billion seeds…', '37% · 60.9 s'], [long, '100% · 118.4 s'], [long, longD], ['Ok', longD]];
      for (const [a, d] of cases) { H.textContent = a; D.textContent = d; D.hidden = !d; await raf(); await raf(); out.push(box('dl-log') + ' | ' + box('reset')); }
      return { out, title: document.title, h1: document.querySelector('h1').textContent.replace(/\s+/g, ' ').trim(), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth };
    });
    const same = r.out.every(x => x === r.out[0]);
    check(same, w + ' px: the buttons stay put across ' + r.out.length + ' status texts (' + (same ? r.out[0] : r.out.join(' / ')) + ')');
    check(r.sw <= r.cw + 1, w + ' px: no horizontal scroll (' + r.sw + ' / ' + r.cw + ')');
    if (w === 1300) { check(r.title === 'Paper Mario Any% (No ACE) (RNG Manipulation)', 'title: ' + r.title); check(r.h1 === 'Paper Mario Any% (No ACE) (RNG Manipulation)', 'header: ' + r.h1); }
    await p.close();
  }
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
