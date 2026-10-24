"""omo_11 route from the east entrance (from omo_10) to under the Super Block, inputs only, over the platforms:
ledge 14 -> bobbing 54 -> ledge 15 (y140) -> wheel (42/45/48) -> ledge 20 (y140) -> bobbing 57 down -> floor
west of 57 (omo11_route3.py does the rest). Collider positions are read only to time hops.
usage: omo11_route2.py OUT.st [STAGE_DIR]   (env START: entry state, default states/omo11_e1_from_omo10.st)"""
import math, os, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
from dump_collision_omo11 import GCOLL
e = Emu('pm-jp.z64', '/dev/shm/pmbot/r2_%d' % os.getpid())
SD = sys.argv[2] if len(sys.argv) > 2 else None
def box(cid):
    coll_ptr = e.u32(GCOLL + 4); c = coll_ptr + cid * 0x1C; ntri = e.s16(c + 0xA); tbl = e.u32(c + 0xC)
    vs = []
    for t in range(ntri):
        tp = tbl + t * 0x40
        for k in range(3):
            v = e.u32(tp + 4 * k); vs.append((e.f32(v), e.f32(v + 4), e.f32(v + 8)))
    return (sum(v[0] for v in vs) / len(vs), max(v[1] for v in vs), sum(v[2] for v in vs) / len(vs))
def chk(tag):
    if e.s16(GAME_MODE) != 4: print('LEFT FIELD at', tag, 'mode', e.s16(GAME_MODE)); sys.exit(1)
    if player(e)['y'] < -50: print('fell at', tag, player(e)); sys.exit(1)
def stage(name, y=None):
    p = player(e)
    if y is not None and abs(p['y'] - y) > 4: print('WRONG HEIGHT at', name, p); sys.exit(1)
    p = player(e); print('%-22s M (%.0f %.0f %.0f) act %d' % (name, p['x'], p['y'], p['z'], p['action']), flush=True)
    if SD: e.save(os.path.join(SD, name + '.st'))
def walk(x, z, tag, tol=3, maxf=400):
    r = go_to(e, x, z, maxf=maxf, tol=tol); chk(tag); return r
def jump_to(x, z, hold=12, tag='', track=None, expect_y=None):
    for i in range(3):
        p = player(e); e.step(0, *stick_world(e, world_yaw_to(p, x, z), 40), 2)
    for i in range(hold):
        p = player(e)
        if track: x, z = track()[0], track()[2]
        e.step(A, *stick_world(e, world_yaw_to(p, x, z)), 2)
    for i in range(60):
        p = player(e)
        if p['action'] in (0, 1, 2) and i > 3: break
        if track: x, z = track()[0], track()[2]
        e.step(0, *stick_world(e, world_yaw_to(p, x, z)), 2)
    chk(tag)
    if callable(expect_y): expect_y = expect_y()
    if expect_y is not None and abs(player(e)['y'] - expect_y) > 3:
        print('MISSED', tag, player(e)); sys.exit(1)
def wait_until(cond, tag, maxf=600):
    for i in range(maxf):
        if cond(): return
        e.step(0, 0, 0, 2); chk(tag)
    print('timeout', tag); sys.exit(1)
def ride(cid, cond, tag, maxf=600):
    for i in range(maxf):
        if cond(): return
        b = box(cid); p = player(e)
        st = stick_world(e, world_yaw_to(p, b[0], b[2]), 30) if math.hypot(b[0] - p['x'], b[2] - p['z']) > 8 else (0, 0)
        e.step(0, st[0], st[1], 2); chk(tag)
    print('timeout', tag); sys.exit(1)
e.load(os.environ.get('START', 'states/omo11_e1_from_omo10.st'))
for i in range(20): e.step(0, 0, 0, 2)
walk(665, -105, 'to ledge14'); stage('a_floor_by_ledge14')
jump_to(622, -105, tag='ledge14', expect_y=35); stage('b_ledge14')
wait_until(lambda: box(54)[1] < 62, 'wait54'); jump_to(545, -105, tag='onto54', expect_y=lambda: box(54)[1]); stage('c_on54')
ride(54, lambda: box(54)[1] > 139.5, 'ride54'); walk(465, -105, 'onto15'); stage('d_ledge15', 140)
WHEEL = (42, 45, 48)
def board_target():
    for c in WHEEL:
        b = box(c)
        if 360 < b[0] < 390 and 125 < b[1] < 150: return c
    return None
wait_until(lambda: board_target() is not None and box(board_target())[1] < 145, 'wait wheel')
wc = board_target(); walk(box(wc)[0], -104, 'onto wheel', tol=5, maxf=40); stage('e_on_wheel', box(wc)[1])
ride(wc, lambda: box(wc)[0] < 262 and box(wc)[1] > 135, 'ride wheel'); walk(170, -104, 'onto20'); stage('f_ledge20', 140)
wait_until(lambda: box(57)[1] > 138, 'wait57'); walk(85, -105, 'onto57'); stage('g_on57')
ride(57, lambda: box(57)[1] < 60, 'ride57 down'); walk(20, -105, 'off57'); walk(-20, -105, 'floor'); stage('h_floor_west')
e.save(sys.argv[1])
