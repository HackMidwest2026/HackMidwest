"""Final Bowser phase 2 aura (energy_in_out type 4, Bowser's ACTOR_DECORATION_RADIAL_STAR_EMITTER): find the effect in RAM,
log every rand_int per frame, and check a frame-by-frame model of the aura's draws against RAM.

Run from the emulator dir (/tmp/claude-0/pm/bot1), debug core:
  M64P_DBG=1 PYTHONPATH=. python3 /path/aura_probe.py STATE N SEED [inputs "f:btn,..."] [--json OUT]
DIAGNOSTIC RAM write: gRandSeed (both copies) is overwritten right after the state load (setup only), unless SEED is '-'.

Model checked (per frame, given the effect's 16 parts: counter unk_14, period unk_10 = 20):
  each part: unk_14 += 1; if unk_14 >= 20: unk_14 = 0, unk_3C = rand_int(359); then unk_3C += unk_40 (-2).
  Parts update in index order 1..16. The frame's draws are replayed from the frame's start seed in logged call order;
  the aura's draws must give exactly the unk_3C values RAM shows after the frame (value - 2)."""
import sys, os, json, struct
sys.path.insert(0, os.getcwd())
import numpy as np
from emu import *
from rngsim import *
AURA_RA = 0xE00D6838
NAMES = {0x800269AC: 'step', 0x80146D54: 'coin', 0xE00BC194: 'bolt', AURA_RA: 'aura', 0x802A1168: 'pbroll', 0xE00861EC: 'stars'}


def find_aura(e):
    """address of the first part (EnergyInOutFXData) of an energy_in_out type-4 instance: unk_00 = 4, colours
    255/255/255, env 255/245/0, unk_38 = 10.0 (D_E00D6E84[4])"""
    w = np.ctypeslib.as_array(e.ram)
    cand = np.nonzero(w == 4)[0]
    out = []
    for i in cand:
        if i + 18 >= len(w): continue
        if (w[i + 6], w[i + 7], w[i + 8], w[i + 10], w[i + 11], w[i + 12], w[i + 14]) == (255, 255, 255, 255, 245, 0, 0x41200000):
            out.append(0x80000000 + 4 * i)
    return out


def f32(e, a): return struct.unpack('<f', struct.pack('<I', e.u32(a)))[0]


def parts(e, base, n=17):
    P = []
    for k in range(1, n):
        a = base + 0x48 * k
        P.append(dict(t=e.s32(a + 0x14), per=e.s32(a + 0x10), v=f32(e, a + 0x38), ang=f32(e, a + 0x3C), rot=f32(e, a + 0x40),
                      x=f32(e, a + 0x04), sc=f32(e, a + 0x34), a24=e.s32(a + 0x24)))
    head = dict(per=e.s32(base + 0x10), t=e.s32(base + 0x14), a24=e.s32(base + 0x24), pos=(f32(e, base + 4), f32(e, base + 8), f32(e, base + 12)),
                scale=f32(e, base + 0x34), s44=f32(e, base + 0x44))
    return head, P


if __name__ == '__main__':
    st, N, SD = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    inp = {}
    if len(sys.argv) > 4 and sys.argv[4] and not sys.argv[4].startswith('--'):
        for tok in sys.argv[4].split(','):
            f, b = tok.split(':'); inp[int(f)] = eval(b)
    jout = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/ap%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    e.load('states/' + st if not st.startswith('/') else st); e.step(0, 0, 0, 2)
    if SD != '-':
        sd = int(SD, 16); e.w32(SEED, sd); e.w32(SEED2, sd)          # DIAGNOSTIC: seed write (setup only)
    e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
    bases = find_aura(e)
    print('aura instances at', [hex(b) for b in bases])
    base = bases[0] if bases else None
    ok = bad = 0; rows = []; order_seen = {}
    for f in range(N):
        s0 = e.u32(SEED)
        prev = parts(e, base)[1] if base else None
        e.step(inp.get(f, 0), 0, 0, 2)
        ev = e.dbg_events()
        s = s0; seq = []; aura_vals = []
        for x in ev:
            s, v = rand_int(s, x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32))
            nm = NAMES.get(x['ra'], hex(x['ra'])); seq.append((nm, x['a0'], v))
            if x['ra'] == AURA_RA: aura_vals.append(v)
        if s != e.u32(SEED): print('frame %d: replay seed mismatch' % f)
        key = tuple(n for n, _, _ in seq if n != 'aura' or True)
        compact = []
        for n, _, _ in seq:
            if not compact or compact[-1][0] != n: compact.append([n, 1])
            else: compact[-1][1] += 1
        order_seen[tuple(n for n, c in compact)] = order_seen.get(tuple(n for n, c in compact), 0) + 1
        if base:
            cur = parts(e, base)[1]
            # model: which parts wrap this frame, in index order
            pred = []
            for k, p in enumerate(prev):
                if p['t'] + 1 >= p['per']: pred.append(k)
            got = []
            for k in pred:
                got.append(int(round(cur[k]['ang'] - cur[k]['rot'])))
            if got == aura_vals: ok += 1
            else:
                bad += 1
                if bad < 10: print('frame %d mismatch: predicted parts %s, RAM angles %s, draws %s' % (f, pred, got, aura_vals))
        rows.append(dict(f=f, s0=s0, seq=seq))
    print('frames', N, 'aura model match', ok, 'mismatch', bad)
    print('same-frame call orders seen:')
    for k, c in sorted(order_seen.items(), key=lambda t: -t[1]): print('  %4d  %s' % (c, ' > '.join(k)))
    if base:
        h, P = parts(e, base)
        print('head', h)
        print('parts: t/per/v/scale', [(p['t'], p['per'], round(p['v'], 2), round(p['sc'], 2)) for p in P])
    if jout: json.dump(dict(state=st, seed=SD, rows=rows), open(jout, 'w'))
