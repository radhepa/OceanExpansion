"""Building blocks for the Ocean Expansion sites: block templates written as native, compressed Minecraft 26.3
structure files (standard library only), plus checks that every block and property exists in vanilla's own
blockstate files (or is one of the few mod blocks listed below).

A Template holds only the blocks it sets. Anything left unset is a structure void, so the world's own block
stays there: the sea around a wreck, the sea floor under it, the open air above the waves.

Kinds of block in a design:
  * built blocks (planks, bricks, logs, prismarine, lanterns...) are always placed;
  * 'water' and 'air' are always placed: 'water' floods a room (inside a wreck, under the sea floor), 'air'
    opens a dry room (above the sea, or an air pocket under a diving bell);
  * NATURAL blocks (stone, sand, gravel, clay...) are "soft": in the world they replace only solid ground and
    never fill water or air. Use them to bed a wreck into the sea floor or line a sea cave.

A wet template (Template(..., wet=True)) is under water below its `waterline` (default: the whole template):
every block there that can hold water is written waterlogged, except in cells kept dry with keep_dry().
"""

import gzip
import json
import os
import random
import re
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, 'src', 'main', 'resources')
NS = 'oceanexpansion'
DATA_VERSION = 5023  # Minecraft 26.3, as in vanilla's own templates
CACHE = os.path.join(HERE, '.cache', 'assets', 'minecraft')

FACINGS = {'north', 'south', 'east', 'west'}
HAUNTS = ('drowned_crew', 'drowned_captain', 'guardians', 'frozen_crew', 'deep_lurkers')
# Our own blocks (and the two Village Friends workstations the Tidewatch garrison trains at), with their properties.
FACING6 = FACINGS | {'up', 'down'}
BOOL = {'true', 'false'}
MOD_BLOCKS = {
    'oceanexpansion:haunt': {'kind': set(HAUNTS), 'waterlogged': BOOL},
    'oceanexpansion:giant_clam': {'facing': FACINGS, 'pearl': BOOL, 'waterlogged': BOOL},
    'oceanexpansion:tube_worms': {'waterlogged': BOOL},
    'oceanexpansion:barnacles': {'facing': FACING6, 'waterlogged': BOOL},
    'oceanexpansion:sea_glass': {},
    'oceanexpansion:sea_glass_pane': {'north': BOOL, 'south': BOOL, 'east': BOOL, 'west': BOOL, 'waterlogged': BOOL},
    'oceanexpansion:signal_lamp': {'facing': FACINGS},
    'oceanexpansion:contraband_crate': {'facing': FACINGS},
    'villagefriends:training_dummy': {'facing': FACINGS},
    'villagefriends:archery_target': {'facing': FACINGS},
}
# Properties that never show up in blockstate files because no model depends on them.
HIDDEN_PROPERTIES = {'waterlogged', 'powered', 'persistent', 'distance', 'occupied', 'triggered', 'enabled',
                     'signal_fire', 'stage', 'note', 'instrument', 'has_book', 'cracked', 'ominous', 'disarmed',
                     'attached', 'conditional', 'lit', 'hanging', 'open', 'bottom', 'in_wall', 'inverted'}

# "Soft" natural blocks: placed only where the world is already solid (never fill a cave). The build's
# oceanexpansion:natural processor gets exactly this list.
NATURAL = sorted({
    'minecraft:stone', 'minecraft:deepslate', 'minecraft:tuff', 'minecraft:andesite', 'minecraft:diorite',
    'minecraft:granite', 'minecraft:calcite', 'minecraft:amethyst_block', 'minecraft:budding_amethyst',
    'minecraft:smooth_basalt', 'minecraft:basalt', 'minecraft:dripstone_block', 'minecraft:moss_block',
    'minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:rooted_dirt', 'minecraft:gravel', 'minecraft:clay',
    'minecraft:mud', 'minecraft:magma_block', 'minecraft:obsidian', 'minecraft:blackstone',
    'minecraft:coal_ore', 'minecraft:iron_ore', 'minecraft:copper_ore', 'minecraft:gold_ore', 'minecraft:redstone_ore',
    'minecraft:lapis_ore', 'minecraft:diamond_ore', 'minecraft:emerald_ore',
    'minecraft:deepslate_coal_ore', 'minecraft:deepslate_iron_ore', 'minecraft:deepslate_copper_ore',
    'minecraft:deepslate_gold_ore', 'minecraft:deepslate_redstone_ore', 'minecraft:deepslate_lapis_ore',
    'minecraft:deepslate_diamond_ore', 'minecraft:deepslate_emerald_ore',
    'minecraft:raw_iron_block', 'minecraft:raw_copper_block', 'minecraft:raw_gold_block',
    'minecraft:sand', 'minecraft:red_sand', 'minecraft:sandstone', 'minecraft:packed_ice', 'minecraft:snow_block',
    'minecraft:podzol', 'minecraft:grass_block', 'minecraft:mud',
})

