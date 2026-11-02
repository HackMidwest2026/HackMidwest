"""Build ridge maps (charge_obs.build_maps) for frames n = 0..N-1 after the first effect's creation (frame 0) and
write MAPS.bin for charge_search. The seed-independent part of the effect (part 0's burst) and the scene are removed
by subtracting an emulator background render (rays zero length, DIAGNOSTIC) of the same frame.
  cams:   charge_prep.py cams PROBE_DIR C OUT.json [N]            cameras + centre from an emulator reference run
  emu:    charge_prep.py emu PROBE_DIR C BG_DIR BG_C OUT.bin [N] [BLUR NOISE]   (end-to-end test on emulator frames)
  video:  charge_prep.py video FRAMES_DIR CAMS.json BG_DIR BG_C V0 OUT.bin [N]
Frame n is shown in emulator image C+n+1 (the image after frame f shows the state of frame f-1); in the capture,
V0 = capture frame showing n = 0, then one game frame per 2 capture frames, re-phased at OBS repeats."""
import sys, json, struct, numpy as np, cv2
from PIL import Image
from charge_obs import *
def write(out, S, C):
    with open(out, 'wb') as f:
        f.write(struct.pack('<ii', S.shape[0], S.shape[2] - 1)); f.write(S.astype('<f4').tobytes()); f.write(C.astype('<f4').tobytes())
def small(d, i): return np.asarray(Image.open('%s/%04d.png' % (d, i)).convert('L'))[60:680:4, 330:1260:4].astype(float)
def game_frames(d, v0, n, thr=0.8):
    """capture frame for each game frame: step 2; if the frame 2 on is a repeat (no change) but the next one changes,
    the OBS repeat sits here, so step 3."""
    out = [v0]
    while len(out) < n:
        i = out[-1] + 2
        dprev = np.abs(small(d, i) - small(d, i - 1)).mean(); dnext = np.abs(small(d, i + 1) - small(d, i)).mean()
        if dprev < thr and dnext > thr: i += 1
        out.append(i)
    return out
def rgb(d, i): return np.asarray(Image.open('%s/%04d.png' % (d, i)).convert('RGB'))
if __name__ == '__main__':
    mode = sys.argv[1]; to2 = lambda x, y: (2 * x, 2 * y)
    if mode == 'cams':
        d, c, out = sys.argv[2], int(sys.argv[3]), sys.argv[4]; N = int(sys.argv[5]) if len(sys.argv) > 5 else 48
        L = json.load(open(d + '/log.json'))
        cen = L[c]['fx'][min(L[c]['fx'], key=lambda a: int(a, 16))][0][1:4]
        json.dump({'centre': cen, 'cams': [L[c + n]['cams']['1'][:20] for n in range(N)]}, open(out, 'w'))
    elif mode == 'emu':
        d, c, bgd, bgc, out = sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), sys.argv[6]
        N = int(sys.argv[7]) if len(sys.argv) > 7 else 48
        blur = float(sys.argv[8]) if len(sys.argv) > 8 else 0; noise = float(sys.argv[9]) if len(sys.argv) > 9 else 0
        L = json.load(open(d + '/log.json')); rng = np.random.default_rng(0); items = []
        for n in range(N):
            fr = L[c + n]; Y = luma(rgb(d, c + n + 1))
            if blur: Y = cv2.GaussianBlur(Y, (0, 0), blur)
            if noise: Y = Y + rng.normal(0, noise, Y.shape).astype(np.float32)
            R, kb = residual(Y, luma(rgb(bgd, bgc + n + 1)), blur if blur else 0.01)
            items.append((R, to2, fr['cams']['1'][:16], fr['cams']['1'][16:20]))
        cen = L[c]['fx'][min(L[c]['fx'], key=lambda a: int(a, 16))][0][1:4]
        S, C = build_maps(items, cen); write(out, S, C); print('centre', cen)
    else:
        d, cams, bgd, bgc, v0, out = sys.argv[2], json.load(open(sys.argv[3])), sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
        N = int(sys.argv[8]) if len(sys.argv) > 8 else 48
        fr = game_frames(d, v0, N); print('capture frames', fr)
        items = []
        for n in range(N):
            R, kb = residual(warp_video(rgb(d, fr[n])), luma(rgb(bgd, bgc + n + 1)))
            items.append((R, to2, cams['cams'][n][:16], cams['cams'][n][16:20]))
        S, C = build_maps(items, cams['centre']); write(out, S, C)
