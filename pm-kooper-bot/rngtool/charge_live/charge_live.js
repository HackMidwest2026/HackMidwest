//@ Charge rays -> gRandSeed, live (charge_live/README.md). Inlined into page_template.html by shared/inline.py; //@ lines
//@ are dropped. Needs the page globals R, FRAME, $, num, slog, st, zw, V, sample, isRoute, RT, routeStep, render and the
//@ zw* tracker. Build fills CHG_CAMS, CHG_MARIO, CHG_CAMS_FB2, CHG_MARIO_FB2 and CHG_WASM (build_page.py).
/* ---------- Charge lock: the seed from Mario's (Super) Charge rays on Hallway Bowser T1 ----------
 * Turn 1 of Hallway Bowser starts with Mario's Charge: two energy_in_out effects (10 rays each) whose angles, speeds
 * and start phases are random draws. The page keeps the capture frames from the Charge's burst onset (the screen
 * brightens 3 game frames after frame 0 = Charge confirm + 13), maps the rays (a ridge filter along every integer
 * angle from Mario, the radial burst removed by subtracting each angle's median), and searches all 2^32 seeds in
 * workers (charge_live/kernel.c as WebAssembly; exact top-K by base angle with branch and bound, then the full
 * simulation over the first-coin frame q). A clear winner seeds the zero-wait tracker (zw*) with
 * seed x q x console lag particles at frame 0; the Spiny Flip, Bowser's attack and the coin on the menus are carried
 * as before, and Time Out's target screen beeps the best frame or says No edge. */
const CHG_CAMS = /*CHG_CAMS*/null, CHG_MARIO = /*CHG_MARIO*/null, CHG_WASM = '/*CHG_WASM*/';
const CHG_CAMS_FB2 = /*CHG_CAMS_FB2*/null, CHG_MARIO_FB2 = /*CHG_MARIO_FB2*/null;
const CHG_N = 48, CHG_ND = 96, CHG_MAP0 = [3.2637, 272.82, 3.3221, -31.09];  // capture 1280x720 = S*x + O (x in 320 space), fitted on the route clips' OBS layout
/* the runner's adjustment (Settings: Charge area size / shift), applied about the game picture's centre: the purple frame
 * on the camera preview is the 320x240 game raster this map gives, so it can be lined up with the real game picture */
function chgMap() {
  const k = (num('chgsc') || 100) / 100, dx = num('chgdx'), dy = num('chgdy'), [SX, OX, SY, OY] = CHG_MAP0;
  return [SX * k, OX + 160 * SX * (1 - k) + dx, SY * k, OY + 120 * SY * (1 - k) + dy];
}
/* the game area the burst trigger averages (320-space x 23.5..299.2, y 39.5..220: the old fixed box), in 0..1 capture units */
function chgGame() { const [SX, OX, SY, OY] = chgMap(); return { x: (OX + 23.5 * SX) / 1280, y: (OY + 39.5 * SY) / 720, w: 275.7 * SX / 1280, h: 180.5 * SY / 720 }; }
/* the purple frame on the preview: the game picture's edges as the route clips show them (320-space x 11.4..308.6,
 * y 9.4..219.8; in the clips' layout the top and right edges are the capture's own, the left and bottom edges are the
 * picture's), in 0..1 capture units. Lined up with the real picture, the Charge rays land where the page looks. */
function chgFrameBox() { const [SX, OX, SY, OY] = chgMap(); return { x: (OX + 11.4 * SX) / 1280, y: (OY + 9.4 * SY) / 720, w: 297.2 * SX / 1280, h: 210.4 * SY / 720 }; }
const CHG_BRIGHT = [7.2, 12.5, 19.4, 28, 35.9, 42.1, 47.6, 49.2, 50.4, 53.9, 56.4, 56.9, 58.8, 61.2, 61.2, 61.7, 60.7, 62.1, 59.9, 57.1, 55.5, 50, 45.4,
  40.7, 29.8, 20.3, 14.7, 8.3, 3.4, 2.2, 4.2, 6.5, 7.3, 6.9, 6.8, 6.6, 6.5, 6.3, 6.2, 6, 6, 6, 5.9];   // game area brightness above the menu, frames 3..45
/* Per-fight profiles. The search, the maps and the trigger are the same; what differs per fight is the camera table, Mario's
 * reference patch, the burst's brightness curve over the fight's background, the nuisance draws interleaved with the
 * ray draws (Final Bowser: the stage lightning, one rand_int(359) per bolt before everything else on its frame;
 * fb2_route/t6_raycheck.py, 3 emulator runs exact incl. bolts on frames 0 and 3), and what the lock starts.
 * hw: Hallway Bowser T1 (unchanged). fb2: Final Bowser phase 2 T6, the route step whose turn is fb2_pb (its pre is
 * the T6 Charge); the lock starts the FB2 tracker (fb2_live.js), stage 1 starts on frames 0..22 while the capture goes on
 * (the initial rays live there; the K window closes 76 frames after the rays), and stage 2 scores every lightning
 * pattern (phases p130 = p220 mod 5) x q. offs: LCG steps from A's base-angle draw to B's (24 + a coin on frames 0-2
 * + bolts on frames 1-3). */
// FB2: the burst over the arena (emulator T6 render through the capture simulation, fb2_route/t6_capsim.py; frames 0-2
// read 1.6, 3.5, 6.0, so the trigger is 7.5 above the menu: frame 3; the one real FB2 clip, 14-47-09 with the aura,
// reads 5.2, 9.4, 15.8, 24 on frames 2-5). The tail goes below the menu: the default camera is darker there.
const CHG_BRIGHT_FB2 = [11, 16.2, 22.4, 28.4, 33.8, 38.7, 42.2, 42.8, 43.7, 46.3, 47.6, 47.7, 49.4, 50.3, 50, 49.9, 47.6, 48.1, 46.1, 44.2, 43.2, 39.9,
  37.8, 34.7, 27.5, 20.7, 14, 9.6, 5.4, 1.5, 2.4, -1.4, -5.2, -6.9, -7.1, -7, -7.1, -7.1, -7, -6.9, -6.9, -7, -6.9];   // frames 3..45
/* Duplighosts T1 (dup_charge/README.md): Mario's Super Charge first, then Bombette's Do Nothing. The battle camera is
 * bit-identical to the Hallway's on all 48 frames (readouts/data/charge_cams_mario_dup.json = charge_cams_mario_route.json),
 * so the Hallway table is used; Mario's Hallway capture patch scores NCC 0.90 on this arena's emulator render (the
 * Hallway's own 0.92). The burst over this room: the page's Hallway curve on frames 0-33 (within 0.7 levels in the
 * emulator), then 1.6-2.8 darker once the camera swings back (charge_dup_reader.json CHG_BRIGHT_dup_suggested: unverified
 * on console). No nuisance draws in the rays (the torches of kpa_01 draw nothing). */
const CHG_BRIGHT_DUP = [7.0, 12.3, 18.8, 27.3, 35.2, 41.8, 47.3, 49.0, 50.6, 54.2, 56.5, 57.3, 59.2, 61.6, 61.4, 61.6, 60.5, 61.7, 59.9, 57.5, 56.0, 50.7, 45.9,
  41.1, 30.3, 20.7, 14.7, 8.2, 3.2, 2.2, 4.2, 4.3, 4.5, 4.8, 4.8, 4.5, 4.4, 4.3, 4.1, 4.0, 4.1, 4.2, 4.3];   // frames 3..45
/* Jr. Troopa T1 / T3 / T5 (jr_charge/README.md section 5): the battle camera is bit-identical to the Hallway's (all 48
 * frames, any turn, any seed; readouts/data/charge_cams_mario_jr.json), so the Hallway table is used; the Hallway capture
 * Mario patch matches the Jr. render at NCC 0.88 (dy -3). The burst over this arena: the page's Hallway curve plus the
 * emulator's Jr. - Hallway difference (charge_jr_reader.json CHG_BRIGHT_jr_suggested: unverified on a capture). No
 * nuisance draws in the rays. */
const CHG_BRIGHT_JR = [6.3, 11.6, 18.3, 26.5, 34.0, 40.2, 45.9, 47.2, 48.8, 52.5, 54.9, 55.8, 57.2, 59.5, 59.4, 59.3, 58.1, 59.9, 58.5, 56.1, 55.1, 49.7, 45.2,
  40.4, 29.7, 20.5, 14.7, 8.2, 3.2, 1.8, 3.7, 3.1, 3.0, 3.0, 3.1, 3.0, 2.9, 2.9, 3.0, 2.8, 2.7, 2.8, 2.7];   // frames 3..45
/* Final Bowser phase 2, T1-T4 (Bowser's star aura up; fb14_live.js): the burst over the arena with Lakilester beside Mario
 * (emulator T1 render through the capture simulation, fb2_route/t14_log.py SHOTS + t6_capsim.py: frames 0-2 read -1.0,
 * 0.9, 3.4; frame 3 is the trigger at 6 above the menu; unverified on console) */
const CHG_BRIGHT_FB1 = [8.3, 13.5, 19.5, 25.2, 30.4, 34.8, 38.2, 38.6, 39.4, 42.0, 43.2, 43.4, 44.9, 46.6, 46.2, 46.2, 44.1, 44.5, 42.3, 40.9, 40.0, 37.7,
  34.8, 31.6, 24.3, 17.5, 10.8, 6.1, 1.9, -1.9, -0.8, 2.1, -2.7, -6.0, -6.5, -6.7, -7.1, -7.7, -7.9, -8.2, -8.3, -8.6, -8.5];   // frames 3..45
const CHG_PROF = {
  hw: { id: 'hw', turn: 'hw_spiny', cams: () => CHG_CAMS, mario: () => CHG_MARIO, bright: () => CHG_BRIGHT, bolts: false, early: false, offs: [24, 25], effects: [0, 1], trigLo: 5, trigHi: 25, trigN: true, tol: () => 1.5, trigMin: 250, trigMax: 1000, baseMin: 30, shape: true },
  fb2: { id: 'fb2', turn: 'fb2_pb', cams: () => CHG_CAMS_FB2 || CHG_CAMS, mario: () => CHG_MARIO_FB2 || CHG_MARIO, bright: () => CHG_BRIGHT_FB2 || CHG_BRIGHT, bolts: true, early: true, offs: [24, 25, 26, 27], effects: [0], trigLo: 7.5, trigHi: 20, tol: tb => 1.5 + 0.08 * Math.abs(tb), trigMin: 0, trigMax: 4000 },
  // dup: the route step with chg 'dup' (Duplighosts, Charge-lock route). The lock starts the zero-wait tracker as on the
  // Hallway; its plan is Bombette's Do Nothing (profile dup3: 3+ copies, 4 as tie-break). altMs: retries only while the
  // runner would still be waiting on Do Nothing (the natural confirm is ~2-3 s after the rays).
  // fb1: Final Bowser phase 2 T1, T2, T4 (route steps with chg 'fb1'): the aura's draws between the rays' (kernel.c fb1score);
  // both effects in stage 1 (A's initial rays alone ranked the true seed below 65536 on the T1 render: Lakilester and the
  // stars cover part of them), B's base draw 24 .. 38 steps after A's (the aura's draws on frames 0-2); the lock starts the
  // T1-T4 tracker (fb14_live.js). A real bar hide arms it, as on the Hallway.
  fb1: { id: 'fb1', turn: null, cams: () => CHG_CAMS_FB2 || CHG_CAMS, mario: () => CHG_MARIO_FB2 || CHG_MARIO, bright: () => CHG_BRIGHT_FB1, bolts: false, aura: true, early: false, offs: Array.from({ length: 15 }, (_, i) => 24 + i), effects: [0, 1], trigLo: 6, trigHi: 20, trigN: true, trigCut: [10.9, 16.5], shiftAlts: [1, -1], tol: tb => 4 + 0.3 * Math.abs(tb), trigMin: 250, trigMax: 1000, baseMin: 30, shape: true, altMs: 12000 },
  dup: { id: 'dup', turn: null, cams: () => CHG_CAMS, mario: () => CHG_MARIO, bright: () => CHG_BRIGHT_DUP, bolts: false, early: false, offs: [24, 25], effects: [0, 1], trigLo: 5, trigHi: 25, trigN: true, tol: () => 1.5, trigMin: 250, trigMax: 1000, baseMin: 30, shape: true, altMs: 6000 },
  // jr: the Jr. Troopa steps (chg 'jr'). The lock goes to jrLock (jr_live.js): the T1 lock starts the tracker that carries it
  // through the fight; the T3 / T5 locks check the carry or start it again.
  jr: { id: 'jr', turn: null, cams: () => CHG_CAMS, mario: () => CHG_MARIO, bright: () => CHG_BRIGHT_JR, bolts: false, early: false, offs: [24, 25], effects: [0, 1], trigLo: 5, trigHi: 25, trigN: true, tol: () => 1.5, trigMin: 250, trigMax: 1000, baseMin: 30, shape: true } };