# Who can live at a site: role -> (entity, profession, level). Wardens and the captain are Village Friends guards.
ROLES = {
    'lightkeeper': ('minecraft:villager', 'oceanexpansion:lightkeeper', 3),
    'warden_knight': ('minecraft:villager', 'villagefriends:knight', 2),
    'warden_archer': ('minecraft:villager', 'villagefriends:archer', 2),
    'captain': ('minecraft:villager', 'villagefriends:knight', 4),
    'smuggler': ('minecraft:villager', 'oceanexpansion:smuggler', 2),
    'smuggler_boss': ('minecraft:villager', 'oceanexpansion:smuggler', 4),
}
YAW = {'south': 0.0, 'west': 90.0, 'north': 180.0, 'east': -90.0}
DIRECTION_ID = {'down': 0, 'up': 1, 'north': 2, 'south': 3, 'west': 4, 'east': 5}

# A design's chests, barrels, pots and minecarts use the loot tables it lists in LOOT_TABLES ('<key>/<name>');
# build.py checks every one exists.
def check_loot(template, loot):
    key = template.name.split('/')[0]
    assert loot.startswith(key + '/') and loot.count('/') == 1, f'{template.name}: loot table {loot} must be one of the design tables ({key}/<name>)'

# Blocks that can hold water (their 'waterlogged' property never shows up in blockstate files).
_WATERLOGGABLE = re.compile(r'(_stairs|_slab|_fence|_pane|_bars|_chain|lantern|candle|sea_pickle|_coral$|_coral_fan$|'
                            r'_coral_wall_fan$|_sign|_trapdoor|^chest|^trapped_chest|^ender_chest|scaffolding|conduit|'
                            r'lightning_rod|pointed_dripstone|amethyst_cluster|_amethyst_bud|glow_lichen|sculk_vein|'
                            r'hanging_roots|mangrove_roots|_grate|decorated_pot|heavy_core|campfire|_leaves|dripleaf|'
                            r'^ladder|^light$|^barrier|_rail$|^rail$|_shelf|resin_clump|^chain$|^iron_bars$|_wall$|'
                            r'oceanexpansion:|seafriends:)')
_NOT_WATERLOGGABLE = re.compile(r'(^sea_lantern$|^jack_o_lantern$|_fence_gate|_wall_banner|_wall_torch|_wall_head|_wall_skull|_glass_pane_dry|^cobblestone_wall_x)')


def waterloggable(name):
    short = name.split(':', 1)[1] if name.startswith('minecraft:') else name
    if name in MOD_BLOCKS: return 'waterlogged' in MOD_BLOCKS[name]
    return bool(_WATERLOGGABLE.search(short)) and not _NOT_WATERLOGGABLE.search(short)


class Byte(int):
    """An NBT byte (TAG_Byte) rather than an int."""


class Float(float):
    """An NBT float (TAG_Float) rather than a double."""


class IntArray(list):
    """An NBT int array (TAG_Int_Array)."""


def _tag_type(value):
    if isinstance(value, (Byte, bool)): return 1
    if isinstance(value, int): return 3
    if isinstance(value, Float): return 5
    if isinstance(value, float): return 6
    if isinstance(value, str): return 8
    if isinstance(value, IntArray): return 11
    if isinstance(value, list): return 9
    if isinstance(value, dict): return 10
    raise TypeError(value)


def _string(value):
    encoded = value.encode('utf-8')
    return struct.pack('>H', len(encoded)) + encoded


