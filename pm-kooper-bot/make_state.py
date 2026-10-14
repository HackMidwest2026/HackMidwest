"""boot, start a new file, and redirect its first map load to nok_14 (entry 0, from nok_13).
saves states/nok14_start.st once mario can move."""
import os
from emu import *
from pm import *

e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), os.environ.get('PM_TMP', '/dev/shm/pmbot'))
redirected = False
for f in range(6000):
    m = e.s16(GAME_MODE)
    btn = 0
    if m in (1, 2, GM_FILE_SELECT) and f % 20 < 2:
        btn = START if m == 2 else A
    if m in (GM_END_FILE_SELECT, GM_ENTER_WORLD) or redirected:
        g = game_status(e)
        if m in (GM_END_FILE_SELECT, GM_ENTER_WORLD):
            e.w16(g + 0x86, AREA_NOK); e.w16(g + 0x8C, MAP_NOK_14); e.w16(g + 0x8E, 0)
            e.w16(SAVE + 0x468, AREA_NOK); e.w16(SAVE + 0x46A, MAP_NOK_14); e.w16(SAVE + 0x46C, 0)
        if not redirected:
            redirected = True
            print('redirect at', f, 'mode', m)
        e.w8(STORY, STORY_CH1_ARRIVED_AT_KOOPA_VILLAGE & 0xFF)
    e.step(btn)
    if redirected and e.s16(GAME_MODE) == GM_WORLD:
        break
print('world at', f, where(e))
# let the entrance walk finish
for i in range(400):
    e.step()
    p = player(e)
    if i % 20 == 0: print(i, where(e), {k: round(v, 2) if isinstance(v, float) else v for k, v in p.items()})
os.makedirs('states', exist_ok=True)
e.save('states/nok14_start.st')
print('saved', e.frame)
