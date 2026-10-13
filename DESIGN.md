# Ocean Expansion: design

Ocean Expansion is an add-on for the Village Friends modpack (Minecraft 26.3, Fabric). It makes the sea worth
exploring with **ten rare sites**: some you see from a boat (a lighthouse, a sea fort, a smugglers' rock, an
iceberg), most you find by diving (a sunken galleon, a whale fall, a drowned temple, a pearl grotto, an old
diving bell, the ember vents of the deep). Three are lived in by Village Friends residents (the lightkeeper, the
Tidewatch garrison, the smugglers); the rest are abandoned, with guardians, lore and loot.

It needs Village Friends (residents, conversation window, guards); Village Friends never needs it. It plays well
with the rest of the pack: **Sea Friends** (merfolk and Prismari villages: sites never stand near them, and the
sea folk know the sites), the Plata Clan, the RPG add-on, Not-So-Vanilla Mobs, Turning Seasons, Cave Expansion,
End Friends and Nether Friends.

## The ten sites

| key | name | anchor, depth | lived in? | the hook |
|---|---|---|---|---|
| `lighthouse` | Lighthouse Isle | surface, 4..20 | the lightkeeper | a rocky islet with a tall lighthouse, the keeper's cottage, a jetty; the keeper sells Sea Charts to the other sites |
| `fort` | Tidewatch Fort | surface, 5..18 | 2 knights, 2 archers, a captain | a stone sea fort on a reef: curtain wall, a keep, a beacon brazier, a sea gate with a moored boat |
| `galleon` | The Sunken Galleon | seabed, 12..40 | no | a great three-masted treasure ship broken in two on the sea floor; the hold, the captain's cabin; a drowned captain |
| `whale` | The Whalefall | seabed, 15..50 | no | the colossal skeleton of an ancient whale, a reef of life on its bones; ambergris, a harpoon, a lost diver |
| `temple` | The Drowned Sanctum | seabed, 18..45 | no | a half-buried temple of the Old Tide in prismarine and dark stone; a flooded nave, a sealed reliquary; guardians |
| `grotto` | The Pearl Grotto | seabed, 6..25 | no | a domed sea cave beside a reef: giant clams with pearls, glowing pickles, an old pearl-diver's camp in an air pocket |
| `bell` | Wexley's Diving Bell | seabed, 10..30 | no | a salvage barge riding the surface, a chain down to a copper diving bell with an air pocket; the diving helmet |
| `smugglers` | Smugglers' Rock | surface, 6..20 | 3 smugglers and their chief | a sea stack hollowed into a hidden cove: a dock inside the cave, a sloop, rope bridges, stashed contraband |
| `iceberg` | The Frozen Hold | surface, 10..40 | no | a huge iceberg with an expedition ship locked inside; frozen crew, the expedition's last log |
| `vents` | The Ember Vents | seabed, 22..60 | no | deep-sea hydrothermal chimneys of magma and basalt, tube worms, an Old Tide fire-shrine; black pearls; deep lurkers |

### Lore (shared by every design, dialogue and book)
- **The Tidewatch**: an old order of coast guards (Village Friends knights and archers) who keep sea forts and
  lighthouses against drowned, raiders and storms. Saying: "We keep the light." Banner: blue field, white
  lighthouse-like charge (vanilla patterns: e.g. `stripe_center` + `triangle_top` + `border`). Forts keep a Tide Log.
- **The Lightkeepers**: keepers of lone lighthouses, mostly old Tidewatch hands. Each keeps a **Lamp Log**. They
  trade Sea Charts drawn from what sailors tell them.
- **The Brine Brotherhood**: smugglers who run spices, silks, pearls and worse past the Tidewatch. They hide in
  hollow sea stacks. Saying: "No names on the water."
- **The Old Tide**: a vanished sea people who built in sea-stone (prismarine, dark prismarine) and dark stone;
  their carvings show **one great eye**. Their works: the Drowned Sanctum, the shrine at the Ember Vents, and
  (people say) the ocean monuments. (With Sea Friends installed, the Prismari are their descendants; never say
  so outright in this mod: hint.)
- **The Golden Heron**: a treasure galleon of a lost fleet that went down in a storm with a fortune in its hold;
  its captain, **Captain Ysolde Marrow**, went down with it. Some say she still keeps her ship.
