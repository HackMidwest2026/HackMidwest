"""Synthetic check helper: emulator truth (aura_render.py stars.json) vs the footage pipeline's part table / readings.
The glide64 frame saved after emulator frame f shows frame f - 1 (aura_tmpl.py), and aura_capsim.py puts saved frame f
on game frame f of the simulated capture, so a star that restarts (draws) on emulator frame f0 restarts on footage
frame f0 + 1. usage: python3 aura_syncheck.py STARS.json PARTS.json [LAG=1]"""
import sys, json
import numpy as np
S = json.load(open(sys.argv[1])); P = json.load(open(sys.argv[2])); LAG = int(sys.argv[3]) if len(sys.argv) > 3 else 1
truth = {}            # part -> dict(phase, v, size, restarts {footage f0: A})
for row in S:
    f = row['f']
    for s in row['stars']:
        d = truth.setdefault(s['i'], dict(v=round(s['v'], 1), size=round(s['size'], 1), r={}))
        if s['t'] == 0: d['r'][f + LAG] = int(round(s['ang'] + 2)) % 360
for i, d in truth.items(): d['phase'] = min(d['r']) % 20 if d['r'] else None
print('truth parts (index: phase v size):', ' '.join('%d:%s/%.1f/%.1f' % (i, d['phase'], d['v'], d['size']) for i, d in sorted(truth.items())))
used = set(); nok = 0; errs = []
for p in P['parts']:
    m = [i for i, d in truth.items() if d['phase'] == p['phase'] and abs(d['v'] - p['v']) < 0.11 and d['size'] == p['size'] and i not in used]
    tag = 'part %d' % m[0] if m else 'NO MATCH'
    if m:
        used.add(m[0]); nok += 1
        for r in p['restarts']:
            if r['f0'] in truth[m[0]]['r']:
                e = (r['A'] - truth[m[0]]['r'][r['f0']] + 180) % 360 - 180
                errs.append((e, r['s'], r['margin'], r['cnt']))
    print('found phase %2d v %.1f size %.1f score %6.1f -> %s' % (p['phase'], p['v'], p['size'], p['score'], tag))
print('parts matched: %d / %d' % (nok, len(P['parts'])))
E = np.array(errs)
if len(E):
    for thr in (0, 5, 10, 20):
        q = E[(E[:, 2] > thr) & (E[:, 3] >= 12)]
        if len(q): print('readings with margin > %2d (full life): %3d; |err| <= 1: %.0f%%, <= 2: %.0f%%, <= 3: %.0f%%, median |err| %.1f' % (
            thr, len(q), 100 * np.mean(np.abs(q[:, 0]) <= 1), 100 * np.mean(np.abs(q[:, 0]) <= 2), 100 * np.mean(np.abs(q[:, 0]) <= 3), np.median(np.abs(q[:, 0]))))
    print('error histogram (all matched readings):', np.histogram(np.clip(E[:, 0], -10, 10), bins=np.arange(-10.5, 11))[0].tolist())
