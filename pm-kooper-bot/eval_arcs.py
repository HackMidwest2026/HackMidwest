"""Take a rev_aim_explore2 archive (arch.json) from a new rock-jump seed, and for every arc that ends with Lakilester
in the lower floor's top-right corner (x >= LX, z <= -200), replay: seed + arc, 1 neutral frame, 3 up, two jumps
holding right (12, 16), stop-and-go right along the top wall until Laki x >= 984, 30 frames. Reports which arcs keep
the stale target and saves the first good one as OUT (new top-right start) with its seq as OUT_seq.json.
usage: eval_arcs.py <arch.json> <seed.st> OUT [LX=690]"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
arch, seed, OUT = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
LX = float(sys.argv[4]) if len(sys.argv) > 4 else 690
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ea%d' % os.getpid())
def laki():
    return [n for n in npcs(e) if n['id'] == -4][0]
cands = sorted((a for k, a in arch.items() if k != 'seed' and a['lx'] >= LX and a['lz'] <= -200), key=lambda a: len(a['seq']))
print(len(cands), 'arcs end in the corner')
saved = False
for a in cands:
    e.load(seed); e.step(0, 0, 0, 2)
    ptr = e.u32(PTR); tgt = (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12))
    for g, th, sl in a['seq']:
        p, l = player(e), laki()
        sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(g): e.step(0, sx, sy, 2)
        for i in range(sl): e.step(0, 0, 0, 2)
    e.step(0, 0, 0, 2)
    rx, ry = stick_for(0, 80)
    for i in range(3): e.step(0, *stick_for(270, 80), 2)
    for H2 in (12, 16):
        for i in range(24):
            e.step(0x80 if i < 8 else 0, rx if i < H2 else 0, ry if i < H2 else 0, 2)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
        for i in range(3): e.step(0, 0, 0, 2)
    for c in range(150):
        e.step(0, rx, ry, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if laki()['x'] >= 984: break
    for i in range(30): e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    ok = e.u32(PTR) == ptr and (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)) == tgt and (e.u32(STATE) >> 16) == 5 and l['x'] >= float(os.environ.get('LMIN', 984))
    print('arc len %2d  L corner (%.0f, %.0f) -> M (%.1f, %.1f, %.1f) L (%.1f, %.1f) %s' % (len(a['seq']), a['lx'], a['lz'], p['x'], p['y'], p['z'], l['x'], l['z'], 'OK' if ok else '-'), flush=True)
    if ok and not saved:
        e.step(0, 0, 0, 2); e.save(OUT); json.dump(a['seq'], open(OUT[:-3] + '_seq.json', 'w')); saved = True; print('saved', OUT)
        if os.environ.get('FIRST'): break
