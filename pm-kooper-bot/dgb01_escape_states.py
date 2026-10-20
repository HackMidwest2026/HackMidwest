"""Build the Tubba-escape savestates by playing the real sequence (needs states/dgb01_e6_woke.st, made with
PRA_MAP=dgb_01 PRA_AREA=15 PRA_ENTRY=6 GB_SET="0x0=0xE3" STATE_SUFFIX=_woke python3 make_state_pra.py).
3F east, story TUBBA_WOKE_UP: walk left until x < 100 (smash-bridges cutscene), mash A through Tubba's line,
get kicked into dgb_08 2F (entry 1) -> states/dgb08_e1_kicked.st; hold left + A into the door back to dgb_01
2F east (entry 4, Tubba on the broken bridge) -> states/dgb01_e4_ctrl.st at the first controllable frame.
A is pressed 2 frames on / 2 off (the game polls at 30 fps)."""
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/escstates')
e.load('states/dgb01_e6_woke.st')
f = 0
while where(e)[1] == 1 and f < 4000:
    x = player(e)['x']
    e.step(A if (f // 2) % 2 and x < 100 else 0, -80 if x >= 99.5 else 0, 0, 1); f += 1
for k in range(400): e.step(0, 0, 0, 1)
print('kicked into', where(e), player(e), 'story', e.s8(STORY))
e.save('states/dgb08_e1_kicked.st')
e.step(0, 0, 0, 1)
f = 0
while where(e)[1] == 8 and f < 600:
    e.step(A if (f // 2) % 2 else 0, -80, 0, 1); f += 1
k = 0
while True:
    e.step(0, 0, 0, 1); k += 1
    if k > 60 and player(e)['flags'] == 1: break
print('control in', where(e), player(e), 'tubba', [(n['x'], n['y'], n['z']) for n in npcs(e) if n['id'] == 4])
e.save('states/dgb01_e4_ctrl.st')
