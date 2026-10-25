"""Exact model of Paper Mario's heap allocator (43F0.c: _heap_malloc / _heap_malloc_tail / _heap_free /
_heap_realloc), working on the same linked list of 0x10-byte HeapNode headers:
    +0x0 next (pointer to the next header or 0)   +0x4 length (bytes after the header)
    +0x8 allocated (u16)   +0xA entryID (u16, from heap_nextMallocID)   +0xC capacity
Block address = header + 0x10.  Sizes are rounded up to 16.  Best fit: the smallest free block that is large enough,
the earliest one on a tie; it is split only if at least size+0x10 would remain, otherwise the whole block is taken.
Free merges with the next block if it is free, and with the previous one if the list walk finds it free.

Heap(nodes, next_id): nodes = {header_addr: [next, length, allocated, id]}, head = lowest header.
from_emu(e, head) reads the live list.  Contents are tracked separately (who last owned each block) so a stale
read like the APG menu fields can be explained: owner_at(addr) -> the allocation event that last covered addr."""
HEAD_GENERAL = 0x802FB800
MASK16 = 0xFFFF


def align16(n):
    return (n + 15) & ~15


class Heap:
    def __init__(self, nodes, head, next_id):
        self.n = {a: list(v) for a, v in nodes.items()}
        self.head = head
        self.next_id = next_id
        self.owner = {}          # block address -> event dict that allocated it (latest)
        self.history = []        # (block, length, event) for every allocation, in order

    @classmethod
    def from_emu(cls, e, head=HEAD_GENERAL, next_id_addr=0x80074250):
        nodes = {}
        a = head
        for i in range(10000):
            nxt, ln, al, mid = e.u32(a), e.u32(a + 4), e.u16(a + 8), e.u16(a + 0xA)
            nodes[a] = [nxt, ln, al, mid]
            if nxt == 0: break
            a = nxt
        return cls(nodes, head, e.u16(next_id_addr + 2) if e.u32(next_id_addr) < 0x10000 else e.u32(next_id_addr) & MASK16)

    # ---- walking ----
    def walk(self):
        a = self.head
        while True:
            nxt, ln, al, mid = self.n[a]
            yield a, nxt, ln, al, mid
            if not nxt: return
            a = nxt

    def blocks(self):
        """[(block_addr, length, allocated, id)] in address order"""
        return [(a + 0x10, ln, al, mid) for a, nxt, ln, al, mid in self.walk()]

    # ---- _heap_malloc ----
    def malloc(self, size, ev=None):
        size = align16(size)
        if not size: return 0
        smallest = 0; prev = None; nxt_of_found = 0
        for a, nxt, ln, al, mid in self.walk():
            if not al and ln >= size and (ln < smallest or not smallest):
                prev, smallest, nxt_of_found = a, ln, nxt
        if not smallest: return 0
        newsize = size + 0x10
        if smallest >= newsize:
            new = prev + newsize
            self.n[prev] = [new, size, 1, self.next_id & MASK16]
            self.n[new] = [nxt_of_found, smallest - newsize, 0, self.n.get(new, [0, 0, 0, 0])[3]]
        else:
            self.n[prev] = [nxt_of_found, smallest, 1, self.next_id & MASK16]
        self.next_id += 1
        blk = prev + 0x10
        self._own(blk, ev)
        return blk

    # ---- _heap_malloc_tail ----
    def malloc_tail(self, size, ev=None):
        size = align16(size)
        if not size: return 0
        found = None; found_len = 0; nxt_of_found = 0
        for a, nxt, ln, al, mid in self.walk():
            if not al and ln >= size:
                found, found_len, nxt_of_found = a, ln, nxt
        if not found_len: return 0
        newsize = size + 0x10
        if found_len >= newsize:
            new = found + found_len - size
            self.n[found] = [new, found_len - newsize, 0, self.n[found][3]]
            self.n[new] = [nxt_of_found, size, 1, self.n.get(new, [0, 0, 0, 0])[3]]
            cur = new
        else:
            self.n[found] = [nxt_of_found, found_len, 1, self.n[found][3]]
            cur = found
        blk = cur + 0x10
        self._own(blk, ev)
        return blk

    # ---- _heap_free ----
    def free(self, addr):
        if not addr: return 1
        node = addr - 0x10
        if node not in self.n or not self.n[node][2]: return 1
        nxt, cur_len = self.n[node][0], self.n[node][1]
        if nxt and not self.n[nxt][2]:
            cur_len += self.n[nxt][1] + 0x10
            dead = nxt
            nxt = self.n[nxt][0]
            del self.n[dead]
        tmp = self.head
        while True:
            hl = self.n[tmp][0]
            if hl == node:
                if not self.n[tmp][2]:
                    cur_len += 0x10 + self.n[tmp][1]
                    del self.n[node]
                    node = tmp
                break
            if node < tmp or not hl: break
            tmp = hl
        old_id = self.n[node][3]
        self.n[node] = [nxt, cur_len, 0, old_id]
        return 0

    # ---- _heap_realloc ----
    def realloc(self, addr, new_size, ev=None):
        cur = addr - 0x10
        ns = align16(new_size)
        if not self.n[cur][2]: return 0
        nxt, nlen = self.n[cur][0], self.n[cur][1]
        if nxt and not self.n[nxt][2]:
            dead = nxt; nxt = self.n[nxt][0]; nlen += 0x10 + self.n[dead][1]; del self.n[dead]
        if nlen < ns:
            # (the game does not merge back the next block here; it was absorbed into nlen only locally)
            raise NotImplementedError('realloc that moves')
        if ns + 0x10 < nlen:
            fb = addr + ns
            self.n[cur][0] = fb; self.n[cur][1] = ns
            self.n[fb] = [nxt, nlen - ns - 0x10, 0, 0]
        else:
            self.n[cur][0] = nxt; self.n[cur][1] = nlen
        return addr

    def _own(self, blk, ev):
        if ev is not None:
            self.owner[blk] = ev
            self.history.append((blk, self.n[blk - 0x10][1], ev))

    def owner_at(self, addr):
        """latest simulated allocation whose block covered addr: (block, length, event)"""
        for blk, ln, ev in reversed(self.history):
            if blk <= addr < blk + ln: return blk, ln, ev
        return None

    # ---- comparison with the live heap ----
    def diff(self, other):
        a = {k: tuple(v[:3]) for k, v in self.n.items()}
        b = {k: tuple(v[:3]) for k, v in other.n.items()}
        return [(hex(k), a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


# breakpoint addresses (JP)
MALLOC, MALLOC_TAIL, FREE, REALLOC = 0x8002902C, 0x80029124, 0x800291DC, 0x80029284


def apply_event(h, ev):
    """apply one logged breakpoint event to a Heap; returns the simulated result address (malloc) or None"""
    if ev['a0'] != h.head: return None
    if ev['pc'] == MALLOC: return h.malloc(ev['a1'], ev)
    if ev['pc'] == MALLOC_TAIL: return h.malloc_tail(ev['a1'], ev)
    if ev['pc'] == FREE: h.free(ev['a1']); return None
    if ev['pc'] == REALLOC: return h.realloc(ev['a1'], ev['a2'], ev)
    return None
