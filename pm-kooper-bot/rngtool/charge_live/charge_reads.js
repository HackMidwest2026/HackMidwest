//@ Every Charge read kept (v77; charge_live/README.md "Charge reads kept"). Inlined into page_template.html after
//@ charge_live.js (shared/inline.py; //@ lines dropped). Needs the page globals CHG, chgP, CHG_PROF, chgFreshFlags, FRAME,
//@ slog, VERSION, routeStep, RT, chgEarly, chgSolve, chgReset and the elements dl-log, chg-reads-*.
/* ---------- Charge reads: every read kept, compact, in this browser only ----------
 * Each Charge the page searched (lock, no-lock, and every re-read of the same pictures with another placement) becomes
 * one record when the read ends: the capture pictures it had (from the ring before the trigger to the end of the rays),
 * each picture's time, brightness and whether it was a new game frame, the trigger (its picture, frame, level and the
 * menu level), the arena reading and the profile, every placement tried (its game frame -> picture table, shift / bans,
 * time after the rays, best seed / score / ratio) and the result. That is what the page's own search needs to run the
 * read again (chgReplay below, charge_live/test_capture_replay.js) and what charge_live/tools/capture_u8.py needs for the
 * offline harnesses.
 * Compact: only the pictures a placement can use are stored (the new game frames from the trigger on, and the ones by
 * time that can be frames -2..2 before it), each the 640x480 game raster cropped to the battle viewport plus the ridge
 * filter's reach (raster x 22..617, y 38..441: every ray sample and Mario's patch), greyscale WebP at quality 0.1 (JPEG
 * where the browser cannot write WebP), with the new-frame flags stored so the placement does not depend on the
 * compression. Measured on the 15-15-06 Hallway read (charge_live/README.md, test_capture_replay.js): lossless 13 MB;
 * WebP q 0.1 ~0.35 MB keeps the lock (seed, q) with 96% of the score at the same ratio. Halving the resolution (the
 * N64's 320x240) lost 17% of the score at any quality, and VP9 video (WebCodecs) at the same size scored no better: the
 * capture noise, not the static background, is what costs. v76 kept 640x480 JPEG q0.92 of the placed frames on a
 * no-lock only: ~2.9 MB per read.
 * Where: the last CHG_CAP_KEEP reads in memory (Download session log: chargeCaptures), and every read in IndexedDB
 * (database tot-charge-reads) with a rolling limit of CHG_DB_KEEP reads / CHG_DB_BYTES, so a refresh or a crash keeps
 * them (Settings > Advanced: Download / Clear saved Charge reads). Nothing is sent anywhere. */