/* the burst's first picture (frame 3) comes 13 game frames after the bar hides for the Charge confirm: 433-478 ms on the
 * 7 route clips and the first live attempt. hw: the trigger only counts trigMin..trigMax ms after a hide that ended a
 * real bar-up (600+ ms, as hudWatch's barHide); a flicker of the coin box never arms it, and a hide with no burst in
 * that window says "Charge not seen" and waits for the next real hide (live log 1793736599276: armed on the hallway's
 * hide, triggered 2 s later on something else, re-armed on a flicker and captured the battle intro 10 s later while
 * the real Charge went by). */
const CHG_NCC_MIN = 0.5;     // Mario on frame 0 (route clips and live 0.94, FB2 0.85; a capture with no Charge 0.09)
const CHG_EARLY_N = 23;      // stage 1 and the joint stage need frames 0..21 (A's initial rays on 0..18, B's on 3..21)
const CHG_K = 16384, CHG_K_FB2 = 65536, CHG_M2 = 300, CHG_IMPS = Array.from({ length: 136 }, (_, i) => 40 + i);   // Spiny Flip thrown with A: impact +40..+175
const CHG_LAGS = [[0, 0.75], [1, 0.25]], CHG_QMAX = 10, CHG_QTOL = 0.02;   // console lag frames after the rays (weights); most q kept, within 2% of the best q
const CHG_SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];     // Spiny Flip confirm vs the bar's hiding (a dropped picture reads it late)
const CHG = { state: 'idle', ring: [], frames: [], res: null };
function chgEnabled() { const el = $('s-chg'); return !el || el.checked; }
/* any Hallway Bowser step arms the Hallway Charge (the runner is often on T2 after a retry; a burst seen there sets the
 * route back to T1, chgFrame) */
const chgHallStep = s => !!(s && s.t && /^Hallway Bowser/.test(s.t));
function chgProfNow() { const s = isRoute() && RT()[routeStep]; if (!s) return null; if (chgHallStep(s)) return CHG_PROF.hw; if (s.chg && CHG_PROF[s.chg]) return CHG_PROF[s.chg]; for (const k in CHG_PROF) if (CHG_PROF[k].turn && CHG_PROF[k].turn === s.turn) return CHG_PROF[k]; return null; }
function chgStepActive() { return !!chgProfNow(); }
/* Which arena the capture shows, read at a real bar hide (the menu just closed, battle camera): the band under the
 * battle floor (320-space y 165-190) is the dark bushes in the Hallway (luma 45-67 at all 43 bar hides of the 14
 * Hallway clips) and the lit stone floor in Final Bowser's arena (114-116 on the FB2 clip); the top of the picture
 * (y 40-100) is the blue windows in the Hallway (B - R +27..+64) and the dark sky in Final Bowser's (+4..+11). Mario's
 * reference patch does not tell them apart (at the hide he is not in the Charge pose: NCC 0.08 with either patch).
 * The Duplighost room (kpa_01): that band is the purple floor, B - R +5..+18 on the console clip of the Duplighost fight
 * (aad978a3, the Surge route: luma 47-73 with the battle camera) and +10..+20 at the emulator's Charge hide, where the
 * Hallway's bushes are -25..-50 and Final Bowser's floor is lit (luma > 95). Checked over every 6th frame of 4 Hallway
 * clips and the FB2 clip: this rule never fires there (0 of 1610 frames), and on 167 of 252 frames of the Duplighost
 * clip. It is tested first: the Duplighost room's top band can read like the Hallway's (B - R up to +21). */
const CHG_ARENA_LOW = [30, 165, 300, 190], CHG_ARENA_TOP = [30, 40, 300, 100];
function chgArenaBox(b) { const [SX, OX, SY, OY] = chgMap(); return { x: (OX + b[0] * SX) / 1280, y: (OY + b[1] * SY) / 720, w: (b[2] - b[0]) * SX / 1280, h: (b[3] - b[1]) * SY / 720 }; }
function chgArena() {
  const rgb = b => { const g = sample(chgArenaBox(b), 32, 8), n = g.length / 4; let r = 0, gr = 0, bl = 0; for (let i = 0; i < g.length; i += 4) { r += g[i]; gr += g[i + 1]; bl += g[i + 2]; } return [r / n, gr / n, bl / n]; };
  const lo = rgb(CHG_ARENA_LOW), tp = rgb(CHG_ARENA_TOP), L = 0.299 * lo[0] + 0.587 * lo[1] + 0.114 * lo[2], br = tp[2] - tp[0], lbr = lo[2] - lo[0];
  return { a: lbr > 2 && L > 30 && L < 95 && br < 30 ? 'dup' : L < 85 && br > 18 ? 'hw' : L > 95 && br < 18 && br > -15 ? 'fb' : chgArenaJr(L, br, lbr) ? 'jr' : null, L: +L.toFixed(1), br: +br.toFixed(1), lbr: +lbr.toFixed(1) };
}
/* Jr. Troopa's arena (Bowser's Castle) at a Charge hide: the grey stone floor (luma 59-68, B - R -1.5 .. -5.4) under grey
 * walls with the dark Bowser doors (top B - R +11 .. +15): the capture-simulated emulator renders and the one console
 * clip of the fight (8526dcdd, 2026-11-02 14:16:56: a T1 Super Charge). Tested after the other three. It moves no route
 * (the castle's corridors are grey stone too); the page logs it (chargeArenaJrSeen). */
const JR_ARENA = { L: [55, 75], br: [8, 17], lbr: [-7, -0.8] };
function chgArenaJr(L, br, lbr) { const A = JR_ARENA; return L > A.L[0] && L < A.L[1] && br > A.br[0] && br < A.br[1] && lbr > A.lbr[0] && lbr < A.lbr[1]; }
/* the profile for a Charge armed on this hide: the step's, unless the picture is the other arena (a black or faded picture
 * is neither). Final Bowser's arena is taken only at a real bar hide (the menu just closed): the Hallway's battle intro
 * flashes white (luma 120) and reads like its lit floor. The Hallway is taken at any arming, as the FB2 profile arms on
 * any hide (its dark bushes and blue windows do not occur in Final Bowser's arena). On the FB2 step
 * (or past it) a Hallway picture is a Hallway retry: the Hallway profile, and the burst sets the route to Hallway T1
 * (chgPendResolve). On a Hallway step a Final Bowser picture is that battle reached: the route goes to the FB2 step. */
/* The Duplighost step (Charge-lock route): a Hallway picture is a Hallway retry (the Hallway profile; its burst sets
 * Hallway T1), a Final Bowser picture at a real hide moves the route there. On a Hallway or Final Bowser step, the
 * Duplighost room at a real hide is that fight (a reset to an earlier save): the route goes to the Duplighost step, but
 * only on the Charge-lock route (on the RTA route the Duplighosts have no Charge to read). */
function chgArenaProf(P0, real) {
  const A = chgArena(), fb1I = RT().findIndex(x => x.chg === 'fb1'), fbI = fb1I >= 0 ? fb1I : RT().findIndex(x => x.turn === CHG_PROF.fb2.turn), dupI = RT().findIndex(x => x.chg === 'dup'), jrI = RT().findIndex(x => x.chg === 'jr');
  // Jr. Troopa (jr_live.js): on his steps a Hallway picture is the Hallway (its burst sets Hallway T1), Final Bowser's arena at
  // a real hide that fight. His arena does not move the route from another fight's step: the castle corridors on the walk
  // after the fight are grey stone too, and no console clip of the fight exists to rule that out (jrI: the log only).
  if (P0 !== CHG_PROF.jr && real && A.a === 'jr' && jrI >= 0) slog('chargeArenaJrSeen', { step: routeStep, L: A.L, br: A.br, lbr: A.lbr });
  if (P0 === CHG_PROF.jr && A.a === 'hw') { slog('chargeArena', { arena: 'hallway', step: routeStep, L: A.L, br: A.br, lbr: A.lbr }); return CHG_PROF.hw; }
  if (P0 === CHG_PROF.jr && real && A.a === 'fb' && fbI >= 0) { slog('chargeArena', { arena: 'final bowser', step: routeStep, L: A.L, br: A.br, lbr: A.lbr }); setStep(fbI); return fb1I >= 0 ? CHG_PROF.fb1 : CHG_PROF.fb2; }
  if ((P0 === CHG_PROF.fb2 || P0 === CHG_PROF.dup || P0 === CHG_PROF.fb1) && A.a === 'hw') { slog('chargeArena', { arena: 'hallway', step: routeStep, L: A.L, br: A.br, lbr: A.lbr }); return CHG_PROF.hw; }
  if ((P0 === CHG_PROF.hw || P0 === CHG_PROF.dup) && real && A.a === 'fb' && fbI >= 0) { slog('chargeArena', { arena: 'final bowser', step: routeStep, L: A.L, br: A.br, lbr: A.lbr }); chgPendDrop('arena'); setStep(fbI); return fb1I >= 0 ? CHG_PROF.fb1 : CHG_PROF.fb2; }
  if ((P0 === CHG_PROF.hw || P0 === CHG_PROF.fb2 || P0 === CHG_PROF.fb1) && real && A.a === 'dup' && dupI >= 0) { slog('chargeArena', { arena: 'duplighosts', step: routeStep, L: A.L, br: A.br, lbr: A.lbr }); chgPendDrop('arena'); setStep(dupI); return CHG_PROF.dup; }
  return P0;
}
const chgP = () => CHG.prof || CHG_PROF.hw;
/* The Hallway Charge confirm is anchored on the burst: the bar hide that would count as the hw_charge pre is held
 * (CHG.pend) until the capture shows a real Charge (shape and Mario); otherwise it is dropped and the pre stays open, so a
 * battle-entry hide (bar up while walking, then the fade from black) never shifts the route's confirms by one. A burst seen
 * on another Hallway step sets the route to T1 (chargeStepSet). The confirm time is the bar hide when it fits the burst
 * (the burst's frame 3 shows 13-15 game frames after the hide), else the trigger minus 14 frames. */
