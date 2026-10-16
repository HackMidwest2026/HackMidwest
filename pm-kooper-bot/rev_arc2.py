"""pra_01 reflected side: arc push steered by waypoints. Each stop-and-go cycle (go G, stop S) Mario aims at the
point W units ahead of Lakilester toward the current waypoint, so Lakilester is pushed along a path:
up from the mirror, right under the north rock, up to the top wall, right along it to the top-right corner.
usage: rev_arc2.py G S W 'x,z;x,z;...' [save_path]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/arc2')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
G, S, Wd = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
wps = [tuple(map(float, w.split(','))) for w in sys.argv[4].split(';')]
e.load('states/pra01_top_rock.st')
wi, c, f = 0, 0, 0
while c < 400 and wi < len(wps):
    p, l = player(e), laki()
    tx, tz = wps[wi]
    if math.hypot(tx - l['x'], tz - l['z']) < 12:
        wi += 1; continue
    d = math.hypot(tx - l['x'], tz - l['z'])
    ax, az = l['x'] + Wd * (tx - l['x']) / d, l['z'] + Wd * (tz - l['z']) / d
    deg = math.degrees(math.atan2(az - p['z'], ax - p['x']))
    sx, sy = stick_for(deg, 80)
    for i in range(G): e.step(0, sx, sy, 2)
    for i in range(S): e.step(0, 0, 0, 2)
    c += 1; f += G + S
    p, l = player(e), laki()
    if c % 10 == 0: print(c, f, 'wp', wi, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']), flush=True)
    if l['speed'] > 0.01:
        print('LOST at', c, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed'])); break
p, l = player(e), laki()
print('end', c, f, 'wp', wi, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']))
if len(sys.argv) > 5: e.save(sys.argv[5])
