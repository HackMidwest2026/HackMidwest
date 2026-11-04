"""A Charge capture the page kept in a saved session log (a no-lock with Mario seen: chargeCaptures, charge_live.js
chgKeepCapture) -> the game-frame rasters harness.c and jsmaps.js read: OUT.u8 = 52 x 480 x 640 uint8, frames 0..49,
then -2 and -1 (a frame the page did not place is all zeros), plus OUT.json with each frame's time from the trigger
picture (ms), its brightness and the page's info (seed, score, Mario, stage-1 bests).
usage: python3 -I capture_u8.py LOG.json OUT [K]   (K: which kept capture, default the last)"""
import sys, json, base64, numpy as np, cv2
log = json.load(open(sys.argv[1])); caps = log.get('chargeCaptures') or []
if not caps: sys.exit('no chargeCaptures in this log')
cap = caps[int(sys.argv[3]) if len(sys.argv) > 3 else -1]
R = np.zeros((52, 480, 640), np.uint8); meta = {'at': cap['at'], 'base': cap['base'], 'prof': cap['prof'], 'info': cap['info'], 'frames': {}}
for f in cap['frames']:
    img = cv2.imdecode(np.frombuffer(base64.b64decode(f['jpg'].split(',', 1)[1]), np.uint8), cv2.IMREAD_GRAYSCALE)
    k = f['n'] if f['n'] >= 0 else 52 + f['n']
    R[k] = img; meta['frames'][f['n']] = {'t': f['t'], 'm': f['m']}
R.tofile(sys.argv[2] + '.u8'); json.dump(meta, open(sys.argv[2] + '.json', 'w'), indent=1)
print('%d frames, trigger at %d ms, %s' % (len(cap['frames']), cap['at'], json.dumps(cap['info'].get('best'))))