def _payload(value):
    kind = _tag_type(value)
    if kind == 1: return struct.pack('>b', int(value))
    if kind == 3: return struct.pack('>i', value)
    if kind == 5: return struct.pack('>f', value)
    if kind == 6: return struct.pack('>d', value)
    if kind == 8: return _string(value)
    if kind == 11: return struct.pack('>i', len(value)) + b''.join(struct.pack('>i', v) for v in value)
    if kind == 9:
        element = _tag_type(value[0]) if value else 10
        assert all(_tag_type(v) == element for v in value), value
        return bytes([element]) + struct.pack('>i', len(value)) + b''.join(_payload(v) for v in value)
    return b''.join(bytes([_tag_type(v)]) + _string(k) + _payload(v) for k, v in value.items()) + b'\0'


def write_nbt(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(gzip.compress(b'\x0a\x00\x00' + _payload(value), mtime=0))


def write_json(rel, value):
    path = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, indent=2) + '\n')


# -- block states ------------------------------------------------------------------------------

_STATE = re.compile(r'^([a-z0-9_:]+)(?:\[(.*)\])?$')


def parse(spec):
    """'oak_stairs[facing=north,half=top]' -> ('minecraft:oak_stairs', {'facing': 'north', 'half': 'top'})."""
    m = _STATE.match(spec)
    assert m, spec
    name = m.group(1) if ':' in m.group(1) else 'minecraft:' + m.group(1)
    props = {}
    if m.group(2):
        for part in m.group(2).split(','):
            k, v = part.split('=')
            props[k.strip()] = v.strip()
    return name, props


def spec(name, props):
    short = name[len('minecraft:'):] if name.startswith('minecraft:') else name
    if not props: return short
    return short + '[' + ','.join(f'{k}={v}' for k, v in sorted(props.items())) + ']'


def full_spec(name, props):
    """With the namespace, as a jigsaw's final_state wants it."""
    return name + ('[' + ','.join(f'{k}={v}' for k, v in sorted(props.items())) + ']' if props else '')


_known = {}


def _vanilla_properties(name):
    """Property names and values a vanilla block shows in its blockstate file, or None if no such block."""
    if name in _known: return _known[name]
    path = os.path.join(CACHE, 'blockstates', name.split(':')[1] + '.json')
    if not name.startswith('minecraft:') or not os.path.exists(path):
        _known[name] = None
        return None
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    props = {}

    def add(key):
        for part in key.split(','):
            if '=' in part:
                k, v = part.split('=')
                props.setdefault(k, set()).update(v.split('|'))

    for key in data.get('variants', {}):
        add(key)
    for part in data.get('multipart', []):
        when = part.get('when', {})
        for cond in when.get('OR', [when]) if 'OR' in when else [when]:
            for k, v in cond.items():
                props.setdefault(k, set()).update(str(v).split('|'))
    _known[name] = props
    return props


def validate_state(name, props, where=''):
    if name in MOD_BLOCKS:
        allowed = MOD_BLOCKS[name]
        for k, v in props.items():
            assert k in allowed and v in allowed[k], f'bad property {k}={v} on {name} {where}'
        return
    assert name.startswith('minecraft:'), f'unknown mod block {name} {where}'
    known = _vanilla_properties(name)
    assert known is not None, f'unknown block {name} {where}'
    for k, v in props.items():
        if k in known:
            assert v in known[k], f'bad value {k}={v} on {name} {where} (allowed {sorted(known[k])})'
        else:
            assert k in HIDDEN_PROPERTIES or k in ('axis', 'rotation', 'facing', 'age', 'level', 'layers', 'type'), \
                f'unknown property {k} on {name} {where}'


# -- templates ---------------------------------------------------------------------------------

HORIZONTAL = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}
LEFT = {'north': 'west', 'west': 'south', 'south': 'east', 'east': 'north'}
RIGHT = {v: k for k, v in LEFT.items()}
ANCHOR = 'oceanexpansion:anchor'


