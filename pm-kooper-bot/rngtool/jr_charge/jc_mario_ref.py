"""Mario reference patch for the page's Charge reader (charge_live chgMarioShift), from an emulator render of the
Jr. Troopa arena: game frame -1 (frame 0 = the first energy_in_out creation = Charge confirm + 13), 640x480 game
raster luma, the same box as charge_live/mario_ref.json (x0 160, y0 236, 160 x 120). Also scores each patch against
the others with a port of chgMarioShift1 (high-pass sigma 4, template rows 248..343 x cols 196..267, dx +-36, dy +-4).
usage: python3 jc_mario_ref.py OUT.json NAME=SHOTDIR:CREATION_FRAME [...]   (SHOTDIR from jc_probe.py with screenshots)"""
import sys, json, base64, numpy as np
from PIL import Image
import cv2
X0, Y0, W, H = 160, 236, 160, 120
def luma_png(fn):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(np.int32)
    return ((77 * a[..., 0] + 150 * a[..., 1] + 29 * a[..., 2] + 128) >> 8).astype(np.uint8)
def hp(P): return P.astype(np.float32) - cv2.GaussianBlur(P.astype(np.float32), (0, 0), 4, borderType=cv2.BORDER_REPLICATE)
def shift(ref, Y):
    """ref: HxW patch at (X0, Y0); Y: 640x480 raster. Returns (dx, dy, ncc) like chgMarioShift1."""
    R0 = hp(ref); tw, th, tx, ty = 72, 96, 196, 248
    T = R0[ty - Y0:ty - Y0 + th, tx - X0:tx - X0 + tw].copy(); T -= T.mean(); sd = np.sqrt((T * T).mean())
    L = hp(Y[236:356, 140:300]); best = (-2, 0, 0); cs = {}
    for dy in range(-4, 5):
        for dx in range(-36, 37):
            ox, oy = tx + dx - 140, ty + dy - 236
            if ox < 0 or ox + tw > W or oy < 0 or oy + th > H: continue
            P = L[oy:oy + th, ox:ox + tw]; r = ((P * T).mean()) / (P.std() * sd + 1e-9); cs[(dx, dy)] = r
            if r > best[0]: best = (r, dx, dy)
    return best[1], best[2], round(float(best[0]), 3)
if __name__ == '__main__':
    out = sys.argv[1]; refs = {}; frames = {}
    for a in sys.argv[2:]:
        name, spec = a.split('='); d, c = spec.split(':'); c = int(c)
        Y = luma_png('%s/%04d.png' % (d, c))          # image after step c shows frame c-1 = frame -1
        frames[name] = Y; refs[name] = Y[Y0:Y0 + H, X0:X0 + W].copy()
    hw = json.load(open('/home/user/HackMidwest/pm-kooper-bot/rngtool/charge_live/mario_ref.json'))
    refs['hallway_route_clip'] = np.frombuffer(base64.b64decode(hw['b64']), np.uint8).reshape(hw['h'], hw['w'])
    for rn, R in refs.items():
        print('ref', rn, {fn: shift(R, Y) for fn, Y in frames.items()})
    doc = {}
    for name in frames:
        doc[name] = {'x0': X0, 'y0': Y0, 'w': W, 'h': H, 'b64': base64.b64encode(refs[name].tobytes()).decode(),
                     'note': 'Mario before the Charge (frame -1, 640x480 game raster luma), EMULATOR render (Glide64), Jr. Troopa arena (battle 0x0207), %s' % name}
    json.dump(doc, open(out, 'w'))
