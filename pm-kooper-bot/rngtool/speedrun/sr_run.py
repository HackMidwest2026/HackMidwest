"""Emulator "speedrun" of the Bowser's Castle C-up rooms for the Time Out Timer page (step 1: the dungeon lock).
Plays each route room in one continuous session (real room loads; DIAGNOSTIC: each exit's destination is redirected
to the next route room by writing gGameStatus area/map/entry while the map change runs, and Mario is teleported back to
the room's entry point before walking out). C-up is pressed the way a runner does (it auto-hides after ~7 s; re-pressed
after a reaction delay). Video: 640x480 at 29.97 fps (one video frame per game frame), 0-6 extra frames per room load (console
load time with no game frames), mild blur + JPEG. Truth: per game frame RNG seed before/after, step count, map.
usage: DISPLAY=:92 M64P_GFX=... python3 sr_run.py OUTDIR [nrooms]   (Xvfb screen 800x600: the crop assumes the centered 640x480 window)
env SR_START=state file, SR_PLAN=json list of [map, open, seconds] to play only part of the route"""
import subprocess, sys, os, io, json, math, random
import numpy as np
from PIL import Image, ImageFilter
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from rngsim import *
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); NR = int(sys.argv[2]) if len(sys.argv) > 2 else 999
rnd = random.Random(7)
MAPS = ['kpa_01','kpa_03','kpa_04','kpa_08','kpa_09','kpa_10','kpa_11','kpa_12','kpa_13','kpa_14','kpa_15','kpa_16','kpa_17','kpa_32','kpa_33','kpa_40','kpa_41','kpa_50','kpa_51','kpa_52','kpa_53','kpa_60','kpa_61','kpa_62','kpa_63','kpa_70','kpa_81','kpa_82','kpa_83','kpa_90','kpa_91','kpa_94','kpa_95','kpa_96','kpa_100','kpa_101','kpa_102','kpa_111','kpa_112','kpa_113','kpa_114','kpa_115','kpa_116','kpa_117','kpa_118','kpa_119','kpa_121','kpa_130','kpa_133','kpa_134']
MID = {m: i for i, m in enumerate(MAPS)}
# (map, C-up open?, seconds in the room)
PLAN = [('kpa_11', 1, 22), ('kpa_62', 1, 14), ('kpa_63', 1, 7), ('kpa_60', 0, 6), ('kpa_133', 1, 9), ('kpa_134', 1, 8),
        ('kpa_130', 1, 8), ('kpa_111', 0, 8), ('kpa_112', 1, 6), ('kpa_113', 0, 5), ('kpa_114', 1, 7), ('kpa_115', 0, 6),
        ('kpa_118', 1, 5), ('kpa_119', 1, 6), ('kpa_118', 1, 5), ('kpa_115', 0, 5), ('kpa_114', 1, 5), ('kpa_113', 0, 4),
        ('kpa_82', 1, 6), ('kpa_82', 0, 40), ('kpa_61', 0, 8), ('kpa_33', 1, 8), ('kpa_52', 0, 5),
        ('kpa_40', 1, 5), ('kpa_41', 1, 5), ('kpa_40', 1, 5), ('kpa_41', 1, 5), ('kpa_40', 1, 5), ('kpa_41', 1, 5), ('kpa_40', 1, 5),
        ('kpa_102', 0, 6), ('kpa_53', 1, 50)][:NR]
