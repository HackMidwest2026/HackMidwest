"""Start a battle against BATTLE (hex id, area<<8|formation) from the nok_13 Koopa encounter: DIAGNOSTIC SETUP: every
encounter in the map gets battle = BATTLE, stage = -1 (the battle's own stage). Then inputs: walk Mario into the
Koopa at (-650, -150) and wait. Saves states/boss_<id>_start.st once the battle is running and Mario's menu has
been idle a while. usage: boss_battle_start.py BATTLE"""
import os, sys, math
from emu import *
from pm import *
from nav import stick_world
BID = int(sys.argv[1], 16)
ENC = 0x800B0EF0
e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), '/dev/shm/pmbot/bs%d' % os.getpid())
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2)
for i in range(e.s8(ENC + 0x1C)):
    p = e.u32(ENC + 0x28 + 4 * i)
    if 0x80000000 < p < 0x80800000:
        e.w16(p + 0x44, BID); e.w16(p + 0x46, 0xFFFF)          # DIAGNOSTIC: battle id + default stage
if os.environ.get('AC'): e.w8(PLAYER_DATA + 0xA, 1)                   # DIAGNOSTIC: action commands learned (Lucky Star), as in a real run after the prologue
if os.environ.get('HP'):
    h = int(os.environ['HP']); e.w8(PLAYER_DATA + 2, h); e.w8(PLAYER_DATA + 3, h); e.w8(PLAYER_DATA + 4, h)   # DIAGNOSTIC: late-game HP
# DIAGNOSTIC setup for the endgame fights: Bombette out (rank from BRANK), the run's badges (BADGES hex list)
if os.environ.get('PARTNER'):
    pid = int(os.environ['PARTNER']); e.w8(PLAYER_DATA + 0x14 + 8 * pid, 1); e.w8(PLAYER_DATA + 0x15 + 8 * pid, int(os.environ.get('BRANK', '0')))
    e.w8(PLAYER_DATA + 0x12, pid)
# DIAGNOSTIC (v87, restoring the uncommitted v84-v86 options): BOOTS (0 normal, 1 super, 2 ultra), FP (cur = max), ITEMS (hex
# item ids, in list order), STARBEAM (gPlayerData.starBeamLevel: 2 = Peach Beam, as after the kkj_25 cutscene; with it the
# 7 star spirits and a full star bar, so the Star Spirits wheel and the Peach Beam are there)
if os.environ.get('BOOTS'): e.w8(PLAYER_DATA + 0, int(os.environ['BOOTS']))
if os.environ.get('FP'):
    h = int(os.environ['FP']); e.w8(PLAYER_DATA + 5, h); e.w8(PLAYER_DATA + 6, h); e.w8(PLAYER_DATA + 7, h)
if os.environ.get('ITEMS'):
    il = [int(x, 16) for x in os.environ['ITEMS'].split(',')]
    for i in range(10): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, il[i] if i < len(il) else 0)
if os.environ.get('STARBEAM'):
    e.w8(PLAYER_DATA + 0x292, int(os.environ['STARBEAM'])); e.w8(PLAYER_DATA + 0x28E, 7); e.w16(PLAYER_DATA + 0x290, 7 * 256)
if os.environ.get('BADGES'):
    bl = [int(x, 16) for x in os.environ['BADGES'].split(',')]
    for i in range(64): e.w16(PLAYER_DATA + 0x208 + 2 * i, bl[i] if i < len(bl) else 0)
tx, tz = -650, -150
for f in range(400):
    p = player(e)
    if os.environ.get('NOFS'): e.w8(0x800B0EF0 + 4, 0)   # DIAGNOSTIC: no first strike
    if e.s16(GAME_MODE) != GM_WORLD: break
    yaw = math.degrees(math.atan2(tx - p['x'], -(tz - p['z']))) % 360
    e.step(0, *stick_world(e, yaw), 2)
if os.environ.get('NOFS'): e.w8(0x800B0EF0 + 4, 0)   # DIAGNOSTIC: no first strike (boss fights start neutrally)
print('left world at step', f, 'mode', e.s16(GAME_MODE), 'first strike type', e.s8(0x800B0EF0 + 4), flush=True)
for i in range(600):
    if os.environ.get('NOFS') and e.s32(0x800DC048) <= 1: e.w8(0x800B0EF0 + 4, 0)   # DIAGNOSTIC: keep it neutral until the battle has started
    e.step(0, 0, 0, 2)
print('mode', e.s16(GAME_MODE), flush=True)
e.save('states/boss_%04x%s_start.st' % (BID, os.environ.get('SUF', ''))); e.step(0, 0, 0, 1)
from btl import to_first_menu, bstate
n = to_first_menu(e); print('menu after', n, 'state', bstate(e), flush=True)
e.save('states/boss_%04x%s_menu.st' % (BID, os.environ.get('SUF', ''))); e.step(0, 0, 0, 1)
