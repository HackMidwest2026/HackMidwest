"""pra_01 reflected side: the legend's arc push. Setup: Mario walks left along the mirror (z ~ -13) into the left rock,
Lakilester trails on his right facing left. Push: stop-and-go (go G frames, stop S) with the stick aimed at
Lakilester (AIM: 'laki' = straight at him, 'right' = always right), so as Lakilester drifts north (-z) on each
overlap the push arcs up. Logs every N cycles; saves the end state. usage: rev_arc.py G S AIM [cycles]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/arc')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
def st(tag):
    p, l = player(e), laki()
    print(tag, 'mario %.1f %.1f %.1f laki %.1f %.1f %.1f spd %.1f yaw %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0x34)), where(e)[:2], flush=True)
G, S, AIM = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 300
if not os.path.exists('states/pra01_top_rock.st'):
    e.load('states/pra01_top_start.st')
    for i in range(50): e.step(0, 80, 0, 2)        # right to x ~740
    for i in range(30): e.step(0, 0, -80, 2)       # down to the mirror
    for i in range(80):                            # left along the mirror into the rock (stop when he slides)
        e.step(0, -80, 0, 2)
        if player(e)['z'] < -14 or player(e)['x'] < 556: break
    for i in range(60): e.step(0, 0, 0, 2)
    e.save('states/pra01_top_rock.st')
e.load('states/pra01_top_rock.st')
st('setup')
for c in range(N):
    p, l = player(e), laki()
    if AIM == 'laki':
        deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x']))
    elif AIM.startswith('lane'):        # head right while steering onto Lakilester's z (gain k)
        k = float(AIM[4:])
        deg = math.degrees(math.atan2(max(-1.5, min(1.5, k * (l['z'] - p['z']))), 1.0))
    else:
        deg = 0
    sx, sy = stick_for(deg, 80)
    for i in range(G): e.step(0, sx, sy, 2)
    for i in range(S): e.step(0, 0, 0, 2)
    if c % 10 == 0: st(c)
    if where(e)[:2] != (21, 0): break
st('end')
e.save('/dev/shm/pmbot/arc/end.st')
