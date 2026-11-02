"""Run the page's coin-present test (gold + white > 0.3 in the coin box, 32x32 sample) over every video frame and
compare with the truth (status bar on screen). usage: sr_detect.py DIR [box x y w h]"""
import json, sys, numpy as np
from PIL import Image
D = sys.argv[1]; box = [float(v) for v in sys.argv[2:6]] if len(sys.argv) > 5 else [0.78, 0.02, 0.065, 0.09]
T = json.load(open(D + '/truth.json')); tr = T['truth']; W, H = 320, 240; FS = W * H * 3 // 2
f = open(D + '/run.y4m', 'rb'); f.readline()
vis_by_vf = {}
for gf, vf, prev, k, mp, md, vis in tr: vis_by_vf[vf] = (vis, mp, md, gf)
def rgb(buf):
    y = np.frombuffer(buf, np.uint8, W * H).reshape(H, W); u = np.frombuffer(buf, np.uint8, W * H // 4, W * H).reshape(H // 2, W // 2); v = np.frombuffer(buf, np.uint8, W * H // 4, W * H * 5 // 4).reshape(H // 2, W // 2)
    return Image.merge('YCbCr', [Image.fromarray(y), Image.fromarray(u).resize((W, H)), Image.fromarray(v).resize((W, H))]).convert('RGB')
NS = []; G2 = []; fp = []; fn = 0; n = 0; i = 0; samples = []
while True:
    hdr = f.readline()
    if not hdr: break
    buf = f.read(FS)
    if i in vis_by_vf:
        vis, mp, md, gf = vis_by_vf[i]
        im = rgb(buf); x0, y0 = box[0] * W, box[1] * H
        a = np.asarray(im.crop((int(x0), int(y0), int(x0 + box[2] * W + 0.5), int(y0 + box[3] * H + 0.5))).resize((32, 32), Image.BILINEAR)).reshape(-1, 3).astype(int)
        r, g, b = a[:, 0], a[:, 1], a[:, 2]
        white = (r > 200) & (g > 200) & (b > 190); gold = ~white & (r > 140) & (g > 95) & (b < 120) & (r > b + 60)
        present = (gold.mean() + white.mean()) > 0.3
        gold2 = gold & (g > 0.6 * r); G2.append((vis, gold2.mean())); NS.append((gf, vis, gold2.mean(), white.mean()))
        if present and not vis: fp.append((gf, mp, md, round(gold.mean(), 2), round(white.mean(), 2))); (len(samples) < 6 and samples.append(i) and im.save('%s/fp_%05d.png' % (D, i)))
        if vis and not present: fn += 1
        n += 1
    i += 1
print('game frames checked', n, '| present while bar hidden:', len(fp), '| bar up but not present:', fn)
from collections import Counter
print('false-present by map:', Counter(x[1] for x in fp).most_common(10)); print('examples', fp[:10])

import numpy as np
v1=np.array([g for v,g in G2 if v]); v0=np.array([g for v,g in G2 if not v])
print('new gold (tan, g>0.6r) fraction: bar up p0.5/p1/p5/median', np.percentile(v1,[0.5,1,5,50]).round(2), '| bar hidden max/p99', v0.max().round(2), np.percentile(v0,99).round(2))

sys.path.insert(0, '/tmp/claude-0/pm/bot1'); from rngsim import adv
SH = 700 * (0xFFFFFFFF // 1010); shg = set()
for gf, vf, prev, k, mp, md, vis in tr:
    if k == 2 and adv(prev) >= SH: shg.update(range(gf, gf + 12))
x = [(g2, w) for gf, vis, g2, w in NS if vis and gf in shg]
print('frames 0-11 after a shine draw with the bar up:', len(x), 'min gold2', round(min(a for a, b in x), 2), 'p2', round(float(np.percentile([a for a, b in x], 2)), 2), 'max white', round(max(b for a, b in x), 2))
