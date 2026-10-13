# WORKED EXAMPLE from an older mod (Cave Expansion): shows how a workstation is painted and modelled. Do not run it here.
"""The Prospecting Table: job site of the Delvers' Guild miner (caveexpansion:prospecting_table).

A sturdy spruce work table with an iron-bound stone top. On top: a sieve tray of ore chunks, a hand lens,
a small pick and a tiny miner's lantern. Under the top: sorting bins of coal, copper and raw iron, and an
ore crate on the bottom shelf. Wood, bark and planks come from vanilla textures by id; everything with
character is hand-painted here from palette-locked ramps (pixel.RAMPS). One texel is always 1/16 block.

    python tools/art/prospecting_table.py                    # write textures, models, blockstate, item files
    python tools/art/prospecting_table.py --check            # verify the written files match this script
    python tools/art/prospecting_table.py --preview out.png  # isometric sheet next to vanilla workstations

Never hand-edit the outputs; change this script and rerun.
"""
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixel  # noqa: E402
from pixel import RAMPS, raster, stamp, locked  # noqa: E402

NS = 'caveexpansion'
NAME = 'prospecting_table'
ASSETS = pixel.PROJECT / f'src/main/resources/assets/{NS}'

R = RAMPS
WOOD = {str(i + 1): c for i, c in enumerate(R['spruce'])}            # '1' darkest .. '7' lightest
BARK = {'k': R['bark'][0], 'K': R['bark'][1], 'B': R['bark'][2], 'b': R['bark'][3]}
IRON = {'i': R['iron'][0], 'I': R['iron'][1], 'J': R['iron'][3], 'r': R['steel'][3], 'R': R['steel'][4]}
STONE = {'s': R['stone'][0], 't': R['stone'][1], 'u': R['stone'][2], 'v': R['stone'][3],
         'w': R['stone'][4], 'x': R['stone'][5], 'y': R['stone'][6]}

# -- textures ----------------------------------------------------------------------------------------

TOP = """
yyyyyyyyyyyyyyyx
yxxwxxxxxxwxxxxv
yxxxxxwxxxxxxwxv
ywxxxxxxxxxxxxxv
yxxxxxxxxwxxxxxv
yxxxwxxxxxxxxxxv
yxxxxxxxxxxxwxxv
vvvvvvvvvvvvvvvu
yyyyyyyyyyyyyyyx
yxxxxwxxxxxxxxxv
yxwxxxxxxxxwxxxv
yxxxxxxxxxxxxxxv
yxxxxxxwxxxxxxxv
ywxxxxxxxxxxwxxv
yxxxxxxxxxxxxxxv
vuuuuuuuuuuuuuuu
"""
BRACKET = """
JJJJI
JRIIi
JIi..
JI...
Ii...
"""


def top():
    """Two polished stone slabs, bound at the corners with riveted iron brackets."""
    image = raster(TOP, STONE)
    for fx in (False, True):
        for fy in (False, True):
            stamp(image, BRACKET, IRON, 11 if fx else 0, 11 if fy else 0, flip_x=fx, flip_y=fy)
    return image


SIDE = """
JIyyyyyyyyyyyyJI
JRxxwxxxxxxwxxJR
JIxwxxxxxwxxxxJI
IiIIIIIIIIIIIIIi
kBK7676776767BKk
kbKi54554455ibKk
kBk4545534544BKk
kBK2121221212BKk
kBK6776767767bKk
kbKi55445545iBkk
kBK5434554453BKk
kBk2121212211BKk
kBK7677676776BKk
kbKi54554455ibKk
kBK4553445545BKk
kKk1111111111KKk
"""


def side():
    """Rows 0-3: the stone top's edge with its iron strap. Rows 4-15: the body, boards between bark posts.
    Auto UVs put y 12..16 on rows 0-3 and y 0..12 on rows 4-15, so one texture dresses every side."""
    return raster(SIDE, {**STONE, **IRON, **BARK, **WOOD})


# Pebble lumps, tones 0 (gaps) to 3 (lit top-left), palette-swapped per ore.
LUMPS = """
32132210
22122110
11011103
03221032
32211021
21110321
10032210
03221110
"""
ORES = {
    'coal': [R['coal'][0], R['coal'][2], R['coal'][4], R['coal'][5]],
    'copper': [R['copper'][0], R['copper'][1], R['copper'][3], R['copper'][5]],
    'iron': [R['raw_iron'][1], R['raw_iron'][3], R['raw_iron'][4], R['raw_iron'][6]],
    'gold': [R['gold'][0], R['gold'][2], R['gold'][3], R['gold'][5]],
}
ORE_AT = {'coal': (0, 0), 'copper': (8, 0), 'iron': (0, 8), 'gold': (8, 8)}


