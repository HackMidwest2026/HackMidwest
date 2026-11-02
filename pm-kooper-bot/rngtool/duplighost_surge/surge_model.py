"""Model of every gRandSeed draw from the first Spiny Surge throw to the 4 Duplighost copy rolls (JP).

Measured in the emulator (trace_turn.py) for the turn: Lakilester (Super) Spiny Surge, then Mario: Strategies >
Change Member > Bombette (confirm on frame C), then the enemy turn. Frame numbers are game frames (2 VIs).

Per game frame, in this order:
  1. script / effect-creation draws:
     - each thrown spiny: rand_int(140), rand_int(80) (ThrowSpinyFX), rand_int(360), rand_int(10) (fx_throw_spiny)
     - the hit: one fx_firework per Duplighost (4) at L+26, L+32, L+38, L+44 (L = frame of the last throw);
       rand_int(359) x 8 each when the damage is 3 (Super rank at 100%), x 6 when it is 1-2
     - copy rolls RandInt(1000) (< 600 = copy): first at C+56; after a copy the next is 97 frames later; after a
       failed copy (flying tackle) the tackle's fx_firework (8 x rand_int(359)) is at roll+34 and the next roll at
       roll+78 (same as the dup3 model of the Bombette "do nothing" turn)
  2. the status-bar coin, if due: rand_int(100); >= 70 (a shine) -> next draw 48 frames later, else 24
  3. one rand_int(1) per frame (0x800269AC)
Mario's menu (gBattleState 13) comes up at L+103. Menu navigation has no draws (only the coin and the per-frame one).
Rejection sampling (an extra step) has probability < 1e-6 per draw for all these ranges and is modelled exactly."""
MUL = 0x5D588B65
M = 0xFFFFFFFF


def adv(s):
    return (s * MUL + 1) & M


def internal(s, mx):
    d = M // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v


def rand_int(s, mx):
    if mx == 0: return s, 0
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)


SPINY = (140, 80, 360, 10)
FW_AT = (26, 32, 38, 44)
MENU_AT = 103          # Mario's menu, frames after the last throw
ROLL1 = 56             # first copy roll, frames after the Change Member confirm
COPY_NEXT, FAIL_NEXT, TACKLE_FX = 97, 78, 34


def simulate(s1, nc, spinies, confirm, fw_draws=8, need=4, trace=None):
    """s1: gRandSeed just before the first throw's frame (frame 0 = first throw); nc: frame of the next coin draw
    (>= 0; frames relative to the first throw); spinies: throw frames (relative, first is 0); confirm: frame of the
    Change Member confirm (relative). Returns the list of copy-roll values (stops early once `need` copies are
    impossible), or appends every draw to `trace` as (frame, kind, max, value)."""
    s = s1; L = spinies[-1]; sp = set(spinies)
    fw = {L + a: fw_draws for a in FW_AT}
    next_roll = confirm + ROLL1; rolls = []; fails = 0
    t = 0
    while len(rolls) < 4:
        if t in sp:
            for mx in SPINY:
                s, v = rand_int(s, mx)
                if trace is not None: trace.append((t, 'spiny', mx, v))
        if t in fw:
            for i in range(fw[t]):
                s, v = rand_int(s, 359)
                if trace is not None: trace.append((t, 'fw', 359, v))
        if t == next_roll:
            s, v = rand_int(s, 1000); rolls.append(v)
            if trace is not None: trace.append((t, 'roll', 1000, v))
            if v < 600: next_roll = t + COPY_NEXT
            else:
                fails += 1
                if fails > 4 - need and trace is None: return rolls
                fw[t + TACKLE_FX] = 8; next_roll = t + FAIL_NEXT
        if t == nc:
            s, v = rand_int(s, 100); nc = t + (48 if v >= 70 else 24)
            if trace is not None: trace.append((t, 'coin', 100, v))
        s, v = rand_int(s, 1)
        t += 1
    return rolls


def copies(rolls):
    return sum(1 for v in rolls if v < 600)


def outcome_table(s1, nc, spinies, c_from, c_to, fw_draws=8):
    """number of copies (0-4) for each confirm frame c_from..c_to (relative to the first throw)"""
    return [copies(simulate(s1, nc, spinies, c, fw_draws, need=0)) for c in range(c_from, c_to + 1)]
