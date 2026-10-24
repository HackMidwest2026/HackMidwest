"""Replay a steplog.py input log (DB key __last__) from BASE.st. With OUT_DIR, save a state every 2 game frames to
OUT_DIR/s%05d.st for the screenshot renderer (throttled), and write OUT_DIR/DONE at the end.
usage: replay_log.py DB BASE.st [OUT_DIR]"""
import glob, json, os, sys, time
from emu import *
from pm import *
steps = json.load(open(sys.argv[1]))['__last__']
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rep%d' % os.getpid())
e.load(sys.argv[2])
out = sys.argv[3] if len(sys.argv) > 3 else None
fr = 0; k = 0
for b, x, y, n in steps:
    e.step(b, x, y, n); fr += n
    if out and fr % 2 == 0:
        while len(glob.glob(os.path.join(out, 's*.st'))) > 60: time.sleep(0.3)
        e.save(os.path.join(out, 's%05d.st' % k)); k += 1
print('steps', len(steps), 'frames', fr, 'shots', k, 'curPartner', e.s8(PLAYER_DATA + 0x12), where(e), flush=True)
if out:
    e.step(0, 0, 0, 1); open(os.path.join(out, 'DONE'), 'w').close()
