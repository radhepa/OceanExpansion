"""Shared helpers for the three lived-in surface sites (lighthouse, fort, smugglers). Not a design itself.

  * Noise / wobble: smooth, deterministic noise for natural islets and sea stacks (irregular radii, ledges);
  * rock(): a weathered coastal rock palette picked from noise (stone, andesite, tuff, cobble, moss near the sea);
  * connect(): sets fence / pane / bars / wall connections from their neighbours (the shapes the game would give);
  * small props: lantern posts, a moored rowboat, a block ballista, the Tidewatch banner;
  * scatter helpers for barnacles, kelp and seagrass on underwater rock.
"""
import math

from kit import HORIZONTAL, dark_spots

# The Tidewatch banner: blue field, a white lighthouse (centre stripe + light at the top) inside a white border.
TIDEWATCH = ('blue', [('stripe_center', 'white'), ('triangle_top', 'white'), ('border', 'white')])
# The same patterns for a loot table's set_banner_pattern modifier.
TIDEWATCH_LOOT = [{'type': 'minecraft:set_banner_pattern', 'append': False,
                   'patterns': [{'pattern': 'minecraft:' + p, 'color': c} for p, c in TIDEWATCH[1]]}]


def tidewatch_banner(t, x, y, z, facing, wall=True):
    t.banner(x, y, z, facing, TIDEWATCH[0], TIDEWATCH[1], wall=wall)


# -- noise ---------------------------------------------------------------------------------------

def _hash(seed, *ns):
    h = (seed * 0x9E3779B1) & 0xffffffff
    for n in ns:
        h = (h ^ (n & 0xffffffff)) * 0x85EBCA6B & 0xffffffff
        h ^= h >> 13
        h = h * 0xC2B2AE35 & 0xffffffff
        h ^= h >> 16
    return h / 0xffffffff


def _smooth(t):
    return t * t * (3 - 2 * t)


class Noise:
    """Smooth value noise in 0..1 over (x, z) or (x, y, z); `scale` is the feature size in blocks."""

    def __init__(self, seed, scale=6.0):
        self.seed, self.scale = seed, float(scale)

    def __call__(self, x, z, y=None):
        if y is None:
            fx, fz = x / self.scale, z / self.scale
            ix, iz = math.floor(fx), math.floor(fz)
            tx, tz = _smooth(fx - ix), _smooth(fz - iz)
            v = lambda a, b: _hash(self.seed, a, b)
            top = v(ix, iz) + (v(ix + 1, iz) - v(ix, iz)) * tx
            bot = v(ix, iz + 1) + (v(ix + 1, iz + 1) - v(ix, iz + 1)) * tx
            return top + (bot - top) * tz
        fx, fy, fz = x / self.scale, y / self.scale, z / self.scale
        ix, iy, iz = math.floor(fx), math.floor(fy), math.floor(fz)
        tx, ty, tz = _smooth(fx - ix), _smooth(fy - iy), _smooth(fz - iz)
        out = 0.0
        for dy, wy in ((0, 1 - ty), (1, ty)):
            for dz, wz in ((0, 1 - tz), (1, tz)):
                for dx, wx in ((0, 1 - tx), (1, tx)):
                    out += wx * wy * wz * _hash(self.seed, ix + dx, iy + dy, iz + dz)
        return out


def wobble(rng, terms=((2, .10), (3, .08), (5, .05), (7, .03))):
    """f(angle) ~ 1 +- a little: an irregular radius multiplier (sums of sines with random phases)."""
    phases = [(n, a * (0.7 + 0.6 * rng.random()), rng.random() * 2 * math.pi) for n, a in terms]
    return lambda th: 1 + sum(a * math.sin(n * th + p) for n, a, p in phases)


# -- rock ----------------------------------------------------------------------------------------

class Rock:
    """A coastal rock palette: big patches of stone / andesite / tuff, cobble and moss near the waterline,
    with a little diorite and gravel. `sea` is the template row of sea level (the first air row)."""

    def __init__(self, seed, sea, mossy=0.35):
        self.a = Noise(seed * 7 + 1, 5.5)
        self.b = Noise(seed * 7 + 2, 3.0)
        self.c = Noise(seed * 7 + 3, 2.2)
        self.sea, self.mossy = sea, mossy

    def __call__(self, x, y, z):
        v = self.a(x, z, y * 1.4)
        w = self.b(x, z, y)
        fine = self.c(x, z, y)
        near_sea = abs(y - self.sea) <= 2
        if near_sea and fine < self.mossy * 0.55: return 'mossy_cobblestone'
        if near_sea and fine > 0.86: return 'cobblestone'
        if v < 0.30: return 'andesite'
        if v < 0.58: return 'stone' if w > 0.22 else 'cobblestone'
        if v < 0.76: return 'tuff'
        if w > 0.80: return 'diorite'
        return 'stone'


