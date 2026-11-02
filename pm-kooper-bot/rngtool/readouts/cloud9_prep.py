"""Cloud Nine puffs on a real capture: white masks for the seed search (cloud9_search.c).
Input: the capture's frames as PNGs (1280x720), FIRST = the file where puff 0's birth dot shows (age 1).
Output (OUTDIR/masks.bin): for ages 1..(NF) frames FIRST, FIRST+2, ... (60 fps capture, 30 fps game), a uint8 'pure
white' mask (min channel > 215, spread < 45) of the region X0..X0+W, Y0..Y0+H.
Projection (from the emulator, cloud9_calib.py: same camera as the Hallway Bowser state, aligned on sprites):
  capture x = 773.8 + 4.313*dx ;  capture y = 503.5 - 4.18*(dy + 0.6*(age - 1))
usage: python3 cloud9_prep.py FRAME_PATTERN FIRST NF OUTDIR   (FRAME_PATTERN like fr/%03d.png, frames cropped at x=310)"""
import sys, numpy as np, cv2
pat, first, nf, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
X0, Y0, W, H = 560, 360, 440, 320          # capture px
XOFF = 310                                  # the frames are cropped at x = 310
ms = []
for i in range(-1, nf):                     # index 0 = the frame before puff 0's birth
    a = cv2.imread(pat % (first + 2 * i)).astype(int)
    mn = a.min(2); sp = a.max(2) - mn
    w = ((mn > 215) & (sp < 45)).astype(np.uint8)
    ms.append(w[Y0:Y0 + H, X0 - XOFF:X0 - XOFF + W])
np.array(ms, np.uint8).tofile(out + '/masks.bin')
print('frames', len(ms), 'roi', X0, Y0, W, H)
