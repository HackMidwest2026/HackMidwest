"""Fast rock part of the setup (shortest waits from fast_fill.py): from states/pra01_top_rock.st walk at 160 deg for
10 frames, 1 neutral frame, jump left (stick 12 frames), wiggle on the rock until Laki's history ring is full, 1
neutral frame, hop right (stick 8 frames). rock_part(e, st) replays it through a step function st(buttons, stick,
tag); run as a script to save the end state (the seed for the arc search; V2=1: rock_part2). usage: fast_setup.py OUT.st"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
def rock_part(e, st):
    def jump(stick, hold, tag):
        for i in range(30):
            st(0x80 if i < 8 else 0, stick if i < hold else (0, 0), tag)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(10): st(0, stick_for(160, 80), 'walk left (angled down 20 deg) 10 frames')
    st(0, (0, 0), 'release')
    jump(stick_for(180, 80), 12, 'jump left onto the rock')
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for f in range(160):
        if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
        st(0, up if f % 2 == 0 else dn, "wiggle on the rock: fill Laki's history")
    st(0, (0, 0), 'history full')
    jump(stick_for(0, 80), 8, 'hop down to the right, next to Laki')
def rock_part2(e, st):
    """Walk-past start (fill_left_search.py, BACK): walk straight left 13 frames past the rock, wait 10 frames (Laki
    follows further left), jump holding down 8 frames onto the rock top, wiggle until the history ring is full, 1
    neutral frame, hop right (stick 8). Stale target (549.6, -15.9)."""
    def jump(stick, hold, tag):
        for i in range(30):
            st(0x80 if i < 8 else 0, stick if i < hold else (0, 0), tag)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(13): st(0, stick_for(180, 80), 'walk left 13 frames, past the rock')
    for i in range(10): st(0, (0, 0), 'wait 10 frames: Laki follows further left')
    jump(stick_for(90, 80), 8, 'jump holding down onto the rock top')
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for f in range(160):
        if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
        st(0, up if f % 2 == 0 else dn, "wiggle on the rock: fill Laki's history")
    st(0, (0, 0), 'history full')
    jump(stick_for(0, 80), 8, 'hop down to the right, next to Laki')
if __name__ == '__main__':
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/fs')
    e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
    n = [0]
    def st(b, s, tag=''): e.step(b, *s, 2); n[0] += 1
    (rock_part2 if os.environ.get('V2') else rock_part)(e, st)
    p, l = player(e), [x for x in npcs(e) if x['id'] == -4][0]; ptr = e.u32(PTR)
    print('%d frames: M (%.1f, %.1f, %.1f) L (%.1f, %.1f) state %d ptr %d target (%.1f, %.1f)' % (n[0], p['x'], p['y'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
    e.save(sys.argv[1]); print('saved', sys.argv[1])