- **The Northward**: an expedition ship that sailed for the frozen north and never came back; it lies locked in
  an iceberg. Its captain was **Arvid Strand**; its log ends mid-sentence.
- **Wexley**: Bartholomew Wexley, an inventor-salvager whose copper diving bell let a diver work the sea floor
  for an hour at a time. His barge is abandoned; the last dive went wrong.
- **Pearl divers** of the coast villages kept a secret grotto; a diver's camp is still there in an air pocket.
- **Sea Friends** (when installed): merfolk and the Prismari know the sea sites and talk about them. Our sites
  never stand near their villages.

## Rarity and placement
- One structure set, `oceanexpansion:sites`: one site per 22 x 22 chunk cell where the sea allows (a cell on land, or whose sea is
  wrong for every site, has none), separation 8; which site is weighted (see each design's `weight`). A site whose biome, depth or sea floor is
  wrong for it lets the set try another kind in the same spot.
- `config/oceanexpansion.json` `"rarity"`: multiplies the spacing (2.0 = half as many per side, 0.5 = more).
- The placement (`oceanexpansion:spread`) keeps clear of: villages 4 chunks, ocean monuments 4, ocean ruins 2,
  shipwrecks 2, Village Friends homesteads 2, Plata dens 2 and warrens 3, Sea Friends merfolk villages 5 and
  Prismari courts 5. A set from a mod that isn't installed is skipped.
- `oceanexpansion:site` (the structure type) samples the sea floor around the chunk: the water depth at the centre
  must be in the site's range and the floor no rougher than its `flatness`; the biome must be one of its biomes.

---

## Design module contract (for whoever builds a site)

Each site is one Python module, `tools/sites/designs/<key>.py`, built with `tools/sites/kit.py` and
`tools/sites/loot.py`. Run from the repo root:

```
python tools/sites/build.py --check --only=<key>    # validates the design (blocks, properties, layouts, loot)
python tools/sites/preview.py <key>                  # isometric cutaways to tools/sites/out/<key>_<piece>.png
python tools/sites/preview.py <key> --full           # whole pieces, uncut
```

Look at your previews (open the PNGs: water is not drawn, so you see inside) and fix what looks wrong.
`designs/_example.py` is a tiny worked example. Do NOT run `build.py` without `--check` (the lead does the
full build). Do not read other mods' code; everything you need is here and in kit.py / loot.py.

### The module
```python
KEY = 'galleon'                 # the structure id: oceanexpansion:galleon
NAME = 'The Sunken Galleon'
FEATURES = ['...']              # one line per notable thing (for the docs and the showcase)
SITE = {
    'anchor': 'seabed',         # 'seabed': the reference height is the sea floor at the centre;
                                # 'surface': the reference height is sea level (y 63, the first air above the water)
    'depth': (12, 40),          # water depth at the centre (blocks of water above the floor), allowed range
    'flatness': 8,              # max difference between the lowest and highest floor sampled out to `radius`
    'radius': 28,               # how far any piece reaches from the centre (blocks)
    'biomes': ['ocean', ...],   # ocean biomes only (see the table / build.OCEANS)
    'weight': 3,                # share of the structure set
    'inhabited': False,         # True: no monster spawns inside the pieces
    'chance': 1.0,              # optional: share of offered spots it takes (<1 keeps a site rarer)
}
LAYOUTS = [                     # one is picked at random; the whole layout is then turned at random (0/90/180/270)
    {'weight': 1, 'pieces': [
        {'piece': 'galleon/stern', 'at': (0, 0), 'turn': 0, 'y': -2, 'mode': 'rigid'},
        {'piece': 'galleon/bow', 'at': (-20, 4), 'turn': 1, 'y': -3, 'mode': 'floor', 'footing': False, 'soft': True},
    ]},
]
LOOT_TABLES = {'galleon/hold': [pool(...), ...], ...}   # every table your chests/barrels/pots use
def pieces(): return [...]      # every Template; names are '<key>/<piece>'
```

### Where pieces go
- `at`: the piece's **centre** (x, z) relative to the site centre. `turn`: quarter turns clockwise.
- `y`: the height of the template's bottom layer (template y = 0) relative to the piece's reference height:
  - `'rigid'`: the site's reference (seabed sites: the floor at the centre + 1, so `y: 0` sits on the floor and
    `y: -2` sinks the bottom two layers into it; surface sites: sea level 63, so `y: -4` puts the bottom 4 rows
    under water).
  - `'floor'`: the sea floor under this piece's own centre + 1 (for pieces that should sit on the floor
    wherever it lies, e.g. a broken-off bow, a buoy).
  - `'surface'`: sea level 63 (e.g. the barge of a seabed site).
