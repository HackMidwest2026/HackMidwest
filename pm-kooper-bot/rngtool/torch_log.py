# (run from the emulator working dir, bot1/) import os, sys, json
os.environ['M64P_DBG'] = '1'
from emu import *
from pm import *
from rngsim import *
st, sd = sys.argv[1], int(sys.argv[2], 16)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/t2%s%d' % (st[:6], os.getpid()))
e.load('states/' + st); e.step(0, 0, 0, 2)
e.w32(SEED, sd); e.w32(SEED2, sd)                     # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
seeds = []; toks = []
for f in range(1500):
    seeds.append(e.u32(SEED)); e.step(0, 0, 0, 2)
    toks.append(['C' if x['ra'] == 0x80146D54 else [x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32), hex(x['ra'])] for x in e.dbg_events() if x['ra'] != 0x800269AC])
json.dump({'seeds': seeds, 'toks': toks}, open('data/torch_%s_%08x.json' % (st[:-3], sd), 'w'))
both = [(f, ['C' if t == 'C' else t[1][-4:] for t in tk]) for f, tk in enumerate(toks) if 'C' in tk and len(tk) > 1]
print(st, '%08x' % sd, 'torch frames', [f for f, tk in enumerate(toks) if len(tk) >= 12][:4], '| coin+torch frames:', both[:3])