class Template:
    """One structure piece. Coordinates are template-local: x east, y up, z south, all from 0."""

    def __init__(self, name, size, seed=None, wet=False, waterline=None):
        """`wet`: the template stands in the sea; every cell below `waterline` (template y; default the whole
        template) is under water, so blocks there that can hold water are written waterlogged."""
        self.name, self.size = name, tuple(size)
        self.wet = wet
        self.waterline = self.size[1] if waterline is None else waterline
        self.dry = set()   # cells kept dry inside a wet template (keep_dry)
        self.blocks = {}   # (x, y, z) -> (name, props)
        self.nbt = {}      # (x, y, z) -> block entity compound
        self.entities = []
        self.jigsaws = []
        self.notes = {}    # facts for tests and docs: residents, chests, haunts, features...
        self.rng = random.Random(seed if seed is not None else name)

    def inside(self, x, y, z):
        return all(0 <= p < s for p, s in zip((x, y, z), self.size))

    def set(self, x, y, z, block, nbt=None):
        assert self.inside(x, y, z), (self.name, x, y, z, block)
        if block is None:
            self.blocks.pop((x, y, z), None)
            self.nbt.pop((x, y, z), None)
            return
        name, props = parse(block) if isinstance(block, str) else block
        self.blocks[(x, y, z)] = (name, props)
        if nbt is not None: self.nbt[(x, y, z)] = nbt
        else: self.nbt.pop((x, y, z), None)

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return None if b is None else spec(*b)

    def name_at(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return None if b is None else b[0]

    def fill(self, a, b, block):
        """Fill the box a..b (inclusive). `block` may be a callable (x, y, z) -> spec (or None to leave void)."""
        for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
            for z in range(min(a[2], b[2]), max(a[2], b[2]) + 1):
                for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                    self.set(x, y, z, block(x, y, z) if callable(block) else block)

    def flood(self, a, b):
        """Fill the box with water (open, flooded rooms; always placed)."""
        self.fill(a, b, 'water')

    def keep_dry(self, a, b):
        """Cells in the box are not under water even below the waterline (an air pocket, a sealed room)."""
        for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
            for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                for z in range(min(a[2], b[2]), max(a[2], b[2]) + 1):
                    self.dry.add((x, y, z))

    def submerged(self, x, y, z):
        return self.wet and y < self.waterline and (x, y, z) not in self.dry

    def carve(self, a, b):
        """Open air in the box a..b (inclusive)."""
        self.fill(a, b, 'air')

    def walls(self, a, b, block):
        """Only the four vertical sides of the box a..b."""
        for y in range(a[1], b[1] + 1):
            for x in range(a[0], b[0] + 1):
                for z in (a[2], b[2]): self.set(x, y, z, block(x, y, z) if callable(block) else block)
            for z in range(a[2], b[2] + 1):
                for x in (a[0], b[0]): self.set(x, y, z, block(x, y, z) if callable(block) else block)

    def shell(self, a, b, block, thickness=1):
        """Line the rock around the box a..b with a NATURAL block, `thickness` deep (the box itself is untouched).
        Only cells still unset are lined, so call it after building the room."""
        if not callable(block):
            name, _ = parse(block) if isinstance(block, str) else block
            assert name in NATURAL, f'shell() wants a NATURAL block, not {name}'
        for y in range(a[1] - thickness, b[1] + thickness + 1):
            for z in range(a[2] - thickness, b[2] + thickness + 1):
                for x in range(a[0] - thickness, b[0] + thickness + 1):
                    if a[0] <= x <= b[0] and a[1] <= y <= b[1] and a[2] <= z <= b[2]: continue
                    if self.inside(x, y, z) and (x, y, z) not in self.blocks:
                        self.set(x, y, z, block(x, y, z) if callable(block) else block)

    # -- connections -------------------------------------------------------------------------

    def jigsaw(self, x, y, z, orientation, name, target='minecraft:empty', pool='minecraft:empty', final='air',
               joint='aligned', placement=0, selection=0):
        """A jigsaw connector. Horizontal ones are '<facing>_up' and sit in the outer face of the template,
        pointing out of it. `pool` is where the next piece comes from; `target` is the name of the jigsaw on that
        piece this one joins to; `final` is the block left in its place."""
        q = lambda s: s if ':' in s else NS + ':' + s
        final_name, final_props = parse(final)
        validate_state(final_name, final_props, f'final state in {self.name}')
        self.set(x, y, z, f'jigsaw[orientation={orientation}]', {
            'id': 'minecraft:jigsaw', 'name': q(name), 'target': q(target), 'pool': q(pool),
            'final_state': full_spec(final_name, final_props),
            'joint': joint, 'placement_priority': placement, 'selection_priority': selection})
        self.jigsaws.append({'pos': (x, y, z), 'orientation': orientation, 'name': q(name), 'target': q(target), 'pool': q(pool)})

    def anchor(self, x, y, z, floor='stone_bricks'):
        """Where a structure stands: a floor block in the middle of its start piece (people walk at y + 1). Every
        start piece has exactly one; the game sets the delve's chosen height here. `floor` is the block left there."""
        assert not any(j['name'] == ANCHOR for j in self.jigsaws), f'{self.name} has two anchors'
        final_name, final_props = parse(floor)
        validate_state(final_name, final_props, f'anchor floor in {self.name}')
        self.set(x, y, z, 'jigsaw[orientation=up_north]', {
            'id': 'minecraft:jigsaw', 'name': ANCHOR, 'target': 'minecraft:empty', 'pool': 'minecraft:empty',
            'final_state': full_spec(final_name, final_props), 'joint': 'rollable',
            'placement_priority': 0, 'selection_priority': 0})
        self.jigsaws.append({'pos': (x, y, z), 'orientation': 'up_north', 'name': ANCHOR, 'target': 'minecraft:empty',
                             'pool': 'minecraft:empty'})
        self.notes['anchor'] = (x, y, z)

    # -- containers and furnishings ------------------------------------------------------------

    def chest(self, x, y, z, facing, loot, kind='chest', custom_name=None):
        """A chest, trapped_chest or barrel filled from one of LOOT (e.g. 'camp/supplies')."""
        check_loot(self, loot)
        props = {'facing': facing}
        if kind == 'barrel': props['open'] = 'false'
        if kind in ('chest', 'trapped_chest'): props.update({'type': 'single', 'waterlogged': 'false'})
        nbt = {'id': 'minecraft:' + ('chest' if kind == 'chest' else 'trapped_chest' if kind == 'trapped_chest' else kind),
               'LootTable': f'{NS}:chests/{loot}'}
        if custom_name: nbt['CustomName'] = {'text': custom_name}
        self.set(x, y, z, ('minecraft:' + kind, props), nbt)
        self.notes.setdefault('loot', []).append(nbt['LootTable'])

    def barrel(self, x, y, z, facing, loot):
        self.chest(x, y, z, facing, loot, kind='barrel')

    def pot(self, x, y, z, facing='north', loot=None, sherds=None):
        """A decorated pot (sherds: four item ids back/left/right/front, default plain bricks), optionally with loot."""
        nbt = {'id': 'minecraft:decorated_pot'}
        if sherds: nbt['sherds'] = [s if ':' in s else 'minecraft:' + s for s in sherds]
        if loot:
            check_loot(self, loot)
            nbt['LootTable'] = f'{NS}:chests/{loot}'
            self.notes.setdefault('loot', []).append(nbt['LootTable'])
        self.set(x, y, z, f'decorated_pot[facing={facing}]', nbt)

    def book(self, title, author, pages):
        """A written book item (for a lectern or a chest). Title at most 32 characters; pages are plain text."""
        assert len(title) <= 32, title
        assert pages and all(len(p) <= 700 for p in pages), f'{title}: keep pages short (about 14 lines of ~19 chars)'
        return {'id': 'minecraft:written_book', 'count': 1, 'components': {
            'minecraft:written_book_content': {'title': title, 'author': author, 'pages': list(pages)}}}

    def lectern(self, x, y, z, facing, title, author, pages):
        """A lectern holding a written book: the place's own record (a log, a ledger, a list of names...)."""
        self.set(x, y, z, f'lectern[facing={facing},has_book=true,powered=false]',
                 {'id': 'minecraft:lectern', 'Book': self.book(title, author, pages), 'Page': 0})
        self.notes.setdefault('books', []).append(title)

    def sign(self, x, y, z, lines, facing='north', wood='spruce', wall=True, color='black', glowing=False):
        """A sign reading `lines` (up to four, ~15 characters each) on its front, which faces `facing`."""
        text = (list(lines) + [''] * 4)[:4]
        nbt = {'id': 'minecraft:sign', 'is_waxed': Byte(1),
               'front_text': {'messages': text, 'color': color, 'has_glowing_text': Byte(1 if glowing else 0)},
               'back_text': {'messages': [''] * 4, 'color': 'black', 'has_glowing_text': Byte(0)}}
        if wall:
            self.set(x, y, z, f'{wood}_wall_sign[facing={facing},waterlogged=false]', nbt)
        else:
            rotation = {'south': 0, 'west': 4, 'north': 8, 'east': 12}[facing]
            self.set(x, y, z, f'{wood}_sign[rotation={rotation},waterlogged=false]', nbt)

    def banner(self, x, y, z, facing, color, patterns=(), wall=True):
        """A banner with vanilla patterns: [('minecraft:border', 'white'), ...]. Wall banners hang on the block
        behind them and face `facing`."""
        nbt = {'id': 'minecraft:banner', 'patterns': [{'pattern': p if ':' in p else 'minecraft:' + p, 'color': c}
                                                        for p, c in patterns]}
        if wall: self.set(x, y, z, f'{color}_wall_banner[facing={facing}]', nbt)
        else: self.set(x, y, z, f'{color}_banner[rotation={ {"south": 0, "west": 4, "north": 8, "east": 12}[facing] }]', nbt)

    def spawner(self, x, y, z, mob, count=2, nearby=5, delay=(300, 700)):
        """A vanilla monster spawner (vanilla mobs only: minecraft:skeleton, cave_spider, zombie...)."""
        assert mob.startswith('minecraft:'), 'spawners take vanilla mobs only (other mods may be missing)'
        self.set(x, y, z, 'spawner', {'id': 'minecraft:mob_spawner', 'SpawnData': {'entity': {'id': mob}},
                                      'SpawnCount': count, 'MaxNearbyEntities': nearby, 'RequiredPlayerRange': 12,
                                      'MinSpawnDelay': delay[0], 'MaxSpawnDelay': delay[1], 'Delay': 80})
        self.notes.setdefault('spawners', []).append(mob)

    def haunt(self, x, y, z, kind):
        """An invisible marker: the first time a player comes within 14 blocks, the place's guardians rise here
        (drowned_crew, drowned_captain, guardians, frozen_crew or deep_lurkers; see DESIGN.md) and the marker is gone. Leave 2 blocks of
        air above it."""
        assert kind in HAUNTS, kind
        self.set(x, y, z, f'oceanexpansion:haunt[kind={kind}]', {'id': 'oceanexpansion:haunt'})
        self.notes.setdefault('haunts', []).append(kind)

    def bed(self, x, y, z, facing, color='red'):
        """A bed whose foot is at (x, y, z) and whose head lies one block toward `facing`."""
        dx, dz = HORIZONTAL[facing]
        self.set(x, y, z, f'{color}_bed[facing={facing},part=foot,occupied=false]')
        self.set(x + dx, y, z + dz, f'{color}_bed[facing={facing},part=head,occupied=false]')
        self.notes['beds'] = self.notes.get('beds', 0) + 1

    def door(self, x, y, z, facing, kind='spruce_door', hinge='left', open_=False):
        """A two-block door standing at (x, y, z) and (x, y + 1, z); `facing` is the way you face walking out."""
        o = 'true' if open_ else 'false'
        self.set(x, y, z, f'{kind}[facing={facing},half=lower,hinge={hinge},open={o},powered=false]')
        self.set(x, y + 1, z, f'{kind}[facing={facing},half=upper,hinge={hinge},open={o},powered=false]')

    # -- entities --------------------------------------------------------------------------------

    def resident(self, x, y, z, role, facing='south'):
        """Someone who lives here (see ROLES), standing on the block at y - 1. The game gives them their name,
        job, look and gear when they first load."""
        assert role in ROLES, role
        entity, profession, level = ROLES[role]
        nbt = {'id': entity, 'PersistenceRequired': Byte(1), 'Age': 0,
               'VillagerData': {'type': 'minecraft:plains', 'profession': profession, 'level': level},
               'Xp': 10 * level, 'Tags': [f'{NS}.resident.{role}'], 'Rotation': [Float(YAW[facing]), Float(0.0)]}
        self.entities.append({'pos': [x + .5, float(y), z + .5], 'blockPos': [x, y, z], 'nbt': nbt})
        self.notes.setdefault('residents', []).append(role)

    def creature(self, x, y, z, entity, facing='south', nbt=None):
        """An animal that lives here (stays put: it never despawns), e.g. 'minecraft:nautilus' or
        'minecraft:tropical_fish'. Mod creatures only if this mod adds them."""
        assert entity.startswith('minecraft:') or entity.startswith(NS + ':'), entity
        data = {'id': entity, 'PersistenceRequired': Byte(1), 'Rotation': [Float(YAW[facing]), Float(0.0)]}
        if nbt: data.update(nbt)
        self.entities.append({'pos': [x + .5, float(y), z + .5], 'blockPos': [x, y, z], 'nbt': data})
        self.notes.setdefault('creatures', []).append(entity)

    def entrance(self, x, y, z):
        """Where you walk or swim in (the floor cell in front of the door, on the template's edge)."""
        self.notes.setdefault('entrances', []).append((x, y, z))

    def item_frame(self, x, y, z, facing, item, glow=False):
        """An item frame hung on the block behind it, facing `facing` (or 'up'/'down' on a floor/ceiling)."""
        nbt = {'id': 'minecraft:glow_item_frame' if glow else 'minecraft:item_frame', 'Facing': Byte(DIRECTION_ID[facing]),
               'block_pos': IntArray([x, y, z]), 'Fixed': Byte(1), 'Invisible': Byte(0),
               'Item': {'id': item if ':' in item else 'minecraft:' + item, 'count': 1}, 'ItemDropChance': Float(0.0)}
        self.entities.append({'pos': [x + .5, y + .5, z + .5], 'blockPos': [x, y, z], 'nbt': nbt})

    def minecart(self, x, y, z, loot=None, facing='south'):
        """A minecart standing on the rail at (x, y, z); with `loot`, a chest minecart."""
        nbt = {'id': 'minecraft:chest_minecart' if loot else 'minecraft:minecart',
               'Rotation': [Float(YAW[facing]), Float(0.0)]}
        if loot:
            check_loot(self, loot)
            nbt['LootTable'] = f'{NS}:chests/{loot}'
            self.notes.setdefault('loot', []).append(nbt['LootTable'])
        self.entities.append({'pos': [x + .5, y + 0.0625, z + .5], 'blockPos': [x, y, z], 'nbt': nbt})

    # -- checks and output --------------------------------------------------------------------------

    def validate(self):
        for pos, (name, props) in self.blocks.items():
            validate_state(name, props, f'at {pos} in {self.name}')
        for j in self.jigsaws:
            if j['name'] == ANCHOR: continue
            x, y, z = j['pos']
            front = j['orientation'].split('_')[0]
            # A jigsaw must face out of the template, or its partner would land inside it.
            dx, dy, dz = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0),
                          'up': (0, 1, 0), 'down': (0, -1, 0)}[front]
            assert not self.inside(x + dx, y + dy, z + dz), (self.name, 'jigsaw faces inward', j)
        for pos, nbt in self.nbt.items():
            assert pos in self.blocks, (self.name, 'block entity without a block', pos)
        for e in self.entities:
            assert self.inside(*e['blockPos']), (self.name, 'entity outside the template', e['blockPos'])

    def save(self):
        self.validate()
        palette, index, blocks = [], {}, []
        for pos in sorted(self.blocks, key=lambda p: (p[1], p[2], p[0])):
            name, props = self.blocks[pos]
            if waterloggable(name) and name != 'minecraft:water':
                props = dict(props)
                props['waterlogged'] = 'true' if self.submerged(*pos) else 'false'
            if name == 'minecraft:water' and not self.submerged(*pos) and self.wet:
                pass
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                entry = {'id': name}
                if props: entry['properties'] = dict(sorted(props.items()))
                palette.append(entry)
            entry = {'pos': list(pos), 'state': index[key]}
            if pos in self.nbt: entry['nbt'] = self.nbt[pos]
            blocks.append(entry)
        data = {'DataVersion': DATA_VERSION, 'size': list(self.size), 'palette': palette, 'blocks': blocks,
                'entities': self.entities}
        write_nbt(os.path.join(RES, 'data', NS, 'structure', self.name + '.nbt'), data)
        return {'id': f'{NS}:{self.name}', 'size': list(self.size), 'blocks': len(self.blocks),
                'jigsaws': [{**j, 'pos': list(j['pos'])} for j in self.jigsaws], 'notes': self.notes}


