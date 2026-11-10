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
  /* ---- fight profiles: the random rolls a confirm decides, counted in frames from the confirm frame ----
   * effects: extra draws in the script phase of a frame (before the coin); rolls: in order, each must pass.
   * vanish: frames from the confirm until the saved target-screen box changes (press check). All measured in the
   * emulator (JP) frame by frame. */
  const PROFILES = {
    timeout: { id: 'timeout', name: 'Hallway Bowser: Time Out', short: 'Time Out works', effects: EFFECTS,
      rolls: [{ at: ROLL, max: 100, ok: v => v <= 30 }], vanish: 2, minRun: 3,
      screen: 'Time Out\'s target screen (hand on Bowser)', box: 'the クッパ name box in the top-left' },
    // Duplighosts x4 (kpa3 formation 2), Bombette out, turn 1 do nothing / do nothing: the confirm is Bombette's
    // "do nothing"; each Duplighost rolls RandInt(1000) < 600 to copy on the enemy turn. On the all-copy path there are
    // no other draws (13 seeds checked, every roll matched).
    dup4: { id: 'dup4', name: 'Duplighosts: all 4 copy Bombette', short: 'all 4 Duplighosts copy', effects: {},
      rolls: [13, 110, 207, 304].map(at => ({ at, max: 1000, ok: v => v < 600 })), vanish: 2, minRun: 2,   // v87: the page closes the Strategies screen on its grey frame (confirm + 2; console clips 2026-11-09, input display)
      screen: 'the Partner’s Strategies menu with the hand on なにもしない (do nothing)', box: 'the Strategies panel (both lines and a little below)' },
    // Final Jr. Troopa (battle 0x0207), Bombette (Super), Mario at 2 HP (Close Call active under 6 HP). Close Call is
    // rand_int(100) < 30 when his attack hits (he only attacks Mario; in base form always Leap, no attack-choice roll).
    // Each model matched the emulator on 8-9 seeds (every roll value). The Bomb mash meter does not matter (tested).
    jrcc_bomb: { id: 'jrcc_bomb', name: 'Jr. Troopa: Close Call after Bombette\'s Bomb', short: 'Close Call', group: 'jr',
      effects: { 73: Array(8).fill(359) }, post: { 73: [360] }, rolls: [{ at: 179, max: 100, ok: v => v < 30 }], vanish: 2, minRun: 2,
      screen: 'Bombette\'s Bomb target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    jrcc_syrup: { id: 'jrcc_syrup', name: 'Jr. Troopa: Close Call after Maple Syrup', short: 'Close Call', group: 'jr',
      effects: { 118: [].concat(...Array(10).fill([359, 10, 10])) }, rolls: [{ at: 163, max: 100, ok: v => v < 30 }], vanish: 2, minRun: 2,
      screen: 'Maple Syrup target screen (hand on Mario)', box: 'the マリオ name box in the top-left' },
    jrcc_nothing: { id: 'jrcc_nothing', name: 'Jr. Troopa: Close Call after Bombette does nothing', short: 'Close Call', group: 'jr',
      effects: {}, rolls: [{ at: 26, max: 100, ok: v => v < 30 }], vanish: 2, minRun: 2,   // v87: the Strategies screen greys on confirm + 2 (the page's close), goes on + 3 (console input display)
      screen: 'the Partner’s Strategies menu with the hand on なにもしない', box: 'the Strategies panel (both lines and a little below)' },
    // Power Bounce vs Jr. Troopa (chance 70: 140, 98, 68, 47, 32...): 6+ hits = the first four cap rolls pass. Rolls
    // every 27 frames; hit-effect draws one frame after each. AC press timing inside the windows does not matter.
    jrpb6: { id: 'jrpb6', name: 'Jr. Troopa: Power Bounce 6+ hits', short: '6+ bounces', group: 'jr',
      effects: { 52: Array(11).fill(359), 79: Array(11).fill(359), 106: Array(10).fill(359), 133: Array(10).fill(359) },
      rolls: [[78, 140], [105, 98], [132, 68], [159, 47]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 2,
      screen: 'Power Bounce target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    // 5+ hits = the first three cap rolls pass (5 hits leave him at 4 HP for Bombette's Bomb on this route)
    jrpb5: { id: 'jrpb5', name: 'Jr. Troopa: Power Bounce 5+ hits (aims at 6+)', short: '5+ bounces', group: 'jr',
      effects: { 52: Array(11).fill(359), 79: Array(11).fill(359), 106: Array(10).fill(359) },
      rolls: [[78, 140], [105, 98], [132, 68]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 2,
      screen: 'Power Bounce target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    // Final Bowser phase 2 Power Bounce (chance 60: 120, 72, 43, 25, 15...), after the Peach Beam, Mario in Danger,
    // 4 Super Charges. Cap rolls every 27 frames from +71; hit-effect draws (11 x rand(359)) one frame before each roll.
    // NOT usable on the page yet: phase 2 also has the stage lightning (fixed schedule from the battle start), which the
    // seed tracking must add before these tables are right. Model (with the lightning added) matched 13 seeds.
    fbpb6: { id: 'fbpb6', name: 'Final Bowser: Power Bounce 6+ hits', short: '6+ bounces', group: 'fb', needsStage: 'kkj_02',
      effects: { 45: Array(11).fill(359), 72: Array(11).fill(359), 99: Array(11).fill(359), 126: Array(11).fill(359) },
      rolls: [[71, 120], [98, 72], [125, 43], [152, 25]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 2,
      screen: 'Power Bounce target screen (hand on Bowser)', box: 'the クッパ name box in the top-left' },
    fbpb7: { id: 'fbpb7', name: 'Final Bowser: Power Bounce 7+ hits', short: '7+ bounces', group: 'fb', needsStage: 'kkj_02',
      effects: { 45: Array(11).fill(359), 72: Array(11).fill(359), 99: Array(11).fill(359), 126: Array(11).fill(359), 153: Array(11).fill(359) },
      rolls: [[71, 120], [98, 72], [125, 43], [152, 25], [179, 15]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 1,
      screen: 'Power Bounce target screen (hand on Bowser)', box: 'the クッパ name box in the top-left' },
    // v84, Normal Boots (pb_nb_log.py, test_pb_nb.js; the menu's boots level 0 = Power Bounce's EVS_UseMove_Basic): every
    // bounce after the first is PlayerBasicJumpToGoal 24 (Ultra: PlayerUltraJumpToGoal 25), so the cap rolls come every 26
    // frames from +77 (Ultra: 27 from +78) and each hit's 359-draws one frame after its roll. The draws per hit follow the
    // damage (Mario's jump charge on the route: Jr. Troopa T7 12 = four Super Charges, Hallway T5 6 = two; 1 + charge -
    // defence, one less per bounce). Same chances and cap rule as Ultra (BaseHitChance 200 x chance / 100 per roll).
    jrpb6n: { id: 'jrpb6n', name: 'Jr. Troopa: Power Bounce 6+ hits (Normal Boots)', short: '6+ bounces', group: 'jr', nb: true,
      effects: { 52: Array(11).fill(359), 78: Array(11).fill(359), 104: Array(11).fill(359), 130: Array(10).fill(359) },
      rolls: [[77, 140], [103, 98], [129, 68], [155, 47]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 2,
      screen: 'Power Bounce target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    jrpb5n: { id: 'jrpb5n', name: 'Jr. Troopa: Power Bounce 5+ hits (Normal Boots)', short: '5+ bounces', group: 'jr', nb: true,
      effects: { 52: Array(11).fill(359), 78: Array(11).fill(359), 104: Array(11).fill(359) },
      rolls: [[77, 140], [103, 98], [129, 68]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 2,
      screen: 'Power Bounce target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    // Hallway Bowser (chance 65: 130, 84, 54, 35, 22), Normal Boots, charge 6: 6+ hits = the first four cap rolls pass
    hwpb6n: { id: 'hwpb6n', name: 'Hallway Bowser: Power Bounce 6+ hits (Normal Boots)', short: '6+ bounces', nb: true,
      effects: { 48: Array(10).fill(359), 74: Array(10).fill(359), 100: Array(8).fill(359), 126: Array(8).fill(359) },
      rolls: [[73, 130], [99, 84], [125, 54], [151, 35]].map(([at, c]) => ({ at, max: 100, ok: v => v <= c })), vanish: 2, minRun: 1,
      screen: 'Power Bounce target screen (hand on Bowser)', box: 'the クッパ name box in the top-left' },
  };
  // Duplighosts with branching: a copy -> next roll 97 frames later; a failed copy -> tackle (8 x rand(359) on +34)
  // and the next roll 78 frames later. Measured in the emulator (13 seeds, every roll and effect matched).
  function dupSim(minCopies) {
    return function (seed, nextCoin, confirm, t0) {
      let s = seed >>> 0, nc = nextCoin, nextRoll = confirm + 13, k = 0, fails = 0; const fx = {};
      for (let t = t0 || 0; k < 4; t++) {
        if (fx[t]) for (let i = 0; i < fx[t]; i++) s = randInt(s, 359)[0];
        if (t === nextRoll) {
          const r = randInt(s, 1000); s = r[0]; k++;
          if (r[1] < 600) nextRoll = t + 97;
          else { if (++fails > 4 - minCopies) return false; fx[t + 34] = 8; nextRoll = t + 78; }
        }
        if (t === nc) { const r = randInt(s, 100); s = r[0]; nc = t + (r[1] >= 70 ? 48 : 24); }
        s = adv(s);
      }
      return true;
    };
  }
  PROFILES.dup3 = { id: 'dup3', name: 'Duplighosts: 3+ copy Bombette', short: '3+ Duplighosts copy', effects: {}, rolls: [{ at: 13 }], sim: dupSim(3),
    vanish: 2, minRun: 2, screen: PROFILES.dup4.screen, box: PROFILES.dup4.box };
  /* Duplighosts: the earliest frame in [from, to] where all 4 copy and both neighbours give 3+; returns
   * {target, window} with window = the 3+ run around it, or null */
  // base profile -> its better outcome: aim at a frame with the better outcome whose neighbours both give the base one
  const TOP = { dup3: 'dup4', jrpb5: 'jrpb6', fbpb6: 'fbpb7', jrpb5n: 'jrpb6n' };
  function aimTop(seed, from, to, baseId) {
    const P3 = PROFILES[baseId], P4 = PROFILES[TOP[baseId]], c3 = {}, w3 = f => (f in c3 ? c3[f] : (c3[f] = works(seed, 0, f, 0, P3)));
    for (let f = from + 1; f < to; f++) {
      if (!w3(f) || !w3(f - 1) || !w3(f + 1) || !works(seed, 0, f, 0, P4)) continue;
      let s = f, e = f; while (s - 1 >= from && w3(s - 1)) s--; while (e + 1 <= to && w3(e + 1)) e++;
      return { target: f, window: { start: s, end: e, length: e - s + 1 } };
    }
    return null;
  }
  /* does confirming on frame `confirm` give the profile's result? seed: value just before frame t0's draws;
   * nextCoin: frame of the next coin draw (>= t0) */
  function works(seed, nextCoin, confirm, t0, prof) {
    prof = prof || PROFILES.timeout;
    if (confirm < (t0 || 0)) return false;                       // before the known state: cannot be judged, never 'works'
    if (prof.sim) return prof.sim(seed, nextCoin, confirm, t0);
    if (!prof.rolls.length) return false;
    let s = seed >>> 0, nc = nextCoin, k = 0; const R_ = prof.rolls, last = R_[R_.length - 1].at;
    for (let t = t0 || 0; t <= confirm + last; t++) {
      const rel = t - confirm, fx = prof.effects[rel];
      if (fx) for (const mx of fx) s = randInt(s, mx)[0];
      while (k < R_.length && R_[k].at === rel) { const r = randInt(s, R_[k].max); s = r[0]; if (!R_[k].ok(r[1])) return false; k++; }
      if (t === nc) { const r = randInt(s, 100); s = r[0]; nc = t + (r[1] >= 70 ? 48 : 24); }
      const px = prof.post && prof.post[rel];                      // effect draws after the coin on that frame
      if (px) for (const mx of px) s = randInt(s, mx)[0];
      s = adv(s);
    }
    return true;
  }
  /* frames (relative to frame 0 = a coin draw whose prior seed is seedBeforeDraw) where confirming works, for
   * confirm frames from..to. Returns an array of booleans indexed from `from`. */
  function timeOutTable(seedBeforeDraw, from, to, prof) {
    const out = [];
    for (let c = from; c <= to; c++) out.push(works(seedBeforeDraw, 0, c, 0, prof));
    return out;
  }
  /* the earliest run of at least minRun consecutive working confirm frames, starting no earlier than `from` */
  function bestWindow(seedBeforeDraw, from, to, minRun, prof) {
    const tab = timeOutTable(seedBeforeDraw, from, to, prof); let runStart = -1;
    for (let i = 0; i <= tab.length; i++) {
      if (i < tab.length && tab[i]) { if (runStart < 0) runStart = i; }
      else if (runStart >= 0) { if (i - runStart >= minRun) return { start: from + runStart, end: from + i - 1, length: i - runStart }; runStart = -1; }
    }
    return null;
  }

  /* ---- first lock across gaps (coin hidden for a while: room loads, menus that cover it) ----
   * Measured in Bowser's Castle (emulator): through a room transition the RNG keeps stepping once per game frame and the
   * coin keeps drawing on its 24/48-frame schedule; the transition only runs a few extra fast frames. So a hidden
   * stretch is the same coin process continuing, and the only unknown is how many game frames passed. A gap is the
   * window [lo, hi] of frames from the previous segment's last tapped shine draw to the next segment's first. Rooms
   * with their own RNG users (enemies, effects) break this, just as they break a single segment. */
  function patSteps(p) { let L = 0; for (let i = 0; i < p.length; i++) { L++; if (i < p.length - 1) L += p.charCodeAt(i) === 83 ? 48 : 24; } return L; }
  function inv32(a) { let x = a; for (let i = 0; i < 5; i++) x = Math.imul(x, (2 - Math.imul(a, x)) >>> 0) >>> 0; return x; }
  function affInv(n) { const [A, C] = affine(n); return [A, C, inv32(A)]; }
  const applyF = (f, s) => (Math.imul(s, f[0]) + f[1]) >>> 0, applyB = (f, s) => Math.imul((s - f[1]) >>> 0, f[2]) >>> 0;
  const F24 = affInv(24), F48 = affInv(48);
  /* forward across a gap: prevPattern starts from seed c; returns seeds before nextPattern's first draw */
  // m1: the first m1 draws after the previous stretch's last shine were seen (coin still visible) and did not shine;
  // m2: the last m2 draws before the next stretch's first shine likewise (coin already back)
  function gapFwd(c, prevPattern, nextPattern, lo, hi, out, cap, m1, m2) {
    m1 = m1 || 0; m2 = m2 || 0;
    let s = afterPattern(c, prevPattern).seedAfterLastDraw, f = 48, j = 0, lastS = 0;   // segments end on a shine: next draw 48 later
    s = step48(s);
    while (f <= hi) {
      const d = adv(s), sh = d >= SHINE_MIN;
      if (sh && j < m1) return true;
      if (sh && f >= lo && f - lastS - 48 >= 24 * m2 && matches(s, nextPattern)) { out.push(s); if (out.length > cap) return false; }
      if (sh) lastS = f;
      s = sh ? step48(d) : step24(d); f += sh ? 48 : 24; j++;
    }
    return true;
  }
  /* seeds before the last segment's first draw that fit every segment. segs: [{pattern, lo, hi}], lo/hi = the gap
   * before that segment in frames (ignored for the first). The scan runs over the anchor segment's first draw value
   * t in [tlo, thi). */
  function searchChain(segs, anchor, tlo, thi, cap) {
    const P = segs.map(g => ({ p: g.pattern, lo: g.lo, hi: g.hi, m1: g.m1 || 0, m2: g.m2 || 0, Lm1: affInv(patSteps(g.pattern) - 1) })), pa = P[anchor].p, out = [];
    tlo = Math.max(tlo, SHINE_MIN); thi = Math.min(thi, 4294967296);
    for (let t = tlo; t < thi; t++) {
      let s = step48(t >>> 0), ok = true;
      for (let i = 1; i < pa.length; i++) {
        s = adv(s); const sh = s >= SHINE_MIN;
        if (sh !== (pa.charCodeAt(i) === 83)) { ok = false; break; }
        s = sh ? step48(s) : step24(s);
      }
      if (!ok) continue;
      const sa = back(t >>> 0);
      let back_ = [sa];
      for (let i = anchor; i > 0 && back_.length; i--) { const r = []; for (const x of back_) { gapBackAll(x, P[i - 1], P[i].lo, P[i].hi, r, 256, P[i].m1, P[i].m2); if (r.length >= 256) break; } back_ = r; }
      if (!back_.length) continue;
      let set = [sa];
      for (let i = anchor + 1; i < P.length && set.length; i++) { const nx = []; for (const c of set) gapFwd(c, P[i - 1].p, P[i].p, P[i].lo, P[i].hi, nx, 4096, P[i].m1, P[i].m2); set = nx; }
      for (const v of set) { out.push(v); if (out.length >= cap) return out; }
    }
    return out;
  }
  /* all start seeds of the previous segment that fit (used when the chain continues further back) */
  function gapBackAll(s, P, lo, hi, out, cap, m1, m2) {
    m1 = m1 || 0; m2 = m2 || 0;
    const st = [s, 0, 0, 0]; let n = 20000;          // seed, frames back, draws back, N draws in a row just before
    while (st.length && n-- > 0) {
      const r = st.pop(), j = st.pop(), f = st.pop(), x = st.pop();
      const y48 = applyB(F48, x);
      if (y48 >= SHINE_MIN && f + 48 <= hi && j + 1 > m2) {
        if (f + 48 >= lo && r >= m1) { const c = applyB(P.Lm1, back(y48)); if (matches(c, P.p)) { out.push(c); if (out.length >= cap) return; } }
        st.push(back(y48), f + 48, j + 1, 0);
      }
      const y24 = applyB(F24, x);
      if (y24 < SHINE_MIN && f + 24 <= hi) st.push(back(y24), f + 24, j + 1, r + 1);
    }
  }
  /* carry candidates across a long gap (the coin hidden for minutes: a cutscene, C-up closed through rooms with other
   * random numbers): the next stretch starts lo..hi steps after each candidate's last draw */
  function extendWide(cands, prevPattern, nextPattern, lo, hi, cap) {
    const out = [];
    for (const c of cands) {
      const r = resync(afterPattern(c, prevPattern).seedAfterLastDraw, nextPattern, hi, cap, lo);
      for (const x of r) { out.push(x.seed); if (out.length > cap) return null; }
    }
    return out;
  }
  /* the same across a gap that ends in a torch room (12 draws every 50 frames, unknown phase): [{seed, phase}] */
  function extendWideTorch(cands, prevPattern, nextPattern, lo, hi, cap) {
    const out = [];
    for (const c of cands) {
      const r = resyncTorch(afterPattern(c, prevPattern).seedAfterLastDraw, nextPattern, hi, cap, lo);
      for (const x of r) { out.push({ seed: x.seed, phase: x.phase }); if (out.length > cap) return null; }
    }
    return out;
  }
  /* carry candidates (seeds before prevPattern's first draw) across one gap; null if too many */
  function extendCands(cands, prevPattern, nextPattern, lo, hi, cap, m1, m2) {
    const out = [];
    for (const c of cands) if (!gapFwd(c, prevPattern, nextPattern, lo, hi, out, cap, m1, m2)) return null;
    return out;
  }

  /* ---- carrying the seed through whole turns (no shines needed between planned presses) ----
   * Measured in the emulator (Jr. Troopa T3 -> T6, 6 runs, random seeds and confirm timing): from each confirm, the
   * turn's random draws land on the same frames with the same ranges every time, for the route's outcome (Close Call
   * lands). TURNS[id]: pre/post = draws before/after the frame's coin draw, keyed by frames after the confirm; eio = the
   * Super Charge sparkles (energy_in_out: created on +c, 10 parts each with rand(10) speed and rand(10) start phase,
   * every part redraws rand(359) each time its 10-frame counter wraps, from the frame it is created until +r). The coin
   * keeps its 24/48-frame schedule through all of it. */
  const TURNS = {"jr_bomb_cc":{"pre":{"73":[359,359,359,359,359,359,359,359],"179":[100]},"post":{"73":[360]}},"jr_bomb":{"pre":{"73":[359,359,359,359,359,359,359,359]},"post":{"73":[360]}},"jr_syrup_cc":{"pre":{"118":[359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10],"163":[100]},"post":{}},"jr_nothing_cc":{"pre":{"26":[100]},"post":{}},"jr_charge":{"pre":{},"post":{},"eio":[[13,58],[16,61]]},"jr_whacka":{"pre":{"118":[359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10,359,10,10],"190":[359,359,359,359,359,359,359,359,359,359]},"post":{}},"hw_charge":{"pre":{},"post":{},"eio":[[13,58],[16,61]]},"hw_spiny":{"pre":{},"post":{},"eio":[[39,119,20]],"impact":[359,359,359,359,359,359,359,359],"ai":44}};
  /* Jr. Troopa on the Charge-lock route (jr_charge/README.md, jc_model.py; checked frame by frame against emulator runs by
   * jr_charge/jc_check_core.js): the T1 Bomb with Jr. Troopa's T1 hit on Mario at 10 HP (+206, no roll), and the turns at
   * 10 HP after a Life Shroom revive (no Close Call roll, the hit lands): Maple Syrup (15 sparkles, the hit at +190) and
   * Bombette doing nothing (the hit at +53). */
  const X359 = n => Array(n).fill(359);
  TURNS.jr_bomb_t1 = { pre: { 73: X359(8), 206: X359(10) }, post: { 73: [360] } };
  TURNS.jr_syrup_hit = { pre: { 118: [].concat(...Array(15).fill([359, 10, 10])), 190: X359(10) }, post: {} };
  TURNS.jr_nothing_hit = { pre: { 53: X359(10) }, post: {} };
  /* v85, the Normal Boots route (charge_live/README.md v85; nb_cc/jr_route_log.py, nb_cc/gch_log.py, checked frame by frame
   * by test_nb_cc_model.js). Goombario's Charge (nb_gch, frame 0 = its target-screen A): energy_in_out on +14 and +17 (as
   * Mario's Charge, one frame later), then "attack power up" in a message box that A closes (cancel A, popup duration 60:
   * A on +73..+132 ends his turn 5 frames later; no A = +133). Everything after hangs off that frame P (nb_jrcc /
   * nb_hwcc / nb_jrhit, frame 0 = P): Jr. Troopa's Close Call rand_int(100) on P + 29 (Mario under 6 HP; a dodge draws
   * nothing more up to the next menu at P + 97), his hit at 10 HP on P + 56; Hallway Bowser's AI (RandInt 80 / 60) on
   * P + 16, then the Close Call as bowserT1 (AI + 54 / 70 / 55). Maple Syrup (nb_syrup): its sparkles on +118. Goombario's
   * Headbonk x2 (nb_hb, frame 0 = its target-screen A; the action command pressed in both windows): the hits' 10 x
   * rand(359) on +54 and +80 (8 damage each: four Charges), Jr. Troopa's Close Call on +143 (the hit at 10 HP on +170).
   * Whacka's Bump (nb_whacka): 22 sparkles on +118; then Goombario's Do Nothing (jr_nothing_hit at 10 HP). */
  TURNS.nb_gch = { pre: {}, post: {}, eio: [[14, 59], [17, 62]] };
  TURNS.nb_jrcc = { pre: { 29: [100] }, post: {} };
  TURNS.nb_jrhit = { pre: { 56: X359(10) }, post: {} };
  TURNS.nb_hwcc = { pre: {}, post: {}, aiAt: 16 };
  TURNS.nb_syrup = { pre: { 118: [].concat(...Array(10).fill([359, 10, 10])) }, post: {} };
  TURNS.nb_hb = { pre: { 54: X359(10), 80: X359(10), 143: [100] }, post: {} };
  TURNS.nb_hb_hit = { pre: { 54: X359(10), 80: X359(10), 170: X359(10) }, post: {} };
  TURNS.nb_whacka = { pre: { 118: [].concat(...Array(22).fill([359, 10, 10])) }, post: {} };
  const NB_K = { lo: 73, hi: 132, none: 133, back: 5, jrcc: 29, jrnext: 97, hwai: 16 };
  /* evs: [{f, id}] (f = frame of the confirm, in the caller's frame numbering) -> Map frame -> {pre, post, eio} */
  function buildEv(list) {
    const m = new Map(), get = f => { let e = m.get(f); if (!e) { e = { pre: [], post: [], eio: [] }; m.set(f, e); } return e; };
    for (const { f, id, imp, guard, danger } of list || []) {
      const T = TURNS[id]; if (!T) continue;
      for (const o in T.pre) get(f + +o).pre.push(...T.pre[o]);
      for (const o in T.post) get(f + +o).post.push(...T.post[o]);
      for (const [c, r, per] of T.eio || []) get(f + c).eio.push([f + r, per || 10]);
      if (T.impact && imp != null) { get(f + imp).pre.push(...T.impact); const a = get(f + imp + T.ai); a.ai = id; a.guard = !!guard; a.danger = !!danger; }
      if (T.aiAt != null) { const a = get(f + T.aiAt); a.ai = id; a.guard = false; a.danger = true; }      // v85 nb_hwcc: Bowser's AI at 3 HP
    }
    return m;
  }
  /* one game frame: battle-script draws, effect creation, the coin (if due), effect updates, the frame step.
   * S = {s, nc, inst}; returns null, or whether the coin drew a shine */
  /* Hallway Bowser's T1 AI (EVS_UseAttack): RandInt(80) < 20 Body Slam; else RandInt(60) < 20 Claw Swipe (frame +72:
   * rand(100) then 10 x rand(359); +231: 6 x rand(359)); else Fire Breath (no draws). All three measured in the emulator (18 runs). */
  /* guarded (A just before the hit): Body Slam and Claw Swipe only draw their 10 x rand(359) (+71 / +72) */
  /* v78/v79, Mario at 5 HP or less (Danger: the runner's Hallway at 3 HP; charge_live/README.md v78, 17 emulator runs): every
   * attack first rolls Close Call, rand_int(100) < 30 (caller 0x80277518, in EnemyTestTarget), at AI + 54 (Body Slam),
   * + 70 (Claw Swipe), + 55 (Fire Breath). Lucky: the attack misses and nothing more is drawn to the next menu (Claw
   * Swipe and Fire Breath measured; Body Slam's miss branch has no random call in the script). Not lucky: the hit kills
   * Mario (5+ damage at 3 HP; Game Over or a Life Shroom revive), which is not modelled: S.ccHit, S.unknown. The guard
   * comes after the roll and changes nothing on either branch. S.cc = { f, v, lucky } once rolled. The impact frame stays
   * open (hw_spiny imp: the throw is the impact - 24); the page carries roll / no-roll by Mario's HP (charge_live/hwcc_live.js). */
  const HW_CC = { 'body slam': 54, 'claw swipe': 70, 'fire breath': 55 };
  function bowserT1(S, f, guard, danger) {
    S.extra = S.extra || new Map();
    if (danger) {
      const a = randInt(S.s, 80); S.s = a[0];
      if (a[1] < 20) S.branch = 'body slam'; else { const b = randInt(S.s, 60); S.s = b[0]; S.branch = b[1] < 20 ? 'claw swipe' : 'fire breath'; }
      S.ccAt = f + HW_CC[S.branch]; return;
    }
    const a = randInt(S.s, 80); S.s = a[0];
    if (a[1] < 20) {                                                  // Body Slam: +71 10 x rand(359), +76 2 x rand(2), +133/139/145 6 x rand(359)
      S.branch = 'body slam'; S.extra.set(f + 71, Array(10).fill(359));
      if (!guard) { S.extra.set(f + 76, [2, 2]); for (const o of [133, 139, 145]) S.extra.set(f + o, Array(6).fill(359)); }
      return;
    }
    const b = randInt(S.s, 60); S.s = b[0];
    if (b[1] < 20) {
      S.branch = 'claw swipe';
      if (guard) S.extra.set(f + 72, Array(10).fill(359));
      else { S.extra.set(f + 72, [100].concat(Array(10).fill(359))); S.extra.set(f + 231, Array(6).fill(359)); }
    } else S.branch = 'fire breath';
  }
  function frameEv(S, f, ev) {
    const e = ev && ev.get(f); let r = null;
    if (e) {
      for (const mx of e.pre) S.s = randInt(S.s, mx)[0];
      if (e.ai) bowserT1(S, f, e.guard, e.danger);
      for (const [rm, per] of e.eio) {
        S.s = randInt(S.s, 360)[0]; const p = [];
        for (let i = 0; i < 10; i++) { S.s = randInt(S.s, 10)[0]; const q = randInt(S.s, per); S.s = q[0]; p.push(-q[1]); }
        S.inst.push({ rm, per, p });
      }
    }
    if (S.extra && S.extra.has(f)) { for (const mx of S.extra.get(f)) S.s = randInt(S.s, mx)[0]; S.extra.delete(f); }
    if (S.ccAt === f) { const q = randInt(S.s, 100); S.s = q[0]; S.ccAt = null; S.cc = { f, v: q[1], lucky: q[1] < 30 }; if (!S.cc.lucky) { S.ccHit = true; S.unknown = true; } }
    if (f === S.nc) { const q = randInt(S.s, 100); S.s = q[0]; r = q[1] >= 70; S.nc = f + (r ? 48 : 24); }
    if (e) for (const mx of e.post) S.s = randInt(S.s, mx)[0];
    if (S.inst.length) {
      for (const I of S.inst) if (f < I.rm) for (let i = 0; i < 10; i++) { if (++I.p[i] >= (I.per || 10)) { I.p[i] = 0; S.s = randInt(S.s, 359)[0]; } }
      S.inst = S.inst.filter(I => f + 1 < I.rm);
    }
    S.s = adv(S.s);
    return r;
  }
  /* pattern check / positions with turn events (frame 0 = the pattern's first draw; seed = value before frame 0) */
  function walkEv(seed, pattern, ev, stopAtLast) {
    const S = { s: seed >>> 0, nc: 0, inst: [] }; let i = 0;
    for (let f = 0; f < 200000; f++) {
      if (stopAtLast && f === S.nc && i === pattern.length - 1) return { ok: true, seedBeforeLast: S.s, f };
      const before = S.s, r = frameEv(S, f, ev);
      if (r !== null) {
        if (r !== (pattern.charCodeAt(i) === 83)) return { ok: false };
        if (++i === pattern.length) return { ok: true, S, f, before };
      }
    }
    return { ok: false };
  }
  function afterPatternEv(seed, pattern, ev) { if (!(ev && ev.size)) return afterPattern(seed, pattern); const w = walkEv(seed, pattern, ev); return { seedAfterLastDraw: w.ok ? w.S.s : afterPattern(seed, pattern).seedAfterLastDraw }; }
  function matchesEv(seed, pattern, ev) { return ev && ev.size ? walkEv(seed, pattern, ev).ok : matches(seed, pattern); }
  function seedBeforeLastDrawEv(seed, pattern, ev) { return ev && ev.size ? walkEv(seed, pattern, ev, true).seedBeforeLast : seedBeforeLastDraw(seed, pattern); }
  /* plan base after the turns: the first coin-draw frame F >= minF with every event done and no sparkles alive; returns
   * the seed before frame F (a coin draw, so plans can start there exactly as from a tapped shine) */
  function baseAfter(seed, ev, minF) {
    const S = { s: seed >>> 0, nc: 0, inst: [] }; let last = 0;
    for (const f of ev.keys()) last = Math.max(last, f);
    for (const e of ev.values()) for (const [rm] of e.eio) last = Math.max(last, rm);
    for (let f = 0; f < 400000; f++) {
      if (S.unknown) return null;
      if (f >= minF && f > last && f === S.nc && !S.inst.length && !(S.extra && S.extra.size) && S.ccAt == null) return { seed: S.s, F: f, branch: S.branch };
      frameEv(S, f, ev);
    }
    return null;
  }

  /* ---- torch rooms (the Duplighost room kpa_53, the Heart Block room kpa_114) ----
   * Measured (12 runs): exactly 12 draws every 50 frames, after the coin when they share a frame, on a phase fixed by
   * the room load (unknown to the page: 50 possibilities). Between two coin draws on frames F and F+g the RNG steps
   * g + 12 x (torch frames in [F, F+g)). */
  const JUMP = (function () { const A = new Uint32Array(2400), C = new Uint32Array(2400); A[0] = 1; for (let i = 1; i < 2400; i++) { A[i] = Math.imul(A[i - 1], MUL) >>> 0; C[i] = (Math.imul(C[i - 1], MUL) + 1) >>> 0; } return { A, C }; })();
  const jumpN = (s, n) => (Math.imul(s, JUMP.A[n]) + JUMP.C[n]) >>> 0;
  const torchesIn = (a, b, ph) => { let n = 0; for (let f = a; f < b; f++) if (((f - ph) % 50 + 50) % 50 === 0) n++; return n; };
  function walkTorch(seed, pattern, ph, upto) {          // returns the seed before draw `upto` (or after the whole pattern), or -1 if the pattern breaks
    let s = seed >>> 0, F = 0;
    for (let i = 0; i < pattern.length; i++) {
      if (i === upto) return s;
      const d = adv(s), sh = d >= SHINE_MIN;
      if (sh !== (pattern.charCodeAt(i) === 83)) return -1;
      const g = sh ? 48 : 24;
      if (i === pattern.length - 1) return upto === -2 ? jumpN(d, 0) : d;   // after the last draw
      s = jumpN(d, g + 12 * torchesIn(F, F + g, ph)); F += g;
    }
    return s;
  }
  const matchesTorch = (seed, pattern, ph) => walkTorch(seed, pattern, ph) !== -1;
  const seedBeforeLastDrawTorch = (seed, pattern, ph) => walkTorch(seed, pattern, ph, pattern.length - 1);
  /* first lock inside a torch room: every seed whose first draw shines, every torch phase; the first gap holds 0 or 1
   * torch bursts, so most seeds are ruled out by checking the second draw both ways before trying the 50 phases */
  function searchShineStartTorch(pattern, lo, hi, cap) {
    // depth-first over "a torch burst in this gap or not" (gaps are under 50 frames: 0 or 1), keeping the set of torch
    // phases (50 bits, as two 25-bit halves) that agree; most seeds die within a few draws
    const out = []; lo = Math.max(lo, SHINE_MIN); hi = Math.min(hi, 4294967296);
    if (!searchShineStartTorch.M) {
      const M = { 24: [], 48: [] };
      for (const g of [24, 48]) for (let f = 0; f < 50; f++) { let a = 0, b = 0; for (let ph = 0; ph < 50; ph++) if (torchesIn(f, f + g, ph) > 0) { if (ph < 25) a |= 1 << ph; else b |= 1 << (ph - 25); } M[g].push([a, b]); }
      searchShineStartTorch.M = M;
    }
    const M = searchShineStartTorch.M, FULL = (1 << 25) - 1, L = pattern.length, P = [];
    for (let i = 0; i < L; i++) P.push(pattern.charCodeAt(i) === 83);
    let s0t = 0, full = false;
    const rec = (d, F, i, ma, mb) => {
      if (i === L - 1) {
        const s0 = back(s0t);
        for (let ph = 0; ph < 50; ph++) if (ph < 25 ? (ma >> ph) & 1 : (mb >> (ph - 25)) & 1) { out.push({ seed: s0, phase: ph }); if (out.length >= cap) { full = true; return; } }
        return;
      }
      const g = P[i] ? 48 : 24, m = M[g][F % 50], want = P[i + 1];
      let na = ma & ~m[0], nb = mb & ~m[1];
      if (na || nb) { const e = adv(jumpN(d, g)); if ((e >= SHINE_MIN) === want) { rec(e, F + g, i + 1, na, nb); if (full) return; } }
      na = ma & m[0]; nb = mb & m[1];
      if (na || nb) { const e = adv(jumpN(d, g + 12)); if ((e >= SHINE_MIN) === want) rec(e, F + g, i + 1, na, nb); }
    };
    for (let t = lo; t < hi && !full; t++) { s0t = t >>> 0; rec(s0t, 0, 0, FULL, FULL); }
    return out;
  }
  /* re-lock in a torch room: every start n in [nlo, nmax] steps after `from` and every phase */
  function resyncTorch(from, pattern, nmax, cap, nlo) {
    const out = []; let s = from >>> 0; nlo = Math.max(0, nlo || 0);
    for (let i = 0; i < nlo; i++) s = adv(s);
    for (let n = nlo; n <= nmax; n++) {
      if ((adv(s) >= SHINE_MIN) === (pattern.charCodeAt(0) === 83))
        for (let ph = 0; ph < 50; ph++) if (matchesTorch(s, pattern, ph)) { out.push({ n, seed: s, phase: ph }); if (out.length >= (cap || 64)) return out; }
      s = adv(s);
    }
    return out;
  }

  /* ---- v84: Final Bowser phase 2, Bowser's attack choice (decomp src/battle/area/kpa2/actor/final_bowser_2.c
   * EVS_TakeTurn_Inner -> EVS_UseAttackOrShockwave / EVS_UseAttack; charge_live/README.md v84). v: Bowser's actor vars
   * as they stand before his turn (AVAR_TurnCount, the TurnsSince* counters, RecoversLeft), enchanted (the Star Rod's
   * aura: ACTOR_EVENT_FLAG_STAR_ROD_ENCHANTED), charged (Mario's jump or hammer charge > 0), hpGap (Mario's HP % minus
   * Bowser's). Every RandInt the script makes, in order, from seed s; returns the attack ('recover', 'starrod', 'wave' =
   * the Draining Shockwave, 'lightning', 'slam', 'claw', 'fire'), the draws [max, value], the seed after them and the vars
   * after the turn (the counters the chosen attack resets). */
  function fbnbAi(s, v0) {
    const v = Object.assign({}, v0), draws = [], ri = mx => { const r = randInt(s, mx); s = r[0]; draws.push([mx, r[1]]); return r[1]; };
    v.turn++; v.sinceClaw++; v.sinceSlam++; v.sinceShock++; v.sinceStar++; v.sinceRecover++;
    const done = atk => { if (atk === 'slam') v.sinceSlam = 0; if (atk === 'claw') v.sinceClaw = 0; if (atk === 'wave') v.sinceShock = 0; if (atk === 'starrod') v.enchanted = true; if (atk === 'recover') { v.sinceRecover = 0; v.recovers = Math.max(0, (v.recovers || 0) - 1); } return { atk, draws, s, v }; };
    if ((v.hpGap || 0) > 25 && v.recovers) {
      if (ri(100) < 75) { if (v.sinceRecover > 1) return done('recover'); if (ri(100) < 0) return done('recover'); }
    }
    if (v.turn > 1 && !v.enchanted) {
      const ch = v.sinceStar === 1 || v.sinceStar === 2 ? 0 : v.sinceStar === 3 ? 15 : 75;
      if (ri(100) < ch) return done('starrod');
    }
    const attack = () => {
      if (ri(80) < 20 && v.sinceSlam >= 2) return done('slam');
      if (ri(60) < 20 && v.sinceClaw >= 2) return done('claw');
      return done('fire');
    };
    if (v.sinceShock < 3 || v.turn <= 3) return attack();
    if (v.sinceShock >= 6) return done(ri(30) < 20 ? 'wave' : 'lightning');
    if (ri(100) < 75 && v.charged) return done('wave');
    const x = ri(110); if (x < 30) return done(x < 20 ? 'wave' : 'lightning');
    return attack();
  }
  /* the Normal Boots route's phase 2 (Peach Beam on T1, Super Charges from T2, Mario at 1 HP: Close Call rand_int(100) < 30,
   * 1A5830.c): the vars before Bowser's turn t when every earlier turn was an allowed one (Peach Beam resets
   * TurnsSinceStarBeam at T1; no wave yet), and the blind chance that turn t is a Close Call on an allowed attack (not the
   * Star Rod, not the Draining Shockwave; the Lightning Blast is allowed: it tests Mario like the normal attacks).
   * Exact over the RandInt values (uniform 0..max; RandInt(100) on 0..1009 / 10). */
  function fbnbVars(t) { return { turn: t - 1, sinceClaw: 3 + t - 1, sinceSlam: 3 + t - 1, sinceShock: t - 1, sinceStar: t - 1, sinceRecover: t - 1, recovers: 3, enchanted: false, charged: t >= 2, hpGap: 0 }; }
  function fbnbTurnBlind(t, v) {
    v = v || fbnbVars(t); const P100 = k => (Math.min(100, Math.max(0, k)) * 10) / 1010, Pu = (k, n) => Math.min(n + 1, Math.max(0, k)) / (n + 1);
    const turn = v.turn + 1, sShock = v.sinceShock + 1, sStar = v.sinceStar + 1; let p = 1;
    if (turn > 1 && !v.enchanted) p *= 1 - P100(sStar === 1 || sStar === 2 ? 0 : sStar === 3 ? 15 : 75);
    if (!(sShock < 3 || turn <= 3)) {
      if (sShock >= 6) p *= 1 - Pu(20, 30);
      else { p *= v.charged ? 1 - P100(75) : 1; p *= 1 - Pu(20, 110); }
    }
    return p * P100(30);
  }
  /* v85 Normal Boots Close Call profiles (TURNS nb_*; charge_live/README.md v85). The cancel modes: "confirm" = the A that
   * closes Goombario's "attack power up" box (P, +73..+132 from his Charge's target-screen A). The wait modes: "confirm" =
   * that target-screen A itself (G), the box running out (P = G + 133). Headbonk: its target-screen A. */
  function evSim(list, rollAt) {      // list(c) -> buildEv list; rollAt(c): a plain roll frame (first draw), else S.cc decides
    return function (seed, nc, c, t0) {
      const S = { s: seed >>> 0, nc, inst: [] }, ev = buildEv(list(c)), ra = rollAt ? rollAt(c) : null;
      for (let f = t0 || 0; f < c + 400; f++) {
        if (ra != null && f === ra) return randInt(S.s, 100)[1] < 30;
        frameEv(S, f, ev);
        if (S.cc) return S.cc.lucky;
      }
      return false;
    };
  }
  const NB_SCREEN_G = 'Goombario\'s Charge target screen (hand on Goombario)';
  Object.assign(PROFILES, {
    jrcc_gch: { id: 'jrcc_gch', name: 'Jr. Troopa: Close Call after Goombario\'s Charge (the A that closes its box)', short: 'Close Call', group: 'jr', nb: true, lever: 'cancel',
      effects: {}, rolls: [{ at: NB_K.jrcc, max: 100, ok: v => v < 30 }], vanish: 0, minRun: 2, screen: 'Goombario\'s "attack power up" box', box: 'the box' },
    jrcc_gchw: { id: 'jrcc_gchw', name: 'Jr. Troopa: Close Call after Goombario\'s Charge (box left to run out)', short: 'Close Call', group: 'jr', nb: true, lever: 'wait',
      effects: {}, rolls: [{ at: NB_K.none + NB_K.jrcc }], sim: evSim(c => [{ f: c, id: 'nb_gch' }], c => c + NB_K.none + NB_K.jrcc), vanish: 2, minRun: 2, screen: NB_SCREEN_G, box: 'the name box in the top-left' },
    jrcc_hb: { id: 'jrcc_hb', name: 'Jr. Troopa: Close Call after Goombario\'s Headbonk x2', short: 'Close Call', group: 'jr', nb: true,
      effects: { 54: X359(10), 80: X359(10) }, rolls: [{ at: 143, max: 100, ok: v => v < 30 }], vanish: 2, minRun: 2, screen: 'Goombario\'s Headbonk target screen (hand on Jr. Troopa)', box: 'the name box in the top-left' },
    hwcc_gch: { id: 'hwcc_gch', name: 'Hallway Bowser: Close Call after Goombario\'s Charge (the A that closes its box)', short: 'Close Call', group: 'jr', nb: true, lever: 'cancel',
      effects: {}, rolls: [{ at: NB_K.hwai }], sim: evSim(c => [{ f: c, id: 'nb_hwcc' }]), vanish: 0, minRun: 2, screen: 'Goombario\'s "attack power up" box', box: 'the box' },
    hwcc_gchw: { id: 'hwcc_gchw', name: 'Hallway Bowser: Close Call after Goombario\'s Charge (box left to run out)', short: 'Close Call', group: 'jr', nb: true, lever: 'wait',
      effects: {}, rolls: [{ at: NB_K.none + NB_K.hwai }], sim: evSim(c => [{ f: c, id: 'nb_gch' }, { f: c + NB_K.none, id: 'nb_hwcc' }]), vanish: 2, minRun: 2, screen: NB_SCREEN_G, box: 'the name box in the top-left' } });
  const api = { NB_K, evSim, fbnbAi, fbnbVars, fbnbTurnBlind, MUL, FRAME_MS, SHINE_MIN, adv, internal, randInt, patternFromTaps, matches, searchRange, afterPattern,
    seedBeforeLastDraw, resync, searchShineStart, back, timeOutRoll, timeOutTable, bestWindow, EFFECTS, ROLL, PROFILES, works, aimTop, TOP, searchChain, extendCands, extendWide, extendWideTorch, patSteps, TURNS, buildEv, frameEv, matchesEv, seedBeforeLastDrawEv, afterPatternEv, baseAfter, matchesTorch, seedBeforeLastDrawTorch, walkTorch, resyncTorch, searchShineStartTorch, aim4: (s, a, b) => aimTop(s, a, b, 'dup3') };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PMRNG = api;
})(typeof self !== 'undefined' ? self : this);
