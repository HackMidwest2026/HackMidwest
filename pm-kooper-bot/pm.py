"""paper mario (jp 1.0) ram layout, from the pmret/papermario decomp (ver/jp)."""
GAME_MODE = 0x8009E700          # CurGameMode (s16)
GAME_STATUS_PTR = 0x8007417C    # gGameStatusPtr
PLAYER = 0x8010F188             # gPlayerStatus
COLLISION = 0x8015F4D0          # gCollisionStatus
SAVE = 0x800DACA0               # gCurrentSaveFile
STORY = SAVE + 0x10B0           # GB_StoryProgress = globalBytes[0]
PLAYER_DATA = 0x8010F450        # gPlayerData
PARTNER_GOOMBARIO = 1

AREA_NOK = 6
MAP_NOK_13, MAP_NOK_14, MAP_NOK_15 = 6, 7, 8
STORY_CH1_ARRIVED_AT_KOOPA_VILLAGE = -97

GM_WORLD, GM_CHANGE_MAP, GM_ENTER_WORLD, GM_FILE_SELECT, GM_END_FILE_SELECT = 4, 5, 7, 14, 15

# PlayerStatus offsets
PS_FLAGS, PS_ANIMFLAGS = 0x000, 0x004
PS_POS = 0x028
PS_JUMPFROM = 0x03C
PS_CURSPEED = 0x054
PS_GRAVITY = 0x070
PS_TARGETYAW, PS_CURYAW = 0x080, 0x084
PS_ACTION, PS_PREVACTION, PS_SUBSTATE = 0x0B4, 0x0B5, 0x0B6

ACTION_NAMES = {0: 'idle', 1: 'walk', 2: 'run', 3: 'jump', 4: 'bounce', 5: 'hop', 6: 'launch',
                7: 'land_on_switch', 8: 'fall', 9: 'step_down', 10: 'land', 11: 'step_down_land'}


def game_status(e):
    return e.u32(GAME_STATUS_PTR)


def where(e):
    g = game_status(e)
    return e.s16(g + 0x86), e.s16(g + 0x8C), e.s16(g + 0x8E)


def player(e):
    p = PLAYER
    return {
        'x': e.f32(p + PS_POS), 'y': e.f32(p + PS_POS + 4), 'z': e.f32(p + PS_POS + 8),
        'action': e.s8(p + PS_ACTION), 'speed': e.f32(p + PS_CURSPEED),
        'yaw': e.f32(p + PS_CURYAW), 'flags': e.u32(p + PS_FLAGS),
    }

NPC_LIST_PTR = 0x8009E9A0       # gCurrentNpcListPtr (static in npc.c; from get_npc_by_index)
NPC_FLAG_PARTNER = 0x100


def npcs(e):
    lst = e.u32(NPC_LIST_PTR)
    out = []
    for i in range(64):
        n = e.u32(lst + 4 * i)
        if n == 0 or e.u32(n) == 0:
            continue
        out.append({'slot': i, 'addr': n, 'flags': e.u32(n), 'id': e.s8(n + 0xA4),
                    'x': e.f32(n + 0x38), 'y': e.f32(n + 0x3C), 'z': e.f32(n + 0x40),
                    'diam': e.s16(n + 0xA6), 'height': e.s16(n + 0xA8), 'speed': e.f32(n + 0x18)})
    return out
