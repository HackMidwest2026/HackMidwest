import os, sys, subprocess
from emu import *
from pm import *
from rngsim import *
SHOT = os.environ.get('SHOT'); out = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/trans'; os.makedirs(out, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/tr%d' % os.getpid())
if SHOT:
    for i in range(150): e.step(0, 0, 0, 2)
e.load('states/kkj11_e1.st'); e.step(0, 0, 0, 2)
s = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in s: e.w16(PLAYER_DATA + 0x208 + 2 * s.index(0), 0x11F)   # DIAGNOSTIC setup: Speedy Spin equipped
rows = []; f = 0
def step(b, x, y):
    global f
    prev = e.u32(SEED); e.step(b, x, y, 2); f += 1; cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 50000: t = adv(t); k += 1
    p = player(e); rows.append((f, where(e)[:2], e.s16(GAME_MODE), k, p['action']))
    if SHOT and f in SHOTS: subprocess.run(['import', '-window', 'root', '%s/f%03d.png' % (out, f)], check=True)
SHOTS = set(int(a) for a in os.environ.get('SHOTS', '').split(',') if a)
for i in range(40): step(0, 0, 80)                      # walk up to the door
for i in range(60):
    step(A if i % 2 == 0 else 0, 0, 80)
    if where(e)[:2] != (4, 5): break
door = f
spin = None
for i in range(260):
    p = player(e)
    b = (Z | U_CBUTTON) if (spin is None and i % 2 == 0) else 0
    step(b, 80, 0)
    if spin is None and player(e)['action'] == 26: spin = f
print('door A accepted on frame', door, 'first spin started on frame', spin)
seq = []
for r in rows:
    if r[0] < door - 30: continue
    seq.append('%d:%s/%d k%d a%d' % (r[0], r[1][1], r[2], r[3], r[4]))
print(' '.join(seq))
