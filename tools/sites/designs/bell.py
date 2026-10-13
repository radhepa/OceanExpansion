"""Wexley's Diving Bell: an abandoned salvage barge riding the surface, its chain running straight down to a
copper diving bell on the sea floor. Inside the bell an air pocket still holds: a bench, a lantern and the
chest with Wexley's diving helmet. Salvage lies scattered around it, and his last diver's crew is still down
there."""
from kit import Template
from loot import item, empty, pool, rolls, sea_chart
from .ship_parts import kelp, check_sealed, connect

KEY = 'bell'
NAME = "Wexley's Diving Bell"
FEATURES = [
    "Wexley's salvage barge at the surface: a winch and shear-leg crane, his hut and his Dive Book",
    'a chain from the crane straight down to the copper diving bell on the sea floor',
    'inside the bell a real air pocket: a bench, a lantern, "AIR. Breathe slow." and the diving helmet',
    'salvage scattered around the bell: crates, a toppled cart of ingots, a broken second helmet',
    'the crew of the last dive, drowned beside the bell',
]
SITE = {'anchor': 'seabed', 'depth': (10, 30), 'flatness': 9, 'radius': 14, 'weight': 2, 'inhabited': False,
        'biomes': ['ocean', 'lukewarm_ocean', 'warm_ocean', 'cold_ocean']}

LOOT_TABLES = {
    # The bell's chest: the diving helmet, always, and the last dive's salvage.
    'bell/bell': [
        pool(1, [item('oceanexpansion:diving_helmet')]),
        pool(rolls(2, 4), [item('copper_ingot', 8, 2, 6), item('iron_ingot', 6, 1, 4), item('gold_nugget', 4, 2, 8),
                           item('nautilus_shell', 2), item('prismarine_shard', 2, 1, 4), item('oceanexpansion:pearl', 3, 1, 2),
                           item('emerald', 2, 1, 2)]),
    ],
    # Wexley's stores on the barge.
    'bell/barge': [
        pool(rolls(3, 5), [item('copper_ingot', 6, 2, 5), item('iron_nugget', 5, 3, 9), item('iron_chain', 4, 2, 6),
                           item('lead', 3, 1, 2), item('paper', 4, 2, 5), item('bucket', 2), item('cod', 4, 1, 3),
                           item('coal', 4, 2, 5), item('candle', 3, 1, 3), item('glass_bottle', 2, 1, 2)]),
        pool(1, [item('compass', 3), item('clock', 3), item('spyglass', 1), item('oceanexpansion:storm_glass', 1), empty(2)]),
        pool(1, [sea_chart(2), empty(3)]),
    ],
    # Salvage brought up from other wrecks and left on the sea floor.
    'bell/salvage': [
        pool(rolls(2, 5), [item('iron_ingot', 8, 1, 4), item('copper_ingot', 8, 2, 6), item('raw_iron', 5, 1, 3),
                           item('gold_ingot', 3, 1, 2), item('gold_nugget', 4, 2, 6), item('emerald', 2, 1, 2),
                           item('nautilus_shell', 2), item('coal', 4, 2, 6), item('bone', 3, 1, 3), item('iron_chain', 2, 1, 3)]),
        pool(1, [item('oceanexpansion:pearl', 2), sea_chart(1), empty(5)]),
    ],
}

DIVE_BOOK = [
    "The Dive Book of\nB. Wexley,\nsalvager.\n\nThe bell works.\nForty turns of the\nwinch to the\nfathom. The air\nkeeps an hour, if\na man breathes\nslow.",
    "Dive 12.\nA merchantman,\nfifty years down.\nBrought up iron,\ncopper and a crate\nof nails.\n\nPip says the bell\nis too small for\ntwo. Pip is right.",
    "Dive 19.\nMade a helmet from\nthe spare copper:\na little bell for\none head. In it a\nman can walk out\nfrom the bell and\nback again.\nI keep it below,\nin the bell's chest.",
    "Dive 23.\nPip went down at\nnoon. The line went\nslack at two. The\nwinch would not\nturn: something\nheld the bell.\n\nThen it let go.",
    "Dive 24.\nI am going down\nfor him. If the\nchain is cut, the\nbell will stay\nwhere it lies, and\nthe air with it.\n\nBreathe slow.\n  - B. Wexley",
]

# The bell: 11 x 8 x 11, centred on (5, 5) so the barge's chain lands on its crown.
C = 5
OX = ['exposed_copper', 'weathered_copper', 'weathered_copper', 'oxidized_copper']
OXCUT = ['exposed_cut_copper', 'weathered_cut_copper', 'weathered_cut_copper', 'oxidized_cut_copper']


