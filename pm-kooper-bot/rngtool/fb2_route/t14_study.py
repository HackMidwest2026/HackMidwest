"""T1-T5 of the FB2 route: what draws happen between the inputs, and do they depend on anything but the seed and the
confirm frames?  From BUILD/tN_menu.st (route_build.py); for each seed (DIAGNOSTIC: gRandSeed written at the turn's
menu, setup only) Mario's action (confirm delay 0, no other input), partner action (delay 0) when Lakilester is up, then
Bowser's turn with NO input (policy none) or A every 25 frames outside menus (a25), to the next Mario menu.
Prints per phase: frames, LCG steps, and draws by caller (rays/aura/coin/bolt folded) plus Bowser's evt draws, the
dodge / Close Call rolls (802774B0 / 80277518), and the result (Mario HP after; partner KO).
Run from bot1 with M64P_DBG=1:  PYTHONPATH=. python3 t14_study.py BUILD TURN SEEDS [none|a25]"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from route_build import TURNS

FOLD = {'aura': 'aura', 'coin': 'coin', 'bolt': 'bolt'}


def fold(nm):
    if nm.startswith('e00d6'): return 'energy_in_out'
    return nm


def play(r, build, t, seed, pol):
    ma, mv, pa = TURNS[t - 1]
    r.load(build + '/t%d_menu.st' % t); r.seed(seed)                # DIAGNOSTIC: gRandSeed at the menu
    ko = r.partner_ko()[0] != 0
    getattr(r, ma)(0, **mv); m0 = r.marks[list(r.marks)[-1]]
    ph = {}
    if not ko and pa:
        r.wait_state((14,), adv_text=(pol == 'a25')); p_menu = r.f; r.idle(20)
        getattr(r, pa)(0); p0 = r.marks[list(r.marks)[-1]]
        ph['mario'] = (m0, p_menu)
    else:
        p0 = None
    r.wait_state((13,), cap=5000, adv_text=(pol == 'a25')); end = r.f
    if p0 is not None: ph['partner+bowser'] = (p0, end)
    else: ph['mario+bowser'] = (m0, end)
    out = dict(seed='%08x' % seed, turn=t, hp=r.e.s8(PLAYER_DATA + 2), ko=r.partner_ko(), reached=bstate(r.e) == 13)
    for k, (a, b) in ph.items():
        c = collections.Counter('%s/%d' % (fold(nm), mx) for f, nm, mx in r.cnt(a, b))
        out[k] = dict(frames=b - a, steps=r.steps(a, b), draws=dict(sorted(c.items())),
                      key=[(f - a, nm, mx) for f, nm, mx in r.cnt(a, b) if nm in ('evt', 'testtgt') or nm.startswith('8027')])
    return out


if __name__ == '__main__':
    build, t = sys.argv[1], int(sys.argv[2]); seeds = [int(x, 16) for x in sys.argv[3].split(',')]
    pol = sys.argv[4] if len(sys.argv) > 4 else 'none'
    r = Run('t14')
    for sd in seeds:
        print(json.dumps(play(r, build, t, sd, pol)), flush=True)
