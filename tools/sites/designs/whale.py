"""The Whalefall: the bones of a colossal old whale on the deep floor, become a reef. See DESIGN.md (whale)."""
import math
import random
import zlib

from kit import Template
from loot import item, empty, pool, rolls, sea_chart, named, WORN
from .nature_parts import (CORALS, barnacles, coral_tuft, fbm, free, full, interp, kelp, lay, lichen, on_top, pickle,
                           polyline, rnd, seagrass, surfaces, tropical_fish, wall_fan)

KEY = 'whale'
NAME = 'The Whalefall'
FEATURES = [
    'the bones of a colossal whale (about 45 blocks long) on the deep sea floor: a great skull with its jaws agape, '
    'a curving spine, high arching ribs (some broken and fallen), long flippers and tail flukes',
    'a reef growing on the bones: bone-eating red tube worms, coral fans, glow lichen, sea pickles, kelp and seagrass',
    'clay pots in the skull and the old belly hold ambergris; an old harpoon hangs in the skull',
    'a lost diver: skull, rusted helmet, cut lifeline, kit chest and a last note',
    'tropical fish and a glow squid live in the ribs',
]
SITE = {'anchor': 'seabed', 'depth': (15, 50), 'flatness': 9, 'radius': 24,
        'biomes': ['ocean', 'deep_ocean', 'cold_ocean', 'deep_cold_ocean', 'lukewarm_ocean', 'deep_lukewarm_ocean'],
        'weight': 2, 'inhabited': False}
