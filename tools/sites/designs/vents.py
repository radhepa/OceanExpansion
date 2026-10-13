"""The Ember Vents: hydrothermal chimneys on the deep floor and a small Old Tide fire-shrine among them.
See DESIGN.md (vents)."""
import math

from kit import Template
from loot import item, empty, pool, rolls, trim, RANDOM_ENCHANT
from .nature_parts import (DIRS, SIDES, CORALS, add, coral_tuft, fbm, free, full, lichen, noise, on_top, rnd,
                           surfaces, wall_fan)

KEY = 'vents'
NAME = 'The Ember Vents'
FEATURES = [
    'a field of hydrothermal chimneys (10 to 19 blocks tall) of basalt, blackstone, tuff and glowing magma veins on '
    'the deep sea floor, flecked with gilded blackstone',
    'magma mouths drag the water down in whirling bubble columns; one old vent breathes out instead (a rising '
    'column where a diver can catch their breath)',
    'red tube worms, glow lichen and dead coral crowd around the chimneys',
    'an Old Tide fire-shrine: a dark prismarine and blackstone platform, broken columns, a great one-eyed carving '
    'whose pupil still burns, magma braziers, an altar chest of black pearls and offering pots',
    'deep lurkers rise when you come near the shrine; a glow squid drifts between the chimneys',
]
SITE = {'anchor': 'seabed', 'depth': (22, 60), 'flatness': 10, 'radius': 20,
        'biomes': ['deep_ocean', 'deep_lukewarm_ocean', 'deep_cold_ocean'], 'weight': 1, 'inhabited': False}


def _chim(name, at, turn=0):
    return {'piece': f'vents/{name}', 'at': at, 'turn': turn, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False}


LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'vents/field', 'at': (0, 0), 'y': -3, 'mode': 'rigid', 'soft': True},
        {'piece': 'vents/shrine', 'at': (-3, 4), 'turn': 0, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        _chim('chimney_tall', (9, -8)),
        _chim('chimney_twin', (-13, -9), 1),
        _chim('chimney_plume', (12, 9), 2),
        _chim('chimney_squat', (-15, 14), 3),
        _chim('spires', (1, -15)),
        _chim('spires', (17, -2), 2),
    ]},
    {'weight': 1, 'pieces': [
        {'piece': 'vents/field', 'at': (0, 0), 'turn': 1, 'y': -3, 'mode': 'rigid', 'soft': True},
        {'piece': 'vents/shrine', 'at': (4, -3), 'turn': 3, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        _chim('chimney_tall', (-9, 6), 2),
        _chim('chimney_twin', (11, 11), 0),
        _chim('chimney_plume', (-12, -10), 1),
        _chim('chimney_squat', (14, -14), 0),
        _chim('spires', (-1, 15), 1),
        _chim('spires', (-17, 2), 3),
    ]},
]
LOOT_TABLES = {
    # The altar: the prize. Black pearls for certain, and the Old Tide's offerings.
    'vents/shrine': [pool(1, [item('oceanexpansion:black_pearl', 1, 1, 2)]),
                     pool(rolls(2, 4), [item('gold_ingot', 5, 2, 5), item('gilded_blackstone', 3, 1, 3),
                                        item('prismarine_crystals', 3, 2, 6), item('emerald', 3, 1, 3),
                                        item('oceanexpansion:pearl', 3, 1, 3), item('magma_cream', 2, 1, 3),
                                        item('book', 1, extra=RANDOM_ENCHANT), empty(2)]),
                     pool(1, [trim('tide', 2), item('heart_of_the_sea', 1), empty(6)])],
    # Offering pots: embers and small gifts to the fire.
    'vents/cache': [pool(rolls(1, 3), [item('gold_nugget', 6, 3, 9), item('blaze_powder', 3, 1, 3), item('coal', 4, 2, 5),
                                       item('magma_cream', 2, 1, 2), item('prismarine_shard', 4, 2, 6),
                                       item('oceanexpansion:pearl', 2), item('fire_charge', 2, 1, 2), empty(3)]),
                    pool(1, [item('oceanexpansion:black_pearl', 1), empty(14)])],
}

