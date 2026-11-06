"""Per-frame draw logs of one FB2 phase-2 turn T1..T5 (JP, emulator, debug core), for the T1-T4 page model (t14model.py).
From BUILD/tN_menu.st (route_build.py). DIAGNOSTIC: gRandSeed written at the turn's menu (setup only).
Per run: PRE idle frames in Mario's menu, Mario's action (route_build.TURNS menu moves) with confirm delay C; frame 0 =
Mario's confirm. Charge turns: the "+3" popup A on confirm+K (K < 0: no press). Then, with Lakilester up, the partner
menu: 20 frames after it opens, the partner action's inputs with W more idle frames before its confirm (Cloud Nine on
T1 with the three-chances A presses on confirm+132/152/172), Bowser's turn with no input to the next Mario menu (+60
frames). Every rand_int: (caller, max) in call order, per frame; the battle state; Mario's HP; Lakilester's KO.
SHOTS=DIR (with M64P_GFX on a DISPLAY): a glide64 screenshot after every step, DIR/s%04d.png = row i of the log (it
shows frame i - 1, readouts/charge_prep.py); SHOTS_TO: only rows 0..SHOTS_TO.
Run from /tmp/claude-0/pm/bot1: M64P_DBG=1 PYTHONPATH=. python3 t14_log.py BUILD TURN SEEDHEX PRE C K W OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from route_build import TURNS

if __name__ == '__main__':
    build, t, seed, PRE, C, K, W, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3], 16), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), sys.argv[8]
    ma, mv, pa = TURNS[t - 1]
    r = Run('t14l')
    SH = os.environ.get('SHOTS'); MAXF = int(os.environ.get('SHOTS_TO', '100000'))
    if SH:                      # glide64 screenshots: SHOTS/s%04d.png after each step (row index from the run's start)
        import subprocess
        os.makedirs(SH, exist_ok=True); _st = r.step
        def step(b=0, y=0):
            _st(b, y)
            if len(r.rows) - 1 - start0[0] <= MAXF:
                subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/s%04d.png' % (SH, len(r.rows) - 1 - start0[0])], check=True)
        r.step = step
    start0 = [0]
    r.load(build + '/t%d_menu.st' % t); r.seed(seed)               # DIAGNOSTIC: gRandSeed at the menu (setup only)
    ko = r.partner_ko()[0] != 0
    start = r.f; start0[0] = start; r.idle(PRE)
    getattr(r, ma)(C, **mv); c0 = r.marks[list(r.marks)[-1]]
    # the confirm was row c0 (its input on that step): frame 0 = that step
    marks = dict(confirm=0)
    n = 0
    while bstate(r.e) != 14 and n < 600 and not ko:
        k = r.f - c0; r.step(A if (K >= 0 and k == K) else 0); n += 1
    if not ko and pa:
        marks['pmenu'] = r.f - c0; r.idle(20)
        if pa == 'cloud_nine':
            r.seq([(A, 0, 20), (0, DOWN, 10), (0, DOWN, 10), (A, 0, 15), (A, 0, 1)], W, 'cn'); p0 = r.marks['cn']
            for i in range(259):
                k = r.f - p0 - 1; r.step(A if k in (132, 152, 172) else 0)   # as route.cloud_nine (route_build's states)
        else:
            r.seq([(0, UP, 10), (A, 0, 20), (0, DOWN, 10), (A, 0, 1)], W, 'nothing'); p0 = r.marks['nothing']
        marks['pconfirm'] = p0 - c0
    else:
        while r.f - c0 < 140: k = r.f - c0; r.step(A if (K >= 0 and k == K) else 0)
    n = 0
    while bstate(r.e) != 13 and n < 4000: r.step(); n += 1
    marks['next_menu'] = r.f - c0
    for i in range(60): r.step()
    rows = [dict(f=x['f'] - c0, s0='%08x' % x['s0'], b=x['b'], bs=x['bs'], d=x['d']) for x in r.rows[start:]]
    res = dict(turn=t, seed='%08x' % seed, PRE=PRE, C=C, K=K, W=W, marks=marks, hp=r.e.s8(PLAYER_DATA + 2), ko=r.partner_ko(),
               fp=r.e.s8(PLAYER_DATA + 5), charges=r.e.s8(BSTATUS + 0x97), cloud9=r.e.s8(BSTATUS + 0xA4), first=rows[0]['f'], rows=rows)
    json.dump(res, open(out, 'w'))
    print(json.dumps({k: v for k, v in res.items() if k != 'rows'}))
