"""Video: pra_18 north->south mirror clip: walk from (610,-60) to (568,-20) leaving Lakilester
behind, C-down on arrival (from pra18_north_gap.py). DIAGNOSTIC SETUP: Mario/Laki start positions
placed in RAM (630,30)/(650,40); every frame after that is real controller input. usage: pra18_zero_video.py OUT.mp4"""
import json, os, subprocess, sys
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zv')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 610.0); e.wf32(PLAYER + PS_POS + 8, -60.0)                 # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 590.0); e.wf32(L['addr'] + 0x40, -60.0)       # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
from nav import go_to
st0 = '/dev/shm/pmbot/zv_n0.st'; e.save(st0); log = []
_step = e.step
def logstep(b, sx, sy, n): log.append((b, sx, sy)); _step(b, sx, sy, n)
e.step = logstep; go_to(e, 568, -20, maxf=300, tol=1.0); e.step = _step; e.load(st0)
rec = {'inputs': log, 'extra_wait': 0}
raw = '/dev/shm/pmbot/zv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 10: 'land', 33: 'ride'}
frames = []
def step(b, sx, sy, title, mark=False):
    e.step(b, sx, sy, 2)
    path = os.path.join(raw, 'f%05d.png' % len(frames))
    subprocess.run(['import', '-window', 'root', path], check=True)
    L = laki()
    frames.append((path, b, sx, sy, title, player(e), e.f32(L['addr'] + 0x18), mark))
for i in range(20): step(0, 0, 0, 'north side of the mirror, on foot')
for b, sx, sy in rec['inputs']: step(b, sx, sy, 'walk down-left to (568, -20); Lakilester lags behind')
for j in range(rec['extra_wait']): step(0, 0, 0, 'stand still')
step(D_CBUTTON, 0, 0, 'C-down on arrival: Laki ~66 away, mount speed set from that gap', mark=True)
for i in range(60): step(0, 0, 0, 'the mount pushes Mario + Laki through the mirror')
tmp = '/dev/shm/pmbot/zv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
def put(im):
    global n; im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
for path, b, sx, sy, title, p, spd, mark in frames:
    im = Image.new('RGB', (593, 450), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if mark: dr.text((10, 300), 'C-DOWN', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((8, 370), 'stick (%d, %d)   Laki speed %.2f' % (sx, sy, spd), fill=(120, 255, 120) if mark else (255, 255, 255), font=big if mark else font)
    side = 'SOUTH of mirror' if p['z'] > 0 else 'NORTH of mirror'
    dr.text((8, 400), 'Mario (%.1f, %.1f, %.1f) %s  -  %s' % (p['x'], p['y'], p['z'], AN.get(p['action'], p['action']), side), fill=(200, 200, 200), font=font)
    dr.text((8, 422), 'pra_18; start positions placed in RAM (setup only), all inputs after are real', fill=(160, 160, 160), font=font)
    put(im)
    if mark:
        for r in range(45): put(im)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n, 'frames; end', frames[-1][5]['x'], frames[-1][5]['z'], frames[-1][5]['action'])
