"""Shared helpers for the natural wonders (whale.py, grotto.py, vents.py): smooth noise, organic lines and
curves, and the life that grows on rock and bone under the sea. Not a site of its own (no KEY)."""
import math
import zlib
from functools import lru_cache

CORALS = ('tube', 'brain', 'bubble', 'fire', 'horn')
DIRS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0), 'up': (0, 1, 0),
        'down': (0, -1, 0)}
SIDES = ('north', 'south', 'west', 'east')
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}

# -- noise ---------------------------------------------------------------------------------------------


@lru_cache(maxsize=None)
def _seed(seed):
    return zlib.crc32(seed.encode()) if isinstance(seed, str) else int(seed)


@lru_cache(maxsize=1 << 18)
def _lattice(ix, iy, iz, seed):
    n = (ix * 374761393 + iy * 668265263 + iz * 1442695041 + seed * 974634281) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFFFF) / float(0x1000000)


def _hash(ix, iy, iz, seed):
    return _lattice(ix, iy, iz, _seed(seed))


def noise(x, y, z, scale=4.0, seed=0):
    """Smooth value noise in 0..1."""
    seed = _seed(seed)
    x, y, z = x / scale, y / scale, z / scale
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    sx, sy, sz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    L = _lattice
    a0 = L(ix, iy, iz, seed); a1 = L(ix + 1, iy, iz, seed)
    b0 = L(ix, iy + 1, iz, seed); b1 = L(ix + 1, iy + 1, iz, seed)
    c0 = L(ix, iy, iz + 1, seed); c1 = L(ix + 1, iy, iz + 1, seed)
    d0 = L(ix, iy + 1, iz + 1, seed); d1 = L(ix + 1, iy + 1, iz + 1, seed)
    x00 = a0 + (a1 - a0) * sx; x10 = b0 + (b1 - b0) * sx
    x01 = c0 + (c1 - c0) * sx; x11 = d0 + (d1 - d0) * sx
    y0 = x00 + (x10 - x00) * sy; y1 = x01 + (x11 - x01) * sy
    return y0 + (y1 - y0) * sz


def fbm(x, y, z, scale=6.0, seed=0, octaves=3):
    """Layered noise in about 0..1 (rougher than noise())."""
    seed = _seed(seed)
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * noise(x, y, z, scale, seed + 101 * o)
        norm += amp
        amp *= 0.5
        scale /= 2.0
    return total / norm


def rnd(x, y, z, seed=0):
    """A fixed random number in 0..1 for one cell."""
    return _hash(int(x), int(y), int(z), _seed(seed) + 7)


# -- lines and curves ------------------------------------------------------------------------------------


def _r(v):
    return int(math.floor(v + 0.5))


def line(a, b):
    """Integer cells from a to b (floats welcome); each cell shares a face with the one before (no gaps)."""
    n = max(1, int(max(abs(b[i] - a[i]) for i in range(3)) * 3) + 1)
    out, last = [], None
    for i in range(n + 1):
        t = i / n
        p = tuple(_r(a[k] + (b[k] - a[k]) * t) for k in range(3))
        if p == last: continue
        if last is not None:
            cur = list(last)
            for k in (1, 0, 2):   # step y first, so a falling bone stays joined
                if p[k] != cur[k]:
                    cur[k] = p[k]
                    if tuple(cur) != p: out.append(tuple(cur))
        out.append(p)
        last = p
    return out


def polyline(points):
    out = []
    for a, b in zip(points, points[1:]):
        for c in line(a, b):
            if not out or out[-1] != c: out.append(c)
    return out


def catmull(points, per=6):
    """A smooth curve through the control points (each a tuple of floats), sampled `per` times a segment."""
    if len(points) < 3: return list(points)
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(len(p1))))
    out.append(points[-1])
    return out


def interp(table, u):
    """Smoothly interpolate a list of (u, value) control points."""
    if u <= table[0][0]: return table[0][1]
    if u >= table[-1][0]: return table[-1][1]
    for i in range(len(table) - 1):
        (u0, v0), (u1, v1) = table[i], table[i + 1]
        if u0 <= u <= u1:
            t = (u - u0) / (u1 - u0)
            t = t * t * (3 - 2 * t)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def axis_between(a, b):
    d = [abs(b[i] - a[i]) for i in range(3)]
    return 'xyz'[d.index(max(d))]


def lay(t, cells, block='bone_block', axis=True, only_free=False):
    """Set a path of cells; `axis` turns a pillar-like block (bone, log, basalt) along the path."""
    cells = [c for c in cells if t.inside(*c)]
    for i, c in enumerate(cells):
        if only_free and not free(t, c): continue
        if axis:
            a = cells[max(0, i - 1)]; b = cells[min(len(cells) - 1, i + 1)]
            ax = axis_between(a, b) if a != b else 'y'
            t.set(*c, f'{block}[axis={ax}]')
        else:
            t.set(*c, block)
    return cells


# -- what a cell holds -----------------------------------------------------------------------------------

