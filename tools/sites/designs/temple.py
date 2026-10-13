"""The Drowned Sanctum: a temple of the Old Tide, half sunk into the sea floor.

Three pieces: the temple itself (a pylon facade with the great carved eye, a flooded nave with stone columns and
side aisles, a grand stair down into the sunken sanctum with the altar under a second eye, and a sealed
reliquary behind the sanctum wall), a fallen colonnade and a leaning eye obelisk from the outer precinct.
See DESIGN.md ("Design module contract" and the temple brief).

Heights in the temple (template y; the piece sits at y -10, so y 9 is the top of the sea floor at the centre and
the water starts at y 10):
  y 0       the sunken sanctum's floor (walk at 1) and the reliquary floor
  y 6       the nave, aisle and gallery floor (walk at 7): three rows under the sand outside
  y 7..21   the nave (vault up to y 22), aisles up to y 13; columns to y 13, arches to y 15
  y 23      the roof ridge (most of the nave roof has fallen; ribs remain)
  y 26      the pylon merlons and the facade crest
Everything under the floor line inside the temple is flooded; the sand drifts there are deliberate.
"""
from kit import Template
from loot import item, empty, pool, rolls, sea_chart, enchanted, WORN, named, trim

KEY = 'temple'
NAME = 'The Drowned Sanctum'
FEATURES = [
    'a pylon facade half sunk in the sand; over the half-buried great door, the great carved eye of the Old Tide '
    '(dark prismarine ring, sea lantern iris, black pupil)',
    'a flooded nave of stone columns and prismarine arches with side aisles; the roof fallen in, one column '
    'toppled across the floor',
    'three guardians wake in the nave',
    'a grand stair down into the sunken sanctum: the altar with the Old Tide trident relic and the altar chest '
    'beneath it, watched by a second great eye',
    'offering niches with Old Tide pots in the aisles and in the sanctum walls',
    'a sealed reliquary behind the dark sanctum wall, reached only through a crack beside the altar: sherd pots, '
    'an inscription, a thief who never left',
    'sand drifting in through the door; coral and kelp reclaiming the breached east gallery',
    'outside: a fallen colonnade of the outer precinct and a leaning eye obelisk with its tip in the sand',
]
SITE = {
    'anchor': 'seabed',
    'depth': (20, 45),      # the ridge stands 17 above the floor: at least one row of water over it
    'flatness': 9,
    'radius': 24,
    'biomes': ['warm_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean', 'ocean', 'deep_ocean'],
    'weight': 2,
    'inhabited': False,
}
LAYOUTS = [
    # The precinct's colonnade on one flank, the obelisk out by the opposite front corner.
    {'weight': 1, 'pieces': [
        {'piece': 'temple/sanctum', 'at': (0, 0), 'turn': 0, 'y': -10, 'mode': 'rigid'},
        {'piece': 'temple/colonnade', 'at': (19, -6), 'turn': 0, 'y': -2, 'mode': 'floor'},
        {'piece': 'temple/obelisk', 'at': (-20, -17), 'turn': 0, 'y': -2, 'mode': 'floor'},
    ]},
    # Mirrored: the colonnade on the other flank toward the back, the obelisk by the rear corner.
    {'weight': 1, 'pieces': [
        {'piece': 'temple/sanctum', 'at': (0, 0), 'turn': 0, 'y': -10, 'mode': 'rigid'},
        {'piece': 'temple/colonnade', 'at': (-19, 8), 'turn': 2, 'y': -2, 'mode': 'floor'},
        {'piece': 'temple/obelisk', 'at': (20, 16), 'turn': 1, 'y': -2, 'mode': 'floor'},
    ]},
]
LOOT_TABLES = {
    # The prize, in the chest under the altar.
    'temple/altar': [
        pool(rolls(3, 5), [item('prismarine_crystals', 6, 2, 6), item('gold_ingot', 5, 2, 5),
                           item('gold_nugget', 4, 4, 10), item('prismarine_shard', 4, 3, 8),
                           item('oceanexpansion:pearl', 3, 1, 3), item('nautilus_shell', 2, 1, 2),
                           item('emerald', 2, 1, 3)]),
        pool(1, [item('heart_of_the_sea', 1), empty(3)]),
        pool(1, [item('trident', 1, extra=enchanted(20, 30) + WORN + named('Trident of the Old Tide')), empty(9)]),
        pool(1, [trim('tide', 1), empty(1)]),
        pool(1, [sea_chart(1), empty(1)]),
    ],
    # Small things left for the eye. A decorated pot holds one stack, so one roll.
    'temple/offering': [
        pool(1, [item('gold_nugget', 6, 2, 5), item('prismarine_shard', 5, 2, 4), item('bone_meal', 4, 2, 4),
                 item('prismarine_crystals', 3, 1, 3), item('oceanexpansion:pearl', 2, 1, 1),
                 item('nautilus_shell', 1), empty(3)]),
    ],
}

CORALS = ('tube', 'brain', 'bubble', 'fire', 'horn')


def _pick(rng, table):
    total = sum(w for _, w in table)
    r = rng.random() * total
    for spec, w in table:
        r -= w
        if r < 0: return spec
    return table[-1][0]


def _materials(t):
    r = t.rng
    wall = lambda *_: _pick(r, [('prismarine_bricks', 7), ('prismarine', 3)])
    stone = lambda *_: _pick(r, [('stone_bricks', 5), ('mossy_stone_bricks', 3), ('cracked_stone_bricks', 3)])
    return wall, stone


def _eye(t, cx, cy, z, sclera, ring='dark_prismarine', iris='sea_lantern', pupil='black_concrete'):
    """The Old Tide's great eye, 13 wide and 7 tall, carved into the wall plane z, centred on (cx, cy)."""
    rows = {
        3: '...DDDDDDD...',
        2: '.DDSSLLLSSDD.',
        1: 'DSSSLLPLLSSSD',
        0: 'DSSLLPPPLLSSD',
        -1: 'DSSSLLPLLSSSD',
        -2: '.DDSSLLLSSDD.',
        -3: '...DDDDDDD...',
    }
    kinds = {'D': ring, 'S': sclera, 'L': iris, 'P': pupil}
    for dy, row in rows.items():
        for i, c in enumerate(row):
            if c != '.': t.set(cx - 6 + i, cy + dy, z, kinds[c])


