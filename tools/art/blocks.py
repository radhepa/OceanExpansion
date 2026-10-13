"""Ocean Expansion block and item art: every texture, block model, blockstate, item model definition and the
diving helmet's worn look, painted from palette-locked ramps (pixel.RAMPS). One texel is always 1/16 block.

    python tools/art/blocks.py                    # write every file under src/main/resources/assets/oceanexpansion
    python tools/art/blocks.py --check            # verify the written files match this script
    python tools/art/blocks.py --preview out.png  # contact sheet: blocks in place, every state, items, the helmet

Blocks: giant_clam, tube_worms, barnacles, sea_glass, sea_glass_pane, signal_lamp, contraband_crate, haunt.
Items: pearl, black_pearl, ambergris, storm_glass, diving_helmet (sprites and the helmet's equipment layer live in
ocean_items.py). Never hand-edit the outputs; change the scripts and rerun.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixel  # noqa: E402
from pixel import RAMPS as R  # noqa: E402
from ocean_paint import paint, put, soft_locked, png, render_scene, slot, gui_block  # noqa: E402
import ocean_items  # noqa: E402

NS = 'oceanexpansion'
ASSETS = pixel.PROJECT / f'src/main/resources/assets/{NS}'
FACINGS = (('north', 0), ('east', 90), ('south', 180), ('west', 270))


def grid(pattern, palette, w=16, h=16):
    rows = [r.replace(' ', '') for r in pattern.strip('\n').splitlines()]
    assert len(rows) == h and all(len(r) == w for r in rows), [(i, len(r)) for i, r in enumerate(rows)]
    return paint(pattern, palette, (w, h))


# == sea glass ==========================================================================================
# Frosted, sea-worn glass: translucent teal-green, a frosted rim (lit top-left, shaded bottom-right) that
# softens at the corners, cloudy frost patches and a couple of bright glints.
GLASS_ALPHAS = (0, 130, 165, 180, 205, 215, 225)
GLASS = {'a': (R['crystal'][1], 165), 'b': (R['crystal'][2], 180), 'c': (R['prismarine'][2], 180),
         'd': (R['crystal'][3], 215), 'e': (R['crystal'][4], 225), 'f': (R['prismarine'][1], 205),
         'g': (R['crystal'][2], 205), 'h': (R['crystal'][2], 130)}
SEA_GLASS = """
hdddeddddddgdddh
debbaaaaaaabbaag
dbeaaaaaaaaaaacf
dbaaaaabbaaaaaaf
daaaaaabbbaaaaaf
gaaaaaaaaaaacaaf
daacaaaaaaaaaaaf
daaaaaaaaaaaaaag
daaaaabaaaaaaaaf
daaaabbaaaacaaaf
gaaaaaaaaaabbaaf
daaaaaaaaaaaaaaf
daacaaaaaaaaabef
daaaaaaabaaaaeaf
dbaaaaaaaaaaaacf
hffgffffffgffffh
"""
PANE_TOP = """
.......dg.......
.......df.......
.......ef.......
.......df.......
.......gf.......
.......df.......
.......dc.......
.......df.......
.......df.......
.......gf.......
.......df.......
.......df.......
.......ef.......
.......df.......
.......gf.......
.......df.......
"""


def sea_glass():
    return grid(SEA_GLASS, GLASS)


def sea_glass_pane_top():
    return grid(PANE_TOP, GLASS)


# == giant clam ===========================================================================================
# Shell tones, dark to light, and the masks that give both valves a scalloped lip: the lower valve's teeth
# stand on columns 1, 2 (mod 4) and the lid's on 3, 0, so they interlock. Both sets map onto themselves when a
# face is mirrored (u -> 15 - u), so a wall's inner and outer faces always cut the same teeth.
SHELL = [R['dripstone'][3], R['dripstone'][4], R['sand'][1], R['bone'][0], R['bone'][3], R['calcite'][4]]
LOWER_RIB = {1: 4, 2: 3, 3: 2, 0: 1}   # column % 4 -> shell tone (rib lit left, groove at 0)
LID_RIB = {3: 4, 0: 3, 1: 2, 2: 1}


def clam_top():
    """The lid seen from above: four broad ribs running back from the lip (lid ribs on x % 4 = 3, 0),
    growth lines every three rows, a lighter lip at the front (v 2) and the worn umbo at the hinge."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            tone = LID_RIB[x % 4]
            if (y - 2) % 3 == 2 and tone > 1:
                tone -= 1
            if y <= 2:
                tone = min(5, tone + 1)
            if y >= 12:
                tone = max(1, tone - 1)
            if x in (0, 1, 14, 15):
                tone = max(0, tone - 1)
            put(image, x, y, SHELL[tone])
    for x, y, c in ((5, 6, R['tuff'][4]), (6, 6, R['calcite'][1]), (10, 9, R['prismarine'][1]), (11, 9, R['prismarine'][2]),
                    (12, 4, R['tuff'][4]), (3, 10, R['prismarine'][2]), (9, 12, R['dripstone'][2]), (8, 13, R['dripstone'][3])):
        put(image, x, y, c)
    return image


