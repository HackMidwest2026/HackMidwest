"""Brute-force the early-Laki entry from a pre-load state (make_state_skew.py PRE_SAVE): for each (T, Y), force
gGameStatus.exitTangent = T and Mario's y = Y through the flo_08 load (UseEntryHeading sets only x/z, so y carries over
from where Mario landed in flo_00), then classify Laki: settle 150 frames, walk right 40, stand 30, left 25, stand 30,
right 25, stand 60. Prints one line per variant: Laki displacement per phase, height above Mario, state, ptr/idx.
usage: skew_variant.py PRE.st OUT.jsonl T1,T2,... Y1,Y2,..."""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE, PTR, IDX = 0x8010D188, 0x8010D17C, 0x8010D178
pre, out = sys.argv[1], sys.argv[2]
Ts = [float(v) for v in sys.argv[3].split(',')]; Ys = [float(v) for v in sys.argv[4].split(',')]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/sv%d' % os.getpid())
fo = open(out, 'a')
L = lambda: ([q for q in npcs(e) if q['id'] == -4] or [None])[0]
for T in Ts:
    for Y in Ys:
        e.load(pre)
        ok = False
        for i in range(400):
            e.wf32(e.u32(GAME_STATUS_PTR) + 0x94, T)
            if where(e)[0] != 19: e.wf32(PLAYER + PS_POS + 4, Y)
            e.step(0, 0, 0, 2)
            if where(e)[0] == 19 and e.s16(GAME_MODE) == GM_WORLD: ok = True; break
        if not ok: continue
        # keep y for the first frames of the new map too (until UseEntryHeading has run)
        for i in range(2): e.wf32(PLAYER + PS_POS + 4, Y); e.step(0, 0, 0, 2)
        for i in range(150): e.step(0, 0, 0, 2)
        ph = []; track = []
        for d, n in ((0, 40), (None, 30), (180, 25), (None, 30), (0, 25), (None, 60)):
            p0, l0 = player(e), L()
            if l0 is None: break
            for i in range(n):
                e.step(0, *(stick_for(d, 80) if d is not None else (0, 0)), 2)
                p, l = player(e), L()
                if l: track.append((round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(l['x'], 1), round(l['y'], 1), round(l['z'], 1), e.u32(STATE) >> 16))
            p1, l1 = player(e), L()
            if l1 is None: break
            ph.append({'d': d, 'mdx': p1['x'] - p0['x'], 'ldx': l1['x'] - l0['x'], 'ldz': l1['z'] - l0['z'], 'ldy': l1['y'] - l0['y']})
        p, l = player(e), L()
        if l is None or len(ph) < 6: continue
        rec = {'T': T, 'Y': Y, 'phases': ph, 'h': l['y'] - p['y'], 'st': e.u32(STATE) >> 16, 'ptr': e.u32(PTR), 'idx': e.u32(IDX),
               'mario': [p['x'], p['y'], p['z']], 'laki': [l['x'], l['y'], l['z']], 'map': where(e), 'track': track[::5]}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
        print('T %6.0f Y %5.0f | %s | h %+6.1f st %d ptr %d idx %d map %s' % (T, Y, ' '.join('%s%+.0f/%+.0f' % ({0: 'R', 180: 'L', None: 'S'}[q['d']], q['mdx'], q['ldx']) for q in ph), rec['h'], rec['st'], rec['ptr'], rec['idx'], rec['map']))