- `footing: True`: every block in the piece's bottom layer (y = 0) is extended straight down until it meets the
  sea floor (stone under an island, log piles under a fort, a chain hanging from a barge down to the bell's roof).
  Only put in the bottom layer what should be extended.
- `soft: True` (default): NATURAL blocks (kit.NATURAL: stone, sand, gravel, clay, packed ice...) only replace solid
  ground; where the world is water or air they are skipped. Good for bedding a wreck into the floor. Set
  `soft: False` for pieces built OF natural blocks that must appear in the water or air (an islet, a sea stack,
  an iceberg, a cave dome rising off the floor): then every block is placed.

### Building pieces (kit.Template)
- Coordinates are template-local: x east, y up, z south, all from 0. `Template(name, (sx, sy, sz), wet=True,
  waterline=N)`.
- **Unset cells are structure void**: the world's own block stays there (the sea, the sea floor, the air).
- `'water'` and `'air'` are always placed: `t.flood(a, b)` floods a room (do this inside wrecks and under the
  floor line so rooms are open water, not sand); `t.carve(a, b)` opens dry air (above the sea, or a sealed air
  pocket). An air pocket under water stays dry if water can't flow in: no water above or beside it at the same
  height; water BELOW an air pocket is fine (an upside-down bell / a dome with an open floor works).
- `wet=True`: every block below `waterline` (template y; default the whole template) that can hold water is
  written waterlogged (stairs, slabs, fences, walls, panes, chests, lanterns, coral fans, sea pickles...). Use
  `t.keep_dry(a, b)` for cells below the waterline that are dry (inside an air pocket). For a surface site whose
  piece has `y: -k`, set `waterline=k`.
- Under water: no torches, no fire, no beds, no carpets, no flowers, no doors you need (they work but look odd).
  Light with sea lanterns, sea pickles (`sea_pickle[pickles=1..4]`), glowstone, lanterns, glow lichen,
  conduits, magma. Living coral (`*_coral_block`, `*_coral`, `*_coral_fan`, `*_coral_wall_fan[facing=..]`) only
  lives under water. `kelp`/`kelp_plant` and `seagrass`/`tall_seagrass` are water plants (kelp: stack
  `kelp_plant` with a `kelp` top). Sand and gravel fall if nothing is under them.
- `set`, `fill(a, b, block)`, `walls`, `shell`, `get`. Block specs are vanilla ids with properties:
  `'spruce_stairs[facing=east,half=top]'`. Every block and property is checked against vanilla 26.3.
- Containers: `chest(x, y, z, facing, '<key>/<table>')`, `barrel(...)`, `pot(x, y, z, facing, loot=None,
  sherds=None)`, `minecart`. Each table must be in your LOOT_TABLES.
- `lectern(x, y, z, facing, title, author, pages)`: the place's own book (title <= 32 chars, 3 to 6 short pages,
  ~14 lines of ~19 characters each, <= 700 chars, plain text, in the voice of the place).
- `sign(x, y, z, lines, facing, wood='spruce', wall=True)`; `banner(x, y, z, facing, color, [(pattern, color)])`;
  `item_frame(x, y, z, facing, 'trident')`; `bed(x, y, z, facing, color)` (dry rooms only).
- `spawner(x, y, z, 'minecraft:drowned')` (vanilla mobs only; use sparingly).
- `haunt(x, y, z, kind)`: invisible marker; the first time a player comes within 14 blocks the guardians rise
  there and it vanishes. Leave two blocks of water/air above it. Kinds: `drowned_crew` (3 drowned),
  `drowned_captain` (a captain drowned in gold and a trident + 2 crew), `guardians` (3 guardians), `frozen_crew`
  (3 strays), `deep_lurkers` (Not-So-Vanilla anglers when installed, else guardians).
