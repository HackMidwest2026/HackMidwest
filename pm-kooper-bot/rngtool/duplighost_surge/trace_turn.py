"""Q1: every gRandSeed draw from the first Spiny Surge throw to the 4th Duplighost copy roll, emulator vs model.

For each case (seed, mash pattern, menu-navigation timing, confirm frame) the turn is played in the emulator (debug
core, every rand_int logged with its caller) and the draws are compared one by one (frame, range, value) with
surge_model.simulate(), which only gets: the seed before the first throw's frame, the frame of the next coin draw,
the throw frames, the damage class (fireworks of 8 or 6 draws) and the confirm frame.
DIAGNOSTIC RAM write: gRandSeed (both words) set once, at Mario's turn-1 menu (stands in for an unknown seed).
usage (from /tmp/claude-0/pm/bot1): M64P_DBG=1 PYTHONPATH=. python3 .../trace_turn.py [N_CASES] [OUT.json]"""
import os, sys, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.getcwd())
from dsurge import *
import surge_model as SM

KIND = {SPINY_RA[0]: 'spiny', SPINY_RA[1]: 'spiny', SPINY_RA[2]: 'spiny', SPINY_RA[3]: 'spiny',
        FIREWORK_RA: 'fw', COIN_RA: 'coin', FRAME_RA: 'frame'}
# minimum frames between the 6 menu inputs (measured, nav probe): up->up 5, up->A 1, A->A 2, A->up 3, up->A 1
MIN_GAP = [5, 1, 2, 3, 1]


def emu_trace(r):
    """draws from the first throw's frame on, as (t, kind, max, value), t relative to the first throw"""
    F1 = r.spinies()[0]; out = []; other = []; nframe = {}
    for row in r.log[F1:]:
        t = row['f'] - F1
        for mx, ra, v in row['ev']:
            k = 'roll' if (ra == COPY_RA and mx == 1000) else KIND.get(ra)
            if k is None: other.append((t, mx, hex(ra), v)); k = 'other'
            if k == 'frame': nframe[t] = nframe.get(t, 0) + 1; continue
            out.append((t, k, mx, v))
    return F1, out, other, nframe


def run_case(r, seed, pat, gaps, confirm_after_menu):
    r.reset(seed)
    on, off, flicks, delay = (list(pat) + [0])[:4]
    r.surge(on, off, flicks=flicks, delay=delay); r.to_mario_menu()
    at = [confirm_after_menu - sum(gaps)]
    for g in gaps: at.append(at[-1] + g)
    r.switch(at)
    r.enemy_turn()
    F1, tr, other, nframe = emu_trace(r)
    sp = [f - F1 for f in r.spinies()]
    L = sp[-1]
    nc = next(t for (t, k, mx, v) in tr if k == 'coin')
    fwd = [n for f, n in r.fireworks() if f - F1 in [L + a for a in SM.FW_AT]]
    fw_draws = fwd[0] if fwd else 8
    s1 = r.log[F1]['seed0']
    C = r.marks['confirm'] - F1
    mt = []; SM.simulate(s1, nc, sp, C, fw_draws, trace=mt)
    rolls_e = [v for (t, k, mx, v) in tr if k == 'roll'][:4]
    # compare up to the 4th roll
    last = max(i for i, x in enumerate(tr) if x[1] == 'roll') if rolls_e else len(tr) - 1
    tr4 = tr[:last + 1]
    bad_frames = sorted(t for t, n in nframe.items() if n != 1 and t <= tr4[-1][0])
    return {
        'seed': '%08x' % seed, 'pattern': pat, 'gaps': gaps, 'spinies': len(sp), 'throws': sp,
        'menu_after_last': r.marks['mario_menu'] - F1 - L, 'confirm_after_menu': r.marks['confirm'] - r.marks['mario_menu'],
        'fw_draws': fw_draws, 'partner': r.partner(), 'rolls': rolls_e,
        'model_match': tr4 == mt[:max(i for i, x in enumerate(mt) if x[1] == 'roll') + 1],
        'n_draws_compared': len(tr4), 'other_draws': other[:10], 'frames_not_1_draw': bad_frames[:10],
        'replay_ok': r.check(),
        'draw_counts': {k: sum(1 for x in tr4 if x[1] == k) for k in ('spiny', 'fw', 'coin', 'roll')},
        'first_mismatch': next(([a, b] for a, b in zip(tr4, mt) if a != b), None),
    }


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    OUT = sys.argv[2] if len(sys.argv) > 2 else None
    rnd = random.Random(20261102)
    pats = [(1, 1, None), (1, 2, None), (2, 2, None), (3, 3, None), (2, 1, None), (4, 4, None), (3, 3, 4, 40), (2, 2, 6, 45)]
    r = Run(0)
    res = []
    for i in range(N):
        seed = rnd.getrandbits(32); pat = pats[i % len(pats)]
        gaps = [g + rnd.randint(0, 12) for g in MIN_GAP]
        d = sum(gaps) + 5 + rnd.randint(0, 60)
        x = run_case(r, seed, pat, gaps, d); res.append(x)
        print(json.dumps({k: x[k] for k in ('seed', 'pattern', 'spinies', 'menu_after_last', 'confirm_after_menu', 'fw_draws',
                                             'partner', 'rolls', 'model_match', 'other_draws', 'replay_ok', 'draw_counts',
                                             'first_mismatch')}), flush=True)
    ok3 = [x for x in res if sum(v < 600 for v in x['rolls']) >= 3]
    print('cases with 3+ copies: %d, model matched %d' % (len(ok3), sum(x['model_match'] for x in ok3)))
    print('cases %d, model matched %d, replay ok %d, unmodelled draws %d' % (
        len(res), sum(x['model_match'] for x in res), sum(x['replay_ok'] for x in res), sum(len(x['other_draws']) for x in res)))
    if OUT: json.dump(res, open(OUT, 'w'), indent=1)
