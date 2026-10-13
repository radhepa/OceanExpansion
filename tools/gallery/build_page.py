"""Builds the Cave Expansion showcase page (one self-contained HTML file) from a game-test run's screenshots and
report, the design previews and the dialogue.

    python tools/gallery/build_page.py <shots folder> <out.html>

The shots folder is a copy of build/run/clientGameTest/screenshots plus delves/report.json (the run folder is
wiped on every run). Images are resized and embedded as JPEG data URIs.
"""
import base64
import html
import io
import json
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEMPLATE = os.path.join(HERE, 'page.html')
LINES = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'caveexpansion', 'talk', 'lines.json')
CATALOG = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'caveexpansion', 'caveexpansion', 'catalog.json')
PREVIEWS = os.path.join(ROOT, 'tools', 'delves', 'out')

# Shallowest first: the page reads like a descent.
ORDER = ['hermit', 'camp', 'seam', 'cistern', 'post', 'grotto', 'forge', 'ossuary']
BLURB = {
    'hermit': "A mossy cave of giant mushrooms (the red one is called the Bishop), glow berries and a lily pond, where an old "
              "Guild delver stayed below thirty years ago. The hermit brews night-sight potions, trades like a cleric and "
              "knows where other delves lie. One way in: a winding crawl that ends in a roof-fall.",
    'camp': "A working camp of the Delvers' Guild: three miners and their foreman in copper helmets, bunks, a forge corner, "
            "ore bins, four prospecting tables and an ore cart on the rails. Rail drifts run out to working faces whose walls "
            "are thick with ore. Miners buy your ore, sell gear, and the foreman sells survey maps.",
    'seam': "The camp the roof came down on. Broken props, rubble you dig through, a derailed ore cart, the foreman's last "
            "log (it stops mid-sentence), a cave-spider nest, and behind a rubble wall the rich seam that got them killed: "
            "diamond ore and raw gold. The buried shift rises when you come near.",
    'cistern': "A groin-vaulted reservoir of the Old Delvers, flooded five deep. Walkways and a causeway cross it; the sunken "
               "vault sits behind a grate at the bottom, the waterwarden's ledger beside a waterwheel. The drowned wake.",
    'post': "A fortified barbican across a cave road, held by the Deepwatch: two knights, two archers and their captain, "
            "who fight what comes up the road. Gatehouse, archer towers, barracks, armory and drill yard. Behind the keep, "
            "the sealed Deepgate and the Long Stair that goes down further than any map.",
    'grotto': "A geode the size of a hall: calcite and amethyst in layers, budding crystal, a still pool lit from below, "
              "and the Old Delvers' crystal shrine with its Great Lantern. No guardians. Finding it is the reward.",
    'forge': "An Old Delver forge-hall over a lava lake: gold-capped pillars, lava channels in the floor, banks of blast "
             "furnaces, a colossal anvil under a hanging hammer. Across the lava, by a jump, the masterwork vault "
             "(a netherite upgrade template, sometimes). Embers stir as you come in. The rarest delve.",
    'ossuary': "The Old Delvers' catacombs, deepest of all: a cross-shaped vaulted crypt with bone niches, candles and "
               "sarcophagi you prise open, two skeleton crypts, the reliquary behind the altar and the book of the "
               "honoured dead. The Keeper wakes.",
}
GUARDIANS = {'seam': 'Restless miners (Lost Miners)', 'cistern': 'Drowned', 'ossuary': 'The Keeper (Gravewarden) and skeletons',
             'forge': 'Soulpyres'}
PEOPLE = {'camp': '3 miners + foreman', 'post': '2 knights, 2 archers, captain', 'hermit': 'the hermit'}


def find(folder, name):
    for f in sorted(os.listdir(folder)):
        stem = os.path.splitext(f)[0]
        if stem == name or (stem[:4].isdigit() and stem.split('_', 1)[-1] == name):
            return os.path.join(folder, f)
    return None


def embed(path, width=1000, quality=78, crop=None):
    if path is None or not os.path.exists(path): return None
    img = Image.open(path).convert('RGB')
    if crop:
        w, h = img.size
        img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def figure(uri, caption, cls=''):
    if uri is None: return ''
    return (f'<figure class="{cls}"><img src="{uri}" alt="{html.escape(caption)}" loading="lazy">'
            f'<figcaption>{html.escape(caption)}</figcaption></figure>')


