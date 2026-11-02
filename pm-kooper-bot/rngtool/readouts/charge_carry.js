/* Carry a Charge-ray seed through Hallway Bowser T1 (Super Charge, Spiny Flip, Bowser's attack) into the T2 Time Out
 * with the speedrun page's model (pmrng_core.js: TURNS hw_charge / hw_spiny, bowserT1, PROFILES.timeout).
 * Frame 0 = the first Charge effect's creation (= Charge confirm + 13); seed = gRandSeed before frame 0's draws.
 * usage: node charge_carry.js '{"seed":"6d3b7b2b","qs":[43],"spiny":F2,"timeout":F3,"shines":[...],"vis":[[a,b],...],"near":10}'
 *   shines: game frames (rel. 0, float) of the middle of each seen coin flash (flash = draw +6/+7); vis: frame ranges
 *   where the coin was on screen (a shine drawn there must be seen, a normal spin must not flash). Prints each Spiny Flip hypothesis (impact frame x guard x first coin q) that
 *   fits the coin observations, with the Time Out result at F3 and the working frames near it. */
const R = require('../pmrng_core.js');
const a = JSON.parse(process.argv[2]);
const seed = parseInt(a.seed, 16) >>> 0, F2 = a.spiny, F3 = a.timeout, near = a.near || 10;
const vis = a.vis || [], obs = a.shines || [], TOL = a.tol || 1.5;   // obs: game frame (float) of each seen flash's middle
const inVis = f => vis.some(([x, y]) => f >= x && f <= y);
const out = [];
for (const q of a.qs) for (let imp = (a.impLo || 138); imp <= (a.impHi || 170); imp++) for (const guard of [false, true]) {
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: F2, id: 'hw_spiny', imp, guard }]);
  const S = { s: seed, nc: q, inst: [] }; const draws = []; const t0 = F3 - near - 2;
  for (let f = 0; f < t0; f++) { const r = R.frameEv(S, f, ev); if (r !== null) draws.push([f, r]); }
  if (S.inst.length || (S.extra && S.extra.size)) { out.push({ q, imp, guard, error: 'events still running at t0' }); continue; }
  // coin check: every predicted draw whose shine frames (+6/+7) are on screen must match; every observed shine must be predicted
  let bad = 0, checked = 0;
  const seen = f => obs.some(o => Math.abs(f + 6.5 - o) <= TOL);   // flash on draw+6/+7
  for (const [f, sh] of draws) if (inVis(f + 5) && inVis(f + 8)) { checked++; if (sh !== seen(f)) bad++; }
  for (const o of obs) if (o < t0 - 8 && !draws.some(([g, sh]) => sh && Math.abs(g + 6.5 - o) <= TOL)) bad++;
  const works = R.works(S.s, S.nc, F3, t0, R.PROFILES.timeout);
  const ok = []; for (let d = -near; d <= near; d++) if (R.works(S.s, S.nc, F3 + d, t0, R.PROFILES.timeout)) ok.push(d);
  out.push({ q, imp, guard, branch: S.branch, bad, checked, works, workingOffsets: ok, shinesPred: draws.filter(x => x[1]).map(x => x[0]), draws });
}
console.log(JSON.stringify(out));