def clam_side():
    """Rows by height (auto UVs): 8 the lid's crown, 9 the lid, 10 the lid's teeth, 11 the lower valve's teeth,
    12-14 the lower valve, 15 its foot. Columns: ribs by the masks above."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            if y <= 10:
                tone = LID_RIB[x % 4]
                if y == 10 and x % 4 not in (3, 0):
                    continue
                if y == 8:
                    tone = max(1, tone - 1)
            else:
                tone = LOWER_RIB[x % 4]
                if y == 11:
                    if x % 4 not in (1, 2):
                        continue
                    tone = min(5, tone + 1)
                if y == 14:
                    tone = max(0, tone - 1)
                if y == 15:
                    tone = max(0, tone - 2)
            put(image, x, y, SHELL[tone])
    for x, y, c in ((6, 13, R['sand'][1]), (11, 14, R['sand'][0]), (2, 12, R['sand'][2]), (13, 9, R['sand'][1])):
        put(image, x, y, c)
    return image


NACRE = R['nacre']


def clam_inner():
    """The nacre inside the lower valve's lip (same teeth as clam_side on row 11), and the brown hinge
    ligament on rows 0-1."""
    image = Image.new('RGBA', (16, 16))
    for y in range(2, 16):
        for x in range(16):
            if y == 11 and x % 4 not in (1, 2):
                continue
            tone = 6 if y == 11 else (5 if (x + y) % 5 else 4)
            if y >= 13:
                tone = 4
            put(image, x, y, NACRE[tone])
    for x in range(16):
        put(image, x, 0, R['dripstone'][1 + (x % 3 == 0)])
        put(image, x, 1, R['dripstone'][0])
    return image


FLESH = {'o': R['pink'][1], 'p': R['pink'][2], 'q': R['pink'][3], 'P': R['pink'][5], 'Q': R['pink'][6],
         'm': R['brain'][1], 'M': R['brain'][0], 't': R['prismarine'][3]}
CLAM_FLESH = """
oooooooooooooooo
oooooooooooooooo
oQPQPPQPPQPPQPQo
oPQPqPPqPPqPPQPo
oQPppmppqppmpPQo
oPPqppptppppqPPo
oPqppppqpptppqPo
oQPmpptppppmpPQo
oPPpppqppqpppPPo
oPqptpoMMoptpqPo
oQPppMoqqoMppPQo
oPPmppoMMopmpPPo
oPQPqPPqPPqPPQPo
oQPQPPQPPQPPQPQo
oooooooooooooooo
oooooooooooooooo
"""


def clam_flesh():
    """The pink mantle: a frilled rim two texels deep (so it shows on the lid's underside and in the bowl),
    magenta eyespots, a few iridescent teal flecks and the siphon slit at the back."""
    return grid(CLAM_FLESH, FLESH)


def clam_pearl():
    """Lustre for the voxel pearl: brightest at the centre (its top faces), pink-lilac towards the edges."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + .5 - 7.5, y + .5 - 6.5)
            c = (R['calcite'][5] if d < 1.2 else NACRE[7] if d < 2.6 else NACRE[6] if d < 3.8 else
                 NACRE[5] if d < 5 else NACRE[4] if d < 6.4 else NACRE[3])
            put(image, x, y, c)
    return image


# == barnacles =============================================================================================
BARN = {'W': R['calcite'][4], 'w': R['calcite'][2], 'v': R['calcite'][1], 'b': R['bone'][1], 's': R['tuff'][4],
        'g': R['tuff'][3], 'd': R['tuff'][1], 'k': R['tuff'][0], 'n': R['sand'][0], 'N': R['dripstone'][3],
        'a': R['prismarine'][0], 'A': R['prismarine'][1]}
# Rows 0-1: the plated walls of a tall cone (cols 0-2 and 3-5); row 2: a flared base (cols 0-4); row 3: a spat's
# wall (cols 0-1). Rows 4-8: tops: the base ring (cols 0-4), a cone's mouth with its tan beak plates round the
# dark opening (cols 5-7), a spat's mouth (cols 8-9).
BARNACLES = """
wWvvWw..........
svgsvg..........
gsdag...........
wv..............
svvvswnwnksvvs..
vgsgvnknkdvggv..
vssgvwnw..vgAv..
vgsAv.....svvs..
svgvs...........
................
................
................
................
................
................
................
"""
BARN_UV = {'cone': [0, 0, 3, 1], 'cone_b': [3, 0, 6, 1], 'base': [0, 2, 5, 3], 'spat': [0, 3, 2, 4],
           'ring': [0, 4, 5, 9], 'ring4': [10, 4, 14, 8], 'mouth': [5, 4, 8, 7], 'spat_mouth': [8, 4, 10, 6]}
CRUST = """
................
.......ws.....v.
.vs...wkvs......
.skv...sv....sv.
..s.........wks.
.........v...vs.
...v............
..wks..........v
..svs....s......
..........v.....
v........ws.....
.....v..wkvs....
....wks..svs..v.
....svv.........
.........v......
...v............
"""


def barnacles():
    return grid(BARNACLES, BARN)


def barnacles_crust():
    """Spat and small barnacles scattered between the big cones, so the crust reads as a crust."""
    return grid(CRUST, BARN)


# == tube worms ============================================================================================
WORM = {'W': R['calcite'][4], 'w': R['bone'][2], 'v': R['calcite'][1], 's': R['tuff'][4], 'o': R['tuff'][0],
        'k': R['fire_coral'][0], 'r': R['fire_coral'][1], 'R': R['fire_coral'][2], 'L': R['fire_coral'][3],
        'p': R['pink'][4]}
PLUMES = [  # 5 wide x 4 tall feathery crowns, cupped like a shaving brush, drawn above a tube's mouth
    """
L.p.L
RLRLR
rRLRr
.rkr.
""",
    """
.L.L.
LRpRL
.rRr.
..k..
""",
    """
p.L.p
LRLRL
rRkRr
.....
""",
]
TUBES = [  # (x of left column, top row, plume or None)
    (1, 7, 0), (5, 4, 1), (9, 9, None), (12, 5, 2), (7, 11, 0), (14, 12, None)]


def tube_worms():
    """The cross-plane sprite: white ringed tubes of different heights, most crowned by a blood-red plume,
    one withdrawn (a dark mouth)."""
    image = Image.new('RGBA', (16, 16))
    for x0, top, plume in TUBES:
        for y in range(top, 16):
            ring = (y - top) % 3 == 2
            put(image, x0, y, WORM['v' if ring else 'W'])
            if x0 + 1 < 16:
                put(image, x0 + 1, y, WORM['s' if ring else 'w'])
        if plume is None:
            put(image, x0, top, WORM['w'])
            if x0 + 1 < 16:
                put(image, x0 + 1, top, WORM['o'])
        else:
            rows = PLUMES[plume].strip('\n').splitlines()
            px, py = x0 - 2 + (0 if x0 < 14 else -1), top - len(rows) + (1 if rows[-1] == '.....' else 0)
            for dy, row in enumerate(rows):
                for dx, ch in enumerate(row):
                    if ch != '.' and 0 <= px + dx < 16 and 0 <= py + dy < 16:
                        put(image, px + dx, py + dy, WORM[ch])
    return image


def tube_worms_tube():
    """For the box tubes (auto UVs by height): ringed white; rows 0-1 cols 0-1 hold the mouth for top faces."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            ring = y % 3 == 0
            lit = x % 2 == 0
            put(image, x, y, WORM[('v' if lit else 's') if ring else ('W' if lit else 'w')])
    paint('wv\nvo', WORM, base=image)
    return image


# Plume tufts for the box tubes: two 3x3 side faces (feather tips lit, dark where they leave the tube) and a
# 3x3 crown seen from above, its corners open so the tuft looks round.
PLUME = """
LRLpRL..........
RLRRLR..........
rkrrkr..........
................
.L..............
LRL.............
.L..............
................
................
................
................
................
................
................
................
................
"""
PLUME_UV = {'side_a': [0, 0, 3, 3], 'side_b': [3, 0, 6, 3], 'crown': [0, 4, 3, 7]}


def tube_worms_plume():
    return grid(PLUME, WORM)


# == signal lamp ===========================================================================================
CU = R['copper_block']
BRASS = R['gold']
LAMP = {'1': CU[0], '2': CU[1], '3': CU[2], '4': CU[3], '5': CU[4], '6': CU[5], '7': CU[6], '8': CU[7],
        'a': BRASS[0], 'b': BRASS[1], 'c': BRASS[2], 'd': BRASS[3], 'e': BRASS[4], 'f': BRASS[5],
        'k': R['bark'][0], 'K': R['iron'][0], 'g': R['verdigris'][2], 'G': R['verdigris'][6], 'h': R['verdigris'][4],
        'i': R['iron'][1], 'I': R['iron'][2], 'J': R['iron'][3], 's': R['steel'][2], 'S': R['steel'][3]}
LAMP_SIDE = """
6666666666666666
6666666666666666
cccdcccccccdcccc
568e78888887e865
5763kkkkkk3G7665
5766888888g67665
5763kkkkkk3h7665
5766888888G67665
5763kkkkkk367665
5766666666667665
5g7e6666666e7g65
aaabbbbbbbbbbaaa
5555555555555555
5555555555555555
5555555555555555
5555555555555555
"""
LAMP_FRONT = """
................
................
...bccccccccb...
...cd.......c...
...c.........c..
...c..........b.
...c..........b.
...c..........b.
...c..........b.
...c..........b.
...b..........b.
...abbbbbbbbba..
................
................
................
................
"""


def lamp_side():
    """The housing's walls (rows 2-11 by height): brass bands, riveted copper, three louvred vents with a
    lit lip, and verdigris weeping from the vents and rivets."""
    return grid(LAMP_SIDE, LAMP)


def lamp_bezel():
    """The brass bezel ring (rows 2-11, cols 3-12), its round opening cut to the lens."""
    image = Image.new('RGBA', (16, 16))
    for y in range(2, 12):
        for x in range(3, 13):
            d = math.hypot(x + .5 - 8, y + .5 - 7)
            if d < 3.9:
                continue
            edge = y in (2, 11) or x in (3, 12)
            if edge:
                c = BRASS[2] if (y == 2 or x == 3) else BRASS[0]
            else:
                c = BRASS[3] if (x + .5 - 8) + (y + .5 - 7) < 0 else BRASS[1]
            put(image, x, y, c)
    for x, y in ((4, 3), (11, 3), (4, 10), (11, 10)):
        put(image, x, y, BRASS[5])
    return image


def lamp_lens():
    """A stepped Fresnel lens glowing amber (rows 3-10, cols 4-11 by auto UVs): a white-hot heart, yellow and
    orange rings with darker grooves, and a glint."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + .5 - 8, y + .5 - 7)
            if d >= 4.0:
                continue
            c = (R['flame'][6] if d < 1.2 else R['flame'][5] if d < 2.0 else R['flame'][3] if d < 2.5 else
                 R['flame'][4] if d < 3.2 else R['honey'][1])
            put(image, x, y, c)
    put(image, 6, 4, R['flame'][6])
    put(image, 5, 5, R['flame'][5])
    return image


def lamp_top():
    """The housing's roof (u, v 3-12): a brass rim round a domed copper lid with the chimney's smoke hole."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            put(image, x, y, CU[4])
    for y in range(3, 13):
        for x in range(3, 13):
            if y == 3 or x == 3:
                c = BRASS[2]
            elif y == 12 or x == 12:
                c = BRASS[0]
            else:
                d = math.hypot(x + .5 - 8, y + .5 - 8)
                c = CU[7] if d > 4 and (x < 8 and y < 8) else CU[6] if d > 3 else CU[5] if d > 2 else CU[3]
            put(image, x, y, c)
    for x, y in ((4, 4), (11, 4), (4, 11), (11, 11)):
        put(image, x, y, BRASS[4])
    return image


STAND = """
iiiiiiiiiiiiiiii
iJJJJJJJJJJJJJJi
iJIIIIIIIIIIIIIi
iJISIIIIIIIIIIIi
iJIIiiiiiiiiIIIi
iJIIiKKKKKKiIIIi
iJIIiKKKKKKiIIIi
iJIIiKKKKKKiIIIi
iJIIiKKKKKKiIIIi
iJIIiKKKKKKiIIIi
iJIIiiiiiiiiISIi
iJIIIIIIIIIIIIIi
cddcdccdcdccddcc
JISJIJSJISJIJSJI
iIiJiIiJiIiJiIiJ
KiKiKiKiKiKiKiKi
"""


def lamp_stand():
    """The cast-iron pedestal (auto UVs): plate top (3-12), row 12 the brass collar, 13-14 the neck, 15 the plate's
    rim with rivets."""
    image = grid(STAND, LAMP)
    for x, y in ((3, 3), (12, 3), (3, 12), (12, 12)):
        put(image, x, y, R['steel'][4])
    return image


# cols 0-11: the hood (rows 0-5 its top, brass front edge first; rows 6-11 its underside; row 12 a brass strip;
# row 13 its side), cols 6-9 row 13 the cap's side; cols 12-14 rows 0-1 the chimney (vent slits); cols 12-13
# rows 2-3 the lever's boss; col 14 rows 4-8 the lever; cols 12-13 rows 10-11 its knob; col 15 rows 2-11 the
# bezel's sides; cols 12-15 rows 12-15 the cap's top with its smoke hole.
LAMP_PARTS = """
cdcdcdcdcdcd787c
766686666867k8kd
766666666667edcc
655555565556cbcc
655655555556c5ec
544444444445c5dc
433343333334c5dc
433333333334c5cc
332222232233c5bc
332222222233c5ac
322222222223KK5c
221111111122KK5c
abbbbbbbbbbacddc
565565cddc55dkkd
5555555555cddkkd
55555555555ccddc
"""
PART = {'hood_up': [0, 0, 12, 6], 'hood_down': [0, 6, 12, 12], 'hood_front': [0, 12, 12, 13], 'hood_side': [0, 13, 6, 14],
        'chimney': [12, 0, 15, 2], 'boss': [12, 2, 14, 4], 'lever': [14, 4, 15, 9], 'knob': [12, 10, 14, 12],
        'bezel_side': [15, 2, 16, 12], 'cap_side': [6, 13, 10, 14], 'cap_top': [12, 12, 16, 16]}


def lamp_parts():
    """Hood (riveted copper, brass front edge), chimney with vent slits, brass cap and the shutter lever."""
    return grid(LAMP_PARTS, LAMP)


# == contraband crate ======================================================================================
SP = R['spruce']
CRATE = {'1': SP[0], '2': SP[1], '3': SP[2], '4': SP[3], '5': SP[4], '6': SP[5], '7': SP[6],
         'k': R['bark'][0], 'K': R['bark'][1], 'B': R['bark'][2], 'b': R['bark'][3],
         't': R['coal'][1], 'T': R['coal'][2], 'u': R['coal'][3], 'U': R['coal'][4], 'x': R['coal'][5], 'z': R['coal'][0],
         'n': R['iron'][1], 'N': R['steel'][2], 'w': R['calcite'][2], 'W': R['calcite'][3], 'y': R['bone'][0]}
# Rows 0-2: the tarred lid's edge (lid sides, y 13-15); row 3: tar run down onto the top board; rows 3-15: three
# rough boards and a scuffed skid, framed by corner battens (cols 1-2, 13-14) nailed to every board.
CRATE_SIDE = """
tTtTUtTTtTtUtTtT
TuTTtTxTTtTTuTTt
ttztttttzttttztt
KtB6tt7656tt7tKk
K673576455767t7K
KN4434344434344K
K5522122122121BK
K6476576657657bK
KN5455445545453K
K4422121211212BK
K7576765766557bK
KN5445435445454K
K3412121221112BK
K5654656565645bK
KN3333333333333K
kkkkkkkkkkkkkkkk
"""


def crate_side(brace=True):
    image = grid(CRATE_SIDE, CRATE)
    if brace:  # a diagonal brace from bottom left to top right, nailed at both ends
        for i in range(10):
            x, y = 3 + i, 13 - i
            put(image, x, y, SP[5] if i % 3 else SP[6])
            put(image, x, y + 1, SP[1])
        put(image, 3, 13, R['iron'][1])
        put(image, 12, 4, R['iron'][1])
    return image


FISH = """
...www...w
.wwWWWw.ww
w.wWWWWwww
.wwWWWw.ww
...www...w
"""


def crate_side_marked():
    """The plain side with the Brotherhood's joke: a pale stencilled fish (the crate says salt fish)."""
    image = crate_side(brace=False)
    paint(FISH, {'w': R['calcite'][2], 'W': R['calcite'][3]}, base=image, x0=3, y0=6)
    for x, y in ((6, 8), (10, 12)):  # chipped paint
        put(image, x, y, SP[2])
    return image


# The front: a stove-in board (cols 6-11, rows 6-11 = x 4-10, y 4-10) with splintered edges round a dark hole.
HOLE = """
.7.67.
7kkkk6
kkkkkk
kkkkkk
6kkkk7
.6.7..
"""


def crate_front():
    image = crate_side(brace=False)
    paint(HOLE, CRATE, base=image, x0=6, y0=6)
    return image


CRATE_LID = """
tTtTUtTTtTtUtTtT
uxUTtTtuTtTUtTtu
TTtzTTttTTtzTTtT
tttttttttttttttt
TtTUtTTxTtTUtTtT
UTTtxuTTtTTtuTTU
tTzTTtTTtTzTTtTT
tttttttttttttttt
TtTUtTTtTtTxUtTT
TTuTtTtxTTtTTuTt
ttTztTttTzTTtzTT
tttttttttttttttt
TUtTtTxTTtTUtTtT
TtTuTTtTUTtTTxTt
tzTTtTTtzTTtTTtt
tttttttttttttttt
"""


def crate_lid():
    """Four tarred boards: black, with glossy runs of fresh tar."""
    return grid(CRATE_LID, CRATE)


def crate_rope():
    """Twisted hemp: diagonal strands in three tones."""
    image = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            put(image, x, y, R['rope'][(x + y) % 3 + 1] if (x + y) % 3 else R['rope'][1])
    return image


PURPLE = {'k': R['purple'][0], 'p': R['purple'][1], 'P': R['purple'][2], 'q': R['purple'][3], 'Q': R['purple'][4],
          'g': R['gold'][1], 'G': R['gold'][3]}
CARGO = """
.QQ.PGGPGgGg....
QPpQpggpqQqQ....
QpkQPGGPpPpP....
.QQ.pggpgGgG....
................
qQqQ............
PpPp............
pPpP............
G.gG............
................
................
................
................
................
................
................
"""
CARGO_UV = {'bolt_end': [0, 0, 4, 4], 'bolt_east': [4, 0, 6, 4], 'bolt_west': [6, 0, 8, 4], 'bolt_up': [8, 0, 12, 2],
            'bolt_down': [8, 2, 12, 4], 'drape': [0, 5, 4, 9]}


def crate_cargo():
    """A bolt of purple silk: its rolled end (layers wound round a dark core), its sides and top with the gold
    selvedge at the front, and the loose end that hangs from the hole with a ragged hem."""
    return grid(CARGO, PURPLE)


# == registry of textures ===================================================================================

def block_textures():
    out = {
        'sea_glass': sea_glass(), 'sea_glass_pane_top': sea_glass_pane_top(),
        'giant_clam_top': clam_top(), 'giant_clam_side': clam_side(), 'giant_clam_inner': clam_inner(),
        'giant_clam_flesh': clam_flesh(), 'giant_clam_pearl': clam_pearl(),
        'barnacles': barnacles(), 'barnacles_crust': barnacles_crust(),
        'tube_worms': tube_worms(), 'tube_worms_tube': tube_worms_tube(), 'tube_worms_plume': tube_worms_plume(),
        'signal_lamp_side': lamp_side(), 'signal_lamp_bezel': lamp_bezel(), 'signal_lamp_lens': lamp_lens(),
        'signal_lamp_top': lamp_top(), 'signal_lamp_stand': lamp_stand(), 'signal_lamp_parts': lamp_parts(),
        'contraband_crate_side': crate_side(), 'contraband_crate_marked': crate_side_marked(),
        'contraband_crate_front': crate_front(), 'contraband_crate_lid': crate_lid(),
        'contraband_crate_rope': crate_rope(), 'contraband_crate_cargo': crate_cargo(),
    }
    for key, image in out.items():
        soft_locked(image, key, GLASS_ALPHAS if key.startswith('sea_glass') else (0, 255))
    return out


# == models =================================================================================================

def M():
    return pixel.Model(NS, '')


def model_dict(m, particle, extra=None):
    out = m.json(particle)
    if extra:
        out.update(extra)
    return out


def flat(m):
    return {'textures': {k: v for k, v in m.textures.items()}, 'elements': m.elements}


# -- giant clam (built facing north: the lip at the front, z 2; the hinge at the back, z 14) -------------------

def clam(angle, pearl):
    m = M()
    side, top, inner, flesh = 'giant_clam_side', 'giant_clam_top', 'giant_clam_inner', 'giant_clam_flesh'
    # The lower valve: a rounded foot, the bowl of mantle, and the scalloped lip standing two texels proud of it.
    m.box([2, 0, 3], [14, 1, 13], {'down': top, '*': side}, skip=('up',))
    m.box([1, 1, 2], [15, 3, 14], {'up': flesh, '*': side}, skip=('down',))
    m.box([1, 3, 2], [15, 5, 3], {'north': side, 'south': inner, 'east': side, 'west': side}, only=('north', 'south', 'east', 'west'))
    m.box([1, 3, 13], [15, 5, 14], {'north': inner, 'south': side, 'east': side, 'west': side}, only=('north', 'south', 'east', 'west'))
    m.box([1, 3, 3], [2, 5, 13], {'west': side, 'east': inner}, only=('west', 'east'))
    m.box([14, 3, 3], [15, 5, 13], {'east': side, 'west': inner}, only=('west', 'east'))
    # The hinge ligament, dark and leathery, between the valves at the back.
    m.box([5, 4, 14], [11, 6, 15], inner, uv={f: [0, 0, 6 if f in ('north', 'south', 'up', 'down') else 1, 2 if f not in ('up', 'down') else 1]
                                             for f in pixel.FACES}, skip=('down', 'north'))
    # The lid, lifted about the hinge: ribbed crown above, mantle beneath (v flipped so its frill is at the lip).
    rot = ('x', angle, (8, 5, 14))
    m.box([1, 5, 2], [15, 7, 14], {'up': top, 'down': flesh, '*': side}, uv={'down': [1, 14, 15, 2]}, rot=rot)
    m.box([2, 7, 3], [14, 8, 13], {'up': top, '*': side}, skip=('down',), rot=rot)
    m.box([4, 8, 5], [12, 9, 12], {'up': top, '*': side}, skip=('down',), rot=rot)
    if pearl:  # a voxel pearl, four across, resting on the mantle near the lip
        for frm, to in (([7, 3, 5.5], [9, 7, 7.5]), ([6, 4, 5.5], [10, 6, 7.5]), ([7, 4, 4.5], [9, 6, 8.5])):
            m.box(frm, to, 'giant_clam_pearl', skip=('down',))
    return m


CLAM_DISPLAY = {
    'gui': {'rotation': [30, 225, 0], 'translation': [0, 1.5, 0], 'scale': [0.7, 0.7, 0.7]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.3, 0.3, 0.3]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, 1, 0], 'scale': [0.6, 0.6, 0.6]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, 1, 0], 'scale': [0.4, 0.4, 0.4]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, 1, 0], 'scale': [0.4, 0.4, 0.4]},
}


