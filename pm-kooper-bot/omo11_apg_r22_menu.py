"""Replay one omo11_apg_random22.py sequence (JSON on argv[1]) with wait W and stop as soon as the menu exists
(no selection), e.g. to log inputs with steplog.py. usage: omo11_apg_r22_menu.py 'SEQ_JSON' W"""
import json, os, sys
sys.argv = [sys.argv[0], '0', '0', '/dev/null'] + sys.argv[1:]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'omo11_apg_random22.py')).read()
exec(src.split('for n in range(N):')[0])
seq, W = json.loads(sys.argv[4]), int(sys.argv[5])
e.load('states/omo11_apg_top22.st')
for a in seq: do(a)
go_to(e, TX, TZ, maxf=150, tol=1.5)
for i in range(1 + W): e.step(0, 0, 0, 2)
for i in range(6): e.step(A, 0, 0, 2)
for f in range(900):
    p = popup()
    if p: break
    e.step(A if f % 8 == 0 else 0, 0, 0, 2)
print('menu %08x id %d en %08x icon0 %08x desc0 %08x' % (p, e.u32(p + 0x108), e.u32(p + 0x18C), e.u32(p), e.u32(p + 0x294)), flush=True)
