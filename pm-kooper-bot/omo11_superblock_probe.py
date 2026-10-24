"""omo_11 Super Block with Goompa as the only partner. Setup: Mario teleported (RAM) onto platform 22 under the block
(labeled setup; the route there is not part of this probe). Optional pre-actions (env PRE, ';'-separated:
'wait:N', 'walk:yaw:N', 'jump', 'spin', 'hammer', 'pause', 'cright', 'cleft') before standing under the block and
jumping into it. Advances the text with A until the partner popup exists, then dumps the uninitialized PopupMenu
fields the menu will use. usage: omo11_superblock_probe.py [SAVE.st]"""
import os, sys, struct
from emu import *
from pm import *
from nav import stick_world, go_to
POPUP_PTR = 0x8010D85C
BX, BZ = -115.0, -120.0
e = Emu('pm-jp.z64', '/dev/shm/pmbot/osb%d' % os.getpid())
def popup():
    p = e.u32(POPUP_PTR)
    if p < 0x80000000 or p > 0x80800000: return None
    if e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0: return p
    return None
def setup():
    if os.environ.get('START'):                                   # real state reached by inputs (omo11_route2/3.py)
        e.load(os.environ['START']); e.step(0, 0, 0, 2); return
    e.load('states/omo11_e0_goompa.st'); e.step(0, 0, 0, 2)
    for a in (PLAYER + PS_POS, ): pass
    e.wf32(PLAYER + PS_POS, BX); e.wf32(PLAYER + PS_POS + 4, 212); e.wf32(PLAYER + PS_POS + 8, -110)
    for i in range(40): e.step(0, 0, 0, 2)
    if os.environ.get('ITEMS'):                                   # inventory setup (RAM): 'slot=id,...'
        for i in range(10): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, 0)
        for kv in os.environ['ITEMS'].split(','):
            k, v = kv.split('='); e.w16(PLAYER_DATA + 0x1B4 + 2 * int(k), int(v, 0))
def pre(actions):
    for a in filter(None, actions.split(';')):
        k = a.split(':')
        if k[0] == 'wait':
            for i in range(int(k[1])): e.step(0, 0, 0, 2)
        elif k[0] == 'walk':
            for i in range(int(k[2])): e.step(0, *stick_world(e, float(k[1])), 2)
        elif k[0] == 'run':
            for i in range(int(k[2])): e.step(0, *stick_world(e, float(k[1]), 80), 2)
        elif k[0] == 'hammerq':
            for i in range(2): e.step(B, 0, 0, 2)
            for i in range(int(k[1])): e.step(0, 0, 0, 2)
        elif k[0] == 'jumpq':
            for i in range(int(k[1])): e.step(A, 0, 0, 2)
            for i in range(25): e.step(0, 0, 0, 2)
        elif k[0] == 'spinjump':
            e.step(Z, 0, 0, 2)
            for i in range(int(k[1])): e.step(0, 0, 0, 2)
            for i in range(4): e.step(A, 0, 0, 2)
            for i in range(30): e.step(0, 0, 0, 2)
        elif k[0] in ('jump', 'spin', 'hammer'):
            b = {'jump': A, 'spin': Z, 'hammer': B}[k[0]]
            for i in range(3): e.step(b, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
        elif k[0] in ('pause', 'cright', 'cleft', 'cup'):
            b = {'pause': START, 'cright': R_CBUTTON, 'cleft': L_CBUTTON, 'cup': U_CBUTTON}[k[0]]
            e.step(b, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
            e.step(B if k[0] != 'pause' else START, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
def hit():
    go_to(e, BX, -112, maxf=120, tol=1.5)
    for i in range(10): e.step(0, 0, 0, 2)
    for i in range(6): e.step(A, 0, 0, 2)
    for f in range(900):
        p = popup()
        if p: return p, f
        e.step(A if f % 8 == 0 else 0, 0, 0, 2)
    return None, None
def dump(p):
    w = lambda o: e.u32(p + o)
    return {'addr': hex(p), 'userIndex[0] (+0x108)': w(0x108), 'enabled[0] (+0x18C)': w(0x18C), 'enabled[-1] (+0x188)': w(0x188),
            'userIndex[-1] (+0x104)': w(0x104), 'nameMsg[0]': hex(w(0x84)), 'descMsg[0]': hex(w(0x294)), 'ptrIcon[0]': hex(w(0)), 'value[0]': w(0x210)}
if __name__ == '__main__':
    setup(); print('Mario', player(e))
    pre(os.environ.get('PRE', ''))
    p, f = hit()
    if not p: print('no popup', player(e)); sys.exit()
    print('popup after', f, 'frames'); print(dump(p))
    if len(sys.argv) > 1: e.save(sys.argv[1])
