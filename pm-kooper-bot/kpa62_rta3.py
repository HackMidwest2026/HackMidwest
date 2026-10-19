"""kpa_62 RTA setup search, version 3 (notch directions only). From the seed spot: ride Laki along up to two stick
directions (60 frames each, so walls/corners fix the spot), dismount (B), wait 25. On foot: optional leg A (one notch
direction held 40 frames, into a wall) then leg B (notch direction held h frames). Two endings per h:
  'run'   : C-down on frame h+1 while still holding (frame-timed),
  'stand' : release, wait 20 frames (Mario stops), then C-down (no timing).
Hit = Mario ends inside the tower outline. Prints, per plan, the working h values (the RTA window).
usage: kpa62_rta3.py STATE PART NPARTS OUT.jsonl   env: HMAX, MAG"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
HMAX = int(os.environ.get('HMAX', '50')); MAG = int(os.environ.get('MAG', '80'))
DIRS = list(range(0, 360, 45))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62c%d' % os.getpid())
tmp = '/dev/shm/pmbot/k62c%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.seed')
def near(p): return -400 <= p['x'] <= -360 and -15 <= p['z'] <= 35
def try_cdown(st):
    e.step(0x400, *st, 2)
    for f in range(30):
        e.step(0, *st, 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
rides = [()] + [(a,) for a in DIRS] + [(a, b) for a in DIRS for b in DIRS if b != a]
fo = open(out, 'a'); tot = 0; seen = set()
for ride in rides[PART::NP]:
    e.load(tmp + '.seed')
    e.step(0x400, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    for a in ride:
        for i in range(60): e.step(0, *stick_for(a, 80), 2)
    for i in range(10): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for i in range(25): e.step(0, 0, 0, 2)
    d = player(e)
    if os.environ.get('DBG'): print(ride, d)
    key = (round(d['x']), round(d['z']))
    if abs(d['y'] - 60) > 2 or key in seen: continue
    seen.add(key); e.save(tmp + '.dis')
    for la in [None] + DIRS:
        e.load(tmp + '.dis')
        if la is not None:
            for i in range(40): e.step(0, *stick_for(la, MAG), 2)
            for i in range(10): e.step(0, 0, 0, 2)
        src = tmp + '.dis' if la is None else tmp + '.a'   # a save right after a load (no frame run) fails
        if la is not None: e.save(src)
        pa = player(e)
        for lb in DIRS:
            e.load(src); st = stick_for(lb, MAG); win = {'run': [], 'stand': []}
            for h in range(HMAX):
                e.step(0, *st, 2); p = player(e)
                if p['y'] < 0: break
                if not near(p): continue
                e.save(tmp + '.h')
                if try_cdown(st): win['run'].append(h + 1)
                e.load(tmp + '.h')
                for i in range(20): e.step(0, 0, 0, 2)
                s = player(e)
                if abs(s['y'] - 50) < .5 and try_cdown((0, 0)):
                    win['stand'].append(h + 1)
                    fo.write(json.dumps({'ride': ride, 'dis': [d['x'], d['z']], 'A': la, 'posA': [pa['x'], pa['z']], 'B': lb, 'h': h + 1, 'stand': [s['x'], s['z']]}) + '\n'); fo.flush()
                e.load(tmp + '.h')
            if win['run'] or win['stand']:
                tot += 1
                print('ride %s dis (%.1f %.1f) legA %s (%.1f %.1f) legB %d -> run h %s | stand h %s' % (ride, d['x'], d['z'], la, pa['x'], pa['z'], lb, win['run'], win['stand']), flush=True)
print('done part', PART, len(seen), 'dismount spots', tot, 'plans with hits')
