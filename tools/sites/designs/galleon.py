"""The Sunken Galleon: the Golden Heron, a three-masted treasure galleon broken in two on the sea floor. The stern
half sits upright, sunk into the sand (sterncastle, captain's cabin, the strongroom in the hold); the bow half
lies a little way off, turned and rolled onto its side; two fallen masts and a field of spilled cargo lie
around them. Everything inside is open water."""
import math

from kit import Template
from loot import item, empty, pool, rolls, sea_chart, treasure_map, enchanted, named, trim
from .ship_parts import (Frame, Hull, Shipwright, voxelize, crop, barnacles, growth, coral_patch, kelp, settle,
                         sand_fill, connect, open_water)

KEY = 'galleon'
NAME = 'The Sunken Galleon'
FEATURES = [
    'the Golden Heron, a 44-block three-masted treasure galleon broken in two on the sea floor',
    'the stern half upright and half buried: sterncastle, stern gallery and gilded transom',
    "Captain Ysolde Marrow's cabin: her last log on a lectern, her chest, a fallen chandelier",
    'the strongroom in the hold behind a bent iron grille: the Crown gold (the big prize)',
    'the bow half rolled onto its side a little way off, with its heron figurehead and the galley',
    'the main mast still standing with a torn sail; the fore and mizzen masts fallen across the sand',
    "a debris field of spilled cargo and the ship's anchor",
    'barnacles, kelp, coral and sand drifts; the drowned captain on her deck and her crew in the hold',
]
SITE = {'anchor': 'seabed', 'depth': (19, 40), 'flatness': 9, 'radius': 30, 'weight': 3, 'inhabited': False,
        'biomes': ['ocean', 'deep_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean', 'warm_ocean', 'cold_ocean',
                   'deep_cold_ocean']}

L = 44
MIZZEN, MAIN, FORE = 10, 21, 37
STERN_SINK, BOW_SINK = 4, 3

LOOT_TABLES = {
    # The strongroom: the Crown gold. The site's big prize.
    'galleon/hold': [
        pool(rolls(4, 7), [item('gold_ingot', 12, 2, 6), item('gold_nugget', 10, 6, 18), item('emerald', 9, 2, 6),
                           item('raw_gold', 4, 2, 4), item('diamond', 2, 1, 2), item('gold_block', 1)]),
        pool(1, [item('heart_of_the_sea', 1), empty(5)]),
        pool(rolls(1, 2), [item('golden_sword', 2, extra=enchanted(15, 30)), item('golden_helmet', 2, extra=enchanted(15, 30)),
                           item('iron_sword', 3, extra=enchanted(10, 25)), item('book', 3, extra=enchanted(15, 30)),
                           item('golden_apple', 2), empty(2)]),
        pool(1, [item('oceanexpansion:pearl', 4, 1, 3), item('oceanexpansion:black_pearl', 1), empty(4)]),
    ],
    # Captain Marrow's own chest.
    'galleon/captain': [
        pool(rolls(2, 4), [item('gold_ingot', 6, 1, 3), item('emerald', 5, 1, 3), item('gold_nugget', 6, 3, 9),
                           item('paper', 4, 2, 5), item('book', 3), item('feather', 2, 1, 3), item('ink_sac', 2, 1, 2)]),
        pool(1, [item('spyglass', 3, extra=named("Captain Marrow's Spyglass")), item('compass', 3), item('clock', 2),
                 item('oceanexpansion:storm_glass', 2)]),
        pool(1, [sea_chart(3), treasure_map(1), empty(2)]),
        pool(1, [item('book', 2, extra=enchanted(20, 30)), trim('coast', 1), item('golden_helmet', 1, extra=enchanted(10, 20)),
                 empty(3)]),
    ],
    # Spices, silks and stores in the hold and the debris field.
    'galleon/cargo': [
        pool(rolls(3, 6), [item('cocoa_beans', 6, 2, 8), item('sugar', 6, 2, 8), item('paper', 5, 2, 6),
                           item('leather', 5, 1, 4), item('white_wool', 4, 2, 6), item('red_wool', 2, 1, 4),
                           item('purple_wool', 1, 1, 3), item('honey_bottle', 3, 1, 2), item('glass_bottle', 3, 1, 3),
                           item('coal', 5, 2, 6), item('iron_nugget', 4, 3, 9), item('gold_nugget', 3, 2, 6),
                           item('emerald', 1, 1, 2), item('rotten_flesh', 3, 1, 3)]),
        pool(1, [sea_chart(1), item('oceanexpansion:pearl', 1), empty(8)]),
    ],
    # What the crew left in their pots and bundles (a pot holds one stack).
    'galleon/crew': [
        pool(1, [item('bone', 5, 1, 3), item('string', 4, 1, 3), item('iron_nugget', 4, 2, 6),
                 item('gold_nugget', 3, 1, 4), item('emerald', 1), item('paper', 2, 1, 2), item('oceanexpansion:pearl', 1),
                 item('leather_boots', 1, extra=enchanted(5, 15))]),
    ],
}

