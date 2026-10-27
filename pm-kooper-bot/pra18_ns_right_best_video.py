"""Video: the closest RIGHT-SIDE (east of statue 2) north->south Lakilester-push attempt from the pra18_ns_push.py search
(push angle 200, 70 cycles of walk 2 frames at stick 35 / stand 2 frames). Mario + Laki start in the north side's
bottom-right corner, Mario pushes Laki up-left, then walks to the clip spot and presses C-down on the frame where Laki's
speed peaks there. No clip (speed far below the 42/44/46 needed).
DIAGNOSTIC SETUP: Mario placed at (700, -25), mounts, rides into the corner, gets off (fresh history); everything after
is real input; Laki's speed is never written. usage: pra18_ns_right_best_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
A, C, (mag, wlk, stand) = 200, 70, (35, 2, 2)
TARGETS = [(574, -14), (572, -15), (570, -16)]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nrv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, m: (int(round(m * math.cos(math.radians(deg)))), -int(round(m * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 700.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/nrv_0.st'; e.save(b0)
# plan: inputs list, then find the walk target + C-down frame with the highest Laki speed on the clip spot
plan = [(0, 80, -40, '1. ride into the bottom-right corner')] * 30 + [(D_CBUTTON, 80, 0, '2. get off facing right')] \
     + [(0, 0, 0, '2. get off facing right')] * 60
for k in range(C):
    plan += [(0, *st(A, mag), '3. stop-and-go push Laki up-left (walk 2 / stand 2) x%d' % C)] * wlk
    plan += [(0, 0, 0, '3. stop-and-go push Laki up-left (walk 2 / stand 2) x%d' % C)] * stand
for b, x, y, _ in plan: e.step(b, x, y, 2)
after = '/dev/shm/pmbot/nrv_a.st'; e.save(after)
best = (-1,)
for T in TARGETS:
    e.load(after); walk = []
    for f in range(70):
        q = player(e); dd = math.hypot(q['x'] - T[0], q['z'] - T[1])
        if dd > 1.2:
            ang = math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])); s = st(ang, 80 if dd > 6 else 25)
        else: s = (0, 0)
        e.step(0, *s, 2); walk.append(s); q = player(e); sp = L()[2]
        if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12 and sp > best[0]:
            best = (sp, T, list(walk))
print('best speed on the clip spot %.2f walking to %s, C-down after %d walk frames' % (best[0], best[1], len(best[2])), flush=True)
for s in best[2]: plan.append((0, *s, '4. walk to the clip spot (%d, %d)' % best[1]))
plan.append((D_CBUTTON, 0, 0, '5. C-down on the frame Laki is fastest there'))
nC = len(plan) - 1
plan += [(0, 0, 0, 'result')] * 45
# record
e.load(b0)
raw = '/dev/shm/pmbot/nrv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 10: 'land', 33: 'ride'}
frames = []; spC = None
for i, (b, x, y, title) in enumerate(plan):
    e.step(b, x, y, 2)
    path = os.path.join(raw, 'f%05d.png' % i)
    subprocess.run(['import', '-window', 'root', path], check=True)
    p = player(e); lx, lz, sp = L()
    if i == nC: spC = sp
    frames.append((path, b, x, y, title, p, sp, math.hypot(lx - p['x'], lz - p['z']), i == nC - 1))
tmp = '/dev/shm/pmbot/nrv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
for j, (path, b, x, y, title, p, sp, dist, mark) in enumerate(frames):
    if j < 25: continue                                              # skip most of the ride-in
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if b & D_CBUTTON: dr.text((10, 300), 'C-DOWN', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), 'stick (%d, %d)   need Laki speed 42/44/46 here' % (x, y), fill=(255, 255, 255), font=font)
    dr.text((8, 392), 'Laki speed %.2f   Laki-Mario distance %.1f' % (sp, dist), fill=(255, 140, 120) if mark else (200, 200, 200), font=big if mark else font)
    side = 'SOUTH' if p['z'] > 0 else 'NORTH'
    dr.text((8, 420), 'Mario (%.1f, %.1f, %.1f) %s - %s of mirror' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action']), side), fill=(200, 200, 200), font=font)
    dr.text((8, 444), 'pra_18 closest right-side push; start placed in RAM, Laki speed NOT edited', fill=(160, 160, 160), font=font)
    put(im)
    if mark:
        for r in range(45): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
last = frames[-1][5]
print('wrote', outp, n, 'frames; speed at C-down frame', frames[nC - 1][6], 'end mario', round(last['x'], 1), round(last['z'], 1), last['action'])
