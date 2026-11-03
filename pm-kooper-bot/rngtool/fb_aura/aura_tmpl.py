"""Star-outline sprite templates from the emulator (glide64), one per size class, for the matched filter (aura_mf.py).
DIAGNOSTIC RAM writes (setup only, for this measurement): gRandSeed; every part except the studied one gets its counter
set to -100000 (alpha 0, never restarts), the studied one 19 (restarts on the next frame); a render with all 16 parts
hidden is the background. Parts 3 / 1 / 2 have size 1.0 / 0.7 / 0.4 (scale = 1 - (index mod 3) * 0.3).
For each size the frames t = 6..13 (alpha >= 0.81) are cut out around the RAM-projected star centre, divided by
(alpha x (white - background)) to give the sprite's coverage, rotated back by the star's RAM angle (the sprite turns with
unk_3C) and averaged: a coverage map at 2x N64 resolution in the sprite's own frame (angle 0).
The glide64 screenshot taken after frame f shows frame f - 1 (one-frame display lag: fast stars sit one step behind
their RAM position), so screenshot f is paired with the RAM state of frame f - 1.
The sprite is not centred on its model point: its centroid sits OFF x size units further out along the radius (the
display list's vertices are offset from the origin and scaled with the size). Each template is recentred on the
sprite centroid and the offset is stored (off_<size>, units: 1.594 px/unit at 320x240, the route camera's scale from the RAM projection).
Run from /tmp/claude-0/pm/bot1 with DISPLAY / M64P_GFX / M64P_DATA as aura_render.py:
  PYTHONPATH=. python3 aura_tmpl.py STATE OUT.npz
OUT.npz: cov_<size> (65x65 at 2x N64 px, centre = model point), plus per-frame records (t, angle, model centre, the
measured centroid) to check the sprite offset."""
import sys, os, math, subprocess
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage
from emu import *
from rngsim import *
from aura_probe import find_aura
from aura_render import frame_stars

H = 32


def grab(path):
    subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', path], check=True)
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float64)


if __name__ == '__main__':
    st, OUT = sys.argv[1], sys.argv[2]
    tmp = OUT + '_frames'; os.makedirs(tmp, exist_ok=True)
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/at%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    def run(keep, tag, N=20):
        e.load('states/' + st); e.step(0, 0, 0, 2)
        e.w32(SEED, 0x1234ABCD); e.w32(SEED2, 0x1234ABCD)               # DIAGNOSTIC: seed write
        base = find_aura(e)[0]
        for k in range(1, 17):
            e.w32(base + 0x48 * k + 0x14, (19 if k == keep else -100000) & 0xFFFFFFFF)   # DIAGNOSTIC: hide / restart parts
        fr = []
        for f in range(N):
            e.step(0, 0, 0, 2)
            C, head, S = frame_stars(e, base)
            fr.append((S, grab('%s/%s_%02d.png' % (tmp, tag, f))))
        return fr
    bg = run(0, 'bg')
    res = {}; recs = []
    for part, size in ((3, 1.0), (1, 0.7), (2, 0.4)):
        fr = run(part, 'p%d' % part); acc = []
        for f in range(1, len(fr)):
            S, img = fr[f - 1][0], fr[f][1]; img0 = bg[f][1]
            s = S[part - 1]; t = s['t']; a = s['alpha'] / 255.0
            cx, cy = 2 * s['sx'], 2 * s['sy']                         # 2x window coordinates
            d = (img - img0).mean(2); w = (255.0 - img0.mean(2))
            yi, xi = int(round(cy)), int(round(cx))
            if not (H <= yi < 480 - H and H <= xi < 640 - H): continue
            cut = d[yi - H:yi + H + 1, xi - H:xi + H + 1]; ww = w[yi - H:yi + H + 1, xi - H:xi + H + 1]
            m = cut > 25
            cen = ndimage.center_of_mass(np.where(m, cut, 0)) if m.any() else (H, H)
            recs.append(dict(size=size, f=f, t=t, ang=s['ang'], alpha=a, model=(cx, cy), cen=(xi - H + cen[1], yi - H + cen[0])))
            if 6 <= t <= 13 and a > 0.5:
                cov = np.clip(cut / np.maximum(a * ww, 30.0), 0, 1.2)
                # shift so the model point is at the centre (subpixel), then rotate back by the angle (ccw on screen)
                cov = ndimage.shift(cov, (yi - cy, xi - cx), order=1)
                acc.append(ndimage.rotate(cov, -s['ang'], reshape=False, order=1))
        c = np.mean(acc, 0)
        cm = np.where(c > 0.1 * c.max(), c, 0); cy, cx = ndimage.center_of_mass(cm)
        res['off_%.1f' % size] = np.array([(cx - H) / 2 / 1.594, -(cy - H) / 2 / 1.594])   # tangential: ccw positive     # radial, tangential (units)
        res['cov_%.1f' % size] = ndimage.shift(c, (H - cy, H - cx), order=1)
        print('size %.1f: sprite centroid offset %.2f units radial, %.2f tangential' % (size, *res['off_%.1f' % size]))
        print('size %.1f: %d frames averaged; peak coverage %.2f; ' % (size, len(acc), res['cov_%.1f' % size].max()), flush=True)
    for r in recs:
        print('  size %.1f t %2d ang %7.1f alpha %.2f model (%.1f,%.1f) centroid (%.1f,%.1f)' % (r['size'], r['t'], r['ang'], r['alpha'], *r['model'], *r['cen']))
    np.savez(OUT, **res, recs=np.array([(r['size'], r['t'], r['ang'], r['alpha'], *r['model'], *r['cen']) for r in recs]))