function chgPend(pr, tObs, key) {
  if (!chgEnabled() || !CHG_WASM || CHG_WASM.length < 100 || pr.id !== 'hw_charge' || chgProfNow() !== CHG_PROF.hw || !['idle', 'notseen', 'armed'].includes(CHG.state)) return false;
  CHG.pend = { pr, tObs, key }; return true;
}
function chgPendDrop(why) {
  const P = CHG.pend; if (!P) return; CHG.pend = null;
  if (V.preDone) delete V.preDone[P.key]; slog('chargePreDropped', { at: Math.round(P.tObs), why });
}
function chgPendResolve() {
  const hi = RT().findIndex(x => x.turn === 'hw_spiny'); if (hi < 0) return;
  const hidePre = RT()[hi].pre.findIndex(q => q.id === 'hw_charge'), hwPre = RT()[hi].pre[hidePre];
  const tBack = CHG.trig.t - 14 * FRAME - (3 - VAN.M()) * FRAME;      // HUD_HIDE.hw_charge 3, the confirm as hudWatch reads it
  let P = CHG.pend; CHG.pend = null;
  if (routeStep !== hi) { const from = routeStep; setStep(hi); slog('chargeStepSet', { from, to: hi }); P = null; }
  const tObs = P && Math.abs(P.tObs - tBack) < 4 * FRAME ? P.tObs : tBack;
  if (V.preDone && V.preDone[hi + ':' + hidePre] && !P && CHG.preUsed === CHG.trig.t) return;
  CHG.preUsed = CHG.trig.t; V.preDone = V.preDone || {}; V.preDone[hi + ':' + hidePre] = true;
  slog('chargeConfirm', { at: Math.round(tObs), from: P ? 'bar' : 'burst' }); preConfirm(hwPre, tObs);
}
function chgReset(why) { if (CHG.pend) chgPendDrop('reset'); if (CHG.workers) CHG.workers.forEach(w => w.terminate()); Object.assign(CHG, { state: 'idle', ring: [], frames: [], res: null, workers: null, means: [], trig: null, why: why || null, taps: [], pres: [], spiny: null, prof: null, early: null, info: null, armP: null, G: null, F0: null, skips: null, alt: 0, forced: 0, trigT0: null }); if (typeof fb2Reset === 'function') fb2Reset(); chgShow(); }
chgReset();
let chgCv = null, chgCtx = null;
function chgCanvas() { if (!chgCv) { chgCv = document.createElement('canvas'); chgCv.width = 640; chgCv.height = 480; chgCtx = chgCv.getContext('2d', { willReadFrequently: true }); } return chgCtx; }
/* the capture frame -> the 640x480 game raster (2 px per 320-space unit), luma */
function chgGrab() {
  const c = chgCanvas(), [vw, vh] = dims(), [SX, OX, SY, OY] = chgMap(), kx = 1280 / vw, ky = 720 / vh;
  c.setTransform(2 / SX * kx, 0, 0, 2 / SY * ky, 0.5 - 2 / SX * (0.5 + OX), 0.5 - 2 / SY * (0.5 + OY));
  c.fillStyle = '#000'; c.fillRect(-1e4, -1e4, 3e4, 3e4); c.drawImage(V.src || V.video, 0, 0, vw, vh); c.setTransform(1, 0, 0, 1, 0, 0);
  const d = c.getImageData(0, 0, 640, 480).data, Y = new Uint8Array(640 * 480);
  for (let i = 0, j = 0; j < Y.length; i += 4, j++) Y[j] = (77 * d[i] + 150 * d[i + 1] + 29 * d[i + 2] + 128) >> 8;
  return Y;
}
/* per video frame (onFrame): arm on Hallway T1 while the status bar is hidden (the Charge confirm hides it 10 game
 * frames before frame 0), trigger on the burst, keep ~110 capture frames */
function chgFrame(t, present) {
  if (V.frames % 15 === 0) chgShow();
  if (!chgEnabled() || !CHG_WASM || CHG_WASM.length < 100) return;
  if (CHG.trig && chgP().id === 'fb2' && typeof fb2Frame === 'function') fb2Frame(t, present);   // FB2: the popup and the coin from the trigger on
  if (CHG.state !== 'idle' && CHG.state !== 'notseen' && CHG.state !== 'armed' && CHG.state !== 'capture') { chgCoin(t, present); return; }
  if (!chgStepActive()) { if (CHG.state !== 'idle') chgReset(); return; }
  if (present && V.presentSince) CHG.menuSince = V.presentSince;            // the turn-1 menu's coin (for the q check)
  CHG.presN = present ? (CHG.presN || 0) + 1 : 0;
  if (present && CHG.state !== 'capture' && (CHG.state !== 'armed' || CHG.presN > 15)) { if (CHG.state === 'armed') { CHG.state = 'idle'; CHG.ring = []; CHG.means = []; } CHG.hideT = null; CHG.armP = null; return; }   // the burst can flicker the coin box: only a bar back for 1/4 s disarms
  if (CHG.hideT == null && !present) {
    const real = V.hudGone === t && V.hudWasUp > 600, P = chgArenaProf(chgProfNow(), real);
    // a capture the other arena's profile started (the FB2 profile arms on any hide) is not this Charge: drop it
    if (CHG.state === 'capture' && CHG.prof && CHG.prof !== P) { slog('chargeArenaDrop', { prof: CHG.prof.id }); CHG.state = 'idle'; CHG.frames = []; CHG.ring = []; CHG.means = []; CHG.trig = null; CHG.early = null; if (CHG.workers) { CHG.workers.forEach(w => w.terminate()); CHG.workers = null; } if (typeof fb2Reset === 'function') fb2Reset(); }
    if (P.trigMin && !real) { CHG.hideT = -1e12; CHG.armP = null; return; }   // not a confirm: the bar was not up
    CHG.hideT = t; CHG.armP = P; CHG.menu = CHG.menuSince ? { from: CHG.menuSince + 1000, to: t - 4 * FRAME, taps: (V.hist || []).filter(x => x > CHG.menuSince + 1000 && x < t) } : null;
  }
  if (CHG.state === 'idle' || CHG.state === 'notseen') { const P = CHG.armP || chgProfNow(); if (t - CHG.hideT > P.trigMax) return; if (typeof fb14ArmOk === 'function' && !fb14ArmOk(P, t)) return; CHG.state = 'armed'; CHG.ring = []; CHG.means = []; CHG.prof = P; }
  const g = sample(chgGame(), 32, 24); let m = 0; for (let i = 0; i < g.length; i += 4) m += 0.299 * g[i] + 0.587 * g[i + 1] + 0.114 * g[i + 2]; m /= 768;
  const tg = performance.now(), last = CHG.state === 'capture' ? CHG.frames[CHG.frames.length - 1] : CHG.ring[CHG.ring.length - 1];
  // FB2: a repeated picture (same coarse brightness) reuses the raster: half the grabs. v75: only right after a fresh grab
  // (each game frame shows on 2 captures): two game frames in a row with the same coarse brightness made the second a
  // copy of the first, a skipped frame in the placement, and the T6 Charge of an end-to-end run never locked
  const rep = chgP().id === 'fb2' && last && !last.rep && Math.abs(last.m - m) < 0.02;
  const fr = { t, m, Y: rep ? last.Y : chgGrab(), rep }; if (!rep) CHG.grabMs = (CHG.grabMs || 0) * 0.9 + 0.1 * (performance.now() - tg);
  if (CHG.state === 'armed') {
    CHG.ring.push(fr); if (CHG.ring.length > 16) CHG.ring.shift(); CHG.means.push(m); if (CHG.means.length > 12) CHG.means.shift();
    const P0 = CHG.prof || CHG_PROF.hw;
    if (t - CHG.hideT > P0.trigMax) { CHG.state = P0.trigMin ? 'notseen' : 'idle'; CHG.ring = []; CHG.frames = []; if (P0.trigMin) { CHG.why = 'Charge not seen: no burst ' + P0.trigMin + '-' + P0.trigMax + ' ms after the bar hid'; slog('chargeNotSeen', { hideAt: Math.round(CHG.hideT), why: 'no burst' }); chgPendDrop('no burst'); chgShow(); } return; }
    if (CHG.means.length >= 8 && t - CHG.hideT >= P0.trigMin) {
      const base = CHG.means.slice(0, -1).sort((a, b) => a - b)[CHG.means.length >> 1];
      const P = CHG.prof || CHG_PROF.hw;
      if (m > base + P.trigLo && m < base + P.trigHi && !(P.baseMin && base < P.baseMin)) {   // baseMin: a fade from black (battle entry) is no Charge
        // which burst frame the trigger picture is (hw): frame 3 reads +7.0..7.8 on every clip and live trigger; when the
        // browser dropped frame 3's pictures the first one above the menu is frame 4 (+12.5) or 5 (+19.4), and v69 took it
        // as frame 3 (or, at +19.4, did not trigger at all): every frame after it one or two off, no lock
        const d0 = m - base, cut = P.trigCut || [9.85, 15.95], n0 = P.trigN ? (d0 < cut[0] ? 3 : d0 < cut[1] ? 4 : 5) : 3;
        CHG.state = 'capture'; CHG.trig = { t: t - (n0 - 3) * FRAME, tRaw: t, n: n0, base, i: CHG.ring.length - 1 }; CHG.shapeBad = 0; if (P.id === 'fb2' && typeof fb2Reset === 'function') fb2Reset(); CHG.frames = CHG.ring.slice(); CHG.ring = []; slog('chargeTrigger', { base: +base.toFixed(1), m: +m.toFixed(1) }); if (P.id === 'fb1' && typeof fb14Trigger === 'function') fb14Trigger(); }
    }
    return;
  }
  // capture: until game frame ~50; the burst must keep rising (a real Charge: +30 within ~0.4 s)
  CHG.frames.push(fr);
  const dt = t - CHG.trig.t;   // from frame 3 (CHG.trig.t is frame 3's time even when the trigger picture was a later frame)
  // hw: every picture of the burst (game frames 5..27 by time) must sit on CHG_BRIGHT, within +-1.5 frames and 10 levels
  if (chgP().shape) { const n = 3 + (t - CHG.trig.t) / FRAME, BRS = chgP().bright();
    if (n >= 5 && n <= 27) { let lo = 1e9, hi = -1e9; for (let k = Math.max(3, Math.floor(n - 1.5)); k <= Math.min(45, Math.ceil(n + 1.5)); k++) { lo = Math.min(lo, BRS[k - 3]); hi = Math.max(hi, BRS[k - 3]); }
      const d = m - CHG.trig.base; if (d < lo - 10 || d > hi + 10) CHG.shapeBad++; } }
  if ((dt > 330 && dt < 400 && m < CHG.trig.base + 15) || CHG.shapeBad > 3) { slog('chargeFalseTrigger', { m: +m.toFixed(1), shapeBad: CHG.shapeBad || 0 }); CHG.state = 'armed'; CHG.ring = CHG.frames.slice(-16); CHG.frames = []; return; }
  if (chgP().early && !CHG.early && dt > (CHG_EARLY_N - 3 + 1.5) * FRAME) { if (typeof FB14 !== 'undefined' && FB14.t6 && chgP().id === 'fb2') CHG.early = { narrow: true }; else { CHG.early = { t }; setTimeout(chgEarly, 0); } }   // stage 1 while the rays go on
  if (dt > CHG_N * FRAME) { CHG.state = 'maps'; CHG.tEnd = t; CHG.taps = []; CHG.pres = []; setTimeout(chgSolve, 0); }
}
/* the coin while the seed is searched: kept, so the tracker gets the Lakilester menu's shines once it is locked */
function chgCoin(t, present) { if (CHG.state === 'search' || CHG.state === 'maps') { CHG.pres.push([t, present]); if (CHG.pres.length > 4000) CHG.pres.shift(); } }
function chgTap(t) { if (CHG.state === 'search' || CHG.state === 'maps') CHG.taps.push(t); }
/* distinct game frames: frame 0 is 3 game frames before the first one 5 brighter than the menu (7 route clips);
 * out[CHG_N + 2], out[CHG_N + 3] = frames -2 and -1 (Mario's position) */
