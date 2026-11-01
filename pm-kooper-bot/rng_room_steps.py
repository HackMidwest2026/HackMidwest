import sys, collections
from emu import *
from pm import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ow2')
e.load(sys.argv[1]); e.step(0, 0, 0, 2)
plan = [('stand', (0, 0), 300), ('walk', None, 300), ('stand', (0, 0), 300)]
for name, stick, n in plan:
    ks = []
    for i in range(n):
        st = stick if stick else ((60, 0) if (i // 40) % 2 == 0 else (-60, 0))
        prev = e.u32(SEED); e.step(0, *st, 2); cur = e.u32(SEED)
        k = 0; x = prev
        while x != cur and k < 5000: x = adv(x); k += 1
        ks.append(k)
    extra = [i for i, k in enumerate(ks) if k != 1]
    gaps = [b - a for a, b in zip(extra, extra[1:])]
    print('%-5s steps per frame: %s; frames with extra steps: %s...; gaps %s' % (name, sorted(collections.Counter(ks).items()), extra[:12], sorted(collections.Counter(gaps).items())))