def ore():
    """Four 8x8 heaps of raw ore: coal, copper (with a little verdigris), raw iron, gold."""
    image = Image.new('RGBA', (16, 16))
    rows = LUMPS.strip().splitlines()
    for kind, (ox, oy) in ORE_AT.items():
        for y, row in enumerate(rows):
            for x, tone in enumerate(row.strip()):
                image.putpixel((ox + x, oy + y), pixel.rgb(ORES[kind][int(tone)]))
    for x, y in ((10, 2), (13, 5), (9, 6)):
        image.putpixel((x, y), pixel.rgb(R['copper'][7] if x != 13 else R['copper'][6]))
    return image


PARTS = """
JJoJJJJJI...IJJI
JkJkEkJ.I...JMnI
JcJJJJ......JmNI
JkJYJk......JLMI
JJJJoJ......iIIi
EkJkJk......JJJI
qPqqPqqPqqJIJiiI
pQppQppQpp..JiiI
J7677676J...IIIi
3i54545i3.yYy...
J2121212JyAaHb..
.........YaHhb..
.........yHhhb..
..........bbb5..
CcOoEeZY.....65.
ccodeDYg......64
"""


def parts():
    """A small atlas of pieces, each used with explicit UVs (see PART)."""
    palette = {**IRON, **WOOD, 'k': R['bark'][0],
               'c': R['coal'][1], 'C': R['coal'][4], 'o': R['copper'][2], 'O': R['copper'][4], 'd': R['copper'][0],
               'e': R['raw_iron'][3], 'E': R['raw_iron'][4], 'D': R['raw_iron'][1],
               'Y': R['gold'][3], 'Z': R['gold'][5], 'g': R['gold'][1], 'y': R['gold'][1], 'b': R['gold'][0],
               'A': R['glass'][3], 'a': R['glass'][1], 'H': R['glass'][2], 'h': R['glass'][0],
               'L': R['flame'][2], 'm': R['flame'][3], 'M': R['flame'][4], 'n': R['flame'][5], 'N': R['flame'][6],
               'p': R['pale'][1], 'P': R['pale'][3], 'q': R['pale'][5], 'Q': R['pale'][0],
               'S': R['steel'][2], 't': R['steel'][3], 'T': R['steel'][4]}
    return raster(PARTS, palette)


# Explicit UV rectangles in the parts atlas.
PART = {
    'mesh': [0, 0, 6, 6], 'lens': [9, 9, 16, 16], 'lamp_side': [12, 0, 16, 5], 'lamp_top': [12, 5, 16, 9],
    'bin_board': [0, 6, 10, 8], 'crate': [0, 8, 9, 11], 'cap': [10, 6, 12, 7], 'loop': [6, 0, 9, 2],
    'coal': [0, 14, 2, 16], 'copper': [2, 14, 4, 16], 'iron': [4, 14, 6, 16], 'gold': [6, 14, 8, 16],
}

PICK = """
................
................
.....s..........
.....TS.........
......TtS.......
.......TtSs.....
......h.tSSs....
.....hd.SsTSs...
....hd...sTSs...
...hd....sSSs...
..hd......ss....
..d.............
................
................
................
................
"""


def pick():
    """A prospector's pick (point on one side, hammer face on the other) on a light oak haft."""
    return raster(PICK, {'h': R['oak'][6], 'H': R['oak'][4], 'd': R['oak'][1], 's': R['steel'][0],
                         'S': R['steel'][2], 't': R['steel'][3], 'T': R['steel'][4]})


# The Guild's mark, burned into the boards: a lantern over two crossed picks.
MARK = """
..k...k..
.k..k..k.
k.kkkkk.k
..kK.Kk..
..k...k..
..kK.Kk..
..kkkkk..
.k.....k.
k.......k
"""


def side_marked():
    return stamp(side(), MARK, {'k': R['bark'][0], 'K': R['bark'][1]}, 4, 5)


def textures():
    out = {'top': top(), 'side': side(), 'side_marked': side_marked(), 'ore': ore(), 'parts': parts(), 'pick': pick()}
    for key, image in out.items():
        locked(image, key)
    return out