LOG_PAGES = [
    "Golden Heron,\nthe fourth night\nof the storm.\n\nThe fleet is gone.\nI saw the Kestrel's\nlamps go under at\ndusk, and then no\nmore lamps at all.",
    "The hold is full.\nMore gold than this\nship was ever meant\nto carry, all of it\nsworn to the Crown\nbefore we sailed.\n\nI will not throw it\nover. Not for the\nsea. Not for the\ncrew.",
    "Hale says the main\nmast groans like a\nliving thing. The\npumps cannot keep\nup. The men want\nthe boats.\n\nI have locked the\nstrongroom and I\nwear the key.",
    "If any read this:\nthe Heron did not\nfounder for want of\nseamanship. She was\ntoo heavy, and her\ncaptain too proud\nto make her light.\nThat is the whole\nof it.",
    "The keel cracked\namidships an hour\nago. I can hear\nher breaking.\n\nI will stay with\nher. A captain\nkeeps her ship.\n\n  - Ysolde Marrow",
]


def brk(v, h):
    """Where the keel broke: a jagged line across the hull (the stern keeps u < brk, the bow u > brk + 1)."""
    return 26.5 + 1.4 * math.sin(.9 * v + .6 * h) + .9 * math.sin(2.1 * h - .7 * v + 1.3)


def shell(u, v, h, layer):
    if u < 1.6 and layer >= 5: return 'transom'
    if layer <= 4: return 'low'
    if layer == 8: return 'band'
    if layer == 12 and u < 16: return 'band'
    if layer >= 10: return 'upper'
    return 'mid'


FAMILIES = {
    'low': {'full': 'dark_oak_planks', 'stairs': 'dark_oak_stairs', 'slab': 'dark_oak_slab'},
    'mid': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'upper': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'band': {'full': 'yellow_terracotta', 'stairs': 'dark_oak_stairs', 'slab': 'dark_oak_slab'},
    'transom': {'full': 'dark_oak_planks', 'stairs': 'dark_oak_stairs', 'slab': 'dark_oak_slab'},
    'deck': {'full': 'oak_planks', 'stairs': 'oak_stairs', 'slab': 'oak_slab'},
    'floor': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
    'bulk': {'full': 'spruce_planks', 'stairs': 'spruce_stairs', 'slab': 'spruce_slab'},
}
SHELL = {'low', 'mid', 'upper', 'band', 'transom'}


def hull(part, holes=()):
    return Hull(L, 5.6, 11, full=(.28, .56), stem=.94, transom=.78, bilge=(4.0, 8.0), stem_rise=9.0,
                keel_rise_from=.70, tumble=(9.0, .2, 8.0), bow_rake=3.0, stern_rake=1.5, skin=1.0, run=(5.0, 6.0),
                fine=.75, sheer=[(-9, 8, 18), (8, 16, 15), (36, 60, 14)],
                decks=[(-9, 60, 1, 'floor'), (-9, 60, 5, 'deck'), (-9, 60, 9, 'deck'), (-9, 16, 13, 'deck'),
                       (-9, 8, 16, 'deck'), (36, 60, 12, 'deck')],
                bulkheads=[(15, 16, 10, 12, 'bulk'), (7, 8, 14, 15, 'bulk'), (36, 37, 10, 11, 'bulk'),
                           (11, 12, 2, 4, 'bulk')],
                holes=holes, part=part, shell=shell)


# -- shared finishing ----------------------------------------------------------------------------------

def splinter(t, f, mats, rng, edge, side):
    """Break up the hull along the fracture: knock out planks near it, leave splinters sticking out.
    `side` +1: the piece lies at u < edge (the stern), -1: at u > edge (the bow)."""
    for c, m in list(mats.items()):
        u, v, h = f.to_ship(c[0] + .5, c[1] + .5, c[2] + .5)
        gap = (edge(v, h) - u) * side
        if gap > 1.6 or t.name_at(*c) is None: continue
        if rng.random() < .35:
            t.set(*c, 'water' if m not in SHELL else None)
            mats.pop(c)
        elif m in SHELL and rng.random() < .3:
            x, y, z = f.to_template(u + side * 1.0, v, h)
            q = (math.floor(x), math.floor(y), math.floor(z))
            if t.inside(*q) and t.name_at(*q) in (None, 'minecraft:water'):
                t.set(*q, rng.choice(['spruce_fence', 'dark_oak_fence', 'spruce_slab[type=bottom]']))


