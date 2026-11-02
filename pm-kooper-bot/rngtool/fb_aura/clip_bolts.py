"""Sky lightning on a capture: purple-pixel count per game frame (thresholds of powerbounce/fb2_bolts.py: r > 150,
b > 170, g at least 40 below both) in the play area, onsets = first frame over 0.3% after a quiet frame. Prints onset
game frames (content-deduplicated) and their gaps; the stage script's sky loop has gaps 60/10/90/60 (220), the low
loop 5/30/5/90 (130). usage: python3 clip_bolts.py CLIP T0 T1"""
import sys, subprocess
import numpy as np
clip, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 320, 180
p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', clip, '-vf', 'scale=%d:%d' % (W, H),
                    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
A = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3).astype(np.int16)
g = -1; fr = []; prev = None
for i in range(len(A)):
    if prev is None or np.abs(A[i] - prev)[30:175, 80:320].mean() > 0.5:
        g += 1
        a = A[i, 10:175, 80:320]
        m = (a[..., 0] > 150) & (a[..., 2] > 170) & (a[..., 1] < np.minimum(a[..., 0], a[..., 2]) - 40)
        fr.append((g, i, float(m.mean())))
    prev = A[i]
on = [f for k, f in enumerate(fr) if f[2] > 0.003 and (k == 0 or fr[k - 1][2] <= 0.003)]
print('game frames', len(fr), 'onsets (game frame, capture frame, purple fraction):')
for o in on: print('  ', o[0], o[1], '%.4f' % o[2])
print('gaps (game frames):', [b[0] - a[0] for a, b in zip(on, on[1:])])
print('gaps (capture frames / 2):', [(b[1] - a[1]) / 2 for a, b in zip(on, on[1:])])
