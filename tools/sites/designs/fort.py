"""Tidewatch Fort: a squat stone sea fort on a reef. A curtain wall with chamfered corners and two round towers,
a sea gate with a portcullis into a little harbour, a three-storey keep (mess, barracks, armory and the captain's
room) with the beacon brazier on its roof. One piece, rigid at sea level; the reef's bottom layer is extended
down to the sea floor (footing)."""
import math

from kit import Template, HORIZONTAL
from loot import item, empty, pool, rolls, sea_chart, enchanted, named, WORN, RANDOM_ENCHANT
from designs.surface_parts import (Noise, Rock, wobble, connect, lantern_post, rowboat, ballista, shore_life,
                                   tidewatch_banner, TIDEWATCH_LOOT)

KEY = 'fort'
NAME = 'Tidewatch Fort'
FEATURES = [
    'a stone sea fort on a reef: a battered curtain wall with crenellations and two round corner towers',
    'a sea gate with a raised portcullis opening into an inner harbour with a pier and a moored rowboat',
    'a three-storey keep: the mess and stores, the barracks (five bunks), the armory with training dummies and '
    'archery targets, and the captain\'s room with the Tide Log',
    'the beacon brazier, an alarm bell and the Tidewatch flag on the keep roof; ballistae on the towers',
    'a forge, a cistern, a supply cart, and the brig a smuggler broke out of',
]
SITE = {'anchor': 'surface', 'depth': (5, 18), 'flatness': 8, 'radius': 24, 'weight': 2, 'inhabited': True,
        'biomes': ['ocean', 'lukewarm_ocean', 'warm_ocean', 'cold_ocean']}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'fort/fort', 'at': (0, 0), 'turn': 0, 'y': -4, 'mode': 'rigid', 'footing': True, 'soft': False},
    ]},
]

TIDEWATCH_BANNER = item('blue_banner', 1, extra=TIDEWATCH_LOOT + named('Tidewatch Banner'))
LOOT_TABLES = {
    'fort/armory': [
        pool(rolls(3, 5), [item('iron_sword', 3, extra=WORN), item('bow', 3, extra=WORN), item('crossbow', 2, extra=WORN),
                           item('arrow', 6, 6, 18), item('shield', 2), item('iron_helmet', 1, extra=WORN),
                           item('chainmail_chestplate', 1, extra=WORN), item('leather_boots', 1),
                           item('iron_ingot', 2, 1, 3), item('string', 2, 2, 5), item('flint', 1, 1, 4)]),
        pool(1, [item('iron_sword', 1, extra=enchanted(15, 25)), item('bow', 1, extra=enchanted(15, 25)),
                 item('crossbow', 1, extra=RANDOM_ENCHANT), item('spectral_arrow', 2, 4, 10), empty(4)]),
        pool(1, [TIDEWATCH_BANNER, empty(5)]),
    ],
    'fort/captain': [
        pool(rolls(2, 4), [item('emerald', 4, 2, 6), item('gold_ingot', 3, 1, 3), item('compass', 2), item('spyglass', 2),
                           item('writable_book', 1), item('paper', 2, 2, 6), item('candle', 2, 1, 3),
                           item('oceanexpansion:pearl', 2, 1, 2), item('honey_bottle', 1, extra=named('Captain\'s Rum'))]),
        pool(1, [sea_chart(3), item('oceanexpansion:storm_glass', 1), item('diamond', 1), empty(3)]),
        pool(1, [TIDEWATCH_BANNER, item('iron_sword', 1, extra=enchanted(20, 30) + named('Watch Blade')), empty(3)]),
    ],
    'fort/stores': [
        pool(rolls(4, 7), [item('bread', 6, 2, 6), item('baked_potato', 4, 2, 5), item('cooked_cod', 4, 2, 5),
                           item('cooked_porkchop', 3, 1, 4), item('apple', 3, 1, 4), item('dried_kelp', 3, 4, 10),
                           item('carrot', 2, 2, 5), item('wheat', 2, 3, 8), item('torch', 3, 4, 10),
                           item('arrow', 3, 6, 16), item('coal', 2, 2, 6), item('leather', 2, 1, 3),
                           item('iron_nugget', 2, 3, 9), item('honey_bottle', 1, extra=named('Ship\'s Rum')), empty(3)]),
        pool(1, [item('cake', 1), item('lantern', 2), item('shield', 1), empty(5)]),
    ],
}

K = 4                       # rows under the sea (0..3); row 4 is sea level (y 63), the courtyard paving
SX, SY, SZ = 46, 27, 46
OUT = (8, 37, 9, 36)        # the curtain wall's outer face: x0, x1, z0, z1 (chamfered at two corners)
CHAMFER = 6
TOWERS = {'nw': (9.5, 10.5), 'se': (35.5, 34.5)}
TOWER_R = 4.6
WALL_TOP = 9                # wall-walk floor row (walk at 10)
TOWER_TOP = 13              # the towers' fighting platforms (walk at 14), over a chamber at wall-walk level
KEEP = (20, 31, 14, 24)     # keep walls x0, x1, z0, z1
F1, F2, F3, ROOF = 4, 9, 14, 19   # floor rows of the keep (walk one above)
GATE = (15, 19)             # sea-gate opening, x range in the south wall
BASIN = (13, 21, 26, 33)    # inner harbour x0, x1, z0, z1