def berms(t, footprint, rng, floor, height=2.6, reach=4, bias=None):
    """Sand heaped against the hull above the sea floor (soft: False pieces, so each column is built up from
    the floor). `bias(x, z)` scales the heap (the side the current piled it on)."""
    from collections import deque
    dist = {c: 0 for c in footprint}
    q = deque(footprint)
    while q:
        x, z = q.popleft()
        d = dist[(x, z)]
        if d >= reach: continue
        for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if n not in dist and 0 <= n[0] < t.size[0] and 0 <= n[1] < t.size[2]:
                dist[n] = d + 1
                q.append(n)
    for (x, z), d in sorted(dist.items()):
        if d == 0: continue
        hgt = int(round((height - .7 * d + rng.uniform(-.6, .6)) * (bias(x, z) if bias else 1.0)))
        top = floor
        for y in range(floor, floor + hgt):
            if not t.inside(x, y, z) or t.name_at(x, y, z) is not None: break
            t.set(x, y, z, 'sand')
            top = y + 1
        if top > floor and t.inside(x, top + 1, z) and t.name_at(x, top, z) is None and rng.random() < .2:
            if rng.random() < .4 and t.name_at(x, top + 1, z) is None:
                t.set(x, top, z, 'tall_seagrass[half=lower]')
                t.set(x, top + 1, z, 'tall_seagrass[half=upper]')
            else:
                t.set(x, top, z, 'seagrass')


def tops(t, mats, wanted):
    """Cells of the given materials that have open water right above them."""
    return [c for c, m in mats.items() if m in wanted and t.name_at(*c) is not None and
            open_water(t, c[0], c[1] + 1, c[2], 0)]


# -- the stern half ------------------------------------------------------------------------------------

