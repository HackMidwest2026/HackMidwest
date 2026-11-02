"""Per capture frame features of a 1280x720 OBS capture: the status-bar coin box (white = shine) and the input
display's A icon (blue). usage: charge_hud.py CLIP.mkv OUT.npz"""
import sys, subprocess, numpy as np
CX, CY, CW, CH = 1080, 40, 40, 52        # coin box (status-bar coin only)
AX, AY, AW, AH = 944, 654, 50, 46        # input display: A icon
def crops(path, x, y, w, h):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'crop=%d:%d:%d:%d' % (w, h, x, y), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, h, w, 3).astype(np.int16)
if __name__ == '__main__':
    c = crops(sys.argv[1], CX, CY, CW, CH); a = crops(sys.argv[1], AX, AY, AW, AH)
    mx = c.max(3); mn = c.min(3)
    white = (mn > 190).mean((1, 2))           # shine flash
    gold = ((c[..., 0] > 150) & (c[..., 1] > 110) & (c[..., 2] < 90)).mean((1, 2))   # coin present
    blue = ((a[..., 2] - (a[..., 0] + a[..., 1]) / 2) > 60).mean((1, 2))
    np.savez(sys.argv[2], white=white, gold=gold, blue=blue)
    print(len(white), 'frames')
