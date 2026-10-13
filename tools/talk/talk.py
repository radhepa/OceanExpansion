"""Compile the sea-site residents' dialogue: tools/talk/lines/<role>.txt -> data/oceanexpansion/talk/lines.json.

  python tools/talk/talk.py            check and write
  python tools/talk/talk.py --check    check only
  python tools/talk/talk.py --stats    lines per pool

A lines file is plain text. `## <pool>` starts a pool; every following non-empty line is one line of
dialogue; `#` starts a comment line. Pool names are `<role>.<topic>[.<detail>]` (see POOLS). A line may use
the placeholders in PLACEHOLDERS; a line whose placeholder has no value at that moment is skipped by the game.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'oceanexpansion', 'talk', 'lines.json')

ROLES = ['lightkeeper', 'warden', 'captain', 'smuggler', 'chief']
# A role with a parent falls back to the parent's pools for anything it doesn't have.
PARENT = {'captain': 'warden', 'chief': 'smuggler'}
HELD = ['pickaxe', 'sword', 'axe', 'shovel', 'bow', 'shield', 'torch', 'ore', 'diamond', 'gold', 'emerald', 'food',
        'map', 'compass', 'book', 'tnt', 'potion', 'flower', 'bucket', 'trident', 'fishing_rod', 'shell', 'pearl', 'fish', 'boat',
        'spyglass']
STATES = ['hurt', 'hungry', 'unarmored', 'diamond', 'leather', 'fire', 'damaged']
POOLS = (['greet', 'greet.stranger', 'greet.friend', 'greet.morning', 'greet.evening', 'greet.night',
          'chat', 'chat.new', 'chat.close', 'past', 'night', 'work', 'adventure', 'joke', 'news', 'heart',
          'rumor', 'rumor.none', 'seafolk']
         + [f'held.{h}' for h in HELD] + [f'player.{s}' for s in STATES])
# Pools every role (or its parent) must have, with a minimum number of lines.
REQUIRED = {'greet': 12, 'greet.stranger': 5, 'greet.friend': 5, 'chat': 20, 'past': 8, 'work': 10, 'adventure': 6,
            'joke': 6, 'news': 6, 'heart': 6, 'rumor': 8, 'rumor.none': 3, 'seafolk': 4}


def required(role):
    """Minimum lines per pool a role must reach (its own plus its parent's)."""
    return REQUIRED
PLACEHOLDERS = {'name', 'player', 'place', 'time', 'captain', 'chief', 'item',
                'rumor_name', 'rumor_dir', 'rumor_dist'}
# Placeholders a pool may rely on (anything else a line uses must be universal).
POOL_ONLY = {'item': lambda p: p.startswith('held.'),
             'rumor_name': lambda p: p == 'rumor', 'rumor_dir': lambda p: p == 'rumor', 'rumor_dist': lambda p: p == 'rumor'}
PLACE = re.compile(r'\{([a-z_]+)\}')


def parse(path):
    pools, pool = {}, None
    with open(path, encoding='utf-8') as f:
        for n, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or (line.startswith('#') and not line.startswith('##')): continue
            if line.startswith('## '):
                pool = line[3:].strip()
                assert pool not in pools, f'{path}:{n}: pool {pool} twice'
                pools[pool] = []
                continue
            assert pool, f'{path}:{n}: a line before any ## pool'
            pools[pool].append((n, line))
    return pools


def check(all_pools):
    problems = []
    for name, lines in all_pools.items():
        role, _, topic = name.partition('.')
        if role not in ROLES: problems.append(f'{name}: unknown role'); continue
        if topic not in POOLS: problems.append(f'{name}: unknown pool (allowed: {", ".join(POOLS)})')
        seen = set()
        for n, line in lines:
            for ph in PLACE.findall(line):
                if ph not in PLACEHOLDERS: problems.append(f'{name} line {n}: unknown placeholder {{{ph}}}')
                elif ph in POOL_ONLY and not POOL_ONLY[ph](topic): problems.append(f'{name} line {n}: {{{ph}}} only in its own pools')
            if topic == 'rumor' and not all(f'{{{p}}}' in line for p in ('rumor_name', 'rumor_dir')):
                problems.append(f'{name} line {n}: a rumour line needs {{rumor_name}} and {{rumor_dir}}')
            if len(line) > 260: problems.append(f'{name} line {n}: too long ({len(line)} chars, keep under 260)')
            if line in seen: problems.append(f'{name} line {n}: duplicate line')
            seen.add(line)
            if '  ' in line or line != line.strip(): problems.append(f'{name} line {n}: stray spaces')
            if any(w in line.lower() for w in ('minecraft', ' mod ', 'npc')):
                problems.append(f'{name} line {n}: breaks the fourth wall: {line[:60]}')
    for role in ROLES:
        for pool, least in required(role).items():
            have, r = 0, role
            while r:
                have += len(all_pools.get(f'{r}.{pool}', []))
                r = PARENT.get(r)
            if have < least: problems.append(f'{role}.{pool}: {have} lines (with its parents), needs at least {least}')
    return problems


def main():
    folder = os.path.join(HERE, 'lines')
    all_pools = {}
    for file in sorted(os.listdir(folder)):
        if not file.endswith('.txt'): continue
        for name, lines in parse(os.path.join(folder, file)).items():
            assert name not in all_pools, f'{file}: pool {name} also defined elsewhere'
            all_pools[name] = lines
    problems = check(all_pools)
    if '--stats' in sys.argv:
        for role in ROLES:
            total = sum(len(v) for k, v in all_pools.items() if k.startswith(role + '.'))
            print(f'{role:8} {total:4} lines in {sum(1 for k in all_pools if k.startswith(role + "."))} pools')
    if problems:
        print('\n'.join(problems))
        print(f'{len(problems)} problem(s)')
        sys.exit(1)
    total = sum(len(v) for v in all_pools.values())
    if '--check' in sys.argv:
        print(f'ok: {total} lines in {len(all_pools)} pools')
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'parents': PARENT, 'pools': {k: [l for _, l in v] for k, v in sorted(all_pools.items())}}, f,
                  indent=1, ensure_ascii=False)
        f.write('\n')
    print(f'wrote {total} lines in {len(all_pools)} pools to {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
