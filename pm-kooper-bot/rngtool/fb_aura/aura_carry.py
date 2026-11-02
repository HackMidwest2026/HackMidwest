"""What happens to gRandSeed between the last aura frame and the next Power Bounce menu (Final Bowser phase 2).
Route used: phase-2 T1 = Peach Beam (the only way to remove Bowser's enchantment, i.e. the aura, and his defense 99),
Lakilester's first move on Bowser (Spiny Flip; A at fixed frames), Bowser's turn (A every 25 frames for text), T2 menu.
For each seed (DIAGNOSTIC: gRandSeed written on the frame the T1 menu opens; setup only) the same inputs are played and
every rand_int is logged by caller; per run it prints the aura's end frame, the draws per caller between the aura's
end and the T2 menu, Bowser's choice, and the total RNG steps. Optionally saves the T2 menu state (first seed).

Run from /tmp/claude-0/pm/bot1, debug core:
  M64P_DBG=1 PYTHONPATH=. python3 aura_carry.py SEED[,SEED...] [--save PATH] [--json OUT]"""
import sys, os, json, collections
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import *
from pm import *
from btl import *
from rngsim import *
from aura_probe import find_aura

NAMES = {0x800269AC: 'step', 0x80146D54: 'coin', 0xE00BC194: 'bolt', 0xE00D6838: 'aura'}
# T1 menu -> star spirits -> wrap up to Peach Beam -> target Bowser -> confirm
T1 = [(0, 30), ('down', 10), ('down', 10), (A, 20), ('up', 10), (A, 20), (A, 10)]


def play(e, sd, save=None):
    e.load('states/boss_2304_peach_start.st'); e.step(0, 0, 0, 2)
    n = 0
    while bstate(e) != 13 and n < 3000:
        e.step(A if (n % 15 == 0 and bstate(e) not in (13, 14, 17)) else 0, 0, 0, 2); n += 1
    e.w32(SEED, sd); e.w32(SEED2, sd)                      # DIAGNOSTIC: seed write at the T1 menu (setup only)
    base = find_aura(e)[0]
    e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
    log = []; F = [0]
    def st(b=0, y=0):
        t0 = e.s32(base + 0x14); e.step(b, 0, y, 2)
        ev = e.dbg_events()
        log.append(dict(f=F[0], bs=bstate(e), seed=e.u32(SEED), aura=e.s32(base + 0x14) == t0 + 1 and e.s32(base) == 4,
                        d=[(NAMES.get(x['ra'], hex(x['ra'])), x['a0']) for x in ev]))
        F[0] += 1
    for b, k in T1:
        y = -70 if b == 'down' else 70 if b == 'up' else 0; bb = 0 if isinstance(b, str) else b
        for j in range(k): st(bb if j == 0 else 0, y if j == 0 else 0)
    confirm = F[0] - 10
    # through the Peach Beam to Lakilester's menu
    while bstate(e) != 14 and F[0] < 4000: st(A if F[0] % 25 == 0 else 0)
    pm_ = F[0]
    for j in range(20): st()
    st(A); [st() for j in range(24)]; st(A)                 # first ability, target Bowser
    for j in range(400):
        st(A if j in (40, 60, 80) else 0)
        if bstate(e) in (20, 21): break
    while not (bstate(e) == 13 and log[-1]['bs'] == 13 and F[0] > pm_ + 200) and F[0] < 8000:
        st(A if F[0] % 25 == 0 else 0)
    for j in range(30): st()
    if save: e.save(save)
    return log, confirm, pm_


if __name__ == '__main__':
    seeds = [int(x, 16) for x in sys.argv[1].split(',')]
    save = sys.argv[sys.argv.index('--save') + 1] if '--save' in sys.argv else None
    jout = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/ac%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    allruns = []
    for k, sd in enumerate(seeds):
        log, confirm, pm_ = play(e, sd, save if k == 0 else None)
        aura_end = max(r['f'] for r in log if r['aura'])
        menu = len(log) - 30
        per = collections.Counter(); first = {}
        for r in log[aura_end + 1:menu]:
            for nm, a0 in r['d']:
                if nm == 'step': continue
                per[(nm, a0)] += 1; first.setdefault((nm, a0), r['f'] - aura_end)
        steps = 0; s = log[aura_end]['seed']
        # count LCG steps from the aura's last frame to the T2 menu
        while s != log[menu]['seed'] and steps < 200000: s = adv(s); steps += 1
        print('seed %08x: confirm f%d, aura last updated f%d (+%d after the confirm), Lakilester menu f%d, T2 menu f%d; '
              'RNG steps aura end -> T2 menu: %d (frames %d)' % (sd, confirm, aura_end, aura_end - confirm, pm_, menu, steps, menu - aura_end))
        print('   non-step draws after the aura (caller, max): count [first frame after aura end]:',
              ', '.join('%s/%d: %d [+%d]' % (k[0], k[1], c, first[k]) for k, c in sorted(per.items(), key=lambda t: first[t[0]])))
        allruns.append(dict(seed=sd, confirm=confirm, aura_end=aura_end, menu=menu, steps=steps, log=log))
    if jout: json.dump(allruns, open(jout, 'w'))