# -- the model (front faces north; the viewer's left is east) -----------------------------------------

def sub(name, dx=0, dy=0, w=None, h=None):
    """A rectangle inside a PART region: offset (dx, dy), size (w, h) in texels."""
    u1, v1, u2, v2 = PART[name]
    w = u2 - u1 if w is None else w
    h = v2 - v1 if h is None else h
    return [u1 + dx, v1 + dy, u1 + dx + w, v1 + dy + h]


def face_sizes(frm, to):
    sx, sy, sz = (to[i] - frm[i] for i in range(3))
    return {'north': (sx, sy), 'south': (sx, sy), 'east': (sz, sy), 'west': (sz, sy), 'up': (sx, sz), 'down': (sx, sz)}


def ore_uv(kind, frm, to, dx=0, dy=0):
    """UVs into one 8x8 heap of the ore atlas, sized to each face."""
    ox, oy = ORE_AT[kind]
    return {f: [ox + dx, oy + dy, ox + dx + min(w, 8 - dx), oy + dy + min(h, 8 - dy)] for f, (w, h) in face_sizes(frm, to).items()}


def chunk(m, kind, frm, to):
    """A loose lump of ore: every face shows the 2x2 lump of that ore in the parts atlas."""
    u1, v1 = PART[kind][:2]
    m.box(frm, to, 'parts', uv={f: [u1, v1, u1 + w, v1 + h] for f, (w, h) in face_sizes(frm, to).items()}, skip=('down',))


def design():
    m = pixel.Model(NS, NAME + '_')
    # The stone top, bound in iron, overhanging the body by a pixel all round.
    m.box([0, 12, 0], [16, 16, 16], {'up': 'top', 'down': 'mc:spruce_planks', '*': 'side'})
    # Two-pixel side walls: their fronts are the front legs; a back wall closes the body.
    # The Guild's mark is burned into the right side and the back.
    m.box([1, 0, 1], [3, 12, 15], {'north': 'mc:spruce_log', 'east': 'mc:spruce_planks', 'down': 'mc:spruce_planks', 'west': 'side_marked', '*': 'side'}, skip=('up',))
    m.box([13, 0, 1], [15, 12, 15], {'north': 'mc:spruce_log', 'west': 'mc:spruce_planks', 'down': 'mc:spruce_planks', '*': 'side'}, skip=('up',))
    m.box([3, 0, 13], [13, 12, 15], {'north': 'mc:dark_oak_planks', 'south': 'side_marked', 'down': 'mc:spruce_planks'}, only=('north', 'south', 'down'))
    # Floor and the middle shelf.
    m.box([3, 0, 1], [13, 1, 13], 'mc:spruce_planks', only=('north', 'up', 'down'))
    m.box([3, 6, 1], [13, 7, 13], 'mc:spruce_planks', only=('north', 'up', 'down'))
    # Bottom shelf: an iron-cornered ore crate, run-of-mine lumps heaped above its rim.
    m.box([3.5, 1, 2], [12.5, 4, 10], {'north': 'parts', '*': 'mc:spruce_planks'}, uv={'north': sub('crate')}, skip=('down',))
    chunk(m, 'iron', [4.5, 4, 3], [6.5, 5.5, 5])
    chunk(m, 'copper', [7, 4, 2.5], [9, 5, 4.5])
    chunk(m, 'coal', [9.5, 4, 3], [11.5, 5.5, 5])
    # Middle shelf: three sorting bins (coal, copper, raw iron) behind a pale lip.
    for kind, x0 in (('coal', 3), ('copper', 6.5), ('iron', 10)):
        m.box([x0, 7, 2], [x0 + 3, 10, 10], 'ore', uv=ore_uv(kind, [x0, 7, 2], [x0 + 3, 10, 10]), skip=('down', 'south'))
        m.box([x0 + .5, 10, 2.5], [x0 + 2.5, 11, 5], 'ore', uv=ore_uv(kind, [x0 + .5, 10, 2.5], [x0 + 2.5, 11, 5], 3, 2), skip=('down',))
    for x0 in (6, 9.5):
        m.box([x0, 7, 2], [x0 + .5, 10.5, 10], 'mc:stripped_spruce_log', skip=('down', 'south'))
    m.box([3, 7, 1.5], [13, 8, 2], {'north': 'parts', '*': 'mc:stripped_spruce_log'}, uv={'north': sub('bin_board', h=1)}, skip=('down', 'south'))
    # A prospector's pick hung on the left side.
    m.box([15.5, 0, 2], [15.5, 12, 14], 'pick', uv={'east': [2, 1, 14, 13]}, only=('east',))
    # On top, back left: a riddle tray with a wire mesh floor and lumps of ore being sorted.
    m.box([7, 16, 6], [15, 18, 7], 'mc:stripped_spruce_log', skip=('down',))
    m.box([7, 16, 13], [15, 18, 14], 'mc:stripped_spruce_log', skip=('down',))
    m.box([7, 16, 7], [8, 18, 13], 'mc:stripped_spruce_log', skip=('down', 'north', 'south'))
    m.box([14, 16, 7], [15, 18, 13], 'mc:stripped_spruce_log', skip=('down', 'north', 'south'))
    m.box([8, 16, 7], [14, 16.5, 13], 'parts', uv={'up': sub('mesh')}, only=('up',))
    chunk(m, 'copper', [9, 16.5, 8], [10.5, 17.5, 9.5])
    chunk(m, 'iron', [11.5, 16.5, 8.5], [13, 17.75, 10])
    chunk(m, 'coal', [9.5, 16.5, 10.5], [11, 17.25, 12])
    chunk(m, 'gold', [12, 16.5, 11.25], [13, 17, 12.25])
    # Back right: a little miner's lantern (its glass glows).
    m.box([1.5, 16, 10.5], [5.5, 21, 14.5], 'parts', uv={**{f: sub('lamp_side') for f in ('north', 'south', 'east', 'west')}, 'up': sub('lamp_top')}, skip=('down',), light=15)
    m.box([2.5, 21, 11.5], [4.5, 22, 13.5], 'parts', uv={f: sub('cap') for f in pixel.FACES}, skip=('down',))
    m.box([2, 22, 12.5], [5, 24, 12.5], 'parts', uv={'north': sub('loop'), 'south': sub('loop')}, only=('north', 'south'))
    m.box([3.5, 22, 11], [3.5, 24, 14], 'parts', uv={'east': sub('loop'), 'west': sub('loop')}, only=('east', 'west'))
    # Front: a hand lens lying on the stone (handle towards the worker), and two samples by it.
    u1, v1, u2, v2 = sub('lens')
    m.box([1, 16.1, 2], [8, 16.1, 9], 'parts', uv={'up': [u1, v2, u2, v1]}, only=('up',))
    chunk(m, 'gold', [10, 16, 3], [11, 16.75, 4])
    chunk(m, 'iron', [11.5, 16, 1.5], [13.5, 17.25, 3.5])
    return m


