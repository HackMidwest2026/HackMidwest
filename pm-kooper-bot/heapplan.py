"""Offline what-if planning on a heaplog.py capture: rebuild the start heap, replay the (edited) event list in
heapsim, and report where the APG menu (malloc 0x330) lands and which simulated allocation last covered
menu+0x100 (the stale effect instance whose part count becomes the partner id).
Effect creation = instance malloc 0x14 (create_effect_instance) followed by its data malloc (size by effect):
walking dust 0x78 (1 part), landing dust 0xCC (3 parts), sparkle 0xDC (5 parts)."""
import json
from heapsim import Heap, apply_event, MALLOC, FREE

def load(path):
    d = json.load(open(path))
    nodes = {int(k, 16): v for k, v in d['start_nodes'].items()}
    return nodes, d['events']

PARTS = {0x78: 1, 0xCC: 3, 0xDC: 5, 0x38: 1}
def tag_effects(events):
    """label effect instance mallocs with the part count implied by the data malloc that follows"""
    for i, j, sz in effect_pairs(events):
        events[i]['tag'] = 'fx%d' % PARTS.get(sz, -1) if sz in PARTS else 'fx?%x' % sz
    return events

def _apply(h, ev, remap):
    """apply with identity tracking: frees/reallocs of an originally-returned address go to where that
    allocation lives in this (edited) replay"""
    if ev['pc'] in (FREE,) or ev['pc'] == 0x80029284:
        ev = dict(ev, a1=remap.get(ev['a1'], ev['a1']))
    r = apply_event(h, ev)
    if r is not None and 'sim_ret' in ev:
        remap[ev['sim_ret']] = r
    return r

def run(nodes, events):
    h = Heap(nodes, 0x802FB800, 0)
    res = {}; remap = {}
    for i, ev in enumerate(events):
        if ev['pc'] == MALLOC and ev['a1'] == 0x330:
            # where will it go, and what stale allocation covers its +0x108 at that moment
            probe = Heap(h.n, h.head, h.next_id)
            m = probe.malloc(0x330)
            res['menu'] = m
            own = h.owner_at(m + 0x108)
            if own:
                blk, ln, oev = own
                res['id_owner'] = (hex(blk), oev.get('tag', ''), 'size', hex(oev['a1']), 'step', oev.get('step'), 'off', hex(m + 0x108 - blk))
            _apply(h, ev, remap)
            break
        _apply(h, ev, remap)
    return res, h

def effect_pairs(events):
    """indices (inst_idx, data_idx, data_size) of effect creations: malloc 0x14 followed by the next malloc"""
    out = []
    for i, ev in enumerate(events):
        if ev['pc'] == MALLOC and ev['a1'] == 0x14:
            for j in range(i + 1, min(i + 4, len(events))):
                if events[j]['pc'] == MALLOC:
                    out.append((i, j, events[j]['a1'])); break
    return out
