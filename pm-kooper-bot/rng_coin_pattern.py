"""Record the status-bar coin pattern in the Hallway Bowser menu: for each coin draw, shine or not, and the number of
seed steps since the previous draw. Saves the true seed just before the first draw."""
import json
from emu import *
from pm import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cp')
e.load('states/boss_2302_menu.st'); e.step(0, 0, 0, 2)
draws = []; total = 0
for f in range(2400):
    prev = e.u32(SEED); e.step(0, 0, 0, 2); cur = e.u32(SEED)
    k = 0; x = prev
    while x != cur and k < 10: x = adv(x); k += 1
    if k == 2:                      # coin draw (first in the frame), then the frame step
        _, v = internal(prev, 1009)
        draws.append({'seed_before': prev, 'shine': int(v // 10 >= 70), 'steps_since_prev': total})
        total = 1                   # the frame step after the draw on this same frame
    else: total += k
print('draws', len(draws), 'pattern', ''.join('S' if d['shine'] else '.' for d in draws))
print('steps between draws after a normal spin:', sorted(set(d['steps_since_prev'] for i, d in enumerate(draws[1:]) if not draws[i]['shine'])),
      'after a shine:', sorted(set(d['steps_since_prev'] for i, d in enumerate(draws[1:]) if draws[i]['shine'])))
json.dump(draws, open('data/coin_pattern_2302.json', 'w'))
