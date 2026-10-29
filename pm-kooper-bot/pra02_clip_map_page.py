"""Builds pra02_clip_map.html from the rev_fullmap_pra02.py output (one JSON line per x column).
usage: pra02_clip_map_page.py <fullmap.jsonl> <out.html>"""
import sys, json
rows = []
for line in open(sys.argv[1]):
    r = json.loads(line)
    for z, v in r['z'].items(): rows.append([r['x'], int(z), v['y'], v['S']])
rows.sort()
walls = [[0, -225, 234, -225], [234, -225, 238, -213], [238, -213, 250, -209], [250, -209, 262, -213], [262, -213, 266, -225],
         [266, -225, 734, -225], [734, -225, 738, -213], [738, -213, 750, -209], [750, -209, 762, -213], [762, -213, 766, -225],
         [766, -225, 1000, -225], [0, -225, 0, -105], [0, -45, 0, 0], [1000, -225, 1000, -125], [1000, -45, 1000, 0]]
tpl = open(__file__.replace('_page.py', '_template.html')).read()
open(sys.argv[2], 'w').write(tpl.replace('/*DATA*/', json.dumps({'rows': rows, 'walls': walls})))
print(len(rows), 'spots,', sum(1 for r in rows if r[3]), 'clip at some speed')
