"""Draw the rays predicted for a seed on capture frames (visual check). usage:
charge_overlay.py FRAMES_DIR CAMS.json V0 SEED Q OUT.png n1,n2,...   (frame 0 = first effect created)"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
from charge_obs import project, VIDEO_MAP
from charge_model import simulate
from charge_prep import game_frames
d, cams, v0, seed, q, out = sys.argv[1], json.load(open(sys.argv[2])), int(sys.argv[3]), int(sys.argv[4], 16), int(sys.argv[5]), sys.argv[6]
ns = [int(x) for x in sys.argv[7].split(',')]
sim = simulate(seed, max(ns) + 1, coin_rule=(q,)); fr = game_frames(d, v0, max(ns) + 1)
SX, OX, SY, OY = VIDEO_MAP; cx, cy, cz = cams['centre']; tiles = []
for n in ns:
    im = Image.open('%s/%04d.png' % (d, fr[n])).convert('RGB'); dr = ImageDraw.Draw(im)
    M, vp = cams['cams'][n][:16], cams['cams'][n][16:20]
    for e, i, th, a, D0, D1 in sim[n]['vis']:
        t = np.radians(th); P = np.array([[cx + D0 * np.cos(t), cy + D0 * np.sin(t), cz], [cx + D1 * np.cos(t), cy + D1 * np.sin(t), cz]])
        x, y, _ = project(M, vp, P)
        dr.line([(SX * x[0] + OX, SY * y[0] + OY), (SX * x[1] + OX, SY * y[1] + OY)], fill=(255, 0, 0) if e == 0 else (0, 255, 255), width=1)
    tiles.append(im.crop((300, 20, 1280, 710)).resize((490, 345)))
W = Image.new('RGB', (490 * min(3, len(tiles)), 345 * ((len(tiles) + 2) // 3)))
for k, t in enumerate(tiles): W.paste(t, ((k % 3) * 490, (k // 3) * 345))
W.save(out)