_NOT_FULL = ('_slab', '_stairs', '_wall', '_fence', '_pane', '_bars', 'chain', 'lantern', 'sea_pickle', 'kelp',
             'seagrass', 'lichen', 'tube_worms', 'giant_clam', 'barnacles', 'decorated_pot', 'chest', 'sign', 'skull',
             'lectern', 'campfire', 'bed', 'candle', 'haunt', 'water', 'air', 'trapdoor', 'button', 'rod')


def free(t, p):
    """Open water (or nothing set): room for a plant or a creature."""
    return t.inside(*p) and t.name_at(*p) in (None, 'minecraft:water')


def full(t, p):
    """A whole block something can grow on."""
    if not t.inside(*p): return False
    n = t.name_at(*p)
    if n is None: return False
    short = n.split(':')[1]
    if short.endswith('_coral') or short.endswith('_coral_fan') or short.endswith('_wall_fan'): return False
    return not any(k in short for k in _NOT_FULL)


def add(p, d):
    return (p[0] + d[0], p[1] + d[1], p[2] + d[2])


# -- life -------------------------------------------------------------------------------------------------


def lichen(t, p, face):
    """Glow lichen in the free cell p, growing on its `face` side (the block that way must be whole)."""
    if not t.inside(*p): return False
    faces = {f: 'false' for f in DIRS}
    n = t.name_at(*p)
    if n == 'minecraft:glow_lichen':
        faces.update({k: v for k, v in t.blocks[p][1].items() if k in DIRS})
    elif not free(t, p):
        return False
    if not full(t, add(p, DIRS[face])): return False
    faces[face] = 'true'
    t.set(*p, ('minecraft:glow_lichen', dict(faces)))
    return True


def wall_fan(t, p, facing, coral, dead=False):
    """A coral fan on the wall behind p, pointing `facing` (out of the wall)."""
    if not free(t, p) or not full(t, add(p, DIRS[OPP[facing]])): return False
    t.set(*p, f'{"dead_" if dead else ""}{coral}_coral_wall_fan[facing={facing}]')
    return True


def barnacles(t, p, facing):
    if not free(t, p) or not full(t, add(p, DIRS[OPP[facing]])): return False
    t.set(*p, f'oceanexpansion:barnacles[facing={facing}]')
    return True


def on_top(t, p, block):
    """Put `block` in the free cell p if a whole block lies under it."""
    if not free(t, p) or not full(t, add(p, (0, -1, 0))): return False
    t.set(*p, block)
    return True


def kelp(t, p, height, top=None):
    """A kelp stalk rising from the free cell p (over a whole block), at most `height` tall and staying below
    y = top (exclusive) and inside open water."""
    if not full(t, add(p, (0, -1, 0))): return 0
    x, y, z = p
    limit = min(t.size[1], top if top is not None else t.size[1])
    h = 0
    while h < height and y + h < limit and free(t, (x, y + h, z)): h += 1
    if h < 2: return 0
    for k in range(h - 1): t.set(x, y + k, z, 'kelp_plant')
    t.set(x, y + h - 1, z, 'kelp[age=25]')
    return h


def seagrass(t, p, tall=False):
    x, y, z = p
    if tall and free(t, (x, y + 1, z)) and on_top(t, p, 'tall_seagrass[half=lower]'):
        t.set(x, y + 1, z, 'tall_seagrass[half=upper]')
        return True
    return on_top(t, p, 'seagrass')


def coral_tuft(t, p, rng, dead=False):
    """A small coral plant or fan on top of the block below p."""
    c = rng.choice(CORALS)
    kind = rng.choice(('_coral', '_coral_fan'))
    return on_top(t, p, f'{"dead_" if dead else ""}{c}{kind}')


def pickle(t, p, rng, most=2):
    return on_top(t, p, f'sea_pickle[pickles={rng.randint(1, most)}]')


def surfaces(t, cells):
    """For a set of block cells: the free cells on top of them, beside them (with the facing pointing out) and
    under them (with the face they hang from)."""
    tops, sides, unders = [], [], []
    for c in cells:
        up = add(c, (0, 1, 0))
        if free(t, up): tops.append(up)
        for f in SIDES:
            q = add(c, DIRS[f])
            if free(t, q): sides.append((q, f))
        dn = add(c, (0, -1, 0))
        if free(t, dn): unders.append(dn)
    return tops, sides, unders


def tropical_fish(t, p, rng, facing=None):
    """A tropical fish with one of a few bright vanilla patterns (size | pattern << 8 | base << 16 | pattern colour << 24)."""
    looks = [(0, 0, 1, 0), (0, 1, 7, 4), (1, 1, 4, 11), (1, 3, 14, 0), (1, 4, 14, 0), (0, 3, 11, 4), (1, 2, 9, 0),
             (0, 5, 6, 3), (1, 0, 3, 4), (0, 2, 10, 4)]
    size, pattern, base, colour = rng.choice(looks)
    variant = size | pattern << 8 | base << 16 | colour << 24
    t.creature(*p, 'minecraft:tropical_fish', facing or rng.choice(SIDES), nbt={'Variant': variant})
