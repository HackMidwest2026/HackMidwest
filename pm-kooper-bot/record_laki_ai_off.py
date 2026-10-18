"""Reference video for the "early Laki" movement: mac_01 start, set Lakilester's follow state to 50 (AI off, as the
joining cutscene leaves it until EnablePartnerAI), then walk away, walk into him, walk away, C-down.
SHOT=1 screenshots; then captions and encodes OUT.mp4. usage: record_laki_ai_off.py STATE OUTDIR OUT.mp4"""
import math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from PIL import Image, ImageDraw, ImageFont
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
st0, D, outp = sys.argv[1:4]; os.makedirs(D, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rao%d' % os.getpid())
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
n = [0]
def shot(tag):
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]
    f = os.path.join(D, 'r.png'); subprocess.run(['import', '-window', 'root', f], check=True)
    im = Image.open(f).crop((103, 96, 696, 460)).convert('RGB'); dr = ImageDraw.Draw(im)
    o = lambda xy, s: dr.text(xy, s, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    o((6, 300), 'Laki follow state %d   dist to Mario %.0f' % (e.u32(STATE) >> 16, math.hypot(p['x'] - l['x'], p['z'] - l['z'])))
    dr.rectangle((0, 334, 593, 364), fill=(0, 0, 0)); o((8, 341), tag)
    im.save(os.path.join(D, 'c%04d.png' % n[0])); n[0] += 1
e.load(st0); e.step(0, 0, 0, 2)
for i in range(20): e.step(0, 0, 0, 2); shot('normal: Laki idle next to Mario')
e.w16(STATE, 50)
for nm, d, k in (('AI off (state 50): walk away, Laki stays put', 90, 40), ('stand', None, 20), ('walk back into Laki: only the collision push moves him', 270, 44),
                 ('walk sideways along him', 0, 12), ('walk sideways along him', 180, 12), ('walk away again', 90, 40), ('stand', None, 15)):
    for i in range(k): e.step(0, *(stick_for(d, 80) if d is not None else (0, 0)), 2); shot(nm)
e.step(0x0400, 0, 0, 2); shot('C-down: the ability still works')
for i in range(75): e.step(0, 0, 0, 2); shot('C-down: the ability still works')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(D, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print(n[0], 'frames ->', outp)