const CHG_CAPS = [];
const CHG_CAP_KEEP = 20, CHG_DB_KEEP = 50, CHG_DB_BYTES = 100e6;
const CHG_CAP_FMT = { codec: 'webp', q: 0.1, scale: 1, x0: 22, y0: 38, w: 596, h: 404 };
const CHG_CAP_RAW = { codec: 'png', scale: 1, x0: 0, y0: 0, w: 640, h: 480 };     // lossless (tests: window.__chgCapRaw)
function chgRecStart() {
  const F = CHG.F0, T = CHG.trig0 || CHG.trig, s = isRoute() && RT()[routeStep];
  CHG.rec = { F, fresh: chgFreshFlags(F), trig: { tRaw: T.tRaw != null ? T.tRaw : F[T.i].t, n: T.n, i: T.i, base: T.base, d0: T.d0, cut: T.cut }, prof: chgP().id,
    arena: CHG.arenaSeen || null, step: routeStep, stepT: s ? s.t || s.turn || null : null, wall: Date.now(), hideT: CHG.hideT, tEnd: CHG.tEnd,
    menu: CHG.menu ? { from: CHG.menu.from, to: CHG.menu.to, taps: CHG.menu.taps.slice() } : null, attempts: [] };
}
function chgRecAttempt(G, locked) {
  const I = CHG.info || {}, A = { alt: CHG.alt || 0, shift: CHG.attShift || 0, banned: CHG.ban ? CHG.ban.size : 0, n0: CHG.trig ? CHG.trig.n : null, frames: I.frames,
    searchMs: I.searchMs, atMs: CHG.tEnd ? Math.round(performance.now() - CHG.tEnd) : null, best: I.best || null, s1: I.s1 || null, locked: !!locked };
  if (CHG.replay) { CHG.replay.attempts.push(A); return; }
  const R = CHG.rec; if (!R) return;
  const ix = new Map(); R.F.forEach((f, i) => ix.set(f, i)); A.G = G ? G.map(f => (f ? (ix.has(f) ? ix.get(f) : -1) : null)) : null;
  R.attempts.push(A);
}
function chgRecEnd(why) {
  const R = CHG.rec; CHG.rec = null; if (!R) return;
  const I = CHG.info || {}, b = I.best || {};
  R.result = { outcome: why, locked: why === 'lock', seed: b.seed || null, q: b.q, score: b.score, ratio: b.ratio, qs: why === 'lock' && CHG.qs ? CHG.qs.slice() : null, alt: CHG.alt || 0, lockAfterRaysMs: I.lockAfterRaysMs };
  R.info = JSON.parse(JSON.stringify(I));
  setTimeout(() => chgRecSave(R), 0);      // after the decision: the tracker / plan come first
}
async function chgRecSave(R) {
  try {
    const cap = await chgCapEncode(R, CHG_CAP_FMT); chgCapKeep(cap);
    if (window.__chgCapRaw) (window.__chgCapsRaw = window.__chgCapsRaw || []).push(await chgCapEncode(R, CHG_CAP_RAW));
  } catch (e) { slog('chargeError', { msg: 'keep read: ' + String(e && e.message || e) }); }
}
/* the record -> its compact form (async: one picture per task) */
async function chgCapEncode(R, fmt0) {
  const F = R.F, T = R.trig, ti = T.i, tT = F[ti].t, keep = new Set([ti]);
  if (R.nOf) F.forEach((f, i) => keep.add(i));
  else {
    for (let i = ti + 1; i < F.length; i++) if (R.fresh[i]) keep.add(i);
    for (const n0 of [3, 4, 5]) for (let n = -2; n <= 2; n++) {     // chgGameFrames: frames -2..2 by time, for any trigger frame
      const want = tT + (n - n0) * FRAME; let bi = null;
      for (let i = 0; i < ti; i++) if (bi == null || Math.abs(F[i].t - want) < Math.abs(F[bi].t - want)) bi = i;
      if (bi != null && Math.abs(F[bi].t - want) < 0.75 * FRAME) keep.add(bi);
    }
    for (const A of R.attempts) if (A.G) for (const i of A.G) if (i != null && i >= 0) keep.add(i);
  }
  let fmt = Object.assign({}, fmt0); const picOf = new Map(), pics = [];
  for (const i of [...keep].sort((a, b) => a - b)) {
    const Y = F[i].Y; if (!Y || picOf.has(Y)) continue;
    let b64 = await chgPicEncode(Y, fmt);
    if (b64 == null && fmt.codec === 'webp') { fmt = Object.assign({}, fmt, { codec: 'jpeg', q: 0.85 }); b64 = await chgPicEncode(Y, fmt); }   // no WebP writer here
    if (b64 == null) throw new Error('no image encoder');
    picOf.set(Y, pics.length); pics.push(b64);
    await new Promise(r => setTimeout(r, 0));
  }
  const r1 = x => Math.round(x * 10) / 10, rel = t => (t == null ? null : r1(t - T.tRaw));
  const cap = { v: 2, id: String(R.wall).padStart(15, '0') + '-' + Math.random().toString(36).slice(2, 8), wall: new Date(R.wall).toISOString(), page: VERSION,
    prof: R.prof, arena: R.arena, step: R.step, stepT: R.stepT, trig: { n: T.n, i: ti, base: T.base != null ? r1(T.base) : null, d0: T.d0 != null ? r1(T.d0) : null, cut: T.cut || null },
    hideMs: rel(R.hideT), tEndMs: rel(R.tEnd), menu: R.menu ? { from: rel(R.menu.from), to: rel(R.menu.to), taps: R.menu.taps.map(rel) } : null,
    fmt, F: F.map((f, i) => { const p = keep.has(i) && f.Y && picOf.has(f.Y) ? picOf.get(f.Y) : -1, e = [rel(f.t), r1(f.m), R.fresh[i] ? 1 : 0, p]; if (R.nOf) e.push(R.nOf.get(f)); return e; }),
    pics, attempts: R.attempts, result: R.result || null, info: R.info || null };
  if (R.nOf) cap.fixed = true;
  if (R.cands && R.cands.length) cap.cands = chgB64(new Uint8Array(Uint32Array.from(R.cands).buffer));
  return cap;
}
function chgB64(u8) { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); }
function chgUnB64(b) { return Uint8Array.from(atob(b), c => c.charCodeAt(0)); }
let chgEncCv = null;
function chgCapCv(w, h) { if (!chgEncCv) chgEncCv = document.createElement('canvas'); if (chgEncCv.width !== w) chgEncCv.width = w; if (chgEncCv.height !== h) chgEncCv.height = h; return chgEncCv; }
/* 640x480 luma -> the stored picture (a scale x scale mean, cropped), base64; null when the browser does not write fmt.codec */
async function chgPicEncode(Y, fmt) {
  const { w, h, x0, y0 } = fmt, s = fmt.scale, c = chgCapCv(w, h), cx = c.getContext('2d'), img = cx.createImageData(w, h), d = img.data, k = s * s;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let a = 0; const bx = (x0 + x) * s, by = (y0 + y) * s;
    for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) a += Y[(by + j) * 640 + bx + i];
    const v = (a + (k >> 1)) / k | 0, o = (y * w + x) * 4; d[o] = d[o + 1] = d[o + 2] = v; d[o + 3] = 255;
  }
  cx.putImageData(img, 0, 0);
  const type = 'image/' + fmt.codec, blob = await new Promise(r => c.toBlob(r, type, fmt.q));
  if (!blob || blob.type !== type) return null;
  return chgB64(new Uint8Array(await blob.arrayBuffer()));
}
/* the stored picture -> 640x480 luma (bilinear back to the raster; outside the crop 0: no ray sample or Mario patch reads it) */
async function chgPicDecode(b64, fmt) {
  const bmp = await createImageBitmap(new Blob([chgUnB64(b64)], { type: 'image/' + fmt.codec })), { w, h, x0, y0 } = fmt, s = fmt.scale;
  const c = chgCapCv(w, h), cx = c.getContext('2d', { willReadFrequently: true }); cx.clearRect(0, 0, w, h); cx.drawImage(bmp, 0, 0); bmp.close && bmp.close();
  const d = cx.getImageData(0, 0, w, h).data, S = new Uint8Array(w * h);
  for (let i = 0, j = 0; j < S.length; i += 4, j++) S[j] = (77 * d[i] + 150 * d[i + 1] + 29 * d[i + 2] + 128) >> 8;
  if (s === 1 && w === 640 && h === 480) return S;
  const Y = new Uint8Array(640 * 480);
  for (let v = 0; v < 480; v++) {
    const sy = (v + 0.5) / s - 0.5 - y0; if (sy < -0.5 || sy > h - 0.5) continue;
    const yy = Math.min(h - 1, Math.max(0, sy)), iy = Math.min(h - 2, Math.floor(yy)), fy = yy - iy;
    for (let u = 0; u < 640; u++) {
      const sx = (u + 0.5) / s - 0.5 - x0; if (sx < -0.5 || sx > w - 0.5) continue;
      const xx = Math.min(w - 1, Math.max(0, sx)), ix = Math.min(w - 2, Math.floor(xx)), fx = xx - ix, o = iy * w + ix;
      Y[v * 640 + u] = Math.round((S[o] * (1 - fx) + S[o + 1] * fx) * (1 - fy) + (S[o + w] * (1 - fx) + S[o + w + 1] * fx) * fy);
    }
  }
  return Y;
}
async function chgUrlLuma(url) {     // a v76 capture's JPEG data URL -> 640x480 luma
  const bmp = await createImageBitmap(await (await fetch(url)).blob()), c = chgCapCv(640, 480), cx = c.getContext('2d', { willReadFrequently: true });
  cx.clearRect(0, 0, 640, 480); cx.drawImage(bmp, 0, 0); const d = cx.getImageData(0, 0, 640, 480).data, Y = new Uint8Array(640 * 480);
  for (let i = 0, j = 0; j < Y.length; i += 4, j++) Y[j] = (77 * d[i] + 150 * d[i + 1] + 29 * d[i + 2] + 128) >> 8;
  return Y;
}
/* a v76 capture (the placed frames of a no-lock as 640x480 JPEG) -> the compact form, its placement fixed */
async function chgCapFromV1(c, fmt) {
  const Gfix = await chgV1Frames(c, 0), F = Gfix.filter(Boolean).sort((a, b) => a.t - b.t), nOf = new Map();
  Gfix.forEach((f, k) => { if (f) nOf.set(f, k < CHG_N + 2 ? k : k - (CHG_N + 4)); });
  const i3 = Gfix[3] ? F.indexOf(Gfix[3]) : 0, wall = c.wall ? Date.parse(c.wall) : Date.now();
  return chgCapEncode({ F, fresh: F.map(() => 1), nOf, trig: { tRaw: 0, n: 3, i: i3, base: c.base }, prof: c.prof, arena: null, step: null, stepT: null, wall, hideT: null, tEnd: null, menu: null, attempts: [], result: null, info: c.info || null }, fmt || CHG_CAP_FMT);
}
async function chgV1Frames(c, T0) {
  const G = new Array(CHG_N + 4).fill(null);
  for (const f of c.frames) G[f.n >= 0 ? f.n : CHG_N + 4 + f.n] = { t: T0 + f.t, m: f.m, Y: await chgUrlLuma(f.jpg) };
  return G;
}
/* the session's reads: memory (session log) and the browser store */
function chgCapKeep(cap) {
  const bytes = JSON.stringify(cap).length; cap.kb = Math.round(bytes / 1024);
  CHG_CAPS.push(cap); while (CHG_CAPS.length > CHG_CAP_KEEP) CHG_CAPS.shift();
  slog('chargeReadKept', { id: cap.id, prof: cap.prof, outcome: cap.result && cap.result.outcome, attempts: cap.attempts.length, pics: cap.pics.length, codec: cap.fmt.codec, kb: cap.kb });
  chgCapTitle(); chgDbPut(cap, bytes);
}
function chgCapBytes() { let n = 0; for (const c of CHG_CAPS) n += (c.kb || 0) * 1024; return n; }
function chgCapTitle() {
  const b = document.getElementById('dl-log'); if (!b) return;
  if (b.dataset.base == null) b.dataset.base = b.title || '';
  b.title = b.dataset.base + (CHG_CAPS.length ? '. Includes the last ' + CHG_CAPS.length + ' Charge read' + (CHG_CAPS.length > 1 ? 's' : '') + ' of this session (' + (chgCapBytes() / 1048576).toFixed(1) + ' MB; at most ' + CHG_CAP_KEEP + ')' : '. No Charge read yet this session');
}
let chgDbP = null;
function chgDb() {
  if (!chgDbP) {
    chgDbP = new Promise((res, rej) => {
      try {
        const r = indexedDB.open('tot-charge-reads', 1);
        r.onupgradeneeded = () => { const d = r.result; if (!d.objectStoreNames.contains('reads')) d.createObjectStore('reads', { keyPath: 'id' }); if (!d.objectStoreNames.contains('meta')) d.createObjectStore('meta', { keyPath: 'id' }); };
        r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error || new Error('open failed')); r.onblocked = () => rej(new Error('blocked'));
      } catch (e) { rej(e); }
    });
    chgDbP.catch(() => { chgDbP = null; });
  }
  return chgDbP;
}
const chgReq = r => new Promise((res, rej) => { r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
const chgTx = tx => new Promise((res, rej) => { tx.oncomplete = () => res(); tx.onerror = tx.onabort = () => rej(tx.error || new Error('transaction failed')); });
async function chgDbPut(cap, bytes) {
  try {
    const d = await chgDb(); let tx = d.transaction(['reads', 'meta'], 'readwrite');
    tx.objectStore('reads').put(cap); tx.objectStore('meta').put({ id: cap.id, bytes, wall: cap.wall, prof: cap.prof, outcome: cap.result && cap.result.outcome }); await chgTx(tx);
    const M = (await chgReq(d.transaction('meta').objectStore('meta').getAll())).sort((a, b) => (a.id < b.id ? 1 : -1));   // newest first
    let tot = 0; const drop = [];
    M.forEach((m, k) => { tot += m.bytes || 0; if (k >= CHG_DB_KEEP || (k > 0 && tot > CHG_DB_BYTES)) drop.push(m.id); });
    if (drop.length) { tx = d.transaction(['reads', 'meta'], 'readwrite'); for (const id of drop) { tx.objectStore('reads').delete(id); tx.objectStore('meta').delete(id); } await chgTx(tx); }
  } catch (e) { slog('chargeDbError', { msg: String(e && e.message || e) }); }
  chgDbShow();
}
async function chgDbStats() { const d = await chgDb(), M = await chgReq(d.transaction('meta').objectStore('meta').getAll()); let b = 0; for (const m of M) b += m.bytes || 0; return { n: M.length, bytes: b }; }
async function chgDbAll() { const d = await chgDb(), A = await chgReq(d.transaction('reads').objectStore('reads').getAll()); return A.sort((a, b) => (a.id < b.id ? -1 : 1)); }
async function chgDbClear() { const d = await chgDb(), tx = d.transaction(['reads', 'meta'], 'readwrite'); tx.objectStore('reads').clear(); tx.objectStore('meta').clear(); await chgTx(tx); }
async function chgDbShow(msg) {
  const el = document.getElementById('chg-reads-msg'); if (!el) return;
  let s; try { const S = await chgDbStats(); s = S.n + ' saved in this browser (' + (S.bytes / 1048576).toFixed(1) + ' MB; the last ' + CHG_DB_KEEP + ', at most ' + Math.round(CHG_DB_BYTES / 1e6) + ' MB)'; }
  catch (e) { s = 'This browser does not let the page keep them (' + String(e && e.message || e) + '); the session log still has this session\'s last ' + CHG_CAP_KEEP; }
  el.textContent = (msg ? msg + ' ' : '') + s + '.';
}
{
  const dl = document.getElementById('chg-reads-dl'), cl = document.getElementById('chg-reads-clear');
  if (dl) dl.onclick = async () => {
    let caps; try { caps = await chgDbAll(); } catch (e) { caps = CHG_CAPS.slice(); }
    const blob = new Blob([JSON.stringify({ version: 1, kind: 'charge-reads', page: VERSION, saved: new Date().toISOString(), chargeCaptures: caps })], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'pm-rng-charge-reads-' + Date.now() + '.json'; document.body.appendChild(a); a.click(); a.remove();
  };
  if (cl) cl.onclick = async () => {      // two clicks: no confirm() (blocked in a sandboxed frame)
    if (!cl.dataset.armed) { cl.dataset.armed = '1'; cl.textContent = 'Click again to clear'; setTimeout(() => { delete cl.dataset.armed; cl.textContent = 'Clear saved Charge reads'; }, 4000); return; }
    delete cl.dataset.armed; cl.textContent = 'Clear saved Charge reads';
    CHG_CAPS.length = 0; chgCapTitle();
    try { await chgDbClear(); chgDbShow('Cleared.'); } catch (e) { chgDbShow('Could not clear (' + String(e && e.message || e) + ').'); }
  };
  chgCapTitle(); setTimeout(() => chgDbShow(), 0);
}
/* Replay a kept read through the page's own search (tests, offline checks): the pictures go back to 640x480, the
 * placement runs on the stored times / levels / new-frame flags (a v76 capture: its placed frames as they were), then the
 * search and, on a no-lock, the same re-reads as live with no clock (opts.maxAlts: at most this many; opts.clock: the
 * live time limit, the rays ending when the replay starts). Resolves
 * { state: 'locked' | 'nolock' | 'notseen' | 'error', best, alt, attempts }. Not while a live read runs. */
async function chgReplay(cap, opts) {
  opts = opts || {};
  if (['capture', 'maps', 'search'].includes(CHG.state) || CHG.replay) throw new Error('a Charge read is running');
  chgReset();
  const P = CHG_PROF[cap.prof] || CHG_PROF.hw, T0 = performance.now() - 5000;
  let F, trig, Gfix = null;
  if (!cap.v) { Gfix = await chgV1Frames(cap, T0); F = Gfix.filter(Boolean).sort((a, b) => a.t - b.t); trig = { t: T0, tRaw: T0, n: 3, base: cap.base, i: Math.max(0, F.indexOf(Gfix[3])) }; }
  else {
    const Ys = []; for (const b of cap.pics) Ys.push(await chgPicDecode(b, cap.fmt));
    F = cap.F.map(e => ({ t: T0 + e[0], m: e[1], fresh: e[2], Y: e[3] >= 0 ? Ys[e[3]] : null }));
    if (cap.fixed) { Gfix = new Array(CHG_N + 4).fill(null); cap.F.forEach((e, i) => { const n = e[4]; if (n != null) Gfix[n >= 0 ? n : CHG_N + 4 + n] = F[i]; }); }
    const T = cap.trig; trig = { t: T0 - (T.n - 3) * FRAME, tRaw: T0, n: T.n, base: T.base, i: T.i, d0: T.d0, cut: T.cut };
  }
  const cands = cap.cands ? Array.from(new Uint32Array(chgUnB64(cap.cands).buffer)) : null;
  return new Promise(resolve => {
    Object.assign(CHG, { prof: P, trig, frames: F, Gfix, menu: null, taps: [], pres: [], tEnd: performance.now(), early: null });
    CHG.replay = { resolve, maxAlts: opts.maxAlts, clock: !!opts.clock, cands, attempts: [], t0: performance.now() };
    if (P.early && !cands) { CHG.state = 'capture'; CHG.early = { t: performance.now() }; chgEarly(); }   // FB2: stage 1 from the early maps, as live
    CHG.state = 'maps'; chgSolve();
  });
}
function chgReplayDone(out) {
  const R = CHG.replay; if (!R) return; CHG.replay = null;
  const I = CHG.info || {};
  R.resolve(Object.assign({ best: I.best || null, alt: CHG.alt || 0, attempts: R.attempts, ms: Math.round(performance.now() - R.t0), info: JSON.parse(JSON.stringify(I)) }, out));
}
