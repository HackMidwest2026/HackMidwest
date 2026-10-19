"""Place Mario on the kpa_62 y-60 platform with Lakilester settled beside him, the way he would be after following
Mario there. Teleporting Mario alone (as the earlier kpa62 scripts did) leaves Laki to fly from the room entry; he hits
the tower and stays in follow state 1 with moveSpeed ~29 forever, which never happens in a real run.
place(e, x, z, y=60): moves Mario and Laki, fills the move history with Laki's position (as
partner_clear_player_tracking does), resets the follow state, then runs frames until Laki is idle."""
from pm import *
HIST, HIST_IDX, HIST_PTR, FOLLOW_STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
def laki(e):
    return [q for q in npcs(e) if q['id'] == -4][0]
def place(e, x, z, y=60.0, settle=40):
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
    a = laki(e)['addr']
    lx, ly, lz = x - 25.0, y + 20.0, z - 10.0
    e.wf32(a + 0x38, lx); e.wf32(a + 0x3C, ly); e.wf32(a + 0x40, lz)
    for off in (0x18, 0x1C, 0x14): e.wf32(a + off, 0.0)              # moveSpeed, jumpVel, jumpScale
    for i in range(40):
        e.wf32(HIST + 16 * i, lx); e.wf32(HIST + 16 * i + 4, y); e.wf32(HIST + 16 * i + 8, lz); e.w32(HIST + 16 * i + 12, 0)
    e.w32(HIST_IDX, 0); e.w32(HIST_PTR, 0)
    e.w16(FOLLOW_STATE, 0)
    for i in range(settle): e.step(0, 0, 0, 2)
