"""Loot-table helpers for the site designs. A design module lists its tables in LOOT_TABLES:

    LOOT_TABLES = {
        'galleon/hold': [pool(rolls(3, 6), [item('gold_ingot', 10, 1, 4), item('emerald', 5, 1, 3), empty(10)]),
                         pool(1, [item('oceanexpansion:pearl', 3, 1, 2), sea_chart(1), empty(6)])],
    }

Item ids without a namespace are vanilla (checked against the 26.3 item list); ours are 'oceanexpansion:<id>'
(see OUR_ITEMS).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS = set(open(os.path.join(HERE, '.cache', 'items.txt'), encoding='utf-8').read().split())
NS = 'oceanexpansion'
# Our items and block items a loot table may hand out.
OUR_ITEMS = {'pearl', 'black_pearl', 'ambergris', 'diving_helmet', 'giant_clam', 'tube_worms', 'barnacles', 'sea_glass',
             'sea_glass_pane', 'signal_lamp', 'contraband_crate', 'storm_glass'}


def full(name):
    if ':' not in name: name = 'minecraft:' + name
    ns, path = name.split(':', 1)
    if ns == 'minecraft': assert path in ITEMS, f'unknown item {name}'
    elif ns == NS: assert path in OUR_ITEMS, f'unknown {NS} item {name}'
    else: raise AssertionError(f'items from other mods may be missing: {name}')
    return name


def item(name, weight=1, lo=1, hi=1, extra=None):
    e = {'type': 'minecraft:item', 'name': full(name), 'weight': weight}
    mods = []
    if (lo, hi) != (1, 1):
        mods.append({'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}})
    mods += extra or []
    if mods: e['modifier'] = mods if len(mods) > 1 else mods[0]
    return e


def empty(weight):
    return {'type': 'minecraft:empty', 'weight': weight}


def rolls(lo, hi):
    return lo if lo == hi else {'type': 'minecraft:uniform', 'min': lo, 'max': hi}


def pool(n, entries):
    return {'rolls': n, 'entries': entries}


def enchanted(lo, hi):
    return [{'type': 'minecraft:enchant_with_levels', 'levels': {'type': 'minecraft:uniform', 'min': lo, 'max': hi},
             'options': '#minecraft:on_random_loot'}]


RANDOM_ENCHANT = [{'type': 'minecraft:enchant_randomly', 'options': '#minecraft:on_random_loot'}]
WORN = [{'type': 'minecraft:set_damage', 'damage': {'type': 'minecraft:uniform', 'min': 0.25, 'max': 0.7}}]


def named(text):
    """A custom item name (plain text), e.g. item('compass', extra=named("Captain Ardel's Compass"))."""
    return [{'type': 'minecraft:set_name', 'target': 'item_name', 'name': text}]


def sea_chart(weight=1):
    """A Sea Chart: a map to the nearest other Ocean Expansion site."""
    return {'type': 'minecraft:item', 'name': 'minecraft:map', 'weight': weight, 'modifier': [
        {'type': 'minecraft:exploration_map', 'destination': f'#{NS}:on_sea_charts', 'decoration': 'minecraft:red_x',
         'zoom': 2, 'search_radius': 60, 'skip_existing_chunks': True},
        {'type': 'minecraft:set_name', 'target': 'item_name', 'name': {'translate': f'item.{NS}.sea_chart'}},
        {'type': 'minecraft:filtered', 'item_filter': {'predicates': {'minecraft:map_id': {}}},
         'on_fail': {'type': 'minecraft:discard'}}]}


def treasure_map(weight=1):
    """A vanilla buried-treasure map."""
    return {'type': 'minecraft:item', 'name': 'minecraft:buried_treasure_map', 'weight': weight, 'modifier': [
        {'type': 'minecraft:exploration_map', 'destination': '#minecraft:on_treasure_maps', 'decoration': 'minecraft:red_x',
         'zoom': 1, 'skip_existing_chunks': False},
        {'type': 'minecraft:filtered', 'item_filter': {'predicates': {'minecraft:map_id': {}}},
         'on_fail': {'type': 'minecraft:discard'}}]}


TRIMS = ['coast', 'dune', 'eye', 'host', 'raiser', 'rib', 'sentry', 'shaper', 'silence', 'snout', 'spire', 'tide', 'vex',
         'ward', 'wayfinder', 'wild', 'flow', 'bolt']


def trim(name, weight=1):
    assert name in TRIMS, name
    return item(f'{name}_armor_trim_smithing_template', weight)


def table(*pools):
    return list(pools)
