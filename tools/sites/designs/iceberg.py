"""The Frozen Hold: a huge iceberg with the expedition ship Northward locked inside it at the waterline. Her bow
and bowsprit stick out of one face, two masts out of the top; a crevasse on the other side climbs from the sea
into an ice vault over her deck. Below deck everything is dry, frozen and very quiet."""
import math
from functools import lru_cache

from kit import Template
from loot import item, empty, pool, rolls, sea_chart, treasure_map, enchanted, named, WORN
from .ship_parts import Frame, Hull, Shipwright, voxelize, crop, check_sealed, connect, is_full

KEY = 'iceberg'
NAME = 'The Frozen Hold'
FEATURES = [
    'a huge iceberg of packed and blue ice, snow-capped, with powder-snow cracks on top',
    "the Northward locked in the ice at the waterline: her bow, bowsprit and bear figurehead jut from one face, "
    'two frozen masts with a yard and a stiff torn sail from the top',
    'a crevasse climbs from the sea into an ice vault over her deck',
    "below deck, dry and frozen: the crew's bunks and their last meal, the hold, the captain's cabin",
    "Captain Arvid Strand's log, which ends mid-sentence; the frozen crew below deck",
    'a drifting floe with the boat two of the crew tried to sail south in',
]
SITE = {'anchor': 'surface', 'depth': (10, 40), 'flatness': 12, 'radius': 22, 'weight': 2, 'inhabited': False,
        'biomes': ['frozen_ocean', 'deep_frozen_ocean', 'cold_ocean', 'deep_cold_ocean']}

SUB = 8                       # rows of the berg under the sea (template y 0..7); y 8 is sea level
LOOT_TABLES = {
    # Captain Strand's chest: the expedition's purse and instruments (the site's prize).
    'iceberg/captain': [
        pool(rolls(2, 4), [item('emerald', 8, 2, 6), item('gold_ingot', 5, 1, 4), item('paper', 4, 2, 6),
                           item('book', 3, 1, 2), item('iron_ingot', 4, 1, 3)]),
        pool(1, [item('diamond', 3, 1, 2), empty(2)]),
        pool(1, [item('spyglass', 3, extra=named("Strand's Spyglass")), item('compass', 3), item('clock', 2),
                 item('oceanexpansion:storm_glass', 2)]),
        pool(1, [item('book', 3, extra=enchanted(20, 30)), item('leather_chestplate', 2, extra=enchanted(15, 25)),
                 item('iron_sword', 2, extra=enchanted(10, 25)), empty(2)]),
        pool(1, [sea_chart(2), treasure_map(1), empty(2)]),
    ],
    # Expedition stores in the hold.
    'iceberg/hold': [
        pool(rolls(3, 6), [item('coal', 8, 3, 9), item('iron_ingot', 5, 1, 4), item('bread', 6, 2, 5),
                           item('cooked_cod', 5, 2, 5), item('dried_kelp', 4, 3, 9), item('leather', 5, 1, 4),
                           item('snowball', 3, 4, 12), item('lantern', 2), item('lead', 2, 1, 2), item('rabbit_hide', 3, 1, 4),
                           item('iron_pickaxe', 2, extra=WORN), item('shears', 2), item('emerald', 2, 1, 3)]),
        pool(1, [item('powder_snow_bucket', 2), item('leather_boots', 2, extra=enchanted(5, 15)), sea_chart(1), empty(4)]),
    ],
    # The crew's barrels and bundles.
    'iceberg/crew': [
        pool(rolls(2, 4), [item('bread', 6, 1, 3), item('cooked_cod', 5, 1, 3), item('candle', 3, 1, 2),
                           item('string', 4, 1, 3), item('leather', 3, 1, 2), item('paper', 3, 1, 3), item('coal', 4, 1, 4),
                           item('iron_nugget', 4, 2, 6), item('emerald', 1), item('leather_helmet', 2, extra=WORN),
                           item('snowball', 3, 2, 6)]),
    ],
}

