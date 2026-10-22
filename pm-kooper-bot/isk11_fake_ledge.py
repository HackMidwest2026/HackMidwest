"""Exploration shortcut: from the ring state, move Mario and Laki (RAM) onto the lock ledge without touching the frozen
history, settle, save OUT.st.  env LAKI=x,y,z MARIO=x,z"""
import os, sys
from emu import *
from pm import *
IDX, PTR, STATE, HIST = 0x8010D178, 0x8010D17C, 0x8010D188, 0x8010CEF8
L = [float(v) for v in os.environ.get('LAKI', '320,-450,425').split(',')]
M = [float(v) for v in os.environ.get('MARIO', '345,415').split(',')]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ifl%d' % os.getpid())
e.load(sys.argv[1]); a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
e.wf32(PLAYER + PS_POS, M[0]); e.wf32(PLAYER + PS_POS + 4, -468); e.wf32(PLAYER + PS_POS + 8, M[1])
e.wf32(a + 0x38, L[0]); e.wf32(a + 0x3C, L[1]); e.wf32(a + 0x40, L[2])
for i in range(20): e.step(0, 0, 0, 2)
p = e.u32(PTR); l = [q for q in npcs(e) if q['id'] == -4][0]
print('state', e.u32(STATE) >> 16, 'ptr', p, 'idx', e.u32(IDX), 'target', e.f32(HIST + 16 * p + 4), e.f32(HIST + 16 * p + 12), player(e), (l['x'], l['y'], l['z']))
e.save(sys.argv[2])