if os.environ.get('SR_PLAN'): PLAN = [tuple(x) for x in json.loads(os.environ['SR_PLAN'])]   # e.g. the maze rooms -> Duplighost room only
# entries with walk exits where the room has one (doors may be locked); the exit back through that entry leaves the room
ENT = {'kpa_11': 1, 'kpa_62': 1, 'kpa_63': 0, 'kpa_60': 1, 'kpa_133': 1, 'kpa_134': 0, 'kpa_130': 0, 'kpa_111': 1, 'kpa_112': 0,
       'kpa_113': 0, 'kpa_114': 0, 'kpa_115': 0, 'kpa_118': 0, 'kpa_119': 0, 'kpa_82': 0, 'kpa_61': 0, 'kpa_33': 0, 'kpa_52': 0,
       'kpa_40': 1, 'kpa_41': 0, 'kpa_102': 0, 'kpa_53': 0}
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sr_emu')
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/' + os.environ.get('SR_START', 'kpa11_e1_nog.st')); e.step(0, 0, 0, 2)
y4m = open(OUT + '/run.y4m', 'wb'); y4m.write(b'YUV4MPEG2 W640 H480 F30000:1001 Ip A1:1 C420jpeg\n')
VF = [0]; truth = []; GF = [0]; events = []
def grab():
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    im = Image.frombytes('RGB', (640, 480), raw)
    bar = np.asarray(im.crop((80, 6, 600, 12))).reshape(-1, 3).astype(int)
    vis = float(np.mean((bar[:, 0] > 150) & (bar[:, 1] > 120) & (bar[:, 2] < 120))) > 0.5
    im = im.filter(ImageFilter.GaussianBlur(0.5)); b = io.BytesIO(); im.save(b, 'JPEG', quality=85); im = Image.open(b).convert('YCbCr')
    y, cb, cr = im.split()
    fr = b'FRAME\n' + y.tobytes() + cb.resize((320, 240), Image.BILINEAR).tobytes() + cr.resize((320, 240), Image.BILINEAR).tobytes()
    return fr, vis