def stern():
    t = Template('galleon/stern', (44, 26, 28), wet=True)
    OX, OZ = 7, 14
    f = Frame((OX, 0, OZ + .5))
    rng = t.rng
    model = hull(lambda u, v, hh: u < brk(v, hh),
                 holes=[(13.5, 5.6, 7.2, 1.4), (24.5, -5.4, 6.2, 1.3), (24.2, 1.2, 9.5, 1.3)])
    mats = voxelize(t, f, model, FAMILIES, 'water', ((-4, -7, 0), (31, 7, 19)))
    sw = Shipwright(t, f)
    P = sw.put
    FL = STERN_SINK

    def inside(u, v, h): return t.name_at(*sw.at(u, v, h)) == 'minecraft:water'

    def into(u, v, h, block):
        if inside(u, v, h): return P(u, v, h, block)

    # Rudder on the sternpost, and the stern gallery outside the great cabin.
    for layer in range(2, 10):
        aft = model.aft(layer + .5)
        for du in (1, 2):
            P(math.floor(aft) - du, 0, layer, 'dark_oak_planks')
    for v in range(-4, 5):
        P(-2, v, 9, 'dark_oak_slab[type=top]')
        P(-3, v, 9, 'dark_oak_slab[type=top]')
        P(-3, v, 10, 'dark_oak_fence')
        if abs(v) in (1, 4): P(-2, v, 8, 'dark_oak_stairs[facing=east,half=top]')
    for v in (-4, 4):
        P(-2, v, 10, 'dark_oak_fence')
    P(-3, 2, 10, 'water')                       # a gap where the rail broke away
    # Stern windows (great cabin and chart room) and the gilded transom.
    for c, m in list(mats.items()):
        if m != 'transom': continue
        u, v, h = f.to_ship(c[0] + .5, c[1] + .5, c[2] + .5)
        layer, vi = math.floor(h), round(v)
        if layer in (10, 11, 14, 15) and 1 <= abs(vi) <= 3: t.set(*c, 'glass_pane')
        elif layer in (13, 16) and abs(vi) <= 4: t.set(*c, 'yellow_terracotta')
        elif layer == 12 and abs(vi) <= 1: t.set(*c, 'gold_block' if vi == 0 else 'yellow_terracotta')
    for v in (-4, 4):                           # stern lanterns (the starboard one fell)
        P(0, v, 18, 'dark_oak_fence')
        if v < 0: P(0, v, 19, 'lantern')
    # Cabin doorway and windows in the bulkhead under the quarterdeck; the chart room's door.
    for layer in (10, 11):
        P(15, 0, layer, 'water')
        P(15, -1, layer, 'water')
    for v in (-3, 3):
        P(15, v, 11, 'glass_pane')
    P(7, 0, 14, 'water'); P(7, 0, 15, 'water')
    P(7, 2, 15, 'glass_pane'); P(7, -2, 15, 'glass_pane')
    # Steps: main deck -> quarterdeck -> poop deck.
    for v in (-3, 3):
        for i, layer in enumerate((10, 11, 12)):
            P(18 - i, v, layer, 'spruce_stairs[facing=west,half=bottom]')
    for i, layer in enumerate((14, 15)):
        P(9 - i, -2, layer, 'spruce_stairs[facing=west,half=bottom]')

    # Masts: the mizzen snapped above the quarterdeck, the main still standing (its top gone).
    sw.line((MIZZEN + .5, 0, 1.5), (MIZZEN + .5, 0, 15.5), 'stripped_spruce_log[axis={axis}]')
    P(MIZZEN, 0, 16, 'spruce_fence')
    P(MIZZEN + 1, 0, 14, 'spruce_slab[type=bottom]')
    sw.line((MAIN + .5, 0, 1.5), (MAIN + .5, 0, 20.5), 'stripped_spruce_log[axis={axis}]')
    P(MAIN, 0, 21, 'spruce_fence')
    for du in (-1, 0, 1):                        # the fighting top
        for dv in (-1, 0, 1):
            if (du, dv) != (0, 0) and (du, dv) != (1, 1): P(MAIN + du, dv, 17, 'spruce_slab[type=top]')
    for du, dv in ((-2, -1), (-2, 0), (-2, 1), (-1, -2), (0, -2), (1, -2), (-1, 2), (0, 2), (2, -1), (2, 0)):
        P(MAIN + du, dv, 18, 'spruce_fence')
    # The main yard hangs askew (a lift parted), its torn course below it.
    yard = sw.line((MAIN + 1.5, -6.4, 15.5), (MAIN + 1.5, 6.4, 13.6), 'stripped_spruce_log[axis={axis}]')
    for c in yard:
        u, v, h = f.to_ship(c[0] + .5, c[1] + .5, c[2] + .5)
        if abs(v) > 5: t.set(*c, 'spruce_fence')
    for v in range(-5, 6):
        top = math.floor(15.5 - (v + 6.4) * (1.9 / 12.8)) - 1
        for layer in range(top, 10, -1):
            depth = (top - layer) / 4
            if rng.random() < .22 + .25 * depth or (layer < top - 2 and rng.random() < .4): continue
            P(MAIN + 2, v, layer, rng.choice(['white_wool', 'white_wool', 'white_wool', 'light_gray_wool']))
    # Shrouds from the fighting top down to the rails (some parted).
    for du in (-1, 1):
        for side in (-1, 1):
            cells = sw.line((MAIN + .5 + du, side * 1.4, 17.5), (MAIN + .5 + du * 1.5, side * 5.2, 10.6), 'dark_oak_fence')
            for c in cells:
                if rng.random() < .2: t.set(*c, None)
    sw.line((MIZZEN + .5, -1.2, 15.2), (MIZZEN + 1.5, -4.6, 14.6), 'dark_oak_fence')
    # Main deck: capstan, coiled rope, the hatch down, the ship's bell.
    P(18, 0, 10, 'stripped_spruce_log[axis=y]'); P(18, 0, 11, 'stripped_spruce_log[axis=y]')
    for du, dv in ((-1, 0), (1, 0), (0, -1), (0, 1)): P(18 + du, dv, 11, 'spruce_fence')
    for v in (-1, 0, 1):
        for u in (23, 24):
            P(u, v, 9, 'water')
    P(23, 1, 9, 'spruce_trapdoor[facing=north,half=top,open=false]')
    for u in (23, 24):
        for v in (-1, 0):
            P(u, v, 5, 'water')
    for u in (19, 20):
        P(u, 3, 10, 'iron_chain[axis=x]')
    P(20, 4, 10, 'iron_chain[axis=z]')
    P(14, -3, 14, 'bell[attachment=floor,facing=east]')
    P(17, -2, 9, 'water'); P(17, -1, 9, 'water')           # aft hatch to the lower deck
    P(17, -2, 10, 'spruce_trapdoor[facing=east,half=bottom,open=true]')
    t.haunt(*sw.at(17, 2, 10), 'drowned_captain')

    # The captain's cabin.
    t.lectern(*sw.at(5, 0, 10), 'east', 'Last Entry of the Golden Heron', 'Capt. Ysolde Marrow', LOG_PAGES)
    t.chest(*sw.at(1, -3, 10), 'east', 'galleon/captain')
    for u, v, layer in ((1, 3, 10), (2, 3, 10), (1, 3, 11), (3, 4, 10), (3, 4, 11)):
        into(u, v, layer, 'bookshelf')
    into(2, 3, 11, 'chiseled_bookshelf[facing=west]')
    for v in (-2, -1, 1, 2):                    # window seat under the stern windows
        into(0, v, 10, 'dark_oak_stairs[facing=west,half=bottom]')
    into(7, -2, 10, 'dark_oak_fence'); into(7, -2, 11, 'spruce_pressure_plate')
    into(8, -2, 10, 'spruce_stairs[facing=west,half=bottom]')
    into(7, -3, 10, 'spruce_stairs[facing=south,half=bottom]')
    into(6, 2, 10, 'spruce_stairs[facing=east,half=bottom]')   # a chair knocked aside
    into(7, 0, 12, 'iron_chain[axis=y]')        # the chandelier's chain; the chandelier lies on the floor
    into(7, 1, 10, 'lantern')
    into(8, 1, 10, 'iron_bars[east=true,west=true]')
    into(6, 1, 10, 'candle[candles=3,lit=false]')
    into(8, 2, 10, 'white_candle[candles=2,lit=false]')
    into(13, -4, 10, 'barrel[facing=up,open=false]')
    into(13, 4, 10, 'barrel[facing=up,open=false]')
    into(12, 4, 10, 'cartography_table')
    t.item_frame(*sw.at(14, 1, 11), 'west', 'map')
    # The chart room under the poop.
    into(2, -2, 14, 'cartography_table')
    into(1, 2, 14, 'barrel[facing=north,open=false]')
    into(3, 0, 15, 'lantern[hanging=true]')
    into(5, 0, 14, 'lever[face=floor,facing=east,powered=false]')   # the whipstaff
    t.item_frame(*sw.at(6, -1, 15), 'west', 'compass')

    # Lower deck: the officers' mess, the galley stove, cargo.
    into(4, 0, 6, 'dark_oak_fence'); into(4, 0, 7, 'spruce_pressure_plate')
    into(3, 0, 6, 'spruce_stairs[facing=east,half=bottom]')
    into(5, 1, 6, 'spruce_stairs[facing=west,half=bottom]')
    t.pot(*sw.at(2, 2, 6), 'east', 'galleon/crew')
    t.pot(*sw.at(2, -2, 6), 'east', 'galleon/crew', sherds=['brick', 'angler_pottery_sherd', 'brick', 'brick'])
    into(13, -3, 6, 'furnace[facing=east,lit=false]')
    into(14, -3, 6, 'water_cauldron[level=3]')
    into(13, -3, 7, 'iron_chain[axis=y]')
    t.sign(*sw.at(13, -2, 6), ["Ship's biscuit", '2 a day.', 'Rum on Sunday.', '- Cook'], facing='east', wall=False)
    for u, v in ((15, 3), (16, 3), (15, 2), (19, -3), (20, -3), (22, 3)):
        into(u, v, 6, 'barrel[facing=up,open=false]')
    into(15, 3, 7, 'barrel[facing=up,open=false]')
    into(19, -3, 7, 'spruce_slab[type=bottom]')
    t.sign(*sw.at(9, 3, 6), ['Days becalmed:', '|||| |||| ||', 'Then the storm.', ''], facing='west', wall=False)
    into(8, 1, 5, 'water')                       # the hatch down into the strongroom, its cover broken
    into(8, 2, 6, 'spruce_trapdoor[facing=south,half=bottom,open=true]')

    # The hold: the strongroom aft behind a bent grille, the cargo hold forward.
    for v in range(-1, 2):
        for layer in (2, 3):
            P(11, v, layer, 'iron_bars')
    P(11, 1, 2, 'water')                         # a bar bent out: just room to swim through
    t.sign(*sw.at(12, -2, 3), ['STRONGROOM', 'Crown gold.', 'No entry but', 'by the Captain'], facing='east')
    t.chest(*sw.at(6, 0, 2), 'east', 'galleon/hold')
    into(5, -1, 2, 'gold_block')
    t.pot(*sw.at(7, 2, 2), 'west', 'galleon/crew', sherds=['brick', 'heart_pottery_sherd', 'brick', 'brick'])
    for u, v, layer in ((4, 2, 2), (4, 1, 2), (4, 2, 3)):
        into(u, v, layer, 'sand')
    t.barrel(*sw.at(14, -2, 2), 'up', 'galleon/cargo')
    t.barrel(*sw.at(19, 2, 2), 'up', 'galleon/cargo')
    for u, v, layer in ((13, -3, 2), (13, -2, 3), (16, 3, 2), (15, 3, 2), (21, -3, 2), (22, -3, 2)):
        into(u, v, layer, 'barrel[facing=up,open=false]')
    for u, v, layer, b in ((16, -3, 2, 'red_wool'), (17, -3, 2, 'purple_wool'), (16, -3, 3, 'white_wool'),
                           (18, 3, 2, 'yellow_wool'), (14, 3, 2, 'spruce_planks'), (14, 3, 3, 'spruce_slab[type=bottom]')):
        into(u, v, layer, b)
    t.haunt(*sw.at(17, 0, 2), 'drowned_crew')

    # The break lets the sea floor in: a sand slope into the hold, planks knocked out along the fracture.
    splinter(t, f, mats, rng, brk, 1)
    slope = []
    for (x, y, z), b in list(t.blocks.items()):
        if b[0] != 'minecraft:water': continue
        u, v, h = f.to_ship(x + .5, y + .5, z + .5)
        if h < 5 and u > brk(v, h) - 6 + (h - 1) * 1.4 + rng.uniform(-.8, .8): slope.append((x, y, z))
    sand_fill(t, slope)

    # Outside: sand heaped along the starboard side and under the counter, sea growth, barnacles.
    foot = {(x, z) for (x, y, z) in mats if y <= FL + 1}
    berms(t, foot, rng, FL, height=2.4, reach=4, bias=lambda x, z: 1.4 if z > OZ else .6)
    growth(t, tops(t, mats, {'deck'}), rng, floor_line=FL, kelp_chance=.12, pickles=.05, grass=.0, coral=False,
           kelp_height=(2, 7), ceiling=19)
    for (u, v, layer) in ((3, 1, 16), (23, -3, 9), (12, 3, 13)):
        x, y, z = sw.at(u, v, layer)
        coral_patch(t, x, y + 1, z, rng, size=1, floor_line=FL)
    for (u, v, layer) in ((5, -2, 16), (20, 3, 9), (11, -3, 13), (25, 0, 5)):
        x, y, z = sw.at(u, v, layer)
        if open_water(t, x, y + 1, z, FL): t.set(x, y + 1, z, 'sea_pickle[pickles=3]')
    barnacles(t, [c for c, m in mats.items() if m in SHELL], rng, chance=.13, floor_line=FL)
    connect(t)
    t.entrance(*sw.at(24, 0, 10))
    return crop(t)