- `resident(x, y, z, role, facing)`: a Village Friends villager standing at (x, y, z) (feet; the block below solid,
  in a DRY room). Roles: `lightkeeper`, `warden_knight`, `warden_archer`, `captain`, `smuggler`, `smuggler_boss`.
  Give each a bed in a dry room. Job sites: the lightkeeper needs `oceanexpansion:signal_lamp[facing=..]`;
  smugglers need `oceanexpansion:contraband_crate[facing=..]` (one each); knights need
  `villagefriends:training_dummy[facing=..]`, archers `villagefriends:archery_target[facing=..]`. Without one they
  lose the job. Lived-in sites must be lit (`kit.dark_spots(t)` should be (nearly) empty for their dry pieces).
- `creature(x, y, z, 'minecraft:tropical_fish')`, `'minecraft:nautilus'`, `'minecraft:dolphin'`,
  `'minecraft:turtle'`, `'minecraft:axolotl'`, `'minecraft:glow_squid'`, `'minecraft:cod'`... (they stay).
- `entrance(x, y, z)`: note where you come in (for the tests).
- Our blocks: `oceanexpansion:giant_clam[facing=..,pearl=true|false]` (a big clam on the floor; right-click a
  pearl one for a pearl; regrows), `oceanexpansion:tube_worms` (red-plumed vent worms, under water, on any
  solid block), `oceanexpansion:barnacles[facing=up|down|north|..]` (a crust on the face of the block BEHIND it,
  pointing out: on a hull wall facing west put `barnacles[facing=west]` in the water cell west of the wall),
  `oceanexpansion:sea_glass` (frosted teal glass block), `oceanexpansion:sea_glass_pane` (with connections
  north/south/east/west=true|false), `oceanexpansion:signal_lamp[facing]` (the lightkeeper's lamp, gives light
  15), `oceanexpansion:contraband_crate[facing]`.
- Notes: the kit records residents, loot, haunts, books, spawners and creatures in `t.notes`.
- Sizes: one piece up to about 48 x 40 x 48; a whole site within its radius. Under ~60,000 set blocks per site.
  Rotations are random, so nothing may depend on a compass direction.
- Style: Minecraft-vanilla blocks only, medieval-fantasy seafaring, no modern things. Make it feel like a
  *place*: clutter, wear, small stories (a half-eaten meal, a tally scratched on a sign, a broken mast). Avoid
  giant empty boxes and perfect symmetry. Ships: real ship shapes (curved hulls built from stairs/slabs,
  tapering bow, raised sterncastle, masts of stripped logs/fences, yards, rigging of chains/fences, torn sails
  of white/brown wool or banners). Wrecks list a little, are broken and barnacled, half full of sand.

### Loot (loot.py)
`item('gold_ingot', weight, lo, hi)`, `item('oceanexpansion:pearl', ...)`, `empty(weight)`, `pool(rolls(lo, hi),
[entries])`, `enchanted(lo, hi)`, `RANDOM_ENCHANT`, `WORN`, `named("Text")`, `sea_chart(weight)` (a map to the
nearest other site), `treasure_map(weight)`, `trim('tide')`. Our items: `pearl`, `black_pearl` (rare),
`ambergris` (whales only), `diving_helmet` (the bell only, guaranteed once), `storm_glass` (a weather glass),
and our block items. Keep loot exciting but fair: one big prize per site, mostly useful stuff, some flavour.

---

## Per-site briefs

**lighthouse: Lighthouse Isle** (surface 4..20, inhabited, weight 2, radius ~20; ocean, lukewarm_ocean,
warm_ocean, cold_ocean). A rocky islet (`soft: False`, `footing: True`: stone/andesite/tuff/gravel/mossy cobble,
a pebble beach of gravel and sand, a bit of grass and a twisted tree or bushes, tide pools) rising from the sea.
A tall round-ish lighthouse (white and red bands: calcite/white terracotta/red terracotta or bricks, 20-28 tall
above the sea) with a spiral stair inside (dry), a lamp room at the top (glass panes, the
`oceanexpansion:signal_lamp` beside the great light: glowstone or sea lanterns inside a glass lens, a gallery
walkway with railings). The keeper's cottage at its foot (bed, kitchen, lectern "Lamp Log", the keeper's chest
`lighthouse/keeper`, a stores barrel `lighthouse/stores`, fishing gear, a cat bed vibe). A wooden jetty with a
moored boat feel (no entity needed), lanterns. Resident: 1 `lightkeeper` (sleeps in the cottage, works at the
signal lamp). Lit.

