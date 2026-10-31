"""pra_01 reverse mirror clip, version 3, with a NEUTRAL second tornado jump. Real inputs, no RAM edits, CountPerOp 1.
From states/pra01_ub_e3.st: walk to (535, -60), hold LEFT to x 510; tornado jump LEFT tilt 40, A 5 frames, A again on
frame 10; 2 frames after landing jump + tornado jump NEUTRAL (A 5 frames, A again on frame 6) -> ledge (~488, 101, -63);
2 frames after landing jump (A 8) with DOWN-LEFT full tilt for 8 frames (start 0-2 frames into the jump), then DOWN.
Peak ~162 over the cave wall, falls under the room, crosses the mirror line, lands south (near cave -> sam_10).
usage: pra01_rmc_v3_neutral_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cpv')
for i in range(150): e.step(0, 0, 0, 2)
raw = '/dev/shm/pmbot/cpv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, mid, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 16), ImageFont.truetype(F % '-Bold', 20)
frames = []
def step(b, sx, sy, title):
    e.step(b, sx, sy, 2)
    path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
    frames.append((path, title, b, sx, sy, player(e), where(e)[:2]))
def sl(tag):
    S = '/dev/shm/pmbot/cpv_%s.st' % tag; e.save(S); e.step(0, 0, 0, 2); e.load(S)
AIR = (3, 4, 5, 6, 8, 15)
e.load('states/pra01_ub_e3.st'); e.step(0, 0, 0, 2)
for f in range(200):
    p = player(e); dx, dz = 535 - p['x'], -60 - p['z']; d = math.hypot(dx, dz)
    if d < 0.5: break
    mag = max(14, min(80, int(d * 10))); step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), '1. walk to (535, -60), north half')
for f in range(60):
    if player(e)['x'] <= 510: break
    step(0, -80, 0, '1. hold LEFT to x 510 (Mario faces left)')
for i in range(8): step(0, 0, 0, '1. wait')
sl('a'); step(0, 0, 0, '1. wait')
for f in range(45):
    step(A if (f < 5 or 10 <= f < 12) else 0, -40, 0, '2. tornado jump: LEFT tilt 40, A 5 frames, A again on frame 10')
    if f > 3 and player(e)['action'] not in AIR: break
sl('b'); step(0, 0, 0, '3. landed sliding on the cliff by the arch')
step(0, 0, 0, '3. wait 1 frame')
for f in range(60):
    step(A if (f < 5 or 6 <= f < 8) else 0, 0, 0, '4. jump + tornado jump: NEUTRAL, A 5 frames, A again on frame 6')
    if f > 3 and player(e)['action'] not in AIR: break
sl('c'); step(0, 0, 0, '5. on the ledge (~488, 101, -63)')
step(0, 0, 0, '5. wait 1 frame')
for f in range(110):
    if f < 8: s, t = (-56, -56), '6. jump (A 8 frames) + DOWN-LEFT full tilt for 8 frames'
    else: s, t = (0, -80), '7. DOWN: over the cave wall, through the cliff, under the room'
    step(A if f < 8 else 0, *s, t)
    if where(e)[:2] != (21, 0):
        for i in range(25): step(0, 0, 0, '8. near side: walks into the near cave -> sam_10')
        break
tmp = '/dev/shm/pmbot/cpv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
W, H, PX = 790, 470, 593
for n, (path, title, b, sx, sy, p, m) in enumerate(frames):
    im = Image.new('RGB', (W, H), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if m == (21, 0):
        dr.text((8, 376), 'x %.1f  z %.1f  y %.1f' % (p['x'], p['z'], p['y']), fill=(255, 255, 255), font=big)
        dr.text((8, 408), 'NORTH of mirror' if p['z'] < 0 else 'SOUTH of mirror', fill=(255, 160, 160) if p['z'] < 0 else (120, 255, 120), font=mid)
    else: dr.text((8, 376), 'loading sam_10', fill=(255, 255, 255), font=big)
    dr.text((8, 444), 'pra_01 RMC v3 (neutral 2nd tornado), JP, CountPerOp 1, real inputs, 30 fps', fill=(160, 160, 160), font=font)
    cx, cy, rad = PX + 98, 110, 70
    dr.text((PX + 14, 14), 'INPUT  frame %d' % n, fill=(200, 200, 200), font=mid)
    dr.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=(150, 150, 150), width=2)
    px_, py_ = cx + sx / 80 * rad, cy - sy / 80 * rad
    dr.line((cx, cy, px_, py_), fill=(230, 230, 230), width=3); dr.ellipse((px_ - 9, py_ - 9, px_ + 9, py_ + 9), fill=(240, 80, 80))
    dr.text((PX + 14, 190), 'stick (%d, %d)' % (sx, sy), fill=(255, 255, 255), font=mid)
    on = bool(b & A)
    dr.rounded_rectangle((PX + 20, 230, PX + 176, 282), radius=10, fill=(70, 120, 255) if on else (45, 45, 45), outline=(70, 120, 255), width=2)
    dr.text((PX + 98, 256), 'A', fill=(0, 0, 0) if on else (70, 120, 255), font=big, anchor='mm')
    im.save(os.path.join(tmp, 'c%05d.png' % n))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', outp, '-filter:v', 'setpts=4.0*PTS', outp.replace('.mp4', '_slow.mp4')], check=True)
south = [f for f in frames if f[6] == (21, 0) and f[5]['z'] > 0.5]
print('wrote', len(frames), 'frames; south-of-mirror frames', len(south), 'max y', max(f[5]['y'] for f in frames if f[6] == (21, 0)))