# -- the bow half ----------------------------------------------------------------------------------------

def heron(sw):
    """The figurehead: a white heron under the bowsprit, neck stretched forward, yellow beak."""
    P = sw.put
    for u, h in ((41, 9), (42, 9), (42, 10), (43, 10)):
        P(u, 0, h, 'white_wool')
    P(41, -1, 10, 'light_gray_wool'); P(41, 1, 10, 'light_gray_wool')        # folded wings
    P(42, -1, 10, 'white_wool'); P(42, 1, 10, 'white_wool')
    P(40, -1, 10, 'light_gray_wool'); P(40, 1, 10, 'light_gray_wool')
    for u, h in ((44, 11), (44, 12), (45, 12)):
        P(u, 0, h, 'quartz_block')
    P(46, 0, 12, 'white_wool')
    P(46, 0, 13, 'white_wool')                   # the crest
    P(47, 0, 12, 'yellow_wool'); P(48, 0, 12, 'yellow_terracotta')


def bow():
    t = Template('galleon/bow', (64, 46, 64), wet=True)
    f = Frame((8, 8, 32.5), yaw=24, pitch=4, roll=25, pivot=(34, 0, 4))
    rng = t.rng
    model = hull(lambda u, v, hh: u > brk(v, hh) + 1.2, holes=[(31, -5.6, 5.5, 2.3), (34, -3, 9.4, 1.4)])
    mats = voxelize(t, f, model, FAMILIES, 'water', ((24, -7, 0), (49, 7, 19)))
    sw = Shipwright(t, f)
    P = sw.put
    lowest = min(y for (x, y, z) in mats)
    FL = lowest + BOW_SINK

    def inside(u, v, h): return t.name_at(*sw.at(u, v, h)) == 'minecraft:water'

    def into(u, v, h, block):
        if inside(u, v, h): return P(u, v, h, block)

    # Forecastle bulkhead door, the foremast stump, the bowsprit, the beakhead and the heron.
    P(36, 0, 10, 'water'); P(36, 0, 11, 'water')
    sw.line((FORE + .5, 0, 1.5), (FORE + .5, 0, 14.5), 'stripped_spruce_log[axis={axis}]')
    P(FORE, 0, 15, 'spruce_fence')
    for du in (-1, 1):
        sw.line((FORE + .5, du * 1.2, 14.2), (FORE + .5, du * 4.6, 12.6), 'dark_oak_fence')
    sw.line((40.5, 0, 12.5), (46.5, 0, 14.5), 'stripped_spruce_log[axis={axis}]')
    P(47, 0, 15, 'spruce_fence')
    for u in range(41, 45):                      # the beakhead platform
        for v in (-1, 0, 1):
            if (u, v) != (44, 1): P(u, v, 10, 'spruce_slab[type=bottom]')
        P(u, -2 if u < 44 else -1, 11, 'dark_oak_fence')
    heron(sw)
    # A small ballista on the forecastle, knocked askew.
    P(39, 2, 13, 'spruce_stairs[facing=west,half=bottom]')
    P(40, 2, 13, 'stripped_spruce_log[axis=x]')
    P(40, 1, 13, 'spruce_fence'); P(40, 3, 13, 'spruce_fence')
    P(41, 2, 13, 'lightning_rod[facing=east,powered=false]')   # the bolt still loaded

    # The galley in the forecastle, the crew's mess on the lower deck: everything slid to the low side.
    into(38, -1, 10, 'smoker[facing=west,lit=false]')
    into(37, -1, 10, 'water_cauldron[level=3]')
    into(37, 1, 11, 'iron_chain[axis=y]')
    loose = [(30, 2, 6, 'barrel[facing=up,open=false]'), (31, 1, 6, 'barrel[facing=up,open=false]'),
             (33, -1, 6, 'barrel[facing=east,open=false]'), (29, 0, 2, 'barrel[facing=up,open=false]'),
             (30, -2, 2, 'red_wool'), (32, 1, 2, 'barrel[facing=up,open=false]'), (34, 0, 2, 'white_wool'),
             (39, 1, 10, 'barrel[facing=up,open=false]'), (38, 0, 10, 'barrel[facing=up,open=false]'), (37, 1, 6, 'spruce_planks')]
    for u, v, layer, b in loose:
        c = sw.at(u, v, layer)
        if t.name_at(*c) == 'minecraft:water': t.set(*settle(t, *c), f.turn_spec(b))
    for u, v, layer in ((32, 0, 6), (35, 2, 6), (37, 1, 10)):
        c = sw.at(u, v, layer)
        if t.name_at(*c) == 'minecraft:water': t.pot(*settle(t, *c), 'north', 'galleon/crew')
    c = sw.at(30, 1, 2)
    if t.name_at(*c) == 'minecraft:water': t.barrel(*settle(t, *c), 'up', 'galleon/cargo')

    splinter(t, f, mats, rng, lambda v, h: brk(v, h) + 1.2, -1)
    # Sand has drifted into the low side of the hull, and heaped against it outside.
    low = [c for c, b in t.blocks.items() if b[0] == 'minecraft:water' and c[1] <= FL + 1]
    sand_fill(t, low)
    foot = {(x, z) for (x, y, z) in mats if y <= FL + 1}
    berms(t, foot, rng, FL, height=2.2, reach=3)
    roof = max(y for (x, y, z) in t.blocks)
    growth(t, tops(t, mats, SHELL | {'deck'}), rng, floor_line=FL, kelp_chance=.1, pickles=.04, grass=0, coral=False,
           kelp_height=(2, 6), ceiling=roof - 1)
    for spot in rng.sample(tops(t, mats, SHELL), 3):
        coral_patch(t, spot[0], spot[1] + 1, spot[2], rng, size=1, floor_line=FL)
    barnacles(t, [c for c, m in mats.items() if m in SHELL], rng, chance=.16, floor_line=FL)
    connect(t)
    t.entrance(*sw.at(30, 0, 9))
    return crop(t)