# -- connections -------------------------------------------------------------------------------

_THIN = ('air', 'water', 'pane', 'bars', 'fence', 'wall', 'slab', 'stairs', 'door', 'trapdoor', 'lantern', 'torch',
         'candle', 'carpet', 'rail', 'ladder', 'sign', 'banner', 'button', 'lever', 'plate', 'chain', 'vine', 'lichen',
         'flower', 'mushroom', 'sapling', 'roots', 'grass', 'fern', 'bush', 'cobweb', 'scaffolding', 'campfire', 'fire',
         'leaves', 'bud', 'cluster', 'dripstone', 'pot', 'chest', 'lectern', 'anvil', 'cauldron', 'bed', 'skull', 'head',
         'shelf', 'grindstone', 'stonecutter', 'bell', 'rod', 'haunt', 'pickle', 'kelp', 'seagrass', 'cake', 'composter',
         'hopper', 'brewing_stand', 'kelp', 'coral', 'petals', 'wildflowers', 'litter', 'egg', 'dried_ghast')


def _full(name):
    """Roughly: does this block offer a full, sturdy side for a fence or pane to join?"""
    if not name.startswith('minecraft:'): return False
    short = name.split(':')[1]
    if short.endswith('glass') or short == 'glass': return True
    return not any(w in short for w in _THIN)


def _kind(name):
    short = name.split(':')[1]
    if short.endswith('_fence'): return 'nether_fence' if short.startswith('nether') else 'fence'
    if short.endswith('_pane') or short.endswith('_bars'): return 'pane'
    if short.endswith('_wall') and 'banner' not in short and 'sign' not in short and 'torch' not in short \
            and 'head' not in short and 'skull' not in short and 'fan' not in short: return 'wall'
    return None


def connect(t):
    """Give every fence, pane, bars and wall in `t` the side connections its neighbours call for."""
    for (x, y, z), (name, props) in list(t.blocks.items()):
        kind = _kind(name)
        if kind is None: continue
        new = {k: v for k, v in props.items() if k not in ('north', 'south', 'east', 'west', 'up')}
        for d, (dx, dz) in HORIZONTAL.items():
            nb = t.blocks.get((x + dx, y, z + dz))
            ok = False
            if nb is not None:
                nk = _kind(nb[0])
                nshort = nb[0].split(':')[1]
                if nshort.endswith('_fence_gate'):
                    f = nb[1].get('facing', 'north')
                    ok = kind in ('fence', 'wall') and (f in ('north', 'south')) == (d in ('east', 'west'))
                elif kind == 'fence': ok = nk == 'fence' or _full(nb[0])
                elif kind == 'nether_fence': ok = nk == 'nether_fence' or _full(nb[0])
                elif kind == 'pane': ok = nk in ('pane', 'wall') or _full(nb[0])
                elif kind == 'wall': ok = nk in ('pane', 'wall') or _full(nb[0])
            if kind == 'pane': new[d] = 'true' if ok else 'false'
            elif ok: new[d] = 'low' if kind == 'wall' else 'true'
        t.blocks[(x, y, z)] = (name, new)


# -- props ---------------------------------------------------------------------------------------

def lantern_post(t, x, y, z, height=2, wood='spruce', hanging_arm=None):
    """A fence post `height` tall standing at (x, y, z) with a lantern on top, or, with `hanging_arm` (a
    direction), a lantern hanging from a short arm at the top."""
    for i in range(height): t.set(x, y + i, z, f'{wood}_fence')
    if hanging_arm is None:
        t.set(x, y + height, z, 'lantern[hanging=false]')
        return
    dx, dz = HORIZONTAL[hanging_arm]
    t.set(x, y + height, z, f'{wood}_fence')
    t.set(x + dx, y + height, z + dz, f'{wood}_fence')
    t.set(x + dx, y + height - 1, z + dz, 'lantern[hanging=true]')


