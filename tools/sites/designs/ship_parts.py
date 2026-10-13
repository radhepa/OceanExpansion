"""Shared helpers for the ship sites (the galleon, the iceberg's frozen ship, Wexley's barge): a smooth wooden
hull voxelized into stairs, slabs and full blocks at any angle (so a wreck can lie turned and tilted), masts,
yards, rigging, torn sails, sea growth, sand drifts, and a check that an air pocket really stays dry.

Ship coordinates: u runs along the keel from the stern (0) to the bow, v across the ship (0 on the centre line,
+ to starboard), h up from the bottom of the keel. A Frame puts the ship into a template, optionally turned
(yaw), nose up (pitch) and rolled onto its side (roll). Not a site: designs/__init__.py only loads the keys it
lists.
"""
import math

from kit import Template, parse, spec, HORIZONTAL, waterloggable

OPEN = 'open'          # inside the hull, not solid: flooded (a wreck) or dry air (a frozen ship)
DIRS6 = {'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0), 'south': (0, 0, 1),
         'north': (0, 0, -1)}

_PARTIAL = ('stairs', 'slab', 'fence', 'pane', 'bars', 'chain', 'lantern', 'trapdoor', 'door', 'sign', 'banner',
            'decorated_pot', 'chest', 'water', 'air', 'kelp', 'seagrass', 'coral', 'pickle', 'barnacles', 'haunt',
            'lectern', 'ladder', 'rod', 'candle', 'skull', 'head', 'bell', 'grindstone', 'anvil', 'cauldron', 'snow',
            'cake', 'bed', 'tube_worms', 'giant_clam', 'lever', 'button', 'plate', 'rail', 'lichen', 'carpet', 'wall',
            'cobweb', 'campfire', 'torch', 'composter', 'hopper', 'brewing', 'flower', 'jigsaw', 'powder_snow')


def is_full(name):
    """A whole, solid cube (water can't pass it, a fence connects to it)."""
    short = name.split(':', 1)[1]
    if short.endswith('_wall_fan') or short.endswith('_fan'): return False
    if short.endswith('_block') or short in ('barrel', 'bookshelf', 'chiseled_bookshelf', 'ice', 'packed_ice', 'blue_ice'):
        return True
    return not any(p in short for p in _PARTIAL)


# -- frames ------------------------------------------------------------------------------------------

def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


class Frame:
    """Where a ship sits in a template. `origin`: the template point (x, y, z) where ship point (0, 0, 0) lands
    before turning; the ship turns about `pivot` (ship coordinates). yaw turns it about the vertical, pitch
    lifts the bow, roll lays it over onto its starboard side (degrees)."""

    def __init__(self, origin, yaw=0.0, pitch=0.0, roll=0.0, pivot=(0.0, 0.0, 0.0)):
        r, p, w = (math.radians(a) for a in (roll, pitch, yaw))
        rx = [[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]]
        rz = [[math.cos(p), -math.sin(p), 0], [math.sin(p), math.cos(p), 0], [0, 0, 1]]
        ry = [[math.cos(w), 0, math.sin(w)], [0, 1, 0], [-math.sin(w), 0, math.cos(w)]]
        self.m = _mul(ry, _mul(rz, rx))
        self.mt = [[self.m[j][i] for j in range(3)] for i in range(3)]
        self.origin = origin
        self.pivot = (pivot[0], pivot[2], pivot[1])   # ship (u, v, h) -> (x, y, z) order (u, h, v)
        self.identity = (yaw, pitch, roll) == (0, 0, 0)

    def to_template(self, u, v, h):
        p = (u - self.pivot[0], h - self.pivot[1], v - self.pivot[2])
        q = [sum(self.m[i][k] * p[k] for k in range(3)) for i in range(3)]
        return (q[0] + self.pivot[0] + self.origin[0], q[1] + self.pivot[1] + self.origin[1],
                q[2] + self.pivot[2] + self.origin[2])

    def to_ship(self, x, y, z):
        p = (x - self.origin[0] - self.pivot[0], y - self.origin[1] - self.pivot[1], z - self.origin[2] - self.pivot[2])
        q = [sum(self.mt[i][k] * p[k] for k in range(3)) for i in range(3)]
        return (q[0] + self.pivot[0], q[2] + self.pivot[2], q[1] + self.pivot[1])

    def cell(self, u, v, h):
        """The template cell holding ship cell (u, v, h) (integers; v on the centre line is 0)."""
        x, y, z = self.to_template(u + .5, v, h + .5)
        return (math.floor(x), math.floor(y), math.floor(z))

    def direction(self, d):
        """A ship-space direction ('east' = toward the bow, 'south' = starboard, 'up') as the nearest template
        direction."""
        dx, dy, dz = DIRS6[d]
        x, y, z = (sum(self.m[i][k] * (dx, dy, dz)[k] for k in range(3)) for i in range(3))
        best = max(DIRS6, key=lambda n: DIRS6[n][0] * x + DIRS6[n][1] * y + DIRS6[n][2] * z)
        return best

    def horizontal(self, d):
        """Like direction(), but always a compass direction (for stairs, chests, signs...)."""
        dx, dy, dz = DIRS6[d]
        x, y, z = (sum(self.m[i][k] * (dx, dy, dz)[k] for k in range(3)) for i in range(3))
        return max(HORIZONTAL, key=lambda n: HORIZONTAL[n][0] * x + HORIZONTAL[n][1] * z)

    def axis(self, a):
        d = {'x': 'east', 'y': 'up', 'z': 'south'}[a]
        return {'east': 'x', 'west': 'x', 'up': 'y', 'down': 'y', 'south': 'z', 'north': 'z'}[self.direction(d)]

    def turn_spec(self, block):
        """Turn a block spec written in ship space (facing / axis) into the template's."""
        if self.identity or not isinstance(block, str) or '[' not in block: return block
        name, props = parse(block)
        props = dict(props)
        if 'axis' in props: props['axis'] = self.axis(props['axis'])
        if 'facing' in props:
            props['facing'] = self.direction(props['facing']) if props['facing'] in ('up', 'down') or \
                name.endswith('barrel') or name.endswith('lightning_rod') or name.endswith('end_rod') or \
                name.endswith('barnacles') else self.horizontal(props['facing'])
        return spec(name, props)