# -- small helpers ------------------------------------------------------------------------------

def facing_of(dx, dz):
    return {(0, -1): 'north', (0, 1): 'south', (-1, 0): 'west', (1, 0): 'east'}[(dx, dz)]


def chance(rng, p):
    return rng.random() < p


# -- light check -----------------------------------------------------------------------------------

LIGHT = {'lantern': 15, 'copper_lantern': 15, 'soul_lantern': 10, 'torch': 14, 'wall_torch': 14, 'copper_torch': 14,
         'copper_wall_torch': 14, 'soul_torch': 10, 'soul_wall_torch': 10, 'campfire': 15, 'soul_campfire': 10,
         'glowstone': 15, 'sea_lantern': 15, 'shroomlight': 15, 'jack_o_lantern': 15, 'ochre_froglight': 15,
         'verdant_froglight': 15, 'pearlescent_froglight': 15, 'end_rod': 14, 'redstone_lamp': 15, 'beacon': 15,
         'conduit': 15, 'lava': 15, 'magma_block': 3, 'glow_lichen': 7, 'crying_obsidian': 10, 'amethyst_cluster': 5,
         'large_amethyst_bud': 4, 'medium_amethyst_bud': 2, 'small_amethyst_bud': 1, 'furnace': 13, 'blast_furnace': 13,
         'smoker': 13, 'brewing_stand': 1, 'sculk_catalyst': 6, 'fire': 15, 'soul_fire': 10, 'cave_vines': 14,
         'cave_vines_plant': 14, 'copper_bulb': 15, 'sea_pickle': 6, 'tide_lamp': 15, 'signal_lamp': 15}