LOG = [
    "The Northward.\nDay 1 of the ice.\n\nThe passage closed\nbehind us in the\nnight. The pack\nhas us now.\nWe are well found\nand in good heart.\n\n  - Arvid Strand",
    "Day 9.\nThe floe is a\nmountain now, and\nwe are in its\nheart. The hull\ngroans at night.\nThe men call the\nice 'the Landlord'.\nI do not laugh.",
    "Day 23.\nRations halved.\nTomas and Brekke\nwalked out over\nthe ice for the\nsouth, with the\nlast good boat.\nGod keep them.",
    "Day 41.\nThe cold gets into\neverything: the\nink, the bread,\nthe men. Some of\nthem stand by the\nhull and listen.\nThey say they hear\nsomeone knocking.",
    "Day 50.\nThe men who went\ndown to look have\ncome back wrong.\nThey do not feel\nthe cold. They\nstand very still\nbelow, and watch\nthe hatch.",
    "Day 52.\nIf you find this,\ndo not go below\nafter dark. Do not\nanswer if they\ncall your name.\nThey are not my\nmen any longer.\nI am going to",
]

L = 24
MAIN, FORE = 11, 18
OX, OY, OZ = 6, 3, 18            # ship (0, 0, 0) -> template (6, 3, 18): keel at y 3, ship layer 5 at sea level


def shell(u, v, h, layer):
    if u < 1.2 and layer >= 4: return 'transom'
    if layer <= 4: return 'low'
    if layer == 8: return 'band'
    return 'side'


FAMILIES = {
    'low': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'side': {'full': 'dark_oak_planks', 'stairs': 'dark_oak_stairs', 'slab': 'dark_oak_slab'},
    'band': {'full': 'stripped_birch_log[axis=x]', 'stairs': 'birch_stairs', 'slab': 'birch_slab'},
    'transom': {'full': 'dark_oak_planks', 'stairs': 'dark_oak_stairs', 'slab': 'dark_oak_slab'},
    'deck': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'floor': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'bulk': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
}


def ship_model():
    return Hull(L, 3.8, 11, full=(.3, .6), stem=.93, transom=.8, bilge=(3.0, 6.0), stem_rise=7.0, keel_rise_from=.7,
                tumble=(8.0, .12, 6.0), bow_rake=2.0, stern_rake=1.0, skin=1.0, run=(3.0, 4.0), fine=.8,
                sheer=[(-5, 7, 15), (19.5, 40, 13)],
                decks=[(-5, 40, 1, 'floor'), (-5, 40, 5, 'deck'), (-5, 40, 9, 'deck'), (-5, 7, 13, 'deck'),
                       (19.5, 40, 11, 'deck')],
                bulkheads=[(6, 7, 10, 12, 'bulk'), (19.5, 20.5, 10, 10, 'bulk'), (19, 20, 1, 4, 'bulk')],
                shell=shell)


def _noise(x, y, z):
    return (math.sin(x * .55 + y * .31) + math.sin(z * .47 - y * .23 + 1.7) + math.sin((x + z) * .29 + 2.9)) / 3


# Ice masses: (centre, radii, sides) in template space; `sides` > 2 squares the walls off into cliffs.
BLOBS = [((14, 3, 18), (15, 6.5, 15), 2.0),      # the wide underwater foot
         ((13, 12, 18), (13.5, 11, 13), 3.2),     # the main mass over the ship
         ((9, 17, 13), (6, 10, 6.5), 2.6),        # the peak
         ((24, 15, 11), (3.5, 8, 3.5), 2.4),      # a spire over the crevasse
         ((6, 15, 27), (3.5, 7, 4), 2.4),         # a spire over the stern
         ((20, 10, 26), (8, 8, 7), 2.8),          # a shoulder
         ((3, 9, 20), (5, 7, 8), 2.6),            # the stern lump
         ((16, 6, 6), (7, 5, 5), 2.6)]            # the crevasse side


@lru_cache(maxsize=None)
def in_berg(x, y, z):
    if y < 0: return False
    n = 1 + .13 * _noise(x, y, z)
    for (cx, cy, cz), (rx, ry, rz), p in BLOBS:
        r = math.sqrt(((x + .5 - cx) / rx) ** 2 + ((z + .5 - cz) / rz) ** 2)
        if r ** p + ((y + .5 - cy) / ry) ** 2 <= n * n: return True
    return False


