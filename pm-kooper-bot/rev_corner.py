"""pra_01 reflected side: the legend's push, scripted.
 A  from states/pra01_top_rock.st (Mario by the left rock at the bottom of the mirror, Lakilester on his right
    facing left) stop-and-go aimed at Lakilester: he is pushed up until he is pinned under the north rock (z ~ -178)
 B  Mario steps around to Lakilester's left at the same depth (down, left, up; staying within the 40-unit tether)
 C  stop-and-go right along the rock's bottom face; past the rock (x > XR) aim at Lakilester again so he drifts up
    to the top wall, then right along the wall until he stops (the step at x ~ 720-740)
Prints the path and Mario/Lakilester distance; saves states/pra01_corner.st.
usage: rev_corner.py G XR"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/corner')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
def st(tag):
    p, l = player(e), laki()
    print(tag, 'mario %.1f %.1f laki %.1f %.1f dist %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], math.hypot(p['x'] - l['x'], p['z'] - l['z']), l['speed']), flush=True)
def cyc(deg, g):
    sx, sy = stick_for(deg, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
def aim(ox=0.0, oz=0.0):
    p, l = player(e), laki()
    return math.degrees(math.atan2(l['z'] + oz - p['z'], l['x'] + ox - p['x']))
G, XR = int(sys.argv[1]), float(sys.argv[2])
e.load('states/pra01_top_rock.st')
for c in range(80):                                   # A
    cyc(aim(), G)
    if laki()['z'] < -176: break
st('A pinned under the rock')
for k in range(20):                                   # wait for the push to settle
    l0 = laki()['x']; cyc(aim(), G)
    if abs(laki()['x'] - l0) < 0.01: break
st('A settled')
for deg, n in ((90, 3), (180, 7), (270, 3)):          # B: down, left, up (single frames, check tether)
    sx, sy = stick_for(deg, 80)
    for i in range(n):
        e.step(0, sx, sy, 2)
    e.step(0, 0, 0, 2)
    st('B %d' % deg)
for c in range(150):                                  # C
    l, p = laki(), player(e)
    if l['x'] < XR:
        deg = math.degrees(math.atan2(l['z'] - p['z'], 30.0))  # right, matching his depth
    else:
        deg = aim(15.0 if l['z'] < -205 else 0.0)
    x0 = l['x']
    cyc(deg, G)
    if c % 5 == 0: st('C%d' % c)
    if laki()['speed'] > 0.01: st('LOST'); break
st('end')
e.save('states/pra01_corner.st')
