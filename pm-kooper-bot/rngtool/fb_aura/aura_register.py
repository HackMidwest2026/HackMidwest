"""Camera for a console stretch from the emulator: register an emulator render of the same battle menu (aura_render.py
frames, passed through aura_capsim.py's S-Video and OBS-layout model, median over frames so the stars drop out) onto
the clip's background (median of the kNN backgrounds' luma), by gradient correlation over Bowser's box, scanning a
scale about the aura centre and a shift. If the best scale is 1.00, the console camera is the emulator's route camera
(homography exact on RAM positions: centre (1027.5, 365.9) in this layout, kx 5.203, ky 5.245, shear 0.114,
pitch -4.9e-4) moved by the shift, and PRE_cam.json is written with it (keeping 'white' / 'gains' if present).
Clip C (Nov 2, 15:24): correlation 0.896 at scale 1.00, shift (-1, -6) px -> centre (1026.5, 359.9).
usage: python3 aura_register.py RENDER_DIR PRE"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aura_mf as m, aura_capsim as cs

EMU_CAM = [1027.5, 365.9, 5.203, 5.245, 0.114, -4.9e-4]

if __name__ == '__main__':
    R, pre = sys.argv[1], sys.argv[2]
    rng = np.random.default_rng(0); E = []
    fs = sorted(f for f in os.listdir(R) if f.endswith('.png'))[::4][:10]
    for f in fs:
        g = np.asarray(Image.open(os.path.join(R, f)).convert('RGB')).astype(float).reshape(240, 2, 320, 2, 3).mean((1, 3))
        a = cs.to_layout(cs.svideo(g, rng)); E.append(m.luma(a.astype(np.float32))[m.Y0:m.Y0 + m.CH, m.X0:m.X0 + m.CW])
    E = np.median(np.stack(E), 0)
    L = np.load(pre + '_B.npy', mmap_mode='r')
    C = np.median(np.stack([L[k].astype(np.float32) for k in range(0, len(L), max(1, len(L) // 50))]), 0)
    grad = lambda a: np.hypot(*[ndimage.sobel(ndimage.gaussian_filter(a, 1.5), ax) for ax in (0, 1)])
    ge, gc = grad(E), grad(C)
    box = (slice(150, 560), slice(100, 540)); b = gc[box]
    cx, cy = EMU_CAM[0] - m.X0, EMU_CAM[1] - m.Y0
    yy, xx = np.mgrid[0:m.CH, 0:m.CW].astype(float)
    best = None
    for sc in np.arange(0.94, 1.061, 0.01):
        es = ndimage.map_coordinates(ge, [(yy - cy) / sc + cy, (xx - cx) / sc + cx], order=1)
        for dy in range(-14, 15):
            for dx in range(-14, 15):
                a = np.roll(np.roll(es, dy, 0), dx, 1)[box]
                c = ((a - a.mean()) * (b - b.mean())).mean() / a.std() / b.std()
                if best is None or c > best[0]: best = (c, sc, dx, dy)
    c, sc, dx, dy = best
    cam = [EMU_CAM[0] + dx, EMU_CAM[1] + dy, EMU_CAM[2] * sc, EMU_CAM[3] * sc, EMU_CAM[4] * sc, EMU_CAM[5]]
    print('registration: correlation %.3f, scale %.2f, shift (%d, %d) -> camera %s' % (c, sc, dx, dy, np.round(cam, 4).tolist()))
    C0 = json.load(open(pre + '_cam.json')) if os.path.exists(pre + '_cam.json') else dict(white=235.0)
    C0['cam'] = [float(v) for v in cam]; C0['registration'] = dict(corr=float(c), scale=float(sc), dx=int(dx), dy=int(dy))
    json.dump(C0, open(pre + '_cam.json', 'w'))
