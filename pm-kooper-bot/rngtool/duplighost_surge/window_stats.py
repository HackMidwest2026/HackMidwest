"""Q2: with the seed known at the Surge, how does the Change Member confirm frame map to the number of copies?

Over many random (seed, coin phase) pairs, from Mario's menu (L+103) on: for each confirm frame, all 4 / 3+ copies
(surge_model, fast event-driven version: between draws the seed is jumped with the LCG's affine power; checked
against surge_model.simulate on random cases first). Frames are game frames (30 per second on the console).
usage: python3 window_stats.py [N_SEEDS] [READY] [SPAN]
  READY = first frame (after Mario's menu comes up) the runner can confirm, SPAN = frames looked at after that."""
import sys, random, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import surge_model as SM

MUL, M = SM.MUL, SM.M
_aff = {}


def affine(n):
    if n not in _aff:
        A, C = 1, 0
        a, c = MUL, 1            # x -> a x + c (one step); binary powering
        k = n
        while k:
            if k & 1: A, C = (a * A) & M, (a * C + c) & M
            a, c = (a * a) & M, (a * c + c) & M
            k >>= 1
        _aff[n] = (A, C)
    return _aff[n]


def jump(s, n):
    A, C = affine(n); return (A * s + C) & M


def d359(s):                       # one rand_int(359) / (1000) / (100): value from the advanced seed (no rejection)
    return s // (M // 360)


def after_confirm(s, nc):
    """s: seed before the confirm frame's draws (frame 0 = confirm), nc: next coin frame (>= 0).
    Returns the number of copies: exact for 3 and 4; 2 means "2 or fewer" (stops at the 2nd failed copy; the rolls
    after it would also need Close Call draws once Mario is under 6 HP)."""
    t = 0; next_roll = SM.ROLL1; fx = None; fails = 0; ncopy = 0; k = 0
    while k < 4:
        ev = min(x for x in (nc, next_roll, fx) if x is not None)
        s = jump(s, ev - t)                     # frames t..ev-1: one rand_int(1) each
        t = ev
        if fx == t:
            s = jump(s, 8); fx = None           # tackle firework, script phase (before a roll/coin on the same frame)
        if next_roll == t:
            s = SM.adv(s); v = s // (M // 1001); k += 1
            if v < 600: ncopy += 1; next_roll = t + SM.COPY_NEXT
            else:
                fails += 1
                if fails >= 2: return 2
                fx = t + SM.TACKLE_FX; next_roll = t + SM.FAIL_NEXT
        if nc == t:
            s = SM.adv(s); v = s // (M // 1010) // 10; nc = t + (48 if v >= 70 else 24)
        # finish frame t: its rand_int(1)
        s = SM.adv(s); t += 1
    return ncopy


def menu_states(s1, nc, spinies, fw_draws, c_from, c_to):
    """(seed before frame c's draws, next coin frame relative to c) for c in c_from..c_to (relative to the first
    throw), by playing the Surge and the menus with surge_model's per-frame rules"""
    s = s1; L = spinies[-1]; sp = set(spinies); fw = {L + a: fw_draws for a in SM.FW_AT}; out = []
    for t in range(c_to + 1):
        if t >= c_from: out.append((s, nc - t))
        if t in sp:
            for mx in SM.SPINY: s, v = SM.rand_int(s, mx)
        if t in fw:
            for i in range(fw[t]): s, v = SM.rand_int(s, 359)
        if t == nc:
            s, v = SM.rand_int(s, 100); nc = t + (48 if v >= 70 else 24)
        s, v = SM.rand_int(s, 1)
    return out


def check_fast(n=300, rnd=random.Random(1)):
    bad = 0
    for i in range(n):
        s1 = rnd.getrandbits(32); nc = rnd.randrange(48); sp = list(range(0, 54, rnd.choice((2, 3, 4, 6))))
        L = sp[-1]; c = L + SM.MENU_AT + rnd.randrange(20, 120)
        ref_rolls = SM.simulate(s1, nc, sp, c, 8, need=0)
        ref_c = max(SM.copies(ref_rolls), 2)
        (s, ncr), = menu_states(s1, nc, sp, 8, c, c)
        got = after_confirm(s, ncr)
        if got != ref_c: bad += 1
    return bad


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    READY = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    SPAN = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    print('fast model vs surge_model.simulate, mismatches on 3+/4 outcomes:', check_fast(), flush=True)
    rnd = random.Random(7)
    sp = list(range(0, 56, 2))                 # 28 throws (1/1 mash); the throw count only shifts the RNG
    L = sp[-1]; M0 = L + SM.MENU_AT            # Mario's menu
    H = SPAN + 200                             # look further for the waits
    per4 = [0] * (SPAN + 1); per3 = [0] * (SPAN + 1); aim = [0] * (SPAN + 1)
    w4, w3, waim = [], [], []; run4 = []
    for i in range(N):
        s1 = rnd.getrandbits(32); nc = rnd.randrange(48 if rnd.random() < 0.3 else 24)
        st = menu_states(s1, nc, sp, 8, M0 + READY - 1, M0 + READY + H + 1)
        out = [after_confirm(s, n) for s, n in st]          # index 0 = READY-1
        o = out[1:]                                                 # o[k] = confirm at READY + k
        for k in range(SPAN + 1):
            per4[k] += o[k] == 4; per3[k] += o[k] >= 3
            aim[k] += o[k] == 4 and out[k] >= 3 and out[k + 2] >= 3
        f4 = next((k for k in range(H + 1) if o[k] == 4), None)
        f3 = next((k for k in range(H + 1) if o[k] >= 3), None)
        fa = next((k for k in range(H) if o[k] == 4 and out[k] >= 3 and out[k + 2] >= 3), None)
        w4.append(f4); w3.append(f3); waim.append(fa)
        r = 0
        for k in range(H + 1):
            if o[k] == 4: r += 1
            elif r: run4.append(r); r = 0

    def summ(w, name):
        ws = sorted(x if x is not None else 10 ** 6 for x in w)
        mean = sum(min(x, H) for x in ws) / len(ws)
        q = lambda p: ws[int(p * (len(ws) - 1))]
        frac = lambda lim: sum(1 for x in ws if x > lim) / len(ws)
        return {'what': name, 'mean_frames': round(mean, 2), 'median': q(.5), 'p90': q(.9), 'p99': q(.99),
                'P(none by +15 frames = 0.5 s)': round(frac(14), 4), 'P(none by +30 = 1 s)': round(frac(29), 4),
                'P(none by +60 = 2 s)': round(frac(59), 4)}
    res = {
        'samples': N, 'ready_after_menu': READY, 'span': SPAN,
        'P(all 4) per frame': round(sum(per4) / N / (SPAN + 1), 4),
        'P(3+) per frame': round(sum(per3) / N / (SPAN + 1), 4),
        'P(aim4: all 4 with both neighbours 3+) per frame': round(sum(aim) / N / (SPAN + 1), 4),
        'runs of all-4 frames (length: share)': {k: round(run4.count(k) / len(run4), 3) for k in sorted(set(run4))},
        'wait_first_4': summ(w4, 'first all-4 frame'),
        'wait_first_3plus': summ(w3, 'first 3+ frame'),
        'wait_first_aim4': summ(waim, 'first all-4 frame with both neighbours 3+'),
    }
    print(json.dumps(res, indent=1))