function chgGameFrames(ban) {     // ban: Set of j * 64 + n, assignments an earlier placement used for a skipped frame
  const F = CHG.frames, out = new Array(CHG_N + 4).fill(null), ti = CHG.trig.i, tT = F[ti].t, NN = CHG_N + 2;
  const diff = (a, b) => { let s = 0; for (let y = 40; y < 440; y += 8) for (let x = 24; x < 616; x += 8) s += Math.abs(a[y * 640 + x] - b[y * 640 + x]); return s / (50 * 74); };
  const fm = chgP().freshMin || 0.8, fresh = F.map((f, i) => i === 0 || diff(f.Y, F[i - 1].Y) > fm);
  // from the trigger on, each new picture is a game frame; which one is set by the burst's brightness, which is the
  // same every Charge (CHG_BRIGHT, 7 route clips, sd < 0.7), and by the time between pictures (the browser's frame
  // times jitter by +-17 ms and it drops pictures), by dynamic programming over n
  const J = []; for (let i = ti; i < F.length; i++) if (i === ti || fresh[i]) J.push(i);
  if (window.__chgDebug) CHG.J0 = F.map((f, i) => [Math.round(f.t - F[ti].t), +f.m.toFixed(1), i >= 1 ? +diff(f.Y, F[i - 1].Y).toFixed(2) : null]);
  const base = CHG.trig.base, INF = 1e18, cost = [], from = [], BR = chgP().bright(), TOL = chgP().tol;
  for (let j = 0; j < J.length; j++) { cost.push(new Float64Array(NN + 3).fill(INF)); from.push(new Int16Array(NN + 3)); }
  if (chgP().trigN) { const d = F[ti].m - base; for (let n = 3; n <= 5; n++) cost[0][n] = Math.min(25, ((d - BR[n - 3]) / TOL(BR[n - 3])) ** 2) + 3 * (n - 3); }
  else cost[0][3] = 0;
  for (let j = 1; j < J.length; j++) {
    const d = F[J[j]].m - base, dt = F[J[j]].t - F[J[j - 1]].t;
    for (let n = 3; n < NN + 3; n++) {
      if (ban && ban.has(j * 64 + n)) continue;
      const tb = BR[n - 3], cb = (tb == null ? 0 : Math.min(25, ((d - tb) / TOL(tb)) ** 2));
      for (let st2 = 0; st2 <= 3; st2++) { const p = n - st2; if (p < 3 || cost[j - 1][p] >= INF) continue;
        const c = cost[j - 1][p] + cb + Math.min(9, ((dt - FRAME * st2) / 12) ** 2) + [3, 0, 2, 4][st2];
        if (c < cost[j][n]) { cost[j][n] = c; from[j][n] = p; } }
    }
  }
  const path = new Array(J.length);
  if (J.length) { let n = 3; for (let k = 4; k < NN + 3; k++) if (cost[J.length - 1][k] < cost[J.length - 1][n]) n = k;
    for (let j = J.length - 1; j >= 0; j--) { path[j] = n; if (n < NN && (out[n] == null || j === 0 || from[j][n] !== n)) out[n] = J[j]; if (j) n = from[j][n]; } }
  // where this placement says a game frame had no picture of its own (or a picture was shown twice) inside the rays: the
  // assignments a retry bans so that the next-best placement puts it elsewhere (chgRetry)
  CHG.skips = []; for (let j = 1; j < J.length; j++) if (path[j] !== path[j - 1] + 1 && path[j] <= 36) CHG.skips.push(j * 64 + path[j]);
  // the trigger picture's frame as placed: frame 3's time (the clock's anchor) follows from it
  const n0 = J.length ? path[0] : 3; CHG.trig.n = n0; CHG.trig.t = (CHG.trig.tRaw != null ? CHG.trig.tRaw : tT) - (n0 - 3) * FRAME;
  // before it the picture barely changes: by time
  for (let n = -2; n <= 2; n++) { const want = tT + (n - n0) * FRAME; let bi = null;
    for (let i = 0; i < ti; i++) if (bi == null || Math.abs(F[i].t - want) < Math.abs(F[bi].t - want)) bi = i;
    if (bi != null && Math.abs(F[bi].t - want) < 0.75 * FRAME) out[n < 0 ? NN + 2 + n : n] = bi; }
  return out.map(i => (i == null ? null : F[i]));
}
/* Mario's horizontal offset from the reference capture (clips 15-14-09 and 15-19-21 had him 16.5 raster px / 6 world
 * units to the right): normalised cross-correlation of the high-passed patch around him on frame 0 */
function chgBlur(Y, W, H, sig) {
  const r = Math.ceil(3 * sig), k = []; let s = 0; for (let i = -r; i <= r; i++) { const v = Math.exp(-i * i / (2 * sig * sig)); k.push(v); s += v; } for (let i = 0; i < k.length; i++) k[i] /= s;
  const T = new Float32Array(W * H), O = new Float32Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { let a = 0; for (let i = -r; i <= r; i++) a += k[i + r] * Y[y * W + Math.min(W - 1, Math.max(0, x + i))]; T[y * W + x] = a; }
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { let a = 0; for (let i = -r; i <= r; i++) a += k[i + r] * T[Math.min(H - 1, Math.max(0, y + i)) * W + x]; O[y * W + x] = a; }
  return O;
}
function chgMarioShift(Ys) {     // Ys: luma rasters of frames around 0; the best match of them counts
  const M = chgP().mario(), L = (Ys || []).filter(Boolean); if (!M || !L.length) return { dx: 0, ncc: 0 };
  return L.map(Y => chgMarioShift1(M, Y)).reduce((a, b) => (b.ncc > a.ncc ? b : a));
}
function chgMarioShift1(M, Y0) {
  const ref = M.ref || (M.ref = Uint8Array.from(atob(M.b64), c => c.charCodeAt(0))), W = M.w, H = M.h;
  const hp = (src, x0, y0) => { const P = new Float32Array(W * H); for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) P[y * W + x] = src(x0 + x, y0 + y); const B = chgBlur(P, W, H, 4); for (let i = 0; i < P.length; i++) P[i] -= B[i]; return P; };
  const R0 = hp((x, y) => ref[(y - M.y0) * W + (x - M.x0)], M.x0, M.y0);
  // the template: raster rows 248..343, cols 196..267 (inside the stored patch)
  const tw = 72, th = 96, tx = 196, ty = 248; const T = new Float32Array(tw * th); let m = 0;
  for (let y = 0; y < th; y++) for (let x = 0; x < tw; x++) { T[y * tw + x] = R0[(ty - M.y0 + y) * W + (tx - M.x0 + x)]; m += T[y * tw + x]; }
  m /= T.length; let sd = 0; for (let i = 0; i < T.length; i++) { T[i] -= m; sd += T[i] * T[i]; } sd = Math.sqrt(sd / T.length);
  const L = hp((x, y) => Y0[Math.min(479, Math.max(0, y)) * 640 + Math.min(639, Math.max(0, x))], 140, 236);   // live: x 140..299, y 236..355
  const LW = W; let best = { c: -2, dx: 0, dy: 0 }; const cs = new Map();
  for (let dy = -4; dy <= 4; dy++) for (let dx = -36; dx <= 36; dx++) {
    const ox = tx + dx - 140, oy = ty + dy - 236; if (ox < 0 || ox + tw > LW || oy < 0 || oy + th > H) continue;
    let a = 0, b = 0, c = 0;
    for (let y = 0; y < th; y++) for (let x = 0; x < tw; x++) { const v = L[(oy + y) * LW + ox + x]; a += v; b += v * v; c += v * T[y * tw + x]; }
    const n = tw * th, mu = a / n, s = Math.sqrt(Math.max(1e-9, b / n - mu * mu)), r = (c / n) / (s * sd);
    cs.set(dx + ',' + dy, r); if (r > best.c) best = { c: r, dx, dy };
  }
  const l = cs.get((best.dx - 1) + ',' + best.dy), h = cs.get((best.dx + 1) + ',' + best.dy);
  let sub = best.dx; if (l != null && h != null && l + h - 2 * best.c < 0) sub += 0.5 * (l - h) / (l + h - 2 * best.c);
  return { dx: sub, dy: best.dy, ncc: best.c };
}
/* ridge maps: for each game frame, each integer angle and each 4-unit step from the centre, the luma on the projected
 * ray minus beside it (+-2 px in 320 space); each angle's median over distance is subtracted (the radial burst);
 * prefix sums along distance. Same as readouts/charge_obs.py polar_ridge + the median step. */
