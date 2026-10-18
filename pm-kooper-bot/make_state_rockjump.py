"""pra_01 reflected side, rock-jump start: from states/pra01_top_rock.st (Mario at the bottom of the mirror by the
small rock, Laki idle on his right) jump left onto the small rock (stick angle D, A held 8, R frames of stick), stand
until Lakilester follows and goes idle (follow state 5), wiggle in place on the rock until the history ring is full,
then hop back down to the right next to Lakilester (stick 0, A held 8, H frames of stick). Prints where everything
ends up and whether the frozen target is intact. Env PRE=k: first walk left k frames and stand WAIT frames (default 60) so Laki follows and idles there, which moves
the stale target (Mario's jump start) further left.
usage: make_state_rockjump.py D R H [out.st]"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rj')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
def st(tag):
    p, l = player(e), laki(); ptr = e.u32(PTR)
    print('%-10s M (%.1f, %.1f, %.1f) act %d  L (%.1f, %.1f, %.1f)  state %d ptr %d idx %d tgt (%.1f, %.1f)' % (tag, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, e.u32(IDX), e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
D, R, H = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
st('start')
for i in range(int(os.environ.get('PRE', 0))): e.step(0, *stick_for(180, 80), 2)
if os.environ.get('PRE'):
    for i in range(int(os.environ.get('WAIT', 60))): e.step(0, 0, 0, 2)
    st('walked')
s = stick_for(D, 80)
for i in range(30):
    e.step(0x80 if i < 8 else 0, *(s if i < R else (0, 0)), 2)
    if i > 3 and player(e)['action'] in (0, 1, 2): break
for i in range(60): e.step(0, 0, 0, 2)
st('on rock')
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(120):
    if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
    e.step(0, *(up if f % 2 == 0 else dn), 2)
for i in range(10): e.step(0, 0, 0, 2)
st('filled')
ptr = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)
xs = [e.f32(HIST + 16 * k + 4) for k in range(40)]; ys = [e.f32(HIST + 16 * k + 8) for k in range(40)]
print('ring x %.1f..%.1f  y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
r = stick_for(0, 80)
for i in range(30):
    e.step(0x80 if i < 8 else 0, *(r if i < H else (0, 0)), 2)
    if i > 3 and player(e)['action'] in (0, 1, 2): break
for i in range(20): e.step(0, 0, 0, 2)
st('down')
ok = e.u32(PTR) == ptr and e.f32(HIST + 16 * ptr + 4) == tx and e.f32(HIST + 16 * ptr + 12) == tz and (e.u32(STATE) >> 16) == 5
p, l = player(e), laki()
print('target intact:', ok, ' Laki right of Mario:', l['x'] > p['x'])
if len(sys.argv) > 4 and ok:
    e.step(0, 0, 0, 2); e.save(sys.argv[4]); print('saved', sys.argv[4])
