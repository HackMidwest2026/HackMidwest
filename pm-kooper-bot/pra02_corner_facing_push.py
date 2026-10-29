"""pra_02 behind the mirror, REAL INPUTS: set Lakilester's facing to north-west by approaching the back-left corner
holding UP-LEFT (his facing is kept from his last movement; dismounting only ever gives 90/270). Then a continuous
steered push east (Mario kept 4 units behind Laki every frame) carries him past both back pillars to the right wall,
because his facing-based wall check holds him 18 units off the back wall (west-facing: 12.76, stuck on the pillars).
Starts from states/pra02_back_left.st. Saves /dev/shm/pmbot/dg_<startx>.st (push end at the right wall).
Measured: the return spike reaches 191-205; it is ~0.2 x (distance from the oldest trail point to Mario), so the
room caps it near 200 (right wall x 987 needs 220; the 170 strip at x 979.5-981.5 is blocked, Mario stops at x ~972)."""
import sys, math, itertools
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/dg')
PTR, STATE = 0x8010D17C, 0x8010D188
fstate = lambda: e.u32(STATE) >> 16
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L():
    a = laki()['addr']; return e.f32(a + 0x38), e.f32(a + 0x3C), e.f32(a + 0x40), e.f32(a + 0x0C)
def pstep(A, gap):
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A))
    p = player(e); lx, ly, lz, yw = L(); tx, tz = lx - gap * ux, lz - gap * uz
    d = math.hypot(tx - p['x'], tz - p['z'])
    s_ = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
    e.step(0, *s_, 2)
def go(tx, tz, maxf=250, tol=0.5):
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < tol: return
        mag = max(14, min(80, int(d * 10)))
        e.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), 2)
e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
for sx_, sz_, fr in ((150, -100, 70), (130, -80, 70), (110, -120, 60), (180, -60, 80)):
    e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
    go(sx_, sz_)
    for i in range(30): e.step(0, 0, 0, 2)
    for i in range(fr): e.step(0, -56, 56, 2)            # hold up-left into the back-left corner
    for i in range(40): e.step(0, 0, 0, 2)
    p = player(e); lx, ly, lz, yw = L()
    s = 'D from (%d,%d) up-left %d: mario (%.1f,%.1f) laki (%.1f,%.1f) yaw %.0f st %d ptr %d' % (sx_, sz_, fr, p['x'], p['z'], lx, lz, yw, fstate(), e.u32(PTR))
    if p['x'] < lx - 2:
        go(lx - 4, lz, 80, 0.3); lx1, ly1, lz1, yw1 = L(); s += ' | lined up, yaw %.0f' % yw1
        for f in range(1500):
            pstep(0, 4)
            if L()[0] > 975: break
        lx2, ly2, lz2, yw2 = L()
        s += ' | push -> laki (%.1f,%.1f) yaw %.0f st %d %s' % (lx2, lz2, yw2, fstate(), 'RIGHT WALL' if lx2 > 970 else ('past left pillar' if lx2 > 270 else 'stuck'))
        e.save('/dev/shm/pmbot/dg_%d.st' % sx_)
    print(s, flush=True)