# -- fallen masts and the debris field ------------------------------------------------------------------

def foremast():
    """The foremast lying on the sand, its yard across it and the torn foresail spread over the floor."""
    t = Template('galleon/foremast', (22, 9, 11), wet=True)
    rng = t.rng
    for x in range(0, 20):
        t.set(x, 0, 5, 'stripped_spruce_log[axis=x]')
    t.set(20, 0, 5, 'spruce_fence'); t.set(21, 0, 5, 'spruce_fence')          # the splintered top
    for z in range(1, 10):                       # the fore yard
        t.set(13, 0, z, 'stripped_spruce_log[axis=z]' if 3 <= z <= 7 else 'spruce_fence')
    for z in (3, 4, 6, 7):                       # the fighting top, flattened
        t.set(16, 0, z, 'spruce_slab[type=bottom]')
    t.set(16, 1, 5, 'spruce_slab[type=bottom]')
    for x in range(4, 13):                       # the sail, spread and torn, a fold standing up
        for z in range(1, 10):
            if z == 5 or rng.random() < .3: continue
            t.set(x, 0, z, rng.choice(['white_wool', 'white_wool', 'light_gray_wool']))
    for z in range(2, 9):
        if rng.random() < .6: t.set(8, 1, z, 'white_wool')
    for x in range(1, 12, 2):                    # rigging lying in the sand
        t.set(x, 0, 9 if x % 4 == 1 else 0, 'iron_chain[axis=x]')
    for x, z in ((2, 4), (3, 6), (11, 3), (14, 8), (6, 2), (10, 8)):
        if t.name_at(x, 0, z) is None: t.set(x, 0, z, 'sand')
    for x, z in ((5, 3), (9, 6), (12, 2), (7, 8)):
        if t.name_at(x, 1, z) is None and t.name_at(x, 0, z) and 'wool' in t.name_at(x, 0, z):
            kelp(t, x, 1, z, rng.randint(3, 7))
    barnacles(t, [(x, 0, 5) for x in range(0, 20)], rng, chance=.3)
    connect(t)
    return t


