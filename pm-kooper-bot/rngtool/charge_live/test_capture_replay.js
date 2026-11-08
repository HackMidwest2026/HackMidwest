/* v77: every Charge read is kept compact and replays to the same lock (charge_reads.js).
 * A. The v76 capture in the session log 54e25740 (Final Bowser T6 no-lock, 45 placed frames, 640x480 JPEG q0.92, 2.9 MB):
 *    replayed through the page's search as it is, then converted to the compact form and replayed again: the same outcome
 *    and best seed, and the compact form is a small fraction of the size.
 * B. A Hallway clip fed frame by frame (2026-11-02 15-15-06, the first 9 s: its T1 Charge locks cf5894f0), as
 *    test_charge_feed.js does: the page keeps the read (compact, and a lossless copy for the test); both replay to the
 *    live lock (seed and q); the compact one is under the size limit; it is in IndexedDB and still there after a reload;
 *    the session log carries it; Clear empties the store.
 * C. A re-read: the same read replayed with its first placement forced wrong (__chgBan0): no-lock, then the re-reads go
 *    on until a placement locks the same seed; each attempt is in the result.
 * usage: node charge_live/test_capture_replay.js   (PAGE=path to timeout_timer_standalone.html; serves on 127.0.0.1 only)
 * The clip's frames are extracted with ffmpeg into the scratchpad on the first run (never into the repository). */
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), http = require('http'), cp = require('child_process');
const SP = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad', U = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887';
const PAGE = process.env.PAGE || SP + '/timeout_timer/timeout_timer_standalone.html';
const LOG = U + '/54e25740-timeout-timer-log-1794071163309.json', CLIP = U + '/63e6e3da-2026-11-02_15-15-06.mkv', FR = SP + '/cap77/clip1506', NF = 540;
const MAX_KB = 400;
let bad = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) bad++; };
(async () => {
  if (!fs.existsSync(FR + '/f00539.jpg')) { fs.mkdirSync(FR, { recursive: true }); cp.execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', CLIP, '-t', '9', '-q:v', '3', '-start_number', '0', FR + '/f%05d.jpg']); }
  const srv = http.createServer((q, r) => { const u = decodeURIComponent(q.url.split('?')[0]); const f = u === '/tot.html' ? PAGE : u.startsWith('/clip/') ? path.join(FR, path.basename(u)) : null;
    if (!f || !fs.existsSync(f)) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : 'image/jpeg' }); fs.createReadStream(f).pipe(r); });
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const base = 'http://127.0.0.1:' + srv.address().port;
  const b = await chromium.launch(), p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } })); window.__chgCapRaw = true; }); if (process.env.DUMP) await p.addInitScript(() => { window.__dumpCaps = true; });
  await p.goto(base + '/tot.html');
  await p.evaluate(() => window.__tot.chgDbClear().catch(() => {}));
  // ---- A: the v76 capture from the log
  const log = JSON.parse(fs.readFileSync(LOG, 'utf8')), c1 = log.chargeCaptures[0], v1kb = Math.round(JSON.stringify(c1).length / 1024);
  const A = await p.evaluate(async c => {
    const T = window.__tot, r0 = await T.chgReplay(c), cap = await T.chgCapFromV1(c), kb = Math.round(JSON.stringify(cap).length / 1024), r1 = await T.chgReplay(cap);
    const f = r => ({ state: r.state, best: r.best, ms: r.ms });
    return { r0: f(r0), r1: f(r1), kb, pics: cap.pics.length, codec: cap.fmt.codec };
  }, c1);
  console.log('A', JSON.stringify(A), 'live:', JSON.stringify(c1.info.best), 'v76 capture', v1kb, 'KB');
  // a no-lock's best is at the noise level (ratio 1.0-1.1): any change to the pictures moves it (WebP even at q 0.6 does), so
  // the outcome is what has to match, and the best stays a no-lock's
  check(A.r0.state === 'nolock' && A.r1.state === 'nolock' && A.r1.best && A.r1.best.ratio < 1.8, 'A: compact replays as the v76 capture: no-lock (best ' + (A.r0.best && A.r0.best.seed + ' ' + A.r0.best.score + ' ' + A.r0.best.ratio + 'x') + ' / compact ' + (A.r1.best && A.r1.best.seed + ' ' + A.r1.best.score + ' ' + A.r1.best.ratio + 'x') + ')');
  check(A.r0.best && A.r0.best.seed === c1.info.best.seed, 'A: the v76 capture replays to the live result (best ' + c1.info.best.seed + ')');
  check(A.kb <= MAX_KB && A.kb * 5 < v1kb, 'A: size ' + v1kb + ' KB -> ' + A.kb + ' KB (' + A.pics + ' pictures, ' + A.codec + ')');
  // ---- B: a frame-fed clip, the read kept live
  await p.evaluate(() => { const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'); T.setStep(hi); document.getElementById('s-lead').value = '1.5'; });
  const B = await p.evaluate(async ({ base, nf }) => {
    const T = window.__tot, url = i => base + '/clip/f' + String(i).padStart(5, '0') + '.jpg', bmp = new Map(); let next = 0, late = 0;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(url(k)).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    want(0); for (let i = 0; i < 60; i++) await bmp.get(i);
    const t0 = performance.now() + 300;
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25) { late++; im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close(); T.V.src = vf; try { T.onFrame(tf); } finally { T.V.src = null; vf.close(); }
    }
    for (let k = 0; k < 200 && !(T.CHG_CAPS.length && (window.__chgCapsRaw || []).length); k++) await new Promise(r => setTimeout(r, 100));
    const S = T.SLOG, lock = S.filter(x => x.ev === 'chargeLock').pop(), C = T.CHG_CAPS[T.CHG_CAPS.length - 1], Rw = (window.__chgCapsRaw || []).slice(-1)[0];
    if (!C || !Rw) return { late, lock: lock && lock.best, none: true };
    const kept = S.filter(x => x.ev === 'chargeReadKept');
    T.chgReset(); T.setStep(T.RT().findIndex(s => s.turn === 'hw_spiny'));
    const rr = await T.chgReplay(Rw), rc = await T.chgReplay(C), db = await T.chgDbStats();
    const kbC = Math.round(JSON.stringify(C).length / 1024), kbR = Math.round(JSON.stringify(Rw).length / 1024);
    const f = r => ({ state: r.state, best: r.best, qs: r.qsRays, alt: r.alt });
    if (window.__dumpCaps) window.__dumped = { raw: Rw, compact: C };
    return { late, lock: lock && lock.best, qs: lock && lock.qs, result: C.result, attempts: C.attempts.map(a => ({ alt: a.alt, best: a.best, locked: a.locked })), kbC, kbR, pics: C.pics.length, F: C.F.length, codec: C.fmt.codec,
      raw: f(rr), compact: f(rc), db, kept, title: document.getElementById('dl-log').title, id: C.id };
  }, { base, nf: NF });
  console.log('B', JSON.stringify(B));
  if (process.env.DUMP) { const d = await p.evaluate(() => window.__dumped); fs.writeFileSync(process.env.DUMP + '/clip_raw.json', JSON.stringify(d.raw)); fs.writeFileSync(process.env.DUMP + '/clip_compact.json', JSON.stringify(d.compact));
    fs.writeFileSync(process.env.DUMP + '/log_raw.json', JSON.stringify(await p.evaluate(c => window.__tot.chgCapFromV1(c, { codec: 'png', scale: 1, x0: 0, y0: 0, w: 640, h: 480 }), c1))); }
  check(!B.none && B.lock && B.lock.seed === 'cf5894f0', 'B: the clip locks cf5894f0 live and the read is kept (' + (B.lock && B.lock.seed) + ')');
  if (!B.none) {
    check(B.result && B.result.outcome === 'lock' && B.result.seed === 'cf5894f0' && B.attempts.length >= 1, 'B: the record has the result and ' + B.attempts.length + ' attempt(s)');
    check(B.raw.state === 'locked' && B.raw.best.seed === 'cf5894f0', 'B: the lossless copy replays to the lock (' + B.raw.best.seed + ' ' + B.raw.best.score + ' ' + B.raw.best.ratio + 'x)');
    check(B.compact.state === 'locked' && B.compact.best.seed === B.raw.best.seed && B.compact.best.q === B.raw.best.q && JSON.stringify(B.compact.qs) === JSON.stringify(B.raw.qs),
      'B: the compact copy replays to the same lock (' + B.compact.best.seed + ' q ' + B.compact.best.q + ' score ' + B.compact.best.score + ' ' + B.compact.best.ratio + 'x, qs ' + B.compact.qs + ')');
    check(B.kbC <= MAX_KB, 'B: size lossless ' + B.kbR + ' KB -> compact ' + B.kbC + ' KB (' + B.pics + ' pictures of ' + B.F + ' capture frames, ' + B.codec + ')');
    check(B.db && B.db.n === 1, 'B: kept in IndexedDB (' + JSON.stringify(B.db) + ')');
    check(/Includes the last 1 Charge read/.test(B.title), 'B: the log button says it: "' + B.title.slice(-90) + '"');
    // after a reload: the read is still in the browser store and replays from there; the session log carries this session's reads
    await p.reload();
    const B2 = await p.evaluate(async id => { const T = window.__tot, all = await T.chgDbAll(), c = all.find(x => x.id === id); if (!c) return { n: all.length };
      const r = await T.chgReplay(c); return { n: all.length, state: r.state, seed: r.best && r.best.seed }; }, B.id);
    check(B2.n === 1 && B2.state === 'locked' && B2.seed === 'cf5894f0', 'B: still in IndexedDB after a reload, and replays from there (' + JSON.stringify(B2) + ')');
    const L = await p.evaluate(() => new Promise(res => { const T = window.__tot, o = URL.createObjectURL; URL.createObjectURL = bl => { bl.text().then(t => res(JSON.parse(t).chargeCaptures.length)); URL.createObjectURL = o; return o(bl); }; document.getElementById('dl-log').click(); }));
    check(L === 0, 'B: a fresh session\'s log starts with no reads (the store keeps them): ' + L);
    // ---- C: a re-read, the first placement forced wrong
    const C = await p.evaluate(async id => { const T = window.__tot, c = (await T.chgDbAll()).find(x => x.id === id);
      window.__chgBan0 = [5, 6, 7, 8, 9, 10, 11].map(n => (n - 3) * 64 + n);        // frames 5-11: no picture may be its own frame
      try { const r = await T.chgReplay(c); return { state: r.state, best: r.best, alt: r.alt, attempts: r.attempts.map(a => ({ alt: a.alt, shift: a.shift, banned: a.banned, best: a.best && a.best.seed + ' ' + a.best.score + ' ' + a.best.ratio, locked: a.locked })) }; }
      finally { window.__chgBan0 = null; } }, B.id);
    console.log('C', JSON.stringify(C));
    check(C.attempts.length >= 2 && !C.attempts[0].locked && C.state === 'locked' && C.best.seed === 'cf5894f0', 'C: a wrong first placement no-locks, a re-read locks cf5894f0 (attempt ' + (C.alt + 1) + ' of ' + C.attempts.length + ')');
    // the live clock: with beeps no lock can meet (3 beeps 20 s apart), the no-lock stops there instead of re-reading
    const C2 = await p.evaluate(async id => { const T = window.__tot, c = (await T.chgDbAll()).find(x => x.id === id), el = document.getElementById('s-gapms'), lead0 = el.value;
      window.__chgBan0 = [5, 6, 7, 8, 9, 10, 11].map(n => (n - 3) * 64 + n); el.value = '20000';
      try { const r = await T.chgReplay(c, { clock: true }); return { state: r.state, stop: r.stop, attempts: r.attempts.length }; } finally { window.__chgBan0 = null; el.value = lead0; } }, B.id);
    check(C2.state === 'nolock' && C2.stop === 'time' && C2.attempts === 1, 'C: no re-read once the beep lead would be missed (' + JSON.stringify(C2) + ')');
    const D = await p.evaluate(async () => { const T = window.__tot; await T.chgDbClear(); return T.chgDbStats(); });
    check(D.n === 0, 'Clear saved Charge reads empties the store');
    const lb = await p.evaluate(() => { const T = window.__tot; return { hw: T.chgLockBy(T.CHG_PROF.hw), dup: T.chgLockBy(T.CHG_PROF.dup), jr: T.chgLockBy(T.CHG_PROF.jr), fb1: T.chgLockBy(T.CHG_PROF.fb1) }; });
    check(lb.hw === 12800 && lb.dup === 7500 && lb.fb1 === 13500, 're-reads until (ms after the rays, lead 1.5 s, 3 beeps): ' + JSON.stringify(lb));
  }
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); srv.close();
  console.log(bad ? bad + ' FAILED' : 'all passed'); process.exit(bad ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
