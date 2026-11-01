"""Exact model of the RNG from Mario's Hallway Bowser target screen to Time Out's STOP roll (JP).
Per frame, in order: [Time Out roll on frame C+386 (first)], [Time Out effect draws on C+24 / C+73 / C+112 (the
effects are spawned by the battle script, which runs before the HUD)], [status-bar coin draw when due], [the
per-frame step]. C = frame of the target-confirm A press.
Coin: draw rand_int(100); 70+ = shine; the next draw comes 48 frames later after a shine, else 24.
Time Out works if the roll (rand_int(100)) <= 30 (Bowser STOP chance 30)."""
M = 0xFFFFFFFF
MUL = 0x5D588B65
def adv(s): return (s * MUL + 1) & M
def internal(s, mx):
    d = M // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)
EFFECTS = {24: [40000] * 72, 73: [359, 10, 10] * 40, 112: [30000] * 72}
ROLL = 386
def coin(s):
    s, v = rand_int(s, 100); return s, v >= 70
def timeout_roll(seed, next_coin, confirm, t0=0):
    """seed = RNG value before frame t0's draws; next_coin = frame of the next coin draw (>= t0);
    confirm = frame of the target-confirm A. Returns the roll."""
    s, nc = seed, next_coin
    for t in range(t0, confirm + ROLL + 1):
        if t == confirm + ROLL:
            s, v = rand_int(s, 100); return v
        for mx in EFFECTS.get(t - confirm, ()): s, _ = rand_int(s, mx)
        if t == nc:
            s, sh = coin(s); nc = t + (48 if sh else 24)
        s = adv(s)
def works(seed, next_coin, confirm, t0=0): return timeout_roll(seed, next_coin, confirm, t0) <= 30
