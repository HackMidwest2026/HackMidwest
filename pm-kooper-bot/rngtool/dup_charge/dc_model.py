"""Duplighosts x4 (battle 0x2402), the runner's T1: Mario Super Charge (rays), Charge popup A, Bombette Do Nothing,
enemy turn. Per-frame RNG model from the Charge confirm to the 4 copy rolls (JP).
Builds on ../jr_charge/jc_model.py (same per-frame order: script draws, energy_in_out creation, status-bar coin,
post draws, energy_in_out updates, per-frame rand_int(1)); adds the Duplighosts' branching enemy turn:
  first copy roll RandInt(1000) at Do Nothing confirm + 13; a copy (< 600) -> next roll +97;
  a failed copy (flying tackle) -> fx_firework 8 x rand(359) at +34 and the next roll at +78.
All of these are script draws ('pre', before the coin on the same frame). Emulator-checked by dc_check.py."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'jr_charge'))
import jc_model as JM
rand_int, adv = JM.rand_int, JM.adv
ROLL0, COPY_NEXT, FAIL_FX, FAIL_NEXT = 13, 97, 34, 78


class DSim(JM.Sim):
    def __init__(self, s, nc):
        super().__init__(s, nc)
        self.dup = None; self.copy_rolls = []          # [(frame, value)]

    def nothing(self, f):
        """Bombette's Do Nothing confirm on frame f (the enemy turn follows)"""
        self.dup = {'next': f + ROLL0, 'fx': {}}
        return self

    def frame(self, f):
        d = self.dup
        if d is not None:
            for i in range(d['fx'].pop(f, 0)): self.s, _ = rand_int(self.s, 359)
            if f == d['next'] and len(self.copy_rolls) < 4:
                self.s, v = rand_int(self.s, 1000); self.copy_rolls.append((f, v))
                if v < 600: d['next'] = f + COPY_NEXT
                else: d['fx'][f + FAIL_FX] = 8; d['next'] = f + FAIL_NEXT
        super().frame(f)

    def copies(self):
        return sum(1 for f, v in self.copy_rolls if v < 600)

    def done(self):
        return len(self.copy_rolls) == 4 and not (self.dup and self.dup['fx'])


def table(s, nc, f0, n):
    """copies for a Do Nothing confirm on each frame f0 .. f0+n-1, from (s, nc) at the start of frame f0 (fast:
    the base state is stepped once per frame, each candidate branches from it)"""
    base = JM.Sim(s, nc); out = []
    for d in range(f0, f0 + n):
        out.append(_from(base.s, base.nc, d))
        base.frame(d)
    return out


def _from(s, nc, C):
    """copies (0-4; 2 means '2 or fewer') for Do Nothing on frame C, given (s, nc) at the start of frame C"""
    f = C; nxt = C + ROLL0; fx = {}; k = 0; cp = 0; fails = 0
    while k < 4:
        n = fx.pop(f, 0)
        for i in range(n): s, _ = rand_int(s, 359)
        if f == nxt:
            s, v = rand_int(s, 1000); k += 1
            if v < 600: cp += 1; nxt = f + COPY_NEXT
            else:
                fails += 1
                if fails >= 3: return cp
                fx[f + FAIL_FX] = 8; nxt = f + FAIL_NEXT
        if f == nc: s, v = rand_int(s, 100); nc = f + (48 if v >= 70 else 24)
        s, _ = rand_int(s, 1); f += 1
    return cp
