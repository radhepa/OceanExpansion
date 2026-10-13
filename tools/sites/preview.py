"""Render every site piece to tools/sites/out/ as an isometric cutaway (vanilla textures).

  python tools/sites/preview.py [key-or-piece-filter] [--full]
--full draws the whole piece instead of cutting the top off; NATURAL lining is drawn like any block."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import designs  # noqa: E402
from render import render_template  # noqa: E402

OUT = os.path.join(HERE, 'out')

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    want = args[0] if args else ''
    key = want.split('/')[0]
    only = [key] if key else None
    for mod in designs.modules(only):
        if not hasattr(mod, 'pieces'):
            print('skipping', mod.__name__, '(not finished)')
            continue
        for t in mod.pieces():
            if want not in t.name: continue
            t.validate()
            flat = t.name.replace('/', '_')
            if '--full' in sys.argv:
                render_template(t, os.path.join(OUT, flat + '.png'), s=10, title=t.name)
            else:
                render_template(t, os.path.join(OUT, flat + '.png'), s=10, title=t.name, cut_y=t.size[1] - 2, open_near=1)
            print('rendered', t.name, t.size, {k: v for k, v in t.notes.items() if k != 'anchor'})
