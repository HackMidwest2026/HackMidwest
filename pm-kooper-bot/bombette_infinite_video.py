"""Video of the infinite Bombette post-blast state (kmr_11 strip behind Bush2, see bombette_infinite.py).
Records: C-down, Mario walks off the void edge 26 game frames later, falls, respawns; Bombette ends her flight below
the strip and keeps falling; Mario walks/jumps around and presses START (nothing opens); then a 2000-frame skip and
more footage. Overlay: partner action state, Bombette y, Mario position/action.
usage: bombette_infinite_video.py OUT.mp4 [STATE X Y Z FACE OFF W TITLE]  (defaults: the kmr_11 setup)"""
import os, subprocess, sys
from emu import *
from pm import *
from PIL import Image, ImageDraw, ImageFont
from nav import stick_world

PSTAT = 0x8010ED70
outp = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/binfvid')
raw = '/dev/shm/pmbot/binfvid_raw'; os.makedirs(raw, exist_ok=True)
for fn in os.listdir(raw): os.remove(os.path.join(raw, fn))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
font, big = ImageFont.truetype(F % '', 14), ImageFont.truetype(F % '-Bold', 20)
STATES = {0: 'NONE (normal)', 1: 'USE (lit, walking)', 2: 'BOMBETTE_2 (blast)', 3: 'BOMBETTE_3 (post-blast window)'}
ACT = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 8: 'fall', 9: 'step down', 10: 'land', 26: 'spin'}
frames, n = [], [0]
def bomb():
    b = [x for x in npcs(e) if x['id'] == -4]
    return b[0] if b else {'x': 0, 'y': 0, 'z': 0}
def step(b, sx, sy, label, note=''):
    e.step(b, sx, sy, 2)
    path = os.path.join(raw, 'f%05d.png' % n[0]); n[0] += 1
    subprocess.run(['import', '-window', 'root', path], check=True)
    s = e.s8(PSTAT); bo = bomb(); p = player(e)
    frames.append((path, label, note, s, bo['y'], p))
GENERIC = len(sys.argv) > 2
if GENERIC:
    STATE = sys.argv[2]; X, Y, Z, FACE, OFF = (float(a) for a in sys.argv[3:8]); W = int(sys.argv[8]); TITLE = sys.argv[9]
    e.load(STATE); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, X); e.wf32(PLAYER + PS_POS + 4, Y); e.wf32(PLAYER + PS_POS + 8, Z)
    e.step(0, 0, 0, 360); e.step(0, *stick_world(e, FACE), 2); e.step(0, 0, 0, 240)
else:
    TITLE = 'kmr_11: Bombette stuck falling forever (infinite post-blast window)'; W = 26
    e.load('states/kmr11_e0_bombette.st'); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, -230.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, 10.0)
    e.step(0, 0, 0, 40); e.step(0, -80, 0, 2); e.step(0, 0, 0, 10)
step(D_CBUTTON, 0, 0, 'C-DOWN', 'light Bombette (she walks west)')
for f in range(200):
    if W <= f < W + 40:
        st = stick_world(e, OFF) if GENERIC else (56, -56)
        step(0, *st, 'WALK OFF', 'walk off the void edge %d frames after C-down' % W)
    elif f < W: step(0, 0, 0, '', 'wait')
    else: step(0, 0, 0, '', 'Mario falls, respawns at his last safe spot; Bombette keeps falling below')
for g in range(60): step(0, *((stick_world(e, FACE) if GENERIC else (-80, 0)) if g < 40 else (0, 0)), 'MOVE' if g < 40 else '', 'Mario is free; partner still "in use"')
for g in range(30): step(A if g < 8 else 0, 0, 0, 'A' if g < 8 else '', 'jump')
step(START, 0, 0, 'START', 'pause menu does not open')
for g in range(30): step(0, 0, 0, '', 'pause menu does not open')
step(R_CBUTTON, 0, 0, 'C-RIGHT', 'partner menu does not open')
for g in range(30): step(0, 0, 0, '', 'partner menu does not open')
e.step(0, 0, 0, 4000)                                   # skip 2000 game frames
for g in range(60): step(0, *((stick_world(e, FACE + 90) if GENERIC else (80, 0)) if g < 30 else (0, 0)), 'MOVE' if g < 30 else '', '2000 game frames (67 s) later: still BOMBETTE_3')
tmp = '/dev/shm/pmbot/binfvid_frames'; os.makedirs(tmp, exist_ok=True)
for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
for i, (path, label, note, s, by, p) in enumerate(frames):
    im = Image.new('RGB', (593, 470), (20, 20, 20))
    im.paste(Image.open(path).crop((103, 96, 696, 460)).convert('RGB'), (0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), TITLE, fill=(255, 220, 120), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if label: dr.text((10, 300), label, fill=(255, 255, 120), font=big, stroke_width=3, stroke_fill=(0, 0, 0))
    col = (120, 255, 120) if s == 3 else (255, 255, 255)
    dr.text((8, 368), 'partner action state: %d %s' % (s, STATES.get(s, '')), fill=col, font=font)
    dr.text((8, 388), 'Bombette y %.1f' % by, fill=col, font=font)
    dr.text((8, 408), 'Mario (%.1f, %.1f, %.1f) %s' % (p['x'], p['y'], p['z'], ACT.get(p['action'], p['action'])), fill=(255, 255, 255), font=font)
    dr.text((8, 430), note, fill=(180, 180, 180), font=font)
    im.save(os.path.join(tmp, 'c%05d.png' % i))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(tmp, 'c%05d.png'), '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '20', outp], check=True)
print('wrote', outp, len(frames), 'frames; final state', frames[-1][3], 'bomb y', frames[-1][4])
