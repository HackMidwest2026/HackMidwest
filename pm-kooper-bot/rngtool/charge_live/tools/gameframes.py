"""Game-frame rasters of a route clip's Charge, as the page reads them: capture -> 640x480 game raster (luma), frame 0 =
3 game frames before the first one whose mean brightness is 5 above the menu's (the burst onset). Also writes
frames -2 and -1 (for Mario's position) after the 50: OUT.u8 holds 52 x 480 x 640 uint8, frames 0..49, -2, -1.
usage: gameframes.py CLIP.mkv OUT.u8 [APPROX_CAPTURE_FRAME]   (writes 50 x 480 x 640 uint8; prints the capture index of frame 0)
APPROX: a capture frame shortly before the Charge confirm (default: found as the first big brightening)."""
import sys, subprocess, numpy as np, cv2
MAP = (3.2637, 272.82, 3.3221, -31.09)
def frames(path, a, n):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'select=between(n\\,%d\\,%d)' % (a, a + n - 1), '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, check=True).stdout
    F = np.frombuffer(p, np.uint8).reshape(-1, 720, 1280, 3)
    return (F[..., 0] * 0.299 + F[..., 1] * 0.587 + F[..., 2] * 0.114).astype(np.float32)
def warp(Y):
    SX, OX, SY, OY = MAP; ys, xs = np.mgrid[0:480, 0:640].astype(np.float32) / 2
    return cv2.remap(Y, (xs * SX + OX).astype(np.float32), (ys * SY + OY).astype(np.float32), cv2.INTER_LINEAR)
if __name__ == '__main__':
    path, out = sys.argv[1], sys.argv[2]
    approx = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if approx is None:   # coarse scan: the burst takes the game area's mean from ~58 to ~120
        p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-t', '20', '-vf', 'scale=160:90', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE, check=True).stdout
        g = np.frombuffer(p, np.uint8).reshape(-1, 90, 160)[:, 12:88, 44:156].astype(np.float32).mean((1, 2))
        approx = int(np.argmax(g > 100)) - 60
    a = max(0, approx - 10); F = frames(path, a, 180)
    m = F[:, 100:700:4, 350:1250:4].mean((1, 2))
    k0 = next(k for k in range(12, len(m)) if m[k] > np.median(m[k - 12:k - 1]) + 5)
    # distinct game frames from the trigger on (each shows on ~2 capture frames), and 2 before it by time
    idx = {3: k0}; k = k0
    for n in range(4, 50):
        k += 1
        while k < len(F) - 1 and np.abs(F[k][60:680:4, 330:1260:4] - F[k - 1][60:680:4, 330:1260:4]).mean() < 0.8: k += 1
        idx[n] = k
    for n in (2, 1, 0, -1, -2): idx[n] = k0 - 2 * (3 - n)
    G = np.stack([warp(F[idx[n]]) for n in list(range(50)) + [-2, -1]])
    np.clip(np.round(G), 0, 255).astype(np.uint8).tofile(out)
    print('frame 0 at capture frame', a + idx[0], 'trigger', a + k0)