# -- voxelizing a smooth shape ------------------------------------------------------------------------

_OCT = [(ix, iy, iz) for iy in (0, 1) for iz in (0, 1) for ix in (0, 1)]


def _pair_side(cells):
    """Two occupied quarter-cells of one layer, side by side -> the compass side they sit on."""
    if len(cells) != 2: return None
    (ax, az), (bx, bz) = cells
    if ax == bx: return 'west' if ax == 0 else 'east'
    if az == bz: return 'north' if az == 0 else 'south'
    return None


def _shape(occ, centre):
    nb = [(ix, iz) for (ix, iy, iz) in _OCT if iy == 0 and occ[(ix, iy, iz)]]
    nt = [(ix, iz) for (ix, iy, iz) in _OCT if iy == 1 and occ[(ix, iy, iz)]]
    n = len(nb) + len(nt)
    if n >= 7: return ('full', None)
    if len(nb) == 4 and len(nt) == 2 and _pair_side(nt): return ('stairs', (_pair_side(nt), 'bottom'))
    if len(nt) == 4 and len(nb) == 2 and _pair_side(nb): return ('stairs', (_pair_side(nb), 'top'))
    if len(nb) == 4 and len(nt) <= 1: return ('slab', 'bottom')
    if len(nt) == 4 and len(nb) <= 1: return ('slab', 'top')
    if n >= 5: return ('full', None) if centre else (('slab', 'bottom') if len(nb) >= len(nt) else ('slab', 'top'))
    if n == 4 and centre: return ('full', None)
    if len(nb) == 3 and not nt: return ('slab', 'bottom')
    if len(nt) == 3 and not nb: return ('slab', 'top')
    return None


