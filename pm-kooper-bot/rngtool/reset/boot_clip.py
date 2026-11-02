"""Real-console boot clip (OBS 60 fps, S-Video -> GV-USB2): per video frame, the scene (no signal / black / logo / title /
field) and the status-bar coin box (gold and white fractions, as the page's detector), so the boot timeline and the coin
shines can be read off. usage: boot_clip.py CLIP OUT.json [coin box x y w h at 1280x720, default 1084 50 38 42]"""
import sys, json, subprocess, numpy as np
clip, out = sys.argv[1], sys.argv[2]
bx, by, bw, bh = [int(v) for v in sys.argv[3:7]] if len(sys.argv) > 6 else (1084, 50, 38, 42)
def frames(vf, w, h):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', clip, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3).astype(int)
rows = []
G = frames('crop=960:720:320:0,scale=96:72', 96, 72)          # game area (right of the overlay column)
C = frames('crop=%d:%d:%d:%d' % (bw, bh, bx, by), bw, bh)
for i, (g, c) in enumerate(zip(G, C)):
    r, gg, b = g[..., 0], g[..., 1], g[..., 2]
    blue = float(((b > 150) & (r < 80) & (gg < 80)).mean())
    lum = float(g.mean())
    cr, cg, cb = c[..., 0], c[..., 1], c[..., 2]
    white = (cr > 200) & (cg > 200) & (cb > 190)
    gold = ~white & (cr > 140) & (cg > 95) & (cb < 120) & (cr > cb + 60)
    bar = float(((cr > 150) & (cg > 120) & (cb > 50) & (cb < 140)).mean())   # tan bar background
    rows.append({'i': i, 'blue': round(blue, 3), 'lum': round(lum, 1), 'white': round(float(white.mean()), 4),
                 'gold': round(float(gold.mean()), 4), 'bar': round(bar, 3), 'cy': round(float(c.mean()), 1)})
json.dump(rows, open(out, 'w'))
print('frames', len(rows))
# ---- summary: timeline and the coin draw pattern (for boot_search.c) ----
sig = next(r['i'] for r in rows if r['blue'] < 0.5)                                  # GV-USB2 blue screen ends
# N64 logo: first frame of the fade-in. It fades in from black (clip 2) or from the capture's grey settling screen
# (clip 1: grey 61 -> 89.7 in one frame), so take the first frame that is either non-black after black or a jump of > 20.
logo = next(r['i'] for k, r in enumerate(rows) if r['i'] > sig + 5 and ((r['lum'] > 10 and rows[k - 1]['lum'] < 3)
                                                                          or r['lum'] - rows[k - 1]['lum'] > 20))
dark = [r['i'] for r in rows if r['lum'] < 2 and r['i'] > logo + 200]
load_lo, load_hi = (dark[0], dark[-1]) if dark else (None, None)                     # black screen of the file load
bar = next((r['i'] for r in rows[(load_hi or 0):] if r['bar'] > 0.2), None)
on = [r['i'] for k, r in enumerate(rows) if bar and r['i'] > bar and r['white'] > 0.02 and rows[k - 1]['white'] <= 0.02]
print('video frames: signal %d, N64 logo %d, file-load black %s-%s, status bar up %s, end %d' % (sig, logo, load_lo, load_hi, bar, len(rows) - 1))
print('bar up for %.1f s; shine onsets: %s' % ((len(rows) - bar) / 60, on))
gaps = [(b - a) / 2 for a, b in zip(on, on[1:])]
ks = [round((g - 48) / 24) for g in gaps]
print('game frames between shines:', gaps, '-> plain draws between:', ks)
print('pattern from the first shine:', 'S' + ''.join('.' * k + 'S' for k in ks),
      '| plain draws possible before it: %d' % int((on[0] - bar) / 2 // 24))
