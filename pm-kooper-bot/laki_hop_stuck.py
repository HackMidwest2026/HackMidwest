"""Hypothesis test for the early-Laki drift: Laki stuck in follow state 2 (the hop) because its landing height
(moveToPos.y) is far below him. Sets state 2, moveToPos.y = MTY, jumpScale = JS, jumpVel = JV, moveSpeed = SPD,
yaw = YAW, then Mario stands / walks; logs Laki every 10 frames. usage: laki_hop_stuck.py STATE MTY JS JV SPD YAW [SCRIPT]
env SHOT=1 OUTDIR=dir OUT=x.mp4 records a captioned video."""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
st0 = sys.argv[1]; MTY, JS, JV, SPD, YAW = map(float, sys.argv[2:7])
SCRIPT = sys.argv[7] if len(sys.argv) > 7 else 's:60,0:30,s:40,180:30,s:60'
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lhs%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
e.wf32(a + 0x60 + 4, MTY); e.wf32(a + 0x14, JS); e.wf32(a + 0x1C, JV); e.wf32(a + 0x18, SPD); e.wf32(a + 0x0C, YAW)
e.w16(STATE, 2)
f = 0
for part in SCRIPT.split(','):
    d, k = part.split(':')
    for i in range(int(k)):
        e.step(0, *(stick_for(float(d), 80) if d != 's' else (0, 0)), 2); f += 1
        if os.environ.get('SHOT'):
            p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]; D = os.environ['OUTDIR']; os.makedirs(D, exist_ok=True)
            subprocess.run(['import', '-window', 'root', os.path.join(D, 'r.png')], check=True)
            im = Image.open(os.path.join(D, 'r.png')).crop((103, 96, 696, 460)).convert('RGB'); dr = ImageDraw.Draw(im)
            ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
            o = lambda xy, s: dr.text(xy, s, fill=(255, 255, 255), font=ft, stroke_width=2, stroke_fill=(0, 0, 0))
            o((6, 262), 'Laki world x %.1f  y %.1f   (Mario x %.1f)' % (l['x'], l['y'], p['x']))
            o((6, 280), 'follow state %d (hop)  hop speed %.2f  jumpScale %.1f  jumpVel %.1f' % (e.u32(STATE) >> 16, l['speed'], e.f32(a + 0x14), e.f32(a + 0x1C)))
            dr.rectangle((0, 334, 593, 364), fill=(0, 0, 0))
            o((8, 341), ('stand' if part.startswith('s') else 'walk ' + {'0': 'right', '180': 'left'}.get(part.split(':')[0], '')) + '  (Laki stuck in the hop, landing height %.0f)' % MTY)
            im.save(os.path.join(D, 'c%04d.png' % (f - 1)))
        if f % 10 == 0:
            p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]
            print('%3d %-5s M (%7.1f %5.1f %6.1f) L (%7.1f %6.1f %6.1f) st %d spd %.2f jv %.2f js %.2f yaw %.0f mty %.0f' % (f, part, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'],
                  e.u32(STATE) >> 16, l['speed'], e.f32(a + 0x1C), e.f32(a + 0x14), e.f32(a + 0x0C), e.f32(a + 0x64)))
if os.environ.get('SHOT'):
    D = os.environ['OUTDIR']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(D, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', os.environ['OUT']], check=True)