_SEE_THROUGH = ('air', 'glass', 'pane', 'bars', 'fence', 'wall', 'slab', 'stairs', 'door', 'trapdoor', 'lantern', 'torch',
                'candle', 'carpet', 'rail', 'ladder', 'sign', 'banner', 'button', 'lever', 'plate', 'chain', 'vine', 'lichen',
                'flower', 'mushroom', 'sapling', 'roots', 'grass', 'fern', 'bush', 'cobweb', 'scaffolding', 'campfire',
                'fire', 'water', 'lava', 'leaves', 'bud', 'cluster', 'dripstone', 'pot', 'chest', 'lectern', 'anvil',
                'cauldron', 'bed', 'skull', 'head', 'frame', 'shelf', 'grindstone', 'stonecutter', 'bell', 'rod', 'haunt',
                'jigsaw', 'brewing_stand', 'hopper', 'composter', 'pickle', 'kelp', 'seagrass', 'moss_carpet', 'dummy', 'target',
                'cave_vines', 'spore', 'azalea', 'leaf_litter', 'hanging')


def _emission(name, props):
    short = name.split(':')[1]
    if props.get('lit') == 'false': return 0
    if short.endswith('candle') or short.endswith('_candle'):
        return 3 * int(props.get('candles', '1')) if props.get('lit') == 'true' else 0
    if short in ('furnace', 'blast_furnace', 'smoker', 'redstone_lamp'): return LIGHT[short] if props.get('lit') == 'true' else 0
    if short in ('cave_vines', 'cave_vines_plant'): return 14 if props.get('berries') == 'true' else 0
    if short == 'copper_bulb': return 15 if props.get('lit') == 'true' else 0
    if short == 'sea_pickle': return 3 + 3 * int(props.get('pickles', '1')) if props.get('waterlogged', 'true') == 'true' else 0
    return LIGHT.get(short, 0)


