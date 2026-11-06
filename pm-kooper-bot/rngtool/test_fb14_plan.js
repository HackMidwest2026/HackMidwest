/* Final Bowser T1-T4: the page's plans (charge_live/fb14_live.js fb14Plan: its share of the states, zwChoose, best
 * chance, lead 1.5 s, max extra wait 1 s) scored against the model, through the built standalone page in headless
 * Chromium. Per case: a random game (seed, first coin) with the aura pattern and lightning phases of an emulator log
 * (fixtures/fb14_logs.json); the page's states are the true state with console lag 0 and its lag-1 twin (an exact lock,
 * 0.75 / 0.25), as the T1 Charge lock leaves them when its fit is unique. For each turn the page plans on the lever's
 * screen, the press lands 1 frame early 25%, on time 50%, late 25%, and the true state plays it: Bowser misses (T4: the
 * wave, missed). The next turn's Mario confirm comes 60 frames after Bowser's turn (popup left alone: the partner menu
 * 154 frames later, the lever screen 66 frames after that). Prints per turn the page's claimed chance (mean), the
 * model's result, blind; and all four.
 * usage (from rngtool/, after python3 build_page.py): node test_fb14_plan.js [PAGE] [N=60] */
'use strict';
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const N = +(process.argv[3] || 60);
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_logs.json'), 'utf8'));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  const res = await p.evaluate(({ N, FIX }) => {
    const T = window.__tot, F = window.__fb14, X = F.FB14;
    let rs = 12345; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296;
    const lever = t => T.RT().findIndex(s => s.fb14 === t && s.fb14role === 'lever');
    const per = { 1: [0, 0, 0], 2: [0, 0, 0], 3: [0, 0, 0], 4: [0, 0, 0] }; let all4 = 0, cases = 0; const rows = [];
    for (let k = 0; k < N; k++) {
      const L = FIX[k % FIX.length], OFF = 1000;
      const ph = [(((L.ph[0] - OFF) % 130) + 130) % 130, (((L.ph[1] - OFF) % 220) + 220) % 220], c = Uint8Array.from(L.aura);
      const truth = F.fbNew({ s: (rnd() * 4294967296) >>> 0, nc: OFF + 61 + Math.floor(rnd() * 48), f: OFF + 61, c, ph, l: 0, w: 1, from: OFF + 61 });
      let M = OFF, ok4 = true; const row = [];
      for (let t = 1; t <= 4; t++) {
        if (t > 1) { const tt = F.fbClone(truth); F.fbRun(tt, M); truth.s = tt.s; truth.nc = tt.nc; truth.f = tt.f; truth.ev = tt.ev; truth.resp = tt.resp; truth.wv = tt.wv; truth.prev = tt.prev; truth.out = tt.out; truth.sh = tt.sh;}
        // the page's states: the truth (lag 0) and its lag-1 twin
        const S0 = F.fbClone(truth); if (t === 3) { S0.ev.push({ k: 'jelly', f: M + 118 }); S0.ev.sort((a, b) => a.f - b.f); } else if (t > 1) { S0.ev.push({ k: 'chg', f: M + 13 }, { k: 'chg', f: M + 16 }); S0.ev.sort((a, b) => a.f - b.f); }
        const S1 = F.fbClone(S0); S1.l = 1; S1.f = S0.f; S0.w = 0.75; S1.w = 0.25; S0.lw = S1.lw = 1; S0.from = S1.from = S0.f;
        X.on = true; X.states = [S0, S1]; X.taps = []; X.vis = []; X.visFrom = null; X.bg = 0; X.bgFrom = 0; X.t0 = 0; X.rate = 33.367;
        T.setStep(lever(t));
        const scr = M + (t === 3 ? 154 : 154) + 66, pl = F.plan(scr);
        if (!pl || pl.target == null) { row.push({ t, none: pl && pl.none }); ok4 = false; per[t][2]++; break; }
        const u = rnd(), d = u < 0.25 ? -1 : u < 0.75 ? 0 : 1, Fc = pl.target + d;
        // the truth plays its turn: Mario's action, then the confirm on Fc
        const G = F.fbClone(S0); G.l = 0;
        const kind = t === 1 ? 'cn' : 'nothing';
        if (kind === 'cn') { for (let i = 200; i < 210; i++) G.ev.push({ k: 'puff', f: Fc + i }); G.ev.push({ k: 'ai', f: Fc + 332, turn: t, t4: false }); }
        else G.ev.push({ k: 'ai', f: Fc + 13, turn: t, t4: t === 4 });
        G.ev.sort((a, b) => a.f - b.f);
        while (!(G.out[t] && G.out[t].v != null)) F.fbStep(G);
        const o = G.out[t], good = !!o.ok, atk = o.atk;
        per[t][0] += pl.p; per[t][1] += good ? 1 : 0; per[t][2]++;
        row.push({ t, target: pl.target, p: +pl.p.toFixed(3), d, atk, v: o.v, ok: good });
        if (!good) ok4 = false;
        // on to the next turn: Bowser's turn ends, the next menu, 60 frames, the next Mario confirm
        const END = { fire: 134, claw: 83, slam: 101, wave: 226 }[atk];
        Object.assign(truth, F.fbClone(G)); M = o.ai + ({ slam: 52, claw: 62, fire: 55, wave: 72 })[atk] + END + 60;
        if (!good) break;
      }
      cases++; if (ok4) all4++; rows.push(row);
    }
    const out = {}; for (const t in per) out['T' + t] = { claimed: +(per[t][0] / Math.max(1, per[t][2])).toFixed(3), model: +(per[t][1] / Math.max(1, per[t][2])).toFixed(3), n: per[t][2] };
    return { per: out, all4: +(all4 / cases).toFixed(3), cases, sample: rows.slice(0, 4) };
  }, { N, FIX });
  console.log(JSON.stringify(res));
  const bad = errs.length || Object.values(res.per).some(x => x.n && (x.model < 0.85 || Math.abs(x.claimed - x.model) > 0.12));
  console.log(bad ? 'FAIL' : 'PASS', ': per turn claimed / model', Object.entries(res.per).map(([k, v]) => k + ' ' + v.claimed + ' / ' + v.model + ' (' + v.n + ')').join(', '), '; all four', res.all4, errs.slice(0, 3).join(' '));
  await b.close(); process.exit(bad ? 1 : 0);
})();
