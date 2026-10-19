"""kpa_62 tower outline (collider 1) used as the clip goal."""
TOWER = [(-365, -5), (-394, -29), (-409, -55), (-414, -75), (-415, -96), (-408, -108), (-390, -112), (-376, -103),
         (-357, -79), (-341, -48), (-340, -20), (-348, -4)]
def inside_tower(x, z, poly=TOWER):
    c = False
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0): c = not c
    return c