DISPLAY = {
    'gui': {'rotation': [30, 225, 0], 'translation': [0, -1.5, 0], 'scale': [0.5, 0.5, 0.5]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.25, 0.25, 0.25]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, -1, 0], 'scale': [0.45, 0.45, 0.45]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2, 0], 'scale': [0.33, 0.33, 0.33]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, -1, 0], 'scale': [0.36, 0.36, 0.36]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, -1, 0], 'scale': [0.36, 0.36, 0.36]},
}


def dump(data):
    return (json.dumps(data, indent=2) + '\n').encode()


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return buffer.getvalue()


def outputs():
    """Every generated file: path -> bytes."""
    files = {ASSETS / f'textures/block/{NAME}_{key}.png': png(image) for key, image in textures().items()}
    files[ASSETS / f'models/block/{NAME}.json'] = dump(design().json('side'))
    variants = {}
    for facing, y in (('north', 0), ('east', 90), ('south', 180), ('west', 270)):
        variants[f'facing={facing}'] = {'model': f'{NS}:block/{NAME}', **({'y': y} if y else {})}
    files[ASSETS / f'blockstates/{NAME}.json'] = dump({'variants': variants})
    files[ASSETS / f'models/item/{NAME}.json'] = dump({'parent': f'{NS}:block/{NAME}', 'display': DISPLAY})
    files[ASSETS / f'items/{NAME}.json'] = dump({'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{NAME}'}})
    return files


def write():
    for path, data in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print('wrote', path.relative_to(pixel.PROJECT).as_posix())


