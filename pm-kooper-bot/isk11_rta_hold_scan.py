"""RTA-style held push scan (inputs only). From BASE (Mario at the start spot, Laki idle next to him), hold one raw
stick (angle from straight up toward right, magnitude) for N frames. The push must keep Laki idle (follow state 5)
and his target frozen once the history is full. Reports how far right Laki got while that held, and when it broke.
usage: isk11_rta_hold_scan.py BASE OUT.jsonl  env ANGS MAGS N"""
import json, math, os, sys
from emu import *
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
ANGS = [float(v) for v in os.environ.get('ANGS', '0,10,20,30,40,50,60').split(',')]
MAGS = [int(v) for v in os.environ.get('MAGS', '20,30,45,65,80').split(',')]
N = int(os.environ.get('N', '240'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rhs%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(sys.argv[2], 'a')
for a in ANGS:
    for m in MAGS:
        e.load(sys.argv[1]); sx, sy = int(round(m * math.sin(math.radians(a)))), int(round(m * math.cos(math.radians(a))))
        frozen = None; best = None; broke = None; trail = []
        for f in range(N):
            e.step(0, sx, sy, 2)
            p, l = player(e), lk(); st = e.u32(STATE) >> 16; ptr, idx = e.u32(PTR), e.u32(IDX)
            full = idx == (ptr - 1) % 40
            if f % 10 == 0: trail.append([f, round(p['x']), round(p['z']), round(l['x']), round(l['z']), st])
            if frozen is None and full and st == 5: frozen = (ptr, round(e.f32(HIST + 16 * ptr + 4), 1), round(e.f32(HIST + 16 * ptr + 12), 1), f)
            if frozen and (st != 5 or ptr != frozen[0]): broke = f; break
            if frozen: best = (round(l['x'], 1), round(l['z'], 1), round(p['x'], 1), round(p['z'], 1), f)
        r = {'ang': a, 'mag': m, 'stick': [sx, sy], 'frozen': frozen, 'best': best, 'broke': broke, 'trail': trail}
        fo.write(json.dumps(r) + '\n'); fo.flush()
        print(a, m, 'frozen', frozen, 'laki_end', best, 'broke', broke, flush=True)