SEED = 'vents'
CRUST = ('blackstone', 'basalt[axis=y]', 'smooth_basalt', 'tuff', 'blackstone', 'basalt[axis=y]')


def crust(x, y, z, seed):
    """The chimney's rind: mostly basalt and blackstone, patches of tuff, a fleck of gold, veins of magma."""
    vein = noise(x * 1.6, y * 0.45, z * 1.6, 2.2, seed + 'v')
    if vein > .74: return 'magma_block'
    n = fbm(x, y * 0.7, z, 3.5, seed + 'c')
    if rnd(x, y, z, seed) < .025: return 'gilded_blackstone'
    if n > .62: return 'tuff'
    if n > .52: return 'smooth_basalt'
    if n > .38: return 'basalt[axis=y]'
    return 'blackstone'


def chimney(t, cx, cz, height, r0, lean, seed, mouth='magma_block', flanges=(), base=2.2, spouts=(), hot_spout=False):
    """One irregular chimney rising from a crusted mound; returns the set of its cells. `spouts`: little side
    vents as (height, direction, length, rise)."""
    cells = set()
    sx, _, sz = t.size
    # the mound at its foot
    for y in range(0, 3):
        for x in range(sx):
            for z in range(sz):
                rb = r0 + base * (1 - y / 2.6) + (fbm(x, y, z, 3, seed + 'm') - .5) * 2.0
                if math.hypot(x - cx, z - cz) < rb:
                    b = crust(x, y, z, seed)
                    if y == 0 and rnd(x, 0, z, seed + 'g') < .3: b = 'gravel'
                    if b == 'magma_block' and y > 0 and rnd(x, y, z, 5) < .6: b = 'blackstone'
                    t.set(x, y, z, b); cells.add((x, y, z))
    # the stack itself, knobbly and leaning
    axis = []
    for y in range(1, height + 1):
        f = y / height
        ox = cx + lean[0] * f ** 1.5 + (noise(0, y, 0, 3, seed + 'w') - .5) * 1.0
        oz = cz + lean[1] * f ** 1.5 + (noise(5, y, 5, 3, seed + 'w') - .5) * 1.0
        axis.append((ox, y, oz))
        r = r0 * (1 - .5 * f) + .35
        for fy in flanges:
            if y == fy: r += 1.4
            elif y == fy + 1: r += .5
        for x in range(sx):
            for z in range(sz):
                d = math.hypot(x - ox, z - oz) + (fbm(x, y, z, 2.0, seed + 'r') - .5) * 1.4
                if d < r:
                    t.set(x, y, z, crust(x, y, z, seed)); cells.add((x, y, z))
    # little side vents
    hot = set()
    for (h, d, length, rise) in spouts:
        ox, _, oz = axis[min(h, height) - 1]
        dx, _, dz = DIRS[d]
        x, z = round(ox), round(oz)
        y = h
        for k in range(1, length + 1):
            x, z = x + dx, z + dz
            if t.inside(x, y, z): t.set(x, y, z, crust(x, y, z, seed)); cells.add((x, y, z))
        for k in range(1, rise + 1):
            tip = 'magma_block' if hot_spout else 'smooth_basalt'
            if t.inside(x, y + k, z): t.set(x, y + k, z, 'basalt[axis=y]' if k < rise else tip); cells.add((x, y + k, z))
        if hot_spout: hot.add((x, y + rise, z))
        hot_spout = False
    # the mouth: a rim of blackstone round a hot throat
    top = max(y for (_, y, _) in cells)
    tops = [(x, z) for (x, y, z) in cells if y == top]
    mx = round(sum(x for x, _ in tops) / len(tops)); mz = round(sum(z for _, z in tops) / len(tops))
    for (x, z) in tops:
        t.set(x, top, z, 'blackstone')
    # magma veins stay sealed under rock: only the throat (and one hot spout) opens to the sea, so the
    # whirling down-draughts stay few
    for c in sorted(cells):
        up = add(c, (0, 1, 0))
        if t.name_at(*c) == 'minecraft:magma_block' and c not in hot and (free(t, up) or not t.inside(*up)):
            t.set(*c, 'blackstone')
    t.set(mx, top, mz, mouth)
    if top + 1 < t.size[1]:   # a broken lip round the throat
        for d in SIDES:
            q = add((mx, top + 1, mz), DIRS[d])
            if t.inside(*q) and (q[0], top, q[2]) in cells and rnd(*q, seed) < .6:
                t.set(*q, 'blackstone'); cells.add(q)
    return cells


