"""APG: vary only HOW Mario arrives back under the omo_11 Super Block (inputs only), then wait W and jump.
Modes: run (full stick, walking dust), walk (slow stick, no dust), spin (Z toward the spot; overshoots the
platform), spinaway (spin away along x holding the stick D steps, walk back slowly), jump (jump toward the spot,
landing dust), still (never moves). Logs the menu fields, the sparkle alignment, and the last heap block seen
covering the enabled word of the sparkle-aligned spot (0x80318FCC) before the menu existed.
usage: omo11_apg_arrive.py MODE DIR D0 D1 W0 W1 WSTEP OUT.jsonl   (env START: state under the block)"""
import json, os, sys
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
from omo11_heapwalk import walk
from omo11_find_sparkle import sparkle
from nav import go_to, stick_world, world_yaw_to
from emu import A, Z
e = P.e
mode, d = sys.argv[1], int(sys.argv[2])
d0, d1, w0, w1, ws = map(int, sys.argv[3:8]); out = sys.argv[8]
EN = 0x80318FCC
TX, TZ = -115, -112
fo = open(out, 'a')
def dist():
    p = P.player(e); return ((p['x'] - TX) ** 2 + (p['z'] - TZ) ** 2) ** 0.5
def steer(mag, buttons=0):
    p = P.player(e); e.step(buttons, *stick_world(e, world_yaw_to(p, TX, TZ), mag), 2)
def settle(mag=20, maxf=200):
    for i in range(maxf):
        if dist() < 1.5: break
        steer(mag)
    for i in range(4): e.step(0, 0, 0, 2)
def arrive():
    if mode == 'run': go_to(e, TX, TZ, maxf=120, tol=1.5)
    elif mode == 'walk': settle(25, 300)
    elif mode == 'spin':
        steer(80, Z); steer(80, Z)
        for i in range(30):
            if dist() < 4: break
            steer(80)
        settle(20)
    elif mode == 'spinaway':                     # D = steps the stick is held during the spin (away along x)
        pass
    elif mode == 'jump':
        for i in range(6): steer(80, A)
        for i in range(40):
            if P.player(e)['action'] in (0, 1, 2) and i > 3: break
            steer(60 if dist() > 6 else 0)
        settle(20)
SP, ENB = {}, {}
def track():
    for inst, data in sparkle(e):
        SP.update(data=data, c4=e.u32(data + 0xB0 + 0x28))
    for n, bk, ln, al, mid in walk(e):
        if bk <= EN < bk + ln:
            ENB.update(blk=hex(bk), len=hex(ln), al=al, id=mid, v=e.u32(EN)); break
for D in range(d0, d1):
    for W in range(w0, w1, ws):
        P.setup(); SP.clear(); ENB.clear()
        if mode == 'spinaway':
            p = P.player(e); st = stick_world(e, world_yaw_to(p, TX + d * 200, TZ))
            e.step(Z, *st, 2)
            for i in range(D): e.step(0, *st, 2)
            for i in range(25): e.step(0, 0, 0, 2)
            settle(25, 300)
        elif mode != 'still':
            for i in range(D):
                p = P.player(e); e.step(0, *stick_world(e, world_yaw_to(p, TX + d * 200, TZ)), 2)
            arrive()
        for i in range(W): track(); e.step(0, 0, 0, 2)
        for i in range(6): track(); e.step(A, 0, 0, 2)
        p = None
        for f in range(900):
            p = P.popup()
            if p: break
            track(); e.step(A if f % 8 == 0 else 0, 0, 0, 2)
        r = {'mode': mode, 'dir': d, 'D': D, 'W': W, 'ok': bool(p), 'y': P.player(e)['y']}
        if p:
            dm = P.dump(p)
            r.update(addr=hex(p), id=dm['userIndex[0] (+0x108)'], en=dm['enabled[0] (+0x18C)'],
                     sparkle=hex(SP['data']) if SP else None, c4=SP.get('c4'), en_block=dict(ENB))
        fo.write(json.dumps(r) + '\n'); fo.flush()
