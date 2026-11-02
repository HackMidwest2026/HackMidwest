"""Video anchor for a boot: power on (cold) in the emulator, step one VI at a time, log the game mode and the logo state
(gGameStatus.startupState) per VI and the COP0 Count, and report how long after the seed line (main.c, Count ~ seed - 1)
the logos game mode starts (the N64 logo's fade-in, the first picture in a capture). No RAM writes.
(The emulator runs without a video plugin, so the frame buffer is empty; the game mode is the anchor.)
usage: boot_anchor.py [T0 PERIOD]   (A every PERIOD game frames from game frame T0, as boot_seed.py)"""
import os, sys, shutil
T0_ = int(sys.argv[1]) if len(sys.argv) > 1 else 120
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 20
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import SEED, adv
TICKS_PER_VI = 811363                     # this core (emu.py)
dd = '/dev/shm/pmbot/ba%d' % os.getpid(); os.makedirs(dd, exist_ok=True)
for f in os.listdir('/tmp/claude-0/pm/savegame'): shutil.copy(os.path.join('/tmp/claude-0/pm/savegame', f), dd)
e = Emu('pm-jp.z64', dd)
vi = 0; gf = 0; init = None; seed0 = None; prev = e.u32(SEED); mode4 = None; log = []
while vi < 6000:
    b = A if (gf >= T0_ and (gf - T0_) % PER == 0 and mode4 is None) else 0   # held for both VIs of the game frame
    e.step(b, 0, 0, 1); vi += 1
    if vi % 2 == 0: gf += 1
    s = e.u32(SEED); m = e.s16(GAME_MODE); gs = e.u32(GAME_STATUS_PTR)
    st = e.u8(gs + 0xAC) if 0x80000000 <= gs < 0x80800000 else -1
    if init is None and prev == 1 and s != 1: init = vi; seed0 = s
    prev = s
    log.append((vi, m, st, e.count(), s))
    if m == 4 and mode4 is None: mode4 = vi
    if mode4 is not None and vi > mode4 + 2: break
C = seed0 - 1
print('seed first seen at harness step', init, ': seed %08x -> boot Count ~ %08x' % (seed0, C))
last = None
for vi_, m, st, cnt, sd in log:
    if (m, st) != last:
        k = 0; t = seed0
        while t != sd and k < 20000: t = adv(t); k += 1
        print('step %4d  mode %2d  startupState %2d  Count %08x  (%+.1f VIs after the seed line)  RNG steps since %d' % (vi_, m, st, cnt, (cnt - C) / TICKS_PER_VI, k))
        last = (m, st)
logos = next(r for r in log if r[1] == 1)
prevr = log[log.index(logos) - 1]
print('logos mode starts between %.1f and %.1f VIs after the seed line' % ((prevr[3] - C) / TICKS_PER_VI, (logos[3] - C) / TICKS_PER_VI))