def grow(t, cells, rng, worms=.45, dead=.18, glow=.12):
    """Tube worms on the ledges, dead coral on the mound, glow lichen up the sides."""
    cells = sorted(c for c in cells if full(t, c))
    tops, sides, unders = surfaces(t, cells)
    for p in tops:
        below = t.name_at(*add(p, (0, -1, 0)))
        if below == 'minecraft:magma_block': continue          # nothing lives in the throat
        r = rng.random()
        near = fbm(*p, 3, 'worms') > .45
        if r < worms and near: on_top(t, p, 'oceanexpansion:tube_worms')
        elif r < worms + dead and p[1] <= 4: coral_tuft(t, p, rng, dead=True)
        elif r < worms + dead + .05 and p[1] <= 3: on_top(t, p, f'dead_{rng.choice(CORALS)}_coral_block')
    for p, f in sides:
        r = rng.random()
        if r < glow: lichen(t, p, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[f])
        elif r < glow + .04 and p[1] <= 5: wall_fan(t, p, f, rng.choice(CORALS), dead=True)


def chimney_piece(name, size, stacks, seed, squid=None):
    t = Template(f'vents/{name}', size, seed=seed, wet=True)
    cells = set()
    for s in stacks:
        cells |= chimney(t, seed=seed + str(len(cells)), **s)
    grow(t, cells, t.rng)
    if squid and free(t, squid): t.creature(*squid, 'minecraft:glow_squid', 'west')
    return t


def spires():
    """A huddle of young, thin vents: knobbly columns of basalt with worms round their feet."""
    t = Template('vents/spires', (7, 9, 7), seed='vents/spires', wet=True)
    rng = t.rng
    cells = set()
    for x in range(7):
        for z in range(7):
            if math.hypot(x - 3, z - 3) < 3.2 + (rnd(x, 0, z, 2) - .5):
                b = crust(x, 0, z, 'sp')
                t.set(x, 0, z, 'blackstone' if b == 'magma_block' else b); cells.add((x, 0, z))
    for (x, z, h) in ((3, 3, 8), (1, 4, 5), (4, 1, 6), (5, 5, 3), (2, 2, 3)):
        for y in range(1, h + 1):
            b = 'basalt[axis=y]' if rnd(x, y, z, 4) < .6 else 'blackstone'
            if y == h: b = 'magma_block' if h == 8 else 'smooth_basalt'
            t.set(x, y, z, b); cells.add((x, y, z))
            if y % 3 == 1 and y < h - 1:   # knobs
                d = rng.choice(SIDES)
                q = add((x, y, z), DIRS[d])
                if t.inside(*q) and free(t, q): t.set(*q, 'smooth_basalt'); cells.add(q)
    grow(t, cells, rng, worms=.6, dead=.2, glow=.2)
    return t


def field():
    """The stained floor round the vents (soft: only recolours the ground): basalt, tuff, blackstone, gravel and a
    few glowing cracks."""
    t = Template('vents/field', (40, 5, 40), seed='vents/field')
    for x in range(40):
        for z in range(40):
            e = math.hypot(x - 19.5, z - 19.5) / 19.5 + (fbm(x, 0, z, 6, 'fe') - .5) * .5
            if e > 1: continue
            n = fbm(x, 0, z, 4, 'fn')
            if e > .7 and n < .45: continue
            if n > .66: b = 'blackstone'
            elif n > .58: b = 'basalt[axis=y]'
            elif n > .5: b = 'tuff'
            elif n > .42: b = 'gravel'
            elif n > .36: b = 'smooth_basalt'
            else: b = 'gravel' if e > .5 else 'blackstone'
            for y in range(5):
                t.set(x, y, z, b)
    for (x, z) in ((17, 21), (18, 21), (18, 22), (25, 14), (26, 14)):   # two short glowing cracks
        for y in range(2, 5):
            t.set(x, y, z, 'magma_block')
    return t