# -- tube worms ---------------------------------------------------------------------------------------------

def tube_worms_model():
    m = M()
    # The seagrass grid of four planes carrying the sprite.
    for frm, to, faces in (([0, 0, 4], [16, 16, 4], ('north', 'south')), ([12, 0, 0], [12, 16, 16], ('west', 'east')),
                           ([4, 0, 0], [4, 16, 16], ('west', 'east')), ([0, 0, 12], [16, 16, 12], ('north', 'south'))):
        m.box(frm, to, 'tube_worms', uv={f: [0, 0, 16, 16] for f in faces}, only=faces)
        m.elements[-1]['shade_direction_override'] = 'up'
    # Four solid tubes in the middle of the clump, each crowned with a red feathery tuft. No tube or tuft face
    # may lie in a sprite plane (4 or 12) or they would z-fight.
    for n, (x, z, h) in enumerate(((7, 7, 11), (9, 5, 8), (9, 9, 6), (5, 9, 4))):
        m.box([x, 0, z], [x + 2, h, z + 2], 'tube_worms_tube', skip=('down',), uv={'up': [0, 0, 2, 2]})
        side = PLUME_UV['side_a' if n % 2 == 0 else 'side_b']
        m.box([x - .5, h, z - .5], [x + 2.5, h + 3, z + 2.5], 'tube_worms_plume',
              uv={**{f: side for f in ('north', 'south', 'east', 'west')}, 'up': PLUME_UV['crown'], 'down': PLUME_UV['crown']})
    return m