def berg():
    t = Template('iceberg/berg', (40, 34, 38), wet=True, waterline=SUB)
    rng = t.rng
    f = Frame((OX, OY, OZ + .5))
    sw = Shipwright(t, f)
    P = sw.put
    model = ship_model()
    mats = voxelize(t, f, model, FAMILIES, 'air', ((-3, -5, 0), (27, 5, 16)))
    inside_ship = {c for c, b in t.blocks.items()}

    def at(u, v, h): return sw.at(u, v, h)

    def air(u, v, h): return t.name_at(*at(u, v, h)) == 'minecraft:air'

    def into(u, v, h, block):
        if air(u, v, h): return P(u, v, h, block)

    # The deck vault: the ice stands off the deck between the castle and the forecastle, an arched cave.
    for u in range(6, 21):
        for v in range(-5, 6):
            hw = model.half_width(u + .5, 10.5) + .6
            if abs(v) > hw: continue
            height = 4 - (abs(v) > 2) - (u in (6, 20))
            for layer in range(10, 10 + height):
                c = at(u, v, layer)
                if t.name_at(*c) is None: t.set(*c, 'air')
    # The crevasse: from the sea on the port side, up a snow stair, over the broken rail onto the deck.
    def step(z): return min(SUB + 4, SUB - 1 + max(0, (z - 4) // 2))
    for z in range(0, OZ - 2):
        floor = step(z)
        mid = 18.5 + 1.2 * math.sin(z * .6)
        for y in range(floor - 1, t.size[1]):
            half = 1.6 + max(0, y - floor) * .32 + .4 * math.sin(y * 1.3 + z)    # a V: wide at the top
            for x in range(math.floor(mid - half), math.ceil(mid + half)):
                if not t.inside(x, y, z) or t.name_at(x, y, z) is not None: continue
                if y < floor + 1:
                    if in_berg(x, y, z): t.set(x, y, z, 'snow_block')
                else:
                    t.set(x, y, z, 'air')
            if y == floor + 1 and step(z + 1) > floor and floor >= SUB:
                for x in range(math.floor(mid - half), math.ceil(mid + half)):
                    if t.name_at(x, y, z) == 'minecraft:air' and t.name_at(x, y - 1, z) == 'minecraft:snow_block':
                        t.set(x, y, z, 'snow[layers=4]')   # half steps
    for u in (12, 13, 14):                       # the rail the ice broke away
        for v in (-3, -4):
            if t.name_at(*at(u, v, 10)) is not None: t.set(*at(u, v, 10), 'air')

    # Fill the berg: blue ice deep down, packed ice and clear ice through the body, snow on top.
    for x in range(t.size[0]):
        for z in range(t.size[2]):
            top = None
            for y in range(t.size[1] - 1, -1, -1):
                if not in_berg(x, y, z): continue
                if top is None: top = y
                if t.name_at(x, y, z) is not None: continue
                if y == top and y > SUB: b = 'snow_block'
                elif y < 3: b = 'blue_ice' if rng.random() < .55 else 'packed_ice'
                else:
                    r = rng.random() + .25 * _noise(z, x, y)
                    b = 'blue_ice' if r < .12 else 'ice' if r > .86 else 'packed_ice'
                t.set(x, y, z, b)
    # The bow below the sea where it juts out of the ice is frozen solid inside.
    for c, b in list(t.blocks.items()):
        if b[0] == 'minecraft:air' and c[1] < SUB + 1 and not in_berg(*c): t.set(*c, 'packed_ice')
    # Keep the whole berg dry (nothing inside it is under water).
    for c in list(t.blocks):
        if in_berg(*c) or c in inside_ship and c[1] >= SUB - 1: t.dry.add(c)

    # Masts out of the top, frozen; bowsprit and the bear figurehead out of the east face.
    sw.line((MAIN + .5, 0, 1.5), (MAIN + .5, 0, 26.5), 'stripped_spruce_log[axis={axis}]')
    P(MAIN, 0, 27, 'spruce_fence')
    yard = sw.line((MAIN + .5, -5.4, 23.5), (MAIN + .5, 5.4, 22.7), 'stripped_spruce_log[axis={axis}]')
    for c in yard:
        if abs(c[2] - OZ) >= 4: t.set(*c, 'spruce_fence')
        above = (c[0], c[1] + 1, c[2])
        if rng.random() < .6 and t.name_at(*above) is None and 'log' in t.get(*c): t.set(*above, 'snow[layers=2]')
    for v in range(-4, 5):                       # the frozen main topsail, stiff and torn
        for layer in range(19, 22):
            c = at(MAIN + 1, v, layer)
            if t.name_at(*c) is None and rng.random() < .62 - .1 * (21 - layer):
                t.set(*c, rng.choice(['white_wool', 'white_wool', 'light_gray_wool']))
    sw.line((FORE + .5, 0, 1.5), (FORE + .5, 0, 21.5), 'stripped_spruce_log[axis={axis}]')
    P(FORE, 0, 22, 'spruce_fence')
    for side in (-1, 1):
        sw.line((FORE + .5, side * 1.0, 20.5), (FORE + .5, side * 3.5, 17.5), 'dark_oak_fence')
        sw.line((MAIN + .5, side * 1.0, 25.5), (MAIN + .5, side * 4.0, 21.0), 'dark_oak_fence')
    sw.line((22.5, 0, 11.5), (30.5, 0, 14.5), 'stripped_spruce_log[axis={axis}]')
    P(31, 0, 15, 'spruce_fence')
    for u, h in ((24, 9), (24, 10), (25, 10)):   # the bear: a white head with a black nose
        P(u, 0, h, 'white_wool')
    P(25, -1, 10, 'white_wool'); P(25, 1, 10, 'white_wool')
    P(26, 0, 10, 'black_wool'); P(24, -1, 11, 'white_wool'); P(24, 1, 11, 'white_wool')
    for u in range(20, 25):                      # icicles and rime on the jutting bow
        for v in (-3, 3):
            c = at(u, v, 9)
            if t.name_at(*c) is None and rng.random() < .4: t.set(*c, 'ice')

    # The captain's cabin in the sterncastle.
    for layer in (10, 11):
        P(6, 0, layer, 'air')
    for c, m in list(mats.items()):              # frosted stern windows (ice behind them)
        if m != 'transom': continue
        u, v, h = f.to_ship(c[0] + .5, c[1] + .5, c[2] + .5)
        if math.floor(h) in (10, 11) and 1 <= abs(round(v)) <= 2: t.set(*c, 'white_stained_glass_pane')
    t.lectern(*at(3, 0, 10), 'east', 'Log of the Northward', 'Capt. Arvid Strand', LOG)
    t.chest(*at(1, -2, 10), 'east', 'iceberg/captain')
    t.bed(*at(2, 2, 10), 'west', 'light_gray')
    into(5, -2, 10, 'cartography_table')
    into(4, -2, 10, 'spruce_stairs[facing=east,half=bottom]')
    into(0, 0, 12, 'soul_lantern[hanging=true]')
    into(5, 2, 10, 'barrel[facing=up,open=false]')
    t.item_frame(*at(5, 0, 12), 'west', 'compass')
    # The crew deck: bunks, the table with the last meal, the stove, the tally. The frozen crew wait here.
    for u, v in ((3, -2), (3, 2), (8, -2), (8, 2)):
        t.bed(*at(u + 1, v, 6), 'west', 'white')
    for u, v in ((9, 0), (10, 0)):
        into(u, v, 6, 'spruce_slab[type=top]')
    into(9, 0, 7, 'cake[bites=4]')
    into(10, 0, 7, 'candle[candles=1,lit=false]')
    into(9, -1, 6, 'spruce_stairs[facing=south,half=bottom]')
    into(11, 1, 6, 'spruce_stairs[facing=west,half=bottom]')
    into(15, -2, 6, 'furnace[facing=east,lit=false]')
    into(16, -2, 6, 'cauldron')
    t.barrel(*at(15, 2, 6), 'up', 'iceberg/crew')
    t.barrel(*at(17, 2, 6), 'up', 'iceberg/crew')
    into(17, -1, 6, 'barrel[facing=up,open=false]')
    t.sign(*at(6, -2, 6), ['Iced in.', 'Day 52.', '|||| |||| ||||', 'Strand: spring'], facing='east', wall=False)
    into(12, 0, 8, 'soul_lantern[hanging=true]')
    t.haunt(*at(14, 0, 6), 'frozen_crew')
    for (u, v) in ((5, 0), (7, 1), (13, -1), (17, 0), (12, 2)):
        c = at(u, v, 6)
        if t.name_at(*c) == 'minecraft:air' and is_full(t.name_at(c[0], c[1] - 1, c[2]) or 'minecraft:air'):
            t.set(*c, f'snow[layers={rng.randint(1, 3)}]')
    # Companionway from the deck vault down to the crew deck, and a ladder-stair to the hold.
    for u in (12, 13, 14):
        P(u, 1, 9, 'air')
    for i, u in enumerate((12, 13, 14)):
        P(u, 1, 6 + i, 'spruce_stairs[facing=east,half=bottom]')
    for u in (8, 9, 10):
        P(u, -1, 5, 'air')
    for i, u in enumerate((10, 9, 8)):
        P(u, -1, 2 + i, 'spruce_stairs[facing=west,half=bottom]')
    # The hold: stores, the expedition's sledge, coal, and the berg pushing in through the starboard side.
    t.chest(*at(14, 0, 2), 'west', 'iceberg/hold')
    for u, v, b in ((4, -1, 'coal_block'), (4, 0, 'coal_block'), (5, -1, 'coal_block'), (4, -1, 'coal_block'),
                    (6, 1, 'barrel[facing=up,open=false]'), (7, 1, 'barrel[facing=up,open=false]'),
                    (12, -1, 'barrel[facing=up,open=false]'), (16, -1, 'spruce_planks'), (17, -1, 'spruce_planks'),
                    (13, 2, 'barrel[facing=north,open=false]')):
        into(u, v, 2, b)
    into(4, 0, 3, 'coal_block')
    for u, v, layer, b in ((6, 1, 3, 'barrel[facing=up,open=false]'), (6, 2, 2, 'barrel[facing=up,open=false]'),
                           (8, 2, 2, 'brown_wool'), (9, 2, 2, 'brown_wool'), (8, 2, 3, 'light_gray_wool'),
                           (15, -2, 2, 'barrel[facing=up,open=false]'), (15, -2, 3, 'barrel[facing=up,open=false]'),
                           (16, -2, 2, 'spruce_planks'), (17, -2, 2, 'spruce_slab[type=bottom]'),
                           (11, -2, 2, 'iron_chain[axis=x]'), (12, -2, 2, 'iron_chain[axis=x]'),
                           (18, 0, 2, 'barrel[facing=west,open=false]'), (5, 1, 2, 'snow[layers=2]'),
                           (13, -1, 2, 'snow[layers=1]')):
        into(u, v, layer, b)
    for u in range(5, 10):                        # spare spars lashed along the port side
        into(u, -2, 2, 'stripped_spruce_log[axis=x]')
    into(12, 0, 4, 'iron_chain[axis=y]')
    into(16, -1, 3, 'spruce_slab[type=bottom]')
    for u in (10, 11, 12):                       # the sledge
        into(u, 1, 2, 'spruce_slab[type=bottom]')
    into(13, 1, 2, 'spruce_stairs[facing=west,half=bottom]')
    into(17, 1, 2, 'skeleton_skull[rotation=6]')
    for u in (14, 15, 16):                       # blue ice shoving through the planking
        for h in (2, 3):
            c = at(u, 2, h)
            if t.name_at(*c) in ('minecraft:air',) or t.name_at(*c) and 'planks' in t.name_at(*c): t.set(*c, 'blue_ice')
        c = at(u, 3, 3)
        t.set(*c, 'blue_ice')
    # Ice and snow inside: rime on the deck, icicles in the vault.
    for (u, v) in ((8, -2), (9, 3), (15, 2), (17, -3), (11, -2), (19, 1), (7, 0), (16, 0)):
        c = at(u, v, 10)
        if t.name_at(*c) == 'minecraft:air' and is_full(t.name_at(c[0], c[1] - 1, c[2]) or 'minecraft:air'):
            t.set(*c, f'snow[layers={rng.randint(1, 4)}]')
    for u in range(7, 20):
        for v in range(-4, 5):
            c = at(u, v, 13)
            above = (c[0], c[1] + 1, c[2])
            if t.name_at(*c) == 'minecraft:air' and t.name_at(*above) in ('minecraft:packed_ice', 'minecraft:ice', 'minecraft:blue_ice') \
                    and rng.random() < .22 and u not in (MAIN, FORE):
                t.set(*c, 'ice')
    # The surface: snow drifts, and powder snow hiding in the cracks.
    for x in range(t.size[0]):
        for z in range(t.size[2]):
            ys = [y for y in range(t.size[1]) if t.name_at(x, y, z) == 'minecraft:snow_block']
            if not ys: continue
            y = max(ys)
            if t.name_at(x, y + 1, z) is not None or y + 1 >= t.size[1]: continue
            r = rng.random()
            if r < .05: t.set(x, y, z, 'powder_snow')
            elif r < .45: t.set(x, y + 1, z, f'snow[layers={rng.randint(1, 3)}]')
    connect(t)
    t.entrance(18, SUB, 1)
    out = crop(t)
    leaks = check_sealed(out)
    assert not leaks, f'the frozen hold leaks: {leaks[:5]}'
    return out


def floe():
    """A drifting floe with the Northward's last good boat frozen into it: Tomas and Brekke never got far."""
    t = Template('iceberg/floe', (13, 5, 11), wet=True, waterline=2)
    rng = t.rng
    for x in range(13):
        for z in range(11):
            d = ((x - 6) / 6.3) ** 2 + ((z - 5) / 5.2) ** 2 + .12 * math.sin(x * 1.3 + z)
            if d <= 1:
                t.set(x, 0, z, 'packed_ice')
                t.set(x, 1, z, 'packed_ice' if d > .55 else 'ice')
            if d <= .78: t.set(x, 2, z, 'snow_block')
            if d <= .3 and rng.random() < .5: t.set(x, 3, z, 'snow[layers=2]')
    # The boat, half sunk in the floe: a little spruce hull with one oar.
    for x in range(4, 9):
        t.set(x, 2, 4, 'spruce_stairs[facing=south,half=bottom]')
        t.set(x, 2, 6, 'spruce_stairs[facing=north,half=bottom]')
        t.set(x, 2, 5, 'spruce_slab[type=bottom]')
    t.set(3, 2, 5, 'spruce_stairs[facing=east,half=bottom]')
    t.set(9, 2, 5, 'spruce_stairs[facing=west,half=bottom]')
    for x, z in ((2, 7), (3, 8)):
        t.set(x, 3, z, 'spruce_fence')
    t.barrel(5, 3, 5, 'up', 'iceberg/crew')
    t.set(7, 3, 5, 'skeleton_skull[rotation=4]')
    t.set(10, 2, 3, 'snow_block')
    t.sign(10, 3, 3, ['Tomas & Brekke', 'of the Northward', 'gone south', 'for help'], facing='west', wall=False)
    for x in range(13):
        for z in range(11):
            if t.name_at(x, 3, z) == 'minecraft:snow' and t.name_at(x, 2, z) != 'minecraft:snow_block':
                t.set(x, 3, z, None)
            if t.name_at(x, 2, z) == 'minecraft:snow_block' and t.name_at(x, 3, z) is None and rng.random() < .3:
                t.set(x, 3, z, 'snow[layers=1]')
    return t


def growler():
    """A smaller chunk of the berg that broke away and drifts nearby."""
    t = Template('iceberg/growler', (11, 13, 10), wet=True, waterline=5)
    rng = t.rng
    for x in range(11):
        for z in range(10):
            for y in range(13):
                n = 1 + .15 * _noise(x * 1.3, y, z * 1.3)
                d = ((x - 5) / 5.2) ** 2 + ((y - 4) / (8.0 if y > 4 else 4.6)) ** 2 + ((z - 4.5) / 4.6) ** 2
                if d <= n * n: t.set(x, y, z, 'packed_ice' if rng.random() < .8 else 'blue_ice')
    for x in range(11):
        for z in range(10):
            ys = [y for y in range(13) if t.name_at(x, y, z)]
            if ys and max(ys) > 6:
                t.set(x, max(ys), z, 'snow_block')
                if max(ys) + 1 < 13 and rng.random() < .5: t.set(x, max(ys) + 1, z, 'snow[layers=1]')
    return t


LAYOUTS = [
    {'weight': 3, 'pieces': [
        {'piece': 'iceberg/berg', 'at': (0, 0), 'turn': 0, 'y': -SUB, 'mode': 'rigid', 'soft': False, 'footing': False},
        {'piece': 'iceberg/floe', 'at': (-4, -19), 'turn': 0, 'y': -2, 'mode': 'surface', 'soft': False},
        {'piece': 'iceberg/growler', 'at': (-17, 10), 'turn': 1, 'y': -5, 'mode': 'surface', 'soft': False},
    ]},
    {'weight': 2, 'pieces': [
        {'piece': 'iceberg/berg', 'at': (0, 0), 'turn': 0, 'y': -SUB, 'mode': 'rigid', 'soft': False, 'footing': False},
        {'piece': 'iceberg/floe', 'at': (16, 14), 'turn': 1, 'y': -2, 'mode': 'surface', 'soft': False},
    ]},
]


def pieces():
    return [berg(), floe(), growler()]