def voxelize(t, frame, model, families, fill, box, keep=None):
    """Sample `model(u, v, h)` (a material name, OPEN or None) over the ship box ((u0, v0, h0), (u1, v1, h1))
    and write it into template `t` through `frame`. Each material is a family {'full', 'stairs', 'slab'}:
    curved surfaces become stairs and slabs. OPEN cells become `fill` ('water', 'air'). `keep(x, y, z)` may
    refuse cells. Returns {template cell: material} for the solid cells."""
    (u0, v0, h0), (u1, v1, h1) = box
    corners = [frame.to_template(u, v, h) for u in (u0, u1) for v in (v0, v1) for h in (h0, h1)]
    lo = [max(0, math.floor(min(c[i] for c in corners)) - 1) for i in range(3)]
    hi = [min(t.size[i] - 1, math.ceil(max(c[i] for c in corners)) + 1) for i in range(3)]
    out = {}
    for y in range(lo[1], hi[1] + 1):
        for z in range(lo[2], hi[2] + 1):
            for x in range(lo[0], hi[0] + 1):
                if keep and not keep(x, y, z): continue
                mats = {}
                for (ix, iy, iz) in _OCT:
                    mats[(ix, iy, iz)] = model(*frame.to_ship(x + .25 + .5 * ix, y + .25 + .5 * iy, z + .25 + .5 * iz))
                c = model(*frame.to_ship(x + .5, y + .5, z + .5))
                occ = {k: (m is not None and m != OPEN) for k, m in mats.items()}
                centre_solid = c is not None and c != OPEN
                sh = _shape(occ, centre_solid) if any(occ.values()) else None
                if sh is None:
                    opens = sum(1 for m in list(mats.values()) + [c] if m == OPEN)
                    outs = sum(1 for m in list(mats.values()) + [c] if m is None)
                    if opens and opens >= outs and fill: t.set(x, y, z, fill)
                    continue
                solid = [m for m in mats.values() if m is not None and m != OPEN]
                mat = c if centre_solid else max(set(solid), key=solid.count)
                fam = families[mat]
                kind, arg = sh
                if kind != 'full' and not fam.get(kind): kind = 'full'
                if kind == 'full':
                    block = fam['full']
                    if callable(block): block = block(x, y, z)
                    if '[axis=' in block:   # logs follow the keel
                        name, props = parse(block)
                        props = dict(props)
                        props['axis'] = frame.axis(props['axis'])
                        block = spec(name, props)
                elif kind == 'stairs':
                    block = f"{fam['stairs']}[facing={arg[0]},half={arg[1]}]"
                else:
                    block = f"{fam['slab']}[type={arg}]"
                t.set(x, y, z, block)
                out[(x, y, z)] = mat
    return out


# -- a parametric wooden hull -----------------------------------------------------------------------

class Hull:
    """A smooth hull: plan width along the keel, a rounded section with tumblehome, a rising stem, a raked
    transom, stepped sheer (castles), decks and bulkheads. All lengths in blocks.

    sheer: [(u_from, u_to, top)]: the top of the bulwark (exclusive layer) between u_from and u_to.
    decks: [(u_from, u_to, layer, material)]; bulkheads: [(u_from, u_to, layer_from, layer_to, material)].
    holes: [(u, v, h, r)] breaches (open). part: (u_from, u_to) or a callable (u, v, h) -> bool."""

    def __init__(self, length, beam, height, full=(.28, .58), stem=.94, transom=.74, bilge=(4.0, 8.0),
                 stem_rise=9.5, keel_rise_from=.70, tumble=(9.0, .17, 8.0), bow_rake=3.0, stern_rake=1.5,
                 skin=1.0, sheer=(), decks=(), bulkheads=(), holes=(), part=None, shell=None, run=(0.0, 1.0),
                 fine=.75):
        self.L, self.B, self.H = length, beam, height
        self.full, self.stem, self.transom = full, stem, transom
        self.bilge, self.stem_rise, self.keel_rise_from = bilge, stem_rise, keel_rise_from
        self.tumble, self.bow_rake, self.stern_rake, self.skin = tumble, bow_rake, stern_rake, skin
        self.sheer, self.decks, self.bulkheads, self.holes = list(sheer), list(decks), list(bulkheads), list(holes)
        self.part = part
        self.run, self.fine = run, fine
        self.shell = shell or (lambda u, v, h, layer: 'hull')

    def _ueff(self, u, h):
        x = u / self.L
        f = min(1.0, max(0.0, h / self.H))
        if x < self.full[0]: return u + self.stern_rake * f
        if x > self.full[1]: return u - self.bow_rake * f * f
        return u

    def keel(self, u):
        x = u / self.L
        if x <= self.keel_rise_from: return 0.0
        return self.stem_rise * min(1.0, (x - self.keel_rise_from) / (self.stem - self.keel_rise_from)) ** 1.6

    def plan(self, ue):
        x = ue / self.L
        a, b = self.full
        if x < 0 or x > self.stem: return 0.0
        if x < a: return self.B * (self.transom + (1 - self.transom) * math.sin(math.pi / 2 * x / a))
        if x <= b: return self.B
        return self.B * max(0.0, 1 - ((x - b) / (self.stem - b)) ** 2) ** self.fine

    def aft(self, h):
        """Where the hull starts at height h: the run sweeps up from the sternpost to the counter."""
        reach, counter = self.run
        return reach * ((counter - h) / counter) ** 1.4 if h < counter else 0.0

    def half_width(self, u, h):
        k = self.keel(u)
        if h < k: return -1.0
        ue = self._ueff(u, h)
        x = ue / self.L
        a, b = self.full
        end = max(0.0, (a - x) / a) if x < a else max(0.0, (x - b) / (self.stem - b)) if x > b else 0.0
        hb = self.bilge[0] + (self.bilge[1] - self.bilge[0]) * min(1.0, end)
        t = min(1.0, (h - k) / hb)
        s = .14 + .86 * (1 - (1 - t) ** 2) ** .55
        h0, amount, span = self.tumble
        if h > h0: s *= 1 - amount * min(1.0, (h - h0) / span)
        return self.plan(ue) * s

    def top(self, u):
        for a, b, top in self.sheer:
            if a <= u < b: return top
        return self.H

    def __call__(self, u, v, h):
        if self.part is not None and not self.part(u, v, h): return None
        k = self.keel(u)
        if h < k or h >= self.top(u): return None
        hw = self.half_width(u, h)
        if abs(v) > hw: return None
        ue = self._ueff(u, h)
        aft = self.aft(h)
        if ue < aft: return None
        layer = math.floor(h)
        for (hu, hv, hh, r) in self.holes:
            if (u - hu) ** 2 + (v - hv) ** 2 + (h - hh) ** 2 < r * r: return OPEN
        inner = h >= k + self.skin and abs(v) <= hw - self.skin and ue >= aft + self.skin
        if not inner: return self.shell(u, v, h, layer)
        for a, b, lay, mat in self.decks:
            if a <= u < b and layer == lay: return mat
        for a, b, l0, l1, mat in self.bulkheads:
            if a <= u < b and l0 <= layer <= l1: return mat
        return OPEN