function chgMaps(G, cen, nf, prev) {     // prev (FB2): the early maps; a frame on the same picture is copied from them
  const N = nf || CHG_N, ND = CHG_ND, CAMS = chgP().cams(), S = new Float32Array(N * 360 * (ND + 1)), C = new Float32Array(N * 360 * (ND + 1));
  const cs = new Float32Array(360), sn = new Float32Array(360); for (let a = 0; a < 360; a++) { cs[a] = Math.cos(a * Math.PI / 180); sn[a] = Math.sin(a * Math.PI / 180); }
  const Rv = new Float32Array(ND), ok = new Uint8Array(ND), tmp = new Float32Array(ND);
  for (let n = 0; n < N; n++) {
    const f = G[n]; if (!f) continue;
    if (prev && prev.G[n] === f && n < prev.N) { const L = 360 * (ND + 1); S.set(prev.S.subarray(n * L, (n + 1) * L), n * L); C.set(prev.C.subarray(n * L, (n + 1) * L), n * L); continue; }
    const Y = f.Y, cam = CAMS.cams[Math.min(n, CAMS.cams.length - 1)], M = cam, Wv = cam[16], Hv = cam[17], X0 = cam[18], Y0 = cam[19];
    const pj = (x, y, z) => { const v0 = x * M[0] + y * M[4] + z * M[8] + M[12], v1 = x * M[1] + y * M[5] + z * M[9] + M[13], v3 = x * M[3] + y * M[7] + z * M[11] + M[15]; return [X0 + Wv / 2 * (1 + v0 / v3), Y0 + Hv / 2 * (1 - v1 / v3), v3]; };
    const c0 = pj(cen[0], cen[1], cen[2]);
    const smp = (x, y) => { const u = 2 * x, v = 2 * y; if (!(u >= 0 && v >= 0 && u <= 639 && v <= 479)) return NaN; const iu = Math.min(638, u | 0), iv = Math.min(478, v | 0), fu = u - iu, fv = v - iv, k = iv * 640 + iu;
      return (Y[k] * (1 - fu) + Y[k + 1] * fu) * (1 - fv) + (Y[k + 640] * (1 - fu) + Y[k + 641] * fu) * fv; };
    for (let a = 0; a < 360; a++) {
      let nv = 0;
      for (let d = 0; d < ND; d++) {
        const D = (d + 0.5) * 4, p = pj(cen[0] + D * cs[a], cen[1] + D * sn[a], cen[2]); ok[d] = 0;
        if (!(p[0] > X0 + 2 && p[0] < X0 + Wv - 2 && p[1] > Y0 + 2 && p[1] < Y0 + Hv - 2 && p[2] > 0)) continue;
        const dx = p[0] - c0[0], dy = p[1] - c0[1], nn = Math.hypot(dx, dy) + 1e-9, tx = -dy / nn * 2, ty = dx / nn * 2;
        const on = smp(p[0], p[1]), l = smp(p[0] + tx, p[1] + ty), r = smp(p[0] - tx, p[1] - ty);
        if (on !== on || l !== l || r !== r) continue;
        Rv[d] = on - 0.5 * (l + r); ok[d] = 1; tmp[nv++] = Rv[d];
      }
      let med = 0; if (nv) { const s = tmp.subarray(0, nv).sort(); med = nv & 1 ? s[nv >> 1] : 0.5 * (s[nv / 2 - 1] + s[nv / 2]); }
      const o = (n * 360 + a) * (ND + 1); let sa = 0, ca = 0;
      for (let d = 0; d < ND; d++) { if (ok[d]) { sa += Rv[d] - med; ca++; } S[o + d + 1] = sa; C[o + d + 1] = ca; }
    }
  }
  return { S, C };
}
const CHG_INVN = 0x6A76AE6D | 0;   // inverse of the LCG multiplier 0x5D588B65 mod 2^32
function chgBack(s, n) { let x = s >>> 0; for (let i = 0; i < n; i++) x = Math.imul((x - 1) >>> 0, CHG_INVN) >>> 0; return x; }
function chgFwd(s, n) { let x = s >>> 0; for (let i = 0; i < n; i++) x = (Math.imul(x, 0x5D588B65) + 1) >>> 0; return x; }
const CHG_WORKER = `
let X = null, mem = null;
const fwd = (s, n) => { for (let i = 0; i < n; i++) s = (Math.imul(s, 0x5D588B65) + 1) >>> 0; return s; };
onmessage = async e => {
  const m = e.data;
  try {
    if (m.type === 'init') {
      const inst = await WebAssembly.instantiate(m.mod, {}); X = inst.exports;
      new Float32Array(X.memory.buffer, X.ptrS(), m.S.length).set(m.S); new Float32Array(X.memory.buffer, X.ptrC(), m.C.length).set(m.C);
      X.prepare(m.N, m.ND); X.setK(m.K);
      if (m.pat) { new Uint8Array(X.memory.buffer, X.patPtr(), m.pat.length).set(m.pat); X.setPatterns(m.pat.length / 52); }
      const ub = []; for (let e2 = 0; e2 < 2; e2++) { const u = []; for (let b = 0; b < 361; b++) u.push(X.ub(e2, b)); ub.push(u); }
      postMessage({ type: 'ready', ub });
    } else if (m.type === 'tasks') {         // this worker's bases, in decreasing bound order, with no round trips
      let n = 0, skipped = 0;
      for (const [e2, b] of m.list) { if (X.ub(e2, b) <= X.thr(e2)) { skipped++; continue; } X.stage1g(e2, b, (b * 11897416) >>> 0, 11897416, -1e30); n++; }
      postMessage({ type: 'done', thr: [X.thr(0), X.thr(1)], n, skipped });
    } else if (m.type === 'maps') {
      new Float32Array(X.memory.buffer, X.ptrS(), m.S.length).set(m.S); new Float32Array(X.memory.buffer, X.ptrC(), m.C.length).set(m.C); X.setN(m.N);
      postMessage({ type: 'mapsok' });
    } else if (m.type === 'heaps') {
      const out = [];
      for (let e2 = 0; e2 < 2; e2++) { const n = X.heapN(e2); out.push({ s: Array.from(new Float32Array(X.memory.buffer, X.heapS(e2), n)), d: Array.from(new Uint32Array(X.memory.buffer, X.heapD(e2), n)) }); }
      postMessage({ type: 'heaps', out });
    } else if (m.type === 'joint') {      // A's candidates get B's best initial rays over the offsets, B's get A's
      const sc = new Float32Array(m.e.length), vb = new Int16Array(m.e.length);
      for (let i = 0; i < m.e.length; i++) { const s0 = m.s0[i];
        if (m.e[i] === 0) { let b = -1e30, bo = 0; for (const o of m.offs) { const x = X.s1score(1, fwd(s0, o + 1)); if (x > b) { b = x; bo = o; } } sc[i] = m.sc[i] + b; vb[i] = bo; } else sc[i] = m.sc[i] + X.s1score(0, fwd(s0, 1)); }
      postMessage({ type: 'joint', sc, vb });
    } else if (m.type === 'q') {
      const out = m.seeds.map(s => Array.from(new Float32Array(X.memory.buffer, X.qscores(s >>> 0), 48)));
      postMessage({ type: 'q', out });
    } else if (m.type === 'ub2') {
      postMessage({ type: 'ub2', out: m.seeds.map(s => ({ ub: X.fb2ub(fwd(s >>> 0, 1)) })) });
    } else if (m.type === 'q2') {
      let best = m.thr * 1.8; const out = m.seeds.map(s => { const sc = X.fb2cand(fwd(s >>> 0, 1), best / 1.8); if (sc > best) best = sc; return { sc, p: X.fb2bp(0), q: X.fb2bp(1) }; });
      postMessage({ type: 'q2', out });
    } else if (m.type === 'fb1') {        // FB2 T1-T4 (the aura): the relaxed path score of each candidate (kernel.c fb1score)
      postMessage({ type: 'fb1', out: m.seeds.map((s, i) => ({ sc: m.v ? X.fb1scorev(fwd(s >>> 0, 1), m.v[i] - 1, m.v[i] + 1) : X.fb1score(fwd(s >>> 0, 1)) })) });
    } else if (m.type === 'fb1h') {       // the structured fit of the best (fb1struct): every (pattern, q, second coin) within tol
      const a = fwd(m.s0 >>> 0, 1), P = X.fb1path(a), v = new Int32Array(X.memory.buffer, P, 52)[0], best = X.fb1struct(a, v), n = X.fb2npat();
      const S3 = new Float32Array(X.memory.buffer, X.sc3Ptr(), n * 96), out = [];
      for (let i = 0; i < n * 96; i++) if (S3[i] > -1e29 && S3[i] >= best * (1 - m.tol)) out.push(i);
      out.sort((x, y) => S3[y] - S3[x]);      // the best first (the list is cut at m.max)
      const hy = out.slice(0, m.max || 4000).map(i => { const p = (i / 96) | 0, q = ((i % 96) / 2) | 0, br = i % 2, sc = X.fb1aura(p, q, br), A = Array.from(new Uint8Array(X.memory.buffer, X.xaPtr(), 20));
        const XB = new Uint8Array(X.memory.buffer, X.xbPtr(), 60), XA = new Uint8Array(X.memory.buffer, X.xaPtr(), 60), PT = new Uint8Array(X.memory.buffer, X.patPtr() + p * 52, 52);
        for (let n2 = 0; n2 < 60; n2++) { XB[n2] = n2 < 48 ? PT[n2] : 0; XA[n2] = A[n2 % 20]; }
        X.fb1end(a, q, 48); const E = new Uint32Array(X.memory.buffer, X.endPtr(), 3), esc = new Float32Array(E.buffer, E.byteOffset + 8, 1)[0];
        const na = X.fb1alts(p, q, br, Math.max(1, best * m.tol - (best - sc)), 600), AL = new Uint8Array(X.memory.buffer, X.altPtr(), na * 20), AS = new Float32Array(X.memory.buffer, X.altScPtr(), na), alts = [], altSc = [];
        for (let i = 0; i < na; i++) { alts.push(Array.from(AL.subarray(i * 20, i * 20 + 20))); altSc.push(AS[i]); }
        return { p, q, br, sc, aura: A, alts, altSc, s48: E[0] >>> 0, nc48: E[1], esc }; });
      postMessage({ type: 'fb1h', a, v, best, n: out.length, hy });
    } else if (m.type === 'cscore') {     // fb14_live.js fb14Joint: each aura pattern's best score over the given fits
      const XA = new Uint8Array(X.memory.buffer, X.xaPtr(), 60), n = m.cands.length / 20, out = new Float32Array(n);
      for (let i = 0; i < n; i++) { for (let j = 0; j < 20; j++) XA[j] = m.cands[i * 20 + j]; let b = -1e30; for (const [p, q, br] of m.hyps) { const x = X.fb1cscore(m.a >>> 0, p, q, br); if (x > b) b = x; } out[i] = b; }
      postMessage({ type: 'cscore', out });
    } else if (m.type === 'hyps') {
      const a = fwd(m.s0 >>> 0, 1), best = X.fb2best(a), n = X.fb2npat(), S2 = new Float32Array(X.memory.buffer, X.sc2Ptr(), n * 48), out = [];
      for (let i = 0; i < n * 48; i++) if (S2[i] >= best * (1 - m.tol)) out.push([(i / 48) | 0, i % 48, S2[i]]);
      for (const o of out) { X.fb2end(a, o[0], o[1], 48); const E = new Uint32Array(X.memory.buffer, X.endPtr(), 3); o.push(E[0], E[1]); }
      postMessage({ type: 'hyps', a, best, pairs: out });
    }
  } catch (err) { postMessage({ type: 'error', msg: String(err) }); }
};`;
function chgWorkerCount() { const n = num('chgcpu'); return Math.max(1, Math.min(16, n > 0 ? n : Math.max(1, (navigator.hardwareConcurrency || 4) - 1))); }
function chgCentre(G) {
  const sh = chgMarioShift([G[CHG_N + 2], G[CHG_N + 3], G[0], G[1]].map(f => f && f.Y)), dxw = Math.abs(sh.dx) >= 3 && sh.ncc > 0.6 ? sh.dx * 0.37 : 0;
  const c = chgP().cams().centre; return { sh, dxw, cen: [c[0] + dxw, c[1], c[2]] };
}
/* FB2: stage 1 from frames 0..22 while the rays go on (chgSearch waits for the full maps before the joint stage) */
function chgEarly() {
  try {
    if (CHG.state !== 'capture' || !CHG.early) return;
    const t0 = performance.now(), G = chgGameFrames(), c = chgCentre(G), maps = chgMaps(G, c.cen, CHG_EARLY_N);
    let give; const full = new Promise(r => { give = r; });
    Object.assign(CHG.early, { c, give, mapsMs: Math.round(performance.now() - t0), t1: performance.now(), prev: { G, S: maps.S, C: maps.C, N: CHG_EARLY_N } });
    CHG.searchP = chgSearch(maps, { N: CHG_EARLY_N, full }); CHG.searchP.catch(() => {});
    slog('chargeEarly', { mapsMs: CHG.early.mapsMs, frames: G.slice(0, CHG_EARLY_N).filter(Boolean).length });
  } catch (e) { slog('chargeError', { msg: 'early: ' + String(e && e.message || e) }); CHG.early = { failed: true }; }
}
async function chgSolve() {
  try {
    const t0 = performance.now(), G = chgGameFrames(window.__chgBan0 ? new Set(window.__chgBan0) : null);   // __chgBan0: tests only
    const E = CHG.early && CHG.early.give ? CHG.early : null, c = E ? E.c : chgCentre(G), sh = c.sh, dxw = c.dxw, cen = c.cen;
    if (!E && chgP().trigMin && !(sh.ncc >= CHG_NCC_MIN)) {     // no Mario where the Charge has him: not the Charge, do not search it
      CHG.frames = []; CHG.state = 'notseen'; CHG.why = 'Charge not seen: Mario not found on the captured frames (NCC ' + (+sh.ncc).toFixed(2) + ')';
      slog('chargeNotSeen', { why: 'no Mario', mario: +(+sh.dx).toFixed(1), marioNcc: +(+sh.ncc).toFixed(2) }); chgPendDrop('no Mario'); chgShow(); return;
    }
    if (chgP().id === 'hw') { st.hwBurstT = CHG.trig.t; chgPendResolve(); }      // the Charge is real: its confirm counts now (and the route is on Hallway T1)
    const maps = chgMaps(G, cen, CHG_N, E && E.prev), t1 = performance.now();
if (window.__chgDebug) {
    CHG.dbg = G.map(f => { if (!f) return null; const a = []; for (let y = 4; y < 480; y += 8) for (let x = 4; x < 640; x += 8) a.push(f.Y[y * 640 + x]); return [Math.round(f.t - CHG.trig.t), a]; });
    CHG.dbgRaw = CHG.frames.map(f => { const a = []; for (let y = 4; y < 480; y += 8) for (let x = 4; x < 640; x += 8) a.push(f.Y[y * 640 + x]); return [Math.round(f.t - CHG.trig.t), a]; });
    }
    if (window.__chgDebug) CHG.G0 = G.map(f => (f ? Math.round(f.t - CHG.trig.t) : null));
    const raw = CHG.frames; CHG.info = { raw: raw.length, spanMs: Math.round(raw[raw.length - 1].t - raw[0].t), grabMs: +(CHG.grabMs || 0).toFixed(1), gaps: raw.slice(1).map((f, i) => Math.round(f.t - raw[i].t)).join(','), frames: G.slice(0, CHG_N).filter(Boolean).length, mario: +sh.dx.toFixed(1), marioNcc: +sh.ncc.toFixed(2), dxWorld: +dxw.toFixed(2), mapsMs: Math.round(t1 - t0) };
    if (E) { CHG.info.early = { mapsMs: E.mapsMs, startedBeforeRaysEndMs: Math.round(CHG.tEnd - E.t1) }; CHG.info.prof = chgP().id; }
    CHG.F0 = CHG.frames; CHG.cen = cen; CHG.alt = 0; CHG.forced = 0; CHG.ban = new Set();
    CHG.frames = []; CHG.G = G; CHG.state = 'search'; CHG.tSearch = E ? E.t1 : t1; chgShow();
    slog('chargeMaps', CHG.info);
    let res;
    const cands = !E && chgP().id === 'fb2' && typeof fb14T6Cands === 'function' ? fb14T6Cands() : null;
    if (cands) {        // T6 with the seed carried from T1-T4: only the carried stream's stretch (fb14_live.js); the full search if it does not lock
      // the runner-up off the best one's stream: the candidates here are runs of consecutive seeds, and one a few steps away
      // shares B's rays and every respawn (the true T6 seed of the end-to-end run, 4753, against its neighbour's ~4700)
      const near = a => { const S = new Set(); let x = a >>> 0, y = a >>> 0; for (let k = 0; k <= 48; k++) { S.add(x); S.add(y); x = chgFwd(x, 1); y = chgBack(y, 1); } return S; };
      const okOf = r => { const T = r.top; if (!T[0] || T[0].sc < CHG_MIN) return false; const N0 = near(T[0].seed); const b = T.slice(1).find(x => x.sc > -1e29 && !N0.has(x.seed >>> 0));
        return T[0].sc / (b ? b.sc : T[0].sc / (CHG_RATIO * 1.0001)) >= CHG_RATIO; };
      res = await chgSearch(maps, { cands }); let ok = okOf(res), sh = 0;
      // (a second's work each: the pictures one frame earlier / later, before the full search)
      for (const d of [1, -1]) { if (ok || typeof fbShiftG !== 'function') break; const r2 = await chgSearch(chgMaps(fbShiftG(G, d), cen, CHG_N), { cands }); slog('chargeNarrowShift', { d, best: r2.top[0] && Math.round(r2.top[0].sc), seed: r2.top[0] && (r2.top[0].seed >>> 0).toString(16) }); if (okOf(r2)) { res = r2; ok = true; sh = d; CHG.trig.t += d * FRAME; } }
      CHG.info.narrow = { cands: cands.length, ms: Math.round(performance.now() - CHG.tSearch), locked: !!ok, shift: sh };
      if (ok) { const N0 = near(res.top[0].seed); res.top = [res.top[0]].concat(res.top.slice(1).filter(x => !N0.has(x.seed >>> 0))); }
      slog('chargeNarrow', CHG.info.narrow);
      if (!ok) { CHG.tSearch = performance.now(); res = await chgSearch(maps); }
    } else if (E) { E.give(maps); res = await CHG.searchP; } else res = await chgSearch(maps);
    CHG.res = res; CHG.tLock = performance.now(); CHG.info.searchMs = Math.round(CHG.tLock - CHG.tSearch); CHG.info.lockAfterRaysMs = Math.round(CHG.tLock - CHG.tEnd);
    if (res.fb2) CHG.info.stage = res.fb2.times;
    chgDecide();
  } catch (e) { slog('chargeError', { msg: String(e && e.message || e) }); CHG.state = 'failed'; CHG.why = 'error: ' + (e && e.message || e); chgShow(); }
}
/* opts (FB2): N = frames in these maps (early stage 1), full = a promise of the full maps, awaited before the joint stage */
function chgSearch(maps, opts) {
  opts = opts || {};
  return new Promise((resolve, reject) => {
    const mod = chgSearch.mod || (chgSearch.mod = new WebAssembly.Module(Uint8Array.from(atob(CHG_WASM), c => c.charCodeAt(0))));
    const url = chgSearch.url || (chgSearch.url = URL.createObjectURL(new Blob([CHG_WORKER], { type: 'text/javascript' })));
    const P = chgP(), nw = chgWorkerCount(), W = [], tS = performance.now(), times = {};
    CHG.workers = W; let ready = 0, ub = null, queue = [], busy = 0; const gthr = [-1e30, -1e30];
    const stats = { tasks: 0, skipped: 0 };
    const fail = msg => { W.forEach(w => w.terminate()); CHG.workers = null; reject(new Error(msg)); };
    // stage 1: the bases dealt round-robin in decreasing bound order, each worker runs its own list (a worker's heap is
    // the exact top K of its bases, so the union's top K is the exact top K of all 2^32)
    const deal = () => { const lists = W.map(() => []); queue.forEach((q, i) => lists[i % W.length].push([q.e, q.b])); busy = W.length; W.forEach((w, k) => w.postMessage({ type: 'tasks', list: lists[k] })); };
    let finishing = false;
    // a narrowed search (FB2 T6 after a carried seed, fb14_live.js): no stage 1; the candidates (seeds before A's base-angle
    // draw) go straight to stage 2
    // they are ranked by their initial rays first (A's, and B's at each offset), as the full search ranks its stage-1 bests:
    // the upper bound alone (any lightning, any insertion count) ranks hundreds of wrong ones above the true one
    const finishN = async () => { finishing = true; times.stage1 = 0; const tj = performance.now();
      try {
        const cs = opts.cands, per = Math.ceil(cs.length / W.length), sc = new Float32Array(cs.length), parts = [];
        for (let k = 0; k < W.length; k++) { const idx = [], s0 = []; for (let i = k * per; i < Math.min(cs.length, (k + 1) * per); i++) { idx.push(i); s0.push(cs[i]); } if (!idx.length) continue;
          // e 0: B's best initial rays over the offsets; e 1: A's (the worker adds the given score: 0 here), summed
          const e = new Uint8Array(2 * idx.length); e.fill(1, idx.length); const S0 = Uint32Array.from(s0.concat(s0));
          parts.push(call(W[k], { type: 'joint', e, s0: S0, sc: new Float32Array(2 * idx.length), offs: P.offs }, 'joint').then(r => r.sc.forEach((v, i) => { sc[idx[i % idx.length]] += v; }))); }
        await Promise.all(parts);
        const order = cs.map((x, i) => i).sort((a, b) => sc[b] - sc[a]); times.joint = Math.round(performance.now() - tj);
        stage2(order.slice(0, CHG_M2).map(i => cs[i]));
      } catch (err) { fail(String(err && err.message || err)); } };
    const finish = async () => {
      if (finishing) return; finishing = true; times.stage1 = Math.round(performance.now() - tS);
      const t2 = performance.now();
      const hs = await Promise.all(W.map(w => call(w, { type: 'heaps' }, 'heaps')));
      const lists = [0, 1].map(e => { const a = []; for (const h of hs) { const L = h.out[e]; for (let i = 0; i < L.s.length; i++) a.push([L.s[i], L.d[i]]); } a.sort((x, y) => y[0] - x[0]); return a.slice(0, P.bolts ? CHG_K_FB2 : CHG_K); });
      // joint initial-ray score: candidate s0 (the seed before A's base-angle draw) with A's and B's initial rays (B's
      // base-angle draw is P.offs + 1 LCG steps after s0: Hallway 25 or 26)
      const items = [];
      for (const [sc, s1] of lists[0]) items.push([0, s1, chgBack(s1, 1), sc]);
      // (B's candidates: the seed P.offs + 1 steps back, stepped back once per offset instead of from B each time: the aura
      // profile has 15 offsets, and this runs on the page's thread)
      const oMin = Math.min(...P.offs), oMax = Math.max(...P.offs);
      for (const [sc, sb] of lists[1]) { let x = chgBack(sb, oMin + 1); for (let o = oMin; o <= oMax; o++) { if (P.offs.includes(o)) items.push([1, sb, x, sc, 0, o]); x = Math.imul((x - 1) >>> 0, CHG_INVN) >>> 0; } }
      const per = Math.ceil(items.length / W.length), parts = [];
      for (let k = 0; k < W.length; k++) { const it = items.slice(k * per, (k + 1) * per), e = new Uint8Array(it.length), s0 = new Uint32Array(it.length), sc = new Float32Array(it.length);
        it.forEach((x, i) => { e[i] = x[0]; s0[i] = x[2]; sc[i] = x[3]; });
        parts.push(call(W[k], { type: 'joint', e, s0, sc, offs: P.offs }, 'joint').then(r => r.sc.forEach((v, i) => { it[i][4] = v; if (it[i][0] === 0) it[i][5] = r.vb[i]; }))); }
      await Promise.all(parts);
      // the best few thousand by a typed-array threshold, then sorted (a full sort of the aura profile's ~260k items
      // stalled the page's thread)
      let pool = items; if (items.length > 20000) { const v = Float32Array.from(items, x => x[4]).sort(); const thr = v[v.length - 8000]; pool = items.filter(x => x[4] >= thr); }
      pool.sort((a, b) => b[4] - a[4]); const seen = new Set(), top = [];
      const topV = [];
      for (const x of pool) { if (seen.has(x[2])) continue; seen.add(x[2]); top.push(x[2]); topV.push(x[5] != null ? x[5] - 24 : null); if (top.length >= CHG_M2) break; }
      top.v = topV;      // the aura profile: B's offset the joint stage found best for each (fb1Stage2 scores v +-1 around it)
      times.joint = Math.round(performance.now() - t2);
      stage2(top, lists);
    };
    const call = (w, msg, type) => new Promise(r => { w.onmessage = e => { if (e.data.type === type) r(e.data); else if (e.data.type === 'error') fail(e.data.msg); }; w.postMessage(msg); });
    const stage2 = async (top, lists) => {
      try {
      // stage 1 per effect: the best base score and the K-th (a no-lock with a clear stage-1 best for one effect read its
      // rays right and missed on the other effect or the draws between; both at the noise level: the rays were misread)
      const s1 = lists ? lists.map(l => (l.length ? [Math.round(l[0][0]), Math.round(l[l.length - 1][0])] : null)) : null;
      if (opts.full) { const tw = performance.now(), M = await opts.full; times.waitMaps = Math.round(performance.now() - tw); await Promise.all(W.map(w => call(w, { type: 'maps', S: M.S, C: M.C, N: CHG_N }, 'mapsok'))); }   // stage 2 needs all 48 frames
      const t3 = performance.now();
      const per2 = Math.ceil(top.length / W.length), qs = [];
      if (P.aura) { const r = await fb1Stage2(W, call, top, times, t3); W.forEach(w => w.terminate()); CHG.workers = null; resolve(Object.assign(r, { stats, workers: W.length, thr: gthr.slice(), s1 })); return; }
      if (!P.bolts) {
        for (let k = 0; k < W.length; k++) { const sd = top.slice(k * per2, (k + 1) * per2); qs.push(call(W[k], { type: 'q', seeds: sd }, 'q').then(r => r.out.map((q, i) => ({ seed: sd[i], q })))); }
        const all = [].concat(...(await Promise.all(qs))).map(o => { let b = 0; for (let q = 1; q < 48; q++) if (o.q[q] > o.q[b]) b = q; return { seed: o.seed, q: b, sc: o.q[b], qs: o.q }; }).sort((a, b) => b.sc - a.sc);
        W.forEach(w => w.terminate()); CHG.workers = null;
        resolve({ top: all.slice(0, 5), stats, workers: W.length, thr: gthr.slice(), s1 });
        return;
      }
      // FB2: every lightning pattern x q per candidate; candidates are dealt round-robin so each worker starts on the
      // best joint ones (a candidate whose best case cannot reach 1/CHG_RATIO of its worker's best so far is skipped)
      // every candidate's upper bound (any pattern, the best insertion count on every frame), then the full scores in
      // decreasing bound order until the next bound is below 1/CHG_RATIO of the best score (the rest stay -1e30)
      const split = async (list, type, extra) => { const ps = []; for (let k = 0; k < W.length; k++) { const sd = list.filter((x, i) => i % W.length === k); if (sd.length) ps.push(call(W[k], Object.assign({ type, seeds: sd }, extra), type).then(r => r.out.map((o, i) => Object.assign({ seed: sd[i] }, o)))); } return [].concat(...(await Promise.all(ps))); };
      const ubs = (await split(top, 'ub2')).sort((a, b) => b.ub - a.ub), all = [];
      let best = -1e30, i0 = 0;
      const cap2 = opts.cands ? 160 : 1e9;      // the narrowed T6 search: its best bounds only (a wrong carry must not delay the full search)
      while (i0 < ubs.length && i0 < cap2 && ubs[i0].ub > best / CHG_RATIO) { const batch = ubs.slice(i0, i0 + W.length).filter(o => o.ub > best / CHG_RATIO); i0 += W.length;
        for (const o of await split(batch.map(o => o.seed), 'q2', { thr: -1e30 })) { all.push(o); best = Math.max(best, o.sc); } }
      for (const o of ubs.slice(i0)) if (!all.some(x => x.seed === o.seed)) all.push({ seed: o.seed, sc: -1e30, p: 0, q: 0 });
      all.sort((a, b) => b.sc - a.sc);
      times.stage2 = Math.round(performance.now() - t3); const t4 = performance.now();
      const top1 = all[0], hy = top1 && top1.sc > -1e29 ? await call(W[0], { type: 'hyps', s0: top1.seed, tol: FB2_TOL }, 'hyps') : null;
      times.hyps = Math.round(performance.now() - t4);
      W.forEach(w => w.terminate()); CHG.workers = null;
      resolve({ top: all.slice(0, opts.cands ? 40 : 5), stats, workers: W.length, thr: gthr.slice(), s1, fb2: { hyps: hy, times, scored: all.filter(x => x.sc > -1e29).length } });
      } catch (err) { fail(String(err && err.message || err)); }
    };
    for (let k = 0; k < nw; k++) {
      const w = new Worker(url); W.push(w);
      w.onerror = e => fail('worker: ' + (e.message || 'error'));
      w.onmessage = e => {
        const m = e.data;
        if (m.type === 'error') return fail(m.msg);
        if (m.type === 'ready') {
          if (opts.cands) { if (++ready === nw) { times.narrow = opts.cands.length; finishN(); } return; }
          if (!ub) { ub = m.ub; const order = []; for (const e2 of P.effects) for (let b = 0; b <= 360; b++) order.push({ e: e2, b, u: ub[e2][b] });
            order.sort((a, b) => b.u - a.u); for (const o of order) queue.push({ e: o.e, b: o.b }); }
          if (++ready === nw) deal();
        } else if (m.type === 'done') { busy--; stats.tasks += m.n; stats.skipped += m.skipped; gthr[0] = Math.max(gthr[0], m.thr[0]); gthr[1] = Math.max(gthr[1], m.thr[1]); if (!busy) finish(); }
      };
      w.postMessage({ type: 'init', mod, S: maps.S, C: maps.C, N: opts.N || CHG_N, ND: CHG_ND, K: P.bolts ? CHG_K_FB2 : CHG_K, pat: P.bolts || P.aura ? fb2Patterns().bytes : null });
    }
  });
}
/* A real Charge (Mario seen) with no clear seed: the placement of the pictures on game frames is the likely culprit. The
 * N64 sometimes runs a game frame with no picture of its own (or shows one twice) inside the rays; the brightness
 * places that well on most Charges (clip 2026-11-03_20-54-59: 7.2k with the skip where the brightness puts it, 6.0k with
 * one picture per game frame), but where the curve is flat (frames 9-17) it can put the skip a few frames off, and
 * then every later frame is off by one: best 1.6-2.0k at 1.0x, exactly the live session's 5 no-locks of 11 (Mario 0.99,
 * 45-48 frames, clean capture). Retry with the next-best placement: the assignments around each skip of the last one
 * are banned (the skip moves or goes), at most CHG_ALTS times (a search is 1.2-3.5 s live; Time Out's target screen comes
 * ~12 s after the rays). */
