"""Shared helpers for Ocean Expansion block and item art: palette-locked rasters, vanilla assets, cuboid models.

Every colour a texture may use comes from RAMPS, hand-picked ramps sampled from vanilla textures so
our art sits next to vanilla blocks. Textures are ASCII rasters ('.' = transparent) mapped through a
small per-texture palette; `locked()` refuses any pixel outside the ramps.
Vanilla textures and models are read straight from the Minecraft jar (never copied into the mod).
"""
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[2]
JAR = Path.home() / '.gradle/caches/fabric-loom/minecraftMaven/net/minecraft/minecraft-merged-deobf/26.3/minecraft-merged-deobf-26.3.jar'
CACHE = PROJECT / 'tools/sites/.cache/assets/minecraft'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

# Colour ramps, darkest first, each sampled from the vanilla texture named in the comment.
RAMPS = {
    'spruce': ['#553A1F', '#5A4424', '#614B2E', '#70522E', '#7A5A34', '#82613A', '#886539'],  # spruce_planks
    'bark': ['#2E1608', '#3B2713', '#4D3317', '#553A1F'],                                    # spruce_log
    'pale': ['#61512D', '#675631', '#705934', '#795B37', '#826038', '#866238'],              # stripped_spruce_log
    'oak': ['#67502C', '#7E6237', '#967441', '#9F844D', '#AF8F55', '#B8945F', '#C29D62'],   # oak_planks
    'iron': ['#252C3D', '#3E4453', '#424A5E', '#495065'],                                    # iron_chain, lantern frame
    'steel': ['#686868', '#72796E', '#9C9C9C', '#ABACAB', '#C5C5C5'],                        # rail, iron_bars
    'stone': ['#5A595A', '#636363', '#6A6D6A', '#787678', '#7F7F7F', '#8B898B', '#9C999C'],  # stone_bricks
    'coal': ['#0D0D0D', '#151515', '#1F1E1E', '#292828', '#363636', '#5C5C5C'],              # coal_block, coal_ore
    'copper': ['#844D3B', '#9D573F', '#BA694C', '#D67B5B', '#EA8770', '#FBA894', '#3A7663', '#4FBA98'],  # raw_copper_block
    'raw_iron': ['#665237', '#7C623F', '#8E7454', '#AF8E77', '#D8AF93', '#E9C8B1', '#FEDEC8'],  # raw_iron_block
    'gold': ['#AE6D26', '#C98C1C', '#EEA41A', '#F7C431', '#FAEA2E', '#FFF79D'],              # raw_gold_block
    'flame': ['#814023', '#8B5230', '#C36322', '#F09149', '#F9C966', '#FDFD8B', '#FFFFD5'],  # lantern
    'glass': ['#7BAEB7', '#8BC1CD', '#A8D0D9', '#D0EAE9'],                                   # glass
    'deepslate': ['#242424', '#2D2D2D', '#383737', '#414141', '#4B4C4F', '#585858', '#6E6E6E'],  # deepslate_tiles
    'blackstone': ['#160F10', '#1F121B', '#27221C', '#312C36', '#3C3947', '#4E4B54'],        # polished_blackstone
    # Ocean Expansion
    'copper_block': ['#904931', '#9A5038', '#A75A40', '#B26247', '#C26B4C', '#C87456', '#D67B5B', '#E3826C'],  # copper_block
    'verdigris': ['#3B6655', '#396E59', '#3E816B', '#4C9484', '#53A178', '#4FAB90', '#59B292', '#6EC59F'],  # oxidized_copper
    'prismarine': ['#41816A', '#468974', '#5EA496', '#79B7AB', '#9BCBBF'],                   # prismarine
    'dark_prismarine': ['#273E36', '#315041', '#345648', '#386251', '#3F6D5C', '#3B8268'],   # dark_prismarine
    'crystal': ['#49645C', '#72A498', '#91C5B7', '#B4D8CA', '#DFE9DC'],                      # prismarine_crystals
    'sand': ['#D1BA8A', '#D5C496', '#DACFA3', '#E3DBB0', '#E7E4BB', '#EDEBCB'],              # sand
    'calcite': ['#B3B3B3', '#C9C9C4', '#D9DBD7', '#EDECE6', '#F0F5F4', '#FFFFFF'],           # calcite
    'bone': ['#DEDAC5', '#E1DDCA', '#E6E2D2', '#E9E6D4'],                                    # bone_block_side
    'tuff': ['#4D5046', '#5D5D52', '#6A6E6F', '#85837B', '#A0A297'],                         # tuff
    'nacre': ['#B08ABB', '#B796BC', '#C2A4C3', '#D4BFC8', '#E2D3D3', '#EFE6E1', '#F9F4F3', '#FFFEFD'],  # pearlescent_froglight_side
    'pink': ['#D76690', '#DF6F96', '#E97B9E', '#F187A7', '#F498B4', '#F4A8C1', '#F4B2C9'],   # pink_wool
    'brain': ['#9D2F77', '#BF4692', '#D6549B', '#E47EB9', '#E88EC1'],                        # brain_coral
    'fire_coral': ['#791A26', '#A4222F', '#C62A37', '#E23F36'],                              # fire_coral
    'honey': ['#D56B2B', '#E57B24', '#EA8E16', '#FABF29', '#FADE29'],                        # honeycomb
    'resin': ['#802A1A', '#9B3300', '#B54006', '#E05504', '#F3791B', '#FAB326', '#FFDBB1'],  # resin_clump
    'membrane': ['#6F516C', '#7E627B', '#826D72', '#8E7F7A', '#958C79', '#9C8A83', '#A99B87', '#C3B9A1', '#DCD9C0'],  # phantom_membrane
    'dripstone': ['#634A47', '#735450', '#836356', '#927965', '#A08D71'],                    # dripstone_block
    'ender': ['#032620', '#0B4D42', '#105E51', '#1B7B6B', '#258474', '#349988', '#2CCDB1', '#8CF4E2'],  # ender_pearl
    'amethyst': ['#54398A', '#6F4FAB', '#8D6ACC', '#B38EF3', '#CFA0F3', '#FECBE6', '#FFFDD5'],  # amethyst_shard
    'obsidian': ['#000001', '#06030B', '#100C1C', '#271E3D', '#3B2754'],                     # obsidian
    'crying': ['#2B0178', '#6006AB', '#8308E4'],                                             # crying_obsidian
    'rope': ['#623220', '#815634', '#B79963', '#DFC38D'],                                    # bundle
    'bottle': ['#5D8FC2', '#8BADD0', '#B3CFEC', '#D4E5F7'],                                  # glass_bottle
    'cork': ['#973716', '#A94725', '#D46D49', '#CCAFA5'],                                    # glass_bottle (cork)
    'purple': ['#641F9C', '#6F24A3', '#7A29AB', '#8630B5', '#9743CD'],                       # purple_wool
    'red': ['#8E2020', '#9C2521', '#AA2B23', '#B8342C'],                                     # red_wool
    'orange': ['#E16100', '#EC6D0B', '#F57816', '#F9932B'],                                  # orange_wool
    'heart': ['#082054', '#0B3A4D', '#0D485F', '#0F5875', '#1D6D8D', '#2180A1', '#1F96B1', '#1DC2D1'],  # heart_of_the_sea
    'lapis': ['#143271', '#1C3890', '#20509C', '#2659AB', '#376792'],                        # lapis_block
    'bricks': ['#733F31', '#7C4536', '#8F503F', '#9B5643', '#B1624D', '#C66851'],            # bricks
    'magma': ['#411616', '#501B1B', '#652828', '#723232', '#CA4E06', '#E66410', '#F48522', '#F89E44', '#FBAA59'],  # magma
    'seagrass': ['#215800', '#297100', '#2F8200', '#389306', '#509529'],                     # seagrass
}
ALLOWED = {c.upper() for ramp in RAMPS.values() for c in ramp}


def rgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ramp(name, i):
    return RAMPS[name][i]


def raster(pattern, palette, size=(16, 16), base=None):
    """Paints an ASCII raster. '.' keeps the base (or transparency); every other char must be in palette."""
    w, h = size
    image = base.copy() if base is not None else Image.new('RGBA', (w, h), (0, 0, 0, 0))
    rows = [r for r in pattern.strip('\n').splitlines()]
    assert len(rows) == h, (len(rows), h)
    for y, row in enumerate(rows):
        row = row.strip()
        assert len(row) == w, (y, row, len(row))
        for x, ch in enumerate(row):
            if ch != '.':
                assert palette[ch].upper() in ALLOWED, (ch, palette[ch])
                image.putpixel((x, y), rgb(palette[ch]))
    return image


def stamp(image, pattern, palette, x0, y0, flip_x=False, flip_y=False):
    """Paints a small raster onto image at (x0, y0), optionally mirrored."""
    rows = [r.strip() for r in pattern.strip('\n').splitlines()]
    if flip_y:
        rows = rows[::-1]
    for dy, row in enumerate(rows):
        if flip_x:
            row = row[::-1]
        for dx, ch in enumerate(row):
            if ch != '.':
                assert palette[ch].upper() in ALLOWED, (ch, palette[ch])
                image.putpixel((x0 + dx, y0 + dy), rgb(palette[ch]))
    return image


