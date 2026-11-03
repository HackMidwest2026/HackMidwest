"""Render the FB2 T6 Super Charge (glide64) with every gRandSeed draw logged per frame, for the page's FB2 Charge
profile (camera table, Mario's reference patch, the nuisance order) and the end-to-end check (capture simulation).
From BUILD/t6_menu.st (route_build.py). DIAGNOSTIC: gRandSeed written at the T6 menu (setup only).
Per run: PRE idle frames in the T6 menu, the Charge menu inputs with confirm delay C (frame 0 = the confirm), popup A
on confirm+K (K < 0: no press, it closes by itself), Bowser's turn to the T7 menu; then, with D >= 0, 20 idle frames,
the Power Bounce menu inputs with the target-screen A after D more idle frames and the bounce presses (A one frame
before each landing), until the bounces end. Frames are numbered from the confirm (f < 0 before it).
OUT/s%04d.png = the screenshot taken after emulator step i (i = 0 is the first step of the run; log.json 'shot0' is
the step index of the confirm), so it shows the state of frame i - 1 (readouts/charge_prep.py).
log.json: per frame f the seed before it, the draws in call order (caller name, max), the battle state, gCameras[1]
(perspective matrix + viewport) for f <= 70, the energy_in_out(6) effects (part 0 position) on the Charge frames;
Bowser's AI draws, the target-test frames, Mario's HP, the T7 menu frame, the Power Bounce confirm and Bowser's HP.
Run from /tmp/claude-0/pm/bot1:
  DISPLAY=:88 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus \\
  M64P_DBG=1 PYTHONPATH=. python3 t6_render.py BUILD SEEDHEX C K D OUT [PRE=60] [SHOTS_TO=f]   (no shots without M64P_GFX)"""
import sys, os, json, struct, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *

GC = 0x800B1D60
def fl(e, a): return struct.unpack('<f', struct.pack('<I', e.u32(a)))[0]
def cam(e, i=1): return [fl(e, GC + 0x558 * i + 0xD4 + 4 * j) for j in range(16)] + [e.s16(GC + 0x558 * i + 0xA), e.s16(GC + 0x558 * i + 0xC), e.s16(GC + 0x558 * i + 0xE), e.s16(GC + 0x558 * i + 0x10)]
def eio_scan(e):
    """energy_in_out part-0 blocks (charge_probe.py signature: unk_00 = 6, colours 255/255/255, 255, 245)"""
    r = e.ram; out = []
    for i in range(0x100000 // 4, 0x800000 // 4):
        if r[i] == 6 and r[i + 6] == 255 and r[i + 7] == 255 and r[i + 8] == 255 and r[i + 10] == 255 and r[i + 11] == 245: out.append(0x80000000 + 4 * i)
    return out

if __name__ == '__main__':
    build, seed, C, K, D, OUT = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    PRE = int(sys.argv[7]) if len(sys.argv) > 7 else 60; SHOTS_TO = int(sys.argv[8]) if len(sys.argv) > 8 else 10 ** 9
    shots = bool(os.environ.get('M64P_GFX')); os.makedirs(OUT, exist_ok=True)
    r = Run('t6r')
    r.load(build + '/t6_menu.st'); r.seed(seed)                     # DIAGNOSTIC: gRandSeed at the T6 menu (setup only)
    n_shot = [0]
    def step(b=0, y=0):
        r.step(b, y)
        if shots and r.f - c0g[0] <= SHOTS_TO:
            subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/s%04d.png' % (OUT, n_shot[0])], check=True)
        n_shot[0] += 1
    c0g = [10 ** 9]
    # pre-roll in the menu, then the Charge menu sequence up to (not including) its confirm; the confirm is frame 0
    seq = [(0, 0)] * PRE
    for b, y, n in r.moves(-2) + [(A, 0, 20)] + r.moves(2) + [(A, 0, 15)]: seq += [(b, y)] + [(0, 0)] * (n - 1)
    seq += [(0, 0)] * C
    start = r.f
    for b, y in seq: step(b, y)
    c0 = r.f; c0g[0] = c0; shot0 = n_shot[0]
    out = dict(seed='%08x' % seed, C=C, K=K, D=D, PRE=PRE, shot0=shot0, first=start - c0)
    known = []; fx_rows = {}; cams = {}
    t7 = None
    for i in range(0, 1500):
        step(A if (i == 0 or i == K) else 0)
        x = r.rows[-1]
        if 10 <= i <= 62:
            if not known or any(nm.startswith('e00d6') for nm, mx in x['d']): known = eio_scan(r.e)
            fx_rows[i] = ['%08x:%.1f,%.1f,%.1f' % (a, fl(r.e, a + 4), fl(r.e, a + 8), fl(r.e, a + 12)) for a in known if r.e.s32(a) == 6]
        if i <= 70: cams[i] = cam(r.e)
        if i > 80 and x['bs'] == 13: t7 = i; break
    out['t7menu'] = t7; out['hp'] = r.e.s8(PLAYER_DATA + 2)
    if D >= 0 and t7 is not None:
        for i in range(20): step()
        items = r.moves(0) + [(A, 0, 20)] + r.moves(1) + [(A, 0, 15)]
        for b, y, n in items:
            step(b, y)
            for j in range(n - 1): step()
        for j in range(D): step()
        dc = r.f; step(A)
        for i in range(27 * 14 + 100):
            k = r.f - dc; step(A if k >= 44 and (k - 44) % 27 == 0 else 0)
        out['pb_confirm'] = dc - c0; out['bowser_hp'] = r.bowser_hp()
    rows = []
    for x in r.rows[start:]:
        f = x['f'] - c0
        rows.append(dict(f=f, s0='%08x' % x['s0'], d=x['d'], bs=x['bs'], cam=cams.get(f), fx=fx_rows.get(f)))
    out['frames'] = rows
    out['evt'] = [(row['f'], mx) for row in rows for nm, mx in row['d'] if nm == 'evt']
    out['testtgt'] = [row['f'] for row in rows for nm, mx in row['d'] if nm in ('testtgt', '80277518')]
    out['pbroll'] = [(row['f'], mx) for row in rows for nm, mx in row['d'] if nm == 'pbroll']
    json.dump(out, open(OUT + '/log.json', 'w'))
    print(json.dumps({k: v for k, v in out.items() if k != 'frames'}))