# -- barnacles (built facing up: lying on the top of the block below) ------------------------------------------
# Little volcanoes: each a flared base under a narrower cone whose top is the mouth. Never more than 2 texels
# tall, so the crust stays a crust.
BIG = [(1, 1), (9, 9)]                                       # 5x5 base, 3x3 cone
MEDIUM = [(10, 2), (2, 10)]                                  # 4x4 base, 2x2 cone
LITTLE = [(6, 6)]                                            # a lone 3x3 cone
SMALL = [(7, 2), (13, 7), (0, 7), (14, 14), (7, 13), (12, 0)]  # 2x2 spat


def barnacles_model():
    m = M()
    t = 'barnacles'
    m.box([0, .25, 0], [16, .25, 16], 'barnacles_crust', uv={'up': [0, 0, 16, 16]}, only=('up',))

    def cone(x, z, size, y0, y1, side, top):
        uv = {f: list(BARN_UV[side]) for f in ('north', 'south', 'east', 'west')}
        uv['up'] = list(BARN_UV[top])
        m.box([x, y0, z], [x + size, y1, z + size], t, uv=uv, skip=('down',))

    for x, z in BIG:
        cone(x, z, 5, 0, 1, 'base', 'ring')
        cone(x + 1, z + 1, 3, 1, 2, 'cone', 'mouth')
    for x, z in MEDIUM:
        cone(x, z, 4, 0, 1, 'base', 'ring4')
        cone(x + 1, z + 1, 2, 1, 2, 'spat', 'spat_mouth')
    for x, z in LITTLE:
        cone(x, z, 3, 0, 1, 'cone_b', 'mouth')
    for x, z in SMALL:
        cone(x, z, 2, 0, 1, 'spat', 'spat_mouth')
    return m