def check():
    for e in design().elements:
        for face in e['faces'].values():
            assert all(0 <= c <= 16 for c in face['uv']), (e['from'], face)
        assert all(-16 <= c <= 32 for c in e['from'] + e['to']), e
    crlf, lf = (chr(13) + chr(10)).encode(), chr(10).encode()

    def current(p):  # git may check JSON out with CRLF line endings
        data = p.read_bytes()
        return data.replace(crlf, lf) if p.suffix == '.json' else data
    bad = [p for p, data in outputs().items() if not p.exists() or current(p) != data]
    if bad:
        print('Out of date (rerun tools/art/prospecting_table.py):')
        for p in bad:
            print('  ' + p.relative_to(pixel.PROJECT).as_posix())
        sys.exit(1)
    print('Prospecting table assets are up to date.')


# -- preview ------------------------------------------------------------------------------------------

def loader():
    ours = {f'{NS}:block/{NAME}_{k}': v for k, v in textures().items()}
    return lambda ref: ours[ref] if ref in ours else pixel.vanilla_texture(ref)


def gui_slot(model, load, display_scale, translate_y, zoom=4):
    """Roughly what the inventory shows: a 16px slot at GUI scale `zoom`, drawn with a slot frame."""
    size = 16 * zoom
    image = pixel.render(model, load, scale=display_scale * zoom, view='front_right', canvas=(size, size),
                         origin=(size / 2, size / 2 - translate_y * zoom))
    slot = Image.new('RGBA', (size + 4, size + 4), '#8B8B8B')
    d = ImageDraw.Draw(slot)
    d.line([(0, 0), (size + 3, 0)], fill='#373737', width=2)
    d.line([(0, 0), (0, size + 3)], fill='#373737', width=2)
    d.line([(1, size + 3), (size + 3, size + 3)], fill='#FFFFFF', width=1)
    d.line([(size + 3, 1), (size + 3, size + 3)], fill='#FFFFFF', width=1)
    slot.alpha_composite(image, (2, 2))
    return slot


def preview(dest):
    load = loader()
    ours = design()
    ours = {'textures': ours.textures, 'elements': ours.elements}
    smithing = pixel.vanilla_model('minecraft:block/smithing_table')
    fletching = pixel.vanilla_model('minecraft:block/fletching_table')
    big, units = 10, 34
    tiles = [
        ('prospecting table', pixel.render(ours, load, big, 'front_right', units)),
        ('vanilla smithing table', pixel.render(smithing, pixel.vanilla_texture, big, 'front_right', units)),
        ('vanilla fletching table', pixel.render(fletching, pixel.vanilla_texture, big, 'front_right', units)),
        ('front, from eye height', pixel.render(ours, load, big, 'front', units)),
        ('front left', pixel.render(ours, load, big, 'front_left', units)),
        ('back left', pixel.render(ours, load, big, 'back_left', units)),
        ('back right', pixel.render(ours, load, big, 'back_right', units)),
    ]
    tile = units * big
    sheet = Image.new('RGBA', (4 * tile, 2 * (tile + 20) + 130), '#7D8C99')
    draw = ImageDraw.Draw(sheet)
    for n, (label, image) in enumerate(tiles):
        x, y = (n % 4) * tile, (n // 4) * (tile + 20)
        sheet.alpha_composite(image, (x, y + 18))
        draw.text((x + 8, y + 4), label, fill='#101820')
    # Our textures at 5x, bottom right.
    x, y = 3 * tile + 8, tile + 20 + 18
    draw.text((x, y - 14), 'textures (5x)', fill='#101820')
    for n, (key, image) in enumerate(textures().items()):
        big_tex = image.resize((80, 80), Image.NEAREST)
        sheet.alpha_composite(big_tex, (x + (n % 4) * 84, y + (n // 4) * 100))
        draw.text((x + (n % 4) * 84, y + (n // 4) * 100 + 82), key, fill='#101820')
    # The inventory slot at GUI scale 4 and 2, next to vanilla's.
    y = 2 * (tile + 20) + 16
    draw.text((8, y - 8), 'inventory slot, GUI scale 4 and 2 (ours, smithing, fletching)', fill='#101820')
    gui = DISPLAY['gui']
    for n, (model, tex, s, t) in enumerate(((ours, load, gui['scale'][0], gui['translation'][1]),
                                            (smithing, pixel.vanilla_texture, .625, 0), (fletching, pixel.vanilla_texture, .625, 0))):
        sheet.alpha_composite(gui_slot(model, tex, s, t), (20 + n * 170, y + 8))
        sheet.alpha_composite(gui_slot(model, tex, s, t, zoom=2), (100 + n * 170, y + 8))
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
