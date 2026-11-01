const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1000, height: 1400 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  const url = 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
  await p.goto(url);
  // an older copy's saved data: the Fight menu on Duplighosts, a saved Time Out screen and Duplighost screen
  await p.evaluate(() => { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ prof: 'dup4', off: '-6' }));
    localStorage.setItem('tot-targets', JSON.stringify({ timeout: { box: { x: .1, y: .1, w: .2, h: .1 }, ref: new Array(384).fill(77) }, dup4: { box: { x: .2, y: .2, w: .2, h: .1 }, ref: new Array(384).fill(55) } })); });
  await p.reload();
  const r = await p.evaluate(() => ({ selectVisible: !document.getElementById('s-prof').hidden, routeShown: !document.getElementById('route').hidden,
    steps: document.querySelectorAll('#route-list li').length, current: document.querySelector('#route-list li[style*="700"]').textContent, label: document.getElementById('target-label').textContent }));
  await p.click('#route-list li[data-i="15"]');
  const r2 = await p.evaluate(() => ({ current: document.querySelector('#route-list li[style*="700"]').textContent, label: document.getElementById('target-label').textContent, carriedOver: !!window.__tot.V.ref, refValue: window.__tot.V.ref && window.__tot.V.ref[0] }));
  await p.click('#route-list li[data-i="0"]');
  const r3 = await p.evaluate(() => ({ current: document.querySelector('#route-list li[style*="700"]').textContent, carriedOver: !!window.__tot.V.ref, refValue: window.__tot.V.ref && window.__tot.V.ref[0] }));
  const panel = await (await p.$('#route')).evaluateHandle(e => e.closest('section')); await panel.asElement().screenshot({ path: 'one.png' });
  console.log(JSON.stringify(r)); console.log('jump to Time Out:', JSON.stringify(r2)); console.log('jump to Duplighosts:', JSON.stringify(r3)); console.log('errors', errs); await b.close();
})();