def kelp(t, x, y0, z, h):
    cells = [(x, y, z) for y in range(y0, y0 + h)]
    if not all(t.inside(*c) and t.name_at(*c) in (None, 'minecraft:water') for c in cells): return
    if t.name_at(x, y0 - 1, z) in (None, 'minecraft:water'): return
    for c in cells[:-1]: t.set(*c, 'kelp_plant')
    t.set(*cells[-1], 'kelp')


def is_water(t, x, y, z):
    return t.inside(x, y, z) and t.name_at(x, y, z) == 'minecraft:water'


SOFT_TOPS = ('water', 'kelp', 'seagrass', 'pickle', '_coral', 'pot', 'lichen', 'barnacles', 'haunt', 'chest', 'skull',
             'sign', '_wall', 'pane', 'fence', 'bars', 'lantern')


def solid_below(t, x, y, z):
    """Is there a block with a full, sturdy top under (x, y, z)? (what pickles, seagrass and coral need)"""
    b = t.blocks.get((x, y - 1, z))
    if b is None: return False
    name, props = b
    short = name.split(':')[1]
    if short.endswith('_coral_block') or short == 'sea_lantern': return True
    if short.endswith('_slab'): return props.get('type') in ('top', 'double')
    if short.endswith('_stairs'): return props.get('half') == 'top'
    return not any(s in short for s in SOFT_TOPS)


DEBRIS = [('prismarine_bricks', 4), ('prismarine', 3), ('dark_prismarine', 2), ('prismarine_brick_slab[type=bottom]', 4),
          ('dark_prismarine_slab[type=bottom]', 2), ('STAIRS', 4), ('cracked_stone_bricks', 2), ('mossy_stone_bricks', 2),
          ('stone_brick_slab[type=bottom]', 2), ('mossy_stone_brick_slab[type=bottom]', 1)]


def rubble(t, x0, x1, z0, z1, y, n, stack=0.25):
    """Scatter n pieces of fallen masonry on the floor whose walk level is y (only into open water)."""
    r = t.rng
    for _ in range(n):
        x, z = r.randint(x0, x1), r.randint(z0, z1)
        for yy in (y, y + 1, y + 2):
            if is_water(t, x, yy, z) and solid_below(t, x, yy, z): break
        else:
            continue
        if yy > y and r.random() > stack: continue
        spec = _pick(r, DEBRIS)
        if spec == 'STAIRS':
            spec = f"{r.choice(['prismarine_brick_stairs', 'dark_prismarine_stairs', 'stone_brick_stairs'])}" \
                   f"[facing={r.choice(['north', 'south', 'east', 'west'])},half={r.choice(['bottom', 'bottom', 'top'])}]"
        t.set(x, yy, z, spec)


def seagrass(t, x0, x1, z0, z1, y, p):
    r = t.rng
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if r.random() < p and is_water(t, x, y, z) and solid_below(t, x, y, z):
                if r.random() < 0.3 and is_water(t, x, y + 1, z):
                    t.set(x, y, z, 'tall_seagrass[half=lower]')
                    t.set(x, y + 1, z, 'tall_seagrass[half=upper]')
                else:
                    t.set(x, y, z, 'seagrass')


# -- the temple -------------------------------------------------------------------------------------------------

W, H, L = 29, 27, 45
CX = 14          # the long axis; the facade looks north (z 0), the apse is at the south end
GT = 9           # top of the sea floor at the centre (the piece sits at y -10)
NF = 6           # nave / aisle / gallery floor (walk at 7)
COLS = (7, 12, 17, 22, 27, 32)   # z of each pair of 2x2 columns (z, z + 1)
PIT = 26         # the grand stair starts here; the sunken sanctum runs to z 36
APSE = 37        # the apse wall, z 37..38
CAP, ARCH, BAND = 13, 14, 15     # column capitals, arch springers, the band over the arcade
CLER = (16, 18)                  # clerestory rows over the arcade
VAULT = {9: 19, 10: 20, 11: 21, 12: 22, 13: 22, 14: 22}               # west half of the vault (inner surface)
ROOF = {7: 19, 8: 19, 9: 20, 10: 21, 11: 22, 12: 23, 13: 23, 14: 23}  # west half of the roof (outer surface)
# The nave roof stands only near the facade, in the middle and over the altar; elsewhere only the ribs remain.
ROOFED = set(range(5, 10)) | set(range(22, 25)) | set(range(34, 39))
RIBS = {12: None, 17: (9, 14), 27: None, 32: (16, 19)}   # rib z -> the x span it still has (None: whole)


def m(x):
    return W - 1 - x


