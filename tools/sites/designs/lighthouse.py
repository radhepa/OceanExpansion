"""Lighthouse Isle: a rocky islet with a tall banded lighthouse, the keeper's cottage at its foot and a jetty.
One piece (the islet carries everything), placed rigid at sea level: its bottom five rows are under the waves and
the islet's bottom layer is extended down to the sea floor (footing), so it stands in any depth from 4 to 20."""
import math

from kit import Template, HORIZONTAL
from loot import item, empty, pool, rolls, sea_chart, enchanted, named, WORN
from designs.surface_parts import Noise, Rock, wobble, connect, lantern_post, rowboat, shore_life, tidewatch_banner

KEY = 'lighthouse'
NAME = 'Lighthouse Isle'
FEATURES = [
    'a rocky islet with cliffs, a pebble beach, tide pools, grass, a wind-bent pine and offshore skerries',
    'a 30-block lighthouse banded white and red, a spiral stair inside, the watch room and the lamp room',
    'the great light: sea lanterns in a glass lens, with the keeper\'s signal lamp beside it and a railed gallery',
    'the keeper\'s cottage: hearth, bed, a half-eaten supper, fishing gear, the Lamp Log and the keeper\'s cat',
    'a plank jetty on log piles with lanterns, a bell to ring for the keeper and a moored rowboat',
    'a little walled garden, a woodpile and a rain barrel',
]
SITE = {'anchor': 'surface', 'depth': (4, 20), 'flatness': 8, 'radius': 21, 'weight': 2, 'inhabited': True,
        'biomes': ['ocean', 'lukewarm_ocean', 'warm_ocean', 'cold_ocean']}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'lighthouse/isle', 'at': (0, 0), 'turn': 0, 'y': -5, 'mode': 'rigid', 'footing': True, 'soft': False},
    ]},
]

LAMP_OIL = named('Lamp Oil')
LOOT_TABLES = {
    'lighthouse/keeper': [
        pool(rolls(2, 4), [item('fishing_rod', 3, extra=enchanted(5, 20)), item('fishing_rod', 2, extra=WORN),
                           item('compass', 3), item('spyglass', 2), item('clock', 1), item('book', 2, 1, 2),
                           item('writable_book', 1), item('candle', 3, 2, 4), item('emerald', 4, 1, 4),
                           item('name_tag', 1), empty(3)]),
        pool(1, [sea_chart(3), item('oceanexpansion:storm_glass', 1), item('oceanexpansion:pearl', 2, 1, 2),
                 item('nautilus_shell', 1), empty(5)]),
        pool(rolls(1, 3), [item('cooked_cod', 4, 2, 5), item('cooked_salmon', 3, 1, 4), item('bread', 3, 1, 3),
                           item('dried_kelp', 2, 3, 8), item('pumpkin_pie', 1)]),
    ],
    'lighthouse/stores': [
        pool(rolls(3, 6), [item('honey_bottle', 4, 1, 3, extra=LAMP_OIL), item('candle', 4, 2, 6),
                           item('glowstone_dust', 3, 2, 6), item('glow_ink_sac', 2, 1, 3), item('string', 3, 2, 6),
                           item('glass_pane', 2, 2, 6), item('ink_sac', 2, 1, 4), item('cod', 3, 2, 6),
                           item('kelp', 2, 3, 10), item('lead', 1), item('torch', 2, 3, 8), empty(4)]),
        pool(1, [item('sea_lantern', 1), item('lantern', 3, 1, 2), item('glass', 2, 2, 4), empty(4)]),
    ],
}

K = 5                  # rows under the sea: template rows 0..4 are water, row 5 is sea level (y 63, the first air)
SX, SY, SZ = 40, 37, 40
CX, CZ = 18.0, 18.5    # the islet's middle
TX, TZ = 14, 14        # the tower's middle
FLOOR = 7              # the plateau (walk at 8)
COT = (11, 19, 19, 25)  # cottage x0, z0, x1, z1 (outer walls)
JETTY_Z = (20, 22)


def r_at(y):
    """The tower's outer radius at template row y (it tapers from the plateau to the gallery)."""
    return 5.25 - (5.25 - 3.75) * (max(y, FLOOR) - 7) / 20.0


def in_tower(x, y, z):
    return FLOOR <= y <= 27 and math.hypot(x - TX, z - TZ) <= r_at(y) + 0.05