def in_out(x, z):
    x0, x1, z0, z1 = OUT
    if not (x0 <= x <= x1 and z0 <= z <= z1): return False
    if (x1 - x) + (z - z0) < CHAMFER: return False       # north-east corner cut
    if (x - x0) + (z1 - z) < CHAMFER: return False       # south-west corner cut
    return True


def in_court(x, z):
    """Inside the curtain wall (3 thick): every cell within Chebyshev 3 is inside the outline."""
    return all(in_out(x + a, z + b) for a in (-3, 0, 3) for b in (-3, 0, 3)) and \
        all(in_out(x + a, z + b) for a in (-2, 2) for b in (-2, 2))


def tower_d(x, z):
    return min((math.hypot(x - cx, z - cz), k) for k, (cx, cz) in TOWERS.items())


class Fort:
    def __init__(self):
        self.t = Template('fort/fort', (SX, SY, SZ), wet=True, waterline=K)
        self.rng = self.t.rng
        self.rock = Rock(31, K, mossy=0.45)
        self.n = Noise(32, 3.0)

    def masonry(self, x, y, z, base='stone_bricks'):
        """Weathered stone bricks: mossy and cracked low down, near the water."""
        r = self.rng.random()
        low = y <= K + 1
        if r < (0.34 if low else 0.12): return 'mossy_stone_bricks'
        if r < (0.44 if low else 0.20): return 'cracked_stone_bricks'
        if r < 0.23 and not low: return 'andesite' if base == 'stone_bricks' else base
        return base

    # -- reef ------------------------------------------------------------------------------------------
    def reef(self):
        t, rng = self.t, self.rng
        wob = wobble(rng, ((2, .1), (3, .09), (5, .06), (8, .03)))
        hn = Noise(33, 4.0)
        cx, cz = 22.5, 22.5
        for x in range(SX):
            for z in range(SZ):
                th = math.atan2(z - cz, x - cx)
                d = math.hypot(x - cx, z - cz)
                R = 21.0 * wob(th)
                if d > R and not in_out(x, z) and tower_d(x, z)[0] > TOWER_R + 1: continue
                inside = in_out(x, z) or tower_d(x, z)[0] <= TOWER_R + 1
                f = max(0.0, (d - 15) / max(1.0, R - 15))
                top = 3 if inside else int(round(3.4 - f * 4 + (hn(x, z) - .5) * 2.6))
                if not inside and hn(x, z) > .78 and f < .6: top = K + rng.randint(0, 1)   # rocks awash
                top = min(top, K + 1)
                for y in range(0, max(0, top) + 1):
                    t.set(x, y, z, self.rock(x, y, z) if not (y == top and top < K and hn(x, z) > .6) else
                          ('gravel' if y > 0 else self.rock(x, y, z)))

    # -- curtain wall and towers --------------------------------------------------------------------------
    def walls(self):
        t, rng = self.t, self.rng
        for x in range(SX):
            for z in range(SZ):
                td, which = tower_d(x, z)
                tower = td <= TOWER_R
                wall = in_out(x, z) and not in_court(x, z)
                if TOWER_R < td <= TOWER_R + 0.95:
                    # the towers' parapets stand out on corbels
                    cx, cz = TOWERS[which]
                    f = (('west' if x > cx else 'east') if abs(x - cx) >= abs(z - cz) else ('north' if z > cz else 'south'))
                    t.set(x, TOWER_TOP, z, f'stone_brick_stairs[facing={f},half=top]')
                    for y in (TOWER_TOP + 1, TOWER_TOP + 2):
                        t.set(x, y, z, self.masonry(x, y, z))
                    ang = math.atan2(z - cz, x - cx)
                    if int((ang + math.pi) / (2 * math.pi) * 20) % 2 == 0:
                        t.set(x, TOWER_TOP + 3, z, self.masonry(x, TOWER_TOP + 3, z))
                if not (tower or wall): continue
                outer = any(not in_out(x + a, z + b) and tower_d(x + a, z + b)[0] > TOWER_R
                            for a, b in HORIZONTAL.values())
                if tower:
                    room = td <= 2.6
                    for y in range(1, TOWER_TOP + 1):
                        if room and (K + 1 <= y <= K + 4 or WALL_TOP + 1 <= y <= TOWER_TOP - 1):
                            t.set(x, y, z, 'air')
                            continue
                        t.set(x, y, z, self.masonry(x, y, z))
                    continue
                for y in range(1, WALL_TOP + 1):
                    t.set(x, y, z, self.masonry(x, y, z))
                if outer:
                    t.set(x, WALL_TOP + 1, z, self.masonry(x, WALL_TOP + 1, z))
                    if (x + z) % 2 == 0: t.set(x, WALL_TOP + 2, z, self.masonry(x, WALL_TOP + 2, z))
        # a battered footing just outside the wall, under and at the waterline
        for x in range(SX):
            for z in range(SZ):
                if in_out(x, z) or tower_d(x, z)[0] <= TOWER_R: continue
                near = any(in_out(x + a, z + b) or tower_d(x + a, z + b)[0] <= TOWER_R for a, b in HORIZONTAL.values())
                if not near: continue
                for y in range(1, K):
                    t.set(x, y, z, 'mossy_cobblestone' if rng.random() < .5 else 'cobblestone')
                if rng.random() < .35: t.set(x, K - 1, z, 'mossy_stone_brick_stairs[facing=%s,half=bottom]' % self._toward_fort(x, z))

    def _toward_fort(self, x, z):
        for d, (a, b) in HORIZONTAL.items():
            if in_out(x + a, z + b) or tower_d(x + a, z + b)[0] <= TOWER_R: return d
        return 'north'

    def courtyard(self):
        t = self.t
        bx0, bx1, bz0, bz1 = BASIN
        for x in range(SX):
            for z in range(SZ):
                if not in_court(x, z): continue
                basin = bx0 <= x <= bx1 and bz0 <= z <= bz1
                for y in range(1, K):
                    t.set(x, y, z, 'water' if basin else self.rock(x, y, z))
                if basin: continue
                v = self.n(x, z)
                t.set(x, K, z, 'cobblestone' if v < .25 else 'gravel' if v > .82 else 'stone_bricks' if v < .6
                      else 'polished_andesite' if v < .7 else 'mossy_stone_bricks')
        # the sea gate: a channel through the south wall, an arch, and the portcullis raised in its slot
        g0, g1 = GATE
        zs = sorted({z for x in range(g0, g1 + 1) for z in range(26, SZ) if in_out(x, z) and not in_court(x, z)})
        for x in range(g0, g1 + 1):
            for z in zs + [bz1]:
                for y in range(1, K): t.set(x, y, z, 'water')
                for y in range(K, K + 4): t.set(x, y, z, None)
            for z in zs:
                t.set(x, K + 4, z, self.masonry(x, K + 4, z))
        for z in zs:
            t.set(g0, K + 3, z, 'stone_brick_stairs[facing=east,half=top]')
            t.set(g1, K + 3, z, 'stone_brick_stairs[facing=west,half=top]')
        mid = zs[len(zs) // 2]
        for bx in (g0 - 1, g1 + 1):                        # Tidewatch banners either side of the sea gate
            tidewatch_banner(t, bx, K + 5, max(zs) + 1, 'south')
        for x in range(g0, g1 + 1):
            t.set(x, K + 3, mid, 'iron_bars')
            t.set(x, K + 4, mid, 'iron_bars')
        self.gate_z = zs
        self.t.entrance((g0 + g1) // 2, K - 1, max(zs))
        # the winch over the gate on the wall-walk
        t.set(g0 + 1, WALL_TOP + 1, mid - 1, 'grindstone[face=floor,facing=east]')
        t.set(g1 - 1, WALL_TOP + 1, mid - 1, 'grindstone[face=floor,facing=west]')
        for x in range(g0 + 2, g1 - 1):
            t.set(x, WALL_TOP + 1, mid - 1, 'iron_chain[axis=x]')
        # the pier along the harbour's east side and the moored boat
        for z in range(bz0, bz1 + 1):
            t.set(bx1, K, z, 'spruce_planks')
            if (z - bz0) % 3 == 0:
                for y in range(1, K): t.set(bx1, y, z, 'spruce_log[axis=y]')
                t.set(bx1, K + 1, z, 'spruce_fence')
        rowboat(t, bx0 + 2, K - 1, bz0 + 1, along='z', length=5)
        t.set(bx1, K + 1, bz0 + 2, 'spruce_fence')
        lantern_post(t, bx1, K + 1, bz1 - 1, 2)

    def stair_to_wall(self, x, z, dx, dz, n=WALL_TOP - K):
        """A straight stone stair against a wall's inner face from the courtyard up to the wall-walk."""
        t = self.t
        f = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}[(dx, dz)]
        for i in range(n):
            px, pz = x + dx * i, z + dz * i
            for y in range(K + 1, K + 1 + i): t.set(px, y, pz, self.masonry(px, y, pz))
            t.set(px, K + 1 + i, pz, f'stone_brick_stairs[facing={f},half=bottom]')

    # -- the keep -------------------------------------------------------------------------------------------
    def keep(self):
        t = self.t
        x0, x1, z0, z1 = KEEP
        ix, iz = x0 + 1, z0 + 1
        P = lambda u, v: (ix + u, iz + v)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                wall = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                for y in range(K, ROOF + 1):
                    if wall:
                        t.set(x, y, z, 'polished_andesite' if corner and y % 5 != 4 else self.masonry(x, y, z))
                    elif y in (F1, F2, F3, ROOF):
                        t.set(x, y, z, 'stone_bricks' if y in (F1, ROOF) else 'spruce_planks')
                    else:
                        t.set(x, y, z, 'air')
                if wall:
                    t.set(x, ROOF + 1, z, self.masonry(x, ROOF + 1, z))
                    if (x + z) % 2 == 0 or corner: t.set(x, ROOF + 2, z, self.masonry(x, ROOF + 2, z))
        # string course of smooth stone between the floors, outside
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                if x0 <= x <= x1 and z0 <= z <= z1: continue
                if x in (x0 - 1, x1 + 1) and z in (z0 - 1, z1 + 1): continue
                f = 'east' if x == x0 - 1 else 'west' if x == x1 + 1 else 'south' if z == z0 - 1 else 'north'
                t.set(x, F3, z, f'stone_brick_stairs[facing={f},half=top]')
                t.set(x, ROOF, z, f'stone_brick_stairs[facing={f},half=top]')
        # doors and windows
        t.door(x0, F1 + 1, z0 + 7, 'west', kind='spruce_door', hinge='left')
        t.entrance(x0 - 1, F1 + 1, z0 + 7)
        tidewatch_banner(t, x0 - 1, F1 + 4, z0 + 5, 'west')
        tidewatch_banner(t, x0 - 1, F1 + 4, z0 + 9, 'west')
        t.set(x0 - 1, F1 + 3, z0 + 6, 'wall_torch[facing=west]')
        t.set(x0 - 1, F1 + 3, z0 + 8, 'wall_torch[facing=west]')
        for (x, z) in ((x0, z0 + 3), (x1, z0 + 3), (x1, z0 + 7), (x0 + 3, z0), (x0 + 7, z0), (x0 + 4, z1), (x0 + 8, z1),
                       (x0, z1 - 1)):
            for fl in (F2, F3):
                t.set(x, fl + 2, z, 'iron_bars')
                t.set(x, fl + 3, z, 'iron_bars')
        for (x, z) in ((x1, z0 + 2), (x0 + 6, z0), (x1, z0 + 5)):
            t.set(x, F1 + 2, z, 'iron_bars')

        # stairs between the floors (head room cut in the floor above)
        def flight(cells, base, facing, under='spruce_planks'):
            for i, (u, v) in enumerate(cells):
                x, z = P(u, v)
                t.set(x, base + 1 + i, z, f'spruce_stairs[facing={facing},half=bottom]')
                for y in range(base + 1, base + 1 + i): t.set(x, y, z, under)
                if 1 <= i <= len(cells) - 2: t.set(x, base + len(cells), z, 'air')
            return cells
        flight([(0, 4), (0, 3), (0, 2), (0, 1), (0, 0)], F1, 'north')
        flight([(9, 8), (9, 7), (9, 6), (9, 5), (9, 4)], F2, 'north')
        for (u, v) in ((1, 1), (1, 2), (1, 3)):                     # rails round the stairwells
            t.set(*self._xyz(P(u, v), F2 + 1), 'spruce_fence')
        for (u, v) in ((8, 5), (8, 6), (8, 7)):
            t.set(*self._xyz(P(u, v), F3 + 1), 'spruce_fence')

        # F1: the mess hall, kitchen and stores
        y = F1 + 1
        for u in range(3, 8):
            t.set(*self._xyz(P(u, 4), y), 'spruce_slab[type=top]')
            t.set(*self._xyz(P(u, 3), y), 'spruce_stairs[facing=north,half=bottom]')
            t.set(*self._xyz(P(u, 5), y), 'spruce_stairs[facing=south,half=bottom]')
        t.set(*self._xyz(P(3, 4), y + 1), 'candle[candles=3,lit=true]')
        t.item_frame(*self._xyz(P(5, 4), y + 1), 'up', 'bread')
        t.item_frame(*self._xyz(P(6, 4), y + 1), 'up', 'cooked_cod')
        t.set(*self._xyz(P(7, 4), y + 1), 'cake[bites=2]')
        t.barrel(*self._xyz(P(9, 0), y), 'west', 'fort/stores')
        t.set(*self._xyz(P(9, 1), y), 'smoker[facing=west,lit=true]')
        t.set(*self._xyz(P(9, 2), y), 'furnace[facing=west,lit=true]')
        t.set(*self._xyz(P(9, 3), y), 'water_cauldron[level=3]')
        t.set(*self._xyz(P(8, 0), y), 'crafting_table')
        t.set(*self._xyz(P(9, 1), y + 1), 'cobblestone')
        t.set(*self._xyz(P(9, 2), y + 1), 'cobblestone')
        for (u, v) in ((7, 8), (8, 8), (9, 8), (9, 7)):
            t.set(*self._xyz(P(u, v), y), 'barrel[facing=up,open=false]')
        t.barrel(*self._xyz(P(8, 7), y), 'north', 'fort/stores')
        t.set(*self._xyz(P(9, 6), y), 'hay_block[axis=y]')
        t.set(*self._xyz(P(9, 8), y + 1), 'barrel[facing=up,open=false]')
        t.set(*self._xyz(P(5, 8), y), 'white_wool')                  # flour sacks
        t.set(*self._xyz(P(6, 8), y), 'brown_wool')
        for (u, v) in ((5, 1), (5, 7), (2, 6), (1, 1)):
            t.set(*self._xyz(P(u, v), F2 - 1), 'lantern[hanging=true]')
        tidewatch_banner(t, *self._xyz(P(4, 0), F2 - 1), 'south')

        # F2: the barracks, five bunks
        y = F2 + 1
        for u in (3, 5, 7):
            t.bed(*self._xyz(P(u, 1), y), 'north', color='blue')
        for u in (3, 5):
            t.bed(*self._xyz(P(u, 7), y), 'south', color='blue')
        for u in (4, 6):
            t.set(*self._xyz(P(u, 0), y), 'barrel[facing=up,open=false]')
            t.set(*self._xyz(P(u, 0), y + 1), 'candle[candles=1,lit=true]')
        t.set(*self._xyz(P(4, 8), y), 'barrel[facing=up,open=false]')
        t.set(*self._xyz(P(8, 0), y), 'barrel[facing=up,open=false]')
        t.set(*self._xyz(P(2, 5), y), 'spruce_slab[type=top]')         # a card table
        t.item_frame(*self._xyz(P(2, 5), y + 1), 'up', 'paper')
        t.set(*self._xyz(P(2, 4), y), 'spruce_stairs[facing=north,half=bottom]')
        t.set(*self._xyz(P(2, 6), y), 'spruce_stairs[facing=south,half=bottom]')
        for (u, v, f, it) in ((9, 1, 'west', 'bow'), (9, 2, 'west', 'iron_sword'), (6, 8, 'north', 'shield')):
            t.item_frame(*self._xyz(P(u, v), y + 1), f, it)
        for (u, v) in ((5, 3), (5, 6), (8, 2), (1, 5), (2, 1), (7, 7)):
            t.set(*self._xyz(P(u, v), F3 - 1), 'lantern[hanging=true]')
        t.resident(*self._xyz(P(4, 3), y), 'warden_knight', 'south')
        t.resident(*self._xyz(P(6, 3), y), 'warden_knight', 'south')
        t.resident(*self._xyz(P(4, 5), y), 'warden_archer', 'north')
        t.resident(*self._xyz(P(6, 5), y), 'warden_archer', 'north')

        # F3: the captain's room (west) and the armory with the training floor (east)
        y = F3 + 1
        for v in range(0, 9):
            for yy in range(y, ROOF):
                t.set(*self._xyz(P(4, v), yy), 'spruce_planks' if v != 4 or yy > y + 1 else 'air')
        t.set(*self._xyz(P(4, 0), y), 'stripped_spruce_log[axis=y]')
        t.door(*self._xyz(P(4, 4), y), 'east', kind='spruce_door', hinge='left')
        # captain
        t.lectern(*self._xyz(P(1, 1), y), 'south', 'Tide Log', 'Captain of the Watch', TIDE_LOG)
        t.chest(*self._xyz(P(3, 8), y), 'north', 'fort/captain')
        t.set(*self._xyz(P(2, 1), y), 'spruce_stairs[facing=north,half=bottom]')
        t.set(*self._xyz(P(0, 0), y), 'bookshelf')
        t.set(*self._xyz(P(0, 1), y), 'bookshelf')
        t.set(*self._xyz(P(0, 0), y + 1), 'bookshelf')
        t.set(*self._xyz(P(3, 0), y), 'cartography_table')
        t.item_frame(*self._xyz(P(0, 3), y + 1), 'east', 'map')
        t.item_frame(*self._xyz(P(0, 4), y + 1), 'east', 'compass')
        t.item_frame(*self._xyz(P(0, 5), y + 1), 'east', 'map')
        for v in range(2, 7):
            for u in range(1, 4):
                t.set(*self._xyz(P(u, v), y), 'blue_carpet')
        t.set(*self._xyz(P(3, 7), y), 'barrel[facing=up,open=false]')
        t.set(*self._xyz(P(3, 7), y + 1), 'candle[candles=2,lit=true]')
        t.set(*self._xyz(P(2, 3), ROOF - 1), 'lantern[hanging=true]')
        t.set(*self._xyz(P(2, 7), ROOF - 1), 'lantern[hanging=true]')
        tidewatch_banner(t, *self._xyz(P(2, 0), y + 2), 'south')
        for yy in range(y, ROOF + 1):                                  # ladder to the roof
            t.set(*self._xyz(P(0, 8), yy), 'ladder[facing=east]')
        t.resident(*self._xyz(P(2, 4), y), 'captain', 'east')
        # armory and training floor
        for u in (5, 7, 9):
            t.set(*self._xyz(P(u, 0), y), 'villagefriends:training_dummy[facing=south]')
        for u in (6, 8):
            t.set(*self._xyz(P(u, 8), y), 'villagefriends:archery_target[facing=north]')
        t.chest(*self._xyz(P(5, 8), y), 'north', 'fort/armory')
        t.set(*self._xyz(P(9, 2), y), 'grindstone[face=floor,facing=west]')
        t.set(*self._xyz(P(9, 3), y), 'anvil[facing=north]')
        t.set(*self._xyz(P(7, 8), y), 'fletching_table')
        for (u, v, f, it) in ((9, 1, 'west', 'crossbow'), (5, 1, 'east', 'iron_axe'), (5, 3, 'east', 'iron_sword'),
                              (5, 6, 'east', 'bow')):
            t.item_frame(*self._xyz(P(u, v), y + 1), f, it)
        for (u, v) in ((7, 2), (7, 6)):
            t.set(*self._xyz(P(u, v), ROOF - 1), 'lantern[hanging=true]')
        t.sign(*self._xyz(P(6, 7), y), ['NO SHOOTING', 'PAST THE LINE', '', 'sgt. of bows'], 'north', wall=False)

        # the roof: the beacon brazier, the flag, the alarm bell and a ballista
        y = ROOF + 1
        cx, cz = P(4, 4)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                t.set(cx + a, y, cz + b, 'polished_blackstone_bricks')
                t.set(cx + a, y + 1, cz + b, 'campfire[facing=north,lit=true]' if a * b == 0 else 'polished_blackstone_wall')
        for a, b in ((-1, -1), (1, 1)):
            t.set(cx + a, y + 2, cz + b, 'lantern[hanging=false]')
        fx, fz = P(9, 0)
        for yy in range(y, y + 6): t.set(fx, yy, fz, 'stripped_spruce_log[axis=y]')
        tidewatch_banner(t, fx - 1, y + 5, fz, 'west')
        tidewatch_banner(t, fx, y + 5, fz + 1, 'south')
        bx, bz = P(0, 0)
        t.set(bx, y, bz + 1, 'stripped_spruce_log[axis=y]')
        t.set(bx, y + 1, bz + 1, 'bell[attachment=floor,facing=east]')
        ballista(t, P(6, 7)[0], y, P(6, 7)[1], 'south')
        t.set(*self._xyz(P(9, 8), y), 'barrel[facing=up,open=false]')

    @staticmethod
    def _xyz(p, y):
        return p[0], y, p[1]

    # -- towers, wall-walk, yard ---------------------------------------------------------------------
    def towers(self):
        t = self.t
        # NW tower: the powder room and stores; SE tower: the brig
        for name, (cx, cz) in TOWERS.items():
            cells = [(x, z) for x in range(int(cx) - 3, int(cx) + 4) for z in range(int(cz) - 3, int(cz) + 4)
                     if math.hypot(x - cx, z - cz) <= 2.6]
            for (x, z) in cells:
                t.set(x, K, z, 'stone_bricks')
                t.set(x, K + 5, z, 'spruce_planks')
            # a doorway to the nearest courtyard cell
            best = min(((x, z) for x in range(SX) for z in range(SZ) if in_court(x, z) and tower_d(x, z)[0] > TOWER_R + .5),
                       key=lambda p: math.hypot(p[0] - cx, p[1] - cz))
            x, z = int(round(cx)), int(round(cz))
            path = []
            while (x, z) != best:
                # step diagonally-ish: whichever axis is further off first
                if abs(best[0] - x) >= abs(best[1] - z): x += 1 if best[0] > x else -1
                else: z += 1 if best[1] > z else -1
                path.append((x, z))
            inside = [p for p in path if tower_d(*p)[0] <= TOWER_R]
            for (x, z) in path:
                if (x, z) == best: break
                t.set(x, K, z, 'stone_bricks')
                t.set(x, K + 1, z, 'air')
                t.set(x, K + 2, z, 'air')
            door = inside[-1]
            nxt = path[path.index(door) + 1]
            f = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}[(nxt[0] - door[0], nxt[1] - door[1])]
            t.door(door[0], K + 1, door[1], f, kind='spruce_door')
            i = path.index(door)
            if i >= 1:                                  # a lantern in a niche over the passage behind the door
                px, pz = path[i - 1]
                t.set(px, K + 3, pz, 'lantern[hanging=true]')
            cxi, czi = int(round(cx)), int(round(cz))
            t.set(cxi, K + 4, czi, 'lantern[hanging=true]')
            room = [c for c in cells if c not in path]
            if name == 'nw':
                for i, (x, z) in enumerate(sorted(room, key=lambda p: -math.hypot(p[0] - best[0], p[1] - best[1]))[:7]):
                    if i < 2: t.barrel(x, K + 1, z, 'up', 'fort/stores')
                    elif i < 5: t.set(x, K + 1, z, 'barrel[facing=up,open=false]')
                    else: t.set(x, K + 1, z, 'hay_block[axis=y]')
                far = sorted(room, key=lambda p: -math.hypot(p[0] - best[0], p[1] - best[1]))
                t.set(far[0][0], K + 2, far[0][1], 'barrel[facing=up,open=false]')
            else:
                # the brig: bars across the back of the room, one bent out, a bucket and a rope ladder of escape
                far = sorted(room, key=lambda p: -math.hypot(p[0] - best[0], p[1] - best[1]))
                cell = far[:5]
                for (x, z) in room:
                    if (x, z) in cell: continue
                    if any((x + a, z + b) in cell for a, b in HORIZONTAL.values()):
                        for yy in (K + 1, K + 2, K + 3):
                            t.set(x, yy, z, 'iron_bars' if (x + z) % 4 else 'air')
                x, z = cell[0]
                t.set(x, K + 1, z, 'cauldron')
                x, z = cell[1]
                t.set(x, K + 1, z, 'white_carpet')
                x, z = cell[2]
                t.sign(x, K + 1, z, ['ESCAPED', 'gave no name', 'took the boat', '- the watch'], 'north', wall=False)
                # the hole he dug out through the outer wall, half-patched with cobble
                ox, oz = cell[0]
                ddx = 1 if ox > cx else -1
                for k in range(1, 4):
                    hx = ox + ddx * k
                    if math.hypot(hx - cx, oz - cz) > TOWER_R: break
                    t.set(hx, K + 1, oz, 'air' if k < 3 else 'cobblestone')      # a crawl hole, patched
            # the chamber at wall-walk level: doorways from both wall-walks, a ladder up to the platform
            sgn = -1 if name == 'se' else 1
            cxi, czi = int(round(cx)), int(round(cz))
            for (ddx, ddz) in ((sgn, 0), (0, sgn)):
                k = 1
                while True:
                    x, z = cxi + ddx * k, czi + ddz * k
                    if tower_d(x, z)[0] > TOWER_R: break
                    t.set(x, WALL_TOP + 1, z, 'air')
                    t.set(x, WALL_TOP + 2, z, 'air')
                    k += 1
                x, z = cxi + ddx * (k - 2), czi + ddz * (k - 2)
                t.set(x, WALL_TOP + 2, z, 'wall_torch[facing=south]' if ddx else 'wall_torch[facing=east]')
            lx = cxi
            while math.hypot(lx - sgn - cx, czi - cz) <= 2.6: lx -= sgn
            for yy in range(WALL_TOP + 1, TOWER_TOP + 1):
                t.set(lx, yy, czi, f'ladder[facing={"east" if sgn == 1 else "west"}]')
            t.set(cxi, TOWER_TOP - 1, czi - sgn, 'lantern[hanging=true]')
            t.set(cxi - sgn, WALL_TOP + 1, czi - sgn, 'barrel[facing=up,open=false]')
            t.set(cxi, WALL_TOP + 1, czi - 2 * sgn, 'barrel[facing=up,open=false]')
            t.set(cxi, WALL_TOP + 2, czi - 2 * sgn, 'iron_chain[axis=x]')
            # arrow slits facing the sea
            for (ddx, ddz) in ((-sgn, 0), (0, -sgn), (-sgn, -sgn)):
                for yy in (K + 2, WALL_TOP + 2):
                    if yy == WALL_TOP + 2 and ddz == 0: continue          # the ladder's wall
                    k = 1
                    while True:
                        x, z = cxi + ddx * k, czi + ddz * k
                        if tower_d(x, z)[0] > TOWER_R: break
                        if math.hypot(x - cx, z - cz) > 2.6:
                            last = tower_d(x + ddx, z + ddz)[0] > TOWER_R
                            t.set(x, yy, z, 'iron_bars' if last else 'air')
                        k += 1
            # a ballista on the platform, facing out to sea
            out = 'north' if name == 'nw' else 'south'
            ballista(t, cxi + sgn, TOWER_TOP + 1, czi, out)
            t.set(cxi - sgn, TOWER_TOP + 1, czi + sgn, 'lantern[hanging=false]')

    def wallwalk(self):
        t = self.t
        x0, x1, z0, z1 = OUT
        # stairs up from the courtyard: west wall (north-going) and east wall (south-going)
        self.stair_to_wall(11, 22, 0, -1)
        self.stair_to_wall(34, 22, 0, 1)
        # lanterns along the wall-walk on posts by the inner edge
        for x in range(SX):
            for z in range(SZ):
                if not (in_out(x, z) and not in_court(x, z)): continue
                inner = any(in_court(x + a, z + b) for a, b in HORIZONTAL.values())
                if inner and (x * 7 + z * 13) % 11 == 0:
                    t.set(x, WALL_TOP + 1, z, 'lantern[hanging=false]')
        # a few loose stones and a gull's nest on the parapet
        t.set(x0 + 15, WALL_TOP + 1, z0 + 1, 'cobblestone_wall')

    def yard(self):
        t = self.t
        y = K + 1
        # the cistern
        for a in range(0, 4):
            for b in range(0, 4):
                x, z = 13 + a, 15 + b
                if a in (0, 3) or b in (0, 3): t.set(x, y, z, 'stone_brick_wall')
                else:
                    t.set(x, K, z, 'water')
                    t.set(x, K - 1, z, 'stone_bricks')
        for (a, b) in ((0, 0), (3, 3)):
            t.set(13 + a, y + 1, 15 + b, 'spruce_fence')
            t.set(13 + a, y + 2, 15 + b, 'spruce_fence')
        for a in range(4):
            t.set(13 + a, y + 3, 15 + a, 'spruce_slab[type=bottom]')
        t.set(14, y + 3, 15, 'spruce_slab[type=bottom]')
        t.set(16, y + 3, 18, 'spruce_slab[type=bottom]')
        # the supply cart and crates near the gate
        cx0 = 24
        for i in range(3):
            t.set(cx0 + i, y, 28, 'spruce_slab[type=top]')
        t.set(cx0 + 1, y + 1, 28, 'barrel[facing=up,open=false]')
        t.set(cx0 + 2, y + 1, 28, 'hay_block[axis=x]')
        for i in (0, 2):
            t.set(cx0 + i, y, 27, 'spruce_trapdoor[facing=north,half=bottom,open=true]')
            t.set(cx0 + i, y, 29, 'spruce_trapdoor[facing=south,half=bottom,open=true]')
        t.set(cx0 - 1, y, 28, 'spruce_fence')
        for (x, z) in ((27, 31), (28, 31), (27, 32), (29, 32)):
            t.set(x, y, z, 'barrel[facing=up,open=false]')
        t.set(27, y + 1, 32, 'barrel[facing=up,open=false]')
        t.set(28, y, 32, 'hay_block[axis=y]')
        # the forge against the east wall
        t.set(32, y, 27, 'blast_furnace[facing=west,lit=true]')
        t.set(32, y, 28, 'smithing_table')
        t.set(31, y, 29, 'anvil[facing=north]')
        t.set(32, y, 29, 'water_cauldron[level=2]')
        t.set(32, y, 26, 'grindstone[face=floor,facing=west]')
        for z in range(26, 30):
            for yy in (y, y + 1, y + 2):
                if (33, yy, z) not in t.blocks: t.set(33, yy, z, self.masonry(33, yy, z))
            t.set(32, y + 3, z, 'spruce_slab[type=bottom]')
            t.set(31, y + 3, z, 'spruce_slab[type=bottom]')
        t.set(31, y + 1, 26, 'spruce_fence'); t.set(31, y + 2, 26, 'spruce_fence')
        t.set(31, y + 1, 29, 'spruce_fence'); t.set(31, y + 2, 29, 'spruce_fence')
        t.set(31, y, 26, 'spruce_fence'); t.set(31, y, 29, None)
        t.set(32, y + 2, 28, 'lantern[hanging=true]')
        # lantern posts about the courtyard
        for (x, z) in ((18, 13), (12, 24), (23, 33), (33, 24), (27, 26)):
            lantern_post(t, x, y, z, 2)
        # a training post and straw targets in the yard for idle hours
        t.set(17, y, 21, 'hay_block[axis=y]')
        t.set(17, y + 1, 21, 'carved_pumpkin[facing=east]')

    def build(self):
        self.reef()
        self.walls()
        self.courtyard()
        self.keep()
        self.towers()
        self.wallwalk()
        self.yard()
        shore_life(self.t, K, self.rng, barnacles=0.3, kelp=0.12, grass=0.3,
                   rock_names={'stone', 'andesite', 'tuff', 'cobblestone', 'mossy_cobblestone', 'diorite', 'gravel',
                               'stone_bricks', 'mossy_stone_bricks', 'cracked_stone_bricks', 'spruce_log'})
        connect(self.t)
        return self.t


TIDE_LOG = [
    'TIDE LOG\nTidewatch Fort\n\nGarrison: two blades, two bows, one captain. Beacon lit at dusk. The lighthouse '
    'answers. We keep the light.',
    'Low water. Three drowned walked up the reef at the ebb and tried the sea gate. Bows saw them off. '
    'Portcullis winch sticks: grease it.',
    'Supply cog late again. Rations cut to bread and salt fish. The men grumble. I grumble. The keeper on the isle '
    'sent a sack of cod by rowboat, bless him.',
    'A sloop running dark past the stacks to the north. Gave chase in the rowboat. Lost her among the rocks. '
    'No names on the water, the smugglers say. We will find one.',
    'The prisoner from the sloop is gone. Dug out through the brig wall with a spoon, took the boat. He laughed '
    'when we asked his name.',
    'Bought a Sea Chart from the keeper: a wreck on the sea floor south of here, gold on her rail. '
    'Not our business. Still. If the weather holds.',
]


def pieces():
    return [Fort().build()]