def sanctum():
    t = Template('temple/sanctum', (W, H, L), wet=True)
    r = t.rng
    wall, stone = _materials(t)

    # -- the rooms, flooded first (everything under the floor line too) ------------------------------------------
    t.flood((3, 7, 5), (25, ARCH, 36))        # aisles, galleries, arcade and nave up to the springers
    t.flood((9, BAND, 5), (19, 21, 36))       # the nave's upper part, up into the vault
    t.flood((9, 1, PIT), (19, 6, 36))         # the sunken sanctum
    t.flood((11, 7, 2), (17, 16, 4))          # the great door
    t.flood((11, 10, 0), (17, 16, 1))         # its approach

    # -- floors ---------------------------------------------------------------------------------------------------
    def nave_floor(x, y, z):
        if x in (7, 8, 9, 19, 20, 21): return 'dark_prismarine'
        if 13 <= x <= 15:
            return 'dark_prismarine' if any(c <= z <= c + 1 for c in COLS) else 'prismarine_bricks'
        return _pick(r, [('prismarine_bricks', 10), ('prismarine', 7), ('sand', 2), ('gravel', 1),
                         ('cracked_stone_bricks', 1)])
    t.fill((3, NF, 5), (25, NF, PIT - 1), nave_floor)
    for x0, x1 in ((3, 6), (22, 25)):
        t.fill((x0, NF, PIT), (x1, NF, 36), nave_floor)              # the galleries over the sanctum
    for x0, x1 in ((7, 8), (20, 21)):
        t.fill((x0, 0, PIT), (x1, NF - 1, 36), stone)                 # the sanctum's side walls
        t.fill((x0, NF, PIT), (x1, NF, 36), 'dark_prismarine')        # their coping
    t.fill((9, 0, PIT), (19, 0, 36), lambda x, y, z: 'dark_prismarine' if x in (9, 19) or z == 36 or (x + z) % 4 == 0
           else 'prismarine_bricks')
    # the grand stair: from the nave floor down six rows into the sanctum, between stepped cheek walls
    for i, z in enumerate(range(PIT, PIT + 5)):
        step = 5 - i
        if step > 1: t.fill((10, 1, z), (18, step - 1, z), stone)
        t.fill((10, step, z), (18, step, z), 'prismarine_brick_stairs[facing=north]')
        for x in (9, 19):
            t.fill((x, 1, z), (x, step, z), 'dark_prismarine')
            t.set(x, step + 1, z, 'dark_prismarine_stairs[facing=north]')
    for x in (9, 19):
        t.set(x, 7, PIT, 'dark_prismarine'); t.set(x, 8, PIT, 'sea_lantern')          # lamp posts at the top
        t.set(x, 1, PIT + 5, 'dark_prismarine'); t.set(x, 2, PIT + 5, 'sea_lantern')  # and at the foot

    # -- outer walls, buttresses ---------------------------------------------------------------------------------
    def outer(x, y, z):
        if y <= 11: return stone()
        return 'dark_prismarine' if y == 12 else wall()
    for x0, x1 in ((1, 2), (26, 27)):
        t.fill((x0, 4, 5), (x1, ARCH, 38), outer)
    for c in COLS:
        for x, f in ((0, 'east'), (28, 'west')):
            top = 12 if r.random() < 0.7 else r.randint(10, 11)                   # some have crumbled
            t.fill((x, 4, c), (x, top, c + 1), stone)
            if top == 12: t.fill((x, 13, c), (x, 13, c + 1), f'stone_brick_stairs[facing={f}]')
            else: t.set(x, top + 1, c + r.randint(0, 1), 'stone_brick_slab[type=bottom]')
    for x in (4, 5, 23, 24):                                                         # and at the back
        t.fill((x, 4, APSE + 2), (x, 12, APSE + 3), stone)
        t.set(x, 13, APSE + 2, 'stone_brick_stairs[facing=north]'); t.set(x, 13, APSE + 3, 'stone_brick_slab[type=bottom]')

    # -- the apse wall (z 37..38): the dark seal over the reliquary low down, a stone panel for the eye -----------
    for x in range(1, 28):
        if x <= 6 or x >= 22: y0, top = 4, ARCH
        elif x in (7, 8, 20, 21): y0, top = 0, CLER[1]
        else: y0, top = 0, VAULT[min(x, m(x))]
        for z in (APSE, APSE + 1):
            for y in range(y0, top + 1):
                if 7 <= x <= 17 and y <= 5: s = 'dark_prismarine'
                elif y <= 5: s = stone()
                elif z == APSE and 8 <= x <= 20 and 8 <= y <= 16: s = stone()
                else: s = 'prismarine_bricks' if z == APSE else wall()
                t.set(x, y, z, s)

    # -- the arcade: 2x2 stone columns, arches, the clerestory ---------------------------------------------------
    def column(x0, z0, lantern=False, broken=None):
        pit = z0 >= PIT
        west = x0 < CX
        aisle_side, nave_side = (x0 - 1, x0 + 2) if west else (x0 + 2, x0 - 1)
        toward = {aisle_side: 'east' if west else 'west', nave_side: 'west' if west else 'east'}
        top = CAP if broken is None else broken
        for x in (x0, x0 + 1):
            for z in (z0, z0 + 1):
                t.set(x, 7, z, 'dark_prismarine')
                for y in range(8, top):
                    t.set(x, y, z, 'chiseled_stone_bricks' if y == 10 else stone())
                if broken is None:
                    t.set(x, CAP, z, 'sea_lantern' if lantern and abs(x - nave_side) == 1 else 'dark_prismarine')
        if broken is not None:
            t.set(x0 + r.randint(0, 1), top, z0 + r.randint(0, 1), stone())        # a jagged break
        for y, half, mat in ((7, 'bottom', 'prismarine_brick_stairs'), (CAP, 'top', 'dark_prismarine_stairs')):
            if y == CAP and broken is not None: continue
            for x in (aisle_side, nave_side):
                if y == 7 and pit and x == nave_side: continue
                for z in (z0, z0 + 1):
                    t.set(x, y, z, f'{mat}[facing={toward[x]},half={half}]')
            if y == 7 and pit: continue
            for x in (x0, x0 + 1):
                t.set(x, y, z0 - 1, f'{mat}[facing=south,half={half}]')
                t.set(x, y, z0 + 2, f'{mat}[facing=north,half={half}]')

    for x0 in (7, 20):
        t.fill((x0, BAND, 5), (x0 + 1, BAND, 36), 'dark_prismarine')
        for c in COLS:
            column(x0, c, lantern=c in (12, 22) or (c == 32 and x0 == 20),
                   broken=11 if (x0, c) == (7, 32) else 10 if (x0, c) == (20, 17) else None)
        for x in (x0, x0 + 1):
            t.set(x, CAP, 5, 'dark_prismarine_stairs[facing=north,half=top]')
            for a, b in [(5, 6)] + [(c + 2, c + 4) for c in COLS]:
                t.set(x, ARCH, a, 'prismarine_brick_stairs[facing=north,half=top]')
                t.set(x, ARCH, b, 'prismarine_brick_stairs[facing=south,half=top]')
        # the balustrade along the sanctum's edge
        xb = x0 + 1 if x0 < CX else x0
        for z in range(PIT, 37):
            if is_water(t, xb, 7, z): t.set(xb, 7, z, 'prismarine_wall[north=low,south=low]')
        # clerestory with sea-glass windows
        t.fill((x0, CLER[0], 5), (x0 + 1, CLER[1], 36), wall)
        inner, outer_x = (x0 + 1, x0) if x0 < CX else (x0, x0 + 1)
        for z in (10, 15, 20, 25, 30, 35):
            for y in (CLER[0] + 1, CLER[1]):
                t.set(outer_x, y, z, None)
                t.set(inner, y, z, 'oceanexpansion:sea_glass_pane[north=true,south=true]' if r.random() < 0.7 else 'water')

    # -- roofs: the aisles' lean-to roofs, and what is left of the nave's ------------------------------------------
    for z in range(5, APSE + 2):
        for side in (0, 1):
            X = (lambda x: x) if side == 0 else m
            up, down = ('east', 'west') if side == 0 else ('west', 'east')
            if z <= 36: t.fill((X(3), ARCH, z), (X(6), ARCH, z), wall)
            for x in (1, 2, 3): t.set(X(x), BAND, z, f'dark_prismarine_stairs[facing={up}]')
            for x in (4, 5, 6):
                t.set(X(x), BAND, z, 'prismarine_bricks')
                t.set(X(x), BAND + 1, z, f'dark_prismarine_stairs[facing={up}]')
            span = RIBS.get(z, False)
            if z not in ROOFED and span is False: continue
            for x, y in ROOF.items():
                if x == 14 and side == 1: continue
                if span not in (None, False) and not span[0] <= X(x) <= span[1]: continue
                if x in (13, 14): s = 'dark_prismarine_slab[type=bottom]'
                else: s = f'dark_prismarine_stairs[facing={up}]'
                if z in RIBS and z not in ROOFED: s = 'dark_prismarine'                # a rib: solid stone
                t.set(X(x), y, z, s)
            if z <= 36:
                for x, y in VAULT.items():
                    if x == 14 and side == 1: continue
                    if span not in (None, False) and not span[0] <= X(x) <= span[1]: continue
                    if x <= 11: t.set(X(x), y, z, f'prismarine_brick_stairs[facing={down},half=top]')
                    else: t.set(X(x), y, z, 'prismarine_bricks')
    # the back gable has fallen in above the eye
    for x in range(8, 21):
        for y in range(17, H):
            if abs(x - 13) <= (y - 16) * 1.3 + r.random() * 0.8:
                for z in range(APSE - 2, APSE + 2):
                    if t.get(x, y, z) is not None: t.set(x, y, z, 'water' if z < APSE else None)

    # -- the facade: two battered pylons and the stone bay with the great door and the eye -----------------------
    for x0, x1 in ((1, 6), (22, 27)):
        t.fill((x0, 4, 1), (x1, 25, 4), lambda x, y, z: stone() if y <= 11 else 'dark_prismarine'
               if y in (12, 18, 24) else wall())
        edge, step = (x0, 1) if x0 == 1 else (x1, -1)
        t.fill((edge, 19, 1), (edge, 25, 4), None)                                   # battered sides
        t.fill((edge + step, 24, 1), (edge + step, 25, 4), None)
        for x in range(x0, x1 + 1):                                                  # merlons
            if t.get(x, 25, 2) and (x - x0) % 2 == 1:
                t.set(x, 26, 2, 'dark_prismarine'); t.set(x, 26, 3, 'dark_prismarine')
        sx = 3 if x0 == 1 else 25                                                    # a tall slot in each face
        for y in range(12, 21): t.set(sx, y, 1, 'water')
        t.set(sx, 12, 1, 'sea_pickle[pickles=3]')
        t.set(sx, 21, 1, 'sea_lantern')
        t.set(sx - 1, 21, 1, 'dark_prismarine_stairs[facing=east,half=top]')
        t.set(sx + 1, 21, 1, 'dark_prismarine_stairs[facing=west,half=top]')
    t.fill((7, 4, 2), (21, 24, 4), stone)
    t.fill((7, 25, 2), (21, 25, 4), 'dark_prismarine')
    for x in range(7, 22):
        t.set(x, 24, 1, 'dark_prismarine_stairs[facing=south,half=top]')          # cornice over the eye
    for x, s in ((12, 'dark_prismarine_slab[type=bottom]'), (13, 'dark_prismarine'), (14, 'sea_lantern'),
                 (15, 'dark_prismarine'), (16, 'dark_prismarine_slab[type=bottom]')):
        t.set(x, 26, 3, s)                                                            # the crest
    for x in (7, 21):                                                                # dark pilasters by the door
        for y in range(10, 17): t.set(x, y, 2, 'dark_prismarine')
    # the great door: 7 wide, a stepped arch, its lower rows silted up
    for z in (2, 3, 4):
        for y in range(7, 17):
            t.set(10, y, z, 'dark_prismarine'); t.set(18, y, z, 'dark_prismarine')
        t.fill((11, 7, z), (17, 14, z), 'water')
        t.fill((12, 15, z), (16, 15, z), 'water')
        t.set(11, 15, z, 'dark_prismarine_stairs[facing=west,half=top]')
        t.set(17, 15, z, 'dark_prismarine_stairs[facing=east,half=top]')
        t.fill((13, 16, z), (15, 16, z), 'water')
        t.set(12, 16, z, 'dark_prismarine_stairs[facing=west,half=top]')
        t.set(16, 16, z, 'dark_prismarine_stairs[facing=east,half=top]')
        t.fill((9, 17, z), (19, 17, z), 'dark_prismarine')
    _eye(t, CX, 20, 2, sclera='prismarine_bricks')
    t.set(9, 12, 4, 'sea_lantern'); t.set(19, 12, 4, 'sea_lantern')                 # inside, either side of the door

    # -- the sunken sanctum: niches, the altar, the second eye ---------------------------------------------------
    for x, f in ((8, 'east'), (20, 'west')):
        for z in ((32, 34) if x == 8 else (32, 35)):
            t.set(x, 2, z, 'water')
            t.set(x, 3, z, 'dark_prismarine')
            t.pot(x, 1, z, f, loot='temple/offering')
        t.set(x, 3, 33, 'sea_lantern')
    t.fill((11, 1, 34), (17, 1, 34), 'prismarine_brick_stairs[facing=south]')     # the dais
    t.fill((11, 1, 35), (11, 1, 36), 'prismarine_brick_stairs[facing=east]')
    t.fill((17, 1, 35), (17, 1, 36), 'prismarine_brick_stairs[facing=west]')
    t.fill((12, 1, 35), (16, 1, 36), 'dark_prismarine')
    # the altar: a table of dark stone over the chest; the relic laid on top
    t.set(13, 2, 35, 'dark_prismarine'); t.set(15, 2, 35, 'dark_prismarine')
    t.chest(14, 2, 35, 'north', 'temple/altar')
    t.fill((13, 3, 35), (15, 3, 35), 'dark_prismarine_slab[type=top]')
    t.item_frame(14, 4, 35, 'up', 'trident')
    t.set(13, 4, 35, 'sea_pickle[pickles=2]'); t.set(15, 4, 35, 'sea_pickle[pickles=1]')
    t.fill((13, 2, 36), (15, 3, 36), 'dark_prismarine')
    t.set(13, 4, 36, 'dark_prismarine_stairs[facing=east]'); t.set(15, 4, 36, 'dark_prismarine_stairs[facing=west]')
    t.set(14, 4, 36, 'dark_prismarine')
    for x in (12, 16):
        t.set(x, 2, 36, 'dark_prismarine'); t.set(x, 3, 36, 'sea_lantern')
    _eye(t, CX, 12, APSE, sclera='prismarine_bricks')
    for z in range(PIT + 5, 37):                                                     # glow lichen on the old walls
        for x, face in ((9, 'west'), (19, 'east')):
            for y in (3, 4, 5):
                if is_water(t, x, y, z) and r.random() < 0.3: t.set(x, y, z, f'glow_lichen[{face}=true]')

    # -- the reliquary: sealed behind the dark wall, a crack beside the altar -----------------------------------
    t.fill((7, 0, APSE + 2), (17, 4, 42), 'dark_prismarine')
    t.flood((8, 1, 39), (16, 3, 41))
    for p in ((9, 1, 37), (10, 1, 37), (9, 2, 37), (10, 2, 37), (10, 3, 37), (9, 1, 38), (10, 1, 38), (9, 2, 38),
              (10, 2, 38)):
        t.set(*p, 'water')
    for p in ((11, 3, 37), (8, 2, 37), (9, 3, 37), (11, 1, 37)):
        t.set(*p, 'cracked_stone_bricks')
    t.set(8, 1, 37, 'mossy_stone_bricks')
    t.fill((16, 1, 39), (16, 1, 41), 'dark_prismarine')
    for z, sherds in ((39, ['brick', 'brick', 'brick', 'angler_pottery_sherd']),
                      (40, ['brick', 'mourner_pottery_sherd', 'flow_pottery_sherd', 'prize_pottery_sherd']),
                      (41, ['brick', 'brick', 'brick', 'heart_pottery_sherd'])):
        t.pot(16, 2, z, 'west', loot='temple/offering', sherds=sherds)
    t.sign(13, 2, 41, ['WHAT THE TIDE', 'TAKES', 'THE EYE', 'KEEPS'], facing='north', wood='dark_oak')
    t.item_frame(11, 2, 41, 'north', 'nautilus_shell')
    t.set(12, 1, 40, 'skeleton_skull[rotation=6]')                                   # a thief who never left
    for p in ((10, 1, 39), (9, 1, 39), (9, 1, 40), (9, 2, 39)): t.set(*p, 'sand')
    t.set(8, 1, 41, 'sea_pickle[pickles=3]'); t.set(15, 1, 39, 'sea_pickle[pickles=2]')
    t.set(14, 3, 40, 'glow_lichen[up=true]'); t.set(8, 3, 39, 'glow_lichen[up=true,west=true]')

    # -- the aisles: offering niches, windows -----------------------------------------------------------------------
    for x, f in ((2, 'east'), (26, 'west')):
        for z in (10, 15, 20):
            t.set(x, 8, z, 'water')
            t.set(x, 9, z, 'dark_prismarine')
            if (x, z) in ((2, 15), (26, 20)): t.set(x, 7, z, 'sea_pickle[pickles=3]')
            else: t.pot(x, 7, z, f, loot='temple/offering')
        xo = 1 if x == 2 else 27
        for z in (10, 15, 20, 25, 30, 35):                                         # narrow windows
            for y in (10, 11):
                t.set(xo, y, z, None); t.set(x, y, z, 'water')

    # -- the fall: aisle roofs caved in, the toppled column, the breach, the broken pylon ------------------------
    def hole(x0, x1, z0, z1, y0, ragged=0.35):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        rx, rz = (x1 - x0) / 2 + 0.5, (z1 - z0) / 2 + 0.5
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                d = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
                if d > 1 or (d > 0.55 and r.random() < ragged): continue
                for y in range(y0, H):
                    if t.get(x, y, z) is not None: t.set(x, y, z, 'water' if y < BAND + 2 else None)
    hole(18, 26, 14, 21, ARCH)         # the east arcade and aisle roof over the toppled column
    hole(4, 8, 30, 35, ARCH, 0.5)      # the west gallery's roof where its column fell
    # the toppled column: the east column of the third pair broke at y 10 and fell across the nave
    for x0, x1, z0 in ((16, 18, 17), (12, 14, 18)):
        t.fill((x0, 7, z0), (x1, 8, z0 + 1), stone)
    t.fill((10, 7, 17), (11, 7, 18), 'dark_prismarine')
    t.set(10, 8, 17, 'dark_prismarine_stairs[facing=east,half=bottom]'); t.set(11, 8, 18, 'dark_prismarine_slab[type=bottom]')
    t.set(15, 7, 17, 'stone_brick_slab[type=bottom]')
    # the west gallery column broke at y 11 and fell into the sanctum at the foot of the stair
    t.fill((10, 1, 31), (11, 2, 32), stone)
    t.fill((13, 1, 31), (14, 2, 32), stone)
    t.set(16, 1, 31, 'dark_prismarine'); t.set(17, 1, 31, 'dark_prismarine_stairs[facing=west]')
    t.set(16, 1, 32, 'dark_prismarine_slab[type=bottom]')
    # the east gallery's outer wall breached: the way in for the reef
    for z in range(27, 34):
        for y in range(9, ARCH + 3):
            if abs(z - 30) + max(0, y - 12) * 1.2 + max(0, 10 - y) * 2 <= 2.8 + r.random() * 0.9:
                for x in (26, 27): t.set(x, y, z, 'water' if y <= GT else None)
    hole(22, 27, 27, 33, ARCH, 0.4)
    # the east pylon's top has broken away
    for x in range(22, 28):
        for y in range(18, H):
            if y >= 27 - (x - 21) - (1 if r.random() < 0.3 else 0):
                for z in range(1, 5): t.set(x, y, z, None)
    for x, y, z, s in ((23, 17, 6, 'dark_prismarine'), (24, 17, 7, 'prismarine_bricks'), (25, 16, 6, 'dark_prismarine_slab[type=bottom]'),
                       (22, 17, 8, 'dark_prismarine_stairs[facing=north]'), (26, 10, 0, 'dark_prismarine'),
                       (24, 10, 0, 'prismarine_bricks'), (25, 11, 0, 'prismarine_brick_slab[type=bottom]')):
        if t.get(x, y, z) is None or t.name_at(x, y, z) == 'minecraft:water': t.set(x, y, z, s)

    # -- the sea comes in: drifts, rubble, coral, kelp, pickles ---------------------------------------------------
    # sand through the door and down into the nave (below the floor line, so it is really there)
    drift = {0: (11, 17, 9), 1: (11, 17, 9), 2: (11, 17, 9), 3: (11, 17, 9), 4: (11, 17, 9), 5: (11, 17, 8),
             6: (11, 17, 8), 7: (11, 17, 7), 8: (12, 16, 7), 9: (13, 15, 7), 10: (14, 14, 7)}
    for z, (x0, x1, top) in drift.items():
        for x in range(x0, x1 + 1):
            h = top - (1 if (x in (x0, x1) and z >= 5) else 0) - (1 if r.random() < 0.15 and z >= 5 else 0)
            for y in range(7, h + 1):
                if t.name_at(x, y, z) in (None, 'minecraft:water'): t.set(x, y, z, 'sand')
    t.set(14, 10, 1, 'seagrass'); t.set(12, 10, 0, 'tall_seagrass[half=lower]'); t.set(12, 11, 0, 'tall_seagrass[half=upper]')
    for x in (3, 25):                                                                # sand along the aisle walls
        for z in range(5, 37):
            h = r.choice((0, 0, 0, 1, 1, 2))
            for y in range(7, 7 + h):
                if is_water(t, x, y, z): t.set(x, y, z, 'sand')
    for x in range(3, 7):                                                            # banked up in the west gallery
        for z in range(33, 37):
            h = (6 - x) + (z - 33) // 2 + r.choice((0, 0, 1))
            for y in range(7, min(7 + h, 10)):
                if is_water(t, x, y, z): t.set(x, y, z, 'sand')
    for p in ((18, 1, 35), (19, 1, 35), (19, 1, 36), (18, 1, 36), (19, 2, 36), (19, 1, 34), (9, 1, 36), (10, 1, 36)):
        if is_water(t, *p): t.set(*p, 'sand')
    # kelp: up through the open roof, and in the sanctum
    for x, y0, z, h in ((10, 7, 15, 14), (18, 7, 14, 12), (12, 7, 21, 15), (23, 7, 17, 9), (24, 7, 29, 8),
                        (18, 1, 33, 20), (10, 1, 33, 18), (16, 7, 23, 6), (5, 7, 29, 7), (11, 7, 11, 13)):
        kelp(t, x, y0, z, h)
    rubble(t, 9, 19, 13, 22, 7, 22)
    rubble(t, 22, 25, 14, 21, 7, 10)
    rubble(t, 9, 19, 31, 36, 1, 10)
    rubble(t, 3, 6, 28, 33, 7, 8)
    rubble(t, 22, 25, 26, 34, 7, 6)
    rubble(t, 9, 19, 33, 36, 1, 6)
    for _ in range(30):                                                              # pickles on the floors
        x, z = r.randint(3, 25), r.randint(5, 36)
        for y in (7, 8, 9, 10):
            if is_water(t, x, y, z) and solid_below(t, x, y, z):
                t.set(x, y, z, f'sea_pickle[pickles={r.randint(1, 4)}]'); break
    # the reef coming in through the breach
    for x in range(22, 28):
        for z in range(25, 36):
            for y in range(8, 18):
                n = t.name_at(x, y, z)
                if n and ('prismarine' in n or 'stone' in n) and not n.endswith(('_stairs', '_slab', '_wall', 'pane')) \
                        and abs(z - 30) + abs(x - 26) * 0.7 <= 4 and r.random() < 0.45:
                    t.set(x, y, z, f'{r.choice(CORALS)}_coral_block')
    for x in range(21, 29):
        for z in range(25, 36):
            for y in range(7, 18):
                if not is_water(t, x, y, z) and not (x == 28 and t.get(x, y, z) is None and y > GT): continue
                if abs(z - 30) + abs(x - 25) * 0.6 > 5: continue
                if solid_below(t, x, y, z) and r.random() < 0.45:
                    t.set(x, y, z, r.choice([f'{c}_coral' for c in CORALS] + [f'{c}_coral_fan' for c in CORALS]))
                    continue
                for f, (dx, dz) in (('east', (-1, 0)), ('west', (1, 0)), ('south', (0, -1)), ('north', (0, 1))):
                    n = t.name_at(x + dx, y, z + dz) if t.inside(x + dx, y, z + dz) else None
                    if n and ('coral_block' in n or 'prismarine' in n) and not n.endswith(('_stairs', '_slab', '_wall', 'pane')) \
                            and r.random() < 0.18:
                        t.set(x, y, z, f'{r.choice(CORALS)}_coral_wall_fan[facing={f}]'); break
    # coral on the facade's tops and along the ribs and roof edges
    for x in range(1, 28):
        for z in range(1, L):
            for y in range(BAND, H - 1):
                if t.get(x, y + 1, z) is None and t.name_at(x, y, z) in ('minecraft:dark_prismarine', 'minecraft:prismarine_bricks') \
                        and r.random() < (0.3 if z <= 4 else 0.06):
                    t.set(x, y + 1, z, r.choice([f'{c}_coral' for c in CORALS] + [f'{c}_coral_fan' for c in CORALS]))
    # barnacles crusting the facade's foot and the column bases
    for x in range(1, 28):
        for y in (10, 11, 12):
            if t.get(x, y, 0) is None and t.get(x, y, 1) and r.random() < 0.35:
                t.set(x, y, 0, 'oceanexpansion:barnacles[facing=north]')
    for c in COLS:
        for x, f in ((9, 'east'), (19, 'west')):
            for z in (c, c + 1):
                if is_water(t, x, 8, z) and r.random() < 0.6: t.set(x, 8, z, f'oceanexpansion:barnacles[facing={f}]')
    seagrass(t, 3, 25, 5, 36, 7, 0.06)
    seagrass(t, 9, 19, PIT + 5, 36, 1, 0.08)

    # -- the haunt, a warning, fish, and how you get in -----------------------------------------------------------
    t.haunt(CX, 7, 14, 'guardians')
    t.set(CX, 8, 14, 'water'); t.set(CX, 9, 14, 'water')
    t.sign(9, 9, 22, ["Three of 'em", 'woke when I', 'swam past.', 'Go round. -K.'], facing='east', wood='dark_oak')
    t.creature(12, 12, 9, 'minecraft:tropical_fish', nbt={'Variant': 65536})
    t.creature(24, 11, 30, 'minecraft:tropical_fish', nbt={'Variant': 67699456})
    t.creature(15, 5, 33, 'minecraft:tropical_fish', nbt={'Variant': 67764993})
    t.entrance(CX, 10, 0)
    t.entrance(28, 11, 30)

    # -- bedding: the top of the sea floor around and over the buried parts turns to temple sand -----------------
    for x in range(W):
        for z in range(L):
            for y in (GT - 1, GT):
                if t.get(x, y, z) is None:
                    t.set(x, y, z, _pick(r, [('sand', 14), ('gravel', 2), ('clay', 1)]))
    t.shell((7, 0, APSE + 2), (17, 4, 42), lambda x, y, z: _pick(r, [('sand', 3), ('gravel', 2), ('clay', 1)]))
    # a little life and fallen stone on the sand outside
    for x in range(W):
        for z in range(L):
            if t.get(x, GT + 1, z) is None and t.name_at(x, GT, z) == 'minecraft:sand':
                v = r.random()
                if v < 0.10: t.set(x, GT + 1, z, 'seagrass')
                elif v < 0.13: t.set(x, GT + 1, z, f'sea_pickle[pickles={r.randint(1, 3)}]')
                elif v < 0.17 or (z >= APSE + 2 and 9 <= x <= 19 and v < 0.35): t.set(x, GT + 1, z, _pick(r, DEBRIS[:5]))
    for x, z, h in ((0, 3, 8), (28, 9, 10), (0, 24, 6), (28, 40, 9), (2, 43, 7), (22, 44, 11), (0, 15, 12)):
        if t.name_at(x, GT + 1, z) in (None, 'minecraft:seagrass'):
            t.set(x, GT + 1, z, None)
            kelp(t, x, GT + 1, z, h)
    return t


