"""Painting and preview helpers shared by tools/art/blocks.py and tools/art/ocean_items.py.

Everything here builds on pixel.py: colours still come only from pixel.RAMPS. What this adds:
  * rasters whose palette entries may carry an alpha ((hex, alpha)) for the few translucent textures,
    and a lock that checks colours AND a fixed set of allowed alphas;
  * a shaded-ball painter for round things (pearls) that quantises to a ramp, so it stays pixel art;
  * a scene renderer: pixel.render's z-buffered projector, extended with blockstate rotations
    (x then y, in 90 degree steps), block offsets and back-to-front blending of translucent texels,
    so previews can show several blocks in place, in every facing.
"""
import io
import math

import numpy as np
from PIL import Image, ImageDraw

import pixel
from pixel import ALLOWED, CORNERS, NORMALS, SHADE, VIEWS


def hexa(spec):
    """'#RRGGBB' or ('#RRGGBB', alpha) -> (hex, alpha)."""
    return (spec, 255) if isinstance(spec, str) else spec


def put(image, x, y, spec):
    h, a = hexa(spec)
    assert h.upper() in ALLOWED, h
    image.putpixel((x, y), pixel.rgb(h, a))


def paint(pattern, palette, size=(16, 16), base=None, x0=0, y0=0):
    """Like pixel.raster/stamp, but palette values may be (hex, alpha). Spaces inside rows are ignored.
    With base, the pattern is stamped at (x0, y0); without, a new transparent image of `size`."""
    image = base if base is not None else Image.new('RGBA', size, (0, 0, 0, 0))
    rows = [r.replace(' ', '') for r in pattern.strip('\n').splitlines()]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                put(image, x0 + dx, y0 + dy, palette[ch])
    return image


def soft_locked(image, name, alphas=(0, 255)):
    """Every visible pixel is a ramp colour and every alpha is one of `alphas`."""
    for r, g, b, a in image.getdata():
        assert a in alphas, (name, 'alpha', a)
        if a:
            assert '#%02X%02X%02X' % (r, g, b) in ALLOWED, (name, '#%02X%02X%02X' % (r, g, b))
    return image


