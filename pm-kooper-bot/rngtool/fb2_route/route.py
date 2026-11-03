"""Final Bowser phase 2 route player (JP, emulator).  Run scripts that import this from /tmp/claude-0/pm/bot1 with the
debug core (M64P_DBG=1) when draws are logged.

Route (runner): T1 Super Charge + Lakilester Cloud Nine; T2-T7 Lakilester "Do Nothing" (Strategies -> nanimo shinai);
T2 Charge, T3 Jammin' Jelly, T4 Charge, T5 Peach Beam, T6 Charge, T7 Power Bounce.
Every action is a menu sequence whose LAST A is the confirm; `delay` = idle frames inserted before that confirm.
One step = one game frame (2 VIs), as in the other rngtool emulator scripts.

DIAGNOSTIC writes (setup only, labelled where done): Mario HP (route enters phase 2 at Danger), gRandSeed."""
import os, sys
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
from rngsim import *

UP, DOWN = 70, -70
NAMES = {0x800269AC: 'step', 0x80146D54: 'coin', 0xE00BC194: 'bolt', 0xE00D6838: 'aura', 0x802D46E0: 'evt',
         0x802774B0: 'testtgt', 0x802A1168: 'pbroll', 0xE00861EC: 'firework', 0x80266DE4: 'r266de4'}
MENU = (13, 14)


class Run:
    def __init__(self, tag='r', log=True):
        self.e = Emu('pm-jp.z64', '/dev/shm/pmbot/%s%d' % (tag, os.getpid()))
        for i in range(60): self.e.step(0, 0, 0, 2)
        self.logging = log
        self.f = 0; self.rows = []; self.marks = {}

    def load(self, st):
        e = self.e
        e.load(st); e.step(0, 0, 0, 2)
        if self.logging:
            e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
        self.f = 0; self.rows = []; self.marks = {}

    def seed(self, s):
        self.e.w32(SEED, s); self.e.w32(SEED2, s)            # DIAGNOSTIC: gRandSeed write (setup only)

    def step(self, b=0, y=0):
        e = self.e
        s0 = e.u32(SEED); e.step(b, 0, y, 2)
        d = []
        if self.logging:
            for x in e.dbg_events():
                d.append((NAMES.get(x['ra'], '%08x' % x['ra']), x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)))
        self.rows.append(dict(f=self.f, b=b, y=y, bs=bstate(e), s0=s0, s1=e.u32(SEED), d=d))
        self.f += 1

    def shot(self, name):
        if os.environ.get('M64P_GFX') and os.environ.get('SHOTDIR'):
            import subprocess
            os.makedirs(os.environ['SHOTDIR'], exist_ok=True)
            subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage',
                            '%s/%s.png' % (os.environ['SHOTDIR'], name)], check=True)

    def idle(self, n):
        for i in range(n): self.step()

    def seq(self, items, delay=0, mark=None):
        """items: list of (button, y, frames_after). The last item is the confirm; `delay` idle frames precede it."""
        for i, (b, y, n) in enumerate(items):
            if i == len(items) - 1:
                self.idle(delay)
                if mark: self.marks[mark] = self.f
            self.step(b, y)
            self.idle(n - 1)
            if os.environ.get('SHOTSEQ'): self.shot('%s_%d_%d' % (mark, self.f, i))

    def wait_state(self, want, cap=6000, adv_text=True):
        """step until bstate in want; A every 25 frames while outside menus/targeting if adv_text (text boxes)."""
        n = 0
        while bstate(self.e) not in want and n < cap:
            self.step(A if (adv_text and n % 25 == 24 and bstate(self.e) not in (13, 14, 17)) else 0); n += 1
        return bstate(self.e)

    # ---- Mario actions (from Mario's menu). The wheel and the submenus remember the last choice, so each action takes
    # `wheel` (stick moves on the wheel: + down, - up) and `sub` (moves in the submenu) for the route's turn order.
    def moves(self, k):
        return [(0, DOWN if k > 0 else UP, 10)] * abs(k)

    def charge(self, delay=0, wheel=0, sub=2):
        self.seq(self.moves(wheel) + [(A, 0, 20)] + self.moves(sub) + [(A, 0, 15), (A, 0, 1)], delay, 'charge')

    def jelly(self, delay=0, wheel=-1, sub=0):
        self.seq(self.moves(wheel) + [(A, 0, 20)] + self.moves(sub) + [(A, 0, 15), (A, 0, 1)], delay, 'jelly')

    def peach_beam(self, delay=0, wheel=2, sub=-1):
        self.seq(self.moves(wheel) + [(A, 0, 20)] + self.moves(sub) + [(A, 0, 20), (A, 0, 1)], delay, 'peach')

    def power_bounce(self, delay=0, wheel=0, sub=1):
        self.seq(self.moves(wheel) + [(A, 0, 20)] + self.moves(sub) + [(A, 0, 15), (A, 0, 1)], delay, 'pb')

    # ---- partner (from the partner menu, wheel on Abilities) ----
    def cloud_nine(self, delay=0, ac=(132, 152, 172)):
        self.seq([(A, 0, 20), (0, DOWN, 10), (0, DOWN, 10), (A, 0, 15), (A, 0, 1)], delay, 'cn')
        t0 = self.f
        while self.f - t0 < 260:
            k = self.f - t0
            self.step(A if k in ac else 0)

    def do_nothing(self, delay=0):
        self.seq([(0, UP, 10), (A, 0, 20), (0, DOWN, 10), (A, 0, 1)], delay, 'nothing')

    def set_bowser_hp(self, hp):
        a = self.e.u32(BSTATUS + 0xE0); self.e.w8(a + 0x1B8, hp)   # DIAGNOSTIC: Bowser HP (route value unknown)

    def partner_ko(self):
        """(koStatus, koDuration) of the partner actor"""
        a = self.e.u32(BSTATUS + 0xDC)
        return (self.e.s8(a + 0x216), self.e.s8(a + 0x217)) if a else None

    def bowser_hp(self):
        a = self.e.u32(BSTATUS + 0xE0)
        return (self.e.s8(a + 0x1B8), self.e.s8(a + 0x1B9)) if a else None

    def settle(self, want, n=20):
        """wait for a menu state, then n idle frames (menus ignore inputs for a few frames after opening)"""
        s = self.wait_state(want); self.idle(n); return s

    def cnt(self, a, b, kinds=None):
        """non-step draws in rows[a:b] as list of (frame, name, max)"""
        out = []
        for r in self.rows[a:b]:
            for nm, mx in r['d']:
                if nm != 'step' and (kinds is None or nm in kinds): out.append((r['f'], nm, mx))
        return out

    def steps(self, a, b):
        """LCG steps between the start of row a and the start of row b"""
        s = self.rows[a]['s0']; t = self.rows[b]['s0'] if b < len(self.rows) else self.e.u32(SEED); k = 0
        while s != t and k < 1000000: s = adv(s); k += 1
        return k
