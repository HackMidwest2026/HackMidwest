"""Replay the brute2 S success and a 'stand still then C-down' control. Same DIAGNOSTIC setup as pra18_brute2.py."""
import json, os, sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rp%d' % os.getpid())
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 630.0); e.wf32(PLAYER + PS_POS + 8, 30.0)     # DIAGNOSTIC
l = laki(); e.wf32(l['addr'] + 0x38, 650.0); e.wf32(l['addr'] + 0x40, 40.0)  # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/rp%d_base.st' % os.getpid(); e.save(base)
rec = json.loads(open('/tmp/claude-0/pm/p18/brute2_S2.jsonl').readline())
for b, sx, sy in rec['inputs']: e.step(b, sx, sy, 2)
p = player(e); print('after inputs', round(p['x'], 2), round(p['z'], 2), 'action', p['action'], 'laki speed', round(e.f32(laki()['addr'] + 0x18), 2))
for j in range(rec['extra_wait']): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(35):
    e.step(0, 0, 0, 2); q = player(e)
    if i % 5 == 0 or i == 34: print(' f%d' % i, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), 'action', q['action'])
e.load(base)
for b, sx, sy in rec['inputs']: e.step(b, sx, sy, 2)
for j in range(rec['extra_wait']): e.step(0, 0, 0, 2)
L = laki(); print('laki before C-down', round(e.f32(L['addr'] + 0x38), 1), round(e.f32(L['addr'] + 0x3C), 1), round(e.f32(L['addr'] + 0x40), 1))
e.step(D_CBUTTON, 0, 0, 2)
for i in range(20):
    e.step(0, 0, 0, 2); L = laki(); q = player(e)
    print(' f%d mario' % i, round(q['x'], 1), round(q['z'], 1), 'laki', round(e.f32(L['addr'] + 0x38), 1), round(e.f32(L['addr'] + 0x40), 1))
