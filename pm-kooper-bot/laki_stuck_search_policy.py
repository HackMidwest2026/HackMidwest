"""Random input policy shared by laki_stuck_search.py and laki_stuck_replay.py."""
from emu import A
from corner_sweep import stick_for
def policy(rng, F):
    seq = []
    while len(seq) < F:
        r = rng.random(); d = rng.uniform(0, 360); k = rng.randint(4, 40)
        if r < 0.12: seq += [(0, 0, 0)] * rng.randint(3, 30)
        elif r < 0.30:
            h = rng.randint(1, 15); seq += [(A,) + stick_for(d, 80)] * h + [(0,) + stick_for(d, 80)] * rng.randint(0, 20)
        else: seq += [(0,) + stick_for(d, rng.choice((80, 80, 40)))] * k
    return seq[:F]