def _toward_centre(x, z):
    dx, dz = C - x, C - z
    if abs(dx) >= abs(dz): return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'


def bell():
    t = Template('bell/bell', (11, 8, 11), wet=True)
    rng = t.rng
    pick = lambda opts: rng.choice(opts)
    ring = lambda r: [(x, z) for x in range(C - r, C + r + 1) for z in range(C - r, C + r + 1)
                      if max(abs(x - C), abs(z - C)) == r]
    # y 0: a scour pit dug round the bell (the template's floor row is the sea floor itself).
    for x in range(11):
        for z in range(11):
            if (x - C) ** 2 + (z - C) ** 2 <= 26: t.set(x, 0, z, 'water')
    # Legs, the flared lip and the rim; under the rim you swim in, up through the moon pool.
    for x, z in ((2, 2), (2, 8), (8, 2), (8, 8), (5, 2), (2, 5)):
        t.set(x, 0, z, pick(['weathered_copper_grate', 'oxidized_copper_grate']))
        t.set(x, 1, z, pick(['weathered_copper_grate', 'exposed_copper_grate']))
    for x, z in ring(4):
        if (x, z) not in ((1, 1), (9, 9)): t.set(x, 2, z, f'{pick(OXCUT)}_slab[type=top]')
    for x, z in ring(3):
        t.set(x, 2, z, pick(OXCUT))
    for x, z in ring(2):
        t.set(x, 2, z, 'spruce_planks')
    for x, z in ring(1) + [(C, C)]:
        t.set(x, 2, z, 'water')                  # the moon pool: the sea's surface inside the bell
    # Walls with four portholes, the shoulder and the crown.
    for y in (3, 4, 5):
        for x, z in ring(3):
            t.set(x, y, z, pick(OX))
    for x, z in ((C, 2), (C, 8), (2, C), (8, C)):
        t.set(x, 4, z, 'glass')
    for x, z in ring(3):
        t.set(x, 6, z, f'{pick(OXCUT)}_stairs[facing={_toward_centre(x, z)},half=bottom]')
    for x, z in ring(2) + ring(1) + [(C, C)]:
        t.set(x, 6, z, pick(OXCUT))
    for x, z in ring(2):
        t.set(x, 7, z, f'{pick(OXCUT)}_stairs[facing={_toward_centre(x, z)},half=bottom]')
    for x, z in ring(1):
        t.set(x, 7, z, pick(OXCUT))
    t.set(C, 7, C, 'weathered_copper')           # the crown, where the chain is shackled
    # The air pocket: 5 x 3 x 5 of dry air over the bench ring.
    t.carve((3, 3, 3), (7, 5, 7))
    t.keep_dry((3, 3, 3), (7, 5, 7))
    for z in (4, 5, 6):                          # the bench along the west wall
        t.set(3, 3, z, 'spruce_stairs[facing=west,half=bottom]')
    t.chest(7, 3, 3, 'west', 'bell/bell', custom_name="Wexley's Chest")
    t.set(7, 3, 7, 'barrel[facing=up,open=false]')
    t.set(C, 5, C, 'lantern[hanging=true]')
    t.sign(6, 4, 7, ['AIR.', 'Breathe slow.', '', ''], facing='north')
    t.sign(4, 4, 3, ['Pip -', 'one hour.', 'Not one breath', 'more.'], facing='south')
    t.item_frame(7, 4, 5, 'west', 'clock')
    # Outside: salvage at the pit's edge, the crew of the last dive, weed.
    t.barrel(1, 0, 4, 'up', 'bell/salvage')
    t.set(0, 0, 5, 'barrel[facing=east,open=false]')
    t.set(1, 0, 6, 'spruce_planks')
    t.set(1, 1, 6, 'spruce_slab[type=bottom]')
    t.set(9, 0, 3, 'iron_chain[axis=x]'); t.set(10, 0, 3, 'iron_chain[axis=x]')
    t.set(4, 0, 9, 'weathered_copper_bulb[lit=false,powered=false]')   # a dented helmet
    t.haunt(10, 0, 6, 'drowned_crew')
    for x, z, h in ((0, 1, 5), (10, 8, 6), (0, 9, 4), (10, 1, 3)):
        kelp(t, x, 1, z, h)
    t.set(9, 1, 1, 'sea_pickle[pickles=2]')
    t.entrance(C, 1, 2)
    leaks = check_sealed(t, sea_level=t.size[1])
    assert not leaks, f'the bell leaks: {leaks[:4]}'
    return t


