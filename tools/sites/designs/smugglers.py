"""Smugglers' Rock: a tall sea stack hollowed into a hidden cove. Through an arch on its seaward side lies a dock
with a moored sloop and the contraband; tunnels climb to the bunk room, a switchback stair to the chief's den, and
a rope-ladder chimney to the lookout on the summit. One piece, rigid at sea level; the stack's bottom layer is
extended to the sea floor (footing) and its rock is placed in water and air (soft: False)."""
import math

from kit import Template, HORIZONTAL
from loot import item, empty, pool, rolls, enchanted, named, treasure_map, WORN
from designs.surface_parts import Noise, Rock, wobble, connect, lantern_post, shore_life

KEY = 'smugglers'
NAME = "Smugglers' Rock"
FEATURES = [
    'a tall sea stack with banded rock, ledges, a wave-cut notch, gull nests and bushes on its crown',
    'a sea arch into a hidden cove: a plank dock, a moored sloop with its sail furled, and a storage loft with a hoist',
    'contraband everywhere: spice, silk, pearls and powder in crates and barrels; a stash hidden under the dock',
    'tunnels up to the bunk room, a switchback stair to the chief\'s den with the ledger "No Names on the Water"',
    'a rope-ladder chimney to the lookout on the summit, with a signal lantern and a spyglass',
]
SITE = {'anchor': 'surface', 'depth': (6, 20), 'flatness': 8, 'radius': 19, 'weight': 2, 'inhabited': True,
        'biomes': ['ocean', 'lukewarm_ocean', 'warm_ocean', 'cold_ocean']}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'smugglers/rock', 'at': (0, 0), 'turn': 0, 'y': -6, 'mode': 'rigid', 'footing': True, 'soft': False},
    ]},
]

RUM = named('Rum')
LOOT_TABLES = {
    'smugglers/stores': [
        pool(rolls(3, 6), [item('cocoa_beans', 6, 4, 12), item('white_wool', 3, 2, 6), item('red_wool', 2, 2, 5),
                           item('purple_wool', 2, 1, 4), item('yellow_wool', 1, 1, 4), item('gunpowder', 4, 2, 6),
                           item('sugar', 3, 2, 8), item('honey_bottle', 3, 1, 3, extra=RUM), item('leather', 2, 1, 4),
                           item('glass_bottle', 2, 1, 4), item('ink_sac', 2, 2, 5), item('emerald', 2, 1, 2),
                           item('string', 2, 2, 6), empty(3)]),
        pool(1, [item('oceanexpansion:pearl', 2, 1, 2), item('spyglass', 1), item('lead', 2), empty(5)]),
    ],
    'smugglers/cache': [
        pool(rolls(3, 5), [item('emerald', 6, 2, 7), item('gold_ingot', 5, 2, 5), item('oceanexpansion:pearl', 5, 1, 3),
                           item('gold_nugget', 3, 4, 12), item('diamond', 1, 1, 2), item('amethyst_shard', 2, 2, 6),
                           item('cocoa_beans', 2, 6, 16)]),
        pool(1, [item('oceanexpansion:black_pearl', 1), treasure_map(3), empty(4)]),
    ],
    'smugglers/boss': [
        pool(rolls(2, 4), [item('emerald', 6, 3, 8), item('gold_ingot', 4, 1, 4), item('oceanexpansion:pearl', 4, 1, 3),
                           item('gunpowder', 2, 2, 5), item('honey_bottle', 2, 1, 2, extra=RUM),
                           item('compass', 2), item('spyglass', 1), item('book', 1)]),
        pool(1, [treasure_map(4), item('oceanexpansion:black_pearl', 1), empty(3)]),
        pool(1, [item('crossbow', 2, extra=enchanted(10, 25)), item('iron_sword', 2, extra=WORN),
                 item('compass', 1, extra=named('The Chief\'s Compass')), empty(4)]),
    ],
}

