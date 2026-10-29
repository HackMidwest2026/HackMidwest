"""Video of pra02_block_clip.py (the real-input reverse mirror clip). Run on Xvfb with a video plugin, e.g.
Xvfb :99 -screen 0 800x600x24 & DISPLAY=:99 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so
usage: pra02_block_clip_video.py OUT.mp4 [rta] (also writes OUT_slow.mp4: the jumps onto the block and the clip at 1/4 speed)
"rta" records pra02_block_clip_rta.py (fixed stick angle, full jump, 4 frames on the floor, short hop) instead."""
import os, sys, subprocess
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
import pra02_block_clip as B
outp = sys.argv[1]
RTA = len(sys.argv) > 2 and sys.argv[2] == 'rta'
if RTA: import pra02_block_clip_rta as R
raw = '/dev/shm/pmbot/bcv_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
frames = []
class Rec:
    def __init__(self, e): self.e, self.n, self.label, self.every, self.slow = e, 0, 'setup', 4, False
    def __getattr__(self, k): return getattr(self.e, k)
    def step(self, b=0, x=0, y=0, n=1):
        self.e.step(b, x, y, n); self.n += 1
        p = player(self.e)
        if p['x'] > 975 - 4 and self.label.startswith('2'): pass
        if self.n % self.every == 0 or self.slow:
            path = os.path.join(raw, 'f%05d.png' % len(frames)); subprocess.run(['import', '-window', 'root', path], check=True)
            l = B.laki(); frames.append((path, self.label, b, x, y, p, l['x'], l['z'], B.spd(), self.slow))
e = Rec(Emu('pm-jp.z64', '/dev/shm/pmbot/bcv'))
for i in range(150): e.e.step(0, 0, 0, 2)
B.e = e
if RTA: R.e = e
HOPS = '3. stick held at 55 deg: full jump, 4 frames on the floor, short hop (A held 5)' if RTA else '3. run 10 frames, then short hops (A held 5) onto the switch block'
def log(s):
    print(s, flush=True)
    if s.startswith('push end'): e.label, e.every, e.slow = HOPS, 1, True
    elif ' on the switch block' in s: e.label = '4. C-down on the first frame standing on the block'
    elif 'C-down' in s: e.label = '5. the mount carries Mario through the mirror'
orig_go = B.go
def go(*a, **k):
    if e.label == 'setup': e.label = '1. corner approach: Lakilester ends facing 315'
    elif e.label.startswith('1'): e.label, e.every = '2. push him east past both pillars (every 8th frame)', 8
    return orig_go(*a, **k)
B.go = go
if RTA: R.go = go
ok = R.route(first=4, log=log) if RTA else B.route(log=log)
tmp = '/dev/shm/pmbot/bcv_frames'; os.makedirs(tmp, exist_ok=True)
def render(sel, out, fps):
    for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
    for n, (path, title, b, sx, sy, p, lx, lz, sp, slow) in enumerate(sel):
        im = Image.new('RGB', (593, 470), (20, 20, 20))
        im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
        dr = ImageDraw.Draw(im)
        dr.text((6, 4), title, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        btn = ('A ' if b & A else '') + ('C-DOWN' if b & D_CBUTTON else '')
        dr.text((8, 372), 'Mario (%.1f, %.1f, %.1f)  stick (%d, %d) %s' % (p['x'], p['y'], p['z'], sx, sy, btn), fill=(255, 255, 255), font=big)
        dr.text((8, 404), 'Lakilester (%.0f, %.0f)  speed %.1f' % (lx, lz, sp), fill=(120, 255, 120) if sp >= 220 else (255, 255, 255), font=big)
        dr.text((8, 444), 'pra_02 reverse mirror clip; real inputs, no RAM edits (block top needs 220)', fill=(160, 160, 160), font=font)
        im.save(os.path.join(tmp, 'c%05d.png' % n))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', out], check=True)
render(frames, outp, 30)
render([f for f in frames if f[9]], outp.replace('.mp4', '_slow.mp4'), 8)
print('wrote', outp, len(frames), 'clip' if ok else 'NO CLIP')