/* v70: up to 4 alternatives while there is time (a lock up to ~9 s after the rays still reaches Time Out: the Spiny Flip
 * confirm is held, CHG.spiny, and the turn-2 menu prunes). A placement with no skip in the rays gets alternatives too:
 * one picture per game frame is the commonest placement, and a game frame with no picture of its own in the flat part
 * of the burst (frames 9-17) leaves it with no skip to move. Those alternatives force a skip at frame 13, then 9, then
 * 17 (the identity assignment of that frame's picture banned). */
const CHG_ALTS = 4, CHG_ALT_MS = 9000, CHG_FORCE = [13, 9, 17, 21];
async function chgRetry() {
  try {
    // a profile with shift alternatives (fb1, fb14_live.js): the first retries put every picture one frame earlier / later
    // (the trigger picture's frame read from the burst's level is off by one when the burst is brighter or darker than
    // the curve), then the skip bans as below
    const SA = chgP().shiftAlts, sh = SA && CHG.alt < SA.length ? SA[CHG.alt] : 0;
    if (sh) { CHG.alt++; if (CHG.trigT0 == null) CHG.trigT0 = CHG.trig.t; CHG.frames = CHG.F0; const G0 = chgGameFrames(null); CHG.frames = []; CHG.trig.t = CHG.trigT0 + sh * FRAME; CHG.trig.n = 3 - sh;
      const G = fbShiftG(G0, sh), t1 = performance.now(), maps = chgMaps(G, CHG.cen, CHG_N); CHG.G = G; CHG.state = 'search'; CHG.tSearch = performance.now(); chgShow();
      slog('chargeRetry', { alt: CHG.alt, shift: sh, frames: G.slice(0, CHG_N).filter(Boolean).length, mapsMs: Math.round(CHG.tSearch - t1) });
      const res = await chgSearch(maps); CHG.res = res; CHG.tLock = performance.now();
      Object.assign(CHG.info, { alt: CHG.alt, shift: sh, searchMs: Math.round(CHG.tLock - CHG.tSearch), lockAfterRaysMs: Math.round(CHG.tLock - CHG.tEnd) });
      chgDecide(); return; }
    if (CHG.trigT0 != null) { CHG.trig.t = CHG.trigT0; CHG.trig.n = 3; }
    CHG.alt++; const path0 = (CHG.skips || []).slice(); for (const k of path0) for (let d = 0; d <= 2; d++) CHG.ban.add(k + d * 65);   // the skip's picture and the next two, at their frames
    if (!path0.length) { const m = CHG_FORCE[(CHG.forced = (CHG.forced || 0) + 1) - 1]; if (m != null) CHG.ban.add((m - 3) * 64 + m); }
    CHG.frames = CHG.F0; const G = chgGameFrames(CHG.ban); CHG.frames = [];
    const t1 = performance.now(), maps = chgMaps(G, CHG.cen, CHG_N); CHG.G = G; CHG.state = 'search'; CHG.tSearch = performance.now(); chgShow();
    slog('chargeRetry', { alt: CHG.alt, banned: CHG.ban.size, skips: CHG.skips.map(k => k & 63), frames: G.slice(0, CHG_N).filter(Boolean).length, mapsMs: Math.round(CHG.tSearch - t1) });
    const res = await chgSearch(maps); CHG.res = res; CHG.tLock = performance.now();
    Object.assign(CHG.info, { alt: CHG.alt, searchMs: Math.round(CHG.tLock - CHG.tSearch), lockAfterRaysMs: Math.round(CHG.tLock - CHG.tEnd), frames: G.slice(0, CHG_N).filter(Boolean).length });
    chgDecide();
  } catch (e) { slog('chargeError', { msg: 'retry: ' + String(e && e.message || e) }); CHG.state = 'failed'; CHG.why = 'error: ' + (e && e.message || e); chgShow(); }
}
/* lock: the best seed's score must be clearly above the rest (true seeds 2900-8300 at 2.1-5.4x the runner-up on the
 * route clips, live under load included; no-lock bests 750-1500 at 1.0-1.2x) */