K = 6                       # rows under the sea (0..5); row 6 is sea level (y 63), the first air
SX, SY, SZ = 40, 40, 40
C = (20.0, 20.0)            # the stack's axis
R0 = 12.6                   # its radius at sea level
TOP = K + 29                # the crown at the axis
NEEDLE = (31.5, 10.5, 3.3, K + 17)    # a lesser stack beside it: x, z, radius at sea level, top
COVE = (20.0, 23.0, 6.5, 7.5, 10.5)   # cove centre x, z; radii x, z; dome height
BUNK = (14, 20, 9, 13)      # bunk room x0, x1, z0, z1 (walk K + 4)
DEN = (19, 25, 15, 19)      # chief's den x0, x1, z0, z1 (walk K + 13)
BUNK_Y, DEN_Y = K + 4, K + 13


class Stack:
    def __init__(self):
        self.t = Template('smugglers/rock', (SX, SY, SZ), wet=True, waterline=K)
        self.rng = self.t.rng
        self.rock = Rock(41, K, mossy=0.45)
        self.carved = set()     # dry carved cells (rooms, tunnels)
        self.cove_air = set()
        self.cove_water = set()

    # -- the stack ---------------------------------------------------------------------------------
    def radius(self, x, y, z):
        th = math.atan2(z - C[1], x - C[0])
        if y < K: r = R0 * self.wob(th) * (1 + (K - y) * 0.05)
        else: r = R0 * self.wob(th) * (1 - 0.40 * ((y - K) / 29.0) ** 1.3)
        r += (self.strata(y * 3.0, 0.5) - .5) * 3.2 + (self.n3(x, z, y) - .5) * 2.2
        if K - 1 <= y <= K + 1: r -= 0.9                     # the wave-cut notch
        return r

    def crown(self, x, z):
        d = math.hypot(x - C[0], z - C[1])
        return TOP - (d / (R0 * 0.72)) ** 4 * 3.5 + (self.n2(x, z) - .5) * 3.0

    def needle(self, x, y, z):
        nx, nz, nr, ntop = NEEDLE
        r = nr * (1.15 if y < K else 1 - 0.55 * (y - K) / (ntop - K)) + (self.n3(x + 50, z, y) - .5) * 1.4
        return y <= ntop + (self.n2(x, z) - .5) * 3 and math.hypot(x - nx, z - nz) <= r

    def stack(self):
        t, rng = self.t, self.rng
        self.wob = wobble(rng, ((2, .08), (3, .08), (4, .05), (7, .04)))
        self.strata = Noise(42, 4.0)
        self.n3 = Noise(43, 3.2)
        self.n2 = Noise(44, 3.0)
        band = Noise(45, 2.5)
        self.solid = set()
        for y in range(0, SY):
            for x in range(SX):
                for z in range(SZ):
                    if self.needle(x, y, z):
                        self.solid.add((x, y, z))
                        continue
                    d = math.hypot(x - C[0], z - C[1])
                    if d > self.radius(x, y, z): continue
                    if y > self.crown(x, z): continue
                    self.solid.add((x, y, z))
        for (x, y, z) in self.solid:
            b = band(0.0, 0.0, y * 2.0 + (self.n2(x, z) - .5) * 1.5)
            if b > .72: m = 'tuff' if rng.random() < .7 else self.rock(x, y, z)
            elif b < .28: m = 'andesite' if rng.random() < .6 else self.rock(x, y, z)
            else: m = self.rock(x, y, z)
            t.set(x, y, z, m)

    def surfaces(self):
        """Grass on the crown, gravel and moss on the ledges, gull nests with white streaks below them."""
        t, rng = self.t, self.rng
        for (x, y, z) in sorted(self.solid):
            if (x, y + 1, z) in self.solid or (x, y, z) in self.carved: continue
            if t.name_at(x, y, z) is None or t.name_at(x, y, z) in ('minecraft:air', 'minecraft:water'): continue
            if y >= TOP - 5:
                t.set(x, y, z, 'grass_block')
                buried = all((x + a, y - 1, z + b) in self.solid for a, b in HORIZONTAL.values())
                if buried and (x, y - 1, z) in self.solid and t.name_at(x, y - 1, z) not in ('minecraft:air',):
                    t.set(x, y - 1, z, 'dirt')
                r = rng.random()
                if y + 1 < SY and (x, y + 1, z) not in t.blocks:
                    if r < .30: t.set(x, y + 1, z, 'short_grass')
                    elif r < .40: t.set(x, y + 1, z, 'bush')
                    elif r < .46: t.set(x, y + 1, z, 'fern')
                    elif r < .50: t.set(x, y + 1, z, 'sweet_berry_bush[age=2]')
                    elif r < .53 and y + 2 < SY:
                        t.set(x, y + 1, z, 'tall_grass[half=lower]')
                        t.set(x, y + 2, z, 'tall_grass[half=upper]')
            elif y >= K + 1:
                r = rng.random()
                held = t.name_at(x, y - 1, z) not in (None, 'minecraft:air', 'minecraft:water')
                if r < .45: t.set(x, y, z, 'gravel' if held else t.get(x, y, z))
                elif r < .62: t.set(x, y, z, 'moss_block')
                if r > .97 and y + 1 < SY and (x, y + 1, z) not in t.blocks:
                    t.set(x, y + 1, z, 'hay_block[axis=y]')               # a gull's nest
                    for k in range(1, 4):
                        if (x, y - k, z) in self.solid: t.set(x, y - k, z, 'calcite')
                elif .62 <= r < .70 and y + 1 < SY and (x, y + 1, z) not in t.blocks:
                    t.set(x, y + 1, z, 'short_grass' if r < .66 else 'bush')

    # -- the cove -------------------------------------------------------------------------------------
    def cove(self):
        t, rng = self.t, self.rng
        cx, cz, rx, rz, ry = COVE
        cn = Noise(46, 2.5)
        foot = set()
        for x in range(SX):
            for z in range(SZ):
                e = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
                for y in range(K, SY):
                    h = (y - K) / ry
                    if e + h * h <= 1.0 + (cn(x, z, y) - .5) * 0.35:
                        self.cove_air.add((x, y, z))
                        if y == K: foot.add((x, z))
        # the arch: the cove opens to the sea on the south side, an irregular mouth
        for z in range(int(cz), SZ):
            for x in range(SX):
                w = 3.4 + (cn(x, z, 0.0) - .5) * 1.2
                if abs(x - cx) > w: continue
                hgt = 8.5 - ((x - cx) / w) ** 2 * 3.5 + (cn(x, z, 9.0) - .5) * 1.6
                for y in range(K, K + int(hgt) + 1):
                    self.cove_air.add((x, y, z))
                foot.add((x, z))
        for (x, y, z) in self.cove_air:
            t.set(x, y, z, 'air')
        for (x, z) in foot:
            for y in range(1, K):
                self.cove_water.add((x, y, z))
                t.set(x, y, z, 'water')
            if (x, 0, z) not in t.blocks: t.set(x, 0, z, self.rock(x, 0, z))
            t.set(x, 1, z, 'sand' if rng.random() < .6 else 'gravel')
        self.foot = foot

    def dock(self):
        """The plank dock along the cove's back (north) wall on log piles, and the loft with its hoist."""
        t, rng = self.t, self.rng
        cx, cz, rx, rz, ry = COVE
        back = {}
        for (x, z) in self.foot:
            if z < cz - 1 and (x not in back or z < back[x]): back[x] = z
        self.dock_cells = set()
        front = int(cz) - 4                     # the dock's front edge; the sloop lies beyond a strip of water
        for x, z0 in back.items():
            for z in range(z0, front + 1):
                if (x, z) not in self.foot: continue
                t.set(x, K, z, 'spruce_planks' if rng.random() > .1 else 'stripped_spruce_wood[axis=x]')
                self.dock_cells.add((x, z))
        xs = sorted(back)
        self.dock_x = (xs[0], xs[-1])
        # head room over the dock: the dome comes down low at the back, so cut it back a little
        for (x, z) in self.dock_cells:
            for y in range(K + 1, K + 4):
                if t.name_at(x, y, z) != 'minecraft:air':
                    t.set(x, y, z, 'air')
                self.cove_air.add((x, y, z))
        xs = sorted({x for (x, z) in self.dock_cells})
        self.dock_x = (xs[0], xs[-1])
        # piles under the front edge
        for x in xs[1::3]:
            z = max(z for (xx, z) in self.dock_cells if xx == x)
            for y in range(1, K): t.set(x, y, z, 'spruce_log[axis=y]')
            t.set(x, K + 1, z, 'spruce_fence')
        # lantern posts at both ends and the middle
        for x in (xs[2], xs[len(xs) // 2], xs[-3]):
            z = max(z for (xx, z) in self.dock_cells if xx == x)
            lantern_post(t, x, K + 1, z, 2)

    def sloop(self):
        """A single-masted sloop moored in the cove, bow toward the arch, sail furled on the boom."""
        t = self.t
        cx = int(COVE[0])
        z0 = int(COVE[1]) - 2                 # stern
        L = 11
        half = [1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0]
        for i in range(L):
            z = z0 + i
            hw = half[i]
            for dx in range(-hw, hw + 1):
                x = cx + dx
                edge = abs(dx) == hw
                # keel and bilge (solid, below the waterline)
                if abs(dx) <= max(0, hw - 1) and 0 < i < L - 1: t.set(x, K - 2, z, 'dark_oak_planks')
                if edge and hw > 0:
                    t.set(x, K - 1, z, f'dark_oak_stairs[facing={"west" if dx > 0 else "east"},half=top]')
                else:
                    t.set(x, K - 1, z, 'dark_oak_planks')
                t.set(x, K, z, 'dark_oak_planks' if edge else 'spruce_planks')
                if edge and i not in (0,):
                    t.set(x, K + 1, z, 'dark_oak_fence' if i % 2 else 'dark_oak_slab[type=bottom]')
                elif not edge:
                    t.set(x, K + 1, z, 'air')
        # stern: a raised quarterdeck with the tiller and a lantern
        for dx in (-1, 0, 1):
            t.set(cx + dx, K + 1, z0, 'dark_oak_slab[type=bottom]')
        t.set(cx, K + 1, z0 + 1, 'dark_oak_fence')
        t.set(cx, K + 2, z0, 'lantern[hanging=false]')
        # bow: stem post and bowsprit
        bz = z0 + L - 1
        t.set(cx, K + 1, bz, 'dark_oak_stairs[facing=north,half=bottom]')
        t.set(cx, K + 1, bz + 1, 'dark_oak_fence')
        t.set(cx, K + 2, bz + 1, 'dark_oak_fence')
        t.set(cx, K + 2, bz + 2, 'dark_oak_fence')
        # the mast, the boom and the furled sail, a yard and rigging
        mz = z0 + 5
        for y in range(K + 1, K + 10): t.set(cx, y, mz, 'stripped_spruce_log[axis=y]')
        t.set(cx, K + 10, mz, 'spruce_fence')
        for k in range(1, 5):
            t.set(cx, K + 3, mz - k, 'stripped_spruce_log[axis=z]' if k < 4 else 'spruce_fence')
            if k < 4: t.set(cx, K + 4, mz - k, 'white_wool' if k % 2 else 'light_gray_wool')
        t.set(cx, K + 4, mz - 4, 'white_carpet')
        for a in (-1, 1):
            t.set(cx + a, K + 8, mz, 'spruce_fence')
        t.set(cx, K + 8, mz + 1, 'spruce_fence')
        for y in range(K + 4, K + 8): t.set(cx, y, mz + 2, 'iron_chain[axis=y]')
        # cargo on deck
        t.set(cx - 1, K + 1, mz + 2, 'barrel[facing=up,open=false]')
        t.set(cx + 1, K + 1, mz + 2, 'barrel[facing=up,open=false]')
        t.set(cx + 1, K + 1, mz + 3, 'barrel[facing=up,open=false]')
        t.set(cx - 1, K + 1, mz - 2, 'brown_wool')
        t.set(cx - 1, K + 1, mz + 4, 'lantern[hanging=false]')
        self.sloop_cells = {(cx + dx, z) for z in range(z0, z0 + L + 2) for dx in range(-2, 3)}

    # -- rooms -----------------------------------------------------------------------------------------
    def carve(self, x, y, z, block='air'):
        self.t.set(x, y, z, block)
        self.carved.add((x, y, z))

    def rooms(self):
        t = self.t
        x0, x1, z0, z1 = BUNK
        # bunk room: floor BUNK_Y - 1, three tall
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                t.set(x, BUNK_Y - 1, z, 'spruce_planks')
                for y in range(BUNK_Y, BUNK_Y + 3): self.carve(x, y, z)
        # the stair from the dock north up into the bunk room (it finishes inside the room if the rock is thin)
        sx = 16
        dz0 = min(z for (x, z) in self.dock_cells if x == sx)
        self.carve(sx, K + 4, dz0)                                          # head room at the stair foot
        y, z = K + 1, dz0 - 1
        while y < BUNK_Y:
            self.carve(sx, y, z, 'spruce_stairs[facing=north,half=bottom]')
            for yy in range(K + 1, y): self.carve(sx, yy, z, 'stone')
            for yy in range(y + 1, max(y + 5, BUNK_Y + 3)): self.carve(sx, yy, z)
            y += 1
            z -= 1
        while z > z1:
            self.carve(sx, BUNK_Y - 1, z, 'spruce_planks')
            for yy in range(BUNK_Y, BUNK_Y + 3): self.carve(sx, yy, z)
            z -= 1
        self.tunnel_z = (min(z + 1, dz0 - 1), dz0 - 1)
        # switchback stair up to the den: east along RUN_Z, a landing, then south into the den
        run_z = z0 + 2
        y = BUNK_Y
        for x in range(x1 + 1, x1 + 6):
            self.carve(x, y, run_z, 'spruce_stairs[facing=east,half=bottom]')
            for yy in range(BUNK_Y, y): self.carve(x, yy, run_z, 'spruce_planks')
            for yy in range(y + 1, y + 5): self.carve(x, yy, run_z)
            y += 1
        lx = x1 + 6
        self.carve(lx, y - 1, run_z, 'spruce_planks')                     # landing
        for yy in range(BUNK_Y, y - 1): self.carve(lx, yy, run_z, 'spruce_planks')
        for yy in range(y, y + 4): self.carve(lx, yy, run_z)
        z = run_z + 1
        while y < DEN_Y:
            self.carve(lx, y, z, 'spruce_stairs[facing=south,half=bottom]')
            for yy in range(BUNK_Y, y): self.carve(lx, yy, z, 'spruce_planks')
            for yy in range(y + 1, y + 5): self.carve(lx, yy, z)
            y += 1
            z += 1
        self.stair_top = (lx, DEN_Y - 1, z - 1)
        assert DEN[0] <= lx - 1 <= DEN[1] and DEN[2] <= z - 1 <= DEN[3], ('the stair must land beside the den', lx, z)
        # the den: floor DEN_Y - 1, three tall, a doorway from the stair top
        x0, x1, z0, z1 = DEN
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                t.set(x, DEN_Y - 1, z, 'spruce_planks')
                for yy in range(DEN_Y, DEN_Y + 3): self.carve(x, yy, z)
        # the rope-ladder chimney from the den to the summit
        chx, chz = 21, z0
        self.chimney = (chx, chz - 1)
        ytop = int(self.crown(chx, chz - 1)) + 1
        for yy in range(DEN_Y, min(SY - 2, ytop + 1)):
            self.carve(chx, yy, chz - 1, 'ladder[facing=south]')
        self.lookout_y = min(SY - 2, ytop + 1)

    def shell(self):
        """Make sure every dry room and tunnel is wrapped in rock (the stack may be thin there)."""
        t = self.t
        for (x, y, z) in list(self.carved):
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    for c in (-1, 0, 1):
                        p = (x + a, y + c, z + b)
                        if not t.inside(*p) or p in t.blocks: continue
                        if p[1] > self.crown(p[0], p[2]) + 0.5 and c >= 0: continue
                        t.set(*p, self.rock(*p))
                        self.solid.add(p)

    def furnish(self):
        t = self.t
        # -- the dock: contraband, stores, two of the crews' crates, the hoist ----------------------------
        dock = sorted(self.dock_cells)
        back = {}
        for (x, z) in dock:
            if x not in back or z < back[x]: back[x] = z
        xa, xb = self.dock_x
        # crates and barrels stacked against the back wall (leave the stair foot, the loft ladder and a walkway clear)
        stair_x = 16
        lxs = [x for x in sorted(back) if xb - 5 <= x <= xb - 1]
        ladder_x = lxs[0] - 1
        depth = lambda x: sum(1 for (xx, zz) in self.dock_cells if xx == x)
        deep = [x for x in sorted(back) if abs(x - stair_x) > 1 and depth(x) >= 3 and abs(x - ladder_x) > 0]
        slots = deep[::2]
        crates = {slots[1], slots[-1]} if len(slots) >= 3 else set(slots[:2])
        assert len(crates) == 2, ('two crates on the dock', slots)
        y = K + 1
        for i, x in enumerate(slots):
            z = back[x]
            if x in crates:
                t.set(x, y, z, 'oceanexpansion:contraband_crate[facing=south]')
            elif i % 3 == 0:
                t.barrel(x, y, z, 'south', 'smugglers/stores')
            else:
                t.set(x, y, z, 'barrel[facing=up,open=false]')
                t.set(x, y + 1, z, 'barrel[facing=up,open=false]' if i % 2 else 'white_wool')
        self.dock_jobs = len(crates)
        # the stash: an underwater niche below the dock's west end, behind kelp
        nx = xa + 2
        nz = back[nx] - 1
        for y in (K - 3, K - 2):
            t.set(nx, y, nz, 'water')
        t.set(nx, K - 1, nz, self.rock(nx, K - 1, nz))
        t.chest(nx, K - 3, nz, 'south', 'smugglers/cache')
        t.set(nx, K - 2, nz, 'water')
        for yy in range(2, K - 2):                                     # a curtain of kelp from the sand
            t.set(nx, yy, nz + 1, 'kelp_plant')
        t.set(nx, K - 2, nz + 1, 'kelp')
        # the loft: a storage shelf cut into the back wall over the dock's east end, a rope ladder and a hoist
        lxs = [x for x in sorted(back) if xb - 5 <= x <= xb - 1]
        for x in lxs:
            bz = back[x]
            for z in (bz - 1, bz, bz + 1):
                t.set(x, K + 4, z, 'spruce_planks')
                for y in (K + 5, K + 6, K + 7):
                    if z == bz - 1 and y == K + 7: continue
                    t.set(x, y, z, 'air')
                    self.cove_air.add((x, y, z))
            t.set(x, K + 5, bz + 1, 'spruce_fence' if x != lxs[len(lxs) // 2] else 'air')
        lx0 = lxs[0]
        lz = back[lx0 - 1] if lx0 - 1 in back else back[lx0]
        for y in range(K + 1, K + 6):
            t.set(lx0 - 1, y, lz, 'ladder[facing=south]')
            if t.name_at(lx0 - 1, y, lz - 1) in (None, 'minecraft:air'): t.set(lx0 - 1, y, lz - 1, self.rock(lx0 - 1, y, lz - 1))
        bz = back[lxs[-1]]
        t.set(lxs[-1], K + 5, bz - 1, 'barrel[facing=up,open=false]')
        t.set(lxs[-1], K + 6, bz - 1, 'barrel[facing=up,open=false]')
        t.set(lxs[-2], K + 5, bz - 1, 'red_wool')
        t.set(lxs[-2], K + 6, bz - 1, 'purple_wool')
        t.set(lxs[-1], K + 5, bz, 'white_wool')
        t.set(lxs[0], K + 5, back[lxs[0]] - 1, 'barrel[facing=up,open=false]')
        t.set(lxs[1], K + 7, back[lxs[1]], 'lantern[hanging=true]')
        # the hoist: a post on the loft's edge, an arm over the dock, a rope and a bale of silk hanging from it
        hx = lxs[len(lxs) // 2]
        hz = back[hx] + 1
        t.set(hx, K + 5, hz, 'spruce_fence')
        t.set(hx, K + 6, hz, 'spruce_fence')
        t.set(hx, K + 7, hz, 'spruce_fence')
        t.set(hx, K + 7, hz + 1, 'spruce_fence')
        for y in (K + 4, K + 5, K + 6): t.set(hx, y, hz + 1, 'iron_chain[axis=y]')
        t.set(hx, K + 3, hz + 1, 'white_wool')
        # a mooring line from the sloop to the dock and a sign by the stair
        t.sign(stair_x + 1, K + 2, back[stair_x + 1], ['NO NAMES', 'ON THE', 'WATER', ''], 'south')
        # -- the bunk room: four bunks, a crate, a table, lamps -------------------------------------------
        x0, x1, z0, z1 = BUNK                                  # the tunnel from the dock comes in at (16, z1)
        y = BUNK_Y
        t.bed(x0, y, z0 + 1, 'north', color='brown')
        t.bed(x0 + 2, y, z0 + 1, 'north', color='red')
        t.bed(x0, y, z1 - 1, 'south', color='gray')
        t.bed(x1 - 1, y, z1 - 1, 'east', color='brown')
        t.set(x0 + 1, y, z0, 'barrel[facing=up,open=false]')
        t.set(x0 + 1, y + 1, z0, 'candle[candles=2,lit=true]')
        t.set(x0 + 1, y, z1, 'chest[facing=north,type=single]')
        t.set(x1, y, z0, 'oceanexpansion:contraband_crate[facing=west]')
        t.set(x1 - 1, y, z0, 'barrel[facing=up,open=false]')
        t.set(x1 - 2, y, z0 + 2, 'spruce_slab[type=top]')                 # a dice table
        t.item_frame(x1 - 2, y + 1, z0 + 2, 'up', 'emerald')
        t.set(x1 - 2, y, z0 + 1, 'spruce_stairs[facing=north,half=bottom]')
        t.set(x1 - 2, y, z0 + 3, 'spruce_stairs[facing=south,half=bottom]')
        t.set(x0 + 1, y + 2, z0 + 2, 'lantern[hanging=true]')
        t.set(x1 - 1, y + 2, z1 - 2, 'lantern[hanging=true]')
        t.set(x1 - 2, y + 2, z0 + 2, 'lantern[hanging=true]')
        t.set(x0 + 1, y, z0 + 2, 'brown_carpet')
        t.item_frame(x0, y + 1, z0 + 2, 'east', 'crossbow')
        t.resident(x0 + 1, y, z0 + 2, 'smuggler', 'east')
        t.resident(x0 + 3, y, z0 + 2, 'smuggler', 'south')
        t.resident(x1 - 1, y, z0 + 2, 'smuggler', 'west')
        # a crack in the north wall to watch the sea from bed
        self.window(x0 + 2, y + 1, z0 - 1, 0, -1)
        # -- the stairs: lamps in niches ---------------------------------------------------------------------
        t.set(BUNK[1] + 3, BUNK_Y + 6, 11, 'lantern[hanging=true]')          # over run 1 (stair at BUNK_Y + 2)
        sx, sy, sz = self.stair_top
        t.set(sx, sy + 2, 13, 'lantern[hanging=true]')                       # over run 2 (stair at sy - 2)
        tz0, tz1 = self.tunnel_z
        t.set(16, BUNK_Y + 2, (tz0 + tz1) // 2 + 1, 'lantern[hanging=true]')
        # -- the chief's den --------------------------------------------------------------------------------
        x0, x1, z0, z1 = DEN
        y = DEN_Y
        t.lectern(x0 + 1, y, z1, 'north', 'No Names on the Water', 'the Brine Brotherhood', LEDGER)
        t.chest(x0, y, z1, 'east', 'smugglers/boss')
        t.set(x0 + 3, y, z0, 'oceanexpansion:contraband_crate[facing=south]')
        t.set(x0 + 4, y, z0, 'barrel[facing=up,open=false]')
        t.set(x0 + 4, y + 1, z0, 'candle[candles=3,lit=true]')
        t.set(x0 + 2, y, z0 + 2, 'spruce_slab[type=top]')                 # the chart table
        t.set(x0 + 3, y, z0 + 2, 'spruce_slab[type=top]')
        t.item_frame(x0 + 2, y + 1, z0 + 2, 'up', 'map')
        t.item_frame(x0 + 3, y + 1, z0 + 2, 'up', 'compass')
        t.set(x0 + 2, y, z0 + 3, 'spruce_stairs[facing=south,half=bottom]')
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                if (x, y, z) not in t.blocks or t.name_at(x, y, z) == 'minecraft:air':
                    t.set(x, y, z, 'red_carpet' if (x + z) % 3 else 'purple_carpet')
        t.set(x1, y, z1, 'dark_oak_stairs[facing=east,half=bottom]')         # the chief's chair
        t.set(x1, y, z1 - 1, 'barrel[facing=up,open=false]')
        t.item_frame(x1, y + 1, z1 - 1, 'up', 'gold_ingot')
        t.set(x0 + 2, y + 2, z0 + 2, 'lantern[hanging=true]')
        t.set(x1 - 1, y + 2, z1 - 1, 'lantern[hanging=true]')
        t.item_frame(x0, y + 1, z0 + 2, 'east', 'spyglass')
        t.resident(x0 + 4, y, z0 + 2, 'smuggler_boss', 'south')
        self.window(x1 + 1, y + 1, z0 + 2, 1, 0)
        # -- the lookout on the summit -----------------------------------------------------------------------
        chx, chz = self.chimney
        ly = self.lookout_y
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                p = (chx + a, ly - 1, chz + b)
                if (a, b) != (0, 0):
                    t.set(*p, 'spruce_planks')
                    for yy in range(ly, ly + 2):
                        if (chx + a, yy, chz + b) in t.blocks: t.set(chx + a, yy, chz + b, None)
        for a in (-2, -1, 0, 1, 2):
            for b in (-2, -1, 0, 1, 2):
                if max(abs(a), abs(b)) == 2:
                    p = (chx + a, ly, chz + b)
                    below = (chx + a, ly - 1, chz + b)
                    if below not in t.blocks: t.set(*below, self.rock(*below))
                    if (a + b) % 2 == 0: t.set(*p, 'spruce_fence')
        t.set(chx, ly - 1, chz, 'spruce_trapdoor[facing=south,half=top,open=true]')
        t.set(chx + 1, ly, chz + 1, 'spruce_log[axis=y]')
        t.set(chx + 1, ly + 1, chz + 1, 'spruce_fence')
        t.set(chx + 1, ly + 2, chz + 1, 'lantern[hanging=false]')
        t.item_frame(chx + 1, ly, chz, 'north', 'spyglass')
        t.set(chx - 1, ly, chz + 1, 'spruce_stairs[facing=north,half=bottom]')
        t.set(chx - 1, ly, chz - 1, 'hay_block[axis=y]')

    def window(self, x, y, z, dx, dz):
        """A narrow crack through the rock from a room to the open air, glazed at its mouth with an iron grille."""
        t = self.t
        for k in range(0, 6):
            p = (x + dx * k, y, z + dz * k)
            if not t.inside(*p): return
            nxt = (p[0] + dx, y, p[2] + dz)
            if nxt not in t.blocks or not t.inside(*nxt):
                t.set(*p, 'iron_bars')
                return
            t.set(*p, 'air')

    def light_ledges(self):
        """A lantern on any rock ledge in the cove still too dark (the cove's walls are noisy)."""
        from kit import dark_spots
        for _ in range(4):
            spots = [p for p in dark_spots(self.t) if p in self.cove_air]
            if not spots: return
            placed = []
            for (x, y, z) in spots:
                if any(abs(x - a) + abs(y - b) + abs(z - c) <= 5 for (a, b, c) in placed): continue
                self.t.set(x, y, z, 'lantern[hanging=false]')
                placed.append((x, y, z))

    def build(self):
        self.stack()
        self.cove()
        self.dock()
        self.sloop()
        self.rooms()
        self.shell()
        self.surfaces()
        self.furnish()
        shore_life(self.t, K, self.rng, barnacles=0.25, kelp=0.12, grass=0.3,
                   rock_names={'stone', 'andesite', 'tuff', 'cobblestone', 'mossy_cobblestone', 'diorite', 'gravel',
                               'sand', 'spruce_log'})
        self.light_ledges()
        t = self.t
        t.entrance(int(COVE[0]), K, SZ - 1)
        connect(t)
        return t


LEDGER = [
    'NO NAMES ON THE WATER\n\nThe rules of the Rock:\n1. No names.\n2. No lamps past the fort.\n3. The Rock takes a '
    'tenth.\n4. What the tide hides, the tide keeps.',
    'IN: 40 sacks spice from the south isles. 12 bolts silk, red and purple. 9 pearls from the grotto divers, '
    'paid in rum. Powder, 6 kegs, do not smoke near.',
    'OUT: spice to the Gull, silk to One-Eye, pearls to the man with the copper bell. Powder kept back. '
    'Black pearl: kept back. Not for sale. Not yet.',
    'The keeper on the isle wrote our sail in his log again. Let him. The Tidewatch took Fen off the sloop. '
    'Fen gave them nothing, then gave them the slip.',
    'Fen says the brig wall was soft as cheese. Drinks on Fen. Sloop needs pitch. Lookout keeps the signal: '
    'one lamp, the coast is clear. Two, run dark.',
]


def pieces():
    return [Stack().build()]
