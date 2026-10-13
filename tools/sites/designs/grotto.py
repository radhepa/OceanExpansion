"""The Pearl Grotto: a domed sea cave beside a reef, giant clams on its sandy floor and the pearl divers' old
camp in a dry air pocket up in the dome. See DESIGN.md (grotto)."""
import math

from kit import Template
from loot import item, empty, pool, rolls, sea_chart, named
from .nature_parts import (CORALS, DIRS, SIDES, add, barnacles, coral_tuft, fbm, free, full, kelp, lichen, noise,
                           pickle, rnd, seagrass, surfaces, tropical_fish, wall_fan)

KEY = 'grotto'
NAME = 'The Pearl Grotto'
FEATURES = [
    'a domed sea cave half sunk into the floor, lined with glow lichen and sea-glass crystals, entered by a tunnel '
    'from a coral reef',
    'giant clams with pearls on a sandy floor, sea pickles everywhere, coral and swaying kelp',
    "the pearl divers' camp up in a dry air pocket in the dome: plank ledge, bed, lantern, a tally of pearls and "
    'the Pearling Book; swim up through the hole in the ledge to breathe',
    "the divers' hoard, buried under the sand where three little lights sit in a row",
]
SITE = {'anchor': 'seabed', 'depth': (6, 25), 'flatness': 8, 'radius': 20,
        'biomes': ['warm_ocean', 'lukewarm_ocean', 'ocean'], 'weight': 2, 'inhabited': False}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'grotto/cave', 'at': (0, 0), 'y': -9, 'mode': 'rigid', 'soft': False},
        {'piece': 'grotto/reef_a', 'at': (-8, -19), 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        {'piece': 'grotto/reef_b', 'at': (8, -18), 'turn': 1, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        {'piece': 'grotto/reef_b', 'at': (-17, 5), 'turn': 2, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
    ]},
    {'weight': 1, 'pieces': [
        {'piece': 'grotto/cave', 'at': (0, 0), 'y': -9, 'mode': 'rigid', 'soft': False},
        {'piece': 'grotto/reef_b', 'at': (-7, -18), 'turn': 3, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        {'piece': 'grotto/reef_a', 'at': (9, -19), 'turn': 2, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
        {'piece': 'grotto/reef_a', 'at': (17, 6), 'turn': 1, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
    ]},
]
WATER_BREATHING = [{'type': 'minecraft:set_potion', 'id': 'minecraft:water_breathing'}]
LOOT_TABLES = {
    # The divers' buried hoard: the prize. Pearls for certain, a black pearl now and then.
    'grotto/hoard': [pool(1, [item('oceanexpansion:pearl', 1, 3, 7)]),
                     pool(1, [item('oceanexpansion:black_pearl', 1), empty(3)]),
                     pool(rolls(2, 4), [item('gold_ingot', 4, 1, 3), item('gold_nugget', 5, 3, 9), item('emerald', 3, 1, 3),
                                        item('nautilus_shell', 1), item('prismarine_crystals', 2, 2, 5), empty(2)]),
                     pool(1, [sea_chart(1), empty(3)])],
    # The camp barrel: a pearl diver's gear and a little food.
    'grotto/camp': [pool(rolls(3, 5), [item('dried_kelp', 6, 3, 8), item('cooked_cod', 4, 1, 3), item('bread', 3, 1, 2),
                                       item('string', 3, 2, 4), item('lead', 2), item('glass_bottle', 2, 1, 3),
                                       item('candle', 2, 1, 3), item('shears', 1, extra=named('Pearling Knife')),
                                       item('potion', 2, extra=WATER_BREATHING), empty(2)]),
                    pool(1, [item('oceanexpansion:pearl', 2, 1, 2), item('turtle_scute', 1), empty(3)])],
}

S, SY = 31, 15          # the cave piece: 31 x 15 x 31
C = 15                  # its centre (x and z)
SEABED = 8              # template y of the sea floor's top layer at the centre (rigid, y -9)
CAVE_FLOOR = 2          # sand; the cave's water starts a block above
CAMP_Y = 9              # the camp's floor of air (its plank ledge is a block lower, level with the sea floor)
CAMP = [(x, y, z) for x in range(12, 18) for z in range(24, 28) for y in range(CAMP_Y, CAMP_Y + 3)
        if not (y == CAMP_Y + 2 and x in (12, 17) and z in (24, 27))]
POOL = {(13, 24), (14, 24)}   # the hole in the ledge you come up through
HOARD = (8, CAVE_FLOOR - 1, 13)
SEED = 'grotto'


def cavity(x, y, z):
    if y <= CAVE_FLOOR: return False
    r = math.hypot(x - C, z - C)
    reach = 10.6 * (0.88 + 0.22 * fbm(x, y * 1.4, z, 5, SEED))
    return (r / reach) ** 2.2 + ((y - CAVE_FLOOR) / 9.2) ** 2 < 1


def tunnel(x, y, z):
    """The way in: from the reef (north, low z) through the porch and down into the cave."""
    path = [(15.0, 10.3, -1.0), (15.0, 10.0, 3.0), (15.3, 8.6, 6.0), (15.0, 6.5, 8.5)]
    best = 99
    for a, b in zip(path, path[1:]):
        ab = [b[i] - a[i] for i in range(3)]
        ap = [(x, y, z)[i] - a[i] for i in range(3)]
        tt = max(0.0, min(1.0, sum(ab[i] * ap[i] for i in range(3)) / sum(v * v for v in ab)))
        d = math.sqrt(sum((ap[i] - ab[i] * tt) ** 2 for i in range(3)))
        best = min(best, d)
    mouth = max(0.0, min(1.0, 1 - z / 7.0))
    return best < 1.5 + 0.55 * mouth + 0.35 * noise(x, y, z, 2.5, 3)


def mound(x, y, z):
    """The rock rising above the sea floor: the dome, the porch over the entrance and the hump over the camp."""
    if y <= SEABED or y >= SY - 1: return False
    r = math.hypot(x - C, z - C)
    ro = 11.8 * (0.92 + 0.16 * fbm(x, 0, z, 6, SEED + 'o'))
    rise = 5.8 * math.sqrt(max(0.0, 1 - (r / ro) ** 2.4)) + (fbm(x, 0, z, 3, SEED + 'b') - .5) * 1.2
    if y - SEABED < rise: return True
    if ((x - 15) / 4.8) ** 2 + ((y - SEABED) / 4.7) ** 2 + ((z - 3.6) / 4.4) ** 2 < 1: return True
    if ((x - 14.5) / 6.6) ** 2 + ((y - SEABED) / 5.4) ** 2 + ((z - 25.3) / 4.8) ** 2 < 1: return True
    return False


def rock(x, y, z, inner=False):
    n = fbm(x, y * 1.6, z, 6, SEED + 'r')
    m = noise(x, y, z, 3, 17)
    if inner and m > .62: return 'calcite'
    if n > .62: return 'diorite' if m > .5 else 'calcite'
    if n > .45: return 'andesite'
    if n > .38 and m > .6: return 'tuff'
    return 'stone'


def cave():
    t = Template('grotto/cave', (S, SY, S), seed=SEED, wet=True)
    rng = t.rng
    camp = set(CAMP)
    water, mounded = set(), set()
    for x in range(S):
        for z in range(S):
            for y in range(SY):
                if mound(x, y, z): mounded.add((x, y, z))
                if (x, y, z) in camp: continue
                if cavity(x, y, z) or tunnel(x, y, z): water.add((x, y, z))
    # the rock: a lining round the cave (two blocks), the floor under it and the mound above the sea floor
    solid = set()
    for (x, y, z) in water:
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    p = (x + dx, y + dy, z + dz)
                    if t.inside(*p) and p not in water and (p[1] <= SEABED or p in mounded
                                                            or max(abs(dx), abs(dy), abs(dz)) <= 1): solid.add(p)
    solid |= mounded - water
    for x in range(S):
        for z in range(S):
            if any((x + dx, CAVE_FLOOR + 1, z + dz) in water for dx in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2)):
                solid.add((x, 0, z))
    # a skirt of rock under the mound's edge, so it never hangs over a dip in the sea floor
    for x in range(S):
        for z in range(S):
            if (x, SEABED + 1, z) in mounded:
                for y in range(3, SEABED + 1):
                    if (x, y, z) not in water: solid.add((x, y, z))
    # the camp's walls, roof and floor: closed above and at the sides, open below only through the hole
    for c in camp:
        for d in ('north', 'south', 'east', 'west', 'up'):
            n = add(c, DIRS[d])
            if n not in camp:
                water.discard(n); solid.add(n)
        below = add(c, DIRS['down'])
        if below not in camp and (below[0], below[2]) not in POOL:
            water.discard(below); solid.add(below)
    for (x, z) in POOL:                       # the shaft up from the cave
        for y in range(4, CAMP_Y):
            water.add((x, y, z)); solid.discard((x, y, z))
        for y in range(4, 7):
            for zz in (z - 2, z - 1):
                water.add((x, y, zz)); solid.discard((x, y, zz))
    for p in sorted(solid):
        near = any(add(p, DIRS[d]) in water for d in DIRS)
        t.set(*p, rock(*p, inner=near))
    for p in water: t.set(*p, 'water')
    for p in camp: t.set(*p, 'air')
    t.keep_dry((12, CAMP_Y, 24), (17, CAMP_Y + 2, 27))

    # -- the sandy floor ----------------------------------------------------------------------------------
    floor = sorted((x, CAVE_FLOOR + 1, z) for (x, y, z) in water if y == CAVE_FLOOR + 1
                   and t.name_at(x, CAVE_FLOOR, z) is not None)
    for (x, y, z) in floor:
        t.set(x, CAVE_FLOOR, z, 'sand')
        if t.name_at(x, CAVE_FLOOR - 1, z) != 'minecraft:water': t.set(x, CAVE_FLOOR - 1, z, 'sand')
        t.set(x, 0, z, 'stone')
    dunes = []
    for (x, y, z) in floor:   # low dunes and boulders
        n = fbm(x, 0, z, 4, SEED + 'd')
        if n > .64 and math.hypot(x - C, z - C) > 4: t.set(x, y, z, 'sand'); dunes.append((x, y, z))
        elif rnd(x, 1, z, 3) < .025: t.set(x, y, z, rng.choice(('andesite', 'calcite', 'diorite')))
    # -- the hoard: a chest under the sand, three little lights in a row, the big clam beside them ----------
    hx, hy, hz = HOARD
    t.set(hx, hy, hz, None)
    t.chest(hx, hy, hz, 'east', 'grotto/hoard')
    t.set(hx, CAVE_FLOOR, hz, 'sand')
    for dz in (-1, 0, 1):
        t.set(hx, CAVE_FLOOR + 1, hz + dz, 'sea_pickle[pickles=1]')
    marked = {(hx + dx, hz + dz) for dx in (-1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2)}
    clams = [(hx + 2, hz, 'west')]
    # -- giant clams on the sand -----------------------------------------------------------------------
    for (x, z, f) in ((12, 10, 'south'), (19, 11, 'west'), (21, 16, 'north'), (17, 19, 'east'), (11, 18, 'east'),
                      (14, 14, 'south'), (7, 17, 'north'), (22, 9, 'south'), (16, 7, 'east')):
        clams.append((x, z, f))
    for i, (x, z, f) in enumerate(clams):
        y = CAVE_FLOOR + 1
        while t.name_at(x, y, z) not in ('minecraft:water',) and y < CAVE_FLOOR + 3: y += 1
        if not full(t, (x, y - 1, z)): continue
        pearl = 'false' if i in (4, 8) else 'true'
        t.set(x, y, z, f'oceanexpansion:giant_clam[facing={f},pearl={pearl}]')
        marked.add((x, z))
    # -- coral heads against the walls, kelp, seagrass and pickles everywhere ---------------------------------
    edge = [p for p in floor if any(add(p, DIRS[d]) not in water for d in SIDES)
            and (p[0], p[2]) not in marked and math.hypot(p[0] - C, p[2] - C) > 6]
    rng.shuffle(edge)
    for (x, y, z) in edge[:14]:
        c = rng.choice(CORALS)
        for k in range(rng.randint(1, 3)):
            if free(t, (x, y + k, z)): t.set(x, y + k, z, f'{c}_coral_block')
    open_floor = [p for p in floor if free(t, p) and (p[0], p[2]) not in marked]
    rng.shuffle(open_floor)
    kelped = 0
    for p in open_floor:
        x, y, z = p
        if (x, z) in POOL or abs(x - 12.5) < 3 and z > 19: continue
        r = rng.random()
        if r < .06 and kelped < 9 and math.hypot(x - C, z - C) < 8:
            if kelp(t, p, rng.randint(4, 7), top=10): kelped += 1
        elif r < .2: pickle(t, p, rng, 4)
        elif r < .5: seagrass(t, p, tall=rng.random() < .4)
        elif r < .58: coral_tuft(t, p, rng)
    for d in dunes:
        if free(t, add(d, (0, 1, 0))) and rng.random() < .5: pickle(t, add(d, (0, 1, 0)), rng, 3)
    # -- the walls: glow lichen, coral fans, sea-glass crystals, a vein of prismarine ---------------------
    walls = []
    for p in sorted(water):
        if p[1] <= CAVE_FLOOR + 1 or not free(t, p): continue
        for d in DIRS:
            if d == 'down': continue
            n = add(p, DIRS[d])
            if t.inside(*n) and n in solid and full(t, n): walls.append((p, d))
    rng.shuffle(walls)
    crystals = 0
    for p, d in walls:
        n = add(p, DIRS[d])
        if (n[0], n[2]) in POOL or n in camp: continue
        r = rng.random()
        if d != 'up' and crystals < 9 and 5 <= n[1] <= 10 and r < .03:
            t.set(*n, 'oceanexpansion:sea_glass'); crystals += 1
            m = add(n, DIRS[rng.choice(('up', 'north', 'south', 'east', 'west'))])
            if m in solid and m not in camp and all(add(m, DIRS[k]) not in camp for k in DIRS): t.set(*m, 'oceanexpansion:sea_glass')
        elif r < .06: t.set(*n, 'prismarine' if rng.random() < .7 else 'dark_prismarine')
        elif fbm(*p, 4, SEED + 'l') > .47 or d == 'up' and r < .5:
            lichen(t, p, d)
        elif d != 'up' and r < .7 and p[1] < 8:
            wall_fan(t, p, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[d], rng.choice(CORALS))
    # pickles on ledges up the walls
    for p in sorted(water):
        if p[1] > CAVE_FLOOR + 2 and free(t, p) and full(t, add(p, (0, -1, 0))) and rnd(*p, 9) < .25:
            pickle(t, p, rng, 3)

    # -- the camp in the air pocket -------------------------------------------------------------------------
    for x in range(12, 18):
        for z in range(24, 28):
            if (x, z) in POOL: continue
            t.set(x, CAMP_Y - 1, z, 'spruce_planks' if rnd(x, 0, z, 4) < .8 else 'stripped_spruce_log[axis=x]')
    for x, z in ((15, 24), (12, 25)):
        t.set(x, CAMP_Y, z, 'spruce_slab[type=bottom]')          # a step up out of the water
    t.bed(17, CAMP_Y, 26, 'south', 'light_blue')
    t.barrel(17, CAMP_Y, 24, 'west', 'grotto/camp')
    t.set(17, CAMP_Y + 1, 24, 'candle[candles=3,lit=true]')
    t.lectern(15, CAMP_Y, 27, 'north', 'Pearling Book', 'Nell Corrow', BOOK)
    t.set(16, CAMP_Y + 2, 25, 'lantern[hanging=true]')
    t.set(12, CAMP_Y, 27, 'lantern[hanging=false]')
    t.sign(12, CAMP_Y + 1, 26, ['PEARLS', 'IIII IIII IIII', 'IIII III', 'black: I'], 'east', wood='spruce')
    t.item_frame(13, CAMP_Y + 1, 27, 'north', 'shears')
    t.set(13, CAMP_Y, 27, 'spruce_slab[type=bottom]')
    t.pot(14, CAMP_Y, 27, 'north')                                # an empty pearl jar
    t.set(16, CAMP_Y, 25, 'white_carpet')                         # a wet old towel by the hole
    # a sign down in the cave where the shaft begins
    spots = []
    for (x, y, z) in water:
        if not (10 <= x <= 17 and 4 <= y <= 7 and 19 <= z <= 25) or (x, z) in POOL: continue
        if t.name_at(x, y, z) != 'minecraft:water': continue
        for f, back in (('east', (-1, 0)), ('west', (1, 0)), ('north', (0, 1)), ('south', (0, -1))):
            if full(t, (x + back[0], y, z + back[1])):
                spots.append((abs(x - 13.5) + abs(z - 23) + abs(y - 6), (x, y, z), f))
    if spots:
        _, (x, y, z), f = min(spots)
        t.sign(x, y, z, ['BREATH ABOVE', 'swim up slow', '^ ^ ^'], f, wood='spruce')

    # -- the mound outside: sand on its shoulders, grass and a few pickles --------------------------------------
    tops, sides, _ = surfaces(t, [p for p in solid if p[1] >= SEABED and t.name_at(*p) and full(t, p)])
    for p in tops:
        if p[1] >= SY or p in water: continue
        r = rng.random()
        below = add(p, (0, -1, 0))
        if r < .25 and fbm(*p, 5, SEED + 's') > .5 and below not in camp and full(t, add(below, (0, -1, 0)))                 and add(below, (0, -1, 0)) not in camp:
            t.set(*below, 'sand')
        elif r < .45: seagrass(t, p)
        elif r < .5: pickle(t, p, rng, 2)
        elif r < .55: coral_tuft(t, p, rng)
    for p, f in sides:
        r = rng.random()
        if p[1] > SEABED and r < .05: wall_fan(t, p, f, rng.choice(CORALS))
        elif p[1] > SEABED and r < .12: barnacles(t, p, f)

    # -- the living -----------------------------------------------------------------------------------------
    for p in ((12, 6, 12), (18, 7, 14), (15, 5, 18), (10, 5, 15), (19, 4, 19), (14, 8, 10)):
        if free(t, p): tropical_fish(t, p, rng)
    if free(t, (16, 4, 15)): t.creature(16, 4, 15, 'minecraft:nautilus', 'west')
    t.entrance(15, 9, 0)
    return t


def reef(name, seed):
    """A coral head on the reef outside: coral blocks heaped on a sandy patch, fans, pickles, kelp."""
    t = Template(name, (9, 7, 9), seed=seed, wet=True)
    rng = t.rng
    blocks = []
    for x in range(9):
        for z in range(9):
            e = math.hypot(x - 4, z - 4) / 4.5 + (fbm(x, 0, z, 3, seed) - .5) * .6
            if e > 1: continue
            t.set(x, 0, z, 'sand' if rnd(x, 0, z, seed) < .7 else 'gravel')
            h = int((1 - e) * 5.5 * fbm(x, 1, z, 3, seed + 'h'))
            for y in range(1, 1 + h):
                c = CORALS[int(fbm(x, y, z, 3, seed + 'c') * 9.99) % 5]
                t.set(x, y, z, f'{c}_coral_block'); blocks.append((x, y, z))
    tops, sides, unders = surfaces(t, blocks + [(x, 0, z) for x in range(9) for z in range(9) if t.get(x, 0, z)])
    for p in tops:
        r = rng.random()
        if r < .45: coral_tuft(t, p, rng)
        elif r < .6: pickle(t, p, rng, 3)
        elif r < .75 and p[1] == 1: seagrass(t, p, tall=rng.random() < .5)
    for p, f in sides:
        if p[1] >= 1 and rng.random() < .35: wall_fan(t, p, f, rng.choice(CORALS))
    for p in ((0, 1, 4), (8, 1, 3), (4, 1, 8)):
        kelp(t, p, rng.randint(3, 6))
    tropical_fish(t, (4, 5, 4), rng)
    return t


BOOK = [
    'PEARLING BOOK\n\nKept in the Breath, the dry room up in the Grotto. Write your name and your take. '
    'Tell no one ashore where the cave lies. Not the priest, not the Tidewatch, not your sweetheart.',
    'THE RULES\n\nOne pearl from a clam, no more. Leave her be and she makes another by the next moon. '
    'Never prise a shut clam. Never dive alone. Come up through the hole and breathe slow.',
    'Spring tally\nNell - 6\nTobin - 4\nAna - 7, one BLACK\nOld Corr - 3\n\nThe black one we kept. '
    'They say black pearls grow only by the fires in the deep. So how did it get here?',
    'The best of the take we keep for lean years, under the sand where three little lights sit in a row by '
    'the big clam. Borrow if you must. Put back what you borrow.',
    'Autumn. Tobin went out past the reef alone, after the black ones, and did not come up. We searched a '
    'week. Ana says the sea has had enough of us. I am the last. The book stays here. - N.',
]


def pieces():
    return [cave(), reef('grotto/reef_a', 'grotto-reef-a'), reef('grotto/reef_b', 'grotto-reef-b')]
