"""Record one Jump variant as per-game-frame savestates for rendering: from Mario's menu, A (Jump), 15 steps, A
(confirm target, frame 0), then A presses on steps K/Q/P (run cancel / quick jump / action command); continues
TAIL steps after the partner menu opens. Writes DIR/s%05d.st and DIR/meta.txt (partner-menu frame).
usage: btl_record_variant.py BATTLE DIR K Q P [TAIL]   (use -1 for unused presses)"""
import os, sys
from emu import *
from pm import *
from btl import *
bid, d, K, Q, P = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
TAIL = int(sys.argv[6]) if len(sys.argv) > 6 else 60
os.makedirs(d, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rv%d' % os.getpid())
e.load('states/boss_%s_menu.st' % bid); e.step(0, 0, 0, 2)
e.step(A, 0, 0, 2)
for i in range(15): e.step(0, 0, 0, 2)
k = 0
def snap():
    global k
    e.save(os.path.join(d, "s%05d.st" % k)); k += 1
for i in range(10): e.step(0, 0, 0, 2); snap()          # a little lead-in on the target cursor
e.step(A, 0, 0, 2); snap(); f0 = k - 1                    # confirm = frame 0
menu = None
for s in range(1, 400):
    e.step(A if s in (K, Q, P) else 0, 0, 0, 2); snap()
    if menu is None and bstate(e) == 14: menu = s
    if menu is not None and s >= menu + TAIL: break
open(os.path.join(d, 'meta.txt'), 'w').write('confirm_index %d partner_menu_frame %d quality %d\n' % (f0, menu, e.s8(BSTATUS + 0x81)))
print('confirm idx', f0, 'partner menu at', menu, flush=True)
