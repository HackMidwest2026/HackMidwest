"""v86: the Normal Boots Final Bowser phase-2 measurements as a fixture (fixtures/fbnb_p2_logs.json, test_fbnb_turn.js).
Inputs: nb_cc/gch_log.py runs from states/boss_2304_nbg_t2menu.st (nb_p2_state.py: T1 Peach Beam + Goombario Charge done,
Bowser 89 HP; Mario at 1 HP written by gch_log: Close Call), and pb_nb_log.py runs from boss_2304_nbg_pbtarget.st (the T2
menu's Power Bounce target screen, Normal Boots). Per Charge run: Goombario's confirm G, the box A P (or none), the frames
of Goombario's two energy_in_out creations, Bowser's AI frame and its RandInt calls (max, value, with the seed before
them), the Close Call roll's frame and value, Mario's HP at the end, the next menu. Per Power Bounce run: the cap rolls
(frame, value) and the hits' draw frames and counts. usage: python3 nb_p2_fixture.py OUT.json GCH_DIR PB.json"""
import sys, os, json, glob
sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from rngsim import rand_int
out, gdir, pbf = sys.argv[1], sys.argv[2], sys.argv[3]
runs = []
for f in sorted(glob.glob(gdir + '/g_*.json')):
    d = json.load(open(f)); L = d['log']; m = d['marks']; G = m['G'][0]; P = (m.get('P') or [None])[0]
    ai = [i for i, x in enumerate(L) if i > G and any(c[0] == '802d46e0' for c in x['c'])][0]
    cc = [i for i, x in enumerate(L) if any(c[0] == '80277518' for c in x['c'])][0]
    def dec(i, who):
        s = int(L[i - 1]['seed'], 16); o = []; s0 = None
        for c in L[i]['c']:
            if c[0] == who and s0 is None: s0 = s
            s, v = rand_int(s, abs(c[1]))
            if c[0] == who: o.append([c[1], v])
        return s0, o
    s_ai, aid = dec(ai, '802d46e0'); _, ccv = dec(cc, '80277518')
    gc = [i - G for i, x in enumerate(L) if G < i < G + 40 and any(c[0] == 'e00d6160' for c in x['c'])]
    menu = m['end'][0] if d['hpEnd'] > 0 else None                  # the log stops on the next Mario menu (battle state 13)
    runs.append(dict(seed=d['seed'], K=d['K'], G=G, P=P, gc=gc, ai=ai, aiSeed='%08x' % s_ai, aiDraws=aid, cc=cc, ccv=ccv[0][1], hpEnd=d['hpEnd'], menu=menu))
pb = json.load(open(pbf))
pbr = []
for c in pb['cases']:
    hits = {}
    for f, ra, mx, v in c['log']:
        if ra == 'e00861ec': hits[f] = hits.get(f, 0) + 1
    pbr.append(dict(seed=c['seed'], rolls=c['rolls'], hits=sorted(hits.items())))
json.dump(dict(about='v86 Normal Boots Final Bowser phase 2 (T2: Peach Beam on T1, Goombario Super, Bowser 89 HP, Mario 1 HP), emulator JP', vars=dict(turn=1, sinceShock=1, sinceStar=1, sinceClaw=4, sinceSlam=4, sinceRecover=1, recovers=3, enchanted=False, charged=True, hpGap=0),
               charge=runs, pb=dict(charge=pb['charge'], cases=pbr)), open(out, 'w'), separators=(',', ':'))
print(len(runs), 'Charge runs', len(pbr), 'Power Bounce runs')
