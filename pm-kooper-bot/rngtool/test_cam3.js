/* Automatic mode after the OBS fixes: seed lock from emulator footage through the fake camera, with
 * MODE=vfc (normal video callbacks) or MODE=bg (forced background path: frames read from the track, as when the
 * window is hidden behind OBS). Also reports the search thread count and the window-capture source opening. */
const { chromium } = require('playwright');
const truth = require('/dev/shm/pmbot/vid_truth.json');
const MODE = process.env.MODE || 'vfc';
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--use-file-for-fake-video-capture=/dev/shm/pmbot/coin.y4m', '--autoplay-policy=no-user-gesture-required', '--auto-select-desktop-capture-source=Entire screen'] });
  const ctx = await b.newContext({ permissions: ['camera'] }); const p = await ctx.newPage({ viewport: { width: 1100, height: 1500 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  // window source: check it opens
  await p.selectOption('#cam-sel', 'window'); await p.click('#cam-start'); await p.waitForTimeout(1500);
  console.log('window source:', await p.textContent('#cam-msg'), '| frames', await p.textContent('#r-fps'));
  await p.click('#cam-stop');
  // camera source (fake camera labelled as a non-OBS device: the page must refuse it)
  await p.evaluate(() => { const o = document.createElement('option'); o.value = ''; document.getElementById('cam-sel').appendChild(o); document.getElementById('cam-sel').value = ''; });
  await p.click('#cam-start'); await p.waitForTimeout(800);
  console.log('non-OBS camera:', await p.textContent('#cam-msg'));
  // for the footage test, accept the fake camera as if it were OBS
  await p.evaluate(() => { window.__tot.V.force = null; });
  await p.evaluate(async (mode) => {
    const T = window.__tot; const gum = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    const s = await gum({ video: { frameRate: { ideal: 60 } } });
    Object.defineProperty(s.getVideoTracks()[0], 'label', { value: 'OBS Virtual Camera (test)' });
    navigator.mediaDevices.getUserMedia = async () => s;
    if (mode === 'bg') T.V.force = 'bg';
  }, MODE);
  await p.click('#cam-start');
  const seeds = new Set(truth.filter(t => t.shine).map(t => t.seed_before >>> 0));
  let threads = 0;
  for (let s = 0; s < 80; s += 5) {
    await p.waitForTimeout(5000);
    const r = await p.evaluate(() => { const T = window.__tot; return { shines: T.V.shines, fps: Math.round(T.V.fps), bg: T.V.bgFrames || 0, cands: T.st.cands && T.st.cands.length, lock: T.st.lock && T.st.lock.seed, searching: T.st.searching }; });
    console.log(s + 5 + 's', JSON.stringify(r), r.lock ? ('lock is a true pre-shine seed: ' + seeds.has(r.lock >>> 0)) : '');
    if (r.lock) break;
  }
  console.log('errors', errs);
  await b.close();
})();