def locked(image, name):
    """Asserts every opaque pixel is a ramp colour and alpha is all-or-nothing (no blur, no gradients)."""
    for r, g, b, a in image.getdata():
        assert a in (0, 255), (name, 'partial alpha')
        if a:
            assert '#%02X%02X%02X' % (r, g, b) in ALLOWED, (name, '#%02X%02X%02X' % (r, g, b))
    return image


# -- vanilla assets ----------------------------------------------------------------------------------

_jar = None


def vanilla_bytes(path):
    """assets/minecraft/<path> from the Minecraft jar (or the extracted cache)."""
    global _jar
    if _jar is None and JAR.exists():
        _jar = zipfile.ZipFile(JAR)
    if _jar is not None:
        return _jar.read('assets/minecraft/' + path)
    return (CACHE / path).read_bytes()


def vanilla_texture(ref):
    """'minecraft:block/spruce_planks' -> 16x16 RGBA (first frame of animated textures)."""
    name = ref.split(':', 1)[-1]
    image = Image.open(io.BytesIO(vanilla_bytes(f'textures/{name}.png'))).convert('RGBA')
    return image.crop((0, 0, image.width, image.width))


def vanilla_model(ref):
    """A vanilla block model with its parents resolved: {'textures': {...}, 'elements': [...]}."""
    name = ref.split(':', 1)[-1]
    data = json.loads(vanilla_bytes(f'models/{name}.json'))
    textures, elements = dict(data.get('textures', {})), data.get('elements')
    if 'parent' in data:
        parent = vanilla_model(data['parent'])
        textures = {**parent['textures'], **textures}
        elements = elements if elements is not None else parent['elements']
    return {'textures': textures, 'elements': elements or []}


# -- cuboid models -----------------------------------------------------------------------------------

def auto_uv(face, frm, to):
    """Vanilla's default UVs for a face, shifted a whole block when the element pokes outside the block
    (UVs must stay inside 0..16 or they sample neighbouring sprites in the atlas)."""
    x1, y1, z1 = frm
    x2, y2, z2 = to
    u1, v1, u2, v2 = {
        'down': (x1, 16 - z2, x2, 16 - z1), 'up': (x1, z1, x2, z2),
        'north': (16 - x2, 16 - y2, 16 - x1, 16 - y1), 'south': (x1, 16 - y2, x2, 16 - y1),
        'west': (z1, 16 - y2, z2, 16 - y1), 'east': (16 - z2, 16 - y2, 16 - z1, 16 - y1),
    }[face]

    def fit(a, b):
        while a < 0:
            a, b = a + 16, b + 16
        while b > 16:
            a, b = a - 16, b - 16
        return (0, b - a) if a < 0 else (a, b)
    u1, u2 = fit(u1, u2)
    v1, v2 = fit(v1, v2)
    return [round(c, 4) for c in (u1, v1, u2, v2)]


