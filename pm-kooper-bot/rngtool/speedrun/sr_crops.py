"""Cut the coin-box region (x 480..560, y 0..64 of 640x480) out of every video frame -> crops.rgb"""
import sys, numpy as np
from PIL import Image
D = sys.argv[1]; W, H = 640, 480; FS = W * H * 3 // 2
f = open(D + '/run.y4m', 'rb'); f.readline(); out = open(D + '/crops.rgb', 'wb'); n = 0
while True:
    if not f.readline(): break
    buf = f.read(FS)
    y = np.frombuffer(buf, np.uint8, W * H).reshape(H, W)[0:64, 480:560]
    u = np.frombuffer(buf, np.uint8, W * H // 4, W * H).reshape(H // 2, W // 2)[0:32, 240:280]
    v = np.frombuffer(buf, np.uint8, W * H // 4, W * H * 5 // 4).reshape(H // 2, W // 2)[0:32, 240:280]
    im = Image.merge('YCbCr', [Image.fromarray(np.ascontiguousarray(y)), Image.fromarray(np.ascontiguousarray(u)).resize((80, 64)), Image.fromarray(np.ascontiguousarray(v)).resize((80, 64))]).convert('RGB')
    out.write(im.tobytes()); n += 1
print('frames', n)
