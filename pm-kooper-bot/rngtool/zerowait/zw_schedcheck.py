"""Check the B-held hallway scene model: from the seed at the state load, the per-frame step + the coin (24/48 schedule,
phase found once) + the fixed extra schedule (zw_sched.py) must give the emulator's seed on every frame up to the
battle. DIAGNOSTIC: random seeds. Prints the coin phase and, per seed, the first mismatching frame (none = exact)."""
import os, sys, random
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import *
SCHED = {138: 7, 139: 11, 140: 12, 141: 2, 147: 10, 152: 12, 153: 11, 158: 12, 159: 10, 199: 5, 286: 12, 287: 12, 288: 8}
D1009 = 4294967295 // 1010
def coin(s):
    while True:
        s = adv(s); v = s // D1009
        if v <= 1009: return s, v // 10
def model(s, nc, upto, order, rule='2448'):
    out = []
    for f in range(upto):
        x = SCHED.get(f, 0)
        if order == 'pre':
            for i in range(x): s = adv(s)
        if f == nc: s, v = coin(s); nc = f + (48 if v >= 70 and rule == '2448' else 24)
        if order == 'post':
            for i in range(x): s = adv(s)
        s = adv(s); out.append(s)
    return out
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zwsc')
for i in range(60): e.step(0, 0, 0, 2)
rnd = random.Random(23); runs = []
for n in range(int(sys.argv[1]) if len(sys.argv) > 1 else 6):
    e.load('states/kkj13_e0.st'); e.step(0, 0, 0, 2)
    s0 = rnd.getrandbits(32); e.w32(SEED, s0)          # DIAGNOSTIC
    tr = []
    for f in range(346): e.step(B, 0, 0, 2); tr.append(e.u32(SEED))
    runs.append((s0, tr))
best = None
for rule in ('2448', 'always24'):
  for order in ('pre', 'post'):
    for nc in range(48):
        ok = sum(1 for s0, tr in runs if model(s0, nc, 346, order, rule) == tr)
        if best is None or ok > best[0]: best = (ok, order, nc, rule)
print('best model: %d of %d seeds exact on every frame, extras %s the coin, first coin draw at frame %d, coin spacing rule %s' % (best[0], len(runs), best[1], best[2], best[3]))
for s0, tr in runs:
    m = model(s0, best[2], 346, best[1], best[3]); bad = next((i for i in range(346) if m[i] != tr[i]), None)
    print('%08x first mismatch frame %s' % (s0, bad))