**fort: Tidewatch Fort** (surface 5..18, inhabited, weight 2, radius ~24; ocean, lukewarm_ocean, warm_ocean,
cold_ocean). A squat stone sea fort on a reef (`footing: True`): a ring or square curtain wall of stone bricks
rising from the water with crenellations and two corner towers, a central keep (3 floors: barracks with 5 beds,
mess, armory `fort/armory` with 2 training dummies and 2 archery targets, the captain's room with lectern "Tide
Log" and `fort/captain`), stores `fort/stores`, a beacon brazier (campfire) on the keep roof, a sea gate with a
small dock and a portcullis (iron bars), Tidewatch banners, a few ballistae made of blocks (fences, stairs) on the
walls. Residents: 2 `warden_knight`, 2 `warden_archer`, 1 `captain`. Lit.

**galleon: The Sunken Galleon** (seabed 12..40, weight 3, radius ~28; ocean, deep_ocean, lukewarm_ocean,
deep_lukewarm_ocean, warm_ocean, cold_ocean, deep_cold_ocean). The *Golden Heron*: a great three-masted
galleon (~40-50 long) broken in two: the stern half (sterncastle with the captain's cabin: lectern "Last Entry of
the Golden Heron", `galleon/captain` chest, a broken chandelier, gilded trim of gold blocks/stairs if you like)
and the bow half (lying a few blocks away, turned and tilted, figurehead of a heron in white/yellow wool or
quartz). Hold between decks: cargo of barrels, crates, `galleon/cargo` barrels, the treasure hold `galleon/hold`
(the big prize: gold, emeralds, a heart of the sea once in a while). Masts: one standing, two fallen across the
floor; torn sails; cannons? no (medieval): ballista or none. Half-buried in sand, barnacles, kelp, coral starting
to grow. A `drowned_captain` haunt on the deck by the cabin, a `drowned_crew` haunt in the hold. Dim.

**whale: The Whalefall** (seabed 15..50, weight 2, radius ~24; ocean, deep_ocean, cold_ocean, deep_cold_ocean,
lukewarm_ocean, deep_lukewarm_ocean). The skeleton of a colossal whale (~40 long) lying on the floor: skull
(bone blocks, a jaw), spine of bone blocks curving along, arching ribs (bone block arches, some broken and fallen),
flipper bones, tail flukes. Life on the bones: sea pickles, coral fans, kelp, seagrass, tube worms, glow lichen,
tropical fish and a glow squid (`creature`). In the skull or ribcage, `whale/bones` pots and an old harpoon in an
item frame; a lost diver's remains (a skeleton skull, a rusted helmet on an armour-stand-free spot: just blocks
and a chest `whale/drift` with their kit and a note on a sign). `whale/bones` gives **ambergris**. No haunt.
Beautiful and eerie, dim.

**temple: The Drowned Sanctum** (seabed 18..45, weight 2, radius ~24; warm_ocean, lukewarm_ocean,
deep_lukewarm_ocean, ocean, deep_ocean). An Old Tide temple, half-buried (`y` around -4..-6): prismarine bricks,
dark prismarine, prismarine and stone pillars, sea lanterns, carved eyes (a design of one great eye on a wall
using blocks: dark prismarine ring, sea lantern iris, black concrete pupil...). A flooded nave with columns and
side aisles, a grand stair down, an altar with a trident in an item frame (the relic, `temple/altar` chest
under it), offering niches with `temple/offering` pots, a sealed reliquary (behind dark prismarine, reached by a
hidden switch-free crawl or a broken wall), sand drifts, coral reclaiming it. A `guardians` haunt in the nave.
Dim with sea-lantern glows.

**grotto: The Pearl Grotto** (seabed 6..25, weight 2, radius ~16; warm_ocean, lukewarm_ocean, ocean). A domed sea
cave half sunk into the floor (`soft: False` dome of stone/andesite/diorite/calcite, lined with glow lichen,
prismarine crystals feel): inside, a sandy floor with 6-10 `oceanexpansion:giant_clam` (most with pearl=true),
sea pickles everywhere, coral, kelp swaying; an entrance tunnel from the reef side. At the back, raised up into
the dome, the **diver's camp in an air pocket** (dry, `keep_dry`): a ledge of planks, a bed, a barrel
`grotto/camp`, a lantern, a sign tally of pearls, a lectern "Pearling Book". Hidden under the sand somewhere: a
chest `grotto/hoard` (the prize: pearls, a black pearl, gold). No haunt. Lit by pickles.

**bell: Wexley's Diving Bell** (seabed 10..30, weight 2, radius ~14; ocean, lukewarm_ocean, warm_ocean,
cold_ocean). Two parts: the **barge** at the surface (`mode: 'surface'`, `y` about -2: a flat spruce barge with a
winch/crane (logs, fences, a grindstone or stonecutter as the winch), coils of rope (chains), a hut with
Wexley's notes (lectern "Wexley's Dive Book"), barrel `bell/barge`, lanterns; `footing: True` on ONE chain block
in the bottom layer under the crane: it extends down to the bell roof) and the **bell** on the floor (`mode:
'rigid'`, under the barge: an upside-down copper bell, ~7 wide, 6 tall, of copper blocks/cut copper/copper
grates and a few glass portholes, open at the bottom, with an **air pocket** inside (`keep_dry`): a small bench,
a chest `bell/bell` with the **diving helmet** (guaranteed) and salvage, a lantern, a sign "AIR. Breathe slow.");
salvage around it (crates, a toppled cart of ingots, a broken second helmet...). A `drowned_crew` haunt near the
bell (the last dive went wrong). Dim except the bell.

