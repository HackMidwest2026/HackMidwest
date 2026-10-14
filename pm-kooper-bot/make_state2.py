"""boot, start a new file, load nok_13 at the entrance from nok_14, give mario boots, hammer and
goombario, then walk into nok_14.  saves states/nok14_start_goombario.st."""
import os, sys
from emu import *
from pm import *

e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), os.environ.get('PM_TMP', '/dev/shm/pmbot'))
for f in range(6000):
    m = e.s16(GAME_MODE)
    btn = 0
    if m in (1, 2, GM_FILE_SELECT) and f % 20 < 2:
        btn = START if m == 2 else A
    if m in (GM_END_FILE_SELECT, GM_ENTER_WORLD):
        g = game_status(e)
        e.w16(g + 0x86, AREA_NOK); e.w16(g + 0x8C, MAP_NOK_13); e.w16(g + 0x8E, 2)
        e.w16(SAVE + 0x468, AREA_NOK); e.w16(SAVE + 0x46A, MAP_NOK_13); e.w16(SAVE + 0x46C, 2)
        e.w8(STORY, STORY_CH1_ARRIVED_AT_KOOPA_VILLAGE & 0xFF)
    e.step(btn)
    if where(e)[:2] == (AREA_NOK, MAP_NOK_13) and e.s16(GAME_MODE) == GM_WORLD:
        break
for i in range(120):
    e.step()
print('in nok_13', player(e))
e.w8(STORY, STORY_CH1_ARRIVED_AT_KOOPA_VILLAGE & 0xFF)
e.w8(PLAYER_DATA + 0, 0); e.w8(PLAYER_DATA + 1, 0)
e.w8(PLAYER_DATA + 0x12, PARTNER_GOOMBARIO); e.w8(PLAYER_DATA + 0x14 + 8 * PARTNER_GOOMBARIO, 1)
e.save('/dev/shm/pmbot/n13.st')
# walk back out the way mario came in: try each direction until nok_14 loads
for sx, sy in [(80, 0), (-80, 0), (0, 80), (0, -80)]:
    e.load('/dev/shm/pmbot/n13.st')
    for i in range(300):
        e.step(0, sx, sy, 2)
        if where(e)[1] == MAP_NOK_14 and e.s16(GAME_MODE) == GM_WORLD:
            break
    if where(e)[1] == MAP_NOK_14:
        break
print('direction', sx, sy, where(e))
for i in range(200):
    e.step(0, 0, 0, 2)
p = player(e)
print('nok_14', p, 'partner', e.s8(PLAYER_DATA + 0x12))
os.makedirs('states', exist_ok=True)
e.save('states/nok14_start_goombario.st')
