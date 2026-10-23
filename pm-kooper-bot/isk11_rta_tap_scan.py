"""RTA-style tap push scan (inputs only). From BASE, repeat one rhythm: hold right at tilt MAG for H frames, release
for W frames, for up to C cycles. Tracks when the history fills (target frozen) and how far right Laki gets while he
stays idle with that target. usage: isk11_rta_tap_scan.py BASE OUT.jsonl  env MAGS HS WS C ANG (deg up from right)"""
import json, math, os, sys
from emu import *
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
MAGS = [int(v) for v in os.environ.get('MAGS', '20,40,80').split(',')]
HS = [int(v) for v in os.environ.get('HS', '1,2').split(',')]; WS = [int(v) for v in os.environ.get('WS', '2,3,4,6,8').split(',')]
C = int(os.environ.get('C', '400')); ANG = float(os.environ.get('ANG', '0'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rts%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(sys.argv[2], 'a')
for m in MAGS:
    for h in HS:
        for w in WS:
            e.load(sys.argv[1]); sx, sy = int(round(m * math.cos(math.radians(ANG)))), int(round(m * math.sin(math.radians(ANG))))
            frozen = None; best = None; broke = None; f = 0
            for c in range(C):
                for i in range(h + w):
                    e.step(0, sx if i < h else 0, sy if i < h else 0, 2); f += 1
                    st = e.u32(STATE) >> 16; ptr, idx = e.u32(PTR), e.u32(IDX)
                    if frozen is None and idx == (ptr - 1) % 40 and st == 5: frozen = (ptr, round(e.f32(HIST + 16 * ptr + 4), 1), round(e.f32(HIST + 16 * ptr + 12), 1), f)
                    if frozen and (st != 5 or ptr != frozen[0]): broke = f; break
                if broke: break
                if frozen:
                    p, l = player(e), lk(); best = (round(l['x'], 1), round(l['z'], 1), round(p['x'], 1), round(p['z'], 1), c)
            r = {'mag': m, 'h': h, 'w': w, 'ang': ANG, 'frozen': frozen, 'best': best, 'broke': broke}
            fo.write(json.dumps(r) + '\n'); fo.flush()
