"""Inputs only: replay a greedy-push action list (ACTIONS.json) from STATE, save OUT and print where Mario and Laki
end, the follow state and the distance to the frozen target.  usage: isk11_replay_actions.py STATE ACTIONS.json OUT"""
import json, math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ira')
e.load(sys.argv[1])
for (d, t, h, w) in json.load(open(sys.argv[2])):
    if h < 0:
        for i in range(-h): e.step(A, *stick_for(d % 360, t), 2)
    else:
        for i in range(h): e.step(0, *stick_for(d % 360, t), 2)
    for i in range(w): e.step(0, 0, 0, 2)
for i in range(3): e.step(0, 0, 0, 2)
p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]; ptr = e.u32(PTR)
tx, tz = e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)
print('state', e.u32(STATE) >> 16, 'M', [round(v) for v in (p['x'], p['y'], p['z'])], 'L', [round(v) for v in (l['x'], l['y'], l['z'])], 'target', round(tx), round(tz), 'd', round(math.hypot(l['x'] - tx, l['z'] - tz), 1))
e.save(sys.argv[3])
