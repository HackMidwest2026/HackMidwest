"""Gap from the kkj_12 -> kkj_13 door press to the first coin draw in the Hallway Bowser battle menu, holding B
through the cutscene. Varies the seed (DIAGNOSTIC) and the frame of the door press."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gr%d' % os.getpid())
def run(seed, delay, trace=False):
    e.load('states/kkj12_e1.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed)                    # DIAGNOSTIC: chosen seed
    for i in range(delay): e.step(0, 0, 0, 2)
    # walk right into the door and press A
    for i in range(60):
        e.step(0, 80, 0, 2)
        if where(e)[:2] != (4, 6): break
        if i >= 6 and i % 2 == 0: e.step(A, 80, 0, 2)
        if where(e)[:2] != (4, 6): break
    # reference: the frame the map change is queued (the door accepted A)
    s_ref = e.u32(SEED); steps = 0; frames = 0; prev = s_ref; seen = []; draws = 0
    for i in range(6000):
        e.step(B, 0, 0, 2); frames += 1
        cur = e.u32(SEED); k = 0; x = prev
        while x != cur and k < 20000: x = adv(x); k += 1
        steps += k; prev = cur
        gm = e.s16(GAME_MODE); bs = bstate(e) if gm == 8 else None
        if trace and (not seen or seen[-1][1:] != (gm, bs)): seen.append((frames, gm, bs))
        if gm == 8 and bs == 13 and k == 2:          # first coin draw with Mario's menu up
            return frames, steps, seen
    return None, None, seen
if len(sys.argv) > 1 and sys.argv[1] == 'trace':
    f, s, seen = run(0x12345678, 0, True); print('frames', f, 'steps', s, 'modes/states', seen[:40]); sys.exit()
for seed in [int(a, 16) for a in sys.argv[1:]]:
    r = [run(seed, d)[:2] for d in (0, 1, 2, 3)]
    print('seed %08x: (frames, steps) for door press shifted 0..3 frames: %s' % (seed, r), flush=True)
