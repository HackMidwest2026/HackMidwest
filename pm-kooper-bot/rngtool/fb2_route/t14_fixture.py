"""The page model's fixture (fixtures/fb14_logs.json, test_fb14_model.js) from t14_log.py logs: per log the turn, its
inputs (Mario's confirm = frame 0, the partner confirm P), the nuisance t14model.fit finds (the aura pattern by frame mod
20, the lightning phases, the first coin frame), the seed before every frame (base64 uint32 little-endian, from the
log's first frame) and the dodge test (frame, value). usage: python3 t14_fixture.py OUT.json LOG.json [...]"""
import sys, os, json, base64, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t14model import fit, check

out = []
for p in sys.argv[2:]:
    L = json.load(open(p)); c, ph, nc = fit(L); ck = check(p)
    rows = L['rows']; s0 = b''.join(struct.pack('<I', int(r['s0'], 16)) for r in rows)
    out.append(dict(name=os.path.basename(p), turn=L['turn'], P=L['marks'].get('pconfirm'), f0=rows[0]['f'], n=len(rows), aura=c, ph=ph, nc=nc,
                    s0=base64.b64encode(s0).decode(), test=ck['info'][0] if ck['info'] else None, flags=ck['flags'], exact_all=ck['exact_all'], first_mismatch=ck['first_mismatch']))
json.dump(out, open(sys.argv[1], 'w'), separators=(',', ':'))
print(len(out), 'logs', os.path.getsize(sys.argv[1]), 'bytes')
