"""Infinite Bombette window: kmr_11 strip, C-down, Mario walks south-east off the void edge at game frame 26, falls,
gets respawned (lastGoodPos) during Bombette's FLY. Bombette (launched downward by jumpVel = (mario.y - her.y)/20 + 30)
ends FLY >500 below Mario, under the strip, takes the 'far' branch of FALL and falls forever: partnerActionState stays
BOMBETTE_3 while Mario is free. Saves states/kmr11_bombette_inf.st, then runs experiments.
usage: bombette_infinite.py make | long N | menu | cdown | jump"""
import sys
from emu import *
from pm import *
PSTAT = 0x8010ED70
e = Emu('pm-jp.z64', '/dev/shm/pmbot/binf')
def bomb():
    b = [n for n in npcs(e) if n['id'] == -4]
    return b[0] if b else {'x': 0, 'y': 0, 'z': 0, 'addr': PLAYER, 'flags': 0}
def show(tag):
    b = bomb(); p = player(e)
    print('%s state %d acting %d bomb (%.1f, %.1f, %.1f) jumpVel %.2f flags %08x | mario (%.1f, %.1f, %.1f) act %d inDis %d mode %d map %s' % (
        tag, e.s8(PSTAT), e.s8(PSTAT + 3), b['x'], b['y'], b['z'], e.f32(b['addr'] + 0x1C), b['flags'], p['x'], p['y'], p['z'], p['action'],
        e.s8(PLAYER + 0x15), e.s16(GAME_MODE), where(e)), flush=True)
mode = sys.argv[1]
if mode == 'make':
    e.load('states/kmr11_e0_bombette.st'); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, -230.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, 10.0)
    e.step(0, 0, 0, 40); e.step(0, -80, 0, 2); e.step(0, 0, 0, 10)
    e.step(D_CBUTTON, 0, 0, 2)
    for f in range(200):
        e.step(*((0, 56, -56) if 26 <= f < 66 else (0, 0, 0)), 2)
        if f in (86, 87, 98, 110, 112, 130, 199): show('f%d' % f)
    e.step(0, 0, 0, 1); e.save('states/kmr11_bombette_inf.st'); print('saved')
else:
    e.load('states/kmr11_bombette_inf.st')
    if mode == 'long':
        n = int(sys.argv[2])
        for i in range(n):
            e.step(0, 0, 0, 2)
            if i % (n // 10) == 0: show('t+%d' % i)
        show('end')
    elif mode == 'menu':
        show('before'); e.step(R_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 20); show('after C-right')
        e.step(START, 0, 0, 2); e.step(0, 0, 0, 30); show('after START')
    elif mode == 'cdown':
        show('before'); e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 60); show('after C-down')
    elif mode == 'jump':
        show('before')
        for g in range(40): e.step(A if g < 8 else 0, -80 if g < 20 else 0, 0, 2)
        show('after walk+jump')
if mode == 'exit':
    # teleport onto the west exit floor (deiliw, x -938..-1038) and walk out; follow into the next map
    show('before')
    e.wf32(PLAYER + PS_POS, -900.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, -56.0)
    for i in range(400):
        e.step(0, -80 if i < 60 else 0, 0, 2)
        if i % 40 == 0: show('t+%d' % i)
    show('end')
    for g in range(30): e.step(D_CBUTTON if g == 2 else 0, 0, 0, 2)
    show('after C-down in new map')
    e.step(START, 0, 0, 2); e.step(0, 0, 0, 30); show('after START in new map')
if mode == 'battle':
    e.w8(game_status(e) + 0x74, 0)
    g = [n for n in npcs(e) if n['id'] >= 0 and n['y'] > -500]
    print('npcs', [(n['id'], round(n['x']), round(n['y']), round(n['z'])) for n in g])
    t = g[0]
    show('before')
    # put Mario right next to an enemy NPC
    e.wf32(PLAYER + PS_POS, t['x'] + 20); e.wf32(PLAYER + PS_POS + 4, t['y']); e.wf32(PLAYER + PS_POS + 8, t['z'])
    for i in range(600):
        e.step(0, -80 if i < 20 else 0, 0, 2)
        if i % 60 == 0: show('t+%d' % i)
