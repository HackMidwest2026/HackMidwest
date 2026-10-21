"""Probe Bombette's post-blast window in mac_02 (Bombette state from make_state_room.py PARTNER=3).
Logs gPartnerStatus.partnerActionState / actingPartner, Bombette's NPC flags (0x100 = IGNORE_PLAYER_COLLISION),
Bombette / Mario y, and whether a mid-air A press in front of the street sign starts the sign script."""
import sys
from emu import *
from pm import *
PSTAT = 0x8010ED70
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bprobe')
def bomb():
    return [n for n in npcs(e) if n['id'] == -4][0]
def st(): return e.s8(PSTAT), e.s8(PSTAT + 3)
def setup(x, z):
    e.load('states/mac02_e0_bombette.st'); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    e.step(0, 0, 0, 60)
    e.step(0, 0, 80, 2); e.step(0, 0, 0, 10)             # face north (toward the sign)
def frame_log(tag, f):
    b = bomb(); p = player(e); a, ap = st()
    return '%s f%3d state %d acting %d bomb flags %08x ign %d bomb y %7.1f mario (%.1f, %.1f, %.1f) act %d inputDis %d' % (
        tag, f, a, ap, b['flags'], 1 if b['flags'] & 0x100 else 0, b['y'], p['x'], p['y'], p['z'], p['action'], e.s16(PLAYER + 0x0) if False else e.s8(PLAYER + 0x15) )
mode = sys.argv[1]
if mode == 'window':
    setup(-92.0, -120.0)
    e.step(D_CBUTTON, 0, 0, 2)
    prev = None
    for f in range(220):
        e.step(0, 0, 0, 2)
        a, ap = st(); b = bomb()
        cur = (a, ap, b['flags'] & 0x100)
        if cur != prev or f % 20 == 0: print(frame_log('W', f)); prev = cur
elif mode in ('sign', 'signctl'):
    setup(-92.0, -100.0)
    if mode == 'sign':
        e.step(D_CBUTTON, 0, 0, 2)
        f = 0
        while st()[0] != 3 and f < 200: e.step(0, 0, 0, 2); f += 1
        print('window opened after', f, 'game frames')
    # jump, then press A again near the apex while facing the sign
    run = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    for g in range(run + 30):
        b = A if run <= g < run + 6 or (g >= run + 7 and g % 2 == 0) else 0   # run, full jump, then tap A in the air
        e.step(b, 0, 80, 2)
        p = player(e)
        print(frame_log('S', g), 'mode', e.s16(GAME_MODE))
elif mode in ('push', 'pushctl'):
    # npc 7 at (-56, 0, 39): blast next to it (or not), then walk past it with Bombette following
    setup(-130.0, 40.0)
    target = [n for n in npcs(e) if n['id'] == 7][0]['addr']
    if mode == 'push':
        e.step(D_CBUTTON, 0, 0, 2)
        for f in range(200):
            e.step(0, 0, 0, 2)
            if st()[0] == 0 and f > 100: break
    print(frame_log('P', 0), 'npc7', round(e.f32(target + 0x38), 1), round(e.f32(target + 0x40), 1))
    for f in range(60):
        e.step(0, 80, 0, 2)
        if f % 10 == 0: print(frame_log('P', f), 'npc7', round(e.f32(target + 0x38), 1), round(e.f32(target + 0x40), 1), 'bomb', round(bomb()['x'], 1), round(bomb()['z'], 1))
if mode in ('spin', 'spinctl'):
    setup(-92.0, -100.0)
    if mode == 'spin':
        e.step(D_CBUTTON, 0, 0, 2)
        f = 0
        while st()[0] != 3 and f < 200: e.step(0, 0, 0, 2); f += 1
    for g in range(60):
        b = A if 6 <= g < 12 else 0                        # run 6, jump onto the ledge (no extra A taps)
        if g == 24: b = Z                                   # spin on the ledge, facing the sign
        if g in (27, 28): b = A                             # A during the spin
        e.step(b, 0, 80 if g < 17 else 0, 2)
        p = player(e)
        if g >= 20: print(frame_log('Z', g))
if mode in ('push4', 'push4ctl', 'push4walk'):
    setup(-26.0, -185.0)                                     # just south of NPC 4 (-26, 0, -220), facing it
    t = [n for n in npcs(e) if n['id'] == 4][0]['addr']
    e.step(0, 0, 80, 20)                                      # walk into it
    e.step(0, 0, 0, 6)
    if mode != 'push4ctl': e.step(D_CBUTTON, 0, 0, 2)
    last = None
    for f in range(260):
        sx, sy = (0, 0)
        if mode == 'push4walk' and st()[0] == 0 and f > 120: sx, sy = (0, 80)   # after she lands, keep walking into it
        e.step(0, sx, sy, 2)
        cur = (round(e.f32(t + 0x38), 2), round(e.f32(t + 0x40), 2))
        if cur != last or f % 40 == 0:
            b = bomb(); p = player(e)
            print('f%3d state %d ign %d npc4 %s bomb (%.1f, %.1f, %.1f) mario (%.1f, %.1f, %.1f)' % (f, st()[0], 1 if b['flags'] & 0x100 else 0, cur, b['x'], b['y'], b['z'], p['x'], p['y'], p['z']))
            last = cur
if mode == 'pushjump':
    # in the window, jump over NPC 4 (holding up) so Bombette's landing spot (Mario's xz + 6.5) overlaps it
    res = []
    for delay in range(0, 66, 3):
        setup(-26.0, -185.0)
        t = [n for n in npcs(e) if n['id'] == 4][0]['addr']
        e.step(0, 0, 80, 20); e.step(0, 0, 0, 6)
        e.step(D_CBUTTON, 0, 0, 2)
        f = 0
        while st()[0] != 3 and f < 200: e.step(0, 0, 0, 2); f += 1
        e.step(0, 0, 0, 2 * delay)
        x0, z0 = e.f32(t + 0x38), e.f32(t + 0x40)
        moved = 0.0; when = None
        for g in range(120):
            b = A if g < 10 else 0
            e.step(b, 0, 80 if g < 30 else 0, 2)
            dx, dz = e.f32(t + 0x38) - x0, e.f32(t + 0x40) - z0
            d = (dx * dx + dz * dz) ** 0.5
            if d > moved + 0.01: moved, when = d, (g, st()[0])
        p = player(e)
        res.append((delay, round(moved, 2), when, (round(e.f32(t + 0x38), 2), round(e.f32(t + 0x40), 2))))
        print('delay', delay, 'npc4 moved', round(moved, 2), 'last move at (frame, state)', when, 'npc4 now', res[-1][3], 'mario', round(p['x'], 1), round(p['z'], 1), flush=True)
