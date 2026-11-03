"""Mario's reference patch for the page's FB2 Charge profile (charge_live/mario_ref_fb2.json, same layout as
mario_ref.json): the 640x480 game raster (charge_live.js chgGrab: CHG_MAP0, luma) of the picture showing rays frame -1
(confirm + 12) in a simulated capture (t6_capsim.py) of an emulator T6 render, raster x 160..319, y 236..355.
usage: python3 t6_marioref.py CAPTURE.mkv CAPTURE.json SHOT0 OUT.json   (SHOT0 = t6_render.py log 'shot0')"""
import sys, json, base64, subprocess, numpy as np, cv2
mkv, js, s0, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
J = json.load(open(js)); want = s0 + 13                       # the screenshot after logic frame 12 + 1 shows frame 12
c = J['shown'].index(want - J['first'])
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', mkv, '-vf', 'select=eq(n\\,%d)' % c, '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, check=True).stdout
F = np.frombuffer(p, np.uint8).reshape(720, 1280, 3).astype(np.float32)
SX, OX, SY, OY = 3.2637, 272.82, 3.3221, -31.09
ys, xs = np.mgrid[0:480, 0:640].astype(np.float32)
Y = 0.299 * F[..., 0] + 0.587 * F[..., 1] + 0.114 * F[..., 2]
G = cv2.remap(Y, (xs / 2 * SX + OX).astype(np.float32), (ys / 2 * SY + OY).astype(np.float32), cv2.INTER_LINEAR)   # as charge_live/tools/gameframes.py
P = np.clip(np.round(G[236:356, 160:320]), 0, 255).astype(np.uint8)
json.dump({'y0': 236, 'x0': 160, 'h': 120, 'w': 160, 'b64': base64.b64encode(P.tobytes()).decode(),
           'note': 'Mario before the FB2 T6 Charge (frame -1, game raster 640x480 luma): emulator render through the capture simulation (fb2_route/t6_marioref.py)'}, open(out, 'w'))
cv2.imwrite(out.replace('.json', '.png'), P); print('capture frame', c, 'patch mean', round(float(P.mean()), 1))
