"""v86: the Normal Boots Final Bowser phase-2 states (setup only). From states/boss_2304_nbg_menu.st (boss_battle_start_setup.py
2304 with AC=1 PARTNER=1 BRANK=1 BADGES=10c,e4,112,11f BOOTS=0 FP=10 HP=10 ITEMS=93,95,95,a3 NOFS=1 STARBEAM=2 SUF=_nbg:
Goombario Super, Normal Boots, Super Charge / Power Bounce / Close Call, the Peach Beam): T1 Peach Beam, Goombario Charge
(his box left to run out), Bowser's turn with A every 25 frames on his texts, to the T2 menu: states/boss_2304_nbg_t2menu.st.
DIAGNOSTIC: Mario's HP written (HP env, default 10) before T1 so that Bowser's T1 cannot end it.
Run from /tmp/claude-0/pm/bot1: PYTHONPATH=. python3 .../nb_p2_state.py [SEEDHEX]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
r = Run('nbp2', log=False)
seed = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1234
for attempt in range(40):
  r.load('/tmp/claude-0/pm/bot1/states/boss_2304_nbg_menu.st')
  r.seed(seed + attempt)                                               # DIAGNOSTIC: gRandSeed (setup only)
  r.e.w8(PLAYER_DATA + 2, int(os.environ.get('HP', '10')))             # DIAGNOSTIC: Mario's HP
  r.set_bowser_hp(int(os.environ.get('BHP', '89')))                    # DIAGNOSTIC: Bowser's HP (the runner's phase 1 leaves 89)
  r.settle(MENU, 20)
  def enchanted():
      a = r.e.u32(BSTATUS + 0xE0); part = r.e.u32(a + 0x1F4); return int(bool(r.e.u32(part + 0x7C) & 0x00080000))
  print('T1 menu: aura', enchanted(), 'hp', r.e.s8(PLAYER_DATA + 2), 'fp', r.e.s8(PLAYER_DATA + 5), 'bowser', r.bowser_hp(), flush=True)
  r.peach_beam(0)
  n = 0
  while bstate(r.e) != 14 and n < 3000: r.step(A if (n % 25 == 24 and bstate(r.e) not in (13, 14, 17)) else 0); n += 1
  print('after the beam: state', bstate(r.e), 'frames', n, 'aura', enchanted(), flush=True)
  r.idle(10); r.seq([(A, 0, 25), (0, DOWN, 25), (0, DOWN, 25), (A, 0, 10)]); r.wait_state((17,), cap=60, adv_text=False); r.idle(5); r.step(A)   # Abilities, Charge, target (Goombario), A
  st = r.wait_state((13,), cap=4000)
  print('T2 menu: state', st, 'hp', r.e.s8(PLAYER_DATA + 2), 'aura', enchanted(), 'bowser', r.bowser_hp(), 'glow', r.e.s8(r.e.u32(BSTATUS + 0xDC) + 0x220), flush=True)
  a = r.e.u32(BSTATUS + 0xE0); va = [r.e.s32(a + 0x88 + 4 * i) for i in range(8)]; print('vars', va)
  if st == 13 and va[4] != 0: break                                  # not the Claw Swipe (it poisons Mario: 1 HP a turn)
  print('Claw Swipe on T1 (poison): next seed', flush=True)
r.idle(20); r.e.save('/tmp/claude-0/pm/bot1/states/boss_2304_nbg_t2menu.st')
