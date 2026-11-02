"""(run from bot1/) FB2 Life Shroom revive: from states/fb2_diag_bowserturn.st (DIAGNOSTIC-built: Life Shroom added,
Mario 1 HP, Focus + Lakilester ability, saved in Bowser's turn), per seed (DIAGNOSTIC: written at the start):
frames from Mario's death (HP 0) to the next Mario menu (bstate 13), RNG steps over that window, draw classes, coin draws.
usage: M64P_DBG=1 _fbrevive.py N [shotseed]"""
import sys, os, random, collections, subprocess
from emu import *
from pm import *
from btl import *
from rngsim import *
N = int(sys.argv[1]); SHOT = os.environ.get('SHOTDIR')
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbr%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT)
rnd = random.Random(11)
for t in range(N):
    seed = rnd.getrandbits(32)
    e.dbg_log(0); e.load('states/fb2_diag_bowserturn.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed)                                    # DIAGNOSTIC
    e.dbg_log(1); e.dbg_events()
    death = None; steps = 0; cls = collections.Counter(); coins = []; L = []
    for f in range(2500):
        e.step(0, 0, 0, 2)
        ev = e.dbg_events()
        hp = e.s8(PLAYER_DATA + 2)
        if death is None and hp <= 0: death = f; s0 = e.u32(SEED)
        if death is not None:
            for x in ev:
                steps += 1 if x['ra'] == 0x800269AC else 0
                cls[hex(x['ra'])] += 1
                if x['ra'] == 0x80146D54: coins.append(f - death)
                if x['ra'] == 0xE00BC194: L.append(f - death)
            if SHOT and t == 0 and (f - death) % 40 == 0:
                subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '%s/r%04d.png' % (SHOT, f - death)], check=True)
        if death is not None and bstate(e) == 13: break
        if death is None and f > 1200: break
    dist = None
    if death is not None:
        s1 = e.u32(SEED); x = s0
        for i in range(20000):
            if x == s1: dist = i; break
            x = adv(x)
    print('RES seed %08x death %s menu_after %s steps %s light %d coins %s hp %d calls %s' % (seed, death, None if death is None else f - death, dist,
          len(L), coins, e.s8(PLAYER_DATA + 2), dict(cls)), flush=True)
