"""Run a route script with every emulator step watched: whenever u32 at any WATCH address changes, log the step,
value and the heap block (len, id, allocated) covering it. usage: WATCH=0xaddr,0xaddr omo11_lastwriter.py LOG SCRIPT ARGS..."""
import json, os, runpy, sys
import emu
from omo11_heapwalk import walk
W = [int(a, 16) for a in os.environ['WATCH'].split(',')]
log = open(sys.argv[1], 'a'); script = sys.argv[2]; sys.argv = [script] + sys.argv[3:]
orig = emu.Emu.step; last = {}; n = [0]
def step(self, *a, **k):
    orig(self, *a, **k); n[0] += 1
    for x in W:
        v = self.u32(x)
        if last.get(x) != v:
            last[x] = v
            blk = [(hex(bk), hex(ln), al, mid) for nd, bk, ln, al, mid in walk(self) if bk <= x < bk + ln]
            log.write(json.dumps({'script': os.path.basename(script), 'n': n[0], 'addr': hex(x), 'v': v, 'blk': blk}) + '\n')
emu.Emu.step = step
runpy.run_path(script, run_name='__main__')
