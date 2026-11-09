/* v83: the perfect-press planner (page_template.html ppPick / ppText, used by zwChoose, mixPlan, fb2PlanK / fb2PlanT7).
 * The beeped frame must always be a frame that works (for the states: share >= 0.5 and within PP_TOL of the best in
 * reach), the centre of the widest run of working frames; never a failing frame between working ones (the Jr. T4 case:
 * working at -2, -1, +2 around a failing 0). The goals with an all-4-like top outcome (safe3 / free / run2 / four), the
 * clamp to the reachable window, no edge, and the text ("Perfect press: works · window N frames · seed confidence NN%").
 * usage (from rngtool/, after python3 build_page.py): node test_pp_plan.js [PAGE] */
'use strict';
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(() => {
    const T = window.__tot, a = 80, bb = 130, mk = (set, v) => { const s = new Float64Array(bb - a + 1); for (const [f, x] of set) s[f - a] = x; return s; };
    const ones = (lo, hi, v = 1) => { const o = []; for (let f = lo; f <= hi; f++) o.push([f, v]); return o; };
    const spread = sh => c => 0.25 * (sh[c - 1 - a] || 0) + 0.5 * (sh[c - a] || 0) + 0.25 * (sh[c + 1 - a] || 0);
    const pick = (sh, sh4, from, W, goal) => T.ppPick(sh, sh4, a, bb, from, W, spread(sh), goal || 'safe3');
    const out = {};
    // the Jr. T4 case: works on 98, 99 and 102 (the old spread-weighted best could sit on 100 / 101 between them)
    { const sh = mk([[98, 1], [99, 1], [102, 1]]); out.jr = pick(sh, null, 92, 14); out.jrWorks = [98, 99, 102]; }
    // the widest run wins over an earlier single frame; its centre
    out.wide = pick(mk([[101, 1]].concat(ones(105, 109))), null, 95, 20);
    // the centre clamped into the reachable window (a run that started before the earliest beepable frame)
    out.clamp = pick(mk(ones(88, 97)), null, 95, 10);
    // within PP_TOL of the best share the frames count as working; further below they do not
    out.tolIn = pick(mk([[101, 1]].concat(ones(105, 109, 0.97))), null, 95, 20);
    out.tolOut = pick(mk([[101, 1]].concat(ones(105, 109, 0.9))), null, 95, 20);
    // no frame most states agree on: not ok (zwChoose then says no edge on the perfect press's chance)
    out.none = pick(mk([[101, 0.3], [102, 0.45]]), null, 95, 20);
    // goals: 3+ on 100..108 and 110..111, all 4 on 101, 107 and 110..111
    { const s3 = mk(ones(100, 108).concat(ones(110, 111))), s4 = mk([[101, 1], [107, 1], [110, 1], [111, 1]]);
      out.goals = {}; for (const g of ['safe3', 'free', 'run2', 'four']) out.goals[g] = pick(s3, s4, 95, 20, g);
      out.goals4in = {}; const s4b = mk([[101, 1], [107, 1]]); for (const g of ['safe3', 'free', 'run2', 'four']) out.goals4in[g] = pick(s3, s4b, 95, 20, g); }
    // the texts
    out.txt = T.ppText({ pp: 0.97, ppStates: 1, win: 5, p: 0.81, doubt: 0.03 }, 'jrcc_bomb');
    out.txtLong = T.ppText({ pp: 0.97, ppStates: 1, win: 5, p: 0.81, doubt: 0.03 }, 'jrcc_bomb', true);
    out.txtPart = T.ppText({ pp: 0.8, ppStates: 0.82, win: 3, p: 0.7, doubt: 0.02 }, 'timeout');
    out.txtDup = T.ppText({ pp: 0.97, pp4: 0.9, ppStates: 1, win: 5, win4: 2, p: 0.9, p4: 0.5, doubt: 0.03 }, 'dup3');
    out.txtDup3 = T.ppText({ pp: 0.97, pp4: 0.1, ppStates: 1, win: 5, win4: null, p: 0.9, p4: 0.1, doubt: 0.03 }, 'dup3');
    out.txtPb = T.ppText({ pp: 1, pp4: 1, ppStates: 1, win: 4, win4: 1, p: 0.95, p4: 0.6, doubt: 0 }, 'jrpb5');
    return out;
  });
  console.log(JSON.stringify(r).slice(0, 1500));
  check(r.jr.ok && r.jr.target === 98 && r.jrWorks.includes(r.jr.target), 'Jr. T4 case (works -2, -1, +2): a working frame, in the 2-frame run (' + r.jr.target + ', window ' + r.jr.run.length + ')');
  check(r.wide.target === 107 && r.wide.run.length === 5, 'the centre of the widest run (107 of 105..109), not the earlier single frame');
  check(r.clamp.target === 95 && r.clamp.run.length === 10, 'a run reaching before the earliest beepable frame: the reachable frame most centred (95)');
  check(r.tolIn.target === 107, 'frames within ' + 0.05 + ' of the best share count as working (107)');
  check(r.tolOut.target === 101, 'frames further below the best share do not (101)');
  check(!r.none.ok, 'no frame most states agree on: not ok (no edge)');
  const G = r.goals, G2 = r.goals4in;
  check(G.safe3.target === 104, '3+ safe: the centre of the widest 3+ window (104)');
  check(G.four.target === 110 && G.four.run4.length === 2 && G.run2.target === 110, '4 first and 4 if 2+: the widest all-4 window (110..111), even in a narrower 3+ window');
  check([101, 107].includes(G.free.target) && G.free.run.length === 9, '4 when it\'s free: an all-4 frame inside the widest 3+ window, a 3+ frame either side (' + G.free.target + ')');
  check(G2.safe3.target === 104 && [101, 107].includes(G2.free.target) && [101, 107].includes(G2.four.target) && G2.run2.target === G2.free.target, 'no 2+ all-4 run: 4 if 2+ = 4 when it\'s free; 3+ safe stays centred');
  check(r.txt === 'Perfect press: works · window 5 frames · seed confidence 97%', 'text: ' + r.txt);
  check(/Counting your press spread: 81%/.test(r.txtLong), 'the spread-weighted chance only in the long text (Details): ' + r.txtLong);
  check(r.txtPart === 'Perfect press: works for 82% of the states · window 3 frames · seed confidence 98%', 'text, states disagreeing: ' + r.txtPart);
  check(r.txtDup === 'Perfect press: 3+ copies (window 5 frames), all 4 (window 2 frames) · seed confidence 97%', 'text, Duplighosts: ' + r.txtDup);
  check(r.txtDup3 === 'Perfect press: 3+ copies (window 5 frames), not all 4 · seed confidence 97%', 'text, Duplighosts 3 only: ' + r.txtDup3);
  check(r.txtPb === 'Perfect press: 5+ bounces (window 4 frames), 6+ (window 1 frame) · seed confidence 100%', 'text, Power Bounce: ' + r.txtPb);
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
