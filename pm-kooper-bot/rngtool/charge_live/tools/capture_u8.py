"""A Charge read the page kept (charge_reads.js: chargeCaptures in a saved session log, or a Download saved Charge reads
file) -> the game-frame rasters harness.c and jsmaps.js read: OUT.u8 = 52 x 480 x 640 uint8, frames 0..49, then -2 and
-1 (a frame the page did not place is all zeros), plus OUT.json with each frame's time from the trigger picture (ms), its
brightness and the page's info (seed, score, Mario, stage-1 bests).
v2 reads (v77 on: every read, compact): the placement of attempt A (default the last one, the one that locked or the
last re-read); v76 captures (no-locks only, the placed frames as 640x480 JPEG) as before.
usage: python3 -I capture_u8.py LOG.json OUT [K [A]]   (K: which kept read, default the last; A: which attempt)"""
import sys, json, base64, numpy as np, cv2
log = json.load(open(sys.argv[1])); caps = log.get('chargeCaptures') or []
if not caps: sys.exit('no chargeCaptures in this file')
cap = caps[int(sys.argv[3]) if len(sys.argv) > 3 else -1]
R = np.zeros((52, 480, 640), np.uint8)
def put(k, img): R[k if k >= 0 else 52 + k] = img
if not cap.get('v'):
    meta = {'at': cap['at'], 'base': cap['base'], 'prof': cap['prof'], 'info': cap['info'], 'frames': {}}
    for f in cap['frames']:
        put(f['n'], cv2.imdecode(np.frombuffer(base64.b64decode(f['jpg'].split(',', 1)[1]), np.uint8), cv2.IMREAD_GRAYSCALE))
        meta['frames'][f['n']] = {'t': f['t'], 'm': f['m']}
else:
    fm = cap['fmt']; s, x0, y0, w, h = fm['scale'], fm['x0'], fm['y0'], fm['w'], fm['h']
    def pic(p):
        S = cv2.imdecode(np.frombuffer(base64.b64decode(cap['pics'][p]), np.uint8), cv2.IMREAD_GRAYSCALE).astype(np.float32)
        Y = np.zeros((480, 640), np.float32)
        if s == 1: Y[y0:y0 + h, x0:x0 + w] = S; return Y.round().astype(np.uint8)
        v, u = np.mgrid[0:480, 0:640]; sy = (v + 0.5) / s - 0.5 - y0; sx = (u + 0.5) / s - 0.5 - x0   # charge_reads.js chgPicDecode
        ok = (sy >= -0.5) & (sy <= h - 0.5) & (sx >= -0.5) & (sx <= w - 0.5)
        yy = np.clip(sy, 0, h - 1); xx = np.clip(sx, 0, w - 1); iy = np.minimum(h - 2, np.floor(yy)).astype(int); ix = np.minimum(w - 2, np.floor(xx)).astype(int); fy = yy - iy; fx = xx - ix
        Y = (S[iy, ix] * (1 - fx) + S[iy, ix + 1] * fx) * (1 - fy) + (S[iy + 1, ix] * (1 - fx) + S[iy + 1, ix + 1] * fx) * fy
        return np.where(ok, Y, 0).round().astype(np.uint8)
    F, att = cap['F'], cap.get('attempts') or []
    A = att[int(sys.argv[4]) if len(sys.argv) > 4 else -1] if att else None
    if cap.get('fixed'): G = [None] * 52; [G.__setitem__(e[4] if e[4] >= 0 else 52 + e[4], i) for i, e in enumerate(F) if len(e) > 4 and e[4] is not None]
    else: G = A['G']
    meta = {'id': cap['id'], 'prof': cap['prof'], 'arena': cap.get('arena'), 'trig': cap['trig'], 'result': cap.get('result'), 'attempt': A and {k: A[k] for k in A if k != 'G'}, 'info': cap.get('info'), 'frames': {}}
    for k, i in enumerate(G):
        if i is None or i < 0 or F[i][3] < 0: continue
        n = k if k < 50 else k - 52; put(n, pic(F[i][3])); meta['frames'][n] = {'t': F[i][0], 'm': F[i][1]}
R.tofile(sys.argv[2] + '.u8'); json.dump(meta, open(sys.argv[2] + '.json', 'w'), indent=1)
print('%d frames, %s' % (len(meta['frames']), json.dumps((meta.get('result') or meta['info'] or {}).get('best') if not cap.get('v') else meta.get('result'))))
