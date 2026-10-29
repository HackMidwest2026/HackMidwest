"""Full-speed video of pra02_block_clip_rta.py with an input display: every game frame is captured (30 fps), from
states/pra02_back_left.st through the corner approach, the push, the hops onto the switch block and the clip.
Run on Xvfb with a video plugin (see pra02_block_clip_video.py). usage: pra02_block_clip_rta_video.py OUT.mp4"""
import os, sys, math, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
import pra02_block_clip as BC
import pra02_block_clip_rta as R
outp = sys.argv[1]
raw = '/dev/shm/pmbot/rvf_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, mid, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 16), ImageFont.truetype(F % '-Bold', 22)
frames = []
class Rec:
    def __init__(self, e): self.e, self.label = e, '1. walk to (130, -80), wait, hold up-left into the corner'
    def __getattr__(self, k): return getattr(self.e, k)
    def step(self, b=0, x=0, y=0, n=1):
        self.e.step(b, x, y, n)
        path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
        p = player(self.e); l = BC.laki()
        frames.append((path, self.label, b, x, y, p, BC.spd()))
e = Rec(Emu('pm-jp.z64', '/dev/shm/pmbot/rvf'))
for i in range(150): e.e.step(0, 0, 0, 2)
R.e = e; BC.e = e
ngo = [0]
def go(*a, **k):
    ngo[0] += 1
    if ngo[0] == 2: e.label = '2. line up behind Lakilester and push him east past both pillars'
    return BC.go(*a, **k)
R.go = go
def log(s):
    print(s, flush=True)
    if s.startswith('push end'): e.label = '3. stop at Laki x 930; hold stick 55 deg down-left; full jump'
    elif 'landed on the floor' in s: e.label = '4. exactly 4 frames on the floor'
    elif 'short hop' in s: e.label = '5. short hop: A held exactly 5 frames, onto the switch block'
    elif 'on the switch block' in s: e.label = '6. C-down on the first frame standing on the block'
    elif 'C-down' in s: e.label = '7. the mount carries Mario through the mirror'
ok = R.route(first=4, log=log)
for i in range(30): e.step(0, 0, 0, 2)
tmp = '/dev/shm/pmbot/rvf_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
W, H, PX = 790, 470, 593
for n, (path, title, b, sx, sy, p, sp) in enumerate(frames):
    im = Image.new('RGB', (W, H), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.text((8, 372), 'Mario (%.1f, %.1f, %.1f)' % (p['x'], p['y'], p['z']), fill=(255, 255, 255), font=big)
    dr.text((8, 404), 'Lakilester speed %.1f' % sp, fill=(120, 255, 120) if sp >= 220 else (255, 255, 255), font=big)
    dr.text((8, 444), 'pra_02 reverse mirror clip, RTA route; real inputs, no RAM edits, 30 fps', fill=(160, 160, 160), font=font)
    # input display: stick gate, stick position, A and C-down
    cx, cy, rad = PX + 98, 110, 70
    dr.text((PX + 14, 14), 'INPUT  frame %d' % n, fill=(200, 200, 200), font=mid)
    dr.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=(150, 150, 150), width=2)
    dr.line((cx - rad, cy, cx + rad, cy), fill=(70, 70, 70)); dr.line((cx, cy - rad, cx, cy + rad), fill=(70, 70, 70))
    px_, py_ = cx + sx / 80 * rad, cy - sy / 80 * rad
    dr.line((cx, cy, px_, py_), fill=(230, 230, 230), width=3); dr.ellipse((px_ - 9, py_ - 9, px_ + 9, py_ + 9), fill=(240, 80, 80))
    dr.text((PX + 14, 190), 'stick (%d, %d)' % (sx, sy), fill=(255, 255, 255), font=mid)
    for i, (name, bit, col) in enumerate((('A', A, (70, 120, 255)), ('C-DOWN', D_CBUTTON, (255, 210, 40)))):
        y0 = 230 + i * 70; on = bool(b & bit)
        dr.rounded_rectangle((PX + 20, y0, PX + 176, y0 + 52), radius=10, fill=col if on else (45, 45, 45), outline=col, width=2)
        dr.text((PX + 98, y0 + 26), name, fill=(0, 0, 0) if on else col, font=big, anchor='mm')
    im.save(os.path.join(tmp, 'c%05d.png' % n))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, len(frames), 'frames', 'clip' if ok else 'NO CLIP')
