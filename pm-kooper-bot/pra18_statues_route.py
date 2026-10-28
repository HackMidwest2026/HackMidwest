"""Video: pra_18 both Clubba statues with Ultra Boots from the west door (statue 1 climb, then statue 2). NO RAM writes.
Hold right to the statue face (x 237), hold up into the corner with the north wall (237,-137), hold DOWN; A on run
frame 7 or 8 held 6-7 frames; tornado (A) exactly 8 frames after the first A, switching the stick to RIGHT (or neutral)
on that press. Mario lands on the club (y ~75-76) and stays; A + right jumps over the statue top into the corridor.
Statue 2: hold down into the corridor's bottom-right corner (437,-63), hold UP-RIGHT (Mario pins against the corridor's
north wall at z -85.5), A on any frame from 7 on, held 5-9, tornado 6-10 frames after the first A, keep up-right (a
zeroed stick fails); Mario lands on statue 2's club (437, 69.8, -85.5); A + right clears it into the east section.
usage: pra18_statues_route.py OUT.mp4"""
import json, os, subprocess, sys, math
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s1v')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/snv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 15: 'tornado', 16: 'land', 18: 'hammer', 33: 'ride'}
frames = []
def step(b, sx, sy, title, k=None, mark=False):
    e.step(b, sx, sy, 2)
    path = os.path.join(raw, 'f%05d.png' % len(frames))
    subprocess.run(['import', '-window', 'root', path], check=True)
    Ln = laki(); p = player(e)
    frames.append((path, b, sx, sy, title, k, p, 0.0, 0.0, mark))
J = 7
for i in range(60): step(0, 80, 0, '1. from the door: hold RIGHT until Mario stops at the statue face')
for i in range(40): step(0, 0, 80, '2. hold UP into the corner with the north wall')
for i in range(10): step(0, 0, 0, '2. corner (237, -137)')
for k in range(J): step(0, 0, -80, '3. hold DOWN', k=k)
for k in range(J, J + 6): step(A, 0, -80, '4. A on run frame 7-8, hold A 6-7 frames', k=k)
for k in range(J + 6, J + 8): step(0, 0, -80, '4. keep holding down', k=k)
step(A, 80, 0, '5. TORNADO: A 8 frames after the first A, switch stick to RIGHT', k=J + 8, mark=True)
for k in range(30): step(0, 80, 0, '6. Mario lands on the club and stays (keep right or let go)')
for k in range(12): step(A, 80, 0, '7. A + RIGHT: jump over the statue top')
for k in range(40): step(0, 80, 0, '7. past statue 1, into the corridor')
for k in range(25): step(0, 0, -80, '8. statue 2: hold DOWN into the bottom-right corner')
for k in range(12): step(0, 56, 56, '9. hold UP-RIGHT (pins in the corner)', k=k)
for k in range(12, 18): step(A, 56, 56, '10. A (any frame from 7 on), hold 5-9', k=k)
for k in range(18, 20): step(0, 56, 56, '10. keep holding up-right', k=k)
step(A, 56, 56, '11. TORNADO 6-10 frames after the first A, keep up-right', k=20, mark=True)
for k in range(25): step(0, 56, 56, '12. Mario lands on statue 2\'s club')
for k in range(12): step(A, 80, 0, '13. A + RIGHT: over statue 2')
for k in range(45): step(0, 80, 0, '13. past both statues')
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
    if b & A: dr.text((10, 300), 'A', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), ('frame %d   ' % k if k is not None else '') + 'stick (%d, %d)  %s' % (sx, sy, 'A' if b & A else ''), fill=(255, 255, 255), font=font)
    dr.text((8, 400), 'Mario (%.2f, %.2f, %.2f) %s' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action'])), fill=(120, 255, 120) if p['y'] > 70 else (200, 200, 200), font=big)
    dr.text((8, 444), 'pra_18 from the west door: no RAM writes, all inputs real', fill=(160, 160, 160), font=font)
    put(im)
    if len(frames) and path == frames[0][0]:
        for r in range(20): put(im)
    if mark:
        for r in range(45): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
last = frames[-1][6]
print('wrote', outp, n, 'frames; end mario', round(last['x'], 1), round(last['y'], 1), round(last['z'], 1), 'PAST BOTH STATUES' if last['x'] > 500 else 'not past')
