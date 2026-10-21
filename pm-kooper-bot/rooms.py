"""per-room settings for the clip searches (explore_clip.py, corner_sweep.py).

pick one with the ROOM environment variable (default nok14)."""
import os

ROOMS = {
    # kmr_11 right after the Goomba King, the trapped arena on the left: its low pocket (y -8) has an acute corner at
    # about (-227, 48.5) where the Bush2 wall (collider 12) meets the arena's south-east wall (22). Behind the bush
    # wall (north of the bush, east of its west tip (-309, 19); the corridor there is 1.4 units too narrow for Mario) is a strip along the fortress whose east edge is open void.
    'kmr11bush2': {
        'collision': 'kmr11_collision.json',
        'start': 'states/kmr11_e0_kingdone.st',
        'start_pos': {'x': -300.0, 'y': -8.0, 'z': 100.0, 'action': 0, 'floor': 17},
        'map': (0, 9),
        'goal_floors': [],
        'goal_maps': [],
        'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: _kmr11_behind_bush2(x, z),
        'focus_min_x': -1e9,
        'focus_box': (-420.0, -150.0, -60.0, 210.0),
        'corners': {
            'corner': {'p': (-227.1, 48.5), 'wedge': (141.0, 196.0)},
            # bush points, approached from the arena side (south, +z): angle = atan2(dz, dx) from the point
            'bush_e': {'p': (-246.0, 43.0), 'wedge': (17.0, 163.0)},
            'bush_m': {'p': (-272.0, 36.0), 'wedge': (20.0, 160.0)},
            'bush_w': {'p': (-309.0, 19.0), 'wedge': (25.0, 200.0)},
            'wall_end': {'p': (-213.0, 37.5), 'wedge': (141.0, 191.0)},
            # the 1.4-unit-too-narrow gap between the fortress south face and the bush's west tip
            'gap': {'p': (-309.0, 7.0), 'wedge': (90.0, 225.0)},
        },
        'floor_y': lambda x, z: -8.0 if z > 25 else 0.0,
        'disable_enemy_contact': True,
    },
    # Goomba King's castle grounds (kmr_11) after the Goomba King: the fence of one-sided walls by the right-side bush
    # (colliders 13 + 29, polyline (290,-225) (373,-210) (457,-210) (509,-200) (587,-218)). Goal: south of it.
    'kmr11fence': {
        'collision': 'kmr11_collision.json',
        'start': 'states/kmr11_e0_kingdone.st',
        'start_pos': {'x': 420.0, 'y': 0.0, 'z': -250.0, 'action': 0, 'floor': 31},
        'map': (0, 9),
        'goal_floors': [],
        'goal_maps': [],
        'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: _kmr11_south(x, z),
        'focus_min_x': -1e9,
        'focus_box': (270.0, 600.0, -330.0, -190.0),
        'corners': {
            'w_end': {'p': (290.0, -225.0), 'wedge': (190.0, 350.0)},
            'bush_w': {'p': (373.0, -210.0), 'wedge': (190.0, 350.0)},
            'bush_mid': {'p': (415.0, -210.0), 'wedge': (190.0, 350.0)},
            'bush_e': {'p': (457.0, -210.0), 'wedge': (190.0, 350.0)},
            'kink': {'p': (509.0, -200.0), 'wedge': (190.0, 350.0)},
            'e_end': {'p': (587.0, -218.0), 'wedge': (190.0, 350.0)},
        },
        'floor_y': lambda x, z: 0.0,
        'disable_enemy_contact': True,
    },
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
    # Kooper skip room, front-left corner of the top level (y 75, near the five coins): get through the front wall
    # (-870,0)-(-848,18)-(-743,59)-(-695,48) onto the out-of-bounds part of floor collider 2 in front of it
    'nok14fl': {
        'collision': 'nok14_collision.json',
        'start': 'states/nok14_start_goombario.st',
        'start_pos': {'x': -855.0, 'y': 75.0, 'z': -35.0, 'action': 0, 'floor': 2},
        'map': (6, 7),
        'goal_floors': [],
        'goal_maps': [],
        'goal_box': (1e9, -1e9, 1e9, -1e9),   # unused (goal_fn)
        'goal_fn': lambda x, z: _past_front_wall(x, z),
        'focus_min_x': -1e9,
        'focus_box': (-875.0, -660.0, -80.0, 75.0),
        'corners': {
            'c1': {'p': (-848.0, 18.0), 'wedge': (219.3, 381.3)},
            'c2': {'p': (-743.0, 59.0), 'wedge': (201.3, 347.1)},
            'c3': {'p': (-695.0, 48.0), 'wedge': (167.1, 360.0)},
        },
        'floor_y': lambda x, z: 75.0,
        'disable_enemy_contact': True,
    },
    # Bowser's Castle jail cell (kpa_17): get out through the bombable doorway (x = 1200, z -600..-550) onto the
    # exit floor (collider 14), or anywhere outside the cell walls (x 750..1200, z -650..-350)
    'kpa17': {
        'collision': 'kpa17_collision.json',
        'start': 'states/kpa17_e1.st',
        'start_pos': {'x': 1168.0, 'y': 30.0, 'z': -560.0, 'action': 0, 'floor': 4},
        'map': (22, 12),
        'goal_floors': [14],
        'goal_maps': [],
        'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: x > 1200.5 or x < 749.5 or z < -650.5 or z > -349.5,
        'focus_min_x': -1e9,
        'corners': {
            'door_n': {'p': (1200.0, -600.0), 'wedge': (90.0, 270.0)},
            'door_s': {'p': (1200.0, -550.0), 'wedge': (90.0, 270.0)},
            'ne': {'p': (1200.0, -650.0), 'wedge': (90.0, 180.0)},
        },
        'floor_y': lambda x, z: 30.0,
        'disable_enemy_contact': True,
    },
    # Bowser's Castle flood room (left, kpa_133). Key at (-350, 215, -50) on the top-left back ledge (y 215).
    # Water level 0 (kpa133w0): Mario on the front floor y 0. Water level 2, under the water (kpa133w2u): Mario at
    # y 0 below the y-200 water surface. Goal: out of the room, behind the back blocks' front faces, or up to y >= 100.
    'kpa133w0': {
        'collision': 'kpa133_w0_collision.json',
        'start': 'states/kpa133_e0_w0.st',
        'start_pos': {'x': -347.0, 'y': 0.0, 'z': 115.0, 'action': 0, 'floor': 6},
        'map': (22, 48), 'goal_floors': [], 'goal_maps': [], 'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: z > 205.5 or (abs(x) > 400.5 and not (75 < z < 160)),
        'goal_fn3': lambda x, y, z: y >= 100 or z < -100.5,
        'focus_min_x': -1e9, 'cdown': True, 'corners': {},
        'floor_y': lambda x, z: 0.0, 'disable_enemy_contact': True,
    },
    'kpa133w1u': {
        'collision': 'kpa133_w1_collision.json',
        'start': 'states/kpa133_e0_w1.st',
        'start_pos': {'x': -347.0, 'y': 0.0, 'z': 115.0, 'action': 0, 'floor': 6},
        'map': (22, 48), 'goal_floors': [], 'goal_maps': [], 'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: z > 205.5 or (abs(x) > 400.5 and not (75 < z < 160)),
        'goal_fn3': lambda x, y, z: y >= 100 or z < -100.5,
        'focus_min_x': -1e9, 'cdown': True, 'corners': {},
        'floor_y': lambda x, z: 0.0, 'disable_enemy_contact': True,
    },
    'kpa133w2u': {
        'collision': 'kpa133_w2_collision.json',
        'start': 'states/kpa133_e0_w2.st',
        'start_pos': {'x': -347.0, 'y': 0.0, 'z': 115.0, 'action': 0, 'floor': 6},
        'map': (22, 48), 'goal_floors': [], 'goal_maps': [], 'goal_box': (1e9, -1e9, 1e9, -1e9),
        'goal_fn': lambda x, z: z > 205.5 or (abs(x) > 400.5 and not (75 < z < 160)),
        'goal_fn3': lambda x, y, z: y >= 100 or z < -100.5,
        'focus_min_x': -1e9, 'cdown': True, 'corners': {},
        'floor_y': lambda x, z: 0.0, 'disable_enemy_contact': True,
    },
    # Outside Bowser's Castle (kpa_62): Laki dismount / hold down / remount teleport into a wall
    'kpa62': {
        'collision': 'kpa62_collision.json',
        'start': 'states/kpa62_e0.st',
        'start_pos': {'x': -191.0, 'y': 0.0, 'z': -95.0, 'action': 0, 'floor': 6},
        'map': (22, 23), 'goal_floors': [11, 41], 'goal_maps': [], 'goal_box': (1e9, -1e9, 1e9, -1e9),
        'focus_min_x': -1e9, 'cdown': True, 'corners': {},
        'floor_y': lambda x, z: 0.0, 'disable_enemy_contact': True,
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

FRONT_WALL = [(-870.0, 0.0), (-848.0, 18.0), (-743.0, 59.0), (-695.0, 48.0)]


_KMR11_FENCE = [(290, -225), (373, -210), (457, -210), (509, -200), (587, -218)]
def _kmr11_south(x, z):
    for (x0, z0), (x1, z1) in zip(_KMR11_FENCE, _KMR11_FENCE[1:]):
        if x0 <= x <= x1:
            return z > z0 + (z1 - z0) * (x - x0) / (x1 - x0) + 1.0
    return False


_KMR11_BUSH2 = [(-309, 19), (-272, 36), (-246, 43), (-222, 50)]
def _kmr11_behind_bush2(x, z):
    if x > -205 and z > -45: return True               # over the open void east of the strip
    for (x0, z0), (x1, z1) in zip(_KMR11_BUSH2, _KMR11_BUSH2[1:]):
        if x0 <= x <= x1:
            return z < z0 + (z1 - z0) * (x - x0) / (x1 - x0) - 1.0 and z > -45
    return False


def _past_front_wall(x, z):
    """in front of (larger z than) the nok_14 top-level front wall polyline, between its ends, by more than 1 unit"""
    if not (FRONT_WALL[0][0] < x < FRONT_WALL[-1][0]):
        return False
    for (x0, z0), (x1, z1) in zip(FRONT_WALL, FRONT_WALL[1:]):
        if x0 <= x <= x1:
            return z > z0 + (z1 - z0) * (x - x0) / (x1 - x0) + 1.0
    return False


NAME = os.environ.get('ROOM', 'nok14')
ROOM = ROOMS[NAME]


def in_goal(x, z):
    if 'goal_fn' in ROOM:
        return ROOM['goal_fn'](x, z)
    x0, x1, z0, z1 = ROOM['goal_box']
    return x0 < x < x1 and z0 < z < z1
