"""Ocean Expansion item sprites (16x16, palette-locked) and the diving helmet's worn layer (64x32).

Used by tools/art/blocks.py, which writes them; run that script, not this one.
  SPRITES: the items' own sprites (pearl, black_pearl, ambergris, storm_glass, diving_helmet);
  BLOCK_SPRITES: flat inventory sprites for block items (tube_worms, barnacles).
"""
import io
import math

from PIL import Image

import pixel
from pixel import RAMPS as R
from ocean_paint import paint, put, ball, soft_locked, render_scene

SPRITES = ('pearl', 'black_pearl', 'ambergris', 'storm_glass', 'diving_helmet')
BLOCK_SPRITES = ('tube_worms', 'barnacles')


def blank():
    return Image.new('RGBA', (16, 16))


def grid(pattern, palette, w=16, h=16):
    rows = [r.replace(' ', '') for r in pattern.strip('\n').splitlines()]
    assert len(rows) == h and all(len(r) == w for r in rows), [(i, len(r)) for i, r in enumerate(rows)]
    return paint(pattern, palette, (w, h))


def twinkle(image, x, y, c=None, arm=R['nacre'][5]):
    """A tiny four-point glint centred on (x, y)."""
    put(image, x, y, c or R['calcite'][5])
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(image, x + dx, y + dy, arm)
    return image


# -- pearls -------------------------------------------------------------------------------------------------

def pearl():
    """A lustrous white pearl: lilac shadow, pink reflected light on the lower right, a hot white highlight."""
    image = blank()
    tones = R['nacre'][1:]
    ball(image, 7.5, 8.5, 5.2, tones, outline=R['nacre'][0], spec=R['calcite'][5], rim=(R['pink'][5], .45))
    twinkle(image, 12, 3)
    return image


def black_pearl():
    """A Tahitian black pearl: near-black body, a violet sheen across the lit side, a peacock-green rim below."""
    image = blank()
    tones = [R['obsidian'][2], R['obsidian'][3], R['obsidian'][4], R['amethyst'][0], R['amethyst'][1], R['amethyst'][2]]
    ball(image, 7.5, 8.5, 5.2, tones, outline=R['obsidian'][1], spec=R['amethyst'][5], rim=(R['ender'][3], .68))
    twinkle(image, 12, 3, R['amethyst'][6], R['amethyst'][3])
    return image


# -- ambergris ----------------------------------------------------------------------------------------------
AMBER = {'k': R['dripstone'][0], 'K': R['membrane'][2], 'g': R['membrane'][3], 'G': R['membrane'][5],
         'h': R['membrane'][6], 'H': R['membrane'][7], 'w': R['membrane'][8], 'a': R['gold'][0], 'A': R['gold'][1],
         'y': R['gold'][2], 'd': R['dripstone'][2]}
AMBERGRIS = """
................
................
................
.......kkkk.....
.....kkHwwHk....
....kHwwHHhGk...
...kHwHhhahGk...
..kHwhhGaAahGk..
.kHwhGhhGahGGkk.
.kHhGGhGGGgGHwk.
.khGgGaGGgGhwHk.
.kgGgAyaggGhHgk.
..kgKgaAgKgGgk..
...kkgKggkgKkk..
.....kkkkkkk....
................
"""


def ambergris():
    """A waxy lump of ambergris, grey and greasy, marbled with old amber."""
    return grid(AMBERGRIS, AMBER)


# -- storm glass ----------------------------------------------------------------------------------------------
STORM = {'o': R['bottle'][0], 'B': R['bottle'][2], 'W': R['bottle'][3],
         'l': R['glass'][1], 'L': R['glass'][2], 'c': R['calcite'][5], 'C': R['calcite'][3], 'v': R['calcite'][1],
         'a': R['gold'][0], 'b': R['gold'][1], 'c': R['calcite'][5], 'd': R['gold'][3]}
