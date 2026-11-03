"""Emulator renders -> simulated console capture, for the end-to-end check of the aura pipeline (README section 8).
Input: aura_render.py output (glide64 2x frames f0000.png..). Per game frame:
  2x2 mean -> 320x240 (the N64's own raster); S-Video as readouts/shimmer_svideo.py (320 -> 720 resample, line
  doubling, luma low-pass 4.2 MHz, chroma 1.3 MHz, noise Y 2 / C 3 levels); then the OBS layout of the real clips
  (capture x = 274 + 3.264 X, y = -24 + 3.32 Y for N64 px X, Y; README section 7 registration), 1280x720.
Cadence like the console clips: each game frame on 2 capture frames, a 3rd copy every 45 or 90 capture frames
(alternating, seeded), and one game frame shown once every ~400 frames. Encoded with x264 crf 16 (the real clips are
x264 too). Writes OUT.mkv and OUT_cadence.json (capture frames per game frame).
usage: python3 aura_capsim.py RENDER_DIR N OUT [seed=1]"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image
from scipy import ndimage


def lp(ch, mhz, axis=-1):
    s = 13.5 / (2 * math.pi * mhz)
    return ndimage.gaussian_filter1d(ch, s, axis=axis, mode='nearest')


def svideo(img320, rng):
    """(240,320,3) float 0..255 -> (480,720,3) float RGB after the S-Video path"""
    h, w = img320.shape[:2]
    xs = np.linspace(0, w - 1, 720); j0 = np.floor(xs).astype(int); j1 = np.minimum(j0 + 1, w - 1); f = xs - j0
    a = img320[:, j0] * (1 - f)[:, None] + img320[:, j1] * f[:, None]
    a = np.repeat(a, 2, axis=0)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B; U = (B - Y) * 0.564; V = (R - Y) * 0.713
    Y = lp(Y, 4.2) + rng.normal(0, 2.0, Y.shape); U = lp(U, 1.3) + rng.normal(0, 3.0, U.shape); V = lp(V, 1.3) + rng.normal(0, 3.0, V.shape)
    R = Y + V / 0.713; B = Y + U / 0.564; G = (Y - 0.299 * R - 0.114 * B) / 0.587
    return np.clip(np.stack([R, G, B], -1), 0, 255)


def to_layout(a720):
    """(480,720,3) -> (720,1280,3): capture (x, y) = (274 + 1.4507 u, -24 + 1.66 v) for 720x480 px (u, v)"""
    yy, xx = np.mgrid[0:720, 0:1280].astype(np.float64)
    u = (xx + 0.5 - 274) / (3.264 / 2.25) - 0.5; v = (yy + 0.5 + 24) / 1.66 - 0.5
    out = np.stack([ndimage.map_coordinates(a720[..., c], [v, u], order=1, cval=0) for c in range(3)], -1)
    out[(u < 0) | (u > 719) | (v < 0) | (v > 479)] = 0
    return out


if __name__ == '__main__':
    D, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    rng = np.random.default_rng(int(sys.argv[4]) if len(sys.argv) > 4 else 1)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '60',
                           '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', OUT + '.mkv'], stdin=subprocess.PIPE)
    cad = []; nxt3 = 45; c = 0
    for f in range(N):
        g = np.asarray(Image.open(os.path.join(D, 'f%04d.png' % f)).convert('RGB')).astype(np.float64)
        g = g.reshape(240, 2, 320, 2, 3).mean((1, 3))
        frame = to_layout(svideo(g, rng)).astype(np.uint8)
        k = 2
        if c >= nxt3: k = 3; nxt3 = c + (90 if rng.random() < 0.5 else 45)
        elif f % 400 == 199: k = 1
        for _ in range(k): ff.stdin.write(frame.tobytes())
        cad.append(k); c += k
    ff.stdin.close(); ff.wait()
    json.dump(cad, open(OUT + '_cadence.json', 'w'))
    print('game frames', N, 'capture frames', c, 'copies', {k: cad.count(k) for k in (1, 2, 3)})
