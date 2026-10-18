"""Wider search of endings from the very top-right corner (cardinal stick, A, hammer only), scored by input windows.
Every run: up 10, right 10 into the corner; then
  L1 > 0: B+left (hammer) and left L1 frames (Laki stays idle while Mario is within ~45 units); B+down (hammer)
  L1 = 0: B+down (hammer)
then down D0, A + down N (A held 12), then a tail:
  tail H (hammer stop): B+left, hold left (through the forced drop onto step 3) for K frames after the step-3
          landing (K = 1 is the landing frame), B+up, hold up
  tail W (release + wait): release, hold left until the forced drop, release during it, left T frames, release,
          stand U frames, then hold up
Ending: C-down (up held) at offset o = 0..6 frames after Mario lands on step 2 (y -20; the landing also records its
absolute frame, counted from the top-right state); a run's result is the set of
offsets that clip. One emulator per worker; the shared prefix of each (L1, D0, N) group is saved once and branched.
Results are appended to OUT.jsonl as they come. usage: PART=i NPARTS=4 rta_wide.py FAMILY OUT.jsonl   (FAMILY H or W)"""
import json, os, sys
from multiprocessing import Pool
from rta_end5 import *
B = 0x40
G = {}
class CEmu(Emu):
    """Emu that counts frames since the top-right state was loaded (fr), restored with the save states"""
    fr = 0
    saved = {}
    def step(self, *a):
        super().step(*a); self.fr += 1
    def save(self, path):
        super().save(path); self.saved[path] = self.fr
    def load(self, path, frame=0):
        super().load(path); self.fr = self.saved.get(path, 0)
def init():
    G['e'] = CEmu(os.environ['PM_ROM'], '/dev/shm/pmbot/rw%d' % os.getpid()); G['w'] = '/dev/shm/pmbot/rw%d' % os.getpid()
def load(path):
    for t in range(3):
        try: G['e'].load(path); return True
        except RuntimeError: pass
    return False
def finish():
    """hold up until Mario lands on step 2, then try C-down at offsets 0..6; returns (landing, clipping offsets)"""
    e, w = G['e'], G['w']
    k, prev = 0, player(e)['y']
    while k < 90:
        e.step(0, *U_, 2); k += 1; p = player(e)
        if abs(p['y'] + 20) < 0.01 and prev > -19.99: break
        prev = p['y']
    if k >= 90: return None, []
    land = (round(p['x'], 2), round(p['z'], 2), e.fr)
    e.save(w + '/l.st'); offs = []
    for o in range(7):
        if not load(w + '/l.st'): continue
        for i in range(o): e.step(0, *U_, 2)
        e.step(CD, *U_, 2)
        if laki(e)['speed'] < 115.5: continue
        for i in range(60): e.step(0, 0, 0, 2)
        if player(e)['z'] > 1: offs.append(o)
    return land, offs
def group(a):
    fam, L1, D0, N = a
    e, w = G['e'], G['w']
    e.load(os.environ.get('START', 'states/pra01_topright_v2.st')); e.step(0, 0, 0, 2); e.fr = 0
    for i in range(10): e.step(0, *U_, 2)
    for i in range(10): e.step(0, *SD['R'], 2)
    if L1:
        e.step(B, *SD['L'], 2)
        for i in range(9 + L1): e.step(0, *SD['L'], 2)
    e.step(B, *SD['D'], 2)
    for i in range(9 + D0): e.step(0, *SD['D'], 2)
    for i in range(N): e.step(0x80 if i < 12 else 0, *SD['D'], 2)
    out = []
    if fam == 'H':
        e.step(B, *SD['L'], 2)
        k = 0
        while abs(player(e)['y'] + 10) > 0.01 and k < 90: e.step(0, *SD['L'], 2); k += 1
        if k >= 90: return out
        e.save(w + '/g.st')
        for K in range(1, 8):
            if not load(w + '/g.st'): continue
            for i in range(K - 1): e.step(0, *SD['L'], 2)
            x = player(e)['x']
            e.step(B, *U_, 2)
            land, offs = finish()
            out.append(((fam, L1, D0, N, K), round(x, 2), land, offs))
    else:
        e.step(0, 0, 0, 2)
        k = 0
        while player(e)['action'] != 9 and k < 90: e.step(0, *SD['L'], 2); k += 1
        if k >= 90: return out
        for i in range(8): e.step(0, 0, 0, 2)
        e.save(w + '/g.st')
        for T in (3, 4, 5, 6, 7):
            load(w + '/g.st')
            for i in range(T): e.step(0, *SD['L'], 2)
            e.step(0, 0, 0, 2); x = player(e)['x']
            e.save(w + '/t.st')
            for U in range(0, 45):
                if not load(w + '/t.st'): continue
                for i in range(U): e.step(0, 0, 0, 2)
                land, offs = finish()
                out.append(((fam, L1, D0, N, T, U), round(x, 2), land, offs))
    return out
if __name__ == '__main__':
    # run as 4 separate processes (PART=0..3): a multiprocessing pool with the emulator in a worker initializer hangs
    fam, outp = sys.argv[1], sys.argv[2]
    part, nparts = int(os.environ.get('PART', 0)), int(os.environ.get('NPARTS', 1))
    if fam == 'H': grid = [('H', L1, D0, N) for L1 in range(0, 10) for D0 in (2, 3, 4, 6) for N in range(18, 46)]
    else: grid = [('W', L1, D0, N) for L1 in range(0, 10, 3) for D0 in (4,) for N in range(20, 42)]
    grid = grid[part::nparts]
    init(); n = c = 0
    with open(outp, 'w') as f:
        for g in grid:
            for r in group(g):
                f.write(json.dumps(r) + '\n'); n += 1
                if r[3]: c += 1; print(r, flush=True)
            f.flush()
    print('done', n, 'runs,', c, 'clip', flush=True)