def light_map(t):
    """Block light (0..15) in every cell of the template, spread through air and see-through blocks; unset cells
    count as solid rock. A rough check (no sky light, everything leaks evenly)."""
    from collections import deque
    level = {}
    queue = deque()
    for pos, (name, props) in t.blocks.items():
        e = _emission(name, props)
        if e:
            level[pos] = e
            queue.append(pos)

    def open_(pos):
        b = t.blocks.get(pos)
        return b is not None and any(w in b[0] for w in _SEE_THROUGH)

    while queue:
        pos = queue.popleft()
        v = level[pos] - 1
        if v <= 0: continue
        x, y, z = pos
        for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)):
            if not t.inside(*n) or not open_(n) or level.get(n, 0) >= v: continue
            level[n] = v
            queue.append(n)
    return level


def dark_spots(t, threshold=8):
    """Walkable cells (open, open above, a solid block below) whose block light is under `threshold`: where a
    monster could spawn in a lit, lived-in place."""
    level = light_map(t)
    out = []
    for (x, y, z), (name, _) in t.blocks.items():
        if name != 'minecraft:air' or y == 0: continue
        above = t.blocks.get((x, y + 1, z)); below = t.blocks.get((x, y - 1, z))
        if above is None or above[0] != 'minecraft:air' or below is None: continue
        if any(w in below[0] for w in _SEE_THROUGH): continue
        if level.get((x, y, z), 0) < threshold: out.append((x, y, z))
    return sorted(out)
