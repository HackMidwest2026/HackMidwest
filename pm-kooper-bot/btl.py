"""battle helpers (JP): gBattleState, reaching Mario's first menu from a boss start state."""
from emu import *
from pm import *
BSTATE = 0x800DC048          # gBattleState (JP; found via gCurrentBattleID at 0x800DC4C8 - 0x480)
BSTATUS = 0x800DC050         # gBattleStatus
def bstate(e): return e.s32(BSTATE)
def to_first_menu(e, cap=3000):
    """advance intro text with A (only while not in a menu) until Mario's menu (13) is up; returns steps used"""
    seen = []
    for f in range(cap):
        s = bstate(e)
        if not seen or seen[-1] != s: seen.append(s)
        if s == 13 and f > 0: break
        e.step(A if (f % 15 == 0 and s not in (13, 14, 17)) else 0, 0, 0, 2)
    for i in range(20): e.step(0, 0, 0, 2)
    print('battle states seen', seen[-15:], flush=True)
    return f