# -- placing things in ship space ------------------------------------------------------------------

class Shipwright:
    """Puts blocks, lines and sails into a template in ship coordinates through a Frame."""

    def __init__(self, t, frame):
        self.t, self.f = t, frame

    def at(self, u, v, h):
        return self.f.cell(u, v, h)

    def put(self, u, v, h, block, only_if=None):
        x, y, z = self.at(u, v, h)
        if not self.t.inside(x, y, z): return None
        if only_if and not only_if(self.t.get(x, y, z)): return None
        self.t.set(x, y, z, self.f.turn_spec(block))
        return (x, y, z)

    def line(self, a, b, block, step=.25):
        """A straight run of blocks from ship point a to b (u, v, h floats). `block` may contain {axis} (the
        run's main template axis). Returns the cells."""
        pa, pb = self.f.to_template(*a), self.f.to_template(*b)
        d = [pb[i] - pa[i] for i in range(3)]
        n = max(1, int(max(abs(c) for c in d) / step))
        axis = 'xyz'[max(range(3), key=lambda i: abs(d[i]))]
        cells = []
        for i in range(n + 1):
            p = [pa[k] + d[k] * i / n for k in range(3)]
            c = tuple(math.floor(v) for v in p)
            if c not in cells and self.t.inside(*c): cells.append(c)
        for c in cells:
            self.t.set(*c, block.replace('{axis}', axis) if isinstance(block, str) else block(c, axis))
        return cells

    def sail(self, u, v0, v1, h_top, h_bot, rng, tear=.25, colors=('white_wool',), ragged=2, sag=0.0):
        """A torn square sail hanging across the ship at station u, from h_top down to h_bot. Holes get more
        likely toward the ragged foot. `sag`: the foot bellies toward the bow."""
        cells = []
        for h in range(h_bot, h_top + 1):
            for v in range(v0, v1 + 1):
                depth = (h_top - h) / max(1, h_top - h_bot)
                if rng.random() < tear * (.3 + depth): continue
                if h - h_bot < ragged and rng.random() < .5: continue
                belly = sag * math.sin(math.pi * (v - v0) / max(1, v1 - v0)) * depth
                cells.append(self.put(round(u + belly), v, h, rng.choice(colors)))
        return [c for c in cells if c]


# -- after the build: growth, sand, checks ------------------------------------------------------------

def open_water(t, x, y, z, floor_line=0):
    """Is the cell sea water once placed: written as water, or left void above the sea floor line."""
    if not t.inside(x, y, z): return False
    b = t.name_at(x, y, z)
    if b == 'minecraft:water': return True
    return b is None and y >= floor_line


