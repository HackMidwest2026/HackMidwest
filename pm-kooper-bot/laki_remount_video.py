"""Video of the two remount speed tests from laki_remount_speed.py (isk_11 west -520 floor, holding world direction
DIR the whole time, no RAM edits): A = dismount, keep holding, C-down on frame KA after the dismount press;
B = dismount, Z on the landing frame, A for 1 frame J frames after the spin, C-down K frames after the jump.
Overlay: inputs, Laki's moveSpeed each frame and the speed the mount reads; the C-down frame is repeated slowed.
Record with the Glide64mk2 plugin. usage: laki_remount_video.py OUT.mp4 [KA J K DIR]"""
import math, os, subprocess, sys
from emu import *
from pm import *
from corner_sweep import stick_for
from nav import go_to
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
KA, J, K = (int(a) for a in sys.argv[2:5]) if len(sys.argv) > 4 else (35, 8, 10)
DIR = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lrv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
import os
if os.environ.get('SPEEDY'):                                  # Speedy Spin badge (item 287) owned + equipped (RAM)
    e.w16(PLAYER_DATA + 0xB4, 287); e.w16(PLAYER_DATA + 0x208, 287)
go_to(e, -300, 560, maxf=300); e.step(0, 0, 0, 30)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(60):
    e.step(0, 0, 0, 2)
    if e.u8(PLAYER + PS_ACTION) == 33: break
e.step(0, 0, 0, 30)
st = stick_for(DIR, 80)
for i in range(6): e.step(0, st[0], st[1], 2)
base = '/dev/shm/pmbot/lrv_ride.st'; e.save(base)
raw = '/dev/shm/pmbot/lrv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 26: 'spin', 33: 'ride'}
frames = []
def step(b, label, title, mark=False):
    e.step(b, st[0], st[1], 2)
    path = os.path.join(raw, 'f%05d.png' % len(frames))
    subprocess.run(['import', '-window', 'root', path], check=True)
    frames.append((path, label, title, player(e), e.f32(laki()['addr'] + 0x18), mark))
def run(title, plan, n):
    e.load(base)
    for f in range(1, n + 1):
        b = plan.get(f, 0)
        lab = ' + '.join(x for x, m in (('C-DOWN', D_CBUTTON), ('Z (spin)', Z), ('A (1 frame)', A)) if b & m)
        step(b, lab, title, mark=(b & D_CBUTTON) and f > 1)
    for i in range(30): step(0, '', title)
run('A: dismount, keep holding right, C-down on frame %d' % KA, {1: D_CBUTTON, KA: D_CBUTTON}, KA + 12)
LAND = 17
run('B: dismount, spin on landing, 1-frame jump %d later, C-down %d after the jump' % (J, K), {1: D_CBUTTON, LAND: Z, LAND + J: A, LAND + J + K: D_CBUTTON}, LAND + J + K + 12)
tmp = '/dev/shm/pmbot/lrv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
mount_read = {}
for i, fr in enumerate(frames):
    if fr[5]:
        for j in range(i, min(i + 12, len(frames))):
            if frames[j][3]['action'] == 33: mount_read[i] = frames[j][4]; break
for i, (path, label, title, p, spd, mark) in enumerate(frames):
    im = Image.new('RGB', (593, 450), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if label: dr.text((10, 300), label, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), ('mount reads Laki speed %.2f' % mount_read.get(i, 0.0)) if mark else ('Laki speed %.2f' % spd), fill=(120, 255, 120) if mark else (255, 255, 255), font=big if mark else font)
    dr.text((8, 400), 'Mario (%.0f, %.0f, %.0f) %s' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action'])), fill=(200, 200, 200), font=font)
    dr.text((8, 422), ('Speedy Spin equipped (RAM); ' if os.environ.get('SPEEDY') else '') + 'holding right the whole time; isk_11 west floor', fill=(160, 160, 160), font=font)
    put(im)
    if mark:
        for r in range(30): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames; mount speeds', [round(v, 2) for v in mount_read.values()])