class Model:
    """Builds a block model from cuboids. Texture keys: 'mc:spruce_planks' is vanilla, anything else is ours."""

    def __init__(self, ns, prefix):
        self.ns, self.prefix, self.elements, self.textures = ns, prefix, [], {}

    def ref(self, key):
        return f'minecraft:block/{key[3:]}' if key.startswith('mc:') else f'{self.ns}:block/{self.prefix}{key}'

    def tex(self, key):
        name = key.replace(':', '_')
        self.textures[name] = self.ref(key)
        return '#' + name

    def box(self, frm, to, tex, uv=None, skip=(), only=None, rot=None, light=0, shade=True):
        """A cuboid. tex: one key for all faces or {face: key, '*': default}; uv: {face: [u1, v1, u2, v2]}."""
        faces = {}
        for face in (only or FACES):
            key = tex.get(face, tex.get('*')) if isinstance(tex, dict) else tex
            if face in skip or key is None:
                continue
            entry = {'uv': list((uv or {}).get(face) or auto_uv(face, frm, to)), 'texture': self.tex(key)}
            axis = {'north': (2, 0), 'south': (2, 16), 'west': (0, 0), 'east': (0, 16), 'down': (1, 0), 'up': (1, 16)}[face]
            plane = frm[axis[0]] if axis[1] == 0 else to[axis[0]]
            if not rot and plane == axis[1]:
                entry['cullface'] = face
            faces[face] = entry
        element = {'from': list(frm), 'to': list(to)}
        if rot:
            axis, angle, origin = rot
            element['rotation'] = {'origin': list(origin), 'axis': axis, 'angle': angle}
        if not shade:
            element['shade'] = False
        if light:
            element['light_emission'] = light
        element['faces'] = faces
        self.elements.append(element)
        return self

    def json(self, particle, display=None):
        textures = dict(sorted(self.textures.items()))
        textures['particle'] = self.ref(particle)
        out = {'parent': 'minecraft:block/block', 'textures': textures, 'elements': self.elements}
        if display:
            out['display'] = display
        return out


# -- isometric preview renderer ----------------------------------------------------------------------

CORNERS = {  # face -> (top-left, top-right, bottom-left) as the texture lies on it
    'north': lambda a, b: [(b[0], b[1], a[2]), (a[0], b[1], a[2]), (b[0], a[1], a[2])],
    'south': lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (a[0], a[1], b[2])],
    'west': lambda a, b: [(a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], a[2])],
    'east': lambda a, b: [(b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], b[2])],
    'up': lambda a, b: [(a[0], b[1], a[2]), (b[0], b[1], a[2]), (a[0], b[1], b[2])],
    'down': lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], a[2])],
}
NORMALS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}
SHADE = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
ELEV = math.tan(math.radians(30)) * math.sqrt(2)
VIEWS = {'front_right': (1, ELEV, -1), 'front_left': (-1, ELEV, -1), 'back_left': (-1, ELEV, 1), 'back_right': (1, ELEV, 1),
         'front': (.25, .45, -1)}  # roughly where a standing player's eye sees a block one step away


def _rotate(p, rot):
    if not rot:
        return np.array(p, float)
    axis, angle, origin = rot['axis'], math.radians(rot['angle']), np.array(rot['origin'], float)
    x, y, z = np.array(p, float) - origin
    c, s = math.cos(angle), math.sin(angle)
    if axis == 'x':
        y, z = y * c - z * s, y * s + z * c
    elif axis == 'y':
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return np.array([x, y, z]) + origin


