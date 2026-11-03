"""Dump the route-relevant parts of a Final Bowser phase-2 savestate (read only; no RAM writes).
Mario HP/FP, equipped badges, items, partner ranks, star power, BattleStatus charge / Cloud Nine fields, battle state.
Run from /tmp/claude-0/pm/bot1:  PYTHONPATH=. python3 .../fb2_state.py STATE [STATE ...]"""
import sys, os, json
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
NAMES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'item_names.json')))
PARTNERS = ['-', 'Goombario', 'Kooper', 'Bombette', 'Parakarry', 'Goompa', 'Watt', 'Sushie', 'Lakilester', 'Bow',
            'Goombaria', 'Twink']


def dump(e):
    P = PLAYER_DATA
    out = dict(hp=e.s8(P + 2), maxhp=e.s8(P + 3), fp=e.s8(P + 5), maxfp=e.s8(P + 6), boots=e.s8(P), hammer=e.s8(P + 1),
               partner=PARTNERS[e.s8(P + 0x12)],
               partner_ranks={PARTNERS[i]: e.s8(P + 0x14 + 8 * i + 1) for i in range(1, 12) if e.s8(P + 0x14 + 8 * i)},
               badges=[NAMES[e.s16(P + 0x208 + 2 * i)] for i in range(64) if e.s16(P + 0x208 + 2 * i) > 0],
               items=[NAMES[e.s16(P + 0x1B4 + 2 * i)] for i in range(10) if e.s16(P + 0x1B4 + 2 * i) > 0],
               star_power=e.s16(P + 0x290), max_star=e.s8(P + 0x28E), star_beam=e.s8(P + 0x292),
               bstate=bstate(e), jumpCharge=e.s8(BSTATUS + 0x97), hammerCharge=e.s8(BSTATUS + 0x96),
               cloud9=e.s8(BSTATUS + 0xA4), seed='%08x' % e.u32(0x800743F0))
    return out


if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/st%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    for st in sys.argv[1:]:
        e.load(st); e.step(0, 0, 0, 2)
        print(os.path.basename(st), json.dumps(dump(e)))
