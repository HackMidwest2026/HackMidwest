"""Video: pra_02 behind the mirror near the right wall: where Mario gets stopped short of the x 979.5-981.5 clip strip.
From the real-input push end (Lakilester pushed to the right wall), (a) walk to (930,-80) and hold right: Mario stops at
x ~969.7; (b) hold right to the wall and then down along it: Mario stops at (987, -112). Then (c) walk right along
z -40: he crosses the strip to the wall, so the strip itself is reachable from the west. No RAM edits.
usage: pra02_stuck_video.py STATE OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
src, outp = sys.argv[1], sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/stv')
for i in range(150): e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/stv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
frames = []
def step(sx, sy, title, show=True):
    e.step(0, sx, sy, 2)
    if show:
        p = player(e); path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
        frames.append((path, title, sx, sy, p))
def go(tx, tz, title, maxf=250, show=False):
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < 0.5: return
        mag = max(14, min(80, int(d * 10)))
        step(int(round(mag * dx / d)), int(round(-mag * dz / d)), title, show and f % 2 == 0)
for part in ('a', 'b', 'c'):
    e.load(src); e.step(0, 0, 0, 2)
    if part == 'a':
        go(930, -80, 'a. walk to (930, -80)', show=True)
        for i in range(30): step(80, 0, 'a. hold RIGHT along z -80: Mario stops at x ~970')
    elif part == 'b':
        for i in range(12): step(80, 0, 'b. hold RIGHT into the right wall')
        for i in range(30): step(0, -80, 'b. hold DOWN along the right wall: stops at z -112')
    else:
        go(930, -40, 'c. walk to (930, -40)', show=True)
        for i in range(20): step(80, 0, 'c. hold RIGHT along z -40: crosses the strip (x 979.5-981.5) to the wall')
    for i in range(20): step(0, 0, '%s. (holding position)' % part)
tmp = '/dev/shm/pmbot/stv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
for n, (path, title, sx, sy, p) in enumerate(frames):
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    strip = 979.5 <= p['x'] <= 981.5 and -68 <= p['z'] <= -13
    dr.text((8, 380), 'Mario (%.2f, %.1f, %.2f)  stick (%d, %d)' % (p['x'], p['y'], p['z'], sx, sy), fill=(255, 255, 255), font=big)
    dr.text((8, 412), 'ON THE CLIP STRIP' if strip else '', fill=(120, 255, 120), font=big)
    dr.text((8, 444), 'pra_02 back side, right end; no RAM edits', fill=(160, 160, 160), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % n))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '20', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, len(frames))
