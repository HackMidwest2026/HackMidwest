"""Status bar hide delay after every confirm of a fight run (sr_fight.py output): the page's coin-present test on
the frames after each A. usage: sr_hudcheck.py DIR"""
import json, sys, io
import numpy as np
from PIL import Image
D = sys.argv[1]
F = json.load(open(D + '/fight.json')); data = open(D + '/run.mjpeg', 'rb').read()
starts = []; i = 0
while True:
    j = data.find(b'\xff\xd8\xff', i)
    if j < 0: break
    starts.append(j); i = j + 3
def frame(n):   # video frame n (1-based, as VF)
    a = starts[n - 1]; b = starts[n] if n < len(starts) else len(data)
    return Image.open(io.BytesIO(data[a:b])).convert('RGB')
def gold(im):
    a = np.asarray(im.crop((int(.78*640), int(.02*480), int(.845*640), int(.11*480))).resize((32, 32))).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return float(np.mean((r > 140) & (g > 95) & (b < 120) & (r > b + 60) & (g > 0.6 * r)))
for ev in F['events']:
    st = ev.get('step') if ('confirm' in ev or 'press' in ev) else None
    if not st: continue
    gs = [round(gold(frame(st + k)), 2) for k in range(0, 7)]
    first = next((k for k in range(0, 7) if gs[k] < 0.3), None)
    print(ev.get('confirm') or ev.get('press'), 'A at', st, 'gold k=0..6', gs, 'gone at +%s' % first)