def mizzen():
    """The mizzen mast with its long slanting lateen yard, the triangular sail half buried."""
    t = Template('galleon/mizzen', (17, 9, 13), wet=True)
    rng = t.rng
    for x in range(1, 14):
        t.set(x, 0, 3, 'stripped_spruce_log[axis=x]')
    t.set(14, 0, 3, 'spruce_fence')
    for i in range(14):                          # the lateen yard, diagonal across the mast
        x, z = 2 + i, 11 - round(i * .65)
        if t.name_at(x, 0, z) is None: t.set(x, 0, z, 'spruce_fence' if i in (0, 13) else 'stripped_spruce_log[axis=x]')
    for i in range(12):                          # the sail: a triangle between yard and mast
        x0, z0 = 3 + i, 11 - round(i * .65)
        for z in range(4, z0):
            if rng.random() < .25 + .03 * i: continue
            t.set(x0, 0, z, rng.choice(['white_wool', 'brown_wool', 'white_wool']))
    for x, z in ((4, 7), (9, 6), (12, 5)):
        if t.name_at(x, 1, z) is None: t.set(x, 1, z, 'sand')
    kelp(t, 6, 1, 6, 5); kelp(t, 10, 1, 7, 4)
    barnacles(t, [(x, 0, 3) for x in range(1, 14)], rng, chance=.3)
    connect(t)
    return t


