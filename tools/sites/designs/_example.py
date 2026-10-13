"""A tiny worked example of a site design (not built into the mod): a wrecked rowboat on the sea floor and a
buoy at the surface above it. Copy its shape, not its looks. See DESIGN.md, "Design module contract"."""
from kit import Template
from loot import item, empty, pool, rolls, sea_chart

KEY = 'example'
NAME = 'Example Wreck'
FEATURES = ['a rowboat on the sea floor with a chest', 'a buoy at the surface']
SITE = {'anchor': 'seabed', 'depth': (8, 30), 'flatness': 6, 'radius': 12, 'weight': 1,
        'biomes': ['ocean', 'lukewarm_ocean', 'warm_ocean'], 'inhabited': False}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'example/boat', 'at': (0, 0), 'y': -1, 'mode': 'rigid'},   # bedded one block into the floor
        {'piece': 'example/buoy', 'at': (6, 3), 'y': 0, 'mode': 'floor', 'footing': True},
    ]},
]
LOOT_TABLES = {
    'example/stash': [pool(rolls(2, 4), [item('gold_nugget', 5, 2, 6), item('oceanexpansion:pearl', 1), empty(4)]),
                      pool(1, [sea_chart(1), empty(3)])],
}


def boat():
    t = Template('example/boat', (7, 3, 4), wet=True)
    t.fill((0, 0, 0), (6, 0, 3), 'sand')                    # soft: only where the floor is solid
    t.fill((1, 1, 0), (5, 1, 3), 'spruce_planks')           # hull bottom (built)
    t.walls((1, 2, 0), (5, 2, 3), 'spruce_slab[type=bottom]')
    t.flood((2, 2, 1), (4, 2, 2))                           # the inside is open water
    t.chest(3, 2, 1, 'south', 'example/stash')              # waterlogged automatically (wet template)
    return t


def buoy():
    # A float that rides at the surface would need the sea level: here a post rises from the floor instead,
    # and footing=True extends its bottom block down to the floor wherever it lands.
    t = Template('example/buoy', (1, 6, 1), wet=True)
    t.fill((0, 0, 0), (0, 4, 0), 'stripped_spruce_log')
    t.set(0, 5, 0, 'sea_pickle[pickles=4]')
    return t


def pieces():
    return [boat(), buoy()]
