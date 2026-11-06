"""The capture simulation of ../fb2_route/t6_capsim.py (S-Video path, the route clips' OBS layout, 60 fps capture by time,
about one logic frame in 90 with no picture of its own) for long renders, cached per game frame: the noise is seeded by
the game frame index and the screenshot's size + mtime, so a re-render that changes only the later frames recomputes
only those. Writes the capture frames as JPEG (quality 92; t6_capsim.py encodes x264 crf 16) and OUT.json (per capture
frame the game frame shown).
usage: python3 jc_capsim.py RENDER_DIR NGAME OUTDIR [seed=7]"""
import sys, os, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'fb2_route')); sys.path.insert(0, os.path.join(HERE, '..', 'fb_aura'))
from t6_capsim import to_layout
from aura_capsim import svideo
D, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 7
CACHE = os.path.join(D, '.cap'); os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)
shown = list(range(N)); skip = int(rng.integers(60, 120))
while skip < N: shown[skip] = shown[skip - 1]; skip += int(rng.integers(80, 111))
def frame(g):
    src = os.path.join(D, 's%04d.png' % g); st = os.stat(src)
    key = hashlib.md5(('%d:%d:%d:%d' % (g, st.st_size, int(st.st_mtime_ns), SEED)).encode()).hexdigest()[:12]
    p = os.path.join(CACHE, 'c%04d_%s.jpg' % (g, key))
    if not os.path.exists(p):
        im = np.asarray(Image.open(src).convert('RGB')).astype(np.float64).reshape(240, 2, 320, 2, 3).mean((1, 3))
        Image.fromarray(to_layout(svideo(im, np.random.default_rng([SEED, g]))).astype(np.uint8)).save(p, quality=92)
    return p
ncap = int(N / 29.97 * 60); idx = []; new = 0
for c in range(ncap):
    g = shown[min(N - 1, int((c + 0.5) / 60 * 29.97))]
    dst = os.path.join(OUT, 'f%05d.jpg' % c)
    if os.path.lexists(dst): os.remove(dst)
    os.symlink(frame(g), dst); idx.append(g)
json.dump({'first': 0, 'shown': idx}, open(OUT + '.json', 'w'))
print('game frames', N, 'capture frames', ncap)
