"""Jr. Troopa (final) RNG model per game frame, from the Charge rays to the rolls that matter (JP).
Same semantics as pmrng_core.js frameEv/works (and readouts/charge_model.py for the rays):
  per frame: battle-script draws ('pre'), energy_in_out creation (rand(360), then per part rand(10) speed, rand(10)
  phase), the status-bar coin (rand(100) on its 24/48 schedule), effect-overlay draws after the coin ('post'),
  energy_in_out updates (each part redraws rand(359) when its 10-frame counter wraps, from creation until removal),
  the per-frame rand_int(1).
Events are keyed by the frame of the confirm that causes them. Rolls are 'pre' draws with a name; their values are
returned. Offsets: pmrng_core.js TURNS / PROFILES (emulator-measured), re-checked here by jc_check.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
M32 = 0xFFFFFFFF
def adv(s): return (s * 0x5D588B65 + 1) & M32
def internal(s, mx):
    d = M32 // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    mx = abs(mx)
    if mx == 0: return s, 0
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)
X = lambda n, m: [m] * n
# offset -> list of draws; a draw is a max or (max, roll name)
TURNS = {
    'charge':      {'eio': [(13, 58), (16, 61)]},                                   # (Super) Charge confirm
    'bomb':        {'pre': {73: X(8, 359)}, 'post': {73: [360]}},                    # Bombette's Bomb confirm (explosion)
    'bomb_cc':     {'pre': {73: X(8, 359), 179: [(100, 'cc')]}, 'post': {73: [360]}},  # Bomb, then Jr. Troopa hits Mario at < 6 HP
    'syrup_cc':    {'pre': {118: [359, 10, 10] * 10, 163: [(100, 'cc')]}},          # Maple Syrup, then the hit (Close Call)
    'nothing_cc':  {'pre': {26: [(100, 'cc')]}},                                    # Bombette does nothing, then the hit
    'bomb_t1':     {'pre': {73: X(8, 359), 206: X(10, 359)}, 'post': {73: [360]}},   # T1 Bomb + Jr. Troopa's T1 hit at 10 HP (no roll)
    'syrup_hit':   {'pre': {118: [359, 10, 10] * 15, 190: X(10, 359)}},           # Maple Syrup at 10 HP (after a revive): 15 sparkles, no roll, the hit
    'nothing_hit': {'pre': {53: X(10, 359)}},                                      # do nothing at 10 HP: no roll, the hit
    'whacka':      {'pre': {118: [359, 10, 10] * 22, 190: X(10, 359)}},             # Whacka's Bump + Jr. Troopa's T2 turn (10 HP)
    'pb':          {'pre': {52: X(11, 359), 78: [(100, 'pb1')], 79: X(11, 359), 105: [(100, 'pb2')], 106: X(10, 359),
                            132: [(100, 'pb3')], 133: X(10, 359), 159: [(100, 'pb4')]}},   # Power Bounce cap rolls (<= 140/98/68/47)
}
PB_CAP = [140, 98, 68, 47]
class Sim:
    def __init__(self, s, nc):
        self.s = s & M32; self.nc = nc; self.inst = []; self.ev = {}; self.rolls = {}; self.coins = []
    def add(self, f, name, turns=TURNS):
        T = turns[name]
        for k in ('pre', 'post'):
            for o, L in T.get(k, {}).items(): self.ev.setdefault(f + o, {'pre': [], 'post': [], 'eio': []})[k].extend(L)
        for c, rm in T.get('eio', []): self.ev.setdefault(f + c, {'pre': [], 'post': [], 'eio': []})['eio'].append(f + rm)
        return self
    def _draw(self, d):
        if isinstance(d, tuple): self.s, v = rand_int(self.s, d[0]); self.rolls[d[1]] = v
        else: self.s, _ = rand_int(self.s, d)
    def frame(self, f):
        e = self.ev.get(f)
        if e:
            for d in e['pre']: self._draw(d)
            for rm in e['eio']:
                self.s, _ = rand_int(self.s, 360); p = []
                for i in range(10): self.s, _ = rand_int(self.s, 10); self.s, v = rand_int(self.s, 10); p.append(-v)
                self.inst.append([rm, p])
        if f == self.nc:
            self.s, v = rand_int(self.s, 100); self.nc = f + (48 if v >= 70 else 24); self.coins.append((f, v))
        if e:
            for d in e['post']: self._draw(d)
        for I in self.inst:
            if f < I[0]:
                p = I[1]
                for i in range(10):
                    p[i] += 1
                    if p[i] >= 10: p[i] = 0; self.s, _ = rand_int(self.s, 359)
        self.inst = [I for I in self.inst if f + 1 < I[0]]
        self.s, _ = rand_int(self.s, 1)
    def run(self, f0, f1):
        for f in range(f0, f1): self.frame(f)
        return self
    def copy(self):
        import copy; return copy.deepcopy(self)
def lucky(v): return v < 30
def pb_hits(R):
    """bounces landed (>= 5 means the first three cap rolls passed; 6+ = four)"""
    n = 2
    for k in range(4):
        if R.get('pb%d' % (k + 1)) is None or R['pb%d' % (k + 1)] > PB_CAP[k]: return n
        n += 1
    return n   # 6 = 6 or more (the 5th cap roll is not modelled; 6 hits kill Jr. Troopa on this route)
