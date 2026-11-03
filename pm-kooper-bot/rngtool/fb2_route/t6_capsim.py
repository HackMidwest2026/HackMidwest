"""Emulator renders (t6_render.py s%04d.png, one per game frame) -> a simulated console capture at the Charge lock's
OBS layout (charge_live.js CHG_MAP0: capture x = 272.82 + 3.2637 X, y = -31.09 + 3.3221 Y for 320x240 game pixels;
the route clips' 1280x720 OBS layout), for feeding the page.
Per game frame: 2x2 mean -> 320x240, the S-Video path of fb_aura/aura_capsim.py (4.2 MHz luma, 1.3 MHz chroma, noise Y 2
/ C 3), the layout. Cadence by time: the game runs at 29.97 logic frames/s and the capture at 60.00 frames/s, so a
capture frame shows the newest game frame due by then (2 copies each, a 3rd about every 17 s); and, as fb_aura README
section 8 found on console, about one logic frame in 90 (seeded) never gets a picture of its own. x264 crf 16 (the real
clips are x264). Writes OUT.mkv and OUT.json (per capture frame the game-frame index shown).
usage: python3 t6_capsim.py RENDER_DIR FIRST LAST OUT [seed=1]"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fb_aura'))
from aura_capsim import svideo
from scipy import ndimage
MAP = (3.2637, 272.82, 3.3221, -31.09)

def to_layout(a720, m=MAP):
    """(480,720,3) S-Video frame (720 samples per 320 game px, line-doubled) -> (720,1280,3) at capture = O + S * X"""
    SX, OX, SY, OY = m
    yy, xx = np.mgrid[0:720, 0:1280].astype(np.float64)
    X = (xx + 0.5 - OX) / SX; Y = (yy + 0.5 - OY) / SY            # 320x240 game coordinates (pixel edges at integers)
    u = X * 720 / 320 - 0.5; v = Y * 2 - 0.5
    out = np.stack([ndimage.map_coordinates(a720[..., c], [v, u], order=1, cval=0) for c in range(3)], -1)
    out[(u < -0.5) | (u > 719.5) | (v < -0.5) | (v > 479.5)] = 0
    return out

if __name__ == '__main__':
    D, A, B, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    rng = np.random.default_rng(int(sys.argv[5]) if len(sys.argv) > 5 else 1)
    n = B - A + 1
    shown = list(range(n)); skip = int(rng.integers(60, 120))
    while skip < n:                                    # a logic frame with no picture: the one before stays up
        shown[skip] = shown[skip - 1]; skip += int(rng.integers(80, 111))
    ncap = int(n / 29.97 * 60)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '60',
                          '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', OUT + '.mkv'], stdin=subprocess.PIPE)
    cache = {}; idx = []
    for c in range(ncap):
        g = shown[min(n - 1, int((c + 0.5) / 60 * 29.97))]
        if g not in cache:
            cache.clear()
            im = np.asarray(Image.open(os.path.join(D, 's%04d.png' % (A + g))).convert('RGB')).astype(np.float64).reshape(240, 2, 320, 2, 3).mean((1, 3))
            cache[g] = to_layout(svideo(im, rng)).astype(np.uint8)
        ff.stdin.write(cache[g].tobytes()); idx.append(g)
    ff.stdin.close(); ff.wait()
    json.dump(dict(first=A, shown=idx), open(OUT + '.json', 'w'))
    print('game frames', n, 'capture frames', ncap, 'logic frames without a picture', sum(1 for i in range(1, n) if shown[i] == shown[i - 1]))
