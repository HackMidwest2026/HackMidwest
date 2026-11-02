"""Deterministic shimmer particle geometry (status_star_shimmer.c): positions and scales per frame are fixed by the
InitialVelocities table; only the colours are random. Counts how many particles are individually readable:
centre on screen, visible star radius >= RMIN px (320x240 space), and the centre not covered by a later-drawn
(on top) particle. Rotation (frameCounter*10 deg) is ignored; star arms reach ~VIS*scale px."""
import sys
V = [(247,105),(239,87),(17,87),(9,105),(0,122),(230,69),(26,69),(221,52),(35,52),(202,49),(186,255),(200,241),(0,200),
     (56,241),(70,255),(54,49),(196,222),(239,191),(17,191),(60,222),(85,13),(74,46),(99,27),(93,43),(12,33),(12,22),
     (24,22),(24,33),(12,10),(24,10),(24,45),(232,33),(232,22),(232,45),(113,40),(193,203),(190,183),(182,46),(163,43),
     (35,182),(52,173),(12,45),(244,22),(244,33),(232,10),(244,10),(244,45),(204,173),(221,182),(186,164),(171,13),
     (157,27),(143,40),(63,203),(66,183),(70,164)]
S = [40,90,81,72,65,59,53,47,43,38,34,31,28,25,22,20,18,16,15,13,12,10,9,8,7,7,6,5,5,4]
s8 = lambda v: v - 256 if v > 127 else v
def tracks(ex, ey):
    out = []
    for vx, vy in V:
        x, y, dx, dy = ex, ey, s8(vx) * 0.1, -s8(vy) * 0.1
        t = []
        for k in range(30):
            x += dx; y += dy; dx *= 0.92; dy *= 0.92
            t.append((x, y, S[k] * 0.04))
        out.append(t)
    return out
def readable(ex, ey, VIS=2.5, RMIN=3.0, TOP=8, W=320):
    T = tracks(ex, ey); best = {}
    for k in range(30):
        for j in range(56):
            x, y, sc = T[j][k]; r = VIS * sc
            if r < RMIN or y < TOP or y > 232 or x < 0 or x > W: continue
            if any(((T[i][k][0] - x) ** 2 + (T[i][k][1] - y) ** 2) ** 0.5 < VIS * T[i][k][2] + 1.0 for i in range(j + 1, 56)):
                continue
            if r > best.get(j, (0, 0))[1]: best[j] = (k, r)
    return best
if __name__ == '__main__':
    for ex in (32, 52, 82, 112):                       # emitter x = bar x + 20 + SPsegments*2.5 (0..8 bars of 8 segs)
        for VIS, RMIN in ((2.5, 3.0), (2.5, 2.0), (3.5, 3.0)):
            b = readable(ex, 46, VIS, RMIN)
            print('emitter x %3d VIS %.1f RMIN %.1f: %2d readable particles, frames %s' % (
                ex, VIS, RMIN, len(b), sorted(set(v[0] for v in b.values()))))
