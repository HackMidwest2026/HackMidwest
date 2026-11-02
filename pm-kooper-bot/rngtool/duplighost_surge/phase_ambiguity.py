"""If the Surge readout leaves the coin phase open by a few frames (the coin drew between two throws that were not
both observed), how often does an all-4 frame planned for one phase still give 4 / 3+ under the other?
Model only (window_stats.after_confirm). Same seed at the menu, next coin draw shifted by DPH frames.
usage: python3 phase_ambiguity.py [N] [DPH...]"""
import sys, random
import window_stats as W
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
DPH = [int(x) for x in sys.argv[2:]] or [1, 2, 3, 6]
rnd = random.Random(3)
for d in DPH:
    n4 = both4 = both3 = 0
    for i in range(N):
        s = rnd.getrandbits(32); nc = rnd.randrange(d, 24)
        for c in range(40):                       # 40 confirm frames from this menu state
            st = W.jump(s, c); a = W.after_confirm(st, nc - c if nc - c >= 0 else (nc - c) % 24)
            if a != 4: continue
            n4 += 1
            b = W.after_confirm(st, (nc - d - c) % 24 if nc - d - c < 0 else nc - d - c)
            both4 += b == 4; both3 += b >= 3
    print('phase off by %d frames: an all-4 frame stays all-4 %.1f%%, 3+ %.1f%% (%d frames)' % (d, 100 * both4 / n4, 100 * both3 / n4, n4))