def debris():
    """Cargo spilled when she broke: barrels, a burst crate, pots, and the anchor with its cable."""
    t = Template('galleon/debris', (15, 9, 13), wet=True)
    rng = t.rng
    # The anchor, lying on its side: shank, stock, arms and flukes, the cable running off.
    for x in range(3, 9):
        t.set(x, 0, 6, 'iron_bars[east=true,west=true]')
    for z in range(4, 9):
        t.set(9, 0, z, 'stripped_dark_oak_log[axis=z]')
    t.set(2, 0, 6, 'iron_block')
    t.set(2, 0, 5, 'iron_bars[north=true,south=true]'); t.set(2, 0, 7, 'iron_bars[north=true,south=true]')
    t.set(2, 0, 4, 'iron_trapdoor[facing=north,half=bottom,open=false]')
    t.set(2, 0, 8, 'iron_trapdoor[facing=south,half=bottom,open=false]')
    for x in range(10, 15):
        t.set(x, 0, 6 + (x > 12), 'iron_chain[axis=x]')
    # Cargo.
    t.barrel(5, 0, 1, 'up', 'galleon/cargo')
    t.barrel(11, 0, 10, 'east', 'galleon/cargo')
    for x, z, b in ((6, 1, 'barrel[facing=up,open=false]'), (6, 2, 'barrel[facing=north,open=false]'),
                    (12, 9, 'barrel[facing=up,open=false]'), (12, 10, 'spruce_planks'), (13, 10, 'spruce_slab[type=bottom]'),
                    (11, 11, 'spruce_slab[type=bottom]'), (4, 10, 'red_wool'), (5, 11, 'red_wool'),
                    (12, 2, 'spruce_planks'), (13, 3, 'spruce_slab[type=bottom]')):
        t.set(x, 0, z, b)
    t.set(12, 1, 10, 'barrel[facing=up,open=false]')
    t.pot(8, 0, 11, 'north', 'galleon/crew', sherds=['brick', 'explorer_pottery_sherd', 'brick', 'brick'])
    t.pot(1, 0, 11, 'east')
    for x, z in ((7, 9), (8, 3), (3, 2), (10, 4), (1, 9)):
        t.set(x, 0, z, 'sand')
    kelp(t, 4, 1, 10, 6); kelp(t, 12, 1, 2, 4)
    t.set(7, 1, 9, 'sea_pickle[pickles=2]')
    t.set(1, 0, 2, 'seagrass'); t.set(9, 0, 10, 'seagrass'); t.set(13, 0, 6, 'seagrass')
    barnacles(t, [(x, 0, 6) for x in range(2, 9)] + [(9, 0, z) for z in range(4, 9)], rng, chance=.3)
    return t


# -- the site --------------------------------------------------------------------------------------------

LAYOUTS = [
    # The stern sits near the centre (rigid, on the floor sampled there); the bow lies a few blocks off its
    # broken end, turned and rolled; the fallen masts and the spilled cargo around them.
    {'weight': 3, 'pieces': [
        {'piece': 'galleon/stern', 'at': (-8, 0), 'turn': 0, 'y': -STERN_SINK, 'mode': 'rigid', 'soft': False},
        {'piece': 'galleon/bow', 'at': (16, 2), 'turn': 0, 'y': -BOW_SINK, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/debris', 'at': (4, 14), 'turn': 0, 'y': 0, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/foremast', 'at': (12, -14), 'turn': 0, 'y': 0, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/mizzen', 'at': (-14, 15), 'turn': 2, 'y': 0, 'mode': 'floor', 'soft': False},
    ]},
    {'weight': 2, 'pieces': [
        {'piece': 'galleon/stern', 'at': (-9, 1), 'turn': 0, 'y': -STERN_SINK, 'mode': 'rigid', 'soft': False},
        {'piece': 'galleon/bow', 'at': (17, -4), 'turn': 0, 'y': -BOW_SINK, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/debris', 'at': (-8, -15), 'turn': 1, 'y': 0, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/foremast', 'at': (16, 14), 'turn': 3, 'y': 0, 'mode': 'floor', 'soft': False},
        {'piece': 'galleon/mizzen', 'at': (-4, 17), 'turn': 0, 'y': 0, 'mode': 'floor', 'soft': False},
    ]},
]


def pieces():
    return [stern(), bow(), foremast(), mizzen(), debris()]
