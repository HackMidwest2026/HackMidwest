"""RTA-style phased push (inputs only). A plan is a list of phases; each phase repeats one rhythm COUNT times:
hold raw stick at ANG (deg, 0 = right, 90 = up) with tilt MAG for H frames (A also held if JUMP), then neutral for W
frames. Logs Laki/Mario/target after every phase and stops when Laki leaves follow state 5 or his target moves.
run(plan, base) -> dict; also usable as a script: isk11_rta_phases.py BASE 'ang,mag,h,w,count[,jump];...' [OUT.st]"""
import json, math, os, sys
from emu import *
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
_e = None
def emu():
    global _e
    if _e is None: _e = Emu('pm-jp.z64', '/dev/shm/pmbot/rph%d' % os.getpid())
    return _e
def run(plan, base, save=None, every=None):
    e = emu(); e.load(base); lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
    frozen = None; log = []; f = 0; ok = True
    for pi, ph in enumerate(plan):
        ang, mag, h, w, cnt = ph[:5]; jump = len(ph) > 5 and ph[5]
        sx, sy = int(round(mag * math.cos(math.radians(ang)))), int(round(mag * math.sin(math.radians(ang))))
        for c in range(cnt):
            for i in range(h + w):
                e.step((A if jump else 0) if i < h else 0, sx if i < h else 0, sy if i < h else 0, 2); f += 1
                st = e.u32(STATE) >> 16; ptr, idx = e.u32(PTR), e.u32(IDX)
                if frozen is None and idx == (ptr - 1) % 40 and st == 5: frozen = (ptr, round(e.f32(HIST + 16 * ptr + 4), 1), round(e.f32(HIST + 16 * ptr + 12), 1))
                if frozen and (st != 5 or ptr != frozen[0]): ok = False; break
                if every and f % every == 0: every_cb(e, f)
            if not ok: break
        p, l = player(e), lk()
        log.append({'phase': pi, 'f': f, 'M': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], 'L': [round(l['x'], 1), round(l['y'], 1), round(l['z'], 1)], 'ok': ok})
        if not ok: break
    if save and ok: e.save(save)
    return {'plan': plan, 'frozen': frozen, 'ok': ok, 'log': log}
every_cb = lambda e, f: None
if __name__ == '__main__':
    plan = [[float(v) if i < 2 else int(v) for i, v in enumerate(p.split(','))] for p in sys.argv[2].split(';')]
    r = run(plan, sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else None)
    print('frozen', r['frozen'], 'ok', r['ok'])
    for g in r['log']: print(g)