**smugglers: Smugglers' Rock** (surface 6..20, inhabited, weight 2, radius ~18; ocean, lukewarm_ocean,
warm_ocean, cold_ocean). A tall natural sea stack (`soft: False`, `footing: True`: stone, andesite, tuff,
mossy stone, gravel ledges, a few bushes on top, seabirds' nests of hay) whose seaward side opens into a sea cave:
inside, a hidden **cove** with a wooden dock, a moored sloop (a small boat build with a mast and furled sail),
crates and barrels of contraband (`smugglers/stores`), a hidden stash (`smugglers/cache`), rope ladders and
plank walkways up to dry rooms carved in the rock: a bunk room (4 beds), a lookout at the top with a spyglass feel
and a lantern signal, the chief's den (lectern "No Names on the Water" (a ledger), `smugglers/boss` chest).
4 `contraband_crate` job sites. Residents: 3 `smuggler`, 1 `smuggler_boss`. Lit (lanterns).

**iceberg: The Frozen Hold** (surface 10..40, weight 2, radius ~22; frozen_ocean, deep_frozen_ocean, cold_ocean,
deep_cold_ocean). A huge iceberg (`soft: False`, `footing: False`: packed ice, blue ice, ice, snow blocks, powder
snow cracks; ~30-40 across, 12-20 above the sea and deeper below) with the *Northward*, an expedition ship
(~24 long), locked inside it at the waterline: you see its bow and a mast sticking out; a crevasse leads in; the
hull is a dry, frozen space (snow, ice, frost) with the crew's quarters, the hold `iceberg/hold`, the captain's
cabin (lectern "Log of the Northward", `iceberg/captain`). A `frozen_crew` haunt below deck. Dim, cold, quiet.

**vents: The Ember Vents** (seabed 22..60, weight 1, radius ~20; deep_ocean, deep_lukewarm_ocean,
deep_cold_ocean). A field of hydrothermal chimneys on the deep floor: 4-6 tall chimneys of basalt, smooth basalt,
blackstone and magma blocks (magma makes downward bubble columns: that's fine and part of the danger), with
tube worms, glow lichen and dead coral around them, a black-smoker look (tuff, blackstone, a little gilded
blackstone). Among them, a small Old Tide **fire-shrine**: dark prismarine and blackstone, an eye carving, an
altar with `vents/shrine` (black pearls, the prize), `vents/cache` pots. A `deep_lurkers` haunt. Dark, lit by
magma and worms.
