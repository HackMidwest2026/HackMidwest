"""Boot to the field, then press the console's reset button (mupen64plus M64CMD_RESET, soft) and log gRandSeed through the
re-boot. Shows how this emulator treats osGetCount after a soft reset. No RAM writes. usage: python3 soft_reset.py [WAIT_FRAMES]"""
import os, sys, shutil, ctypes
W = int(sys.argv[1]) if len(sys.argv) > 1 else 100
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
import emu as emumod
from emu import *; from pm import *; from rngsim import SEED, adv
dd = '/dev/shm/pmbot/sr%d' % os.getpid(); os.makedirs(dd, exist_ok=True)
for f in os.listdir('/tmp/claude-0/pm/savegame'): shutil.copy(os.path.join('/tmp/claude-0/pm/savegame', f), dd)
e = Emu('pm-jp.z64', dd)
core = ctypes.CDLL(os.path.abspath(emumod.CORE), mode=ctypes.RTLD_GLOBAL)
for f in range(800):
    e.step(A if f % 20 == 0 else 0, 0, 0, 2)
    if e.s16(GAME_MODE) == 4: break
for i in range(W): e.step(0, 0, 0, 2)
print('before reset: frame', e.frame, 'seed %08x' % e.u32(SEED), 'count %08x' % e.count())
r = core.CoreDoCommand(19, 0, None)        # M64CMD_RESET, 0 = soft
print('reset cmd', r)
prev = e.u32(SEED); seen = []
for f in range(200):
    e.step(0, 0, 0, 1)
    s = e.u32(SEED)
    if s != prev and (prev == 1 or s == 1 or len(seen) < 3): seen.append((f, '%08x' % prev, '%08x' % s, '%08x' % e.count()))
    prev = s
for x in seen[:8]: print('VI', x)
