from rmc_lo_end import *
def post_search(t, tag, rs=(0, 4, 8, 12, 16, 20, 24, 30, 40), tz=60):
    """from the C-down frame: 16 frames, ride r toward the pra_01 south door, B, spin to the door, hold right, A."""
    e = t.e; S = '/dev/shm/pmbot/lp_%s.st' % tag
    for i in range(16): t.step()
    e.save(S); n0 = t.n; res = []
    for r in rs:
        for rc in (20, 50, 90):
            for far in (60, 120):
                for stopd in (10, 30, 60):
                    e.load(S); t.n = n0
                    ride(t, 1000, tz, r); dismount(t)
                    af, mc = to_door(t, 1000, tz, (80, 0), rc, far, stopd)
                    if af: res.append((af, mc, r, rc, far, stopd))
    return sorted(res)
