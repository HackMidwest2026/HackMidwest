"""Timeline of a capture (1280x720 60 fps): per capture frame, whether it is a new game frame (content change),
the status bar (gold HUD pixels in the top band), the input display's A circle, and the scene-change size.
Prints the game-frame count between events. usage: python3 clip_timeline.py CLIP T0 T1 OUT.json"""
import sys, subprocess, json
import numpy as np
clip, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
W, H = 320, 180
p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', clip, '-vf', 'scale=%d:%d' % (W, H),
                    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
A = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3).astype(np.int16)
rows = []; g = -1
for i in range(len(A)):
    d = float(np.abs(A[i] - A[i - 1])[30:175, 80:320].mean()) if i else 99.0
    new = d > 0.5
    if new: g += 1
    top = A[i, 8:30, 80:318]
    gold = float(((top[..., 0] > 170) & (top[..., 1] > 130) & (top[..., 2] < 110)).mean())
    rows.append(dict(i=i, t=t0 + i / 60.0, g=g, new=new, diff=d, gold=gold))
json.dump(rows, open(out, 'w'))
prev = None
for r in rows:
    bar = r['gold'] > 0.25
    if prev is None or bar != prev or r['diff'] > 25:
        print('t %.3f  capture %4d  game frame %4d  bar %s  diff %.1f' % (r['t'], r['i'], r['g'], 'up' if bar else '--', r['diff']))
    prev = bar