# 'c' is crystal white; the cap uses a/b/d (dark, mid, lit brass).
STORM_GLASS = """
.......aa.......
......a..a......
......bddb......
.....bcddcb.....
.....abbbba.....
......oWLo......
.....oWlLLo.....
....oWlLlLLo....
....oWlclLLo....
....oBlLlcLo....
....oBclCLlo....
....oBlcCcLo....
....oBCcCcCo....
....oCcCvCco....
.....abbbba.....
......aaaa......
"""


def storm_glass():
    """A sealed weather glass: a brass-capped vial of clear spirit with fern-like crystals growing in it."""
    image = grid(STORM_GLASS, STORM)
    return image


# -- diving helmet ------------------------------------------------------------------------------------------
CU = R['copper_block']
BRASS = R['gold']


def diving_helmet():
    """Wexley's copper helmet: a riveted dome, a round brass-ringed faceplate with a glint, side ports and
    a bolted breastplate collar."""
    image = blank()
    ball(image, 8, 7.5, 6.3, CU[1:], outline=R['bricks'][0], spec=R['copper'][5], light=(-.6, -.7, .5))
    # Breastplate collar.
    for y, (x0, x1) in ((12, (2, 13)), (13, (1, 14)), (14, (1, 14))):
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y == 14
            put(image, x, y, R['bricks'][0] if edge else (CU[3] if y == 13 else CU[5]))
    for x in (3, 6, 9, 12):
        put(image, x, 13, BRASS[3])
    # The faceplate: a brass ring round a dark sea-green window with a glint.
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + .5 - 8, y + .5 - 8)
            if d < 2.6:
                put(image, x, y, R['heart'][2] if (x + y) % 2 else R['heart'][1])
            elif d < 3.7:
                put(image, x, y, BRASS[3] if (x + .5 - 8) + (y + .5 - 8) < 0 else BRASS[1])
    for x, y, c in ((7, 6, R['glass'][3]), (6, 7, R['glass'][2]), (9, 9, R['heart'][4])):
        put(image, x, y, c)
    for x, y in ((8, 4), (4, 8), (11, 8), (8, 11)):
        put(image, x, y, BRASS[5])
    # Side ports, a valve on the crown.
    for x in (2, 13):
        put(image, x, 7, R['heart'][3])
        put(image, x, 8, R['heart'][1])
    put(image, 7, 1, BRASS[2])
    put(image, 8, 1, BRASS[1])
    put(image, 7, 0, BRASS[4])
    put(image, 8, 0, BRASS[2])
    return image


# -- block item sprites ---------------------------------------------------------------------------------------
WORM = {'W': R['calcite'][4], 'w': R['bone'][2], 'v': R['calcite'][1], 's': R['tuff'][4], 'o': R['tuff'][0],
        'k': R['fire_coral'][0], 'r': R['fire_coral'][1], 'R': R['fire_coral'][2], 'L': R['fire_coral'][3],
        'p': R['pink'][4], 'g': R['tuff'][2], 'G': R['tuff'][3], 'd': R['tuff'][1]}
TUBE_WORMS = """
.....L.p.L......
....RLRLRLR.....
.L.p.rRkRr.p.L..
RLRLR.rkr.LRLRL.
.rRkRr.Ww.rRkRr.
..rkr..wv..rkr..
...Ww..Wv...Ww..
...wv..ws...wv..
.L.Wv..Wv...Wv..
RLRwv..wv...ws..
.rkWv..Ws...Wv..
..Wws..Wv.p.wv..
..wvv..wvRrRWv..
..Wvv..WvrkrWv..
.dGWvgdWvgWvWvd.
dgGGgGGgGGgGGGgd
"""
BARNACLES = """
................
................
................
................
................
................
.......kn.......
......wWWv..kn..
..kn.wWWWWvwWWv.
.wWWvwWWWWswWWWv
.wWWswWWWWsvWWWs
wWWWWswWWswwWWWs
vwWWsvvwssvvwWss
GgsssGGggGGgsssG
dGGgGGdGGgGdGGgd
.dddddddddddddd.
"""
BARN = {'W': R['calcite'][4], 'w': R['calcite'][2], 'v': R['calcite'][1], 's': R['tuff'][4], 'k': R['tuff'][0],
        'n': R['sand'][0], 'g': R['tuff'][2], 'G': R['tuff'][3], 'd': R['tuff'][1]}


