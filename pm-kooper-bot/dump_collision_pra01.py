"""dump nok_14's loaded collision (gCollisionData) and its triggers to json."""
import json, sys
from emu import Emu
from pm import *

GCOLL = 0x800B42C0
TRIGLIST = 0x8015E310

def read_collision(e, base=GCOLL):
    verts_ptr, coll_ptr = e.u32(base), e.u32(base + 4)
    n = e.s16(base + 0xC)
    colliders = []
    for i in range(n):
        c = coll_ptr + i * 0x1C
        flags = e.u32(c)
        ntri = e.s16(c + 0xA)
        tbl = e.u32(c + 0xC)
        tris = []
        for t in range(ntri):
            tp = tbl + t * 0x40
            vs = []
            for k in range(3):
                vp = e.u32(tp + 4 * k)
                vs.append([e.f32(vp), e.f32(vp + 4), e.f32(vp + 8)])
            normal = [e.f32(tp + 0x30), e.f32(tp + 0x34), e.f32(tp + 0x38)]
            tris.append({'v': vs, 'n': normal, 'one_sided': e.s16(tp + 0x3C)})
        colliders.append({'id': i, 'flags': flags, 'next': e.s16(c + 4), 'child': e.s16(c + 6), 'tris': tris})
    return colliders

def read_triggers(e):
    lst = e.u32(TRIGLIST)
    out = []
    for i in range(64):
        t = e.u32(lst + 4 * i)
        if t == 0: continue
        out.append({'slot': i, 'flags': e.u32(t), 'collider': e.s32(t + 8), 'evt': e.u32(t + 0x10)})
    return out

if __name__ == '__main__':
    e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), os.environ.get('PM_TMP', '/dev/shm/pmbot'))
    e.load('states/pra01_start.st')
    for i in range(60): e.step()
    print('ran 600 frames, mode', e.s16(GAME_MODE), player(e))
    cols = read_collision(e)
    zones = read_collision(e, 0x800D91B0)
    trig = read_triggers(e)
    json.dump({'colliders': cols, 'zones': zones, 'triggers': trig}, open('pra01_collision.json', 'w'))
    print(len(cols), 'colliders', sum(len(c['tris']) for c in cols), 'tris;', len(zones), 'zones')
    for t in trig: print('trigger', hex(t['flags']), 'collider', t['collider'], hex(t['evt']))
    cs = COLLISION
    print('collision status floor', e.s16(cs + 2), 'below', e.s16(cs + 6), player(e))
