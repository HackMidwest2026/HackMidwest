"""Name a JP code address from the decomp's ver/jp/symbol_addrs.txt (nearest function at or below it)."""
import bisect, os, re
_S = None
def _load():
    global _S
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'papermario', 'ver', 'jp', 'symbol_addrs.txt')
    syms = []
    for l in open(path):
        m = re.match(r'\s*(\w+)\s*=\s*0x([0-9A-Fa-f]+);.*type:func', l)
        if m: syms.append((int(m.group(2), 16), m.group(1)))
    syms.sort(); _S = ([a for a, n in syms], [n for a, n in syms])
def name(addr):
    if _S is None: _load()
    i = bisect.bisect_right(_S[0], addr) - 1
    if i < 0: return hex(addr)
    off = addr - _S[0][i]
    return '%s+0x%x' % (_S[1][i], off) if off < 0x4000 else hex(addr)
