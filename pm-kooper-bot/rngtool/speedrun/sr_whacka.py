"""Fast Whacka's Bump (emulator, no page): from the T2 item list, A on the item, then A again k frames later. Prints per k
when the target state starts, whether the confirm was taken, the best match of the hand-on-Mario name box before the
confirm (against M_charge.png from a slow confirm) and when the status bar is gone (the page's coin-present test).
usage: DISPLAY=... M64P_GFX=... M64P_DATA=... sr_whacka.py [k ...]   (needs /dev/shm/s2/explore/M_charge.png)"""
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
import numpy as np
from PIL import Image
OUT = '/dev/shm/s2/explore/'; os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s2exp')
for i in range(60): e.step(0, 0, 0, 2)
def grab():
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    return Image.frombytes('RGB', (640, 480), raw)
def gold(im):
    a = np.asarray(im.crop((int(.78*640), int(.02*480), int(.845*640), int(.11*480))).resize((32, 32))).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return float(np.mean((r > 140) & (g > 95) & (b < 120) & (r > b + 60) & (g > 0.6 * r)))
REFM = np.asarray(Image.open(OUT + 'M_charge.png').convert('L').crop((90, 115, 192, 156))).astype(float)
def mscore(im):
    a = np.asarray(im.convert('L').crop((90, 115, 192, 156))).astype(float); return 1 - np.mean(np.abs(a - REFM)) / 255
F = [0]
def step(b=0, x=0, y=0):
    e.step(b, x, y, 2); F[0] += 1; im = grab(); return im
def jw(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=3000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
ST = '/dev/shm/s2/whacka_items.st'
if not os.path.exists(ST):
    e.load('states/jr_t2_menu.st'); e.step(0, 0, 0, 2); until([13]); jw(20)
    jw(30, Z); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); jw(10); step(A)
    until([13], cap=4000, mash=True); jw(15)
    jw(15, 0, 0, 70); jw(25, A); jw(5); e.save(ST)
res = []
for k in [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6, 8, 10, 14]:
    e.load(ST); e.step(0, 0, 0, 2); rows = []
    for i in range(2): rows.append(('pre', bstate(e), gold(step()), 0))
    im = step(A); rows.append(('itemA', bstate(e), gold(im), round(mscore(im), 3)))
    t17 = None
    for i in range(1, 40):
        if t17 is None and bstate(e) == 17: t17 = i
        b = A if i == k else 0
        im = step(b); rows.append((i, bstate(e), round(gold(im), 2), round(mscore(im), 3), 'A' if b else ''))
        if i == k: im.save(OUT + 'whacka_k%d.png' % k)
    for i in range(40, 200):
        im = step(); rows.append((i, bstate(e), round(gold(im), 2), round(mscore(im), 3), ''))
    res.append({'k': k, 't17': t17, 'rows': rows})
    left = [r for r in rows if isinstance(r[0], int) and r[0] > k and r[1] != 17]
    hide = [r[0] for r in rows if isinstance(r[0], int) and r[0] > k and r[2] < 0.3]
    print('k', k, 'first bstate17 at', t17, 'm-score max before A', max([r[3] for r in rows if isinstance(r[0], int) and r[0] <= k] + [0]),
          'left17 at', left[0][0] if left else None, 'HUD gone (gold<0.3) at', hide[0] if hide else None, flush=True)
json.dump(res, open(OUT + 'whacka.json', 'w'))
