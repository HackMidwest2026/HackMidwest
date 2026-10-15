"""per-room settings for the clip searches (explore_clip.py, corner_sweep.py).

pick one with the ROOM environment variable (default nok14)."""
import os

ROOMS = {
    # Pleasant Path, Kooper skip room: get past the bridge wall at x = -100
    'nok14': {
        'collision': 'nok14_collision.json',
        'start': 'states/nok14_start_goombario.st',
        'start_pos': {'x': -855.0, 'y': 75.0, 'z': -35.0, 'action': 0, 'floor': 2},
        'map': (6, 7),
        'goal_floors': [14],
        'goal_maps': [(6, 8)],           # nok_15
        'goal_box': (-100.0, 1e9, -100.0, -20.0),   # x_min, x_max, z_min, z_max
        'focus_min_x': -480,
        'corners': {
            'north': {'p': (-100.0, -100.0), 'wedge': None, 'walls': ((-110.0, -102.0), (-100.0, -20.0))},
            # the same corner approached from every in-bounds side: the corridor (west/south-west) and the grass
            # behind the fence (north-west/north); start points off the floor are skipped
            'north_all': {'p': (-100.0, -100.0), 'wedge': (90.0, 340.0)},
            'south': {'p': (-100.0, -20.0), 'wedge': None, 'walls': ((-100.0, -100.0), (-127.0, 32.0))},
            # points along the thin diagonal wall (-110,-102)-(-52,-118) between the north lobe and the gap,
            # approached from the lobe (north) side
            'lobe1': {'p': (-104.2, -103.6), 'wedge': (164.3, 344.3)},
            'lobe2': {'p': (-92.6, -106.8), 'wedge': (164.3, 344.3)},
            'lobe3': {'p': (-81.0, -110.0), 'wedge': (164.3, 344.3)},
            'lobe4': {'p': (-69.4, -113.2), 'wedge': (164.3, 344.3)},
            'lobe5': {'p': (-57.8, -116.4), 'wedge': (164.3, 344.3)},
        },
        'floor_y': lambda x, z: 0.0,
        'disable_enemy_contact': True,
    },
    # Toad Town Tunnels, Rip Cheato's room: get past the bombable wall at x = -250 (|z| < 50)
    'tik15': {
        'collision': 'tik15_collision.json',
        'start': 'states/tik15_start.st',
        'start_pos': {'x': -230.0, 'y': -10.0, 'z': 0.0, 'action': 0, 'floor': 0},
        'map': (2, 12),
        'goal_floors': [12],
        'goal_maps': [(2, 11)],          # tik_14, behind the bombable wall (not the pipe up to toad town)
        'goal_box': (-1e9, -250.0, -50.0, 50.0),
        'focus_min_x': -1e9,
        'corners': {
            # where the bombable wall meets the rest of the west wall (same plane: a seam), approached from the room
            'seam_north': {'p': (-250.0, -50.0), 'wedge': (-90.0, 90.0)},
            'seam_south': {'p': (-250.0, 50.0), 'wedge': (-90.0, 90.0)},
            # outer corners of the low ledges beside the bombable wall
            'ledge_north': {'p': (-230.0, -50.0), 'wedge': (-90.0, 180.0)},
            'ledge_south': {'p': (-230.0, 50.0), 'wedge': (-180.0, 90.0)},
        },
        'floor_y': lambda x, z: 10.0 if (-250 < x < -230 and abs(z) > 50) else -10.0,
        'disable_enemy_contact': False,
    },
}

NAME = os.environ.get('ROOM', 'nok14')
ROOM = ROOMS[NAME]


def in_goal(x, z):
    x0, x1, z0, z1 = ROOM['goal_box']
    return x0 < x < x1 and z0 < z < z1