def barge():
    """The barge: 15 x 12 x 11, riding the surface (bottom three rows under water). Its only block in the
    bottom row is the chain under the crane: it is extended down to the bell."""
    t = Template('bell/barge', (15, 12, 11), wet=True, waterline=3)
    rng = t.rng
    cx, cz = 7, 5
    t.set(cx, 0, cz, 'iron_chain[axis=y]')
    # Hull: a flat spruce barge with raked ends; the deck at sea level.
    for x in range(2, 13):
        for z in range(2, 9):
            t.set(x, 1, z, 'dark_oak_planks')
    for x in range(1, 14):
        for z in range(1, 10):
            edge = x in (1, 13) or z in (1, 9)
            t.set(x, 2, z, 'stripped_spruce_log[axis=x]' if z in (1, 9) else 'spruce_planks')
    for z in range(1, 10):
        t.set(0, 2, z, 'spruce_stairs[facing=east,half=top]')
        t.set(14, 2, z, 'spruce_stairs[facing=west,half=top]')
    for x in range(1, 14):
        for z in range(1, 10):
            t.set(x, 3, z, 'spruce_planks' if (x + z) % 5 else 'stripped_spruce_wood[axis=x]')
    for z in range(1, 10):
        t.set(0, 3, z, 'spruce_slab[type=bottom]')
        t.set(14, 3, z, 'spruce_slab[type=bottom]')
    for y in (1, 2, 3):                          # the chain well
        t.set(cx, y, cz, 'iron_chain[axis=y]')
    t.set(cx - 1, 3, cz, 'spruce_trapdoor[facing=east,half=top,open=false]')
    # Gunwale rail (a section broken away), lanterns on the corner posts.
    for x in range(1, 14):
        for z in (1, 9):
            if not (z == 9 and 3 <= x <= 5): t.set(x, 4, z, 'spruce_fence')
    for z in range(2, 9):
        t.set(1, 4, z, 'spruce_fence')
    for x, z in ((1, 1), (1, 9), (13, 1)):
        t.set(x, 4, z, 'stripped_spruce_log[axis=y]')
        t.set(x, 5, z, 'lantern')
    # The shear-leg crane over the well, the chain hanging from its head.
    for y in range(4, 10):
        dz = min(2, (y - 4) * 3 // 5)
        t.set(cx, y, 2 + dz, 'stripped_spruce_log[axis=y]')
        t.set(cx, y, 8 - dz, 'stripped_spruce_log[axis=y]')
    for z in range(3, 8):
        t.set(cx, 10, z, 'stripped_spruce_log[axis=z]')
    t.set(cx, 11, cz, 'spruce_fence')
    for y in range(4, 10):
        t.set(cx, y, cz, 'iron_chain[axis=y]')
    for x in range(3, 7):                        # the back-stay down to the winch
        t.set(x, 10 - (7 - x) * 2 + 1, cz, 'spruce_fence')
    # The winch: a drum on a frame, a grindstone for the crank, rope (chain) wound on it.
    for z in (4, 5, 6):
        t.set(3, 4, z, 'stripped_spruce_log[axis=z]')
        t.set(3, 5, z, 'iron_chain[axis=z]')
    t.set(3, 4, 3, 'grindstone[face=floor,facing=east]')
    t.set(3, 4, 7, 'spruce_fence')
    for x in (4, 5, 6):
        t.set(x, 4, cz, 'iron_chain[axis=x]')
    t.sign(2, 4, 5, ['40 turns to', 'the fathom.', 'Mind the chain!', '- B.W.'], facing='west', wall=False)
    for x, z, axis in ((5, 2, 'x'), (6, 2, 'x'), (5, 8, 'z'), (4, 8, 'x')):   # coils of chain
        t.set(x, 4, z, f'iron_chain[axis={axis}]')
    t.set(2, 4, 8, 'barrel[facing=up,open=false]')
    t.set(2, 4, 2, 'barrel[facing=up,open=false]')
    t.set(2, 5, 2, 'cauldron')
    t.set(4, 4, 2, 'composter')
    # Wexley's hut on the after end.
    for y in (4, 5, 6):
        for x in range(9, 14):
            for z in range(2, 9):
                if x in (9, 13) or z in (2, 8):
                    corner = x in (9, 13) and z in (2, 8)
                    t.set(x, y, z, 'stripped_spruce_log[axis=y]' if corner else 'spruce_planks')
    roof = {1: 7, 2: 7, 3: 8, 4: 8, 5: 9, 6: 8, 7: 8, 8: 7, 9: 7}
    for x in range(8, 15):                       # pitched roof, gable ends boarded
        for z, y in roof.items():
            if z == 5: t.set(x, y, z, 'dark_oak_slab[type=bottom]')
            else: t.set(x, y, z, f"dark_oak_stairs[facing={'south' if z < 5 else 'north'},half=bottom]")
    for x in (9, 13):
        for z in range(3, 8):
            t.set(x, 7, z, 'spruce_planks')
        t.set(x, 8, 5, 'spruce_planks')
    t.carve((10, 4, 3), (12, 6, 7))
    t.carve((10, 7, 3), (12, 7, 7))
    t.carve((10, 8, 5), (12, 8, 5))
    t.door(9, 4, 5, 'west', kind='spruce_door')
    t.set(9, 5, 3, 'glass_pane'); t.set(9, 5, 7, 'glass_pane'); t.set(13, 5, 5, 'glass_pane')
    t.set(11, 6, 2, 'glass_pane'); t.set(11, 6, 8, 'glass_pane')
    t.lectern(12, 4, 5, 'west', "Wexley's Dive Book", 'B. Wexley', DIVE_BOOK)
    t.barrel(12, 4, 3, 'up', 'bell/barge')
    t.bed(10, 4, 7, 'east', 'brown')
    t.set(12, 4, 7, 'crafting_table')
    t.set(10, 4, 3, 'smithing_table')
    t.set(11, 8, 5, 'lantern[hanging=true]')  # hangs from the ridge
    t.set(11, 4, 3, 'barrel[facing=up,open=false]')
    t.item_frame(12, 5, 4, 'west', 'copper_ingot')
    t.sign(8, 5, 6, ['WEXLEY', 'SALVAGE', 'Keep off', 'the winch!'], facing='west')
    t.set(12, 5, 7, 'candle[candles=2,lit=false]')
    connect(t)
    t.entrance(1, 4, 5)
    return t


def salvage():
    """Salvage on the sea floor near the bell: a chest cart tipped on its side with ingots spilled, crates,
    a broken spare helmet, a coil of chain."""
    t = Template('bell/salvage', (9, 3, 9), wet=True)
    rng = t.rng
    t.minecart(3, 0, 4, loot='bell/salvage', facing='east')
    for x, z, shape in ((1, 4, 'east_west'), (2, 5, 'east_west'), (5, 3, 'north_south'), (6, 6, 'east_west')):
        t.set(x, 0, z, f'rail[shape={shape}]')
    t.set(5, 0, 4, 'raw_iron_block')
    for x, z in ((4, 5), (6, 4), (5, 6)):
        t.set(x, 0, z, 'iron_trapdoor[facing=north,half=bottom,open=false]')   # ingots spilled from the cart
    t.set(4, 0, 3, 'heavy_weighted_pressure_plate[power=0]')
    t.barrel(7, 0, 7, 'north', 'bell/salvage')
    t.set(7, 0, 6, 'barrel[facing=up,open=false]')
    t.set(7, 1, 7, 'spruce_slab[type=bottom]')
    t.set(1, 0, 1, 'spruce_planks'); t.set(2, 0, 1, 'spruce_slab[type=bottom]'); t.set(1, 1, 1, 'barrel[facing=east,open=false]')
    t.set(6, 0, 1, 'oxidized_copper_bulb[lit=false,powered=false]')            # the broken spare helmet
    t.set(7, 0, 1, 'oxidized_copper_grate')
    for x in range(0, 4):
        t.set(x, 0, 7, 'iron_chain[axis=x]')
    t.set(0, 0, 8, 'iron_chain[axis=z]')
    kelp(t, 3, 0, 1, 5); kelp(t, 8, 0, 3, 4); kelp(t, 0, 0, 5, 6)
    t.set(5, 0, 8, 'seagrass'); t.set(2, 0, 3, 'seagrass'); t.set(8, 0, 5, 'sea_pickle[pickles=1]')
    return t


LAYOUTS = [
    # The bell and the barge share the centre, so the barge's chain (extended down by footing) lands on the
    # bell's crown whatever the turn. List the bell first.
    {'weight': 2, 'pieces': [
        {'piece': 'bell/bell', 'at': (0, 0), 'turn': 0, 'y': -1, 'mode': 'rigid'},
        {'piece': 'bell/barge', 'at': (0, 0), 'turn': 0, 'y': -3, 'mode': 'surface', 'footing': True},
        {'piece': 'bell/salvage', 'at': (7, -8), 'turn': 0, 'y': 0, 'mode': 'floor', 'soft': False},
    ]},
    {'weight': 1, 'pieces': [
        {'piece': 'bell/bell', 'at': (0, 0), 'turn': 1, 'y': -1, 'mode': 'rigid'},
        {'piece': 'bell/barge', 'at': (0, 0), 'turn': 2, 'y': -3, 'mode': 'surface', 'footing': True},
        {'piece': 'bell/salvage', 'at': (-9, 5), 'turn': 3, 'y': 0, 'mode': 'floor', 'soft': False},
    ]},
]


def pieces():
    return [bell(), barge(), salvage()]