def main():
    shots, out = sys.argv[1], sys.argv[2]
    report = json.load(open(os.path.join(shots, 'report.json'), encoding='utf-8'))
    catalog = json.load(open(CATALOG, encoding='utf-8'))
    lines = json.load(open(LINES, encoding='utf-8'))['pools']
    rnd = random.Random(7)
    sections = []
    for key in ORDER:
        info, facts = catalog[key], report.get(key, {})
        lo, hi = info['depth']
        figs = []
        for i, suffix in enumerate(('-1', '-2')):
            p = None
            for f in os.listdir(shots):
                if f.endswith(f'-{key}{suffix}.png'): p = os.path.join(shots, f)
            figs.append(figure(embed(p), f"{info['name']}, in game" + (' (night vision)' if i == 0 else ''), 'shot'))
        extra = find(shots, f'delve-{key}-resident') or find(shots, f'delve-{key}-guardians')
        if extra:
            label = 'Who lives here' if 'resident' in extra else 'The guardians rise'
            figs.append(figure(embed(extra), label, 'shot'))
        cut = os.path.join(shots, f'cutaway_{key}.png')
        if os.path.exists(cut): figs.append(figure(embed(cut, 1100, 82), 'X-ray: everything built, the rock taken away', 'cut'))
        chips = [f'<span class="chip depth">y {lo} to {hi}</span>']
        chips.append(f'<span class="chip lived">{PEOPLE[key]}</span>' if key in PEOPLE else f'<span class="chip wild">{GUARDIANS.get(key, "no guardians")}</span>')
        loot = facts.get('loot', {})
        if loot: chips.append(f'<span class="chip">{sum(loot.values())} loot containers</span>')
        talk = ''
        if facts.get('talk'):
            said = rnd.choice(facts['talk'])
            who, rest = said.split(': ', 1)
            greet = rest.split(' | ')[0]
            talk = f'<blockquote><p>{html.escape(greet)}</p><cite>{html.escape(who)}</cite></blockquote>'
        sections.append(f'''
<section class="delve" id="{key}" data-y="{lo}">
  <header><span class="mark" aria-hidden="true"></span><h2>{html.escape(info['name'])}</h2><div class="chips">{''.join(chips)}</div></header>
  <p class="blurb">{html.escape(BLURB[key])}</p>
  {talk}
  <div class="figs">{''.join(figs)}</div>
</section>''')
    census = report.get('census', {})
    kinds = census.get('kinds', {})
    total = sum(kinds.values()) or 1
    bars = ''.join(f'<div class="bar"><span class="label">{html.escape(catalog[k]["name"])}</span><span class="track">'
                   f'<span class="fill" style="width:{100 * kinds.get(k, 0) / max(kinds.values() or [1]):.0f}%"></span></span>'
                   f'<span class="n">{kinds.get(k, 0)}</span></div>' for k in ORDER)
    sample = []
    for role, label in (('miner', 'A miner'), ('foreman', 'The foreman'), ('warden', 'A Deepwatch warden'), ('captain', 'The captain'), ('hermit', 'The hermit')):
        pool = [l for l in lines.get(f'{role}.chat', []) if '{' not in l]
        if pool: sample.append(f'<blockquote><p>{html.escape(rnd.choice(pool))}</p><cite>{label}</cite></blockquote>')
    mods = ', '.join(m for m in report.get('mods', []) if not m.startswith(('caveexpansion', 'deepdelves')))
    page = open(TEMPLATE, encoding='utf-8').read()
    page = (page.replace('{{SECTIONS}}', ''.join(sections)).replace('{{BARS}}', bars)
            .replace('{{CELLS}}', str(census.get('cells', 81))).replace('{{FOUND}}', str(census.get('delves', '?')))
            .replace('{{PER}}', str(census.get('blocks_per_delve', '?'))).replace('{{SAMPLE}}', ''.join(sample))
            .replace('{{MODS}}', html.escape(mods)).replace('{{LINES}}', str(sum(len(v) for v in lines.values())))
            .replace('{{TABLE}}', embed(os.path.join(shots, 'table.png'), 900, 85) or ''))
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    print('wrote', out, round(os.path.getsize(out) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
