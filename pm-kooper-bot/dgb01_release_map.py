"""dgb_01: map of the remount speeds reachable after a push (dgb01_push.py end state). From the push end, walk at angle A
(every STEP degrees, full tilt) and press C-down on frame f (1..FMAX); record where Mario is when he mounts and Laki's
speed when the mount reads it.
usage: dgb01_release_map.py PUSH_END.st OUT.jsonl   env: STEP (15), FMAX (90)"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
st, out = sys.argv[1], sys.argv[2]
STEP, FMAX = int(os.environ.get('STEP', '15')), int(os.environ.get('FMAX', '90'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/drm%d' % os.getpid())
tmp = '/dev/shm/pmbot/drm%d' % os.getpid()
fo = open(out, 'w'); best = (0,)
for A in range(0, 360, STEP):
    e.load(st); e.step(0, 0, 0, 2); e.save(tmp + '.a')
    for f in range(1, FMAX + 1):
        e.load(tmp + '.a')
        e.step(0x400, *stick_for(A, 80), 2)
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: break
            e.step(0, 0, 0, 2)
        S = e.f32(a + 0x18); q = player(e)
        fo.write(json.dumps({'A': A, 'f': f, 'x': round(q['x'], 1), 'z': round(q['z'], 1), 'S': round(S, 2)}) + '\n')
        if S > best[0]: best = (S, A, f, q['x'], q['z'])
        e.load(tmp + '.a'); e.step(0, *stick_for(A, 80), 2); e.save(tmp + '.a')
print('best mount speed %.1f walking at %d deg, C-down frame %d, Mario at (%.0f, %.0f)' % best)
