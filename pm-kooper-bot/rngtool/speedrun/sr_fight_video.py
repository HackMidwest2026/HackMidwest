"""Overlay for the fight run (sr_fight.py): the page's shine detections, lock, beeps (final beep frame), each press
(frames off the ideal frame, the page's press readout) and the game's outcome. usage: sr_fight_video.py DIR OUT.mp4 [title]"""
import json, sys, subprocess
D, OUT = sys.argv[1], sys.argv[2]; TITLE = sys.argv[3] if len(sys.argv) > 3 else ''
VMS = 1001 / 30
F = json.load(open(D + '/fight.json')); tr = F['truth']; P = F['page']; t0 = P['t0']; NV = len(tr)
def ts(vf): s = max(0, vf) * VMS / 1000; return '%d:%02d:%05.2f' % (s // 3600, s % 3600 // 60, s % 60)
vf = lambda t: round((t - t0) / VMS)
ev = []
for x in P['slog']:
    v = vf(x['t'])
    if x['ev'] == 'shine': ev.append((v, v + 15, 'Det', 'page: shine'))
    elif x['ev'] == 'lock': ev.append((v, v + 90, 'Lock', 'LOCKED %08x' % x['seed']))
    elif x['ev'] == 'unlock': ev.append((v, v + 60, 'Ev', 'page: unlocked (new segment)'))
    elif x['ev'] == 'plan': ev.append((v, vf(x['tPress']) + 2, 'Plan', 'beeps: %s, target frame %d, window %d' % (x['prof'], x['target'], x['window'])))
    elif x['ev'] == 'press': ev.append((v, v + 120, 'Press', 'page readout: %+.2f frames, %s' % (x['err'], 'working frame' if x['works'] else 'FAILING frame')))
    elif x['ev'] in ('turn', 'preConfirm', 'screenClosed', 'step', 'hudConfirm'):
        ev.append((v, v + 45, 'Ev', '%s %s' % (x['ev'], {k: w for k, w in x.items() if k not in ('t', 'ev')})))
for x in F['events']:
    if 'press' in x and x.get('step'): ev.append((x['step'], x['step'] + 120, 'Res', 'A pressed: %+d frames from the ideal frame' % (x['off_vs_ideal'] if x.get('off_vs_ideal') is not None else 99)))
    if 'confirm' in x: ev.append((x['step'], x['step'] + 45, 'Res', 'A: ' + x['confirm']))
    if 'result' in x or 'copies' in x:
        s = x.get('step') or 0
        txt = ('Duplighosts copied: %d of 4' % x['copies']) if 'copies' in x else ('%s Close Call: %s' % (x['result'], 'YES' if x.get('close_call') else 'no')) if 'close_call' in x else ('Power Bounce: Jr. Troopa HP %d (%s)' % (x['hp']['jr'], '6+ bounces' if x.get('six') else 'capped early'))
        ev.append((x.get('vf', 0), x.get('vf', 0) + 150, 'Lock', txt))
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 640
PlayResY: 480
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Det,DejaVu Sans,16,&H0000FF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,9,10,10,60,1
Style: Lock,DejaVu Sans,22,&H0000FF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,140,1
Style: Plan,DejaVu Sans,16,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,170,1
Style: Press,DejaVu Sans,16,&H00FFC0FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,195,1
Style: Res,DejaVu Sans,16,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,220,1
Style: Ev,DejaVu Sans,12,&H00FFC080,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,1,10,10,60,1
Style: Title,DejaVu Sans,13,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,1,10,10,12,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = ['Dialogue: 0,%s,%s,%s,,0,0,0,,%s' % (ts(a), ts(b), st, txt) for a, b, st, txt in sorted(ev)]
if TITLE: lines.append('Dialogue: 0,%s,%s,Title,,0,0,0,,%s' % (ts(0), ts(NV), TITLE))
open(D + '/ov.ass', 'w').write(hdr + '\n'.join(lines) + '\n')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'mjpeg', '-framerate', '30000/1001', '-i', D + '/run.mjpeg', '-vf', 'ass=' + D + '/ov.ass',
                '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', OUT], check=True)
print('wrote', OUT)
