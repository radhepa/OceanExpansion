"""The Ocean Expansion mod icon: a red-and-white lighthouse on a rock at night, its beam sweeping out over the
waves towards a small ship on the horizon, inside a rope frame.

Painted at 32x32 from palette-locked colours (pixel.RAMPS), upscaled 4x with nearest-neighbour.

    python tools/art/icon.py                    # writes src/main/resources/assets/oceanexpansion/icon.png
    python tools/art/icon.py --check            # verifies the written icon matches this script
    python tools/art/icon.py --preview out.png  # the icon at 128, 64 and 32 px on light and dark grounds
"""
import io
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixel  # noqa: E402
from pixel import RAMPS as R, stamp, locked  # noqa: E402

DEST = pixel.PROJECT / 'src/main/resources/assets/oceanexpansion/icon.png'
SIZE, SCALE = 32, 4
HORIZON = 20          # first row of sea
LAMP = (25.0, 7.5)    # centre of the lamp room (pixel corners)

# Night sky, top to horizon, with the boundary rows dithered.
SKY = [(0, R['heart'][0]), (7, R['lapis'][0]), (13, R['lapis'][1]), (17, R['lapis'][2])]
STARS = [(4, 3), (9, 2), (15, 4), (19, 2), (28, 4), (6, 8), (12, 6), (3, 13), (29, 12), (17, 13)]
TWINKLES = [(13, 3)]
# Sea, horizon to bottom.
SEA = [(HORIZON, R['heart'][4]), (22, R['heart'][3]), (25, R['heart'][2]), (28, R['heart'][1])]

# The lighthouse, drawn over the sky: columns 21-28, rows 3-20.
TOWER = """
...dd...
..rRRr..
.rRRRRr.
.iyYYyi.
.iYWWYi.
.iyYYyi.
iiiiiiii
.wWWWwc.
.wWWWwc.
.rRRRrq.
.rRRRrq.
.rRRRrq.
.wWWWWc.
wWWWWWwc
wWWWWWwc
rRRRRRrq
rRRRRRrq
rRRRRRrq
"""
TOWER_COLORS = {'d': R['iron'][0], 'r': R['bricks'][2], 'R': R['bricks'][4], 'q': R['bricks'][0],
                'w': R['calcite'][2], 'W': R['calcite'][4], 'c': R['calcite'][0],
                'i': R['iron'][1], 'y': R['flame'][4], 'Y': R['flame'][5]}
ROCK = """
.....kKKk...
...kKSsKKk..
..kKSssSKKk.
.kKSsKKsSKKk
kKSsKKKKsSKk
"""
ROCK_COLORS = {'k': R['deepslate'][0], 'K': R['deepslate'][2], 's': R['deepslate'][4], 'S': R['deepslate'][5]}
SHIP = """
....d.....
...ddd.d..
..dddd.dd.
.ddddd.ddd
...d...d..
dddddddddd
.dddddddd.
"""
SHIP_COLORS = {'d': R['heart'][0]}


def sky_colour(y, x):
    colour = SKY[0][1]
    for i, (row, c) in enumerate(SKY):
        if y > row or (y == row and (x + y) % 2 == 0):
            colour = c
    return colour


def sea_colour(y, x):
    colour = SEA[0][1]
    for row, c in SEA:
        if y > row or (y == row and (x + y) % 2 == 0):
            colour = c
    return colour


def beam(x, y):
    """0 outside the beam, else 1 (glow), 2 (light) or 3 (core): a wedge from the lamp out to the left edge."""
    lx, ly = LAMP
    if x + .5 >= lx - 1:
        return 0
    t = (lx - (x + .5)) / (lx - 2)
    axis = ly - 2.2 * t
    half = .75 + 3.1 * t
    d = abs(y + .5 - axis) / half
    if d < .4:
        return 3
    if d < .78:
        return 2
    if d < 1.05 or (d < 1.3 and (x + y) % 2 == 0):
        return 1
    return 0


BEAM = {3: [R['flame'][6], R['flame'][5], R['sand'][5]], 2: [R['flame'][5], R['flame'][4], R['sand'][2]],
        1: [R['lapis'][4], R['lapis'][4], R['lapis'][3]]}


