"""FB2 lightning-bolt detector check: per screenshot (592x390 crop, files fNNNNN.png) count purple bolt pixels in the
sky band and compare with the emulator's lightning draw frames. usage: fb2_bolts.py DIR LIGHTFILE"""
import sys, glob, re, os
import numpy as np
from PIL import Image
D = sys.argv[1]; L = eval(open(sys.argv[2]).read().split('LIGHT', 1)[1])
def purple(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)[60:250]       # sky band below the status bar
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int(np.sum((r > 150) & (b > 170) & (g < r - 40) & (g < b - 40)))
fs = sorted(glob.glob(D + '/f*.png')); cnt = {int(re.search(r'f(\d+)', os.path.basename(f)).group(1)): purple(f) for f in fs}
Ls = sorted(set(L)); onsets = [f for f in sorted(cnt) if cnt[f] > 30 and cnt.get(f - 1, 0) <= 30]
print('draw frames', Ls); print('visual onsets', onsets)
print('lags', [min((o - l for o in onsets if o >= l), default=None) for l in Ls])
