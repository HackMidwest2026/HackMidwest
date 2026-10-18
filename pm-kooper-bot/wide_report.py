"""Summarize rta_wide.py results: every clipping run, and for each, the window of each input (number of consecutive
values of that input, others fixed, that still clip with the same C-down offset after the step-2 landing).
usage: wide_report.py FAMILY"""
import glob, json, sys
from collections import defaultdict
fam = sys.argv[1]
rows = [json.loads(l) for f in glob.glob('states/wide_%s_?.jsonl' % fam) for l in open(f)]
res = {tuple(r[0]): set(r[3]) for r in rows}
names = ('L1', 'D0', 'N', 'K') if fam == 'H' else ('L1', 'D0', 'N', 'T', 'U')
clips = [(k, o) for k, s in res.items() for o in s]
print(len(rows), 'runs,', len(clips), 'clipping (run, C-down offset) pairs')
out = []
for k, o in clips:
    win = []
    for i in range(1, len(k)):
        lo = hi = k[i]
        while True:
            kk = list(k); kk[i] = lo - 1
            if o in res.get(tuple(kk), ()): lo -= 1
            else: break
        while True:
            kk = list(k); kk[i] = hi + 1
            if o in res.get(tuple(kk), ()): hi += 1
            else: break
        win.append(hi - lo + 1)
    out.append((sorted(win), k, o, win))
for w, k, o, win in sorted(out, key=lambda t: (-min(t[0][:2]) if len(t[0]) > 1 else 0, -sum(t[3])))[:25]:
    print(dict(zip(names, k[1:])), 'C-down', o, 'after landing; windows', dict(zip(names[1:] if False else names, win)))
