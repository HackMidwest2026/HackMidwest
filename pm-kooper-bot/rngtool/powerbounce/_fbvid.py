"""(run from bot1/) Record the Final Bowser phase 2 Power Bounce for a given seed and confirm delay (DIAGNOSTIC: seed written at frame 0,
Bowser HP 127 so all bounces fit). Presses: confirm at DELAY, then 1 frame before each landing (DELAY+44+27k).
Saves every frame as PNG in OUT and prints the cap rolls and Bowser's HP."""
import sys, os, subprocess
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, d, OUT, N = int(sys.argv[1], 16), int(sys.argv[2]), sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 480
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbv%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/fb2_t7like_pb.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed); e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, 127)     # DIAGNOSTIC: seed, Bowser HP 127
PRESS = {d} | {d + 44 + 27 * k for k in range(16)}
hp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
hits = 0; last = hp(); s = seed
for f in range(N):
    e.step(A if f in PRESS else 0, 0, 0, 2)
    h = hp()
    if h < last: hits += 1; print('frame %d: hit %d, Bowser HP %d' % (f, hits, h), flush=True)
    last = h
    subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '+repage', '%s/f%04d.png' % (OUT, f)], check=True)
print('BOUNCES', hits)