def background():
    image = Image.new('RGBA', (SIZE, SIZE))
    for y in range(SIZE):
        for x in range(SIZE):
            if y < HORIZON:
                c = sky_colour(y, x)
                b = beam(x, y)
                if b:
                    t = (LAMP[0] - x) / LAMP[0]
                    c = BEAM[b][0 if t < .3 else 1 if t < .65 else 2]
            else:
                c = sea_colour(y, x)
            image.putpixel((x, y), pixel.rgb(c))
    for x, y in STARS:
        if not beam(x, y):
            image.putpixel((x, y), pixel.rgb(R['calcite'][5] if (x * 7 + y) % 3 else R['crystal'][3]))
    for x, y in TWINKLES:
        stamp(image, '.n.\nnWn\n.n.', {'n': R['lapis'][4], 'W': R['calcite'][5]}, x - 1, y - 1)
    return image


def waves(image):
    """Rows of wave crests: a lit crest, foam on the tallest, and the beam's glints on the water below it."""
    for row, phase, length in ((22, 0, 7), (25, 4, 9), (28, 2, 8)):
        for x in range(2, SIZE - 2):
            k = (x + phase) % length
            if k == 0:
                image.putpixel((x, row), pixel.rgb(R['heart'][6]))
                image.putpixel((x + 1, row - 1), pixel.rgb(R['crystal'][4] if row == 22 else R['heart'][7]))
                image.putpixel((x + 2, row), pixel.rgb(R['heart'][6]))
    # Glints of the beam on the swell under the lighthouse.
    for x, y in ((17, 21), (14, 21), (18, 23), (11, 22)):
        image.putpixel((x, y), pixel.rgb(R['flame'][4] if x > 13 else R['sand'][3]))
    return image


def frame(image):
    """A navy edge and a twisted rope just inside it."""
    last = SIZE - 1
    for i in range(SIZE):
        for x, y in ((i, 0), (0, i), (i, last), (last, i)):
            image.putpixel((x, y), pixel.rgb(R['heart'][0]))
    for i in range(1, last):
        c = R['rope'][3] if i % 2 else R['rope'][1]
        d = R['rope'][2] if i % 2 else R['rope'][0]
        image.putpixel((i, 1), pixel.rgb(c))
        image.putpixel((1, i), pixel.rgb(c))
        image.putpixel((i, last - 1), pixel.rgb(d))
        image.putpixel((last - 1, i), pixel.rgb(d))
    for x, y in ((1, 1), (last - 1, 1), (1, last - 1), (last - 1, last - 1)):
        image.putpixel((x, y), pixel.rgb(R['rope'][2]))
    return image


def icon():
    image = background()
    waves(image)
    stamp(image, SHIP, SHIP_COLORS, 4, 15)
    image.putpixel((12, 19), pixel.rgb(R['flame'][4]))   # the ship's stern lantern
    stamp(image, ROCK, ROCK_COLORS, 19, 19)
    stamp(image, TOWER, TOWER_COLORS, 21, 3)
    # The lamp room's glass burns white-hot in the middle.
    for x, y in ((24, 7), (25, 7)):
        image.putpixel((x, y), pixel.rgb(R['flame'][6]))
    frame(image)
    return locked(image, 'icon')


def big(image, scale=SCALE):
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return buffer.getvalue()


def preview(dest):
    """The icon at 128, 64 and 32 px (as Mod Menu shows it) on light and dark grounds."""
    full = big(icon())
    sheet = Image.new('RGBA', (2 * (128 + 64 + 32 + 40) + 20, 148), '#D8DEE4')
    sheet.paste(Image.new('RGBA', (sheet.width // 2, 148), '#1E2228'), (sheet.width // 2, 0))
    for n in range(2):
        x = 10 + n * (sheet.width // 2)
        for size in (128, 64, 32):
            sheet.alpha_composite(full.resize((size, size), Image.LANCZOS if size < 128 else Image.NEAREST), (x, 10))
            x += size + 20
    sheet.convert('RGB').save(dest)
    print('preview', dest)


if __name__ == '__main__':
    if '--preview' in sys.argv:
        preview(sys.argv[sys.argv.index('--preview') + 1])
    elif '--check' in sys.argv:
        ok = DEST.exists() and DEST.read_bytes() == png(big(icon()))
        print('Icon is up to date.' if ok else 'Icon is out of date (rerun tools/art/icon.py).')
        sys.exit(0 if ok else 1)
    else:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_bytes(png(big(icon())))
        print('wrote', DEST.relative_to(pixel.PROJECT).as_posix())