_SOFT = {'minecraft:water', 'minecraft:kelp', 'minecraft:kelp_plant', 'minecraft:seagrass', 'minecraft:tall_seagrass',
         'minecraft:sea_pickle', 'oceanexpansion:barnacles'}


def sky_open(t, x, y, z):
    """Nothing but water and weed above the cell, up to the template's top (out under the open sea)."""
    for yy in range(y + 1, t.size[1]):
        b = t.name_at(x, yy, z)
        if b is not None and b not in _SOFT: return False
    return True


def solid_at(t, x, y, z):
    b = t.name_at(x, y, z)
    return b is not None and is_full(b)


def barnacles(t, cells, rng, chance=.18, floor_line=0, up=True, outside_only=True):
    """Crust some faces of `cells` (hull blocks) with barnacles in the water beside them (by default only on the
    outside: the open sea, not the rooms inside)."""
    n = 0
    for (x, y, z) in sorted(cells):
        if not solid_at(t, x, y, z): continue
        for d, (dx, dy, dz) in DIRS6.items():
            if d == 'down' or (d == 'up' and not up): continue
            q = (x + dx, y + dy, z + dz)
            if not open_water(t, *q, floor_line=floor_line): continue
            if outside_only and t.name_at(*q) is not None and not sky_open(t, *q): continue
            if rng.random() < chance:
                t.set(*q, f'oceanexpansion:barnacles[facing={d}]')
                n += 1
    return n


def kelp(t, x, y, z, height, floor_line=0):
    """A kelp stalk growing up from the solid block under (x, y, z)."""
    if not solid_at(t, x, y - 1, z): return 0
    cells = []
    for i in range(height):
        if not open_water(t, x, y + i, z, floor_line) or y + i >= t.size[1] - 1: break
        cells.append((x, y + i, z))
    if not cells: return 0
    for c in cells[:-1]: t.set(*c, 'kelp_plant')
    t.set(*cells[-1], 'kelp')
    return len(cells)


def growth(t, spots, rng, floor_line=0, kelp_chance=.25, coral=True, pickles=.08, grass=.3, kelp_height=(3, 9),
           ceiling=None):
    """Sea life on the top faces of `spots` (cells with open sea above): kelp, seagrass, coral, sea pickles.
    Kelp never grows above template y `ceiling`."""
    corals = ['tube', 'brain', 'bubble', 'fire', 'horn']
    for (x, y, z) in spots:
        a = (x, y + 1, z)
        if not solid_at(t, x, y, z) or not open_water(t, *a, floor_line=floor_line) or not sky_open(t, x, y, z): continue
        r = rng.random()
        if r < kelp_chance:
            hgt = rng.randint(*kelp_height)
            if ceiling is not None: hgt = min(hgt, ceiling - a[1] + 1)
            if hgt > 0: kelp(t, *a, hgt, floor_line)
        elif r < kelp_chance + pickles:
            t.set(*a, f'sea_pickle[pickles={rng.randint(1, 4)}]')
        elif coral and r < kelp_chance + pickles + .07:
            c = rng.choice(corals)
            t.set(*a, rng.choice([f'{c}_coral', f'{c}_coral_fan']))
        elif r < kelp_chance + pickles + .07 + grass:
            if open_water(t, x, y + 2, z, floor_line) and rng.random() < .4:
                t.set(*a, 'tall_seagrass[half=lower]')
                t.set(x, y + 2, z, 'tall_seagrass[half=upper]')
            else:
                t.set(*a, 'seagrass')


def coral_patch(t, x, y, z, rng, size=2, floor_line=0):
    """A small coral colony of coral blocks with fans on top and on the sides, grown on the block below."""
    kind = rng.choice(['tube', 'brain', 'bubble', 'fire', 'horn'])
    placed = []
    for dx in range(-size, size + 1):
        for dz in range(-size, size + 1):
            if dx * dx + dz * dz > size * size or rng.random() < .35: continue
            c = (x + dx, y, z + dz)
            if open_water(t, *c, floor_line=floor_line) and solid_at(t, c[0], c[1] - 1, c[2]):
                t.set(*c, f'{kind}_coral_block')
                placed.append(c)
    for (cx, cy, cz) in placed:
        top = (cx, cy + 1, cz)
        if open_water(t, *top, floor_line=floor_line) and rng.random() < .6:
            t.set(*top, rng.choice([f'{kind}_coral', f'{kind}_coral_fan', f'{rng.choice(["tube", "brain", "horn"])}_coral_fan']))
        for d in HORIZONTAL:
            dx, dz = HORIZONTAL[d]
            s = (cx + dx, cy, cz + dz)
            if open_water(t, *s, floor_line=floor_line) and rng.random() < .25:
                t.set(*s, f'{kind}_coral_wall_fan[facing={d}]')
    return placed


