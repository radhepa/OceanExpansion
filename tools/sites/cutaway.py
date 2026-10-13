"""X-ray view of a whole generated site, from the block dump the game test writes
(build/run/clientGameTest/sites/<key>.json): every block of its pieces except plain rock and air, so the
rooms, tunnels and linings show as they actually landed in the world (and where they broke into caves).

  python tools/sites/cutaway.py build/run/clientGameTest/sites/camp.json out.png [--scale 6] [--cut 6]

--cut keeps only the lowest N blocks above each column's lowest block (a dollhouse cut); default: no cut.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render  # noqa: E402

# Rock-like blocks hidden too, so the built parts read clearly.
HIDE = ('cave_air', 'water', 'lava', 'calcite', 'smooth_basalt', 'clay', 'coarse_dirt', 'rooted_dirt', 'moss_block',
        'dripstone_block', 'magma_block', 'obsidian', 'blackstone', 'basalt', 'mud', 'glow_lichen', 'pointed_dripstone')


def state(raw):
    """'minecraft:oak_stairs[facing=north,half=top]' as the game prints it -> the same spec render() wants."""
    return raw.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dump')
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=6)
    ap.add_argument('--cut', type=int, default=0)
    ap.add_argument('--keep-lining', action='store_true', help='draw the natural linings (calcite, moss...) too')
    args = ap.parse_args()
    with open(args.dump, encoding='utf-8') as f:
        data = json.load(f)
    blocks = {}
    low = {}
    for x, y, z, raw in data['cells']:
        low[(x, z)] = min(low.get((x, z), y), y)
    for x, y, z, raw in data['cells']:
        if args.cut and y > low[(x, z)] + args.cut: continue
        blocks[(x, y, z)] = state(raw)
    hide = ('cave_air', 'water', 'lava') if args.keep_lining else HIDE
    render(blocks, args.out, s=args.scale, hide=hide, title=os.path.splitext(os.path.basename(args.dump))[0])
    print('wrote', args.out, len(blocks), 'blocks')


if __name__ == '__main__':
    main()
