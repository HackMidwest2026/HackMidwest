/* Calibrate from last press (feedback item 9): the action sits in a closed menu under the strip, shows what it will change,
 * needs a second click to apply, sets the beep and visual offsets from the last press (or the average of the last 3 / 5),
 * can leave either offset alone, and clears the presses measured against the old offsets. Cancel changes nothing.
 * The old one-click Move beeps / Move visual buttons are gone from the press row.
 * usage: node test_calibrate.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1400 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE); await p.evaluate(() => localStorage.setItem('tot-settings', JSON.stringify({ off: '-5', voff: '-6' }))); await p.goto('file://' + PAGE);
  const val = id => p.evaluate(i => document.getElementById(i).value, id);
  check(await p.evaluate(() => !document.getElementById('press-apply') && !document.getElementById('press-apply-v')), 'the one-click Move beeps / Move visual buttons are still there');
  check(await p.evaluate(() => !document.getElementById('cal-menu').open), 'the calibrate menu should start closed');
  // no press yet: the action is disabled
  await p.evaluate(() => { const T = window.__tot; T.showPresses(); document.getElementById('press-row').hidden = false; });
  await p.click('#cal-menu > summary');
  check(await p.evaluate(() => document.getElementById('cal-go').disabled), 'with no press measured the action should be disabled');
  // presses: +2.0, +1.0, +1.5 (late); the last press is +1.5
  await p.evaluate(() => { const T = window.__tot; T.presses.push(2.0, 1.0, 1.5); T.calPreview(); });
  const prev1 = await p.textContent('#cal-preview');
  check(/1\.5 frames late/.test(prev1) && /Beep offset -5 → -6\.5/.test(prev1) && /Visual offset -6 → -7\.5/.test(prev1), 'preview for the last press: ' + prev1);
  await p.click('#cal-go');
  check(await p.isVisible('#cal-yes') && await p.isVisible('#cal-no'), 'the action should ask for confirmation');
  check(await val('s-off') === '-5' && await val('s-voff') === '-6', 'nothing may change before the confirmation');
  await p.click('#cal-no');
  check(await val('s-off') === '-5' && await val('s-voff') === '-6' && !(await p.isVisible('#cal-yes')), 'Cancel must change nothing');
  // average of the last 3 = 1.5 as well; use 5 (only 3 so far) and only the beep offset
  await p.selectOption('#cal-n', '5'); await p.uncheck('#cal-vis');
  const prev2 = await p.textContent('#cal-preview');
  check(/only 3 so far/.test(prev2) && /Beep offset -5 → -6\.5/.test(prev2) && !/Visual offset/.test(prev2), 'preview, average of 5 (3 so far), beep only: ' + prev2);
  await p.click('#cal-go'); await p.click('#cal-yes');
  check(await val('s-off') === '-6.5' && await val('s-voff') === '-6', 'after confirming: beep offset -6.5, visual offset unchanged; got ' + (await val('s-off')) + ' / ' + (await val('s-voff')));
  check(await p.evaluate(() => window.__tot.presses.length === 0), 'the presses measured against the old offsets should be cleared');
  check(await p.evaluate(() => JSON.parse(localStorage.getItem('tot-settings')).off === '-6.5'), 'the new offset should be saved');
  // both offsets from one early press
  await p.evaluate(() => { const T = window.__tot; T.presses.push(-2.3); document.getElementById('cal-menu').open = true; document.getElementById('cal-vis').checked = true; document.getElementById('cal-n').value = '1'; T.calPreview(); });
  await p.click('#cal-go'); await p.click('#cal-yes');
  check(await val('s-off') === '-4.2' && await val('s-voff') === '-3.7', 'both offsets from a press 2.3 frames early: ' + (await val('s-off')) + ' / ' + (await val('s-voff')));
  check(await p.evaluate(() => window.__tot.SLOG.filter(e => e.ev === 'calibrated').length === 2), 'each calibration should be logged');
  console.log('preview texts:', JSON.stringify([prev1, prev2]));
  console.log('errors', JSON.stringify(errs)); console.log(fails || errs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || errs.length ? 1 : 0);
})();