def tube_worms_item():
    return grid(TUBE_WORMS, WORM)


def barnacles_item():
    return grid(BARNACLES, BARN)


def sprites():
    out = {'pearl': pearl(), 'black_pearl': black_pearl(), 'ambergris': ambergris(), 'storm_glass': storm_glass(),
           'diving_helmet': diving_helmet(), 'tube_worms': tube_worms_item(), 'barnacles': barnacles_item()}
    for key, image in out.items():
        soft_locked(image, key)
    return out


# -- the worn helmet (equipment layer) -------------------------------------------------------------------------
# Head box, 8x8x8 at (0, 0): top (8-15, 0-7), right side (0-7, 8-15), front (8-15, 8-15), left side (16-23, 8-15),
# back (24-31, 8-15); the bottom (16-23, 0-7) stays open. Row 7 of every side is the bolted collar.
HELM = {'1': CU[0], '2': CU[1], '3': CU[2], '4': CU[3], '5': CU[4], '6': CU[5], '7': CU[6], '8': CU[7],
        'a': BRASS[0], 'b': BRASS[1], 'c': BRASS[2], 'd': BRASS[3], 'e': BRASS[4], 'f': BRASS[5],
        'g': R['glass'][3], 'G': R['glass'][2], 'k': R['heart'][1], 'K': R['heart'][0], 'x': R['iron'][0]}
HELM_TOP = """
45677654
56788765
67888876
678dd876
678dd876
67888876
56788765
45677654
"""
HELM_FRONT = """
56788765
5abccba5
5bg..Gb5
5c....c5
5c....c5
5bG...b5
4abccba4
3e3ee3e3
"""
HELM_SIDE = """
56788765
45677654
4abbbba4
4bkkkkb4
4abbbba4
4bkkkkb4
3abbbba3
2e2ee2e2
"""
HELM_BACK = """
56788765
45677654
456ab654
45bxxb54
45bxxb54
456ab654
34444443
2e2ee2e2
"""


def helmet_layer():
    image = Image.new('RGBA', (64, 32))
    paint(HELM_TOP, HELM, base=image, x0=8, y0=0)
    paint(HELM_SIDE, HELM, base=image, x0=0, y0=8)
    paint(HELM_FRONT, HELM, base=image, x0=8, y0=8)
    side = '\n'.join(r[::-1] for r in HELM_SIDE.strip('\n').splitlines())
    paint(side, HELM, base=image, x0=16, y0=8)
    paint(HELM_BACK, HELM, base=image, x0=24, y0=8)
    return soft_locked(image, 'diving_helmet layer')


def helmet_preview(view='front_right', size=140):
    """Steve's head wearing the helmet (inflated by 1 like vanilla's helmet layer), for the preview sheet."""
    skin = Image.open(io.BytesIO(pixel.vanilla_bytes('textures/entity/player/wide/steve.png'))).convert('RGBA')
    layer = helmet_layer()

    def head(frm, to, tex):
        uv = {'up': [2, 0, 4, 2], 'east': [0, 2, 2, 4], 'north': [2, 2, 4, 4], 'west': [4, 2, 6, 4], 'south': [6, 2, 8, 4]}
        return {'from': frm, 'to': to, 'faces': {f: {'uv': u, 'texture': '#' + tex} for f, u in uv.items()}}
    model = {'textures': {'skin': 'x:skin', 'helm': 'x:helm'},
             'elements': [head([4, 4, 4], [12, 12, 12], 'skin'), head([3, 3, 3], [13, 13, 13], 'helm')]}
    load = {'x:skin': skin, 'x:helm': layer}.__getitem__
    return render_scene([(model, load, (0, 0), (0, 0, 0))], scale=9, view=view, canvas=(size, size), origin=(size / 2, size / 2))
