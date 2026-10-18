"""Video of a skewed-entry state (make_state_skew.py): Mario walks left/right/stands in steps like the user's clip;
captions show Mario/Laki world positions, Laki follow state, history pointer/index and speed.
usage: record_skew.py STATE OUTDIR OUT.mp4 [SCRIPT] (SCRIPT = 'd:n,d:n,...' with d = stick angle or s for stand)"""
import math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from PIL import Image, ImageDraw, ImageFont
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE, PTR, IDX = 0x8010D188, 0x8010D17C, 0x8010D178
st0, D, outp = sys.argv[1:4]
SCRIPT = sys.argv[4] if len(sys.argv) > 4 else 's:120,0:40,s:30,180:30,s:30,0:25,s:30,180:45,s:40,0:30,s:40'
os.makedirs(D, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rsk%d' % os.getpid())
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
n = [0]; rows = []
def shot(tag):
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]
    rows.append((n[0], p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, e.u32(PTR), e.u32(IDX), l['speed']))
    if os.environ.get('SHOT'):
        f = os.path.join(D, 'r.png'); subprocess.run(['import', '-window', 'root', f], check=True)
        im = Image.open(f).crop((103, 96, 696, 460)).convert('RGB'); dr = ImageDraw.Draw(im)
        o = lambda xy, s: dr.text(xy, s, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        o((6, 262), 'Mario (%.1f, %.1f, %.1f) action %d' % (p['x'], p['y'], p['z'], p['action']))
        o((6, 280), 'Laki  (%.1f, %.1f, %.1f)' % (l['x'], l['y'], l['z']))
        o((6, 298), 'Laki follow state %d  history ptr %d idx %d  speed %.2f' % (e.u32(STATE) >> 16, e.u32(PTR), e.u32(IDX), l['speed']))
        dr.rectangle((0, 334, 593, 364), fill=(0, 0, 0)); o((8, 341), tag)
        im.save(os.path.join(D, 'c%04d.png' % n[0]))
    n[0] += 1
e.load(st0)
for part in SCRIPT.split(','):
    d, k = part.split(':')
    for i in range(int(k)):
        e.step(0, *(stick_for(float(d), 80) if d != 's' else (0, 0)), 2)
        shot('stand' if d == 's' else 'walk ' + {'0': 'right', '180': 'left', '90': 'down', '270': 'up'}.get(d, d))
if os.environ.get('SHOT'):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(D, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
for r in rows[::10]: print('%3d M (%7.1f %6.1f %6.1f) a%2d | L (%7.1f %6.1f %6.1f) st %d ptr %d idx %d spd %.2f' % r)