# -- signal lamp (built facing north: the lens at the front) ----------------------------------------------------

def signal_lamp_model():
    m = M()
    P = 'signal_lamp_parts'

    def part(name):
        return list(PART[name])

    def all_faces(name, faces=('north', 'south', 'east', 'west', 'up', 'down')):
        return {f: part(name) for f in faces}
    # Cast-iron pedestal with a brass collar.
    m.box([3, 0, 3], [13, 1, 13], 'signal_lamp_stand')
    m.box([6, 1, 6], [10, 3, 10], 'signal_lamp_stand', skip=('up', 'down'))
    m.box([5, 3, 5], [11, 4, 11], 'signal_lamp_stand', skip=('up',))
    # The copper housing, banded in brass.
    m.box([3, 4, 3], [13, 14, 13], {'up': 'signal_lamp_top', 'down': 'signal_lamp_stand', '*': 'signal_lamp_side'})
    # The lens, set back half a texel inside a raised brass bezel; it glows.
    m.box([4, 5, 2.5], [12, 13, 2.5], 'signal_lamp_lens', only=('north',), light=15)
    m.box([3, 4, 2], [13, 14, 3], {'north': 'signal_lamp_bezel', '*': P},
          uv={'east': part('bezel_side'), 'west': part('bezel_side'), 'up': [0, 12, 10, 13], 'down': [0, 12, 10, 13]},
          skip=('south',))
    # The hood: a riveted visor over the lens, drooping at the front.
    m.box([2, 14, 0], [14, 15, 6], P, uv={'up': part('hood_up'), 'down': part('hood_down'), 'north': part('hood_front'),
                                          'south': part('hood_front'), 'east': part('hood_side'), 'west': part('hood_side')},
          rot=('x', -22.5, (8, 15, 6)))
    # Chimney with vent slits, a brass cap with its smoke hole, and a finial.
    m.box([6.5, 14, 7], [9.5, 16, 10], P, uv=all_faces('chimney'), only=('north', 'south', 'east', 'west'))
    m.box([6, 16, 6.5], [10, 17, 10.5], P, uv={**all_faces('cap_side'), 'up': part('cap_top')}, skip=('down',))
    # The shutter lever on the right-hand side: a brass boss, the rod and a dark wooden knob.
    m.box([13, 8, 7], [14, 10, 9], P, uv=all_faces('boss'), skip=('west',))
    m.box([14, 6, 7.5], [15, 11, 8.5], P, uv={**all_faces('lever'), 'up': [14, 4, 15, 5], 'down': [14, 8, 15, 9]}, skip=('west',))
    m.box([13.5, 11, 7], [15.5, 12, 9], P, uv=all_faces('knob'))
    return m


