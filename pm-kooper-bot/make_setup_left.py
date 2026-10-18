"""Full setup with the stale target further left: from states/pra01_top_rock.st walk left PRE frames and wait 60
(Laki follows and idles further left), jump left (stick R frames), wait, wiggle to fill the history ring, hop right
(stick H frames); then the stage-2 arc (states/pra01_corner_rj_seq.json, aimed at Laki), stage 3 (3 up, two jumps
holding right, stop-and-go right along the top wall until Laki x >= 984, 30 frames). Prints the state after each
stage and whether the stale target is intact; saves OUT (the new top-right start) if it is.
usage: make_setup_left.py PRE R H OUT [seq.json]"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
PRE, R, H, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SEQ = sys.argv[5] if len(sys.argv) > 5 else 'states/pra01_corner_rj_seq.json'
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/msl%d' % os.getpid())
def laki():
    return [n for n in npcs(e) if n['id'] == -4][0]
def st(tag):
    p, l = player(e), laki(); ptr = e.u32(PTR)
    print('%-8s M (%.1f, %.1f, %.1f)  L (%.1f, %.1f, %.1f)  state %d ptr %d tgt (%.1f, %.1f)' % (tag, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
def jump(stick, hold):
    for i in range(30):
        e.step(0x80 if i < 8 else 0, *(stick if i < hold else (0, 0)), 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
for i in range(PRE): e.step(0, *stick_for(float(os.environ.get('PA', 180)), 80), 2)
for i in range(60): e.step(0, 0, 0, 2)
st('walked')
jump(stick_for(180, 80), R)
for i in range(60): e.step(0, 0, 0, 2)
st('rock')
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(120):
    if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
    e.step(0, *(up if f % 2 == 0 else dn), 2)
for i in range(10): e.step(0, 0, 0, 2)
jump(stick_for(0, 80), H)
for i in range(21): e.step(0, 0, 0, 2)
ptr = e.u32(PTR); tgt = (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12))
st('fill')
if os.environ.get('FILL_OUT'):   # rock-jump state for the arc search (it loads this and steps one neutral frame)
    e.save(os.environ['FILL_OUT']); print('saved', os.environ['FILL_OUT'])
    if os.environ.get('STOP') == 'fill': sys.exit()
e.step(0, 0, 0, 2)   # the original stages started from a saved state + 1 neutral frame
def intact():
    return e.u32(PTR) == ptr and (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)) == tgt
for g, th, sl in json.load(open(SEQ)):
    p, l = player(e), laki()
    sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    for i in range(sl): e.step(0, 0, 0, 2)
st('arc'); print('  intact', intact())
e.step(0, 0, 0, 2)
rx, ry = stick_for(0, 80)
for i in range(3): e.step(0, *stick_for(270, 80), 2)
for H2 in (12, 16):
    for i in range(24):
        e.step(0x80 if i < 8 else 0, rx if i < H2 else 0, ry if i < H2 else 0, 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(3): e.step(0, 0, 0, 2)
st('ledge'); print('  intact', intact())
for c in range(150):
    e.step(0, rx, ry, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    if laki()['x'] >= 984: break
for i in range(30): e.step(0, 0, 0, 2)
st('wall'); ok = intact(); l = laki(); print('  intact', ok, ' Laki-target distance %.1f' % math.hypot(l['x'] - tgt[0], l['z'] - tgt[1]))
if ok and l['x'] >= 984:
    e.step(0, 0, 0, 2); e.save(OUT); print('saved', OUT)
