"""Time Mario's basic Jump from the target-confirm press until the partner's menu opens (gBattleState 14), with and
without the run cancel (A press at step K, after A was released) and the quick jump (A press at step Q during the
crouch), each with a successful jump action command (A press at step P, searched). Steps are game frames (2 VI).
Inputs only after states/boss_XXXX_menu.st (Mario's first menu).
usage: btl_jump_timing.py BATTLEHEX TARGET_RIGHTS OUT.json"""
import os, sys, json
from emu import *
from pm import *
from btl import *
BID, R, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jt%d' % os.getpid())
MENU = 'states/boss_%s_menu.st' % BID
base = '/dev/shm/pmbot/jt%d_confirm.st' % os.getpid()
e.load(MENU); e.step(0, 0, 0, 2)
e.step(A, 0, 0, 2)
for i in range(15): e.step(0, 0, 0, 2)
for r in range(R):
    e.step(0, 70, 0, 2)
    for i in range(6): e.step(0, 0, 0, 2)
pa = e.u32(BSTATUS + 0xD8)
tgt = e.u32(BSTATUS + 0x1A4) if False else None
e.save(base); e.step(0, 0, 0, 1)
def run(K=None, Q=None, P=None, trace=False, cap=900):
    e.load(base); e.step(0, 0, 0, 2)
    e.step(A, 0, 0, 2)                        # confirm target: step 0
    pr = {K, Q, P} - {None}
    tr = []; ok = False; jump0 = None
    for s in range(1, cap):
        e.step(A if s in pr else 0, 0, 0, 2)
        x, y = e.f32(pa + 0x144), e.f32(pa + 0x148)
        if trace: tr.append((s, round(x, 1), round(y, 1), bstate(e)))
        if jump0 is None and y > 0.5: jump0 = s
        if e.s8(BSTATUS + 0x81) > 0: ok = True
        if bstate(e) == 14: return s, ok, jump0, tr
    return None, ok, jump0, tr
HPOFF = 0x1B8
res = {}
def enemy_hp():
    out = []
    for i in range(24):
        a = e.u32(BSTATUS + 0xE0 + 4 * i)
        if 0x80000000 < a < 0x80800000: out.append((i, e.u8(a + 0x136), e.s8(a + HPOFF), round(e.f32(a + 0x144))))
    return out
e.load(base); e.step(0, 0, 0, 2); hp_before = enemy_hp()
t0, ok0, j0, tr0 = run(trace=True)
res['hp_before'] = hp_before; res['hp_after_base'] = enemy_hp(); print('target check: before', hp_before, 'after', res['hp_after_base'], flush=True)
res['base_noAC'] = (t0, ok0, j0)
runxs = [x for s, x, y, b in tr0 if y < 0.5 and (j0 is None or s < j0)]
res['run_steps_to_jump'] = j0
print('base, no AC: partner menu at', t0, 'jump starts', j0, flush=True)
def best_P(K=None, Q=None):
    _, _, j, _ = run(K, Q)
    best = None
    for P in range(j, j + 45):
        t, ok, _, _ = run(K, Q, P)
        if ok and t and (best is None or t < best[0]): best = (t, P)
        if best and P > best[1] + 6: break
    return best
res['base_AC'] = best_P(); print('base with AC (t, P):', res['base_AC'], flush=True)
# quick jump only
bq = None
for Q in range(max(1, j0 - 12), j0 + 1):
    t, ok, j, _ = run(None, Q)
    if t and (bq is None or t < bq[0]): bq = (t, Q, j)
res['quick_noAC'] = bq; print('quick only, no AC:', bq, flush=True)
# run cancel K (no AC) then quick Q
bk = None
for K in range(2, j0 + 1):
    t, ok, j, _ = run(K)
    if t and (bk is None or t < bk[0]): bk = (t, K, j)
res['cancel_noAC'] = bk; print('cancel only, no AC:', bk, flush=True)
bkq = None
if bk:
    K = bk[1]
    for Q in range(K + 1, bk[2] + 1):
        t, ok, j, _ = run(K, Q)
        if t and (bkq is None or t < bkq[0]): bkq = (t, K, Q, j)
res['cancel_quick_noAC'] = bkq; print('cancel + quick, no AC:', bkq, flush=True)
if bq: res['quick_AC'] = best_P(None, bq[1]); print('quick with AC:', res['quick_AC'], flush=True)
if bkq: res['cancel_quick_AC'] = best_P(bkq[1], bkq[2]); print('cancel + quick with AC:', res['cancel_quick_AC'], flush=True)
json.dump(res, open(out, 'w'))