def _band(rng, y):
    """The tower's skin: a stone plinth, then white and red bands with a little wear."""
    if y <= 9:
        r = rng.random()
        return 'mossy_stone_bricks' if r < .3 else 'cracked_stone_bricks' if r < .42 else 'stone_bricks'
    white = ((y - 10) // 4) % 2 == 0
    r = rng.random()
    if white: return 'calcite' if r < .82 else 'polished_diorite' if r < .93 else 'diorite'
    return 'red_terracotta' if r < .8 else 'bricks' if r < .92 else 'terracotta'


def _ring():
    """The spiral stair's ring around the 3x3 newel, starting at the door (south middle), going clockwise
    seen from above (west first)."""
    return [(0, 2), (-1, 2), (-2, 2), (-2, 1), (-2, 0), (-2, -1), (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
            (2, -1), (2, 0), (2, 1), (2, 2), (1, 2)]


def _facing(a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    return {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}[(dx, dz)]


def _inward(dx, dz):
    """The way from a ring cell toward the tower's axis (dominant axis)."""
    if abs(dx) >= abs(dz): return 'west' if dx > 0 else 'east'
    return 'north' if dz > 0 else 'south'


class Isle:
    def __init__(self):
        self.t = Template('lighthouse/isle', (SX, SY, SZ), wet=True, waterline=K)
        self.rng = self.t.rng
        self.top = {}          # (x, z) -> top row of rock
        self.kind = {}         # (x, z) -> 'grass' | 'beach' | 'rock' | 'sea'
        self.built = set()     # columns covered by buildings / paths (no plants)

    # -- the islet -------------------------------------------------------------------------------
    def terrain(self):
        t, rng = self.t, self.rng
        wob, wob_b = wobble(rng), wobble(rng, ((2, .12), (4, .08), (6, .05)))
        hn, gn, sn = Noise(11, 4.5), Noise(12, 3.5), Noise(13, 2.5)
        rock = Rock(21, K)
        self.rock = rock
        crags = []          # rocky knolls: (angle from the middle, fraction of the radius, height, spread)
        for th, frac, a, sg in ((-1.25, .74, 4.4, 2.6), (3.0, .70, 4.6, 2.6), (2.3, .72, 5.4, 3.0), (1.6, .80, 3.2, 2.4),
                                (-1.95, .84, 3.8, 2.0), (-2.6, .82, 3.0, 2.2)):
            R = 12.8 * wob(th) * frac
            crags.append((CX + math.cos(th) * R / 0.95, CZ + math.sin(th) * R / 1.08, a, sg))
        for x in range(SX):
            for z in range(SZ):
                dx, dz = x - CX, z - CZ
                d = math.hypot(dx * 0.95, dz * 1.08)
                th = math.atan2(dz, dx)
                R = 12.8 * wob(th)
                beach = max(0.0, math.cos(th)) ** 3          # the east side shelves into a pebble beach
                if beach > 0.2: R += 0.6 * beach
                Rb = R + 4.6 * wob_b(th) + 0.6
                s = d / R
                if s <= 1:
                    p = 1.4 + 9 * (1 - beach)
                    h = 3.3 * (1 - s ** p) + (hn(x, z) - 0.5) * 2.0 * (1 - 0.6 * beach)
                    bump = max(a * math.exp(-((x - bx) ** 2 + (z - bz) ** 2) / (2 * sg * sg)) for bx, bz, a, sg in crags)
                    h += bump * (1 - s ** 9) * (1 - beach)
                    if beach > 0.45: h = min(h, 3.0 * (1 - s ** 1.3) + 0.4)
                    top = 4 + round(h)
                elif d <= Rb:
                    f = (d - R) / max(0.5, Rb - R)
                    top = 4 - round(f * 4.8 + (hn(x, z) - 0.5) * 1.6) - 1
                else:
                    continue
                top = max(-1, min(top, 11))
                if top < 0: continue
                self.top[(x, z)] = top
                if 6 <= top <= 8 and beach < 0.5 and gn(x, z) > 0.33 and s < 0.9: self.kind[(x, z)] = 'grass'
                elif beach > 0.45 and top <= 6: self.kind[(x, z)] = 'beach'
                elif top < 4: self.kind[(x, z)] = 'sea'
                else: self.kind[(x, z)] = 'rock'
        # skerries: a few rocks breaking the surface off the cliffs
        for ox, oz, rad, height in ((3.5, 31.5, 2.2, 7), (1.5, 15.0, 1.4, 5), (31.0, 4.0, 2.0, 6), (35.5, 31.5, 1.3, 4),
                                    (21.0, 36.0, 1.2, 4)):
            for x in range(int(ox - rad - 2), int(ox + rad + 3)):
                for z in range(int(oz - rad - 2), int(oz + rad + 3)):
                    if not (0 <= x < SX and 0 <= z < SZ): continue
                    dd = math.hypot(x - ox, z - oz) / (rad * (0.8 + 0.4 * sn(x, z)))
                    if dd > 1.6: continue
                    top = round(height - dd * 2.2 - sn(x, z) * 1.2) if dd <= 1 else round(3 - (dd - 1) * 5)
                    if top < 0: continue
                    if top > self.top.get((x, z), -1):
                        self.top[(x, z)] = top
                        self.kind[(x, z)] = 'rock' if top >= 4 else 'sea'
        # the plateau the tower, cottage and yard stand on
        for (x, z) in list(self.top):
            if self._plateau(x, z):
                self.top[(x, z)] = FLOOR
                if self.kind[(x, z)] != 'grass': self.kind[(x, z)] = 'grass'
        for x in range(SX):
            for z in range(SZ):
                if self._plateau(x, z) and (x, z) not in self.top:
                    self.top[(x, z)] = FLOOR
                    self.kind[(x, z)] = 'grass'
        # soften the step around the plateau: neighbours lower than FLOOR - 2 come up a little
        for (x, z), top in list(self.top.items()):
            if self._plateau(x, z): continue
            near = any(self._plateau(x + a, z + b) for a in (-1, 0, 1) for b in (-1, 0, 1))
            if near and top < FLOOR - 1 and self.kind[(x, z)] != 'beach': self.top[(x, z)] = FLOOR - 1
        # write the columns
        for (x, z), top in self.top.items():
            kind = self.kind[(x, z)]
            for y in range(0, top + 1):
                depth = top - y
                if kind == 'grass':
                    b = 'grass_block' if depth == 0 else 'dirt' if depth <= 1 + (sn(x, z) > .5) else rock(x, y, z)
                elif kind == 'beach':
                    b = (('sand' if sn(x, z) > .55 else 'gravel') if depth == 0 else 'gravel' if depth == 1 else rock(x, y, z))
                elif kind == 'sea':
                    v = sn(x, z)
                    b = (('sand' if v > .6 else 'gravel' if v > .35 else 'clay' if v > .3 else rock(x, y, z)) if depth == 0
                         else rock(x, y, z))
                else:
                    b = 'gravel' if depth == 0 and top <= 6 and sn(x, z) > .72 else rock(x, y, z)
                if b in ('sand', 'gravel') and y == 0: b = rock(x, y, z)
                t.set(x, y, z, b)

    def _plateau(self, x, z):
        if math.hypot(x - TX, z - TZ) <= 6.2: return True
        if COT[0] - 1 <= x <= COT[2] + 1 and COT[1] - 1 <= z <= COT[3] + 1: return True
        if 20 <= x <= 25 and 13 <= z <= 26: return True
        return False

    def tide_pools(self):
        t, rng = self.t, self.rng
        made = 0
        cells = sorted(self.top)
        rng.shuffle(cells)
        pools = []
        for (x, z) in cells:
            if made >= 7: break
            top = self.top[(x, z)]
            if top not in (K, K + 1) or self.kind[(x, z)] not in ('rock', 'beach') or (x, z) in self.built: continue
            if (x, top + 1, z) in t.blocks and t.name_at(x, top + 1, z) != 'minecraft:air': continue
            if any(self.top.get((x + a, z + b), -1) < top for a, b in HORIZONTAL.values()): continue
            if any(abs(x - px) + abs(z - pz) < 4 for px, pz in pools): continue
            t.set(x, top, z, 'seagrass' if rng.random() < .45 else 'water')
            self.built.add((x, z))
            pools.append((x, z))
            made += 1

    def plants(self):
        t, rng = self.t, self.rng
        flora = ['short_grass'] * 8 + ['fern'] * 2 + ['bush'] * 2 + ['tall_grass', 'oxeye_daisy', 'dandelion',
                                                                        'short_dry_grass', 'wildflowers']
        for (x, z), kind in self.kind.items():
            if kind != 'grass' or (x, z) in self.built: continue
            top = self.top[(x, z)]
            if (x, top + 1, z) in t.blocks or top + 2 >= SY: continue
            if rng.random() > 0.42: continue
            f = rng.choice(flora)
            if f == 'tall_grass':
                t.set(x, top + 1, z, 'tall_grass[half=lower]')
                t.set(x, top + 2, z, 'tall_grass[half=upper]')
            elif f == 'wildflowers':
                t.set(x, top + 1, z, f'wildflowers[facing={rng.choice(list(HORIZONTAL))},flower_amount={rng.randint(2, 4)}]')
            else:
                t.set(x, top + 1, z, f)
        # gull nests and white streaks on the far skerries and cliff tops
        for (x, z), kind in self.kind.items():
            top = self.top[(x, z)]
            if kind == 'rock' and top >= 6 and rng.random() < 0.025 and (x, top + 1, z) not in t.blocks:
                t.set(x, top + 1, z, 'hay_block[axis=y]' if rng.random() < .5 else 'short_dry_grass')
                t.set(x, top, z, 'calcite')

    # -- the lighthouse ---------------------------------------------------------------------------
    def tower(self):
        t, rng = self.t, self.rng
        ring = _ring()
        WATCH, LAMP = 24, 29           # walk levels of the watch room and the lamp room
        for y in range(K, 28):
            for dx in range(-6, 7):
                for dz in range(-6, 7):
                    x, z = TX + dx, TZ + dz
                    cheb, d = max(abs(dx), abs(dz)), math.hypot(dx, dz)
                    if d > r_at(y) + 0.05: continue
                    if y <= FLOOR:
                        if cheb > 2: t.set(x, y, z, 'mossy_stone_bricks' if rng.random() < .4 else 'stone_bricks')
                        continue
                    if cheb <= 2: continue
                    t.set(x, y, z, _band(rng, y))
        # ground floor and the newel
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                t.set(TX + dx, FLOOR, TZ + dz, 'polished_andesite')
        for y in range(FLOOR + 1, WATCH - 1):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    t.set(TX + dx, y, TZ + dz, 'stone_bricks' if rng.random() < .85 else 'mossy_stone_bricks')
        # the ring: open, then the stair climbing one block a step, solid beneath each step
        for i, (dx, dz) in enumerate(ring):
            for y in range(FLOOR + 1, WATCH):
                t.set(TX + dx, y, TZ + dz, 'air')
        for i in range(1, 16):
            dx, dz = ring[i]
            y = FLOOR + i
            t.set(TX + dx, y, TZ + dz, f'stone_brick_stairs[facing={_facing(ring[i], ring[(i + 1) % 16])},half=bottom]')
            for yy in range(FLOOR + 1, y):
                t.set(TX + dx, yy, TZ + dz, 'stone_bricks')
        # torches on the outer wall and little windows up the stair
        for i in (4, 8, 12):
            dx, dz = ring[i]
            t.set(TX + dx, FLOOR + i + 2, TZ + dz, f'wall_torch[facing={_inward(dx, dz)}]')
        for i in (1, 5, 9, 13):
            dx, dz = ring[i]
            ox, oz = (0, 1 if dz > 0 else -1) if abs(dz) == 2 else (1 if dx > 0 else -1, 0)
            y = FLOOR + i + 2
            k = 3
            while True:
                x, z = TX + dx + ox * (k - 2), TZ + dz + oz * (k - 2)
                outer = math.hypot(dx + ox * (k - 1), dz + oz * (k - 1)) > r_at(y) + 0.05
                if outer:
                    t.set(x, y, z, 'glass_pane')
                    break
                t.set(x, y, z, 'air')
                k += 1
        t.set(TX, FLOOR + 2, TZ + 2, 'wall_torch[facing=south]')       # at the foot of the stair
        # the doorway through the thick wall into the cottage
        for dz in (3, 4):
            t.set(TX, FLOOR + 1, TZ + dz, 'air')
            t.set(TX, FLOOR + 2, TZ + dz, 'air')
        t.door(TX, FLOOR + 1, TZ + 5, 'south', kind='spruce_door', hinge='left')

        # -- the watch room (walk 24) --------------------------------------------------------------
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                t.set(TX + dx, WATCH - 1, TZ + dz, 'spruce_planks')
                for y in range(WATCH, WATCH + 4):
                    t.set(TX + dx, y, TZ + dz, 'air')
        for dx, dz in ((2, 1), (2, 2), (1, 2)):                      # the stairwell coming up (head room)
            t.set(TX + dx, WATCH - 1, TZ + dz, 'air')
        t.set(TX, WATCH - 1, TZ + 2, 'stone_brick_stairs[facing=west,half=bottom]')
        t.set(TX + 2, WATCH, TZ, 'spruce_fence')
        t.set(TX + 1, WATCH, TZ + 1, 'spruce_fence')
        # the stair on up to the lamp room, along the west wall
        for j, dz in enumerate((2, 1, 0, -1, -2)):
            t.set(TX - 2, WATCH + j, TZ + dz, 'spruce_stairs[facing=north,half=bottom]')
            for yy in range(WATCH, WATCH + j):
                t.set(TX - 2, yy, TZ + dz, 'barrel[facing=up,open=false]' if yy == WATCH and dz in (1, -1) else 'spruce_planks')
        # watch-room things: oil barrels, a table with a candle and a chair, a spyglass, the old banner
        t.barrel(TX + 2, WATCH, TZ - 2, 'north', 'lighthouse/stores')
        t.set(TX + 2, WATCH + 1, TZ - 2, 'candle[candles=3,lit=true]')
        t.set(TX + 1, WATCH, TZ - 2, 'spruce_slab[type=top]')
        t.set(TX + 1, WATCH + 1, TZ - 2, 'candle[candles=1,lit=true]')
        t.set(TX + 1, WATCH, TZ - 1, 'spruce_stairs[facing=south,half=bottom]')
        t.set(TX, WATCH, TZ - 2, 'barrel[facing=up,open=false]')
        t.set(TX, WATCH + 3, TZ, 'lantern[hanging=true]')
        t.item_frame(TX + 2, WATCH + 1, TZ - 1, 'west', 'spyglass')
        t.item_frame(TX + 2, WATCH + 1, TZ + 1, 'west', 'clock')
        tidewatch_banner(t, TX + 1, WATCH + 3, TZ - 2, 'south')
        for side, (wx, wz) in (('n', (0, -3)), ('s', (0, 3)), ('e', (3, 0)), ('w', (-3, 0))):
            for y in (WATCH + 1, WATCH + 2):
                t.set(TX + wx, y, TZ + wz, 'glass_pane')

        # -- the gallery floor, lamp room and roof ---------------------------------------------------
        G = LAMP - 1                                                 # gallery / lamp-room floor row
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                d, cheb = math.hypot(dx, dz), max(abs(dx), abs(dz))
                x, z = TX + dx, TZ + dz
                if d > 5.3: continue
                if cheb <= 3:
                    t.set(x, G, z, 'polished_andesite' if cheb <= 2 else 'waxed_weathered_cut_copper')
                else:
                    t.set(x, G, z, 'smooth_stone_slab[type=top]')
                if d > r_at(27) + 0.05 and cheb >= 3:
                    t.set(x, G - 1, z, f'stone_brick_stairs[facing={_inward(dx, dz)},half=top]')
                edge = any(math.hypot(dx + a, dz + b) > 5.3 for a, b in HORIZONTAL.values())
                if edge: t.set(x, G + 1, z, 'iron_bars')
        for dz in (1, 0, -1):                                        # the stairwell from the watch room
            t.set(TX - 2, G, TZ + dz, 'air')
        t.set(TX - 2, G, TZ - 2, 'spruce_stairs[facing=north,half=bottom]')     # top step of the watch-room stair
        # lamp-room glazing (an octagon) and the lens
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                cheb = max(abs(dx), abs(dz))
                x, z = TX + dx, TZ + dz
                for y in (LAMP, LAMP + 1, LAMP + 2):
                    if cheb == 3 and not (abs(dx) == 3 and abs(dz) == 3):
                        t.set(x, y, z, 'glass_pane')
                    elif cheb == 2:
                        t.set(x, y, z, 'air')
                    elif cheb <= 1:
                        t.set(x, y, z, 'sea_lantern' if (dx, dz) == (0, 0) else
                              'yellow_stained_glass' if y == LAMP + 1 and cheb == 1 and dx * dz == 0 else 'glass')
        t.set(TX - 2, LAMP, TZ + 2, 'oceanexpansion:signal_lamp[facing=south]')     # the keeper's lamp (job site)
        t.sign(TX + 1, LAMP + 1, TZ + 2, ['WE KEEP', 'THE LIGHT', '', 'lit every night'], 'south')
        t.sign(TX - 1, LAMP + 1, TZ - 2, ['wick  oil', 'glass  log', '', 'nights: |||| ||'], 'north')
        t.door(TX + 3, LAMP, TZ, 'east', kind='waxed_weathered_copper_door', hinge='left')
        # roof: a stepped copper cap, a ball and a rod
        R0 = LAMP + 3
        for level, size in ((0, 3), (1, 2), (2, 1)):
            for dx in range(-size, size + 1):
                for dz in range(-size, size + 1):
                    if level == 0 and abs(dx) == 3 and abs(dz) == 3: continue
                    edge = max(abs(dx), abs(dz)) == size
                    corner = abs(dx) == size and abs(dz) == size
                    b = ('waxed_weathered_cut_copper' if (not edge or corner)
                         else f'waxed_weathered_cut_copper_stairs[facing={_inward(dx, dz)},half=bottom]')
                    t.set(TX + dx, R0 + level, TZ + dz, b)
        t.set(TX, R0 + 3, TZ, 'waxed_weathered_copper')
        t.set(TX, R0 + 4, TZ, 'waxed_weathered_lightning_rod[facing=up]')

    # -- the keeper's cottage ---------------------------------------------------------------------
    def cottage(self):
        t, rng = self.t, self.rng
        x0, z0, x1, z1 = COT
        F = FLOOR
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.built.add((x, z))
                wall = x in (x0, x1) or z in (z0, z1)
                t.set(x, F, z, ('cobblestone' if rng.random() < .6 else 'mossy_cobblestone') if wall else 'spruce_planks')
                for y in range(F + 1, F + 4):
                    if in_tower(x, y, z): continue                 # the tower's own wall (and its door)
                    if wall:
                        post = x in (x0, x1) and z in (z0, z1)
                        t.set(x, y, z, 'stripped_spruce_log[axis=y]' if post else 'calcite')
                    else:
                        t.set(x, y, z, 'air')
                if not in_tower(x, F + 4, z): t.set(x, F + 4, z, 'spruce_planks')   # ceiling
        # gable roof along x, ridge over z0 + 3, eaves overhanging one block
        mid = z0 + 3
        for x in range(x0 - 1, x1 + 2):
            for step in range(0, 5):
                y = F + 4 + step
                za, zb = z0 - 1 + step, z1 + 1 - step
                if za > mid: break
                if za == zb:
                    if in_tower(x, y, za): continue
                    t.set(x, y, za, 'spruce_slab[type=bottom]' if x in (x0 - 1, x1 + 1) else 'spruce_planks')
                    t.set(x, y + 1, za, 'deepslate_tile_slab[type=bottom]')
                    continue
                if not in_tower(x, y, za): t.set(x, y, za, 'deepslate_tile_stairs[facing=south,half=bottom]')
                t.set(x, y, zb, 'deepslate_tile_stairs[facing=north,half=bottom]')
                if x in (x0, x1) and step >= 1:
                    for z in range(za + 1, zb):
                        if not in_tower(x, y, z): t.set(x, y, z, 'spruce_planks')
        # windows with shutters and a flower box
        for (x, z, f) in ((x0 + 2, z1, 'south'), (x0 + 5, z1, 'south'), (x1, z0 + 1, 'east'), (x1, z1 - 1, 'east'),
                          (x0, z0 + 1, 'west')):
            t.set(x, F + 2, z, 'glass_pane')
            dx, dz = HORIZONTAL[f]
            if f in ('south', 'north'):
                t.set(x - 1, F + 2, z + dz, f'spruce_trapdoor[facing={f},half=bottom,open=true]')
                t.set(x + 1, F + 2, z + dz, f'spruce_trapdoor[facing={f},half=bottom,open=true]')
                t.set(x + dx, F + 1, z + dz, f'spruce_trapdoor[facing={f},half=top,open=false]')
        t.set(x0 + 5, F + 2, z1 + 1, 'potted_red_tulip')
        t.set(x0 + 2, F + 2, z1 + 1, 'potted_cornflower')
        # front door to the yard, a step and a lantern over it
        dz_door = z0 + 3
        t.door(x1, F + 1, dz_door, 'east', kind='spruce_door', hinge='right')
        t.set(x1 + 1, F + 3, dz_door + 1, 'spruce_fence')
        t.set(x1 + 1, F + 2, dz_door + 1, 'lantern[hanging=true]')
        t.entrance(x1 + 1, F + 1, dz_door)
        # chimney and hearth on the west gable
        hx, hz = x0, z0 + 3
        for y in range(F, F + 11):
            t.set(hx, y, hz, 'cobblestone' if rng.random() < .7 else 'mossy_cobblestone')
        for y in range(F - 1, F + 3):
            t.set(hx - 1, y, hz, 'cobblestone')
        t.set(hx - 1, F + 3, hz, 'cobblestone_wall')
        t.set(hx, F + 11, hz, 'campfire[facing=north,lit=true]')
        t.set(hx + 1, F + 1, hz, 'smoker[facing=east,lit=true]')
        t.set(hx + 1, F + 2, hz, 'cobblestone')
        t.set(hx + 1, F + 3, hz, 'cobblestone_wall')
        t.set(hx + 2, F + 1, hz, 'red_carpet')                  # the cat's place by the fire
        t.creature(hx + 2, F + 1, hz + 1, 'minecraft:cat', facing='west')
        # bed in the south-west corner, the keeper's chest at its foot
        t.bed(x0 + 2, F + 1, z1 - 1, 'west', color='blue')
        t.chest(x0 + 3, F + 1, z1 - 1, 'east', 'lighthouse/keeper')
        t.set(x0 + 1, F + 1, z1 - 2, 'barrel[facing=up,open=false]')
        t.set(x0 + 1, F + 2, z1 - 2, 'candle[candles=2,lit=true]')
        # table with a half-eaten supper, two chairs
        tx, tz = x0 + 4, z0 + 3
        t.set(tx, F + 1, tz, 'spruce_slab[type=top]')
        t.set(tx + 1, F + 1, tz, 'spruce_slab[type=top]')
        t.set(tx, F + 2, tz, 'cake[bites=3]')
        t.item_frame(tx + 1, F + 2, tz, 'up', 'cooked_cod')
        t.set(tx, F + 1, tz - 1, 'spruce_stairs[facing=north,half=bottom]')
        t.set(tx + 1, F + 1, tz + 1, 'spruce_stairs[facing=south,half=bottom]')
        t.set(tx, F + 3, tz, 'lantern[hanging=true]')
        # the Lamp Log on its lectern by the south window
        t.lectern(x0 + 6, F + 1, z1 - 1, 'north', 'Lamp Log', 'the Keeper of the Isle', LAMP_LOG)
        # kitchen and fishing corner (north side, by the tower)
        t.barrel(x1 - 1, F + 1, z0 + 1, 'west', 'lighthouse/stores')
        t.set(x1 - 1, F + 2, z0 + 1, 'barrel[facing=up,open=false]')
        t.set(x1 - 1, F + 1, z0 + 2, 'water_cauldron[level=2]')
        t.set(x0 + 1, F + 1, z0 + 1, 'crafting_table')
        t.set(x0 + 2, F + 1, z0 + 1, 'barrel[facing=up,open=false]')
        t.item_frame(x1 - 1, F + 2, z0 + 2, 'west', 'fishing_rod')
        t.item_frame(x0 + 1, F + 2, z0 + 2, 'east', 'cod')
        t.set(x1 - 1, F + 3, z0 + 1, 'cobweb')                       # an old net in the rafters
        t.set(x0 + 5, F + 3, z0 + 1, 'lantern[hanging=true]')
        tidewatch_banner(t, x0 + 6, F + 3, z0 + 1, 'south')
        t.resident(x0 + 4, F + 1, z1 - 1, 'lightkeeper', 'north')

    # -- yard, path, garden, jetty ---------------------------------------------------------------------
    def yard(self):
        t, rng = self.t, self.rng
        F = FLOOR
        # a path of coarse dirt / gravel from the door to the beach, the jetty's root
        for x in range(COT[2] + 1, 33):
            for z in (21, 22):
                top = self.top.get((x, z))
                if top is None or top < K: continue
                if (x, top + 1, z) in t.blocks and t.name_at(x, top + 1, z) not in ('minecraft:short_grass',):
                    t.set(x, top + 1, z, None)
                t.set(x, top, z, 'dirt_path' if top >= 6 and rng.random() < .7 else 'gravel' if top < 6 else 'coarse_dirt')
                self.built.add((x, z))
        # a little garden walled in cobble, a composter and a rain barrel
        gx0, gz0, gx1, gz1 = 21, 14, 25, 18
        for x in range(gx0, gx1 + 1):
            for z in range(gz0, gz1 + 1):
                self.built.add((x, z))
                if x in (gx0, gx1) or z in (gz0, gz1):
                    t.set(x, F + 1, z, 'mossy_cobblestone_wall' if rng.random() < .4 else 'cobblestone_wall')
                else:
                    t.set(x, F, z, 'farmland[moisture=0]')
                    crop = rng.choice(['carrots', 'potatoes', 'beetroots'])
                    t.set(x, F + 1, z, f'{crop}[age={rng.randint(1, 3) if crop == "beetroots" else rng.randint(2, 7)}]')
        t.set(gx0 + 2, F + 1, gz1, 'spruce_fence_gate[facing=south,open=false,in_wall=true]')
        t.set(gx1 + 1, F + 1, gz0 + 1, 'composter[level=4]')
        t.set(COT[2] + 1, F + 1, COT[3] - 1, 'water_cauldron[level=3]')      # rain barrel under the eaves
        # woodpile against the cottage's south wall
        for x in range(COT[0] + 1, COT[0] + 4):
            t.set(x, F + 1, COT[3] + 1, 'spruce_log[axis=x]')
        t.set(COT[0] + 1, F + 2, COT[3] + 1, 'spruce_log[axis=x]')
        t.set(COT[0] + 4, F + 1, COT[3] + 1, 'stripped_spruce_log[axis=y]')     # the chopping block
        for x in range(COT[0], COT[0] + 5): self.built.add((x, COT[3] + 1))
        # lantern posts along the path
        lantern_post(t, 24, F + 1, 20, 2)
        self.built.add((24, 20))
        # a wind-bent pine on the north-east rocks
        self.pine(23, 11)
        # an upturned boat on the beach
        bx, bz = 27, 26
        top = self.top.get((bx, bz))
        if top is not None and top >= K:
            for i in range(4):
                t.set(bx + i, top + 1, bz, 'spruce_stairs[facing=south,half=top]')
                t.set(bx + i, top + 1, bz + 1, 'spruce_stairs[facing=north,half=top]')
                self.built.update({(bx + i, bz), (bx + i, bz + 1)})

    def pine(self, px, pz):
        t = self.t
        top = self.top.get((px, pz), FLOOR)
        y = top + 1
        trunk = [(0, 0), (0, 0), (0, 0), (1, 0), (1, 0), (2, 1)]
        x, z = px, pz
        for i, (ox, oz) in enumerate(trunk):
            x, z = px + ox, pz + oz
            t.set(x, y + i, z, 'spruce_log[axis=y]')
            self.built.add((x, z))
        t.set(px + 1, y + 2, pz, 'spruce_log[axis=x]')
        cx, cy, cz = px + 2, y + 6, pz + 1
        for dx in range(-3, 4):
            for dy in range(-1, 3):
                for dz in range(-3, 4):
                    r = (dx * dx) / 9.0 + (dz * dz) / 6.0 + (dy * dy) / 2.5
                    if r <= 1.0 and (cx + dx, cy + dy, cz + dz) not in t.blocks and self.rng.random() < .92:
                        t.set(cx + dx, cy + dy, cz + dz, 'spruce_leaves[persistent=true,distance=1]')
        t.set(cx, cy, cz, 'spruce_log[axis=y]')
        t.set(cx - 1, cy - 1, cz, 'spruce_log[axis=x]')
        for dx, dz in ((-2, 0), (-1, 1), (0, -1)):
            t.set(px - 1 + dx + 1, y + 3, pz + dz, 'spruce_leaves[persistent=true,distance=1]')

    def jetty(self):
        t, rng = self.t, self.rng
        za, zb = JETTY_Z
        start = None
        for x in range(26, SX):
            if self.top.get((x, 21), -1) <= K:
                start = x
                break
        start = start or 30
        end = 37
        for x in range(start, end + 1):
            for z in range(za, zb + 1):
                if self.top.get((x, z), -1) > K: continue
                plank = 'spruce_planks' if rng.random() > .08 else 'stripped_spruce_wood[axis=x]'
                t.set(x, K, z, plank)
                for y in range(K + 1, K + 3):
                    if (x, y, z) in t.blocks: t.set(x, y, z, None)
        # the T-head
        for x in range(end - 2, end + 1):
            for z in range(za - 2, zb + 3):
                t.set(x, K, z, 'spruce_planks')
        # piles from the sea floor (footing extends the bottom block) up to a post above the deck
        piles = [(x, z, True) for x in range(start + 1, end, 3) for z in (za, zb)]
        piles += [(end - 2, za - 2, True), (end, za - 2, True), (end - 2, zb + 2, True), (end, zb + 2, True),
                  (end, 21, False)]
        for (x, z, post) in piles:
            if self.top.get((x, z), -1) >= K: continue
            low = max(0, self.top.get((x, z), -1) + 1)
            for y in range(low, K + (2 if post else 1)):
                t.set(x, y, z, 'spruce_log[axis=y]')
        # rails between the posts on the head, lanterns, the bell, barrels and a coil of rope
        lantern_post(t, end, K + 1, za - 2, 2)
        lantern_post(t, end, K + 1, zb + 2, 2)
        lantern_post(t, start + 1, K + 2, za, 1)
        t.set(end - 1, K + 1, za - 2, 'stripped_spruce_log[axis=y]')
        t.set(end - 1, K + 2, za - 2, 'bell[attachment=floor,facing=east]')
        t.sign(end - 1, K + 1, za - 1, ['RING FOR', 'THE KEEPER', '', 'charts sold'], 'south')
        t.set(end - 2, K + 1, zb + 2, 'barrel[facing=up,open=false]')
        t.set(end - 2, K + 1, zb + 1, 'barrel[facing=up,open=false]')
        t.set(end - 2, K + 2, zb + 2, 'iron_chain[axis=x]')
        t.entrance(end, K + 1, 21)
        # the rowboat moored alongside, in open water, tied to the deck by a rope
        best = None
        for x0 in range(start, end - 6):
            for z0, tie in ((za - 3, za - 1), (zb + 1, zb + 1)):
                cells = [(x0 + i, z0 + j) for i in range(5) for j in range(3)]
                if all(self.top.get(c, -1) <= K - 2 and (c[0], K - 1, c[1]) not in t.blocks and
                       (c[0], K, c[1]) not in t.blocks for c in cells):
                    best = (x0, z0, tie)
        if best:
            x0, z0, tie = best
            rowboat(t, x0, K - 1, z0, along='x', length=5)
            self.built.update((x0 + i, z0 + j) for i in range(5) for j in range(3))
            rope_z = za if tie == za - 1 else zb
            t.set(x0 + 3, K + 1, rope_z, 'spruce_fence')                   # a cleat on the deck edge

    def build(self):
        self.terrain()
        self.tower()
        self.cottage()
        self.yard()
        self.jetty()
        self.tide_pools()
        self.plants()
        shore_life(self.t, K, self.rng, rock_names={'stone', 'andesite', 'tuff', 'cobblestone', 'mossy_cobblestone',
                                                     'diorite', 'gravel', 'sand', 'clay', 'spruce_log'})
        connect(self.t)
        return self.t


LAMP_LOG = [
    'LAMP LOG\n\nKept on this isle as the Tidewatch taught me: wick, oil, glass, log. Every night, any weather.\n\n'
    'We keep the light.',
    'Spring. Oil low till the supply cog comes. Gulls back on the north rocks. Lit at sunset, out at dawn. '
    'Glass clean. The cat has taken my bed again.',
    'A fisher hailed me from the jetty. Swears he saw a mast standing up out of the sea floor, gold on her '
    'stern rail. The Golden Heron, he says. I drew it on a chart and sold it on.',
    'Storm three nights running. Lamp held. At the turn of the tide something rang a bell out on the water. '
    'There is no bell out there. Blue lights deep down to the south, slow.',
    'The fort answers my light with its beacon, as it should. A sloop slipped past tonight with no lamps lit. '
    'No names on the water, they say. I wrote it down anyway.',
    'If you come for a Sea Chart, bring a compass and some coin. The sea tells sailors, sailors tell me, '
    'and I tell the paper. Ring the bell on the jetty.',
]


def pieces():
    return [Isle().build()]
