"""Headless recorder for the mac_01 OOB partner glitch video (log format of isk11_explain_record.py). Teleport onto the
OOB grass (RAM, labeled), wait, walk south off the edge, fall, respawn, idle; optional C-down on frame CDOWN (counted
like mac01_flicker.py). usage: mac01_record.py DIR  env CDOWN"""
import glob, json, math, os, sys, time
from emu import *
from pm import *
from nav import stick_world
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); CD = int(os.environ.get('CDOWN', '-1'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mrec%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
log = []; k = [0]
def rec(tag, shot=True):
    p, l = player(e), lk(); ptr = e.u32(PTR)
    r = {'k': k[0], 'tag': tag, 'm': [p['x'], p['y'], p['z']], 'act': p['action'], 'l': [l['x'], l['y'], l['z']], 'ls': l['speed'], 'st': e.u32(STATE) >> 16,
         'ptr': ptr, 'idx': e.u32(IDX), 't': [e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)], 'ty': e.f32(HIST + 16 * ptr + 8),
         'hist': [[round(e.f32(HIST + 16 * i + 4), 1), round(e.f32(HIST + 16 * i + 12), 1)] for i in range(40)], 'map': where(e)[1], 'shot': shot}
    if shot:
        while len(glob.glob(os.path.join(OUT, 's*.st'))) > 80: time.sleep(0.5)
        e.save(os.path.join(OUT, 's%05d.st' % k[0]))
    log.append(r); k[0] += 1
e.load('states/mac01_e0.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -480); e.wf32(PLAYER + PS_POS + 4, 20); e.wf32(PLAYER + PS_POS + 8, 368)
for i in range(180): e.step(0, 0, 0, 2); rec('setup: Mario teleported (RAM, once) onto the out-of-bounds grass by Rowf\'s shop', i % 3 == 0)
respawn = None; prevy = player(e)['y']
for f in range(260):
    if respawn is None: st = stick_world(e, 180); tag = 'walk south off the wall-less edge into the void (inputs from here on)'
    else: st = (0, 0); tag = 'after the respawn: Mario stands still'
    b = D_CBUTTON if f == CD else 0
    e.step(b, st[0], st[1], 2); p = player(e)
    if respawn is None and f > 20 and abs(p['y'] - prevy) > 500: respawn = f
    prevy = p['y']
    if f == CD: tag = 'C-DOWN on the snap frame (Laki speed %.2f)' % lk()['speed']
    elif respawn is not None and f == respawn: tag = 'RESPAWN: Mario back at his last good spot, Laki still ~19,000 units up'
    elif respawn is not None and lk()['speed'] > 30 and CD < 0: tag = 'SNAP: Laki more than 1000 units from Mario -> placed on him (speed %.1f)' % lk()['speed']
    elif respawn is None and p['y'] > 100: tag = 'the fall integrator flips: Mario flies UP (uncapped), still recorded in Laki\'s history'
    rec(tag)
    if CD >= 0 and f > CD + 70: break
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w')); open(os.path.join(OUT, 'DONE'), 'w').write('1')
print('recorded', len(log), 'respawn', respawn)