# -- the shrine ------------------------------------------------------------------------------------------------
EYE = [            # the carving on the back wall, seen from the front: P lid, M ember iris, G the burning pupil
    '..PPPPP..',
    '.PMMMMMP.',
    'PMMMGMMMP',
    '.PMMMMMP.',
    '..PPPPP..',
]


def shrine():
    """An Old Tide fire-shrine: front is south (high z), the eye wall is at the back (low z)."""
    t = Template('vents/shrine', (13, 10, 13), seed='vents/shrine', wet=True)
    rng = t.rng
    # foundation and platform: blackstone below, dark prismarine floor, broken at the edges
    for x in range(13):
        for z in range(13):
            edge = min(x, z, 12 - x, 12 - z)
            if edge == 0 and rnd(x, 0, z, 'sh') < .35: continue
            t.set(x, 0, z, 'polished_blackstone_bricks' if rnd(x, 1, z, 'sh') < .7 else 'cracked_polished_blackstone_bricks')
            if edge >= 1:
                t.set(x, 1, z, 'dark_prismarine' if edge >= 2 else 'polished_blackstone_bricks')
                if edge >= 2 and rnd(x, 2, z, 'sh') < .12: t.set(x, 1, z, 'prismarine_bricks')
    for x in range(4, 9):   # the front steps
        t.set(x, 1, 12, 'polished_blackstone_brick_stairs[facing=north,half=bottom,shape=straight]')
    # the eye wall: three thick, blackstone with dark prismarine courses
    for x in range(1, 12):
        for y in range(1, 9):
            if y >= 7 and (x <= 2 or x >= 10): continue          # stepped shoulders
            if y == 8 and (x <= 3 or x >= 9): continue
            for z in range(1, 4):
                b = 'dark_prismarine' if y in (1, 6) else 'polished_blackstone_bricks'
                if rnd(x, y, z, 'w') < .08: b = 'cracked_polished_blackstone_bricks'
                t.set(x, y, z, b)
    for x in (4, 6, 8):
        t.set(x, 9, 2, 'dark_prismarine_slab[type=bottom]')
    t.set(6, 9, 1, 'dark_prismarine')
    for r, row in enumerate(EYE):       # the carving on the wall's face (z = 3)
        y = 6 - r
        for i, ch in enumerate(row):
            x = 2 + i
            if ch == 'P': t.set(x, y, 3, 'prismarine_bricks')
            elif ch == 'M': t.set(x, y, 3, 'magma_block')
            elif ch == 'G': t.set(x, y, 3, 'glass')
    # behind the pupil, sealed in the wall: the fire that never went out
    t.set(6, 4, 2, 'campfire[facing=south,lit=true,signal_fire=false]')
    t.keep_dry((6, 4, 2), (6, 4, 2))
    # columns: two standing, one broken, one fallen across the floor
    for (x, z, h) in ((1, 6, 6), (11, 6, 7), (1, 10, 3), (11, 10, 0)):
        if not h: continue
        for y in range(2, 2 + h):
            t.set(x, y, z, 'prismarine_bricks' if y % 3 == 1 else 'dark_prismarine')
        t.set(x, 2 + h, z, 'chiseled_polished_blackstone' if h > 4 else 'dark_prismarine_slab[type=bottom]')
    t.set(11, 2, 10, 'polished_blackstone_bricks')
    for z in (7, 8, 9):                                    # the fallen one, broken in drums
        t.set(9, 2, z, 'dark_prismarine' if z != 8 else 'prismarine_bricks')
    t.set(8, 2, 11, 'chiseled_polished_blackstone')
    # a lintel once ran from the wall to the columns
    for z in (4, 5):
        t.set(1, 7, z, 'dark_prismarine_slab[type=top]')
    t.set(11, 9, 6, 'dark_prismarine_slab[type=bottom]')
    t.set(11, 9, 5, 'dark_prismarine_slab[type=bottom]')
    # the altar before the eye, the offering chest on it, embers in grated braziers either side
    for x in range(4, 9):
        t.set(x, 2, 6, 'polished_blackstone_bricks')
        if x in (4, 8): t.set(x, 2, 7, 'polished_blackstone_brick_stairs[facing=north,half=bottom,shape=straight]')
    t.set(5, 3, 6, 'dark_prismarine_slab[type=bottom]'); t.set(7, 3, 6, 'dark_prismarine_slab[type=bottom]')
    t.chest(6, 3, 6, 'south', 'vents/shrine')
    for x in (3, 9):
        t.set(x, 2, 5, 'polished_blackstone_wall')
        t.set(x, 3, 5, 'magma_block')
        t.set(x, 4, 5, 'oxidized_copper_grate')
    # offering niches with pots in the wall's foot and by the columns
    t.pot(2, 2, 4, 'south', loot='vents/cache', sherds=['brick', 'brick', 'brick', 'brick'])
    t.pot(10, 2, 4, 'south', loot='vents/cache')
    t.pot(2, 2, 9, 'east', loot='vents/cache')
    # Tobin got this far
    t.sign(10, 2, 11, ['Tobin, pearl', 'diver, came for', 'the black ones.', 'The eye burns.'], 'south',
           wood='dark_oak', wall=False)
    t.set(9, 2, 11, 'skeleton_skull[rotation=10]')
    t.haunt(6, 2, 9, 'deep_lurkers')
    # the deep's life creeps over it
    cells = [p for p in list(t.blocks) if full(t, p)]
    tops, sides, unders = surfaces(t, cells)
    for p in tops:
        if t.name_at(*add(p, (0, -1, 0))) == 'minecraft:magma_block': continue
        if p == (6, 3, 9) or p == (6, 4, 9): continue
        r = rng.random()
        if p[1] <= 2 and (p[0] in (0, 12) or p[2] in (0, 12)) and r < .5: on_top(t, p, 'oceanexpansion:tube_worms')
        elif r < .08: on_top(t, p, 'oceanexpansion:tube_worms')
        elif r < .14: coral_tuft(t, p, rng, dead=True)
    for p, f in sides:
        if rng.random() < .1: lichen(t, p, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[f])
    t.creature(6, 7, 9, 'minecraft:glow_squid', 'north')
    t.entrance(6, 2, 12)
    return t