def ball(image, cx, cy, r, tones, light=(-.55, -.65, .55), outline=None, spec=None, rim=None, rim_dir=(.6, .7, .2),
         bands=None):
    """A shaded sphere centred at pixel corner (cx, cy), radius r, quantised to `tones` (dark -> light).
    outline: colour for the outermost ring; spec: highlight colour on the brightest texel(s);
    rim: (colour, threshold) reflected light on the side facing rim_dir; bands: optional list of
    (lo, hi, colour) diffuse bands that override the tone (for iridescent sheens)."""
    L = np.array(light, float)
    L /= np.linalg.norm(L)
    R = np.array(rim_dir, float)
    R /= np.linalg.norm(R)
    best, best_xy = -9, []
    cells = {}
    for y in range(image.height):
        for x in range(image.width):
            dx, dy = (x + .5 - cx) / r, (y + .5 - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            n = np.array([dx, dy, math.sqrt(max(0, 1 - d2))])
            diffuse = max(0, float(n @ L))
            cells[(x, y)] = (n, diffuse, d2)
    for (x, y), (n, diffuse, d2) in cells.items():
        i = min(len(tones) - 1, int(diffuse * len(tones) * 1.02))
        colour = tones[i]
        if bands:
            for lo, hi, c in bands:
                if lo <= diffuse < hi:
                    colour = c
        if rim and float(n @ R) > rim[1] and diffuse < .45:
            colour = rim[0]
        edge = any((x + ox, y + oy) not in cells for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if outline and edge:
            colour = outline
        put(image, x, y, colour)
        if diffuse > best + 1e-6:
            best, best_xy = diffuse, [(x, y)]
        elif abs(diffuse - best) < 1e-6:
            best_xy.append((x, y))
    if spec:
        for x, y in best_xy[:1]:
            put(image, x, y, spec)
    return image


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return buffer.getvalue()


# -- scene renderer -----------------------------------------------------------------------------------

def _elem_rotate(p, rot):
    return pixel._rotate(p, rot)


def _state_rotate(v, rx, ry):
    """Blockstate rotation of a vector relative to the block centre: x first, then y (90 degree steps).
    x=90 turns up into north; y=90 turns north into east (clockwise seen from above)."""
    x, y, z = v
    for _ in range((rx // 90) % 4):
        y, z = z, -y
    for _ in range((ry // 90) % 4):
        x, z = -z, x
    return np.array([x, y, z], float)


def render_scene(parts, scale=12, view='front_right', canvas=(480, 480), origin=None):
    """parts: list of (model, load, (rx, ry), (dx, dy, dz)) where model is {'textures', 'elements'}, load(ref)
    -> RGBA image, (rx, ry) a blockstate rotation and (dx, dy, dz) a block offset. Opaque and cutout texels are
    z-buffered (alpha >= 128 shows, like vanilla cutout); translucent texels (0 < alpha < 255 in a texture marked
    translucent) are blended back to front afterwards."""
    c = np.array(VIEWS[view] if isinstance(view, str) else view, float)
    c /= np.linalg.norm(c)
    f = -c
    right = np.array([-f[2], 0, f[0]])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    W, H = canvas
    ox, oy = origin or (W / 2, H * .6)
    color = np.zeros((H, W, 4), float)
    depth = np.full((H, W), -1e9)
    cache = {}
    later = []
    for model, load, (rx, ry), offset in parts:
        off = np.array(offset, float) * 16
        for e in model['elements']:
            rot = e.get('rotation')
            for face, spec in e['faces'].items():
                n = _elem_rotate(NORMALS[face], rot and {**rot, 'origin': [0, 0, 0]})
                n = _state_rotate(n, rx, ry)
                if np.dot(n, c) <= 1e-6:
                    continue
                pts = []
                for p in CORNERS[face](e['from'], e['to']):
                    q = _state_rotate(_elem_rotate(p, rot) - 8, rx, ry) + off
                    pts.append(q)
                P = [np.array([np.dot(p, right) * scale + ox, -np.dot(p, up) * scale + oy]) for p in pts]
                D = [np.dot(p, c) for p in pts]
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
                tref = spec['texture']
                ref = pixel._resolve({k: (v['sprite'] if isinstance(v, dict) else v) for k, v in model['textures'].items()}, tref)
                translucent = any(isinstance(v, dict) and v.get('force_translucent') and v['sprite'] == ref
                                  for v in model['textures'].values())
                key = (id(load), ref)
                if key not in cache:
                    cache[key] = np.array(load(ref).convert('RGBA'))
                tex = cache[key]
                k = tex.shape[1] / 16
                u1, v1, u2, v2 = spec.get('uv') or pixel.auto_uv(face, e['from'], e['to'])
                u = u1 + (u2 - u1) * a
                v = v1 + (v2 - v1) * b
                ui = np.clip(np.floor(np.clip(u, min(u1, u2), max(u1, u2) - 1e-4) * k), 0, tex.shape[1] - 1).astype(int)
                vi = np.clip(np.floor(np.clip(v, min(v1, v2), max(v1, v2) - 1e-4) * k), 0, tex.shape[0] - 1).astype(int)
                texel = tex[vi, ui].astype(float)
                lit = e.get('light_emission', 0)
                shade = 1.0 if lit else SHADE[_face_of(n)]
                if translucent:
                    later.append((x0, y0, x1, y1, inside & (texel[..., 3] > 0), d, texel, shade))
                    continue
                ok = inside & (texel[..., 3] >= 128) & (d > depth[y0:y1, x0:x1])
                region = color[y0:y1, x0:x1]
                region[ok, :3] = texel[ok, :3] * shade
                region[ok, 3] = 255
                depth[y0:y1, x0:x1][ok] = d[ok]
    # Translucent faces, far ones first, blended over what is already drawn (no depth writes).
    later.sort(key=lambda t: float(np.mean(t[5][t[4]])) if t[4].any() else 0)
    for x0, y0, x1, y1, mask, d, texel, shade in later:
        ok = mask & (d > depth[y0:y1, x0:x1])
        region = color[y0:y1, x0:x1]
        alpha = texel[..., 3:4] / 255.0
        cover = region[..., 3:4] / 255.0
        out_a = alpha + cover * (1 - alpha)
        rgb = (texel[..., :3] * shade * alpha + region[..., :3] * cover * (1 - alpha)) / np.maximum(out_a, 1e-6)
        region[ok, :3] = rgb[ok]
        region[ok, 3] = (out_a[..., 0] * 255)[ok]
    return Image.fromarray(np.clip(color, 0, 255).astype(np.uint8), 'RGBA')


def _face_of(n):
    axis = int(np.argmax(np.abs(n)))
    return [('west', 'east'), ('down', 'up'), ('north', 'south')][axis][1 if n[axis] > 0 else 0]


def slot(image16_or_render, zoom=4):
    """An inventory slot frame around a 16*zoom px picture."""
    size = 16 * zoom
    out = Image.new('RGBA', (size + 4, size + 4), '#8B8B8B')
    d = ImageDraw.Draw(out)
    d.line([(0, 0), (size + 3, 0)], fill='#373737', width=2)
    d.line([(0, 0), (0, size + 3)], fill='#373737', width=2)
    d.line([(1, size + 3), (size + 3, size + 3)], fill='#FFFFFF', width=1)
    d.line([(size + 3, 1), (size + 3, size + 3)], fill='#FFFFFF', width=1)
    pic = image16_or_render
    if pic.width == 16:
        pic = pic.resize((size, size), Image.NEAREST)
    out.alpha_composite(pic, (2, 2))
    return out


GUI_VIEW = (1, math.tan(math.radians(30)) * math.sqrt(2), -1)  # block/block's gui rotation [30, 225, 0]


def gui_block(model, load, display, zoom=4):
    """Roughly what the inventory shows for a block item: the gui transform's scale and y translation."""
    gui = display.get('gui', {'scale': [.625] * 3, 'translation': [0, 0, 0]})
    s, t = gui['scale'][0], gui['translation'][1]
    size = 16 * zoom
    return render_scene([(model, load, (0, 0), (0, 0, 0))], scale=s * zoom, view='front_right', canvas=(size, size),
                        origin=(size / 2, size / 2 - t * zoom))