# -- the outer precinct --------------------------------------------------------------------------------------------

def colonnade():
    """Three columns of the precinct's colonnade: two still carry a length of lintel, the third has fallen."""
    t = Template('temple/colonnade', (7, 16, 13), wet=True)
    r = t.rng
    wall, stone = _materials(t)
    # the stylobate, buried in the floor (y 1 is the top of the sea floor), and its raised course
    t.fill((0, 0, 0), (6, 1, 12), lambda x, y, z: None if (x in (0, 6) or z in (0, 12)) and r.random() < 0.4
           else ('sand' if y == 1 and (x in (0, 6) or z in (0, 12)) else stone()))
    t.fill((1, 2, 0), (5, 2, 12), lambda x, y, z: None if z in (0, 12) and r.random() < 0.5 else stone())
    for z in range(13):
        if t.get(1, 2, z) and r.random() < 0.8: t.set(0, 2, z, 'stone_brick_stairs[facing=east]')
        if t.get(5, 2, z) and r.random() < 0.7: t.set(6, 2, z, 'stone_brick_stairs[facing=west]')

    def fluted(cz, top):
        for x in (2, 3, 4):
            for z in (cz - 1, cz, cz + 1):
                t.set(x, 3, z, 'dark_prismarine' if (x == 3 or z == cz) else 'prismarine_brick_slab[type=bottom]')
        for y in range(4, top):
            t.set(3, y, cz, 'chiseled_stone_bricks' if y in (7, 11) else stone())
            t.set(2, y, cz, 'stone_brick_wall[east=tall]'); t.set(4, y, cz, 'stone_brick_wall[west=tall]')
            t.set(3, y, cz - 1, 'stone_brick_wall[south=tall]'); t.set(3, y, cz + 1, 'stone_brick_wall[north=tall]')

    for cz in (2, 7):
        fluted(cz, 13)
        for x in (2, 3, 4):
            for z in (cz - 1, cz, cz + 1):
                t.set(x, 13, z, 'dark_prismarine' if (x == 3 or z == cz) else 'dark_prismarine_slab[type=top]')
    # the lintel they still carry, broken off past the second column
    t.fill((2, 14, 0), (4, 14, 9), 'prismarine_bricks')
    t.fill((2, 15, 0), (4, 15, 8), 'dark_prismarine_slab[type=bottom]')
    t.set(2, 14, 9, None); t.set(4, 14, 9, 'prismarine_brick_stairs[facing=north,half=top]')
    t.set(3, 15, 8, None); t.set(2, 14, 0, 'prismarine_brick_stairs[facing=south,half=top]')
    t.set(3, 14, 4, 'dark_prismarine'); t.set(3, 14, 5, 'dark_prismarine')         # a carved band mid-span
    # the third column: a stump, its drums and capital fallen beside the platform
    fluted(11, 7)
    t.set(3, 7, 11, stone()); t.set(2, 6, 11, None); t.set(3, 6, 12, None)
    t.fill((5, 3, 3), (6, 4, 5), stone)
    t.fill((5, 3, 7), (6, 4, 9), stone)
    t.set(6, 4, 9, 'stone_brick_slab[type=bottom]'); t.set(5, 4, 3, 'mossy_stone_brick_slab[type=bottom]')
    t.set(0, 3, 10, 'dark_prismarine'); t.set(0, 3, 11, 'dark_prismarine_stairs[facing=north]')
    t.set(1, 3, 9, 'prismarine_bricks'); t.set(0, 3, 8, 'prismarine_brick_slab[type=bottom]')
    # life on the stones
    for x in range(7):
        for z in range(13):
            for y in range(2, 16):
                if t.get(x, y, z) is None and solid_below(t, x, y, z) and r.random() < 0.18:
                    v = r.random()
                    t.set(x, y, z, f'sea_pickle[pickles={r.randint(1, 3)}]' if v < 0.3 else
                          f'{r.choice(CORALS)}_coral' if v < 0.65 else 'seagrass')
                    break
    for x, z, h in ((1, 4, 9), (5, 12, 6), (4, 10, 11)):
        kelp(t, x, 3, z, h)
    if t.get(4, 8, 2): t.set(5, 8, 2, 'oceanexpansion:barnacles[facing=east]')
    t.set(1, 5, 7, 'oceanexpansion:barnacles[facing=west]')
    t.set(2, 9, 6, 'tube_coral_wall_fan[facing=north]')
    return t


