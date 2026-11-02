"""Real clip: track one isolated spiny from its launch and fit the flight model (throw_spiny_main: x linear to the rest
point over 30 frames; y: vy0 = dy/30 + 3 units/frame, -0.2 units/frame^2, so y is a parabola with a fixed curvature).
The fitted curvature gives the capture px per world unit; the fit residual gives the readout precision of the rest
point (x, y) and so the bits per spiny. Game frame k = capture frames (F0 + 2k, F0 + 2k + 1).
usage: python3 clip_fit.py FRAMEDIR F0 NFRAMES X Y   (X, Y: the blob's capture position on its first frame)"""
import sys, os, math
import numpy as np
from PIL import Image
from scipy import ndimage

D, F0, N, X, Y = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
pts = []
x, y = X, Y
for k in range(N):
    im = np.asarray(Image.open(os.path.join(D, '%04d.png' % (F0 + 2 * k))).convert('RGB')).astype(np.int16)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    m = (r > 140) & (g < 90) & (b < 100) & (r - g > 90)
    # only pixels within 45 px of the predicted position (one spiny is ~100 px across with spikes, ~70 px red body)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    px = x + (pts[-1][1] - pts[-2][1] if len(pts) > 1 else 0); py = y + (pts[-1][2] - pts[-2][2] if len(pts) > 1 else 0)
    w = m & ((xx - px) ** 2 + (yy - py) ** 2 < 45 ** 2)
    if w.sum() < 300: break
    cy, cx = ndimage.center_of_mass(w)
    pts.append((k, cx, cy, int(w.sum()))); x, y = cx, cy
pts = np.array(pts)
t, cx, cy = pts[:, 0], pts[:, 1], pts[:, 2]
A = np.vstack([np.ones_like(t), t]).T
bx, rx, *_ = np.linalg.lstsq(A, cx, rcond=None)
A2 = np.vstack([np.ones_like(t), t, t * t]).T
by, ry, *_ = np.linalg.lstsq(A2, cy, rcond=None)
resx = cx - A @ bx; resy = cy - A2 @ by
s = -by[2] / 0.1 * -1 if by[2] != 0 else float('nan')   # capture y grows downward: +0.1 s px/frame^2
s = by[2] / 0.1
print('tracked %d game frames' % len(t))
for row in pts: print('  k=%2d x=%7.1f y=%7.1f area=%d' % tuple(row))
print('x: v = %.3f px/frame, residual rms %.2f px; y: quadratic coef %.4f px/frame^2 -> %.2f capture px per unit; residual rms %.2f px'
      % (bx[1], resx.std(), by[2], s, resy.std()))
n = len(t)
# x: screen x is not linear in t (z also moves 20 units toward the camera, so the projection speeds up): until the
# emulator projection is fitted, use a free quadratic and the standard error of its extrapolation to t = 30
bx2 = np.polyfit(t, cx, 2); rx2 = cx - np.polyval(bx2, t)
X2 = np.vstack([t * t, t, np.ones_like(t)]).T; cov = np.linalg.inv(X2.T @ X2) * rx2.var(ddof=3)
v30 = np.array([900., 30., 1.]); sig_tx = math.sqrt(v30 @ cov @ v30) / s
# y: with the curvature known, vy0 is the slope of y - 0.1 s t^2
yc = cy - 0.1 * s * t * t
by2 = np.polyfit(t, yc, 1); sig_vy = (yc - np.polyval(by2, t)).std(ddof=2) * math.sqrt(12 / (n ** 3 - n))
sig_ty = 30 * sig_vy / s
print('x quadratic residual rms %.2f px; rest x +-%.2f units (1 sd, extrapolated to frame 30); rest y +-%.2f units (1 sd)'
      % (rx2.std(), sig_tx, sig_ty))
for k in (2, 3):
    bits = math.log2(141 / (2 * k * max(sig_tx, 0.5))) + math.log2(81 / (2 * k * max(sig_ty, 0.5)))
    print('bits from (x, y) at +-%d sd (tolerance floored at 0.5 unit): %.1f' % (k, bits))