def rowboat(t, x, y, z, along='x', length=5, wood='spruce', oars=True):
    """A small moored rowboat of blocks. (x, y, z) is the stern-left corner of its bottom row, which should be
    the top water row (its slabs sit flush with the surface); the gunwale is the row above. 3 wide."""
    ax = along == 'x'

    def put(i, j, dy, block):
        px, pz = (x + i, z + j) if ax else (x + j, z + i)
        t.set(px, y + dy, pz, block)
    fwd, back = ('east', 'west') if ax else ('south', 'north')
    side_a, side_b = ('north', 'south') if ax else ('west', 'east')
    for i in range(length):
        for j in range(3):
            bow = i == length - 1
            if bow and j != 1: continue
            put(i, j, 0, f'{wood}_slab[type=top]')
    for i in range(length):
        for j in range(3):
            bow = i == length - 1
            if bow:
                if j == 1: put(i, j, 1, f'{wood}_stairs[facing={back},half=bottom]')
                continue
            edge = i == 0 or j != 1
            if i == length - 2 and j != 1:
                put(i, j, 1, f'{wood}_stairs[facing={side_b if j == 0 else side_a},half=bottom]')
            elif edge:
                put(i, j, 1, f'{wood}_slab[type=bottom]')
            else:
                put(i, j, 1, 'air')
    put(2, 1, 1, f'{wood}_slab[type=bottom]')     # the thwart (seat)
    if oars:
        put(2, 0, 1, f'{wood}_fence')
        put(1, 2, 1, f'{wood}_trapdoor[facing={side_b},half=bottom,open=false]')


def ballista(t, x, y, z, facing, wood='spruce'):
    """A siege ballista standing on the floor block below (x, y, z), shooting toward `facing`: a post, a bow beam
    of fences, a slab stock and a bolt (an end rod: it glows a little at night)."""
    fx, fz = HORIZONTAL[facing]
    rx, rz = -fz, fx
    t.set(x, y, z, f'{wood}_fence')
    t.set(x, y + 1, z, f'{wood}_fence')
    for s in (-1, 1):
        t.set(x + s * rx, y + 1, z + s * rz, f'{wood}_fence')
        t.set(x + s * rx - fx, y + 1, z + s * rz - fz, f'iron_chain[axis={"x" if rx else "z"}]')
    t.set(x - fx, y + 1, z - fz, f'{wood}_slab[type=bottom]')
    t.set(x - 2 * fx, y, z - 2 * fz, f'{wood}_trapdoor[facing={facing},half=bottom,open=false]')
    t.set(x + fx, y + 1, z + fz, f'end_rod[facing={facing}]')


# -- life on the rock ------------------------------------------------------------------------------

def shore_life(t, sea, rng, barnacles=0.22, kelp=0.10, grass=0.35, rock_names=None):
    """Barnacles on rock faces just under the surface, kelp and seagrass on underwater rock tops. Only touches
    unset cells under the waterline (template rows below `sea`)."""
    solid = lambda p: p in t.blocks and t.blocks[p][0] != 'minecraft:water' and (
        rock_names is None or t.blocks[p][0].split(':')[1] in rock_names)
    cells = list(t.blocks.keys())
    for (x, y, z) in cells:
        if y >= sea or not solid((x, y, z)): continue
        # barnacles on the four sides, in the top three water rows
        if y >= sea - 3:
            for d, (dx, dz) in HORIZONTAL.items():
                n = (x + dx, y, z + dz)
                if t.inside(*n) and n not in t.blocks and rng.random() < barnacles:
                    t.set(*n, f'oceanexpansion:barnacles[facing={d}]')
        # plants on top
        up = (x, y + 1, z)
        if y + 1 >= sea - 1 or not t.inside(*up) or up in t.blocks: continue
        r = rng.random()
        if r < kelp:
            top = min(sea - 2, y + 1 + rng.randint(1, 5))
            for yy in range(y + 1, top):
                if (x, yy, z) in t.blocks: break
                t.set(x, yy, z, 'kelp_plant')
            if (x, top, z) not in t.blocks: t.set(x, top, z, 'kelp')
        elif r < kelp + grass:
            if rng.random() < 0.3 and y + 2 < sea - 1 and (x, y + 2, z) not in t.blocks:
                t.set(x, y + 1, z, 'tall_seagrass[half=lower]')
                t.set(x, y + 2, z, 'tall_seagrass[half=upper]')
            else:
                t.set(x, y + 1, z, 'seagrass')


def report(t, label=None):
    """Dark walkable cells in a lived-in piece (for development)."""
    spots = dark_spots(t)
    print(f'{label or t.name}: {len(spots)} dark spots', spots[:12])
    return spots