def settle(t, x, y, z):
    """Drop a loose thing straight down through water to the first solid block (template space)."""
    while y > 0 and t.name_at(x, y - 1, z) == 'minecraft:water': y -= 1
    return (x, y, z)


def sand_fill(t, cells, block='sand'):
    """Fill water cells with sand from the bottom up, only where each one has something solid under it."""
    for (x, y, z) in sorted(cells, key=lambda c: c[1]):
        below = t.name_at(x, y - 1, z)
        if t.name_at(x, y, z) in (None, 'minecraft:water') and below is not None and (is_full(below) or 'sand' in below):
            t.set(x, y, z, block)


def connect(t):
    """Join fences, panes and bars to their neighbours (fences, panes, bars and whole blocks)."""
    for (x, y, z), (name, props) in list(t.blocks.items()):
        short = name.split(':')[1]
        fence = short.endswith('_fence')
        pane = short.endswith('_pane') or short.endswith('_bars') or short == 'iron_bars'
        if not (fence or pane): continue
        new = {k: v for k, v in props.items() if k not in HORIZONTAL}
        for d, (dx, dz) in HORIZONTAL.items():
            n = t.name_at(x + dx, y, z + dz)
            if n is None: continue
            ns = n.split(':')[1]
            ok = is_full(n) or (fence and ns.endswith('_fence')) or (pane and (ns.endswith('_pane') or ns.endswith('_bars')))
            if ok: new[d] = 'true'
            elif pane: new[d] = 'false'
        t.blocks[(x, y, z)] = (name, new)


def crop(t, pad=0):
    """A copy of `t` trimmed to what it holds (plus `pad`), everything shifted to start at 0."""
    pts = list(t.blocks) + [tuple(e['blockPos']) for e in t.entities]
    lo = [max(0, min(p[i] for p in pts) - pad) for i in range(3)]
    hi = [min(t.size[i] - 1, max(p[i] for p in pts) + pad) for i in range(3)]
    size = tuple(hi[i] - lo[i] + 1 for i in range(3))
    full_height = t.waterline >= t.size[1]
    out = Template(t.name, size, wet=t.wet, waterline=None if full_height else t.waterline - lo[1])
    sh = lambda p: (p[0] - lo[0], p[1] - lo[1], p[2] - lo[2])
    for p, b in t.blocks.items(): out.blocks[sh(p)] = b
    for p, n in t.nbt.items(): out.nbt[sh(p)] = n
    out.dry = {sh(p) for p in t.dry}
    for e in t.entities:
        e = dict(e)
        e['pos'] = [e['pos'][0] - lo[0], e['pos'][1] - lo[1], e['pos'][2] - lo[2]]
        e['blockPos'] = list(sh(e['blockPos']))
        nbt = dict(e['nbt'])
        if 'block_pos' in nbt:
            nbt['block_pos'] = type(nbt['block_pos'])(list(sh(nbt['block_pos'])))
        e['nbt'] = nbt
        out.entities.append(e)
    out.notes = dict(t.notes)
    if 'entrances' in out.notes: out.notes['entrances'] = [sh(p) for p in out.notes['entrances']]
    if 'anchor' in out.notes: out.notes['anchor'] = sh(out.notes['anchor'])
    out.offset = tuple(lo)
    return out


def check_sealed(t, sea_level=None):
    """Every dry (air) cell below `sea_level` (template y; default the waterline) must be walled off from the
    sea: no water, no void and no waterlogged block beside or above it. Returns the leaks."""
    sea = t.waterline if sea_level is None else sea_level
    leaks = []
    for (x, y, z), (name, _) in t.blocks.items():
        if name != 'minecraft:air' or y >= sea: continue
        for d, (dx, dy, dz) in DIRS6.items():
            if d == 'down': continue
            q = (x + dx, y + dy, z + dz)
            if not t.inside(*q):
                leaks.append(((x, y, z), d, 'edge'))
                continue
            b = t.name_at(*q)
            if b is None:
                if q[1] < sea: leaks.append(((x, y, z), d, 'void'))
            elif b == 'minecraft:water':
                leaks.append(((x, y, z), d, 'water'))
            elif t.submerged(*q) and waterloggable(b):
                leaks.append(((x, y, z), d, 'wet ' + b))
    return leaks