const CHG_MIN = 2000, CHG_RATIO = 1.8;
function chgDecide() {
  const T = CHG.res.top, a = T[0], fb2 = !!CHG.res.fb2;
  // FB2: candidates whose best case could not reach 1/CHG_RATIO of the best were skipped (score -1e30): below that ratio
  const b = fb2 ? (T.slice(1).find(x => x.sc > -1e29) || { sc: a ? a.sc / (CHG_RATIO * 1.0001) : 1, skipped: true }) : (T[1] || { sc: 1 });
  CHG.info.best = a && { seed: (a.seed >>> 0).toString(16).padStart(8, '0'), q: a.q, score: Math.round(a.sc), ratio: +(a.sc / b.sc).toFixed(2) };
  if (CHG.res.s1) CHG.info.s1 = CHG.res.s1;
  if (CHG.res.fb1 && CHG.res.fb1.times) CHG.info.stage = CHG.res.fb1.times;
  const G = CHG.G; CHG.G = null;
  if (!a || a.sc < CHG_MIN || a.sc / b.sc < CHG_RATIO) {
    CHG.state = 'nolock'; CHG.why = a ? 'no clear seed (best ' + Math.round(a.sc) + ', ' + (a.sc / b.sc).toFixed(2) + 'x the next)' : 'no candidates';
    slog('chargeNoLock', CHG.info);
    if (!fb2 && CHG.info.marioNcc >= CHG_NCC_MIN && CHG.alt < CHG_ALTS && CHG.F0 && performance.now() - CHG.tEnd < (chgP().altMs || CHG_ALT_MS) && ((CHG.skips && CHG.skips.length) || (CHG.forced || 0) < CHG_FORCE.length)) { chgRetry(); return; }
    CHG.F0 = null; chgShow(); if (G && CHG.info.marioNcc >= CHG_NCC_MIN) chgKeepCapture(G, CHG.info); return;
  }
  CHG.F0 = null;
  if (fb2) { CHG.state = 'locked'; CHG.qs = [a.q]; slog('chargeLock', Object.assign({ fb2: true, scored: CHG.res.fb2.scored }, CHG.info)); fb2Lock(CHG.res); chgShow(); return; }
  if (CHG.res.fb1) { CHG.state = 'locked'; CHG.qs = []; if (CHG.res.fb1.times) CHG.info.stage = CHG.res.fb1.times; slog('chargeLock', Object.assign({ fb1: true, hyps: CHG.res.fb1.hyps ? CHG.res.fb1.hyps.n : 0 }, CHG.info)); fb14Refine(CHG.res, G).then(r => fb14Lock(r)); chgShow(); return; }
  // q hypotheses: every first-coin frame whose score is within CHG_QTOL of the best (late coins barely move the rays: v71
  // kept 0.5% and 6 at most, and on the Duplighost render 1234abcd the true q 42 was not among them), best first; the
  // turn-1 menu's coin then weighs them (chgQBack: a likelihood, not a filter) and the tracker's shines settle them
  let qs = []; a.qs.forEach((s, q) => { if (s >= a.sc * (1 - CHG_QTOL)) qs.push(q); });
  qs = qs.sort((x, y) => a.qs[y] - a.qs[x]).slice(0, CHG_QMAX).sort((x, y) => x - y);
  const qb = chgQBack(a.seed >>> 0, qs); CHG.qsRays = qs.slice(); CHG.qw = qb.w;
  if (qb.w) { qs = qs.filter(q => qb.w[q] > 0); }
  CHG.info.qBack = qb.w ? qs.map(q => q + ':' + qb.w[q].toFixed(3)).join(' ') : CHG.menu ? 'menu too short' : 'no menu coin seen';
  CHG.info.qRays = CHG.qsRays.map(q => q + ':' + (a.qs[q] / a.sc).toFixed(4)).join(' ');
  CHG.qs = qs; CHG.state = 'locked'; slog('chargeLock', Object.assign({ qs }, CHG.info));
  chgStartTracker(a.seed >>> 0, qs, qb.w);
  chgShow();
}
/* A Charge that showed Mario but locked nothing: its game frames go into the saved session log (the last 2, as greyscale
 * JPEG of the 640x480 game raster, about 2 MB each), so the miss can be replayed offline (charge_live/tools/capture_u8.py
 * -> tools/harness.c). Encoded one frame per task so the page does not stall. */
const CHG_CAPS = [];
function chgKeepCapture(G, info) {
  const cv = document.createElement('canvas'); cv.width = 640; cv.height = 480; const cx = cv.getContext('2d'), img = cx.createImageData(640, 480), t0 = CHG.trig ? CHG.trig.t : 0;
  const cap = { at: Math.round(t0), base: CHG.trig ? +CHG.trig.base.toFixed(1) : null, prof: chgP().id, info: Object.assign({}, info, { gaps: undefined }), frames: [] };
  const idx = G.map((f, i) => i).filter(i => G[i]);
  const one = k => {
    if (k >= idx.length) { CHG_CAPS.push(cap); while (CHG_CAPS.length > 2) CHG_CAPS.shift(); slog('chargeCaptureKept', { at: cap.at, frames: cap.frames.length }); return; }
    const i = idx[k], f = G[i], Y = f.Y, d = img.data;
    for (let j = 0, o = 0; j < Y.length; j++, o += 4) { d[o] = d[o + 1] = d[o + 2] = Y[j]; d[o + 3] = 255; }
    cx.putImageData(img, 0, 0);
    cap.frames.push({ n: i < CHG_N + 2 ? i : i - (CHG_N + 4), t: Math.round(f.t - t0), m: +f.m.toFixed(1), jpg: cv.toDataURL('image/jpeg', 0.92) });
    setTimeout(() => one(k + 1), 0);
  };
  try { one(0); } catch (e) { slog('chargeError', { msg: 'capture: ' + String(e && e.message || e) }); }
}
/* the first-coin frame q, weighed by the turn-1 menu's coin before the Charge: frames before frame 0 draw only the coin
 * and the per-frame step, so for each q the coins before it follow from the seed stepped back (gap 48 after a roll >= 70,
 * else 24; readouts/charge_qback.py). v71 kept only the q for which every predicted shine on the steady menu coin was seen
 * and every seen shine was predicted (+-1.5 frames): on the Duplighost render 1234abcd the true q was not offered and the
 * check kept two wrong ones, and the simulated capture reads the menu's flashes 2.3-3.3 frames later than the console
 * calibration (4.8 after the draw). v72: each q gets the tracker's likelihood (zwLR: a seen shine it has, a missed one, a
 * false one) in a window of -1.5 .. +4 frames (the console reads at 0, the simulated capture at +2.2 .. +3.5); a q whose chain cannot be built (neither gap fits the seed) gets
 * 1e-3; the weights are normalised, and a q below 1e-4 of the best is dropped. Returns { w: { q: weight } } or {} when
 * no menu stretch of a second or more was seen. */
