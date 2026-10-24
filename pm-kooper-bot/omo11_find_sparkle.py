"""Find the Super Block sparkle (stars_shimmer, effect 34, 5 parts) data block in a state and the two menu addresses
that would put +0x108 on a part's frame counter (part 0: data-0xE0, part 4: data-0x30). usage: omo11_find_sparkle.py STATE..."""
import os, sys
from emu import *
from omo11_heapwalk import walk
def sparkle(e):
    out = []
    for n, bk, ln, al, mid in walk(e):
        if al and ln == 0x20 and e.u32(bk + 4) == 34 and e.u32(bk + 8) == 5:
            out.append((bk, e.u32(bk + 0xC)))
    return out
if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/fs%d' % os.getpid())
    for st in sys.argv[1:]:
        e.load(st); e.step(0, 0, 0, 2)
        for inst, data in sparkle(e):
            print(st.split('/')[-2], 'sparkle inst %08x data %08x -> menu at %08x (part 0) or %08x (part 4)' % (inst, data, data - 0xE0, data - 0x30))
