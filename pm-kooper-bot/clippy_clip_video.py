"""Video: what clippy does (nok_13 south stumps). From the post-flee clippy state (counter -1, made by
clippy_natural.py + one more Run Away, no position edits) Mario walks to (-520, 50) and holds west-north-west (world
yaw 285) with a spin every 30 game frames. Clippy: pinned 13 units deeper into the y 50 stump's side, the spin pushes
him into it, step-up, falls through the floor, void respawn. Control: the same run with the counter written back to 0
(pinned outside, nothing happens). usage: clippy_clip_video.py STATE OUT.mp4"""
import math, os, subprocess, sys
from emu import *
from pm import *
from nav import stick_world
from PIL import Image, ImageDraw, ImageFont
st0, outp = sys.argv[1], sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ccv')
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
AN = {0: 'idle', 1: 'walk', 2: 'run', 8: 'fall', 26: 'spin', 34: 'step up'}
tmp = '/dev/shm/pmbot/ccv_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
n = 0
for cnt, title in ((-1, 'CLIPPY (collision counter -1)'), (0, 'CONTROL: same inputs, counter set back to 0')):
    e.load(st0)
    if cnt == 0: e.w8(PLAYER + 0x14, 0)
    for f in range(250):
        p = player(e)
        if math.hypot(-520 - p['x'], 50 - p['z']) < 4: break
        s = stick_world(e, math.degrees(math.atan2(-520 - p['x'], -(50 - p['z']))) % 360); e.step(0, s[0], s[1], 2)
    e.step(0, 0, 0, 30)
    for f in range(110):
        s = stick_world(e, 285); b = Z if f % 30 == 0 else 0
        e.step(b, s[0], s[1], 2)
        path = '/dev/shm/pmbot/ccv_raw.png'
        subprocess.run(['import', '-window', 'root', path], check=True)
        p = player(e)
        im = Image.new('RGB', (593, 450), (20, 20, 20))
        im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
        dr = ImageDraw.Draw(im)
        dr.text((6, 4), 'nok_13 stumps: ' + title, fill=(255, 220, 120) if cnt < 0 else (180, 200, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        dr.text((10, 300), ('Z (spin) + ' if b else '') + 'hold west-north-west', fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
        dr.text((8, 370), 'frame %d  %s  Mario (%.1f, %.1f, %.1f)' % (f, AN.get(p['action'], p['action']), p['x'], p['y'], p['z']), fill=(255, 255, 255), font=font)
        dr.text((8, 392), 'collision counter %d  (push-out of overlapping walls %s while moving)' % (e.s8(PLAYER + 0x14), 'SKIPPED' if e.s8(PLAYER + 0x14) else 'on'), fill=(120, 255, 120) if cnt < 0 else (200, 200, 200), font=font)
        dr.text((8, 414), 'clippy state reached with no position edits (Lucky Star + Spike Shield only)' if cnt < 0 else 'control only: counter written to 0', fill=(160, 160, 160), font=font)
        im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
    for r in range(20): im.save(os.path.join(tmp, 'c%05d.png' % n)); n += 1
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, n)
