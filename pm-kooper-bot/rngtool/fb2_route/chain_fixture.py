"""v87: the fixture of the continuous T1 -> T4 logs (chain_log.py) for test_fb14_chain.js: per log the seed before every
frame (base64 uint32 little-endian), the turns' inputs (Mario's confirm M and kind, the lever P and kind), the nuisance
t14model.fit finds (the aura pattern by frame mod 20, the lightning phases, the first coin frame), the dodge tests (frame,
value, from the caller testtgt) and the frame the Jelly's sparkles drew (to check FB14_JELLY).
usage: python3 chain_fixture.py OUT.json LOG.json [...]"""
import sys, os, json, base64, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t14model import fit, rand_int

out = []
for p in sys.argv[2:]:
    L = json.load(open(p)); rows = L['rows']; c, ph, nc = fit(L)
    tests, jelly = [], []
    for r in rows:
        s = int(r['s0'], 16)
        for n, m in r['d']:
            s, v = rand_int(s, m)
            if n == 'testtgt': tests.append([r['f'], v])
            if n == 'e0044170': jelly.append(r['f'])
    s0 = b''.join(struct.pack('<I', int(r['s0'], 16)) for r in rows)
    out.append(dict(name=os.path.basename(p), seed=L['seed'], guard=L.get('guard', False), f0=rows[0]['f'], n=len(rows), aura=c, ph=ph, nc=nc,
                    turns=[dict(turn=t['turn'], M=t['M'], mkind=t['mkind'], P=t['P'], pkind=t['pkind'], next=t['next'], hp=t['hp'], ko=t['ko']) for t in L['turns']],
                    tests=tests, jelly=jelly[:1], s0=base64.b64encode(s0).decode()))
    print(out[-1]['name'], 'frames', len(rows), 'aura', ''.join(map(str, c)), 'ph', ph, 'nc', nc, 'tests', tests, 'jelly', jelly[:1])
json.dump(out, open(sys.argv[1], 'w'), separators=(',', ':'))
print(len(out), 'logs', os.path.getsize(sys.argv[1]), 'bytes')