def obelisk():
    """An Old Tide eye obelisk on its plinth, leaning; its tip broke off and lies in the sand beside it."""
    t = Template('temple/obelisk', (9, 17, 7), wet=True)
    r = t.rng
    wall, stone = _materials(t)
    t.fill((1, 0, 1), (5, 1, 5), lambda x, y, z: 'sand' if y == 1 and x in (1, 5) and z in (1, 5) else wall())
    for x in range(1, 6):
        for z in range(1, 6):
            if x in (1, 5) or z in (1, 5):
                f = 'east' if x == 1 else 'west' if x == 5 else 'south' if z == 1 else 'north'
                if r.random() < 0.85: t.set(x, 2, z, f'prismarine_brick_stairs[facing={f}]')
            else:
                t.set(x, 2, z, 'dark_prismarine')
    t.fill((2, 3, 2), (4, 3, 4), 'dark_prismarine')
    t.fill((2, 4, 2), (4, 10, 4), wall)
    t.fill((3, 11, 2), (5, 13, 4), wall)                                       # it leans east
    t.fill((2, 10, 2), (4, 10, 4), 'dark_prismarine')
    t.fill((4, 14, 2), (5, 14, 3), 'prismarine')                               # broken off
    t.set(5, 14, 4, 'prismarine_brick_slab[type=bottom]'); t.set(3, 14, 3, 'prismarine_brick_slab[type=bottom]')
    for zz in (2, 4):                                                          # the eye, on both faces
        t.set(3, 7, zz, 'black_concrete')
        for x, y in ((2, 7), (4, 7), (3, 6), (3, 8)): t.set(x, y, zz, 'sea_lantern')
        for x, y in ((2, 6), (4, 6), (2, 8), (4, 8)): t.set(x, y, zz, 'dark_prismarine')
    # the tip, lying on the floor
    t.fill((6, 2, 4), (7, 2, 5), 'prismarine')
    t.fill((6, 3, 4), (7, 3, 5), 'dark_prismarine')
    t.set(8, 2, 4, 'dark_prismarine_stairs[facing=west]'); t.set(8, 2, 5, 'dark_prismarine_stairs[facing=west]')
    t.set(8, 3, 4, 'dark_prismarine_slab[type=bottom]')
    t.set(6, 2, 6, 'sand'); t.set(7, 2, 6, 'sand')
    for x, y, z, s in ((6, 4, 5, 'brain_coral'), (7, 4, 4, 'sea_pickle[pickles=2]'), (0, 2, 2, 'seagrass'),
                       (8, 2, 1, 'seagrass'), (2, 2, 6, 'sea_pickle[pickles=1]'), (6, 4, 4, 'tube_coral_fan')):
        t.set(x, y, z, s)
    for y in range(2, 9): t.set(0, y, 5, 'kelp_plant')
    t.set(0, 9, 5, 'kelp')
    t.set(1, 5, 3, 'oceanexpansion:barnacles[facing=west]')
    t.set(5, 5, 3, 'oceanexpansion:barnacles[facing=east]')
    return t


def pieces():
    return [sanctum(), colonnade(), obelisk()]