LAMP_DISPLAY = {
    'gui': {'rotation': [30, 225, 0], 'translation': [0, -1, 0], 'scale': [0.6, 0.6, 0.6]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.25, 0.25, 0.25]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, -0.5, 0], 'scale': [0.5, 0.5, 0.5]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, 0, 0], 'scale': [0.4, 0.4, 0.4]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, 0, 0], 'scale': [0.4, 0.4, 0.4]},
}


# -- contraband crate (built facing north: the stove-in board and the silk at the front) -------------------------

def contraband_crate_model():
    m = M()
    m.box([1, 0, 1], [15, 13, 15], {'north': 'contraband_crate_front', 'south': 'contraband_crate_side',
                                    'east': 'contraband_crate_marked', 'west': 'contraband_crate_marked',
                                    'up': 'contraband_crate_lid', 'down': 'mc:spruce_planks'})
    m.box([.5, 13, .5], [15.5, 15, 15.5], {'up': 'contraband_crate_lid', 'down': 'contraband_crate_lid', '*': 'contraband_crate_side'},
          uv={f: [0, 1, 15, 3] for f in ('north', 'south', 'east', 'west')})
    # Rope lashing: one turn front to back, one side to side, knotted where they cross on the lid.
    r = 'contraband_crate_rope'
    m.box([10, 0, .25], [12, 15.25, 15.75], r, only=('north', 'south', 'up', 'east', 'west'))
    m.box([.25, 0, 10], [15.75, 15.25, 12], r, only=('east', 'west', 'up', 'north', 'south'))
    m.box([9.5, 15.25, 9.5], [12.5, 16, 12.5], r, skip=('down',))
    # The bolt of silk poking out of the hole, its loose end hanging down the front.
    c = 'contraband_crate_cargo'
    m.box([5, 5, -1], [9, 9, 1], c, uv={'north': CARGO_UV['bolt_end'], 'east': CARGO_UV['bolt_east'], 'west': CARGO_UV['bolt_west'],
                                       'up': CARGO_UV['bolt_up'], 'down': CARGO_UV['bolt_down']}, skip=('south',))
    u1, v1, u2, v2 = CARGO_UV['drape']
    m.box([5, 1, -.75], [9, 5, -.75], c, uv={'north': [u1, v1, u2, v2], 'south': [u2, v1, u1, v2]}, only=('north', 'south'))
    return m


CRATE_DISPLAY = {
    'gui': {'rotation': [30, 225, 0], 'translation': [0, -0.5, 0], 'scale': [0.6, 0.6, 0.6]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.25, 0.25, 0.25]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.5, 0.5, 0.5]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, 0, 0], 'scale': [0.4, 0.4, 0.4]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, 0, 0], 'scale': [0.4, 0.4, 0.4]},
}


# == files ===================================================================================================

def ref(name):
    return f'{NS}:block/{name}'


def translucent(name):
    return {'sprite': ref(name), 'force_translucent': True}


def dump(data):
    return (json.dumps(data, indent=2) + '\n').encode()


def models():
    """block model name -> model JSON."""
    out = {}
    for pearl in (True, False):
        name = 'giant_clam_pearl' if pearl else 'giant_clam'
        out[name] = model_dict(clam(22.5, pearl), 'giant_clam_top')
    out['tube_worms'] = model_dict(tube_worms_model(), 'tube_worms', {'ambientocclusion': False})
    out['barnacles'] = model_dict(barnacles_model(), 'barnacles', {'ambientocclusion': False})
    out['sea_glass'] = {'parent': 'minecraft:block/cube_all', 'textures': {'all': translucent('sea_glass')}}
    for part in ('post', 'side', 'side_alt', 'noside', 'noside_alt'):
        out[f'sea_glass_pane_{part}'] = {'parent': f'minecraft:block/template_glass_pane_{part}',
                                         'textures': {'edge': translucent('sea_glass_pane_top'), 'pane': translucent('sea_glass')}}
    out['signal_lamp'] = model_dict(signal_lamp_model(), 'signal_lamp_side')
    out['contraband_crate'] = model_dict(contraband_crate_model(), 'contraband_crate_side')
    out['haunt'] = {'textures': {'particle': 'minecraft:item/structure_void'}}
    return out


def blockstates():
    def facing4(model):
        return {'variants': {f'facing={f}': {'model': ref(model), **({'y': y} if y else {})} for f, y in FACINGS}}
    out = {}
    out['giant_clam'] = {'variants': {f'facing={f},pearl={str(p).lower()}': {'model': ref('giant_clam_pearl' if p else 'giant_clam'), **({'y': y} if y else {})}
                                      for f, y in FACINGS for p in (True, False)}}
    out['tube_worms'] = {'variants': {'': [{'model': ref('tube_worms'), **({'y': y} if y else {})} for y in (0, 90, 180, 270)]}}
    rot = {'up': {}, 'down': {'x': 180}, 'north': {'x': 90}, 'south': {'x': 90, 'y': 180}, 'east': {'x': 90, 'y': 90},
           'west': {'x': 90, 'y': 270}}
    out['barnacles'] = {'variants': {}}
    for f, r in rot.items():
        if f in ('up', 'down'):  # lying flat they can be turned freely for variety
            out['barnacles']['variants'][f'facing={f}'] = [{'model': ref('barnacles'), **r, **({'y': y} if y else {})} for y in (0, 90, 180, 270)]
        else:
            out['barnacles']['variants'][f'facing={f}'] = {'model': ref('barnacles'), **r}
    out['sea_glass'] = {'variants': {'': {'model': ref('sea_glass')}}}
    pane = lambda part: ref(f'sea_glass_pane_{part}')  # noqa: E731
    out['sea_glass_pane'] = {'multipart': [
        {'apply': {'model': pane('post')}},
        {'apply': {'model': pane('side')}, 'when': {'north': 'true'}},
        {'apply': {'model': pane('side'), 'y': 90}, 'when': {'east': 'true'}},
        {'apply': {'model': pane('side_alt')}, 'when': {'south': 'true'}},
        {'apply': {'model': pane('side_alt'), 'y': 90}, 'when': {'west': 'true'}},
        {'apply': {'model': pane('noside')}, 'when': {'north': 'false'}},
        {'apply': {'model': pane('noside_alt')}, 'when': {'east': 'false'}},
        {'apply': {'model': pane('noside_alt'), 'y': 90}, 'when': {'south': 'false'}},
        {'apply': {'model': pane('noside'), 'y': 270}, 'when': {'west': 'false'}},
    ]}
    out['signal_lamp'] = facing4('signal_lamp')
    out['contraband_crate'] = facing4('contraband_crate')
    out['haunt'] = {'variants': {'': {'model': ref('haunt')}}}
    return out


