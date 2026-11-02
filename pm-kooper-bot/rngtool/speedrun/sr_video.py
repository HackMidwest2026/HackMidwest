"""Overlay the page's view on the emulator run video: room (C-up open/closed), true shine draws, the page's detections,
its searches and lock, then encode an mp4. usage: sr_video.py DIR OUT.mp4 [title]"""
import json, sys, subprocess
sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from rngsim import adv
D, OUT = sys.argv[1], sys.argv[2]; TITLE = sys.argv[3] if len(sys.argv) > 3 else ''
SH = 700 * (0xFFFFFFFF // 1010); VMS = 1001 / 30
T = json.load(open(D + '/truth.json')); P = json.load(open(D + '/page.json')); tr = T['truth']
names = {15: 'maze (kpa_40)', 16: 'maze (kpa_41)', 36: 'kpa_102 (enemies, C-up closed)', 20: 'Duplighost room (kpa_53)'}
def ts(vf): s = max(0, vf) * VMS / 1000; return '%d:%02d:%05.2f' % (s // 3600, s % 3600 // 60, s % 60)
ev = []
rooms = [x for x in T['events'] if 'room' in x]
for i, r in enumerate(rooms):
    end = rooms[i + 1]['vf'] if i + 1 < len(rooms) else T['video_frames']
    ev.append((r['vf'], end, 'Room', names.get(r['where'][1], 'map %d' % r['where'][1]) + ('' if r['open'] else '  [C-up closed]')))
for gf, vf, prev, k, mp, md, vis in tr:
    if k == 2 and adv(prev) >= SH: ev.append((vf, vf + 12, 'True', 'true shine draw' + ('' if vis else ' (bar hidden)')))
t0 = P['t0']
for t in P.get('hist', []): vf = round((t - t0) / VMS); ev.append((vf, vf + 15, 'Det', 'page: shine detected'))
lockvf = None
for x in P.get('slog', []):
    vf = round((x['t'] - t0) / VMS)
    if x['ev'] in ('chainSearch', 'wideExtend', 'wideExtendTorch', 'torchSearchDone', 'carryDied'):
        ev.append((vf, vf + 60, 'Ev', '%s %s' % (x['ev'], {k: v for k, v in x.items() if k not in ('t', 'ev')})))
    if x['ev'] == 'lock' and lockvf is None: lockvf = vf
if lockvf is not None: ev.append((lockvf, T['video_frames'], 'Lock', 'PAGE LOCKED seed %08x' % (P['lock'] or 0)))
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 640
PlayResY: 480
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Room,DejaVu Sans,18,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,1,10,10,40,1
Style: True,DejaVu Sans,16,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,7,10,10,90,1
Style: Det,DejaVu Sans,16,&H0000FF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,7,10,10,115,1
Style: Ev,DejaVu Sans,13,&H00FFC080,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,1,10,10,70,1
Style: Lock,DejaVu Sans,22,&H0000FF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,140,1
Style: Title,DejaVu Sans,13,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,1,10,10,12,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = ['Dialogue: 0,%s,%s,%s,,0,0,0,,%s' % (ts(a), ts(b), st, txt) for a, b, st, txt in sorted(ev)]
if TITLE: lines.append('Dialogue: 0,%s,%s,Title,,0,0,0,,%s' % (ts(0), ts(T['video_frames']), TITLE))
open(D + '/ov.ass', 'w').write(hdr + '\n'.join(lines) + '\n')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', D + '/run.y4m', '-vf', 'ass=' + D + '/ov.ass', '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', OUT], check=True)
print('wrote', OUT, 'lock at video frame', lockvf)
