"""Screen geometry of single aura stars (glide64), to fit the RAM -> screen mapping used by the readout model.
DIAGNOSTIC RAM writes (setup only, for this measurement): gRandSeed; and every part except the one studied gets its
counter set to -100000 (alpha 0, never restarts), so one star is on screen alone. A background render with all 16
parts hidden is subtracted. The battle menu camera is static, so the background is the same frame by frame except for
Bowser's idle animation and lightning; both renders run the same frames from the same state.
Run from /tmp/claude-0/pm/bot1 with DISPLAY / M64P_GFX / M64P_DATA as aura_render.py:
  PYTHONPATH=. python3 aura_geom.py STATE OUTDIR PART[,PART...] [N=24]
Writes OUTDIR/geom.json: per part and frame, RAM (t, angle, radius, alpha) and the measured star centroid / pixel count
in 320x240 viewport coordinates, plus the projection of the RAM model."""
import sys, os, json, subprocess
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from emu import *
from rngsim import *
from aura_probe import find_aura, parts
from aura_render import camera, project, star_world, frame_stars


def grab(path):
    subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', path], check=True)
    return np.asarray(Image.open(path).convert('RGB')).astype(np.int32)


if __name__ == '__main__':
    st, OUT, PL = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
    N = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    os.makedirs(OUT, exist_ok=True)
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/ag%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    res = {}
    def run(keep, tag):
        e.load('states/' + st); e.step(0, 0, 0, 2)
        e.w32(SEED, 0x1234ABCD); e.w32(SEED2, 0x1234ABCD)               # DIAGNOSTIC
        base = find_aura(e)[0]
        for k in range(1, 17):
            if k != keep: e.w32(base + 0x48 * k + 0x14, (-100000) & 0xFFFFFFFF)   # DIAGNOSTIC: hide part k
            else: e.w32(base + 0x48 * k + 0x14, 19)                    # DIAGNOSTIC: restart on the next frame
        frames = []
        for f in range(N):
            e.step(0, 0, 0, 2)
            C, head, S = frame_stars(e, base)
            img = grab('%s/%s_%02d.png' % (OUT, tag, f))
            frames.append((S, img, C))
        return frames
    bg = run(0, 'bg')
    for k in PL:
        fr = run(k, 'p%02d' % k); rows = []
        for f, ((S, img, C), (_, img0, _)) in enumerate(zip(fr, bg)):
            d = np.abs(img - img0).sum(2)
            d[:, :300] = 0; d[400:, :] = 0                    # only around Bowser (the menu wheel differs bottom-left)
            ys, xs = np.nonzero(d > 60)
            s = S[k - 1]
            row = dict(f=f, t=s['t'], ang=s['ang'], r=s['r'], alpha=s['alpha'], model=(s['sx'], s['sy']), n=int(len(xs)))
            if len(xs):
                w = d[ys, xs].astype(float)
                row['cen'] = (float((xs * w).sum() / w.sum()) / 2, float((ys * w).sum() / w.sum()) / 2)
                row['box'] = (int(xs.min()) // 2, int(ys.min()) // 2, int(xs.max()) // 2, int(ys.max()) // 2)
            rows.append(row)
        res[k] = rows
        print('part', k, [(r['f'], r['t'], round(r['ang']), round(r['r'], 1), r['n'], tuple(round(v, 1) for v in r.get('cen', ())),
                           tuple(round(v, 1) for v in r['model'])) for r in rows][:24], flush=True)
    json.dump(res, open(os.path.join(OUT, 'geom.json'), 'w'))
