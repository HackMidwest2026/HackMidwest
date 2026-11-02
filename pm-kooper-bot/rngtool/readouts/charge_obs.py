"""Charge rays (energy_in_out type 6) readout: geometry + per-frame polar ridge maps.

Geometry (decomp + JP RAM display list D_09000688, verified on emulator frames):
  part i>0 is a quad x in [0,128], y in [-5,5] (local), drawn with  S(scale_i,1,1) * T(pos.x + 20) * Rz(unk_3C)
  under part 0's  S(scale0) * Ry(-camYaw) * T(effect pos).  So ray i covers world distance
  D in scale0 * [pos.x + 20, pos.x + 20 + 128 * scale_i] from the effect centre along direction (cos t, sin t, 0).
  Screen = row vector [x y z 1] * Camera.mtxPerspective (gCameras[1] + 0xD4), viewport (296x200 at 12,20 in 320x240).
  The image shown on game frame f+1 is the RAM state after frame f.
P[f][theta][d]: ridge response (luma on the ray minus luma beside it, beside = +-W px in 320 space,
  perpendicular to the projected ray) at world distance d*DSTEP from the centre, theta integer degrees."""
import numpy as np, cv2, math
DSTEP = 4.0
ND = 96            # D up to 384 world units
def project(M, vp, P):
    W, H, X0, Y0 = vp
    v = np.concatenate([np.asarray(P, float), np.ones(P.shape[:-1] + (1,))], -1) @ np.asarray(M, float).reshape(4, 4)
    return X0 + W / 2 * (1 + v[..., 0] / v[..., 3]), Y0 + H / 2 * (1 - v[..., 1] / v[..., 3]), v[..., 3]
def ray_points(centre, scale0=1.0):
    th = np.radians(np.arange(360))[:, None]; D = (np.arange(ND) + 0.5)[None, :] * DSTEP
    cx, cy, cz = centre
    return np.stack([cx + D * np.cos(th), cy + D * np.sin(th), cz + 0 * th * D], -1)
def polar_ridge(Y, to_img, M, vp, centre, W=2.0):
    """Y: luma image (float32). to_img(x320, y320) -> (u, v) image pixel coords."""
    P = ray_points(centre)
    x, y, w = project(M, vp, P)
    # screen direction of each ray (from the projected centre)
    c0x, c0y, _ = project(M, vp, np.asarray(centre, float)[None, :])
    dx, dy = x - c0x[0], y - c0y[0]; n = np.hypot(dx, dy) + 1e-9
    tx, ty = -dy / n, dx / n
    def samp(xx, yy):
        u, v = to_img(xx, yy)
        return cv2.remap(Y, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    on = samp(x, y); l = samp(x + W * tx, y + W * ty); r = samp(x - W * tx, y - W * ty)
    R = on - 0.5 * (l + r)
    inside = (x > vp[2] + 2) & (x < vp[2] + vp[0] - 2) & (y > vp[3] + 2) & (y < vp[3] + vp[1] - 2) & (w > 0)
    R[~inside] = np.nan
    return R, (c0x[0], c0y[0])
def luma(rgb):
    rgb = rgb.astype(np.float32)
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
def build_maps(items, centre, W=2.0):
    """items: list of (Y luma image, to_img, M, vp) for relative frames 0..N-1 (None = missing frame).
    Returns float32 prefix sums S[N][360][ND+1] and counts C[N][360][ND+1] of the ridge response."""
    N = len(items); S = np.zeros((N, 360, ND + 1), np.float32); C = np.zeros((N, 360, ND + 1), np.float32)
    for n, it in enumerate(items):
        if it is None: continue
        Y, to_img, M, vp = it
        R, _ = polar_ridge(Y, to_img, M, vp, centre, W)
        ok = ~np.isnan(R); R = np.where(ok, R, 0)
        S[n, :, 1:] = np.cumsum(R, 1); C[n, :, 1:] = np.cumsum(ok, 1)
    return S, C
VIDEO_MAP = (3.2637, 272.82, 3.3221, -31.09)   # 1280x720 OBS capture (GV-USB2): u = SX*x + OX, v = SY*y + OY (320x240 space);
# fitted by full-frame NCC of capture frame 101 against the emulator render (0.983), blur 1.29 px at 640x480
def video_to_img(m=VIDEO_MAP):
    SX, OX, SY, OY = m
    return lambda x, y: (SX * x + OX, SY * y + OY)

def warp_video(rgb, m=VIDEO_MAP):
    """capture frame -> 640x480 game raster (2 px per 320-space unit)"""
    SX, OX, SY, OY = m
    ys, xs = np.mgrid[0:480, 0:640].astype(np.float32) / 2
    return cv2.remap(luma(rgb), (xs * SX + OX).astype(np.float32), (ys * SY + OY).astype(np.float32), cv2.INTER_LINEAR)
def residual(Yg, bg, sigma=1.29, mask_margin=4):
    """Yg: frame in the 640x480 raster; bg: emulator background-only render (DIAGNOSTIC, rays zero length) of the same
    frame. Robust affine fit Yg ~ k*bg + b (blurred to the capture), returns Yg - fit."""
    B = cv2.GaussianBlur(bg, (0, 0), sigma)
    m = np.zeros(Yg.shape, bool); m[40 + mask_margin:440 - mask_margin, 24 + mask_margin:616 - mask_margin] = True
    x, y = B[m], Yg[m]; w = np.ones_like(x)
    for it in range(4):
        A = np.stack([x * w, w], 1); k, b = np.linalg.lstsq(A, y * w, rcond=None)[0]
        r = y - (k * x + b); s = 1.4826 * np.median(np.abs(r)) + 1e-3; w = 1 / np.maximum(1, np.abs(r) / (2 * s))
    return (Yg - (k * B + b)).astype(np.float32), (k, b)
