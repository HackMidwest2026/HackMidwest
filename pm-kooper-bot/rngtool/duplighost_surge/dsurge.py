"""Duplighosts x4 (battle 0x2402), Lakilester (Super) out, Bombette in the party: shared emulator driver.

Turn 1 as the runner plays it: Z (partner first) -> Lakilester: Abilities > Spiny Surge (mash) -> Mario: Strategies >
Change Member > Bombette (the confirm) -> enemy turn (each Duplighost: RandInt(1000) < 600 = copy).

Every rand_int call is logged with its frame, max, caller (ra) and value (debug core, M64P_DBG=1), and the seed is
replayed in Python to check the log is complete (compared with gRandSeed at the end).
State: states/boss_2402_laki_menu.st, made with
  PARTNER=8 BRANK=1 BADGES=121,112,11f NOFS=1 SUF=_laki boss_battle_start_setup.py 2402
AC=1 (DIAGNOSTIC SETUP like the Bombette state boss_2402_bomb_menu.st: same badges/HP/FP; Lakilester Super rank).
Run from /tmp/claude-0/pm/bot1 with PYTHONPATH=. (emu.py, btl.py, rngsim.py, the ROM and states live there)."""
import os, sys, subprocess
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
from rngsim import *

STATE = 'states/boss_2402_laki_menu.st'
COIN_RA = 0x80146D54            # status-bar coin rand_int(100)
FRAME_RA = 0x800269AC           # rand_int(1) once per game frame (the "per-frame step" of the other tools' models)
FIREWORK_RA = 0xE00861EC        # fx_firework part angles, rand_int(359)
COPY_RA = 0x802D46E0            # evt RandInt (Duplighost copy roll: max 1000)
SPINY_RA = (0x80238AD0, 0x80238AE8, 0xE00C819C, 0xE00C81B4)
# controller stick: y > 0 is up on the menus (e2e_dup.py: (0, 0, 70) twice = Mario's wheel to Strategies)
UP, DOWN, LEFT = (0, 70), (0, -70), (-80, 0)


class Run:
    def __init__(self, seed, state=STATE, shots=None, tag='r'):
        self.e = Emu('pm-jp.z64', '/dev/shm/pmbot/dsg%d' % os.getpid())
        self.shots = shots; self.tag = tag
        self.reset(seed, state)

    def reset(self, seed, state=STATE):
        e = self.e
        e.load(state); e.step(0, 0, 0, 2)
        self.dbg = os.environ.get('M64P_DBG') == '1'
        if self.dbg: e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
        if seed is not None:
            e.w32(SEED, seed); e.w32(SEED2, seed)           # DIAGNOSTIC: chosen seed (stands in for the run's seed)
        self.s = e.u32(SEED); self.f = 0; self.log = []; self.states = []; self.marks = {}

    def step(self, b=0, x=0, y=0):
        e = self.e
        seed_before = self.s
        e.step(b, x, y, 2)
        ev = []
        for x_ in (e.dbg_events() if self.dbg else []):
            mx = x_['a0'] if x_['a0'] < 0x80000000 else x_['a0'] - (1 << 32)
            self.s, v = rand_int(self.s, mx)
            ev.append((mx, x_['ra'], v))
        bs = bstate(e)
        self.log.append({'f': self.f, 'seed0': seed_before, 'ev': ev, 'bs': bs})
        if not self.states or self.states[-1][1] != bs: self.states.append((self.f, bs))
        if self.shots and self.shots.get('on'): self.shot()
        self.f += 1

    def check(self):
        """the replayed seed must equal the game's (else the log missed a draw)"""
        return self.s == self.e.u32(SEED)

    def shot(self, name=None):
        d = self.shots['dir']; os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name or '%s%05d.png' % (self.tag, self.f))
        subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', p], check=True)

    def wait(self, n):
        for i in range(n): self.step()

    def press(self, b=0, xy=(0, 0), hold=1, after=0):
        for i in range(hold): self.step(b, *xy)
        self.wait(after)

    def until(self, states, cap=4000):
        for i in range(cap):
            if bstate(self.e) in states: return i
            self.step()
        raise RuntimeError('state %d not in %s' % (bstate(self.e), states))

    # ---- the turn ----
    def surge(self, on=1, off=1, dur=170, flicks=None, pre=15, delay=0):
        """Z, then Lakilester: Abilities > Spiny Surge, then the stick mash: left `on` frames, neutral `off` frames,
        repeated for `dur` frames (or `flicks` cycles, then neutral), after `delay` neutral frames. The mash window
        itself is 60 frames and opens ~40 frames after the target confirm."""
        self.wait(pre)
        self.press(Z, after=1); self.until([14]); self.wait(10)
        self.press(A, after=25)                                  # Abilities
        self.press(0, DOWN, after=12)                            # Spiny Surge (2nd in the list)
        self.marks['pick'] = self.f
        self.press(A, after=25)                                  # pick the move
        for k in range(6): self.step(A)                          # any target confirm
        per = on + off
        self.wait(delay)
        for f in range(dur - delay):
            mash = flicks is None or f // per < flicks
            self.step(0, *(LEFT if mash and f % per < on else (0, 0)))
        self.marks['mash_end'] = self.f

    def fireworks(self):
        """(frame, draws) of each firework (one per damaged enemy: 6 draws = damage 1-2, 8 = damage 3-4)"""
        return [(r['f'], sum(1 for mx, ra, v in r['ev'] if ra == FIREWORK_RA)) for r in self.log
                if any(ra == FIREWORK_RA for mx, ra, v in r['ev'])]

    def to_mario_menu(self):
        self.until([13]); self.marks['mario_menu'] = self.f

    def spinies(self, lo=None):
        """frames of each spiny's 4 draws"""
        out = []
        for r in self.log[lo or 0:]:
            for mx, ra, v in r['ev']:
                if ra == SPINY_RA[0]: out.append(r['f'])
        return out

    def copy_rolls(self):
        return [(r['f'], v) for r in self.log for mx, ra, v in r['ev'] if ra == COPY_RA and mx == 1000]

    # Mario: Strategies (wheel up 2) > Change Member (1st) > Bombette (the list opens on Lakilester, Bombette is 1 up)
    SWITCH = [(0, UP), (0, UP), (A, (0, 0)), (A, (0, 0)), (0, UP), (A, (0, 0))]

    def switch(self, at):
        """at: frames after Mario's menu came up (marks['mario_menu']) for each of the 6 inputs; the last is the
        confirm. One-frame presses (stick back to neutral the next frame)."""
        m = self.marks['mario_menu']
        for (b, xy), t in zip(self.SWITCH, at):
            assert m + t >= self.f, (t, self.f - m)
            self.wait(m + t - self.f)
            self.step(b, *xy)
        self.marks['confirm'] = m + at[-1]

    def enemy_turn(self, cap=1500):
        """step until the 4 copy rolls are logged and the next player menu is up (or cap)"""
        for i in range(cap):
            if len(self.copy_rolls()) >= 4 and bstate(self.e) == 13: return True
            self.step()
        return False

    def partner(self):
        return self.e.u8(PLAYER_DATA + 0x12)

    def snapshot(self, path):
        """savestate + the Python-side log, to branch several confirms off one Surge"""
        self.e.save(path)
        self._snap = (path, self.s, self.f, list(self.log), list(self.states), dict(self.marks))

    def restore(self):
        path, self.s, self.f, log, states, marks = self._snap
        self.log, self.states, self.marks = list(log), list(states), dict(marks)
        self.e.load(path)
        if self.dbg: self.e.dbg_events()
        assert self.e.u32(SEED) == self.s, 'restore: seed mismatch'
