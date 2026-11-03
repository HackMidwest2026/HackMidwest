"""Check the Charge-ray model with the stage lightning as a nuisance stream, against t6_render.py logs.
Model per frame (frame 0 = Charge confirm + 13, readouts/charge_model.py plus the bolts):
  1. lightning: one rand_int(359) per bolt starting on this frame (kkj stage loops; the frames come from the log here)
  2. script: effect creation (frames 0 and 3: rand_int(360), then rand_int(10) x 2 per part)
  3. coin: rand_int(100) on its frame (24 / 48 rule)
  4. effect updates: each part redraws rand_int(359) when its counter wraps
  5. the per-frame rand_int(1)
For each log, the model starts from the logged seed before frame 0 and the logged first coin frame and bolt frames,
and must reproduce the logged seed after every frame 0..47 and the order of the draws (callers) on every frame (the ray redraws log as
'aura': route.py names 0xE00D6838, the energy_in_out update, after the aura that uses the same effect).
usage: python3 t6_raycheck.py LOG.json [...]"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'readouts'))
from charge_model import Effect, rand_int, adv

def check(path):
    L = json.load(open(path)); R = L['frames']
    f0 = next(r['f'] for r in R if any(nm.startswith('e00d6') for nm, mx in r['d']))
    rows = R[f0:f0 + 49]
    s = int(rows[0]['s0'], 16)
    coin = [r['f'] - f0 for r in rows if any(nm == 'coin' for nm, mx in r['d'])]
    effs = []; ok = 0; bad = []
    for n in range(48):
        r = rows[n]; seq = []
        nb = sum(1 for nm, mx in r['d'] if nm == 'bolt')
        for i in range(nb): s, _ = rand_int(s, 359); seq.append('bolt')
        if n in (0, 3):
            e = Effect(s, 1.2 if n == 0 else 0.8); s = e.s; effs.append(e); seq += ['init'] * 21
        if n in coin: s, v = rand_int(s, 100); seq.append('coin')
        alive = []
        for e in effs:
            out = []; s, live = e.update(s, out); seq += ['ray'] * len(out)
            if live: alive.append(e)
        effs = alive
        s, _ = rand_int(s, 1)
        logged = ['bolt' if nm == 'bolt' else 'coin' if nm == 'coin' else 'init' if nm.startswith('e00d6') and n in (0, 3) and mx in (360, 10) else 'ray' if nm.startswith('e00d6') or nm == 'aura' else nm for nm, mx in r['d'] if nm != 'step']
        if s == int(rows[n + 1]['s0'], 16) and logged == seq: ok += 1
        else: bad.append(n)
    bolts = [r['f'] - f0 for r in rows[:48] for nm, mx in r['d'] if nm == 'bolt']
    print('%s seed %s: %d/48 frames exact; bolts on rays frames %s, coins %s%s' % (os.path.basename(os.path.dirname(path)) or path, L['seed'], ok, bolts, coin, ' BAD ' + str(bad) if bad else ''))
    return ok == 48

if __name__ == '__main__':
    print('all exact' if all([check(p) for p in sys.argv[1:]]) else 'MISMATCH')
