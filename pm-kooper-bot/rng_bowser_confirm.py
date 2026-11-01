import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
st = sys.argv[1]; seed = int(sys.argv[2], 16); Ts = range(int(sys.argv[3]), int(sys.argv[4]))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/e2b%d' % os.getpid())
def run(T, R=2):
    """R = which enemy turn (entry into state 21) has the draws"""
    e.load(st); e.step(0, 0, 0, 2)
    for o in (2, 3, 4): e.w8(PLAYER_DATA + o, 99)          # DIAGNOSTIC setup
    e.w32(SEED, seed); e.w32(SEED2, seed)                   # DIAGNOSTIC: chosen seed
    st_ = {'f': 0, 'n21': 0, 'prev': None, 'n17': 0}; seeds = {}
    def step(b=0):
        e.step(b, 0, 0, 2); st_['f'] += 1; seeds[st_['f']] = e.u32(SEED); bs = bstate(e)
        if bs == 21 and st_['prev'] != 21: st_['n21'] += 1
        if bs == 17 and st_['prev'] != 17: st_['n17'] += 1
        if bs != st_['prev']: trace.append((st_['f'], bs))
        st_['prev'] = bs
    conf = None; trace = []
    for i in range(8000):
        b = bstate(e)
        if b == 13:
            for j in range(10): step()
            step(A); [step() for j in range(15)]; step(A)            # Mario: Jump, default target
            [step() for j in range(30)]
        elif b == 14:
            step(A); [step() for j in range(15)]                       # partner: first ability
        elif b == 17:
            # partner's target select: the decisive press, T frames after the cursor appears (only in the final round)
            final = st_['n21'] == R - 1
            [step() for j in range(T if final else 10)]
            step(A); [step() for j in range(5)]
            if final: conf = st_['f'] - 5
        else: step(A if i % 20 == 0 else 0)
        if st_['n21'] == R: break
    if os.environ.get('TRACE'): print('n21', st_['n21'], 'n17', st_['n17'], 'trace', trace[:80])
    g = st_['f']; step(); step()
    s0 = seeds[g + 1]; s = s0
    s, r80 = rand_int(s, 80); s, r60 = rand_int(s, 60)
    return conf, s0, ('BodySlam' if r80 < 20 else ('Claw' if r60 < 20 else 'Fire')), r80, r60
prev = None
for T in Ts:
    conf, s0, mv, a, b = run(T)
    rel = ''
    if prev is not None:
        k = 0; x = prev
        while x != s0 and k < 50: x = adv(x); k += 1
        rel = '+%d adv' % k if k < 50 else 'unrelated'
    prev = s0
    print('T %2d (confirm on step %d): %-8s r80=%2d r60=%2d  AI seed %08x %s' % (T, conf or -1, mv, a, b, s0, rel), flush=True)
