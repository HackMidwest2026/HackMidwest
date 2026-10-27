"""Video: pra_18 south->north mirror clip with REAL Lakilester speed (no speed written to RAM).
Ride to (644.6, 109.7), dismount (C-down) holding stick (-22, 57) and keep holding it: Mario walks into the pillar's
south face and parks on the clip line; C-down exactly 34 frames after the dismount press, the frame Lakilester's
follow speed spikes. DIAGNOSTIC SETUP ONLY: Mario's start (650,45) is placed in RAM (Clubba 3 parked = defeated);
he then mounts and rides there with real input, which resets Laki's follow history. usage: pra18_sn_video.py OUT.mp4"""
import json, os, subprocess, sys, math
from emu import *
from pm import *
from nav import go_to
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
V = (-22, 57); P = (644.6, 109.7); KC = 34
e = Emu('pm-jp.z64', '/dev/shm/pmbot/snv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
s0 = '/dev/shm/pmbot/snv_0.st'; e.save(s0)
log = []; _step = e.step
def logstep(b, sx, sy, n): log.append((b, sx, sy)); _step(b, sx, sy, n)
e.step = logstep; go_to(e, P[0], P[1], maxf=300, tol=0.6); e.step = _step; e.load(s0)
raw = '/dev/shm/pmbot/snv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 10: 'land', 33: 'ride'}
frames = []
def step(b, sx, sy, title, k=None, mark=False):
    e.step(b, sx, sy, 2)
    path = os.path.join(raw, 'f%05d.png' % len(frames))
    subprocess.run(['import', '-window', 'root', path], check=True)
    Ln = laki(); p = player(e)
    frames.append((path, b, sx, sy, title, k, p, e.f32(Ln['addr'] + 0x18), math.hypot(e.f32(Ln['addr'] + 0x38) - p['x'], e.f32(Ln['addr'] + 0x40) - p['z']), mark))
for b, sx, sy in log: e.step(b, sx, sy, 2)          # ride to the spot off camera (navigation, not part of the trick)

step(D_CBUTTON, *V, 'riding Laki at (644.6, 109.7): C-down to get off, holding (-22, 57)', k=0)
for k in range(1, KC): step(0, *V, 'keep holding (-22, 57): Mario parks on the pillar\'s south face', k=k)
step(D_CBUTTON, 0, 0, 'C-down on frame 34 after getting off (Laki\'s speed spike)', k=KC, mark=True)
for k in range(KC + 1, KC + 60): step(0, 0, 0, 'mount pushes Mario + Lakilester through the mirror', k=k)
tmp = '/dev/shm/pmbot/snv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
for path, b, sx, sy, title, k, p, spd, dist, mark in frames:
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if b & D_CBUTTON: dr.text((10, 300), 'C-DOWN', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), ('frame %d after dismount   ' % k if k is not None else '') + 'stick (%d, %d)' % (sx, sy), fill=(255, 255, 255), font=font)
    dr.text((8, 392), 'Laki speed %.2f   Laki-Mario distance %.1f' % (spd, dist), fill=(120, 255, 120) if mark else (200, 200, 200), font=big if mark else font)
    side = 'SOUTH' if p['z'] > 0 else 'NORTH'
    dr.text((8, 420), 'Mario (%.2f, %.1f, %.2f) %s - %s of mirror' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action']), side), fill=(200, 200, 200), font=font)
    dr.text((8, 444), 'pra_18; start spot placed in RAM (setup), Laki speed NOT edited; all inputs real', fill=(160, 160, 160), font=font)
    put(im)
    if k == 0:
        for r in range(30): put(im)
    if mark:
        for r in range(45): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
last = frames[-1][6]
print('wrote', outp, n, 'frames; end mario', round(last['x'], 1), round(last['z'], 1), 'action', last['action'], 'CLIPPED' if last['z'] < 0 and last['action'] == 33 else 'no clip')