def pieces():
    return [
        field(),
        shrine(),
        chimney_piece('chimney_tall', (13, 20, 13), [
            dict(cx=6, cz=6, height=19, r0=2.1, lean=(1.6, -1.2), flanges=(7, 13),
                 spouts=((5, 'west', 2, 3), (10, 'south', 2, 2)), hot_spout=True)], 'vents-tall', squid=(1, 12, 10)),
        chimney_piece('chimney_twin', (15, 17, 13), [
            dict(cx=5, cz=6, height=16, r0=1.9, lean=(-1.2, 0.9), flanges=(9,), spouts=((6, 'north', 2, 2),)),
            dict(cx=10, cz=7, height=11, r0=1.6, lean=(1.4, 0.4), flanges=(5,), base=1.2)], 'vents-twin'),
        chimney_piece('chimney_plume', (11, 16, 11), [
            dict(cx=5, cz=5, height=14, r0=1.9, lean=(0.6, 1.0), flanges=(8,), mouth='soul_sand',
                 spouts=((4, 'east', 2, 2),))], 'vents-plume'),
        chimney_piece('chimney_squat', (13, 12, 13), [
            dict(cx=6, cz=6, height=8, r0=2.8, lean=(0.4, 0.3), flanges=(4,), base=2.6),
            dict(cx=4, cz=8, height=11, r0=1.2, lean=(-0.8, 0.6), base=0.4, mouth='smooth_basalt'),
            dict(cx=9, cz=5, height=10, r0=1.1, lean=(0.9, -0.5), base=0.4, mouth='smooth_basalt')], 'vents-squat'),
        spires(),
    ]
