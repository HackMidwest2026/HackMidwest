"""flo_08 (the user's clip room) test: put Laki at (LX, LY, LZ) with follow state ST (50 = AI off), then Mario walks
left/right in steps like the clip. Captions show Laki's real world x/z next to the star piece (510, 0, -90).
usage: record_laki_flo08.py STATE OUTDIR OUT.mp4 LX LY LZ [ST=50]"""
import math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from PIL import Image, ImageDraw, ImageFont
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
st0, D, outp = sys.argv[1:4]; LX, LY, LZ = map(float, sys.argv[4:7]); ST = int(sys.argv[7]) if len(sys.argv) > 7 else 50
os.makedirs(D, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rf8%d' % os.getpid())
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
n = [0]; rows = []
def shot(tag):
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]
    rows.append((n[0], p['x'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16))
    if not os.environ.get('SHOT'): n[0] += 1; return
    f = os.path.join(D, 'r.png'); subprocess.run(['import', '-window', 'root', f], check=True)
    im = Image.open(f).crop((103, 96, 696, 460)).convert('RGB'); dr = ImageDraw.Draw(im)
    o = lambda xy, s: dr.text(xy, s, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    o((6, 280), 'Laki world x %.1f z %.1f   (star piece x 510)' % (l['x'], l['z']))
    o((6, 300), 'Mario x %.1f z %.1f   Laki follow state %d' % (p['x'], p['z'], e.u32(STATE) >> 16))
    dr.rectangle((0, 334, 593, 364), fill=(0, 0, 0)); o((8, 341), tag)
    im.save(os.path.join(D, 'c%04d.png' % n[0])); n[0] += 1
e.load(st0); e.step(0, 0, 0, 2)
l = [q for q in npcs(e) if q['id'] == -4][0]
e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
e.w16(STATE, ST)
for nm, d, k in (('walk left', 180, 30), ('stand', None, 15), ('walk right', 0, 14), ('stand', None, 15), ('walk left', 180, 20), ('stand', None, 15),
                 ('walk right', 0, 25), ('stand', None, 15), ('walk left', 180, 25), ('stand', None, 20)):
    for i in range(k): e.step(0, *(stick_for(d, 80) if d is not None else (0, 0)), 2); shot('%s (Laki follow state set to %d)' % (nm, ST))
if os.environ.get('SHOT'):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(D, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
for r in rows[::8]: print('%3d M (%6.1f %6.1f)  L (%6.1f %6.1f) st %d' % r)
