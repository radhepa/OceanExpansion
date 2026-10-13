"""Write everything the Ocean Expansion sites need in the data pack: the block templates of every design in
designs/, a structure per site, the structure set (its own placement keeps clear of
villages, ocean monuments, the Sea Friends' villages...), biome and structure tags, loot tables, the lightkeeper's
and smugglers' trades and a catalog the game tests read.

  python tools/sites/build.py            build (templates are validated against vanilla's blockstates)
  python tools/sites/build.py --render   also render every piece to tools/sites/out/
  python tools/sites/build.py --check    only validate (writes nothing)
  python tools/sites/build.py --check --only=galleon,whale   validate just those designs
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kit import NS, RES, ROLES, write_json  # noqa: E402
import loot as L  # noqa: E402
import designs  # noqa: E402

DATA = os.path.join(RES, 'data', NS)
OCEANS = ['ocean', 'deep_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean', 'warm_ocean', 'cold_ocean', 'deep_cold_ocean',
          'frozen_ocean', 'deep_frozen_ocean']

# One structure set for every site: about one site in each 22 x 22 chunk cell (352 blocks square) of ocean, rarer
# or commoner with "rarity" in config/oceanexpansion.json. A site that can't stand where the set offers it (wrong
# biome, depth or sea floor) lets the set try another kind there. Each set in AVOID is kept that many chunks away;
# a set from a mod that isn't installed is skipped.
SPACING, SEPARATION, SALT = 22, 8, 1186034211
AVOID = [('minecraft:villages', 4), ('minecraft:ocean_monuments', 4), ('minecraft:ocean_ruins', 2),
         ('minecraft:shipwrecks', 2), ('villagefriends:homesteads', 2), ('plataclan:dens', 2), ('plataclan:warrens', 3),
         ('seafriends:merfolk_villages', 5), ('seafriends:prismari_courts', 5)]
NO_MONSTERS = {'monster': {'bounding_box': 'piece', 'spawns': []}}
MODES = ('rigid', 'floor', 'surface')


# -- structures -------------------------------------------------------------------------------------

def check_design(mod, catalog):
    key = mod.KEY
    names = {t: info for t, info in catalog.items() if t.startswith(key + '/')}
    s = mod.SITE
    assert s['anchor'] in ('seabed', 'surface'), f'{key}: anchor must be seabed or surface'
    lo, hi = s['depth']
    assert 3 <= lo < hi <= 60, f'{key}: depth {lo}..{hi}'
    assert s['biomes'] and all(b in OCEANS for b in s['biomes']), f'{key}: biomes must be oceans: {s["biomes"]}'
    assert 4 <= s.get('radius', 16) <= 64
    assert mod.LAYOUTS, f'{key}: no layouts'
    for layout in mod.LAYOUTS:
        for p in layout['pieces']:
            assert p['piece'] in names, f'{key}: layout uses unknown piece {p["piece"]}'
            assert p.get('mode', 'rigid') in MODES, p
            assert p.get('turn', 0) in (0, 1, 2, 3), p
            x, z = p.get('at', (0, 0))
            sx, _, sz = names[p['piece']]['size']
            assert abs(x) + max(sx, sz) / 2 <= s.get('radius', 16) + 2, \
                f'{key}: {p["piece"]} at {p.get("at")} reaches past radius {s.get("radius", 16)}'
    for t, info in names.items():
        for table in info['notes'].get('loot', []):
            assert table.split('chests/', 1)[1] in mod.LOOT_TABLES, f'{key}: {t} uses undefined loot table {table}'


def structures(mods):
    for mod in mods:
        s = mod.SITE
        write_json(f'data/{NS}/tags/worldgen/biome/has_site/{mod.KEY}.json', {'values': ['minecraft:' + b for b in s['biomes']]})
        structure = {
            'type': f'{NS}:site', 'biomes': f'#{NS}:has_site/{mod.KEY}', 'step': 'surface_structures',
            'terrain_adaptation': 'none', 'spawn_overrides': NO_MONSTERS if s.get('inhabited') else {},
            'anchor': s['anchor'], 'depth': {'min': s['depth'][0], 'max': s['depth'][1]},
            'flatness': s.get('flatness', 8), 'radius': s.get('radius', 16),
            'layouts': [{'weight': lay.get('weight', 1), 'pieces': [
                {'template': f'{NS}:{p["piece"]}', 'x': p.get('at', (0, 0))[0], 'z': p.get('at', (0, 0))[1],
                 'y': p.get('y', 0), 'turn': p.get('turn', 0), 'mode': p.get('mode', 'rigid'),
                 'footing': bool(p.get('footing', False)), 'soft': bool(p.get('soft', True))}
                for p in lay['pieces']]} for lay in mod.LAYOUTS]}
        if s.get('chance', 1) < 1: structure['chance'] = s['chance']
        write_json(f'data/{NS}/worldgen/structure/{mod.KEY}.json', structure)
    write_json(f'data/{NS}/worldgen/structure_set/sites.json', {
        'structures': [{'structure': f'{NS}:{m.KEY}', 'weight': m.SITE.get('weight', 1)} for m in mods],
        'placement': {'type': f'{NS}:spread', 'spacing': SPACING, 'separation': SEPARATION, 'salt': SALT,
                      'avoid': [{'set': s, 'chunks': c} for s, c in AVOID]}})
    write_json(f'data/{NS}/tags/worldgen/structure/sites.json', {'values': [f'{NS}:{m.KEY}' for m in mods]})
    write_json(f'data/{NS}/tags/worldgen/structure/inhabited.json',
               {'values': [f'{NS}:{m.KEY}' for m in mods if m.SITE.get('inhabited')]})
    # What a Sea Chart can point you to: any site but a lighthouse (you can see those).
    write_json(f'data/{NS}/tags/worldgen/structure/on_sea_charts.json',
               {'values': [f'{NS}:{m.KEY}' for m in mods if m.KEY != 'lighthouse']})


def loot(mods):
    for mod in mods:
        for name, pools in mod.LOOT_TABLES.items():
            assert name.startswith(mod.KEY + '/'), f'{mod.KEY}: loot table {name} must start with "{mod.KEY}/"'
            write_json(f'data/{NS}/loot_table/chests/{name}.json',
                       {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': f'{NS}:chests/{name}'})


# -- trades ---------------------------------------------------------------------------------------------

def _it(name, count=1):
    return {'id': L.full(name), 'count': count}


# profession -> level -> [(name, wants, gives, max_uses, xp, extra)]; items as (id, count).
TRADES = {
    'lightkeeper': {
        1: [('cod', [('cod', 12)], ('emerald', 1), 16, 2, None),
            ('salmon', [('salmon', 10)], ('emerald', 1), 16, 2, None),
            ('candles', [('emerald', 1)], ('candle', 4), 12, 1, None)],
        2: [('glass', [('emerald', 1)], ('glass', 6), 12, 5, None),
            ('lanterns', [('emerald', 2)], ('lantern', 3), 12, 5, None),
            ('spyglass', [('emerald', 4), ('copper_ingot', 2)], ('spyglass', 1), 4, 10, None)],
        3: [('sea_chart', [('emerald', 8), ('compass', 1)], ('map', 1), 4, 15, 'sea_chart'),
            ('signal_lamp', [('emerald', 6)], ('oceanexpansion:signal_lamp', 1), 4, 10, None),
            ('glow_ink', [('glow_ink_sac', 3)], ('emerald', 1), 12, 15, None)],
        4: [('sea_lanterns', [('emerald', 5)], ('sea_lantern', 2), 8, 15, None),
            ('storm_glass', [('emerald', 10), ('glass_bottle', 1)], ('oceanexpansion:storm_glass', 1), 3, 20, None)],
        5: [('treasure_map', [('emerald', 14), ('compass', 1)], ('buried_treasure_map', 1), 2, 30, 'treasure_map')],
    },
    'smuggler': {
        1: [('rum', [('emerald', 2)], ('honey_bottle', 2), 12, 2, None),
            ('gunpowder', [('emerald', 2)], ('gunpowder', 4), 12, 2, None),
            ('ink', [('ink_sac', 6)], ('emerald', 1), 16, 2, None)],
        2: [('spices', [('emerald', 3)], ('cocoa_beans', 8), 12, 5, None),
            ('silk', [('emerald', 4)], ('white_wool', 6), 12, 5, None),
            ('black_pearl_buy', [('oceanexpansion:black_pearl', 1)], ('emerald', 8), 6, 10, None)],
        3: [('nautilus', [('emerald', 6)], ('nautilus_shell', 1), 6, 15, None),
            ('saddle', [('emerald', 10)], ('saddle', 1), 3, 15, None),
            ('pearl_sell', [('emerald', 4)], ('oceanexpansion:pearl', 1), 6, 15, None)],
        4: [('trident', [('emerald', 30), ('oceanexpansion:black_pearl', 1)], ('trident', 1), 1, 30, 'worn'),
            ('treasure_map', [('emerald', 12), ('compass', 1)], ('buried_treasure_map', 1), 2, 20, 'treasure_map')],
        5: [('heart', [('emerald', 40), ('oceanexpansion:black_pearl', 2)], ('heart_of_the_sea', 1), 1, 30, None)],
    },
}
OFFERS = {1: 2, 2: 2, 3: 2, 4: 2, 5: 1}


def trades():
    for profession, levels in TRADES.items():
        tags = {}
        for level, offers in levels.items():
            for name, wants, gives, uses, xp, extra in offers:
                body = {'wants': _it(*wants[0]), 'gives': _it(*gives), 'max_uses': uses, 'xp': xp,
                        'reputation_discount': 0.05}
                if len(wants) > 1: body['additional_wants'] = _it(*wants[1])
                if extra == 'sea_chart': body['given_item_modifier'] = L.sea_chart(1)['modifier']
                if extra == 'treasure_map': body['given_item_modifier'] = L.treasure_map(1)['modifier']
                if extra == 'worn': body['given_item_modifier'] = L.WORN
                write_json(f'data/{NS}/villager_trade/{profession}/{name}.json', body)
                tags.setdefault(level, []).append(f'{NS}:{profession}/{name}')
        for level, values in tags.items():
            write_json(f'data/{NS}/tags/villager_trade/{profession}/level_{level}.json', {'values': sorted(values)})
            write_json(f'data/{NS}/trade_set/{profession}/level_{level}.json', {
                'trades': f'#{NS}:{profession}/level_{level}', 'amount': OFFERS[level],
                'random_sequence': f'{NS}:trade_set/{profession}/level_{level}'})


# -- catalog for the game tests ----------------------------------------------------------------------

def catalog_file(mods, catalog):
    out = {}
    for mod in mods:
        pieces = {t: info for t, info in catalog.items() if t.startswith(mod.KEY + '/')}
        notes = {k: [] for k in ('residents', 'loot', 'haunts', 'books', 'spawners', 'creatures')}
        for info in pieces.values():
            for k in notes: notes[k] += info['notes'].get(k, [])
        s = mod.SITE
        out[mod.KEY] = {'name': mod.NAME, 'structure': f'{NS}:{mod.KEY}', 'inhabited': bool(s.get('inhabited')),
                        'anchor': s['anchor'], 'depth': list(s['depth']), 'biomes': s['biomes'],
                        'residents': sorted(notes['residents']), 'loot': sorted(set(notes['loot'])),
                        'haunts': sorted(set(notes['haunts'])), 'books': notes['books'],
                        'spawners': sorted(set(notes['spawners'])), 'creatures': sorted(set(notes['creatures'])),
                        'pieces': sorted(pieces), 'features': getattr(mod, 'FEATURES', [])}
        for role in set(notes['residents']): assert role in ROLES
    write_json(f'data/{NS}/{NS}/catalog.json', out)


def main():
    check_only = '--check' in sys.argv
    only = None
    for a in sys.argv:
        if a.startswith('--only='): only = a.split('=', 1)[1].split(',')
    mods = designs.modules(only)
    assert mods, 'no designs yet'
    catalog = {}
    if not check_only and only is None:
        shutil.rmtree(os.path.join(DATA, 'structure'), ignore_errors=True)
        shutil.rmtree(os.path.join(DATA, 'worldgen'), ignore_errors=True)
        shutil.rmtree(os.path.join(DATA, 'loot_table'), ignore_errors=True)
    for mod in mods:
        for t in mod.pieces():
            assert t.name.startswith(mod.KEY + '/'), f'{t.name}: pieces of {mod.KEY} are named "{mod.KEY}/..."'
            assert t.name not in catalog, f'duplicate piece {t.name}'
            if check_only:
                t.validate()
                catalog[t.name] = {'notes': t.notes, 'size': list(t.size), 'blocks': len(t.blocks)}
            else:
                catalog[t.name] = t.save()
        check_design(mod, catalog)
        # every loot table must be valid JSON-able and use known items (L.full asserts while the design builds them)
        json.dumps(mod.LOOT_TABLES)
    if check_only:
        print(f'ok: {len(catalog)} pieces in {len(mods)} designs')
        return
    if only is None:
        structures(mods)
        loot(mods)
        trades()
        catalog_file(mods, catalog)
    for mod in mods:
        pieces = [t for t in catalog if t.startswith(mod.KEY + '/')]
        blocks = sum(catalog[t]['blocks'] for t in pieces)
        print(f'  {mod.KEY:10} {mod.NAME:26} {len(pieces):2} pieces {blocks:6} blocks  {mod.SITE["anchor"]} {mod.SITE["depth"]}')
    print(f'{len(catalog)} templates, {len(mods)} sites')
    if '--render' in sys.argv:
        os.system(f'"{sys.executable}" "{os.path.join(HERE, "preview.py")}"')


if __name__ == '__main__':
    main()
