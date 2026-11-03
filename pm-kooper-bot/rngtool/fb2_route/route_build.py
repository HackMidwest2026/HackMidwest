"""Play the whole FB2 route T1..T7 from the phase-2 start and keep Bowser missing by choosing the partner's confirm
frame (the lever; Mario's own confirm when Lakilester is KO'd): for each turn, from the settled partner menu, every partner-confirm delay 0..MAXD is played through
Bowser's turn to the next Mario menu, and the outcome (Mario HP unchanged = miss) is recorded. The first working delay is
kept and the next turn starts from its Mario menu. Saves the menu states for the later studies.

Setup (DIAGNOSTIC, labelled): Mario HP 5 (Danger, as in the route), Bowser HP (default 80 of 99, so that 7 bounces from a 15-damage first hit (15+14+...+9) are the kill; the real value comes
from phase 1), gRandSeed written at the T1 menu.
Run from /tmp/claude-0/pm/bot1 (normal core is fine):
  PYTHONPATH=. python3 route_build.py SEEDHEX OUTDIR [MAXD] [BOWSER_HP]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *

# (Mario action, its menu moves (wheel, submenu) given what the menus remember from the previous turn, partner action)
# Super Charges done by the end of turn t (the T4 wave must miss: it drains the charges)
CHARGES = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 4}
TURNS = [('charge', dict(wheel=0, sub=2), 'cloud_nine'), ('charge', dict(wheel=0, sub=2), 'do_nothing'),
         ('jelly', dict(wheel=-1, sub=0), 'do_nothing'), ('charge', dict(wheel=1, sub=2), 'do_nothing'),
         ('peach_beam', dict(wheel=2, sub=-1), 'do_nothing'), ('charge', dict(wheel=-2, sub=2), 'do_nothing'),
         ('power_bounce', dict(wheel=0, sub=1), None)]


def aura_up(e):
    """1 if Bowser's first part (partsTable, actor+0x1F4) has ACTOR_EVENT_FLAG_STAR_ROD_ENCHANTED (eventFlags +0x7C)"""
    a = e.u32(BSTATUS + 0xE0); part = e.u32(a + 0x1F4)
    return int(bool(e.u32(part + 0x7C) & 0x00080000)) if part else -1


def items(e):
    return [e.s16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10) if e.s16(PLAYER_DATA + 0x1B4 + 2 * i) > 0]


def build(seed, out, maxd=40, bhp=80, start='/dev/shm/fb2r/t1menu.st'):
    os.makedirs(out, exist_ok=True)
    r = Run('rb', log=False)
    r.load(start)
    r.e.w8(PLAYER_DATA + 2, 5)                               # DIAGNOSTIC: Mario HP 5 (Danger)
    r.set_bowser_hp(bhp)                                     # DIAGNOSTIC: Bowser HP
    r.seed(seed)                                             # DIAGNOSTIC: gRandSeed at the T1 menu
    r.e.save(out + '/t1_menu.st')
    report = []
    for t, (ma, mv, pa) in enumerate(TURNS, 1):
        r.load(out + '/t%d_menu.st' % t)
        if pa is None:
            break
        ko = r.partner_ko()[0] != 0
        lever = 'mario' if ko else 'partner'
        if not ko:
            getattr(r, ma)(0, **mv); r.settle((14,)); r.e.save(out + '/t%d_partner.st' % t)
        res = []; kept = None
        for dl in range(maxd + 1):
            if ko:
                r.load(out + '/t%d_menu.st' % t); getattr(r, ma)(dl, **mv)
            else:
                r.load(out + '/t%d_partner.st' % t); getattr(r, pa)(dl)
            st = r.wait_state((13,), cap=4000)
            ok = st == 13 and r.e.s8(PLAYER_DATA + 2) == 5 and 149 in items(r.e) and r.e.s8(BSTATUS + 0x97) >= 3 * CHARGES[t]
            res.append(int(ok))
            if ok and kept is None:
                kept = dl; r.idle(20); r.e.save(out + '/t%d_menu.st' % (t + 1))
        report.append(dict(turn=t, mario=ma, partner=pa if not ko else 'KO', lever=lever, kept=kept,
                           miss_by_delay=''.join(map(str, res)), p_miss=sum(res) / len(res)))
        print(json.dumps(report[-1]), flush=True)
        if kept is None:
            print('no working delay at T%d' % t); break
        r.load(out + '/t%d_menu.st' % (t + 1))
        print('   T%d menu: hp %d fp %d jumpCharge %d cloud9 %d bowser %s enchanted %d partnerKO %s items %s' % (
              t + 1, r.e.s8(PLAYER_DATA + 2), r.e.s8(PLAYER_DATA + 5), r.e.s8(BSTATUS + 0x97), r.e.s8(BSTATUS + 0xA4),
              r.bowser_hp(), aura_up(r.e), r.partner_ko(), items(r.e)), flush=True)
    json.dump(report, open(out + '/report.json', 'w'))
    return report


if __name__ == '__main__':
    build(int(sys.argv[1], 16), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 40,
          int(sys.argv[4]) if len(sys.argv) > 4 else 80)
