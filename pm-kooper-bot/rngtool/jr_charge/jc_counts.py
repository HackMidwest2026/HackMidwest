"""Draw counts per Charge and from each Charge confirm to the next roll that matters, by caller, over jc_turns.py logs.
usage: python3 jc_counts.py LOG.json [...]"""
import sys, json, os
from collections import Counter
NAMES = {0xe00d6160: 'ray base rand(360)', 0xe00d62c8: 'ray speed rand(10)', 0xe00d6624: 'ray phase rand(10)', 0xe00d6838: 'ray respawn rand(359)',
         0x80146d54: 'coin rand(100)', 0x800269ac: 'per-frame rand(1)', 0x80277518: 'Close Call rand(100)'}
rows = []
for fn in sys.argv[1:]:
    r = json.load(open(fn)); L = r['log']; C = r['confirms']
    ch = [f for f, n, t in C if t == 'charge']
    for c in ch:
        nxt = [(f, n) for f, n, t in C if f > c and t and t != 'charge']
        # roll that matters after this Charge: the next Close Call (or the Power Bounce cap rolls)
        roll = next(((f, x) for f in range(c, len(L)) for x in L[f]['c'] if x[0] in (0x80277518,)), None)
        end = roll[0] if roll else None
        rays = Counter(); seg = Counter(); steps_rays = 0; steps_seg = 0
        for f in range(c, min(c + 62, len(L))):
            for x in L[f]['c']:
                if x[0] >> 12 == 0xe00d6: rays[x[0]] += 1
        if end:
            for f in range(c, end + 1):
                for x in L[f]['c']: seg[NAMES.get(x[0], hex(x[0]) + '/%d' % x[1])] += 1
            # LCG steps from the confirm frame's start to just before the roll
            s0 = L[c]['s0']; s = s0; target = None
        rows.append({'run': os.path.basename(fn), 'charge_at': c, 'ray_draws': sum(rays.values()), 'respawn': rays[0xe00d6838],
                     'to_roll_frames': (end - c) if end else None, 'seg': dict(seg) if end else None, 'next': nxt[0][1] if nxt else None})
for x in rows:
    print(x['run'], 'charge@%d' % x['charge_at'], 'ray draws', x['ray_draws'], '(respawns %d)' % x['respawn'], 'roll at +%s' % x['to_roll_frames'], 'next', x['next'],
          '' if not x['seg'] else {k: v for k, v in x['seg'].items() if k not in ('per-frame rand(1)',)})
rs = [x['respawn'] for x in rows]; print('respawn draws per Charge: min %d max %d over %d Charges' % (min(rs), max(rs), len(rs)))
