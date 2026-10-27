"""pra_18 south->north: is there a held stick direction that makes Mario come to rest against the pillar's south /
south-east faces with x in 615.0..616.1 and z 15..45 (the clip line) from several different starting spots?
Holds every integer stick vector of magnitude ~60-80 pointing roughly north (into the pillar) for 90 frames from each start.
DIAGNOSTIC SETUP: Mario placed on foot at each start; everything after is real input."""
import os, sys, json, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sp%d' % os.getpid())
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/sp%d_b.st' % os.getpid(); e.save(b0)
STARTS = [(616, 70), (606, 70), (626, 70), (640, 60), (596, 60), (620, 100)]
starts = []
for sx, sz in STARTS:
    e.load(b0); e.wf32(PLAYER + PS_POS, float(sx)); e.wf32(PLAYER + PS_POS + 8, float(sz))
    for i in range(20): e.step(0, 0, 0, 2)
    fn = '/dev/shm/pmbot/sp%d_%d_%d.st' % (os.getpid(), sx, sz); e.save(fn); starts.append(fn)
vecs = []
for sx in range(-40, 41):
    for sy in range(30, 81):
        m = math.hypot(sx, sy)
        if 55 <= m <= 82: vecs.append((sx, sy))
res = []
PART, NP = int(sys.argv[1]), int(sys.argv[2]); vecs = vecs[PART::NP]
for v in vecs:
    ends = []
    for fn in starts:
        e.load(fn)
        for i in range(90): e.step(0, v[0], v[1], 2)
        p = player(e); x1, z1 = p['x'], p['z']
        e.step(0, v[0], v[1], 2); p = player(e)
        ends.append((round(p['x'], 2), round(p['z'], 2), round(math.hypot(p['x'] - x1, p['z'] - z1), 3)))
    good = [en for en in ends if 615.0 <= en[0] <= 616.1 and 15 <= en[1] <= 45 and en[2] < 0.05]
    res.append([v, ends])
    if good: print('stick', v, 'rests on the line from', len(good), '/', len(ends), 'starts:', ends, flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/stickpin_%d.json' % PART, 'w')); print('done')
