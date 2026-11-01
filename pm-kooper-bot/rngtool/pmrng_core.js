/* Paper Mario (JP) Hallway Bowser Time Out RNG tool: core logic (browser + Node).
 *
 * RNG: seed = seed * 0x5D588B65 + 1 (mod 2^32), stepped once per game frame plus once per draw.
 * Status-bar coin: at the end of each spin loop it draws rand_int(100); 70+ plays the shine loop. The next draw
 * comes 24 frames later after a normal spin, 48 after a shine.
 * Time Out vs Hallway Bowser: STOP lands if rand_int(100) <= 30. Counting from the frame C of the target-confirm A:
 * effect draws on C+24 (72 x rand(40000)), C+73 (40 x [rand(359), rand(10), rand(10)]), C+112 (72 x rand(30000)),
 * the roll is the first draw on C+386. Within a frame: battle script (roll, effect spawns), then the coin, then the
 * per-frame step. All verified against the emulator frame by frame. */
(function (root) {
  'use strict';
  const MUL = 0x5D588B65;
  const FRAME_MS = 1000 / (60000 / 1001 / 2);           // one game frame = 2 NTSC fields = 33.367 ms
  const D1009 = Math.floor(4294967295 / 1010);
  const SHINE_MIN = 700 * D1009;                          // advanced seed >= this -> rand_int(100) >= 70 -> shine
  const adv = s => (Math.imul(s, MUL) + 1) >>> 0;
  function affine(n) { let A = 1, C = 0; for (let i = 0; i < n; i++) { A = Math.imul(A, MUL) >>> 0; C = (Math.imul(C, MUL) + 1) >>> 0; } return [A, C]; }
  const [A24, C24] = affine(24), [A48, C48] = affine(48);
  const step24 = s => (Math.imul(s, A24) + C24) >>> 0, step48 = s => (Math.imul(s, A48) + C48) >>> 0;
  function internal(s, mx) {
    const d = Math.floor(4294967295 / (mx + 1)) || 1;
    for (;;) { s = adv(s); const v = Math.floor(s / d); if (v <= mx) return [s, v]; }
  }
  function randInt(s, mx) {
    if (mx === 1) { const [t, v] = internal(s, 1000); return [t, v >= 501 ? 1 : 0]; }
    if (mx === 100) { const [t, v] = internal(s, 1009); return [t, Math.floor(v / 10)]; }
    return internal(s, mx);
  }

  /* ---- coin pattern from shine taps ----
   * taps: times (ms) at which the player saw a shine. Returns {pattern, gaps, worst} where pattern is a string of
   * 'S' (shine) and '.' (normal spin), one character per coin draw from the first tapped shine to the last, and
   * worst = the largest timing residual (frames) when snapping each gap to 48 + 24k. */
  function patternFromTaps(taps) {
    let pattern = 'S', worst = 0; const gaps = [];
    for (let i = 1; i < taps.length; i++) {
      const g = (taps[i] - taps[i - 1]) / FRAME_MS, k = Math.round((g - 48) / 24);
      if (k < 0) return { error: 'two shines ' + g.toFixed(1) + ' frames apart (a shine loop is 48): extra tap?' };
      worst = Math.max(worst, Math.abs(g - (48 + 24 * k))); gaps.push(k);
      pattern += '.'.repeat(k) + 'S';
    }
    return { pattern, gaps, worst };
  }
  /* does seed s (value just before the first draw of pattern) reproduce it? */
  function matches(s, pattern) {
    for (let i = 0; i < pattern.length; i++) {
      s = adv(s); const sh = s >= SHINE_MIN;
      if (sh !== (pattern.charCodeAt(i) === 83)) return false;
      s = sh ? step48(s) : step24(s);
    }
    return true;
  }
  /* brute force: all seeds in [lo, hi) that reproduce the pattern (seed = value before its first draw) */
  function searchRange(pattern, lo, hi, cap) {
    const out = []; const first = pattern.charCodeAt(0) === 83;
    for (let x = lo; x < hi; x++) {
      const s0 = x >>> 0, t = adv(s0);
      if ((t >= SHINE_MIN) !== first) continue;                   // fast reject on the first draw
      if (matches(s0, pattern)) { out.push(s0); if (out.length >= cap) break; }
    }
    return out;
  }
  /* faster brute force for patterns that start with a shine: iterate over the advanced seed t of the first draw
   * (only the shine range [SHINE_MIN, 2^32) can match), check the rest, and invert to the seed before the draw.
   * Covers t in [lo, hi) clipped to the shine range. */
  const INV = (function () { let x = MUL; for (let i = 0; i < 5; i++) x = Math.imul(x, (2 - Math.imul(MUL, x)) >>> 0) >>> 0; return x; })();
  const back = s => Math.imul((s - 1) >>> 0, INV) >>> 0;
  function searchShineStart(pattern, lo, hi, cap) {
    const out = []; lo = Math.max(lo, SHINE_MIN); hi = Math.min(hi, 4294967296);
    for (let t = lo; t < hi; t++) {
      let s = t >>> 0, ok = true;
      s = step48(s);
      for (let i = 1; i < pattern.length; i++) {
        s = adv(s); const sh = s >= SHINE_MIN;
        if (sh !== (pattern.charCodeAt(i) === 83)) { ok = false; break; }
        s = sh ? step48(s) : step24(s);
      }
      if (ok) { out.push(back(t >>> 0)); if (out.length >= cap) break; }
    }
    return out;
  }
  /* state after the pattern: seed just before the next coin draw, and how many frames until it */
  function afterPattern(s, pattern) {
    let gap = 0;
    for (let i = 0; i < pattern.length; i++) {
      s = adv(s); const sh = s >= SHINE_MIN;
      if (i < pattern.length - 1) s = sh ? step48(s) : step24(s); else gap = sh ? 48 : 24;
    }
    return { seedAfterLastDraw: s, framesToNextDraw: gap };
  }
  /* seed just before the LAST draw of the pattern */
  function seedBeforeLastDraw(s, pattern) {
    for (let i = 0; i < pattern.length - 1; i++) { s = adv(s); s = (s >= SHINE_MIN) ? step48(s) : step24(s); }
    return s;
  }
  /* resync after a gap: from a known seed `from`, find every n in [0, nmax] such that adv^n(from) reproduces the new
   * pattern (which starts at a tapped shine). Returns the matching n values (with their seeds). */
  function resync(from, pattern, nmax, cap, nlo) {
    const out = []; let s = from >>> 0; nlo = Math.max(0, nlo || 0);
    for (let i = 0; i < nlo; i++) s = adv(s);
    for (let n = nlo; n <= nmax; n++) {
      if (matches(s, pattern)) { out.push({ n, seed: s }); if (out.length >= (cap || 16)) break; }
      s = adv(s);
    }
    return out;
  }

  /* ---- Time Out ---- */
  const EFFECTS = { 24: Array(72).fill(40000), 73: [].concat(...Array(40).fill([359, 10, 10])), 112: Array(72).fill(30000) };
  const ROLL = 386;
  /* seed: value just before frame t0's draws; nextCoin: frame of the next coin draw (>= t0); confirm: frame of the
   * target-confirm A. Returns the Time Out roll (works if <= 30). */
  function timeOutRoll(seed, nextCoin, confirm, t0) {
    let s = seed >>> 0, nc = nextCoin;
    for (let t = t0 || 0; t <= confirm + ROLL; t++) {
      if (t === confirm + ROLL) return randInt(s, 100)[1];
      const fx = EFFECTS[t - confirm];
      if (fx) for (const mx of fx) s = randInt(s, mx)[0];
      if (t === nc) { const r = randInt(s, 100); s = r[0]; nc = t + (r[1] >= 70 ? 48 : 24); }
      s = adv(s);
    }
  }
  /* frames (relative to frame 0 = a coin draw whose prior seed is seedBeforeDraw) where confirming works, for
   * confirm frames from..to. Returns an array of booleans indexed from `from`. */
  function timeOutTable(seedBeforeDraw, from, to) {
    const out = [];
    for (let c = from; c <= to; c++) out.push(timeOutRoll(seedBeforeDraw, 0, c, 0) <= 30);
    return out;
  }
  /* the earliest run of at least minRun consecutive working confirm frames, starting no earlier than `from` */
  function bestWindow(seedBeforeDraw, from, to, minRun) {
    const tab = timeOutTable(seedBeforeDraw, from, to); let runStart = -1;
    for (let i = 0; i <= tab.length; i++) {
      if (i < tab.length && tab[i]) { if (runStart < 0) runStart = i; }
      else if (runStart >= 0) { if (i - runStart >= minRun) return { start: from + runStart, end: from + i - 1, length: i - runStart }; runStart = -1; }
    }
    return null;
  }

  const api = { MUL, FRAME_MS, SHINE_MIN, adv, internal, randInt, patternFromTaps, matches, searchRange, afterPattern,
    seedBeforeLastDraw, resync, searchShineStart, back, timeOutRoll, timeOutTable, bestWindow, EFFECTS, ROLL };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PMRNG = api;
})(typeof self !== 'undefined' ? self : this);