def item_models():
    """item model name -> JSON (models/item)."""
    gen = lambda layer: {'parent': 'minecraft:item/generated', 'textures': {'layer0': layer}}  # noqa: E731
    closed = clam(18, True)
    out = {
        'giant_clam': {**model_dict(closed, 'giant_clam_top'), 'display': CLAM_DISPLAY},
        'tube_worms': gen(f'{NS}:item/tube_worms'),
        'barnacles': gen(f'{NS}:item/barnacles'),
        'sea_glass_pane': gen(ref('sea_glass')),
        'signal_lamp': {'parent': ref('signal_lamp'), 'display': LAMP_DISPLAY},
        'contraband_crate': {'parent': ref('contraband_crate'), 'display': CRATE_DISPLAY},
    }
    for name in ocean_items.SPRITES:
        out[name] = gen(f'{NS}:item/{name}')
    return out


def item_definitions():
    out = {name: {'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{name}'}} for name in item_models()}
    out['sea_glass'] = {'model': {'type': 'minecraft:model', 'model': ref('sea_glass')}}
    return out


def outputs():
    """Every generated file: path -> bytes."""
    files = {}
    for key, image in block_textures().items():
        files[ASSETS / f'textures/block/{key}.png'] = png(image)
    for key, image in ocean_items.sprites().items():
        files[ASSETS / f'textures/item/{key}.png'] = png(image)
    files[ASSETS / 'textures/entity/equipment/humanoid/diving_helmet.png'] = png(ocean_items.helmet_layer())
    files[ASSETS / 'equipment/diving_helmet.json'] = dump({'layers': {'humanoid': [{'texture': f'{NS}:diving_helmet'}]}})
    for name, data in models().items():
        files[ASSETS / f'models/block/{name}.json'] = dump(data)
    for name, data in blockstates().items():
        files[ASSETS / f'blockstates/{name}.json'] = dump(data)
    for name, data in item_models().items():
        files[ASSETS / f'models/item/{name}.json'] = dump(data)
    for name, data in item_definitions().items():
        files[ASSETS / f'items/{name}.json'] = dump(data)
    return files


def write():
    for path, data in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print('wrote', path.relative_to(pixel.PROJECT).as_posix())


def check():
    for name, data in {**models(), **item_models()}.items():
        for e in data.get('elements', []):
            for face in e['faces'].values():
                assert all(0 <= c <= 16 for c in face['uv']), (name, e['from'], face)
            assert all(-16 <= c <= 32 for c in e['from'] + e['to']), (name, e)
    crlf, lf = (chr(13) + chr(10)).encode(), chr(10).encode()

    def current(p):
        data = p.read_bytes()
        return data.replace(crlf, lf) if p.suffix == '.json' else data
    bad = [p for p, data in outputs().items() if not p.exists() or current(p) != data]
    if bad:
        print('Out of date (rerun tools/art/blocks.py):')
        for p in bad:
            print('  ' + p.relative_to(pixel.PROJECT).as_posix())
        sys.exit(1)
    print('Ocean Expansion block and item assets are up to date.')


# == preview ==================================================================================================

def loader():
    ours = {ref(k): v for k, v in block_textures().items()}
    ours.update({f'{NS}:item/{k}': v for k, v in ocean_items.sprites().items()})

    def load(r):
        return ours[r] if r in ours else pixel.vanilla_texture(r)
    return load


def as_model(data):
    """A written model JSON -> {'textures', 'elements'} with vanilla parents resolved."""
    if 'elements' in data or 'parent' not in data:
        return {'textures': data['textures'], 'elements': data.get('elements', [])}
    parent = pixel.vanilla_model(data['parent'])
    return {'textures': {**parent['textures'], **data['textures']}, 'elements': parent['elements']}


def vanilla(name):
    return pixel.vanilla_model(f'minecraft:block/{name}')


