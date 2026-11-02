"""Frame-by-frame gRandSeed model of Final Bowser phase 2 while Bowser's aura is up and nothing else draws (battle menus,
target screens): per frame
  1. lightning: one rand_int(359) per bolt spawned this frame (two fixed loops, kkj_02 stage script:
     sky bolts waits 60/10/90/60 = 220 frames, low bolts 5/30/5/90 = 130 frames);
  2. the status-bar coin rand_int(100) when due (every 24 frames, 48 after a value >= 70);
  3. the aura (energy_in_out type 4, 16 parts, period 20): every part whose counter wraps draws rand_int(359)
     (its new angle), parts in index order 1..16;
  4. the per-frame step.
State for the model: seed, the 16 part counters, both bolt-loop phases, the coin's next frame.

Emulator check (run from /tmp/claude-0/pm/bot1, debug core):
  M64P_DBG=1 PYTHONPATH=. python3 aura_model.py check STATE N SEED [SEED...]
DIAGNOSTIC RAM write: gRandSeed after the load (setup only). The part counters and the coin's next frame are read
from the first run (they do not depend on the seed); the bolt phases are fitted to the first run's bolt frames and then
used unchanged; every frame's end seed and every aura angle is then predicted from the seed alone and compared."""
import sys, os
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
M = 0xFFFFFFFF
def adv(s): return (s * 0x5D588B65 + 1) & M
def internal(s, mx):
    d = M // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    """the game's rand_int (rngsim.py): 100 -> internal(1009) / 10; 1 -> internal(1000) >= 501; 0 -> no draw"""
    mx = abs(mx)
    if mx == 0: return s, 0
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)

SKY = (60, 10, 90, 60)      # EVS_RandomBolts waits (220)
LOW = (5, 30, 5, 90)        # EVS_CirculatingBolts waits (130)


def bolt_frames(first, idx, waits, N):
    """frames < N with a bolt from one loop: first bolt at `first` (>= 0), which is entry `idx` of the loop"""
    out = []; f = first; k = idx
    while f < N:
        out.append(f); f += waits[k % 4]; k += 1
    return out


class Aura:
    def __init__(self, seed, t, coin_next, bolts, per=20):
        self.s = seed & 0xFFFFFFFF; self.t = list(t); self.per = per; self.nc = coin_next; self.bolts = bolts
        self.f = 0

    def frame(self):
        """advance one frame; returns dict(seed_end, angles=[(part, value)], coin=value or None, bolts=n)"""
        f = self.f; out = dict(angles=[], coin=None, bolts=0)
        for _ in range(self.bolts.get(f, 0)):
            self.s, _ = rand_int(self.s, 359); out['bolts'] += 1
        if f == self.nc:
            self.s, v = rand_int(self.s, 100); out['coin'] = v; self.nc = f + (48 if v >= 70 else 24)
        for i in range(16):
            self.t[i] += 1
            if self.t[i] >= self.per:
                self.t[i] = 0; self.s, v = rand_int(self.s, 359); out['angles'].append((i + 1, v))
        self.s = adv(self.s); self.f += 1
        out['seed'] = self.s
        return out


def fit_bolts(frames, N):
    """bolt-frame dict from logged bolt frames (each loop's phase fitted; brute force over the first bolts)"""
    fs = sorted(frames)
    for a0 in range(0, 220):
        for ia in range(4):
            A = bolt_frames(a0, ia, SKY, N)
            if not set(A) <= set(fs): continue
            for b0 in range(0, 130):
                for ib in range(4):
                    B = bolt_frames(b0, ib, LOW, N)
                    cnt = {}
                    for x in A + B: cnt[x] = cnt.get(x, 0) + 1
                    exp = sorted(x for x, c in cnt.items() for _ in range(c))
                    if exp == fs: return cnt, (a0, ia, b0, ib)
    return None, None


if __name__ == '__main__' and sys.argv[1] == 'check':
    from emu import *
    from rngsim import SEED, SEED2, RAND_INT
    from aura_probe import find_aura, parts
    st, N, seeds = sys.argv[2], int(sys.argv[3]), [int(x, 16) for x in sys.argv[4:]]
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/am%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    def run(sd):
        e.load('states/' + st); e.step(0, 0, 0, 2)
        e.w32(SEED, sd); e.w32(SEED2, sd)                     # DIAGNOSTIC: seed write (setup only)
        base = find_aura(e)[0]
        t0 = [p['t'] for p in parts(e, base)[1]]
        e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
        log = []
        for f in range(N):
            e.step(0, 0, 0, 2)
            ev = e.dbg_events()
            P = parts(e, base)[1]
            log.append(dict(seed=e.u32(SEED), ras=[x['ra'] for x in ev], ang={i + 1: P[i]['ang'] for i in range(16)}))
        return t0, log
    t0, log = run(seeds[0])
    bolts = [f for f, r in enumerate(log) for ra in r['ras'] if ra == 0xE00BC194]
    coin = [f for f, r in enumerate(log) if 0x80146D54 in r['ras']]
    B, ph = fit_bolts(bolts, N)
    print('part counters at frame 0:', t0)
    print('bolts', len(bolts), 'loop phases (sky first, idx, low first, idx):', ph, '; first coin draw at frame', coin[0])
    other = sorted(set(ra for r in log for ra in r['ras']) - {0x800269AC, 0x80146D54, 0xE00BC194, 0xE00D6838})
    print('other callers in the first run:', [hex(x) for x in other])
    tot_ok = 0
    for sd in seeds:
        if sd != seeds[0]: _, log = run(sd)
        m = Aura(sd, t0, coin[0], B)
        ok = 0; first_bad = None; nang = 0; angok = 0; both = 0
        for f in range(N):
            o = m.frame()
            if o['bolts'] and o['coin'] is not None: both += 1
            for i, v in o['angles']:
                nang += 1
                if abs((log[f]['ang'][i] + 2) - v) < 1e-3: angok += 1
            if o['seed'] == log[f]['seed']: ok += 1
            elif first_bad is None: first_bad = f
        tot_ok += ok == N
        print('seed %08x: %d/%d frames end seed exact, %d/%d aura angles exact, frames with bolt + coin: %d, first miss %s'
              % (sd, ok, N, angok, nang, both, first_bad), flush=True)
    print('seeds fully matched: %d/%d' % (tot_ok, len(seeds)))
