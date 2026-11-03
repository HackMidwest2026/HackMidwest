"""FB2 T6 Charge camera table for the page (readouts/data/charge_cams_mario_fb2.json), the same method as
readouts/charge_prep.py `cams` (charge_cams_mario_route.json): gCameras[1]'s perspective matrix and viewport on each of
the 48 ray frames of an emulator reference run (t6_render.py log; frame 0 = confirm + 13) and the effect centre (part 0
position on frame 0). Also prints the largest difference to another table (the Hallway route's).
usage: python3 t6_cams.py LOG.json OUT.json [OTHER.json]"""
import sys, json
L = json.load(open(sys.argv[1])); R = {r['f']: r for r in L['frames']}
f0 = min(f for f, r in R.items() if any(nm.startswith('e00d6') for nm, mx in r['d']))
cen = [float(x) for x in R[f0]['fx'][0].split(':')[1].split(',')] if isinstance(R[f0]['fx'][0], str) else R[f0]['fx'][0]
cams = [R[f0 + n]['cam'][:20] for n in range(48)]
json.dump({'centre': cen, 'cams': cams}, open(sys.argv[2], 'w'))
print('frame 0 = confirm +%d, centre %s' % (f0, cen))
if len(sys.argv) > 3:
    O = json.load(open(sys.argv[3]))
    print('max |difference| to %s: matrices %.4g, centre %.4g' % (sys.argv[3], max(abs(a - b) for x, y in zip(cams, O['cams']) for a, b in zip(x[:16], y[:16])),
                                                            max(abs(a - b) for a, b in zip(cen, O['centre']))))