def preview(dest):
    load = loader()
    vload = pixel.vanilla_texture
    mods = {k: as_model(v) for k, v in models().items()}
    items = {k: v for k, v in item_models().items()}
    sand, stone, planks = vanilla('sand'), vanilla('stone'), vanilla('spruce_planks')
    T = 360

    def tile(parts, scale=9, view='front_right'):
        """Renders big, crops to the drawing and centres it in a T x T tile (shrinking the scale until it fits)."""
        while True:
            image = render_scene(parts, scale=scale, view=view, canvas=(3 * T, 3 * T), origin=(1.5 * T, 1.5 * T))
            box = image.getbbox()
            if box is None:
                return Image.new('RGBA', (T, T))
            w, h = box[2] - box[0], box[3] - box[1]
            if (w <= T - 8 and h <= T - 8) or scale <= 2:
                out = Image.new('RGBA', (T, T))
                out.alpha_composite(image.crop(box), ((T - w) // 2, (T - h) // 2))
                return out
            scale -= 1

    def ours(name, rot=(0, 0), off=(0, 0, 0)):
        return (mods[name], load, rot, off)

    def van(model, off):
        return (model, vload, (0, 0), off)
    tiles = []
    floor = [van(sand, (x, -1, z)) for x in (-1, 0, 1) for z in (-1, 0, 1)]
    tiles.append(('giant clam, pearl (N, E)', tile(floor + [ours('giant_clam_pearl'), ours('giant_clam_pearl', (0, 90), (1, 0, 1))], 7)))
    tiles.append(('giant clam, empty (S, W)', tile(floor + [ours('giant_clam', (0, 180)), ours('giant_clam', (0, 270), (-1, 0, 1))], 7)))
    tiles.append(('clam from the front, eye level', tile([van(sand, (0, -1, 0)), ours('giant_clam_pearl')], 16, 'front')))
    tiles.append(('clam item model (18 deg)', tile([(as_model(items['giant_clam']), load, (0, 0), (0, 0, 0))], 16)))
    basalt = vanilla('magma_block')
    tiles.append(('tube worms on magma and stone', tile([van(basalt, (0, -1, 0)), van(stone, (1, -1, 0)), van(stone, (0, -1, 1)),
                                                         ours('tube_worms'), ours('tube_worms', (0, 90), (1, 0, 0)), ours('tube_worms', (0, 180), (0, 0, 1))], 9)))
    tiles.append(('tube worms close', tile([van(stone, (0, -1, 0)), ours('tube_worms')], 16, 'front')))
    wall = [van(planks, (0, 0, 0)), van(planks, (0, 1, 0))] + [van(stone, (x, -1, z)) for x in (0, 1) for z in (-1, 0)]
    barn = [ours('barnacles', (90, 0), (0, 0, -1)), ours('barnacles', (90, 0), (0, 1, -1)), ours('barnacles', (0, 0), (0, 2, 0)),
            ours('barnacles', (90, 90), (1, 0, 0)), ours('barnacles', (90, 90), (1, 1, 0)), ours('barnacles', (0, 0), (1, 0, -1))]
    tiles.append(('barnacles: north + east faces, top, floor', tile(wall + barn, 8)))
    tiles.append(('barnacles close (up)', tile([van(stone, (0, -1, 0)), ours('barnacles')], 16)))
    gl = [ours('sea_glass', off=(0, 0, 0)), ours('sea_glass', off=(0, 1, 0)), ours('sea_glass', off=(1, 0, 0))]
    tiles.append(('sea glass by vanilla glass', tile([van(vanilla('glass'), (-1, 0, 0)), van(vanilla('glass'), (-1, 1, 0)), van(stone, (0, 0, 1)),
                                                      van(stone, (1, 0, 1)), van(stone, (0, 1, 1))] + gl, 9)))

    def pane(n, e, s, w, off):
        parts = [ours('sea_glass_pane_post', off=off)]
        for flag, name, rot in ((n, 'side', 0), (e, 'side', 90), (s, 'side_alt', 0), (w, 'side_alt', 90)):
            if flag:
                parts.append(ours(f'sea_glass_pane_{name}', (0, rot), off))
        for flag, name, rot in ((n, 'noside', 0), (e, 'noside_alt', 0), (s, 'noside_alt', 90), (w, 'noside', 270)):
            if not flag:
                parts.append(ours(f'sea_glass_pane_{name}', (0, rot), off))
        return parts
    panes = pane(0, 1, 0, 0, (-1, 0, 0)) + pane(0, 1, 0, 1, (0, 0, 0)) + pane(0, 0, 1, 1, (1, 0, 0)) + pane(1, 0, 0, 0, (1, 0, 1))
    panes += pane(0, 1, 0, 0, (-1, 1, 0)) + pane(0, 1, 0, 1, (0, 1, 0)) + pane(0, 0, 1, 1, (1, 1, 0)) + pane(1, 0, 0, 0, (1, 1, 1))
    tiles.append(('sea glass panes', tile([van(stone, (x, -1, z)) for x in (-1, 0, 1) for z in (0, 1)] + panes, 8)))
    lamp = mods['signal_lamp']
    tiles.append(('signal lamp', tile([van(planks, (0, -1, 0)), ours('signal_lamp')], 15)))
    tiles.append(('signal lamp front left / back', tile([van(planks, (0, -1, 0)), ours('signal_lamp')], 15, 'front_left')))
    tiles.append(('signal lamp, eye level', tile([van(planks, (0, -1, 0)), ours('signal_lamp')], 15, 'front')))
    tiles.append(('signal lamp, back right', tile([van(planks, (0, -1, 0)), ours('signal_lamp')], 15, 'back_right')))
    tiles.append(('contraband crate', tile([van(planks, (0, -1, 0)), ours('contraband_crate')], 15)))
    tiles.append(('crate front left', tile([van(planks, (0, -1, 0)), ours('contraband_crate')], 15, 'front_left')))
    tiles.append(('crate back right', tile([van(planks, (0, -1, 0)), ours('contraband_crate')], 15, 'back_right')))
    tiles.append(('crate + lamp + vanilla barrel/smoker', tile([van(vanilla('barrel'), (-1, 0, 0)), ours('contraband_crate'), ours('signal_lamp', off=(1, 0, 0)),
                                                                 van(vanilla('smoker'), (1, 0, 1)), van(planks, (-1, -1, 0)), van(planks, (0, -1, 0)), van(planks, (1, -1, 0))], 8)))
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    extra = 560
    sheet = Image.new('RGBA', (cols * T, rows * (T + 18) + extra), '#7D8C99')
    draw = ImageDraw.Draw(sheet)
    for n, (label, image) in enumerate(tiles):
        x, y = (n % cols) * T, (n // cols) * (T + 18)
        sheet.alpha_composite(image, (x, y + 18))
        draw.text((x + 6, y + 4), label, fill='#101820')
    # Bottom band: inventory slots (GUI scale 4) for every item, the helmet worn, textures at 4x.
    y0 = rows * (T + 18) + 8
    draw.text((8, y0), 'inventory slots, GUI scale 4', fill='#101820')
    x = 8
    for name, data in item_models().items():
        if data.get('parent') == 'minecraft:item/generated':
            layer = data['textures']['layer0']
            pic = slot(load(layer))
        else:
            mdl = as_model(data) if 'elements' in data else as_model(models()[data['parent'].split('/')[-1]])
            disp = data.get('display', {})
            pic = slot(gui_block(mdl, load, disp))
        sheet.alpha_composite(pic, (x, y0 + 14))
        draw.text((x, y0 + 86), name[:12], fill='#101820')
        x += 76
    pic = slot(gui_block(mods['sea_glass'], load, {}))
    sheet.alpha_composite(pic, (x, y0 + 14))
    draw.text((x, y0 + 86), 'sea_glass', fill='#101820')
    x += 76
    for view in ('front_right', 'front_left', 'back_right'):
        sheet.alpha_composite(ocean_items.helmet_preview(view), (x, y0 + 4))
        x += 150
    # Item sprites at 8x.
    y1 = y0 + 110
    x = 8
    for name, image in ocean_items.sprites().items():
        sheet.alpha_composite(image.resize((128, 128), Image.NEAREST), (x, y1 + 14))
        draw.text((x, y1), name, fill='#101820')
        x += 136
    big = ocean_items.helmet_layer().crop((0, 0, 32, 16)).resize((256, 128), Image.NEAREST)
    sheet.alpha_composite(big, (x + 10, y1 + 14))
    draw.text((x + 10, y1), 'helmet layer (head box, 8x)', fill='#101820')
    # Block textures at 4x.
    y2 = y1 + 160
    x = 8
    for n, (key, image) in enumerate(block_textures().items()):
        xx, yy = 8 + (n % 24) * 76, y2 + (n // 24) * 90
        back = Image.new('RGBA', (64, 64), '#3A4652')
        back.alpha_composite(image.resize((64, 64), Image.NEAREST))
        sheet.alpha_composite(back, (xx, yy + 14))
        draw.text((xx, yy), key.replace('contraband_', 'cc_').replace('signal_lamp', 'lamp')[:13], fill='#101820')
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(dest)
    print('preview', dest)


if __name__ == '__main__':
    if '--preview' in sys.argv:
        preview(sys.argv[sys.argv.index('--preview') + 1])
    elif '--check' in sys.argv:
        check()
    else:
        write()
