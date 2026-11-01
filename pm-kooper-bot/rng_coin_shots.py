import os, subprocess
from emu import *
from pm import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cs')
for i in range(150): e.step(0, 0, 0, 2)
out = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/coin'; os.makedirs(out, exist_ok=True)
e.load('states/boss_2302_menu.st'); e.step(0, 0, 0, 2)
s = e.u32(SEED); rows = []
for f in range(1, 121):
    prev = e.u32(SEED); e.step(0, 0, 0, 2); cur = e.u32(SEED)
    # count advances this frame; a coin draw makes it 2 (frame advance + coin)
    k = 0; x = prev
    while x != cur and k < 10: x = adv(x); k += 1
    note = ''
    if k == 2:
        x1 = adv(prev); _, v = internal(prev, 1009)
        note = 'coin draw %d -> %s' % (v // 10, 'ALT' if v // 10 >= 70 else 'normal')
    rows.append((f, k, note))
    subprocess.run(['import', '-window', 'root', '%s/f%03d.png' % (out, f)], check=True)
for r in rows:
    if r[2]: print(r)
