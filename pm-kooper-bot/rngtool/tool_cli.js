/* Command-line front end to pmrng_core.js (used by the emulator end-to-end test).
 * node tool_cli.js find   '{"taps":[ms,...]}'                         -> seeds (value before the first tapped draw)
 * node tool_cli.js resync '{"from":seed,"taps":[...],"nmax":N}'        -> matches [{n, seed}]
 * node tool_cli.js plan   '{"seed":seedBeforeLastDraw,"from":f,"to":t,"minRun":k,"profile":"timeout|dup4"}' -> best window (frames after that draw)
 * node tool_cli.js after  '{"seed":seed,"pattern":"S..S"}'             -> seed after the last draw + frames to next draw */
const R = require('./pmrng_core.js');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const os = require('os');
if (!isMainThread) {
  const { pattern, lo, hi } = workerData;
  parentPort.postMessage(R.searchShineStart(pattern, lo, hi, 64));
} else {
  const [cmd, arg] = process.argv.slice(2); const a = JSON.parse(arg || '{}');
  const out = o => console.log(JSON.stringify(o));
  if (cmd === 'find') {
    const p = R.patternFromTaps(a.taps); if (p.error) { out(p); process.exit(0); }
    const n = Math.max(1, Math.min(os.cpus().length, 16)), lo = R.SHINE_MIN, span = Math.ceil((4294967296 - lo) / n);
    let done = 0; const seeds = []; const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const w = new Worker(__filename, { workerData: { pattern: p.pattern, lo: lo + i * span, hi: Math.min(4294967296, lo + (i + 1) * span) } });
      w.on('message', r => { seeds.push(...r); if (++done === n) out({ pattern: p.pattern, worst: p.worst, seeds, seconds: (Date.now() - t0) / 1000 }); });
    }
  } else if (cmd === 'resync') {
    const p = R.patternFromTaps(a.taps); if (p.error) { out(p); process.exit(0); }
    out({ pattern: p.pattern, worst: p.worst, matches: R.resync(a.from >>> 0, p.pattern, a.nmax, 16, a.nlo || 0) });
  } else if (cmd === 'filter') {
    const p = R.patternFromTaps(a.taps); out({ pattern: p.pattern, seeds: a.seeds.filter(s => R.matches(s >>> 0, p.pattern)) });
  } else if (cmd === 'pattern') {
    out(R.patternFromTaps(a.taps));
  } else if (cmd === 'plan') {
    const P = R.PROFILES[a.profile || 'timeout'];
    let w = R.bestWindow(a.seed >>> 0, a.from, a.to, a.minRun, P), target = w ? w.start + Math.floor((w.length - 1) / 2) : null;
    if (P.id === 'dup3') {                     // same as the page: aim at an all-4 frame inside a 3+ window
      for (let s0 = a.from, n = 0; n < 200; n++) {
        const c = R.bestWindow(a.seed >>> 0, s0, a.to, a.minRun, P); if (!c) break;
        const mid = (c.start + c.end) / 2; let best = null;
        for (let f = c.start; f <= c.end; f++) if (R.works(a.seed >>> 0, 0, f, 0, R.PROFILES.dup4) && (best === null || Math.abs(f - mid) < Math.abs(best - mid))) best = f;
        if (best !== null) { w = c; target = best; break; }
        s0 = c.end + 1;
      }
    }
    out({ target, window: w, table: R.timeOutTable(a.seed >>> 0, a.from, a.to, P).map(x => x ? 'S' : '.').join('') });
  } else if (cmd === 'after') {
    out(R.afterPattern(a.seed >>> 0, a.pattern));
  } else if (cmd === 'beforelast') {
    out({ seed: R.seedBeforeLastDraw(a.seed >>> 0, a.pattern) });
  }
}
