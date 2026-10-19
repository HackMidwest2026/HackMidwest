"""kpa_62 remount clip with a spin dash: dismount (B = frame 0) at the spot reached by riding Laki at RA for RK frames,
hold notch D1 and press Z (spin) on frame ZF, hold D1 until frame K, then hold D2 (or release, D2 = -1) and press
C-down on frame T. The spin roughly doubles Mario's distance from Laki when Laki's return (follow state 15) ends, so
Laki's remount speed stays in the clip range for more than one frame. Prints every program with >= 1 working T.
usage: kpa62_spin.py STATE PART NPARTS OUT.jsonl   env: RIDES (RA:RK;...), D1S, ZFS, D2S, KS, TS"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ev = lambda k, d: [int(v) for v in os.environ.get(k, d).split(',')]
RIDES = [tuple(int(v) for v in t.split(':')) for t in os.environ.get('RIDES', '-1:0').split(';')]
D1S, ZFS, D2S = ev('D1S', '90,45,135'), ev('ZFS', '15,16,17,18'), ev('D2S', '-1,0,45,90,135,315')
KS = ev('KS', ','.join(str(k) for k in range(18, 37)))
T0, T1 = ev('TS', '30,40')
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62s%d' % os.getpid())
tmp = '/dev/shm/pmbot/k62s%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.seed')
def stick(d): return (0, 0) if d < 0 else stick_for(d, 80)
def try_cdown(st):
    e.step(0x400, *st, 2)
    for f in range(30):
        e.step(0, *st, 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
jobs = [(r, d1, zf, d2, k) for r in RIDES for d1 in D1S for zf in ZFS for d2 in D2S for k in KS][PART::NP]
fo = open(out, 'a'); good = 0; cur = None
for (r, d1, zf, d2, k) in jobs:
    if r != cur:
        e.load(tmp + '.seed'); e.step(0x400, 0, 0, 2)
        for i in range(30): e.step(0, 0, 0, 2)
        for i in range(r[1]): e.step(0, *stick_for(r[0], 80), 2)
        for i in range(8): e.step(0, 0, 0, 2)
        e.step(0x40, 0, 0, 2); dis = player(e); e.save(tmp + '.dis'); cur = r
    e.load(tmp + '.dis'); win = []; at = {}
    for fr in range(1, T1 + 1):
        st = stick(d1) if fr <= k else stick(d2)
        if fr >= T0:
            p = player(e)
            if abs(p['y'] - 50) < 3 and -392 <= p['x'] <= -366:
                e.save(tmp + '.h')
                if try_cdown(st): win.append(fr); at[fr] = [round(p['x'], 2), round(p['z'], 2)]
                e.load(tmp + '.h')
        e.step(0x20 if fr == zf else 0, *st, 2)
    if win:
        good += 1
        rec = {'ride': r, 'dis': [dis['x'], dis['z']], 'D1': d1, 'ZF': zf, 'K': k, 'D2': d2, 'T': win, 'at': at}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
        if len(win) > 1: print(rec, flush=True)
print('done part', PART, len(jobs), 'programs', good, 'with hits')
