"""Render Final Bowser's phase-2 aura frame by frame (glide64) and project every star from RAM to the screen.
Run from the emulator dir (/tmp/claude-0/pm/bot1):
  DISPLAY=:88 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus \
  PYTHONPATH=. python3 aura_render.py STATE N SEED OUTDIR [inputs "f:btn,..."]
DIAGNOSTIC RAM write: gRandSeed after the load (setup only; '-' keeps the state's seed).
Writes OUTDIR/fNNNN.png (640x480 crop of the 2x glide64 window) and OUTDIR/stars.json: per frame the camera and,
per part (1..16), its counter t, angle unk_3C (deg), radius (pos.x + 10, local units), alpha (0..255 = master x part
alpha), size class, and the projected screen centre (320x240 viewport coordinates) computed like get_screen_coords."""
import sys, os, json, math, subprocess
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import *
from rngsim import *
from aura_probe import find_aura, parts, f32
CAMS, CAM_SIZE, CUR_CAM = 0x800B1D60, 0x558, 0x800773E0


def camera(e, cid=1):
    """battle camera = CAM_BATTLE (1); gCurrentCameraID reads 0 between frames"""
    c = CAMS + CAM_SIZE * cid
    M = [[f32(e, c + 0xD4 + 16 * r + 4 * k) for k in range(4)] for r in range(4)]
    return dict(id=cid, M=M, yaw=f32(e, c + 0x6C), vw=e.s16(c + 0x0A), vh=e.s16(c + 0x0C), vx=e.s16(c + 0x0E), vy=e.s16(c + 0x10))


def project(C, x, y, z):
    M = C['M']
    tx = x * M[0][0] + y * M[1][0] + z * M[2][0] + M[3][0]
    ty = x * M[0][1] + y * M[1][1] + z * M[2][1] + M[3][1]
    tw = x * M[0][3] + y * M[1][3] + z * M[2][3] + M[3][3]
    return (C['vw'] / 2 + tx / tw * C['vw'] * 0.5 + C['vx'], C['vh'] / 2 - ty / tw * C['vh'] * 0.5 + C['vy'])


def star_world(head, p, yaw, sign=1):
    """centre of one star: local (r, 0, 0) rotated about z by the angle, scaled by head scale x unk_44, billboarded
    by -yaw about y, plus the head position"""
    r = p['x'] + 10.0
    th = math.radians(p['ang'])
    lx, ly = r * math.cos(th), sign * r * math.sin(th)
    k = head['scale'] * head['s44']
    lx, ly = lx * k, ly * k
    a = math.radians(-yaw)
    wx, wz = lx * math.cos(a), -lx * math.sin(a)
    hx, hy, hz = head['pos']
    return hx + wx, hy + ly, hz + wz


def frame_stars(e, base):
    head, P = parts(e, base)
    C = camera(e)
    out = []
    for i, p in enumerate(P):
        X = star_world(head, p, C['yaw'])
        sx, sy = project(C, *X)
        out.append(dict(i=i + 1, t=p['t'], ang=p['ang'], r=p['x'] + 10, alpha=head['a24'] * p['a24'] / 255.0,
                        size=(1.0 - (i + 1) % 3 * 0.3), sx=sx, sy=sy, v=p['v']))
    return C, head, out


if __name__ == '__main__':
    st, N, SD, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    inp = {}
    if len(sys.argv) > 5 and sys.argv[5]:
        for tok in sys.argv[5].split(','):
            f, b = tok.split(':'); inp[int(f)] = eval(b)
    os.makedirs(OUT, exist_ok=True)
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/ar%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    e.load('states/' + st if not st.startswith('/') else st); e.step(0, 0, 0, 2)
    if SD != '-':
        sd = int(SD, 16); e.w32(SEED, sd); e.w32(SEED2, sd)          # DIAGNOSTIC: seed write (setup only)
    base = find_aura(e)[0]
    rows = []
    for f in range(N):
        e.step(inp.get(f, 0), 0, 0, 2)
        C, head, S = frame_stars(e, base)
        rows.append(dict(f=f, seed=e.u32(SEED), cam=dict(yaw=C['yaw'], id=C['id'], vp=(C['vw'], C['vh'], C['vx'], C['vy'])),
                         head=head, stars=S))
        subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/f%04d.png' % (OUT, f)], check=True)
    json.dump(rows, open(os.path.join(OUT, 'stars.json'), 'w'))
    print('frames', N, 'camera', rows[0]['cam'], 'head', rows[0]['head'])