VIS = [False]
def step(b=0, x=0, y=0, lag=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    fr, vis = grab(); VIS[0] = vis
    truth.append([GF[0], VF[0], prev, k, where(e)[1], e.s16(GAME_MODE), int(vis)])
    for i in range(1 + lag): y4m.write(fr); VF[0] += 1
    GF[0] += 1
def fb(v): import struct; return struct.unpack('>I', struct.pack('>f', v))[0]
def mode(): return e.s16(GAME_MODE)
def wait_world(maxf=400, target=None, lag=0):
    """run frames through a map change; redirect it to target (DIAGNOSTIC) and add console load lag once"""
    n = 0; redirected = False; lagged = False
    while n < maxf:
        m = mode()
        if m == GM_CHANGE_MAP and target and not redirected:
            g = game_status(e); e.w16(g + 0x86, 22); e.w16(g + 0x8C, MID[target[0]]); e.w16(g + 0x8E, target[1])   # DIAGNOSTIC: exit redirected to the next route room
            redirected = True
        if m == GM_CHANGE_MAP and redirected and not lagged and n > 10: step(lag=lag); lagged = True
        else: step()
        n += 1
        if redirected and mode() == GM_WORLD and n > 30: q = player(e); DOOR[0] = (q['x'], q['z']); break
    for i in range(20): step()
cur_open = [False]; pressed_at = [-999]; hidden_since = [None]
def tick(open_, x=0, y=0, extra=0):
    b = extra
    if open_ and not VIS[0]:
        if hidden_since[0] is None: hidden_since[0] = GF[0] + rnd.randint(8, 18)
        if GF[0] >= hidden_since[0] and GF[0] - pressed_at[0] > 20: b |= U_CBUTTON; pressed_at[0] = GF[0]; hidden_since[0] = None
    elif not open_ and VIS[0] and GF[0] - pressed_at[0] > 20:
        b |= U_CBUTTON; pressed_at[0] = GF[0]
    else: hidden_since[0] = None
    step(b, x, y)
def exit_room(target, riding=False):
    p = ENTRY[0]
    for k, v in enumerate((p['x'], p['y'], p['z'])): e.w32(PLAYER + PS_POS + 4 * k, fb(v))   # DIAGNOSTIC: back to the entry point
    if riding:
        for i in range(40): tick(False, 0, 0, D_CBUTTON if i == 5 else 0)   # get off Lakilester
    th0 = math.radians(p['yaw'] + 180)
    for dd in [0, 180, 90, 270, 45, 135, 225, 315]:
        th = th0 + math.radians(dd)
        for i in range(70):
            tick(False, int(70 * math.sin(th)), int(70 * math.cos(th)), A if i % 8 == 4 else 0)
            if mode() == GM_CHANGE_MAP: wait_world(target=target, lag=rnd.randint(0, 6)); return True
        for k, v in enumerate((p['x'], p['y'], p['z'])): e.w32(PLAYER + PS_POS + 4 * k, fb(v))
    return False
ENTRY = [None]; DOOR = [None]
e.w32(SAVE + 0x0FB0 + 4 * (0x60C // 32), e.u32(SAVE + 0x0FB0 + 4 * (0x60C // 32)) | (1 << (0x60C % 32)))   # DIAGNOSTIC setup: kpa_11 Koopatrol defeated (as in the route)
q = player(e); DOOR[0] = (q['x'], q['z'])
for i in range(20): step()
for ri, (m, op, secs) in enumerate(PLAN):
    ENTRY[0] = player(e); events.append({'room': m, 'open': op, 'gf': GF[0], 'vf': VF[0], 'where': list(where(e))})
    print('room', ri, m, 'open' if op else 'closed', secs, 's  now in', where(e), flush=True)
    n = int(secs * 30)
    unplanned = False
    if m == 'kpa_11':                      # the route rides this room on Lakilester: mount, ride down-left, then left to the exit
        for i in range(700):
            x, y, bb = (0, 0, D_CBUTTON) if i == 120 else ((-50, -50, 0) if 150 < i < 600 else ((-70, 0, 0) if i >= 600 else (0, 0, 0)))
            tick(True, x, y, bb)
            if mode() == GM_CHANGE_MAP: wait_world(target=(PLAN[ri + 1][0], ENT[PLAN[ri + 1][0]]), lag=rnd.randint(0, 6)); unplanned = True; break
        if unplanned: continue
        n = 0
    # which stick direction leads away from the door Mario came in by (into the room)?
    best = (0, 0); bd = -1; p0 = player(e)
    dd0 = math.hypot(p0['x'] - DOOR[0][0], p0['z'] - DOOR[0][1])
    if m == 'kpa_11': bd = 0
    for sx, sy in ([(50, 0), (-50, 0), (0, 50), (0, -50)] if m != 'kpa_11' else []):
        for i in range(6): tick(bool(op), sx, sy)
        q = player(e); d = math.hypot(q['x'] - DOOR[0][0], q['z'] - DOOR[0][1]) - dd0
        if d > bd: bd, best = d, (sx, sy)
        for i in range(6): tick(bool(op), -sx, -sy)
    for i in range(max(0, n - 48)):
        ph = i % 70; sx, sy = best
        x, y = ((sx, sy) if ph < 25 else (-sx, -sy) if 35 <= ph < 55 else (0, 0)) if op == 1 else (0, 0)   # runner-ish steps, drifting into the room (open = 2: stand still with the bar up)
        tick(bool(op), x, y)
        if mode() == GM_CHANGE_MAP and ri + 1 < len(PLAN):                              # walked into an exit anyway: go on
            events.append({'unplanned_exit': m, 'gf': GF[0]}); wait_world(target=(PLAN[ri + 1][0], ENT[PLAN[ri + 1][0]]), lag=rnd.randint(0, 6)); unplanned = True; break
        if mode() != GM_WORLD: events.append({'mode': mode(), 'gf': GF[0]}); print('  mode', mode(), 'at', GF[0], flush=True); break
    if unplanned: continue
    if mode() != GM_WORLD: break
    if ri + 1 < len(PLAN):
        nxt = PLAN[ri + 1]
        if nxt[0] == m: continue
        if not exit_room((nxt[0], ENT[nxt[0]]), riding=(m == 'kpa_11')): print('  could not exit', m, flush=True); events.append({'stuck': m}); break
y4m.close()
json.dump({'truth': truth, 'events': events, 'video_frames': VF[0]}, open(OUT + '/truth.json', 'w'))
print('game frames', GF[0], 'video frames', VF[0])
