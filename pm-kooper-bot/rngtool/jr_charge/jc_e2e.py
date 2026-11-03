"""Emulator end-to-end check of the Charge reader in the Jr. Troopa arena, with the page's own code:
rendered Charge frames (jc_probe.py screenshots; optional blur + noise as a stand-in for S-Video) -> game-frame
rasters -> charge_live's maps (jc_jsmaps.js, with this fight's camera table and Mario patch) -> charge_live's
search kernel natively (charge_live/tools/harness.c). Prints the found seed vs the truth (gRandSeed at frame 0).
usage: python3 jc_e2e.py PROBELOG.json SHOTDIR HARNESS [BLUR NOISE DX]
  DX: shift the rendered frames right by DX raster px (Mario standing elsewhere; tests the Mario patch)."""
import sys, os, json, subprocess, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
log, shots, harness = sys.argv[1:4]
blur = float(sys.argv[4]) if len(sys.argv) > 4 else 0; noise = float(sys.argv[5]) if len(sys.argv) > 5 else 0
DX = int(sys.argv[6]) if len(sys.argv) > 6 else 0
L = json.load(open(log)); c = next(f for f, fr in enumerate(L) if any(x[0] == '0xe00d6160' for x in fr['calls']))
truth = L[c]['s0']; coin = next(f - c for f in range(c, len(L)) if any(x[0] == '0x80146d54' for x in L[f]['calls']))
rng = np.random.default_rng(1)
def raster(i):
    a = np.asarray(Image.open('%s/%04d.png' % (shots, i)).convert('RGB')).astype(np.float32)
    Y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    if DX: Y = np.roll(Y, DX, axis=1)
    if blur: Y = cv2.GaussianBlur(Y, (0, 0), blur)
    if noise: Y = Y + rng.normal(0, noise, Y.shape).astype(np.float32)
    return np.clip(np.round(Y), 0, 255).astype(np.uint8)
G = np.stack([raster(c + n + 1) for n in range(50)] + [raster(c - 1), raster(c)])      # frames 0..49, -2, -1
u8 = '/dev/shm/jrc/e2e_%d.u8' % os.getpid(); mb = u8 + '.bin'; G.tofile(u8)
r1 = subprocess.run(['node', os.path.join(HERE, 'jc_jsmaps.js'), u8, mb], capture_output=True, text=True); print(r1.stdout.strip(), r1.stderr.strip()[:300])
r2 = subprocess.run([harness, mb, '16384', '%08x' % truth], capture_output=True, text=True); print(r2.stdout.strip(), r2.stderr.strip()[:300])
print('truth %08x first coin q %d | blur %.2f noise %.1f dx %d' % (truth, coin, blur, noise, DX))
os.remove(u8); os.remove(mb)
