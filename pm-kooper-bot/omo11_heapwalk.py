"""Walk the general heap (0x802FB800) and print blocks: node, block, length, allocated, id. usage: omo11_heapwalk.py STATE"""
import os, sys
from emu import *
HEAD = 0x802FB800
def walk(e):
    out = []; n = HEAD
    for i in range(2000):
        nxt, ln, al, mid = e.u32(n), e.u32(n + 4), e.u16(n + 8), e.u16(n + 0xA)
        out.append((n, n + 0x10, ln, al, mid))
        if nxt == 0: break
        n = nxt
    return out
if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/hw%d' % os.getpid()); e.load(sys.argv[1]); e.step(0, 0, 0, 2)
    for n, b, ln, al, mid in walk(e):
        print('%08x blk %08x len %6x %s id %d' % (n, b, ln, 'USED' if al else 'free', mid))
