"""pra_01 reflected side push start: Mario at the bottom of the mirror by the left rock, Lakilester on his right
facing left, in follow state 5 with the history pointer NOT 0 (pointer 0 lets the ring buffer overwrite the frozen
target at the 39 -> 0 wrap). Tries a few walk-in lengths; saves states/pra01_top_rock.st and prints pointer/target."""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mktr')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
for extra in range(0, 40):
    e.load('states/pra01_top_start.st')
    for i in range(50 + extra): e.step(0, 80, 0, 2)
    for i in range(30): e.step(0, 0, -80, 2)
    for i in range(120):
        e.step(0, -80, 0, 2)
        if player(e)['z'] < -14 or player(e)['x'] < 556: break
    for i in range(60): e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    ptr = e.u32(PTR)
    print(extra, 'mario %.1f %.1f laki %.1f %.1f st %d idx %d ptr %d tgt (%.1f, %.1f)' % (p['x'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16, e.u32(IDX), ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
    if ptr not in (0, 39) and (e.u32(STATE) >> 16) == 5 and l['x'] > p['x']:
        e.save('states/pra01_top_rock.st'); print('saved'); break
