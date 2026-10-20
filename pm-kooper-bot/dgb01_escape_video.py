"""Record + caption the dgb_01 2F-east escape attempt (boosted Laki dismount hop + PutAway railing snap).
Starts from states/dgb01_e4_ctrl.st (first controllable frame after re-entering from dgb_08), pokes Ultra Boots and
Goombario/Kooper/Bombette into RAM, plays SEQ (tokens like esc_try: DIR:k, hDIR:k half tilt, BTN[+BTN]:DIR:k),
screenshots every game frame (Xvfb :99 + video plugin) and builds a captioned mp4 with a side view (z vs y) of the
back railing.  usage: dgb01_escape_video.py OUTDIR OUT.mp4 'title' 'SEQ'"""
import json, os, subprocess, sys
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont

BTN = {'A': A, 'B': B, 'Z': Z, 'CD': D_CBUTTON, 'CR': R_CBUTTON, 'S': START}
DIRS = {'u': (0, 80), 'd': (0, -80), 'l': (-80, 0), 'r': (80, 0), 'n': (0, 0),
        'hu': (0, 40), 'hd': (0, -40), 'hl': (-40, 0), 'hr': (40, 0)}
NAMES = {'CD': 'C-DOWN', 'CR': 'C-RIGHT', 'A': 'A', 'B': 'B', 'S': 'START'}
DNAME = {'u': 'UP', 'd': 'DOWN', 'l': 'LEFT', 'r': 'RIGHT', 'n': '', 'hu': 'half UP', 'hd': 'half DOWN', 'hl': 'half LEFT', 'hr': 'half RIGHT'}
out, outp, title, seq = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/escvid')
e.load('states/dgb01_e4_ctrl.st')
e.w8(PLAYER_DATA, 2)                                   # ultra boots
for p in (1, 2, 3, 8): e.w8(PLAYER_DATA + 0x14 + 8 * p, 1)
log = []
vi = 0
for tok in seq.split():
    parts = tok.split(':')
    btn, label = 0, ''
    if len(parts) == 3:
        for b in parts[0].split('+'): btn |= BTN[b]
        label = ' + '.join(NAMES[b] for b in parts[0].split('+'))
        parts = parts[1:]
    d, k = parts[0], int(parts[1])
    inp = ' + '.join(s for s in (label, DNAME[d]) if s)
    for i in range(k):
        e.step(btn, *DIRS[d], 1); vi += 1
        if vi % 2: continue
        p = player(e)
        t = [n for n in npcs(e) if n['id'] == 4]
        i_ = len(log)
        subprocess.run(['import', '-window', 'root', os.path.join(out, 'f%04d.png' % i_)], check=True)
        log.append({'i': i_, 'inp': inp, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'],
                    'partner': e.s8(PLAYER_DATA + 0x12), 'mode': e.s16(GAME_MODE),
                    'tx': t[0]['x'] if t else 0, 'tz': t[0]['z'] if t else 0})
json.dump(log, open(os.path.join(out, 'log.json'), 'w'))

F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, small, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '', 12), ImageFont.truetype(F % '-Bold', 22)
W, H = 1020, 430
PN = {1: 'Goombario', 2: 'Kooper', 3: 'Bombette', 8: 'Lakilester'}
def S(z, y): return (612 + (z + 110) * 1.8, 330 - (y - 210) * 2.2)   # side view: z right (toward camera), y up
maxy = 0
tmp = os.path.join(out, 'c'); os.makedirs(tmp, exist_ok=True)
for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
for n, l in enumerate(log):
    maxy = max(maxy, l['y'])
    im = Image.new('RGB', (W, H), (20, 20, 20))
    g = Image.open(os.path.join(out, 'f%04d.png' % l['i'])).crop((103, 96, 696, 460)).convert('RGB')
    im.paste(g, (0, 0)); dr = ImageDraw.Draw(im)
    dr.text((6, 4), title, fill=(255, 220, 120), font=small, stroke_width=2, stroke_fill=(0, 0, 0))
    if l['inp']: dr.text((10, 300), l['inp'], fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    dr.text((10, 334), 'Mario (%.1f, %.1f, %.1f)  action %d  partner %s' % (l['x'], l['y'], l['z'], l['act'], PN.get(l['partner'], l['partner'])),
            fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    dr.rectangle((600, 22, 1014, 380), fill=(250, 250, 248), outline=(120, 120, 120))
    dr.text((604, 24), 'side view at x~445: z right (toward camera), y up', fill=(90, 90, 90), font=small)
    dr.rectangle(S(-99, 285) + S(-74, 210), fill=(150, 110, 80))                     # back railing block
    dr.rectangle(S(74, 285) + S(99, 210), fill=(150, 110, 80))                       # front railing block
    dr.line([S(-74, 210), S(74, 210)], fill=(60, 60, 60), width=3)                   # walkway
    dr.line([S(-110, 285), S(110, 285)], fill=(200, 60, 60), width=1)
    dr.text(S(-60, 292), 'railing top y 285', fill=(200, 60, 60), font=small)
    dr.text(S(-108, 200), 'back railing', fill=(90, 60, 40), font=small)
    dr.text(S(40, 200), 'front railing', fill=(90, 60, 40), font=small)
    m = S(l['z'], l['y'])
    dr.rectangle((m[0] - 13 * 1.8, m[1] - 37 * 2.2, m[0] + 13 * 1.8, m[1]), outline=(40, 110, 220), width=2)
    dr.ellipse((m[0] - 4, m[1] - 4, m[0] + 4, m[1] + 4), fill=(40, 110, 220))
    dr.text((604, 344), 'blue box = Mario (radius 13, height 37); feet dot', fill=(90, 90, 90), font=small)
    dr.text((604, 360), 'peak so far: y %.1f' % maxy, fill=(20, 20, 20), font=font)
    dr.rectangle((0, 392, W, H), fill=(0, 0, 0))
    dr.text((8, 402), 'frame %d (30 fps game frames)' % l['i'], fill=(255, 255, 255), font=font)
    im.save(os.path.join(tmp, 'c%04d.png' % n))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%04d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, len(log), 'frames, peak y %.2f' % maxy)
