"""Video: pra_18 south->north mirror clip, MIRROR-SLIDE setup with no stick release on any C-down. REAL Lakilester speed.
Ride into the east wall, 4 frames left (Laki x 708), then hold UP into the mirror for 45-80 frames: Laki slides west
~0.023/frame along it and ends at x 706.08-706.88. Tap down 1-4 frames, C-down with the stick neutral, start holding left
any time during the dismount (frames 1-15), and C-down on frame 34 after getting off WITH LEFT STILL HELD.
DIAGNOSTIC SETUP ONLY: Mario's start (690,50) is placed in RAM (east Clubba parked = defeated); everything after is
real input. usage: pra18_sn_mirror_slide.py OUT.mp4"""

import json, os, subprocess, sys, math
from emu import *
from pm import *
from nav import go_to
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
KC = 34
UP = int(os.environ.get('UP', 60)); LS = int(os.environ.get('LS', 6))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lsv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 690.0); e.wf32(PLAYER + PS_POS + 8, 50.0)                      # DIAGNOSTIC start
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
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
for i in range(30): step(0, 40, 16, '1. ride right + slightly up into the east wall')
for i in range(20): step(0, 0, 0, '2. let go: Laki settles at x 732.0')
for i in range(4): step(0, -80, 0, '3. hold full left for exactly 4 frames (x 708)')
for i in range(6): step(0, 0, 0, '3. let go')
for i in range(UP): step(0, 0, 80, '4. hold UP into the mirror 45-80 frames (x 706.1-706.9)')
for i in range(8): step(0, 0, 0, '4. let go')
for i in range(2): step(0, 0, -80, '5. tap down (1-4 frames)')
for i in range(8): step(0, 0, 0, '5. let go')
step(D_CBUTTON, 0, 0, '6. C-down to get off (stick neutral)', k=0)
for k in range(1, KC): step(0, 0 if k < LS else -80, 0, '7. hold left (start any time in the dismount)', k=k)
step(D_CBUTTON, -80, 0, '8. C-down on frame 34, LEFT STILL HELD', k=KC, mark=True)
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
    if len(frames) and path == frames[0][0]:
        for r in range(20): put(im)
    if mark:
        for r in range(45): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
last = frames[-1][6]
print('wrote', outp, n, 'frames; end mario', round(last['x'], 1), round(last['z'], 1), 'action', last['action'], 'CLIPPED' if last['z'] < 0 and last['action'] == 33 else 'no clip')
