"""Inline the shared sources into a page template: each line /*@include shared/NAME*/ is replaced by that file's text,
minus its //@ header lines. Used by build_page.py (Time Out Timer) and powerbounce/build_hpbm.py (High Power Bounce
Manipulator), so both pages run the same capture, coin-detector and beep code."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def shared(name):
    s = open(os.path.join(ROOT, name)).read()
    return ''.join(l for l in s.splitlines(True) if not l.startswith('//@'))
def inline(t):
    out = re.sub(r'^/\*@include (shared/[\w.]+)\*/\n', lambda m: shared(m.group(1)), t, flags=re.M)
    assert '@include' not in out, 'unresolved include'
    return out
