"""Video: getting clippy on nok_13 with no position or state edits (only the Lucky Star flag and the Spike Shield
badge are set). Ride Lakilester into the Koopa from the south, C-right on the contact frame, the partner menu stays
open through the battle; Run Away; on the field the menu is still open, pick Goombario: the collision counter
(PlayerStatus+0x14) ends at -1. The Koopa touches Mario again during the swap: run away again, walk off.
Battle stretches are recorded at every 4th game frame. usage: clippy_video.py OUT.mp4"""
import math, os, subprocess, sys
from emu import *
from pm import *
from nav import stick_world
from PIL import Image, ImageDraw, ImageFont
ENC, PSTAT, FREEZE = 0x8009A5E0, 0x8010ED70, 0x8009A5B8
PATH = [(-760, 20), (-650, 20), (-650, -150)]
outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/clvid')
raw = '/dev/shm/pmbot/clvid_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
PN = {1: 'Goombario', 3: 'Bombette', 8: 'Lakilester'}
frames, n = [], [0]
def grab(label, note):
    path = os.path.join(raw, 'f%05d.png' % n[0]); n[0] += 1
    subprocess.run(['import', '-window', 'root', path], check=True)
    frames.append((path, label, note, e.s8(PLAYER + 0x14), int(bool(e.u32(PLAYER) & 0x1000)), e.s8(PLAYER_DATA + 0x12), e.s16(GAME_MODE), e.s32(FREEZE)))
def step(b, sx, sy, label='', note='', every=1, k=[0]):
    e.step(b, sx, sy, 2); k[0] += 1
    if k[0] % every == 0: grab(label, note)
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2)
e.w8(PLAYER_DATA + 0x0A, 1); e.w16(PLAYER_DATA + 0xB4, 229); e.w16(PLAYER_DATA + 0x208, 229)
e.step(0, 0, 0, 30)
step(D_CBUTTON, 0, 0, 'C-DOWN', 'ride Lakilester')
for i in range(30): step(0, 0, 0, '', 'ride Lakilester')
tmp = '/dev/shm/pmbot/clvid_t.st'; k = 0
for f in range(300):
    p = player(e); tx, tz = PATH[k]
    if math.hypot(tx - p['x'], tz - p['z']) < 15 and k < len(PATH) - 1: k += 1
    s = stick_world(e, math.degrees(math.atan2(tx - p['x'], -(tz - p['z']))) % 360)
    e.save(tmp); e.step(0, s[0], s[1], 2)
    if e.s32(ENC) == 3:
        e.load(tmp); step(R_CBUTTON, s[0], s[1], 'C-RIGHT', 'on the frame Mario touches the Koopa'); break
    e.load(tmp); step(0, s[0], s[1], '', 'ride into the Koopa from the south (Mario touches it: no first strike)')
for i in range(80):
    if e.s16(GAME_MODE) == 8: break
    step(0, 0, 0, '', 'partner menu opens during the battle wind-up; leave it open')
for i in range(240): step(0, 0, 0, '', 'battle loads; Laki pre_battle ran: counter 1 -> 0', every=4)
for i in range(2): e.step(0, 0, 70, 4); e.step(0, 0, 0, 20); grab('STRATEGIES', 'run away')
e.step(A, 0, 0, 4); e.step(0, 0, 0, 30); grab('STRATEGIES', 'run away')
for i in range(2): e.step(0, 0, -70, 4); e.step(0, 0, 0, 16); grab('RUN AWAY', 'run away')
step(A, 0, 0, 'RUN AWAY', '')
for f in range(1500):
    if e.s16(GAME_MODE) == 4: break
    step(A if f % 2 == 0 else 0, 0, 0, 'MASH A', 'run away', every=4)
for f in range(400):
    if e.s32(FREEZE) == 3: break
    step(0, 0, 0, '', 'back on the field: the partner menu is still open')
for i in range(20): step(0, 0, 0, '', 'back on the field: the partner menu is still open')
step(0, 0, -80, 'DOWN', 'pick Goombario'); step(0, 0, -80); 
for i in range(6): step(0, 0, 0, '', 'pick Goombario')
step(A, 0, 0, 'A', 'Laki PutAway: still "mounted", collision flag set -> enables again')
for i in range(150):
    step(0, 0, 0, '', 'PutAway re-enables collision a second time: counter 0 -> -1')
    if e.s16(GAME_MODE) == 8: break
if e.s16(GAME_MODE) == 8:
    for i in range(240): step(0, 0, 0, '', 'the Koopa touched Mario again: second battle', every=4)
    for i in range(6): e.step(A, 0, 0, 4); e.step(0, 0, 0, 50); grab('A', "Goombario's first-battle tutorial")
    for i in range(2): e.step(0, 0, 70, 4); e.step(0, 0, 0, 20); grab('STRATEGIES', 'run away')
    e.step(A, 0, 0, 4); e.step(0, 0, 0, 30); grab('STRATEGIES', 'run away')
    for i in range(2): e.step(0, 0, -70, 4); e.step(0, 0, 0, 16); grab('RUN AWAY', 'run away')
    step(A, 0, 0, 'RUN AWAY', '')
    for f in range(1500):
        if e.s16(GAME_MODE) == 4: break
        step(A if f % 2 == 0 else 0, 0, 0, 'MASH A', 'run away', every=4)
    for f in range(600):
        if e.s8(PLAYER + 0x15) == 0: break
        step(0, 0, 0, '', 'field')
for f in range(150):
    p = player(e); s = stick_world(e, math.degrees(math.atan2(-860 - p['x'], -(-35 - p['z']))) % 360)
    step(0, s[0], s[1], 'WALK', 'free to move with the counter at -1 (clippy)')
tmp2 = '/dev/shm/pmbot/clvid_frames'; os.makedirs(tmp2, exist_ok=True)
for fn in os.listdir(tmp2): os.remove(os.path.join(tmp2, fn))
for i, (path, label, note, cnt, nsc, pid, gm, fz) in enumerate(frames):
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), 'nok_13: clippy from a partner menu held through a battle (no position edits)', fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if label: dr.text((10, 300), label, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    col = (120, 255, 120) if cnt < 0 else (255, 255, 255)
    dr.text((8, 368), 'collision counter (PlayerStatus+0x14): %d   NO_STATIC_COLLISION flag: %d' % (cnt, nsc), fill=col, font=font)
    dr.text((8, 388), 'partner: %s   mode: %s   time freeze: %d' % (PN.get(pid, pid), {4: 'field', 8: 'battle'}.get(gm, gm), fz), fill=(255, 255, 255), font=font)
    dr.text((8, 430), note, fill=(180, 180, 180), font=font)
    im.save(os.path.join(tmp2, 'c%05d.png' % i))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp2, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '22', outp], check=True)
print('wrote', outp, len(frames), 'frames; final counter', frames[-1][3], 'partner', frames[-1][5])