function chgQBack(seed, qs) {
  const M = CHG.menu; if (!M || !CHG.trig) return {};
  const rt = chgRate(), f0t = CHG.trig.t - 3 * FRAME, clk = t => (t - f0t) / rt - 4.8;   // shine seen at t -> its draw frame (the flash shows 4.8 frames after)
  const a = clk(M.from), b = clk(M.to) - 1, seen = M.taps.map(clk);
  if (b - a < 24) return {};
  const W = 1.5 + 4, d = W * (ZW_RHO + ZW_FALSE), Lm = (1 - ZW_PMISS) / d, Lmiss = ZW_PMISS, Lf = ZW_FALSE / (ZW_RHO + ZW_FALSE);
  const w = {}; let mx = 0;
  for (const q of qs) {
    let f = q, coins = 0, good = true, lw = 1; const shines = [];
    while (f - 24 > a - 48) {
      let next = null, n = 0;
      for (const gap of [24, 48]) {
        const f1 = f - gap; if (f1 > -1) continue;
        const X = chgBack(seed, -f1 + 1 + coins), v = R.randInt(X, 100)[1];
        if ((v >= 70) === (gap === 48)) { next = [f1, v]; n++; }
      }
      if (n !== 1) { if (!n) good = false; break; }
      f = next[0]; coins++; if (next[1] >= 70) shines.push(f);
    }
    if (!good) lw *= 1e-3;
    const inWin = x => x >= a && x <= b, near = (y, x) => y - x >= -1.5 && y - x <= 4;
    for (const x of shines) if (inWin(x)) lw *= seen.some(y => near(y, x)) ? Lm : Lmiss;
    for (const y of seen) if (inWin(y) && f <= y - 2 && !shines.some(x => near(y, x))) lw *= Lf;
    w[q] = lw; mx = Math.max(mx, lw);
  }
  let tot = 0; for (const q of qs) { if (w[q] < mx * ZW_CUT) w[q] = 0; tot += w[q]; }
  for (const q of qs) w[q] /= tot;
  return { w };
}
/* the zero-wait tracker from the Charge: clock frame 0 = the Charge's frame 0 (confirm + 13). The coin flash shows
 * 4.8 game frames after its draw on this clock (route clips), the tracker's coin reads assume 6, so its clock starts
 * 1.2 frames earlier. */
// the tracker's clock: the console's frame time (consoleRate: measured from the session's shines, else a real N64's)
function chgRate() { return typeof consoleRate === 'function' ? consoleRate() : FRAME; }
function chgStartTracker(seed, qs, qw) {
  if (CHG.prof && CHG.prof.id === 'jr' && !CHG.jrInner && typeof jrLock === 'function') return jrLock(seed, qs, qw);   // Jr. Troopa: jr_live.js
  const dup = !!CHG.prof && CHG.prof.id === 'dup';     // (CHG.prof, not chgP(): the replay tests run this function alone)
  // the Duplighost lock came after the route left that step (the runner confirmed Do Nothing before it landed): nothing to plan
  if (dup && !(isRoute() && RT()[routeStep] && RT()[routeStep].chg === 'dup')) { slog('dupLockAfterStep', { step: routeStep }); return; }
  const rate = chgRate(), t0 = CHG.trig.t - 3 * rate - 1.2 * rate - num('vlag'), parts = [];
  for (const q of qs) for (const [l, wl] of CHG_LAGS) {
    const ev = R.buildEv([{ f: -13, id: 'hw_charge' }]);
    parts.push({ S: { s: seed, nc: q, inst: [] }, g: 0, ev, evMax: 46, pauseAt: CHG_N + 2, pause: l, w: wl * (qw && qw[q] != null ? qw[q] : 1 / qs.length), m: new Set(), fx: new Set(), err: 0 });
  }
  // the background ("the lock or the model is wrong", zwDoubt): ZW_BG0 of the prior mass
  Object.assign(zw, { on: true, dead: false, t0, rate, taps: [], vis: [], visFrom: null, visTo: null, parts, nBase: 1, f0: 0, tapLate: dup ? 4 : 3.5, imps: dup ? null : CHG_IMPS, shifts: dup ? null : CHG_SHIFTS, src: 'charge', fight: dup ? 'dup' : CHG.prof && CHG.prof.id === 'jr' ? 'jr' : 'hw', bg: ZW_BG0 / (1 - ZW_BG0), bgTo: null });
  // what the coin did while the seed was searched
  for (const t of CHG.taps) zwTap(t);
  let up = null;
  // a stretch ends 6 frames before the coin went: a shine drawn on frame f flashes at about f + 6 on this clock (zwTap),
  // so one drawn later never showed. The same end as zwInput's (c - 4, c = the bar hiding - 2). With - 4, a lock that
  // landed after the Spiny Flip confirm killed the true seed on a shine drawn 5 frames before the bar hid (live log
  // 1793735643131, charge_live/test_fix_proposal.js).
  for (const [t, p] of CHG.pres) {
    if (p && up == null) up = t;
    else if (!p && up != null) { const a = zwF(up + 1000, 0), b = zwF(t, 0) - 6; if (b > a) zw.vis.push([a, b]); up = null; }
  }
  if (up != null) { zw.visFrom = zwF(up + 1000, 0); zw.visTo = null; }
  slog('zwStart', { bases: 1, particles: parts.length, from: 'charge', qs, fight: zw.fight });
  if (!dup && CHG.spiny != null) { const c = CHG.spiny; CHG.spiny = null; zwInput('hw_spiny', c, VAN.B(), CHG_IMPS); }
}
function chgHyps() { return zw.on && zw.src === 'charge' ? zw.parts.length : CHG.prof && CHG.prof.id === 'fb1' && typeof FB14 !== 'undefined' && FB14.on ? FB14.states.length : typeof FB2 !== 'undefined' && FB2.on ? FB2.hyps.length : null; }
function chgShow() {
  const el = $('chg-status'); if (!el) return;
  const s = CHG.state, I = CHG.info || {};
  const lost = s === 'locked' && zw.on && zw.src === 'charge' && zw.dead;
  // v72: the tracker weighs its states (zwDoubt: the share left for "none of them is the game's"); 50%+ = doubtful, no beeps
  const dz = s === 'locked' && zw.on && zw.src === 'charge' && !zw.dead ? zwDoubt() : 0, doubt = dz >= 0.5, errs = zw.on && zw.parts && zw.parts.length ? Math.min(...zw.parts.map(p => p.err || 0)) : 0;
  const lock = lost ? 'LOST' : doubt ? 'DOUBTFUL' : s === 'locked' ? 'yes' : s === 'search' || s === 'maps' ? 'searching…' : s === 'capture' ? 'reading the rays…' : s === 'nolock' || s === 'failed' || s === 'notseen' ? 'no' : '–';
  const t = I.lockAfterRaysMs != null ? (I.lockAfterRaysMs / 1000).toFixed(1) + ' s after the rays' : s === 'search' && CHG.tSearch ? (Math.round((performance.now() - CHG.tSearch) / 100) / 10) + ' s so far' : '–';
  const h = chgHyps();
  el.innerHTML = '<b>Charge lock: ' + lock + '</b>' + (s === 'nolock' || s === 'failed' || s === 'notseen' ? ' (' + (CHG.why || '') + ')' : '') +
    '<br>Time to lock: ' + t + (I.searchMs != null ? ' (search ' + (I.searchMs / 1000).toFixed(1) + ' s, ' + (CHG.res ? CHG.res.workers : '?') + ' threads)' : '') +
    '<br>Hypotheses left: ' + (h != null ? h + (zw.dead ? ' (none fit: No edge)' : '') : '–') +
    (s === 'locked' && zw.on && zw.src === 'charge' && !zw.dead ? ' · fit ' + Math.round(100 * (1 - dz)) + '%' + (errs ? ' (best state: ' + errs + ' shine' + (errs > 1 ? 's' : '') + ' did not fit)' : '') : '') +
    (doubt ? '<br><b style="color:var(--warn)">Lock doubtful: the coin fits the tracked states badly (' + errs + ' missed or extra shines on the best one). No beeps; press normally.</b>' : '') +
    (lost ? '<br><b style="color:var(--warn)">Seed lost ' + (zw.deadAt != null ? Math.round((zw.deadAt - zw.f0) * zw.rate / 100) / 10 + ' s after the Charge' : '') + ': the coin did something none of the tracked states fit (a missed or extra shine, an unseen input). Press normally; the next Charge reads it again.</b>' : '') +
    (CHG.prof && CHG.prof.id === 'dup' ? dupStatusLine(s, lost || doubt) : '') +
    (typeof JR_READY !== 'undefined' && JR_READY && ((CHG.prof && CHG.prof.id === 'jr') || jrStepNow()) ? jrStatusLine(s, lost || doubt) : '') +
    (I.best ? '<br><span class="note">seed ' + I.best.seed + ', q ' + (CHG.qs || [I.best.q]).join('/') + ', score ' + I.best.score + ' (' + I.best.ratio + 'x)' + (I.dxWorld ? ', Mario +' + I.dxWorld + ' units' : '') + '</span>' : '');
}
/* the Duplighost line of the Charge panel: the plan's chances, or what to do without a lock (dup_charge/odds.json:
 * blind 3+ 47.2%, 4 12.9%; the Surge route without a lock is the same per-frame draw, 47.5% / 12.9%) */
const DUP_BLIND = { p3: 0.47, p4: 0.13 };
function dupStatusLine(s, lost) {
  const P = st.plan, pc = x => Math.round(100 * x) + '%';
  if (s === 'nolock' || s === 'failed' || s === 'notseen' || lost) return '<br><b>Duplighosts: play it blind.</b> Do Nothing whenever you like: 3+ copies about ' + pc(DUP_BLIND.p3) + ', all 4 about ' + pc(DUP_BLIND.p4) + ' (the same as the RTA Surge route with no lock).';
  if (P && P.mix && P.mix.p4 != null) return '<br><b>Do Nothing on the beep:</b> 3+ copies ' + pc(P.mix.p) + ', all 4 ' + pc(P.mix.p4) + ' (blind: ' + pc(DUP_BLIND.p3) + ' / ' + pc(DUP_BLIND.p4) + ')';
  if (s === 'locked') return '<br>Duplighosts: locked. The beeps start on Bombette\'s Strategies screen (hand on Do Nothing).';
  return '';
}
/* for tests and the session log: the weighted share of the tracker's states for which confirming Time Out on clock
 * frame c works (c = zwF(confirm time, 0)) */
function chgEvalAt(c) {
  zwUpdate(Math.min(c, Math.floor(zwF(performance.now(), 0))));
  let w = 0, ok = 0; for (const p of zw.parts) { if (p.S.inst.length || (p.S.extra && p.S.extra.size) || p.g > c) continue; w += p.w; if (R.works(p.S.s, p.S.nc, c, p.g, R.PROFILES.timeout)) ok += p.w; }
  return { p: w ? ok / w : null, n: zw.parts.length };
}
/* for tests: what zwPlan would beep if Time Out's target screen showed on clock frame cScr (the menu's coin counted up
 * to 4 frames before it): the best confirm frame in the next winS seconds after leadS, with zwPlan's press spread */
function chgPlanAt(cScr, leadS, winS) {
  zw.visTo = cScr - 4; zwUpdate(cScr);
  const parts = zw.parts.filter(p => !p.S.inst.length && !(p.S.extra && p.S.extra.size));
  if (!parts.length) return { noEdge: 'nothing fits', parts: 0 };
  const tot = parts.reduce((a, p) => a + p.w, 0), from = Math.ceil(cScr + leadS * 1000 / zw.rate + 1), W = Math.max(0, Math.round(winS * 1000 / zw.rate));
  const sc = new Array(W + 1).fill(0);
  const PD = typeof pressDist === 'function' ? pressDist() : PRESS_ERR, D = Math.max(...PD.map(x => Math.abs(x[0])));
  for (const p of parts) { const tab = []; for (let c = from - D; c <= from + W + D; c++) tab.push(R.works(p.S.s, p.S.nc, c, p.g, R.PROFILES.timeout) ? 1 : 0);
    for (let k = 0; k <= W; k++) for (const [d, q] of PD) sc[k] += p.w * q * tab[k + D + d]; }
  let k = 0; for (let i = 1; i <= W; i++) if (sc[i] > sc[k] + 1e-12) k = i;
  const states = new Set(parts.map(p => p.S.s + ':' + p.S.nc + ':' + p.g)).size;
  return { target: from + k, p: sc[k] / tot, parts: parts.length, states, from, W };
}