def _resolve(textures, ref):
    seen = 0
    while ref.startswith('#'):
        ref = textures[ref[1:]]
        seen += 1
        assert seen < 10, ref
    return ref if ':' in ref else 'minecraft:' + ref


def render(model, load, scale=12, view='front_right', size=40, canvas=None, origin=None):
    """Orthographic, z-buffered render of a model dict {'textures', 'elements'}; load(ref) -> RGBA image.
    One model unit is `scale` pixels; the canvas is size x size units (or canvas=(w, h) pixels) and the
    block centre lands at origin (default: middle, 60% down)."""
    c = np.array(VIEWS[view], float)
    c /= np.linalg.norm(c)
    f = -c
    right = np.array([-f[2], 0, f[0]])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    W, H = canvas or (int(size * scale), int(size * scale))
    ox, oy = origin or (W / 2, H * .6)
    color = np.zeros((H, W, 4), np.uint8)
    depth = np.full((H, W), -1e9)
    cache = {}
    for e in model['elements']:
        rot = e.get('rotation')
        for face, spec in e['faces'].items():
            n = _rotate(NORMALS[face], rot and {**rot, 'origin': [0, 0, 0]})
            if np.dot(n, c) <= 1e-6:
                continue
            tl, tr, bl = (_rotate(p, rot) - 8 for p in CORNERS[face](e['from'], e['to']))
            P = [np.array([np.dot(p, right) * scale + ox, -np.dot(p, up) * scale + oy]) for p in (tl, tr, bl)]
            D = [np.dot(p, c) for p in (tl, tr, bl)]
            M = np.array([P[1] - P[0], P[2] - P[0]]).T
            if abs(np.linalg.det(M)) < 1e-6:
                continue
            inv = np.linalg.inv(M)
            corners = np.array([P[0], P[1], P[2], P[1] + P[2] - P[0]])
            x0, y0 = np.floor(corners.min(0)).astype(int)
            x1, y1 = np.ceil(corners.max(0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
            if x0 >= x1 or y0 >= y1:
                continue
            ys, xs = np.mgrid[y0:y1, x0:x1]
            px, py = xs + .5 - P[0][0], ys + .5 - P[0][1]
            a = inv[0, 0] * px + inv[0, 1] * py
            b = inv[1, 0] * px + inv[1, 1] * py
            inside = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
            d = D[0] + a * (D[1] - D[0]) + b * (D[2] - D[0])
            ref = _resolve(model['textures'], spec['texture'])
            if ref not in cache:
                cache[ref] = np.array(load(ref).convert('RGBA'))
            tex = cache[ref]
            k = tex.shape[1] / 16
            u1, v1, u2, v2 = spec.get('uv') or auto_uv(face, e['from'], e['to'])
            u = u1 + (u2 - u1) * a
            v = v1 + (v2 - v1) * b
            ui = np.clip(np.floor(np.minimum(u, max(u1, u2) - 1e-4) * k), 0, tex.shape[1] - 1).astype(int)
            vi = np.clip(np.floor(np.minimum(v, max(v1, v2) - 1e-4) * k), 0, tex.shape[0] - 1).astype(int)
            texel = tex[vi, ui]
            ok = inside & (texel[..., 3] >= 128) & (d > depth[y0:y1, x0:x1])
            lit = e.get('light_emission', 0) or (e.get('shade') is False)
            shade = 1.0 if lit else SHADE[face]
            region = color[y0:y1, x0:x1]
            region[ok, :3] = (texel[ok, :3] * shade).astype(np.uint8)
            region[ok, 3] = 255
            depth[y0:y1, x0:x1][ok] = d[ok]
    return Image.fromarray(color, 'RGBA')


def cube_model(ref):
    """A vanilla block model ('minecraft:block/smithing_table') ready for render()."""
    return vanilla_model(ref)
