"""T5 (Peach Beam) -> T6 Charge: how many gRandSeed steps lie between the Peach Beam confirm and the T6 Super Charge's
rays frame 0 (confirm + 13), against the frames between them (JP, emulator). The page's T6 lock searches only the
seeds this many steps after the one it carried to the Peach Beam confirm (fb14_live.js), so this sets its window.
From BUILD/t5_menu.st (route_build.py). DIAGNOSTIC: gRandSeed written at the T5 menu (setup only).
Per run: PRE idle frames, Peach Beam (route_build's menu moves) with confirm delay 0; then the text policy: 'none' (no
input until the T6 menu), or 'aN' (A every N frames outside menus: the remark text advanced); then Q idle frames in
the T6 menu, the T6 Charge inputs (t6_render.py's), and 13 more frames.
Run from /tmp/claude-0/pm/bot1: PYTHONPATH=. python3 t5_steps.py BUILD SEEDS PRE Q POLICY  -> one JSON line per seed"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *

if __name__ == '__main__':
    build, seeds, PRE, Q, pol = sys.argv[1], [int(x, 16) for x in sys.argv[2].split(',')], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    r = Run('t5s', log=False)
    for sd in seeds:
        r.load(build + '/t5_menu.st'); r.seed(sd)                 # DIAGNOSTIC: gRandSeed at the T5 menu (setup only)
        r.idle(PRE); r.peach_beam(0, wheel=2, sub=-1); pb = r.marks['peach']
        n = 0; N = int(pol[1:]) if pol.startswith('a') else 0
        while bstate(r.e) != 13 and n < 3000:
            r.step(A if (N and n % N == N - 1 and bstate(r.e) not in (13, 14, 17)) else 0); n += 1
        menu = r.f; hp = r.e.s8(PLAYER_DATA + 2)
        r.idle(Q)
        for b, y, k in r.moves(-2) + [(A, 0, 20)] + r.moves(2) + [(A, 0, 15), (A, 0, 1)]: r.step(b, y); r.idle(k - 1)
        c0 = r.f - 1
        while r.f < c0 + 14: r.step()
        f0 = c0 + 13
        print(json.dumps(dict(seed='%08x' % sd, PRE=PRE, Q=Q, pol=pol, hp=hp, pb_to_menu=menu - pb, frames=f0 - pb,
                              steps=r.steps(pb, f0), steps_to_menu=r.steps(pb, menu), menu_to_f0=f0 - menu)), flush=True)