LAYOUTS = [
    {'weight': 1, 'pieces': [
        {'piece': 'whale/halo', 'at': (0, 0), 'y': -3, 'mode': 'rigid', 'soft': True},
        {'piece': 'whale/skeleton', 'at': (0, 0), 'y': -2, 'mode': 'rigid', 'footing': True, 'soft': False},
        {'piece': 'whale/strays', 'at': (-10, -15), 'turn': 1, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
    ]},
    {'weight': 1, 'pieces': [
        {'piece': 'whale/halo', 'at': (0, 0), 'turn': 2, 'y': -3, 'mode': 'rigid', 'soft': True},
        {'piece': 'whale/skeleton_turned', 'at': (0, 0), 'y': -2, 'mode': 'rigid', 'footing': True, 'soft': False},
        {'piece': 'whale/strays', 'at': (-10, 15), 'turn': 3, 'y': -1, 'mode': 'floor', 'footing': True, 'soft': False},
    ]},
]
LOOT_TABLES = {
    # Clay pots in the skull and the belly: the prize is ambergris.
    'whale/bones': [pool(1, [item('oceanexpansion:ambergris', 3, 1, 2), empty(2)]),
                    pool(rolls(1, 3), [item('bone', 6, 2, 6), item('bone_meal', 4, 3, 8), item('prismarine_crystals', 2, 1, 4),
                                       item('nautilus_shell', 1), item('gold_nugget', 2, 2, 7), empty(3)])],
    # The lost diver's kit.
    'whale/drift': [pool(1, [item('copper_helmet', 1, extra=WORN + named("Hal's Diving Cap"))]),
                    pool(1, [item('iron_spear', 3, extra=WORN), item('lead', 2, 1, 2), empty(2)]),
                    pool(rolls(2, 4), [item('dried_kelp', 6, 2, 6), item('glass_bottle', 3, 1, 2), item('string', 3, 2, 5),
                                       item('oceanexpansion:pearl', 2, 1, 2), item('gold_nugget', 3, 2, 6), item('compass', 1),
                                       item('potion', 1, extra=[{'type': 'minecraft:set_potion', 'id': 'minecraft:water_breathing'}]),
                                       empty(2)]),
                    pool(1, [sea_chart(1), item('oceanexpansion:storm_glass', 1), item('oceanexpansion:ambergris', 1), empty(5)])],
}

W, H, D = 48, 16, 36   # x along the body (snout at x = 1), y up, z across
ZC = 18                # the body's centre line (before it bends)
FLOOR = 2              # bones lying on the sea floor sit at this y (y 1 is the floor's top layer)
SEDIMENT = ('gravel', 'clay', 'sand', 'gravel', 'coarse_dirt', 'mud', 'sand')


class Whale:
    """Places points given in whale coordinates: u along the body from the snout, v across it (to the whale's
    left, positive), y up. The body bends in plan: the head one way, the tail curling the other."""

    def __init__(self, t, curl, seed):
        self.t, self.curl, self.seed = t, curl, seed
        self.rng = random.Random(seed)
        self.bones = set()

    def bend(self, u):
        c = self.curl
        if u >= 17: return c * 5.5 * ((u - 17) / 27.0) ** 2
        return -c * 1.6 * ((17 - u) / 17.0) ** 2

    def at(self, u, v, y):
        du = 0.5
        slope = (self.bend(u + du) - self.bend(u - du)) / (2 * du)
        n = math.hypot(1, slope)
        return (0.5 + u - v * slope / n, y, ZC + self.bend(u) + v / n)

    def bone(self, pts, block='bone_block'):
        """A bone along whale-coordinate points (u, v, y)."""
        cells = polyline([self.at(*p) for p in pts])
        cells = [c for c in cells if self.t.inside(*c)]
        lay(self.t, cells, block)
        self.bones.update(cells)
        return cells

    def blob(self, centre, radii, hollow=None):
        """The cells of an ellipsoid (u, v, y radii) around a whale-coordinate centre, as ('shell' | 'in', cell)."""
        u0, v0, y0 = centre
        ru, rv, ry = radii
        out = []
        for u in range(int(u0 - ru) - 1, int(u0 + ru) + 2):
            for v in range(int(v0 - rv) - 1, int(v0 + rv) + 2):
                for y in range(int(y0 - ry) - 1, int(y0 + ry) + 2):
                    d = ((u - u0) / ru) ** 2 + ((v - v0) / rv) ** 2 + ((y - y0) / ry) ** 2
                    if d > 1: continue
                    p = tuple(int(math.floor(c + .5)) for c in self.at(u, v, y))
                    if not self.t.inside(*p): continue
                    if hollow and ((u - u0) / hollow[0]) ** 2 + ((v - v0) / hollow[1]) ** 2 + ((y - y0) / hollow[2]) ** 2 < 1:
                        out.append(('in', p))
                        continue
                    out.append(('shell', p))
        return out


def spine_height(u):
    return interp([(12, 6.5), (14.5, 7.5), (18, 10.5), (21, 11.5), (24, 11), (27, 9.5), (30, 7.5), (33, 5.2),
                   (36, 3.4), (39, 2.3), (42, 2), (46, 2)], u)


def rib_reach(u):
    return interp([(14, 5.5), (17, 7.8), (20, 9), (23, 9), (26, 8), (28, 6.8)], u)


def skeleton(name, curl, seed, broken):
    """The whale. `curl`: which way the tail sweeps (+1 / -1); `broken`: which ribs are broken or fallen, as
    {(index, side): 'broken' | 'fallen' | 'gone'}."""
    t = Template(name, (W, H, D), seed=seed, wet=True)
    seed = zlib.crc32(seed.encode()) & 0xFFFF
    wh = Whale(t, curl, seed)
    rng = wh.rng

    # -- the skull ----------------------------------------------------------------------------------
    # The cranium: a domed shell with a hollow (pots inside), eye sockets and an open front into the mouth.
    inner = []
    for kind, p in wh.blob((11.6, 0, 5.4), (3.6, 4.0, 3.4), hollow=(2.5, 2.8, 2.3)):
        if kind == 'in': inner.append(p)
        else:
            t.set(*p, 'bone_block[axis=x]')
            wh.bones.add(p)
    # the brow (supraorbital wings) reach out wide over the eyes
    for s in (1, -1):
        wh.bone([(9.0, s * 3.5, 6.6), (9.5, s * 6.6, 5.9), (11.0, s * 6.4, 5.4)])
        wh.bone([(9.0, s * 3.5, 6.0), (10.2, s * 6.0, 5.0)])
    # the rostrum: a long tapering beak of bone over the open mouth (two maxillae and the middle bone, grooves
    # between them), its tip drooping toward the floor
    for u in range(1, 11):
        half = 0.9 + u * 0.34
        top = 4.2 + 0.26 * u
        vs = {0.0}
        for s_ in (1, -1):
            vs.add(s_ * half)
            vs.add(s_ * max(0.0, half - 1.0))
            if u >= 7: vs.add(s_ * max(0.0, half - 2.0))
        for vv in sorted(vs):
            p = tuple(int(math.floor(c + .5)) for c in wh.at(u, vv, top))
            if t.inside(*p):
                t.set(*p, 'bone_block[axis=x]'); wh.bones.add(p)
        for s_ in (1, -1):   # the upper jaw's lip, a block lower along each edge
            p = tuple(int(math.floor(c + .5)) for c in wh.at(u, s_ * half, top - 1))
            if u > 3 and t.inside(*p):
                t.set(*p, 'bone_block[axis=x]'); wh.bones.add(p)
    # hollow out the cranium (water) and open it to the mouth, the eyes and the blowhole
    for p in inner: t.set(*p, 'water'); wh.bones.discard(p)
    for p in [tuple(int(math.floor(c + .5)) for c in wh.at(u, v, y))
              for u in (7.5, 8.5, 9.4) for v in (-1, 0, 1) for y in (3.0, 4.0, 5.0)]:
        if t.inside(*p): t.set(*p, 'water'); wh.bones.discard(p)
    for s in (1, -1):
        for p in (wh.at(10.5, s * 4.1, 5.0), wh.at(11.2, s * 4.1, 5.0)):
            p = tuple(int(math.floor(c + .5)) for c in p)
            t.set(*p, 'water'); wh.bones.discard(p)
    for p in (wh.at(9.4, 0.6, 8.0), wh.at(9.4, -0.6, 8.0)):
        p = tuple(int(math.floor(c + .5)) for c in p)
        if t.inside(*p): t.set(*p, 'water'); wh.bones.discard(p)
    # the lower jaws: two great bowed bones lying on the floor, the mouth agape between them and the rostrum
    for s in (1, -1):
        jaw = []
        drift = 0.9 if s == -curl else 0.0      # one jaw has slipped a little outward
        for i in range(14):
            u = 13.0 - i * 0.96
            v = s * (1.2 + (u / 13.0) * 3.6 + 2.2 * math.sin(math.pi * u / 13.0) + drift * (1 - u / 13.0))
            jaw.append((u, v, FLOOR + (1.0 if u > 10 else 0.0)))
        cells = wh.bone(jaw)
        for c in cells:   # thick at the back
            if c[0] > 7 and t.inside(c[0], c[1] + 1, c[2]) and free(t, (c[0], c[1] + 1, c[2])) and rnd(*c, seed) < .7:
                t.set(c[0], c[1] + 1, c[2], 'bone_block[axis=x]'); wh.bones.add((c[0], c[1] + 1, c[2]))

    # -- the spine -----------------------------------------------------------------------------------
    spine_pts = [(u / 2.0, 0, spine_height(u / 2.0)) for u in range(28, 86)]
    wh.bone(spine_pts)
    for i, (u, v, y) in enumerate(spine_pts):
        if i % 4: continue   # a vertebra every two blocks: its spinous process up, the transverse processes out
        tall = 2 if u < 31 else 1 if u < 38 else 0
        for k in range(1, tall + 1):
            p = tuple(int(math.floor(c + .5)) for c in wh.at(u, 0, y + k))
            if t.inside(*p) and free(t, p): t.set(*p, 'bone_block[axis=y]'); wh.bones.add(p)
        reach = 1 if u < 26 else 2 if u < 36 else 1 if u < 41 else 0
        for s in (1, -1):
            for k in range(1, reach + 1):
                p = tuple(int(math.floor(c + .5)) for c in wh.at(u, s * k, y))
                if t.inside(*p) and free(t, p): t.set(*p, 'bone_block[axis=z]'); wh.bones.add(p)
        if 33 < u < 41:   # chevron bones hang under the tail
            p = tuple(int(math.floor(c + .5)) for c in wh.at(u, 0, y - 1))
            if t.inside(*p) and p[1] >= FLOOR and free(t, p): t.set(*p, 'bone_block[axis=y]'); wh.bones.add(p)

    # -- the ribs -------------------------------------------------------------------------------------
    fallen_pieces = []
    for i, u in enumerate((15.0, 17.0, 19.0, 21.0, 23.0, 25.0, 27.0)):
        top = spine_height(u)
        reach = rib_reach(u) + (rng.random() - .5) * .8
        for s in (1, -1):
            fate = broken.get((i, s))
            if fate == 'gone': continue
            pts = []
            for k in range(13):
                th = k / 12 * math.pi / 2
                v = s * (0.6 + (reach - 0.6) * math.sin(th) ** 0.75)
                y = FLOOR + (top - FLOOR + 0.6) * math.cos(th) ** 0.8
                pts.append((u + 1.6 * (k / 12) ** 1.6, v, y))
            if fate == 'broken':   # the upper half still hangs from the spine; the rest lies below
                cut = rng.randint(5, 7)
                wh.bone(pts[:cut])
                fallen_pieces.append((pts[cut:], s))
            elif fate == 'fallen':
                fallen_pieces.append((pts, s))
            else:
                wh.bone(pts)
    for pts, s in fallen_pieces:   # a fallen rib lies flat on the floor, outside the cage
        foot = pts[-1]
        n = len(pts)
        flat = [(foot[0] - 2.0 + 0.5 * k, foot[1] + s * (1.0 + 0.55 * k + 0.6 * math.sin(k / max(1, n - 1) * math.pi)), FLOOR)
                for k in range(n)]
        wh.bone(flat)

    # -- the flippers (long, like a humpback's) and the little hip bones ---------------------------------
    for s in (1, -1):
        reach = 1.0 if s == curl else 0.86
        wh.bone([(14.0, s * 3.6, 6.0), (14.6, s * 4.6, 4.0), (15.0, s * 5.0, 3.0)])         # shoulder blade
        wh.bone([(14.4, s * 3.8, 5.2), (13.6, s * 4.8, 4.2)])
        arm = [(15.0, s * 5.0, 3.0), (16.6, s * 7.0, FLOOR + 0.4), (18.6, s * 9.0 * reach, FLOOR)]
        wh.bone(arm)
        wh.bone([(15.6, s * 5.0, 3.0), (17.4, s * 7.0, FLOOR), (19.4, s * 8.8 * reach, FLOOR)])
        for k, (du, dv) in enumerate(((3.6, 4.6), (4.6, 4.2), (5.4, 3.2), (6.0, 2.0))):   # the long fingers
            base = (18.8 + 0.3 * k, s * (9.0 * reach - 0.3 * k), FLOOR)
            gap = k % 2
            pts = [base, (base[0] + du * .5, base[1] + s * dv * .5, FLOOR), (base[0] + du, base[1] + s * dv, FLOOR)]
            cells = wh.bone(pts)
            if gap and len(cells) > 3:  # joints: little gaps between finger bones
                t.set(*cells[len(cells) // 2], None); wh.bones.discard(cells[len(cells) // 2])
        wh.bone([(30.5, s * 2.4, FLOOR + 1), (32.0, s * 2.8, FLOOR)])    # hip bone

    # -- the flukes -----------------------------------------------------------------------------------
    tip = 39.6
    for s in (1, -1):
        edge = [(tip, s * 0.5), (tip + 1.4, s * 3.4), (tip + 2.8, s * 6.0), (tip + 4.4, s * 8.4),   # leading edge
                (tip + 4.6, s * 6.6), (tip + 4.2, s * 4.4), (tip + 3.8, s * 2.4), (tip + 4.3, s * 0.4)]  # trailing edge
        wh.bone([(u, v, FLOOR) for u, v in edge])
        wh.bone([(tip + 0.8, s * 0.6, FLOOR), (tip + 3.5, s * 6.0, FLOOR)])
        wh.bone([(tip + 1.6, s * 0.6, FLOOR), (tip + 3.4, s * 3.2, FLOOR)])

    # -- the sea floor under it: a low drift of dark sediment around everything resting on the floor ------
    under = set()
    for (x, y, z) in list(wh.bones):
        if y <= FLOOR + 1:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    under.add((x + dx, z + dz))
    halo = set()
    for (x, z) in under:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if rnd(x + dx, 0, z + dz, seed) < .55: halo.add((x + dx, z + dz))
    under |= halo
    sediment = lambda x, y, z: SEDIMENT[int(fbm(x, y, z, 5, seed + 3) * 9.99) % len(SEDIMENT)]
    for (x, z) in under:
        if not (0 <= x < W and 0 <= z < D): continue
        t.set(x, 0, z, sediment(x, 0, z))
        if t.get(x, 1, z) is None: t.set(x, 1, z, sediment(x, 1, z))
        if (x, z) not in halo and fbm(x, 2, z, 4, seed + 9) > .58 and free(t, (x, FLOOR, z)):
            t.set(x, FLOOR, z, sediment(x, 2, z))   # little drifts banked against the bones
    # the rest of the hollow under the cranium and the belly: a floor of silt, so pots stand on it
    for (x, y, z) in inner:
        if y == FLOOR and t.get(x, y - 1, z) is None: t.set(x, y - 1, z, 'gravel')

    # -- the reef on the bones ----------------------------------------------------------------------------
    bones = sorted(wh.bones)
    tops, sides, unders = surfaces(t, bones)
    rng.shuffle(tops); rng.shuffle(sides); rng.shuffle(unders)
    for p in tops[:34]:   # bone-eating worms (red plumes) colonise the bone in clusters
        if fbm(*p, 6, seed + 21) > .52:
            on_top(t, p, 'oceanexpansion:tube_worms')
    for p in tops[34:70]:
        r = rng.random()
        if r < .35: pickle(t, p, rng, 2)
        elif r < .6: coral_tuft(t, p, rng)
    for p, f in sides[:60]:
        r = rng.random()
        if r < .22: wall_fan(t, p, f, rng.choice(CORALS))
        elif r < .65: barnacles(t, p, f)
        else: lichen(t, p, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[f])
    for p in unders[:40]:
        lichen(t, p, 'up')
    # kelp and seagrass on the sediment
    floor_cells = [(x, FLOOR, z) for (x, z) in sorted(under) if 0 <= x < W and 0 <= z < D]
    rng.shuffle(floor_cells)
    planted = 0
    for p in floor_cells:
        if not free(t, p) or not full(t, (p[0], p[1] - 1, p[2])): continue
        r = rng.random()
        roofed = any(t.name_at(p[0] + dx, y, p[2] + dz) == 'minecraft:bone_block'
                     for y in range(FLOOR + 2, H) for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))
        if r < .08 and planted < 12 and not roofed:   # kelp only in the open, never inside the ribs
            if kelp(t, p, rng.randint(4, 10), top=H): planted += 1
        elif r < .45:
            seagrass(t, p, tall=rng.random() < .3)

    # -- the skull's hollow: pots of ambergris and the old harpoon --------------------------------------------
    cav = sorted(p for p in inner if p[1] == min(q[1] for q in inner))
    floor_in = [p for p in cav if full(t, (p[0], p[1] - 1, p[2])) and t.name_at(*p) == 'minecraft:water']
    pot_spot = floor_in[len(floor_in) // 2] if floor_in else cav[len(cav) // 2]
    t.pot(*pot_spot, 'east', loot='whale/bones', sherds=['brick', 'brick', 'brick', 'brick'])
    # the harpoon: hung on the cranium's inner wall, near the pot
    best = None
    for p in inner:
        if t.name_at(*p) != 'minecraft:water' or p[1] != pot_spot[1] + 1: continue
        for f, d in (('south', (0, -1)), ('north', (0, 1)), ('east', (-1, 0)), ('west', (1, 0))):
            if full(t, (p[0] + d[0], p[1], p[2] + d[1])):
                dist = abs(p[0] - pot_spot[0]) + abs(p[2] - pot_spot[2])
                if best is None or dist < best[0]: best = (dist, p, f)
    if best: t.item_frame(*best[1], best[2], 'iron_spear')
    # the old belly: two more pots on the sediment inside the ribcage
    for u, v in ((20.0, 1.6 * curl), (23.5, -1.8 * curl)):
        p = tuple(int(math.floor(c + .5)) for c in wh.at(u, v, FLOOR))
        if t.get(p[0], p[1] - 1, p[2]) is None: t.set(p[0], p[1] - 1, p[2], 'gravel')
        if t.get(p[0], 0, p[2]) is None: t.set(p[0], 0, p[2], 'gravel')
        t.pot(*p, 'south', loot='whale/bones')
        for d in ((1, 0), (-1, 0), (0, 1)):
            q = (p[0] + d[0], p[1], p[2] + d[1])
            if free(t, q) and rng.random() < .6: pickle(t, q, rng, 1)

    # -- the lost diver, by the mouth: skull, helmet, kit, cut lifeline and a last note ------------------------
    side = -curl
    dx_, dy_, dz_ = (int(math.floor(c + .5)) for c in wh.at(5.0, side * 9.5, FLOOR))
    for x in range(dx_ - 2, dx_ + 3):
        for z in range(dz_ - 2, dz_ + 3):
            t.set(x, 0, z, 'sand'); t.set(x, 1, z, 'sand')
            if t.name_at(x, FLOOR, z) in ('minecraft:seagrass', 'minecraft:tall_seagrass', 'minecraft:kelp', 'minecraft:kelp_plant'):
                t.set(x, FLOOR, z, None)
    t.set(dx_, FLOOR, dz_, 'skeleton_skull[rotation=6]')
    t.item_frame(dx_ + 1, FLOOR, dz_, 'up', 'copper_helmet')
    t.chest(dx_, FLOOR, dz_ - side, 'south' if side > 0 else 'north', 'whale/drift')
    t.sign(dx_ - 1, FLOOR, dz_ + side, ['Found her. The', 'old bull, as in', "Gran's song.", 'Grey gold.'],
           'east', wood='spruce', wall=False)
    t.sign(dx_ + 2, FLOOR, dz_ + side, ['Line fouled.', 'Air going.', 'Tell Mara I', 'found it. - Hal'],
           'east', wood='spruce', wall=False)
    for k in range(1, 6):   # his lifeline, cut, trailing away over the sand
        x = dx_ - 1 - k
        if 0 <= x < W:
            for y in (0, 1):
                if t.get(x, y, dz_ + (k // 3) * side) is None: t.set(x, y, dz_ + (k // 3) * side, 'sand')
            t.set(x, FLOOR, dz_ + (k // 3) * side, 'iron_chain[axis=x]')
    t.entrance(dx_, FLOOR, dz_)

    # -- the living: fish among the ribs, a glow squid in the skull -----------------------------------------
    for u, v, y in ((18, 2, 6), (20, -3, 5), (22, 1, 8), (24, -2, 4), (26, 3, 6), (8, 3, 3)):
        p = tuple(int(math.floor(c + .5)) for c in wh.at(u, v * curl, y))
        if free(t, p): tropical_fish(t, p, rng)
    p = tuple(int(math.floor(c + .5)) for c in wh.at(21, 0, 5))
    if free(t, p): t.creature(*p, 'minecraft:glow_squid', 'east')
    return t


def halo():
    """The dark stain of a whale fall on the sea floor, wider than the bones (soft: it only recolours ground)."""
    t = Template('whale/halo', (W, 5, D), seed='whale/halo')
    for x in range(W):
        for z in range(D):
            e = ((x - W / 2) / (W / 2 - .5)) ** 2 + ((z - D / 2) / (D / 2 - .5)) ** 2
            if e + (fbm(x, 0, z, 5, 4) - .5) * .7 > 1: continue
            n = fbm(x, 1, z, 4, 11)
            if n < .38 and e > .35: continue
            block = 'mud' if n > .7 else 'clay' if n > .6 else 'gravel' if n > .5 else 'coarse_dirt' if n > .44 else 'sand'
            for y in range(5): t.set(x, y, z, block)
    return t


def strays():
    """Bones the currents carried off: a broken rib, two loose vertebrae and a flipper bone, grown over."""
    t = Template('whale/strays', (11, 4, 9), seed='whale/strays', wet=True)
    rng = t.rng
    for x in range(11):
        for z in range(9):
            if ((x - 5) / 5.5) ** 2 + ((z - 4) / 4.5) ** 2 < 1 and rnd(x, 0, z, 5) < .8:
                t.set(x, 0, z, 'gravel' if rnd(x, 1, z, 6) < .5 else 'sand')
    cells = set()
    cells.update(lay(t, polyline([(1, 1, 2), (4, 1, 1), (7, 1, 1.5), (9, 1, 3)])))          # a rib, lying flat
    cells.update(lay(t, [(2, 1, 6), (3, 1, 6)]))                                            # a vertebra
    t.set(2, 2, 6, 'bone_block[axis=y]'); cells.add((2, 2, 6))
    t.set(2, 1, 5, 'bone_block[axis=z]'); t.set(2, 1, 7, 'bone_block[axis=z]'); cells |= {(2, 1, 5), (2, 1, 7)}
    cells.update(lay(t, [(6, 1, 6), (7, 1, 6), (7, 2, 6)]))                                 # another, tipped up
    cells.update(lay(t, polyline([(5, 1, 3), (8, 1, 4)])))                                  # a finger bone
    tops, sides, unders = surfaces(t, sorted(cells))
    for p in tops:
        r = rng.random()
        if r < .35: on_top(t, p, 'oceanexpansion:tube_worms')
        elif r < .55: pickle(t, p, rng, 2)
        elif r < .75: coral_tuft(t, p, rng)
    for p, f in sides:
        r = rng.random()
        if r < .12: wall_fan(t, p, f, rng.choice(CORALS))
        elif r < .3: barnacles(t, p, f)
    for x in range(11):
        for z in range(9):
            if t.get(x, 0, z) and free(t, (x, 1, z)) and rng.random() < .3: seagrass(t, (x, 1, z), tall=rng.random() < .3)
    kelp(t, (0, 1, 4), 7); kelp(t, (9, 1, 6), 9)
    return t


def pieces():
    return [halo(),
            skeleton('whale/skeleton', 1, 'whale-a', {(1, 1): 'broken', (4, -1): 'broken', (5, 1): 'fallen', (6, -1): 'gone'}),
            skeleton('whale/skeleton_turned', -1, 'whale-b', {(2, -1): 'broken', (3, 1): 'fallen', (5, -1): 'broken',
                                                             (6, 1): 'broken'}),
            strays()]
