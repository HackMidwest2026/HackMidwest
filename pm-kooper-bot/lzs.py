"""loading zone storage jump primitive for nok_14.

a "ready" state is saved right before the game frame on which A must be pressed:
mario has just landed (action LAND, stick was neutral on the landing frame) and the
exit script is still waiting.  jump() presses A with a stick direction, holds A for
a_hold frames, keeps the stick held while airborne, and redoes the landing frame with
a neutral stick so the next jump can be chained.
"""
import math, os
from emu import *
from pm import *

CHANGING_MAP = 0x100000
AIRBORNE = (3, 4, 5, 8, 9)       # jump, bounce, hop, fall, step_down
LAND, STEP_DOWN_LAND = 10, 11

class Lzs:
    def __init__(self, e, tmpdir):
        self.e = e
        self.tmp = tmpdir
        os.makedirs(tmpdir, exist_ok=True)

    def frame(self, buttons, x, y):
        self.e.step(buttons, x, y, 2)

    def snapshot(self):
        e = self.e
        p = player(e)
        p['floor'] = e.s16(COLLISION + 2)
        p['below'] = e.s16(COLLISION + 6)
        p['changing'] = bool(e.u32(PLAYER + PS_ANIMFLAGS) & CHANGING_MAP)
        p['mode'] = e.s16(GAME_MODE)
        return p

    def jump(self, ready, out, sx, sy, a_hold, max_air=120, trace=None):
        """from ready state file, jump with stick (sx, sy) holding A for a_hold frames.
        returns (result, info) with result in: 'ready' (new ready state saved to out),
        'exit' (stored exit fired), 'void' (never landed), 'stuck' (not airborne after A)."""
        e = self.e
        e.load(ready)
        seq = []
        # first pass: find the landing frame with the stick held throughout
        land_at = None
        for f in range(max_air):
            b = A if f < a_hold else 0
            self.frame(b, sx, sy)
            s = self.snapshot()
            if trace is not None: trace.append(s)
            if s['changing'] or s['mode'] != GM_WORLD:
                return 'exit', s
            if f == 0 and s['action'] not in AIRBORNE:
                return 'stuck', s
            if f > 0 and s['action'] not in AIRBORNE:
                land_at = f
                break
        if land_at is None:
            return 'void', s
        # second pass: same inputs, but neutral stick on the landing frame
        e.load(ready)
        for f in range(land_at):
            self.frame(A if f < a_hold else 0, sx, sy)
        self.frame(0, 0, 0)
        s = self.snapshot()
        if s['changing'] or s['mode'] != GM_WORLD:
            return 'exit', s
        if s['action'] in AIRBORNE:
            # neutral stick changed the trajectory and mario is still in the air; keep falling neutral
            for f in range(max_air):
                self.frame(0, 0, 0)
                s = self.snapshot()
                if s['action'] not in AIRBORNE: break
            else:
                return 'void', s
        if s['action'] not in (LAND, STEP_DOWN_LAND):
            return 'exit', s     # landed into idle/walk: the exit fires next frame
        e.save(out)
        s['frames'] = land_at + 1
        return 'ready', s

    def make_first_ready(self, start, out):
        """from the nok14 start state: run left and jump onto deili1, then land with the exit stored."""
        e = self.e
        e.load(start)
        r = self.jump(start, out, -80, 0, 7)
        return r
