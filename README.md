<p align="center">
  <img src="docs/readme/banner.svg" width="100%" alt="Ocean Expansion: ten rare places to find at sea">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Minecraft-26.3-cfe9ff?style=for-the-badge&labelColor=0a2448" alt="Minecraft 26.3">
  <img src="https://img.shields.io/badge/Fabric-0.19.5-e9a774?style=for-the-badge&labelColor=0a2448" alt="Fabric Loader 0.19.5">
  <img src="https://img.shields.io/badge/version-1.0.0-d93a3a?style=for-the-badge&labelColor=0a2448" alt="version 1.0.0">
  <img src="https://img.shields.io/badge/needs-Village_Friends_2.29%2B-ffd36a?style=for-the-badge&labelColor=0a2448" alt="needs Village Friends 2.29+">
  <img src="https://img.shields.io/badge/license-MIT-fff6fb?style=for-the-badge&labelColor=0a2448" alt="MIT license">
</p>

<p align="center"><b>A <a href="https://github.com/radhepa/Village-Friends-Minecraft-Mod">Village Friends</a> add-on that makes the sea worth exploring.</b><br>
Ten rare sites to find at sea, from a lighthouse on a rocky islet to black pearls in the deep.<br>
Three of them are lived in, and their people will tell you where the others are.</p>

---

## The ten sites

<p align="center">
  <img src="docs/readme/lighthouse-isle.svg" width="49%" alt="Lighthouse Isle">
  <img src="docs/readme/tidewatch-fort.svg" width="49%" alt="Tidewatch Fort">
  <img src="docs/readme/smugglers-rock.svg" width="49%" alt="Smugglers' Rock">
  <img src="docs/readme/sunken-galleon.svg" width="49%" alt="The Sunken Galleon">
  <img src="docs/readme/the-whalefall.svg" width="49%" alt="The Whalefall">
  <img src="docs/readme/drowned-sanctum.svg" width="49%" alt="The Drowned Sanctum">
  <img src="docs/readme/pearl-grotto.svg" width="49%" alt="The Pearl Grotto">
  <img src="docs/readme/diving-bell.svg" width="49%" alt="Wexley's Diving Bell">
  <img src="docs/readme/frozen-hold.svg" width="49%" alt="The Frozen Hold">
  <img src="docs/readme/ember-vents.svg" width="49%" alt="The Ember Vents">
</p>

| Site | Where | What you find |
|---|---|---|
| Lighthouse Isle | on a rocky islet | a lighthouse and its keeper, who sells Sea Charts to the other sites |
| Tidewatch Fort | a sea fort on a reef | a garrison of knights and archers, their captain and the Tide Log |
| Smugglers' Rock | a hollow sea stack | the Brine Brotherhood's hidden cove, its sloop, its stash and its chief |
| The Sunken Galleon | on the sea floor | the *Golden Heron*, broken in two; its strongroom; its drowned captain |
| The Whalefall | on the sea floor | the bones of a colossal whale, alive with coral; ambergris |
| The Drowned Sanctum | half-buried | a temple of the Old Tide: a great eye, a flooded nave, a sealed reliquary |
| The Pearl Grotto | a sea cave | giant clams with pearls, and a pearl diver's camp in an air pocket |
| Wexley's Diving Bell | surface and floor | a salvage barge, and a copper bell with air inside and the diving helmet |
| The Frozen Hold | in frozen seas | the expedition ship *Northward*, locked in an iceberg |
| The Ember Vents | the deep ocean | smoking chimneys, tube worms, an Old Tide fire-shrine, black pearls |

## The people at sea

The lightkeeper, the Tidewatch and the smugglers are Village Friends residents: talk to them, trade, make friends.
They have their own lines and tell you about the nearest other site.

<table>
  <tr>
    <td width="33%"><img src="docs/readme/shots/lightkeeper.jpg" alt="The lightkeeper"><br><sub>The keeper's cottage under the light.</sub></td>
    <td width="33%"><img src="docs/readme/shots/tidewatch.jpg" alt="The Tidewatch"><br><sub>The Tidewatch keep.</sub></td>
    <td width="33%"><img src="docs/readme/shots/smugglers.jpg" alt="The smugglers"><br><sub>Smugglers' Rock, up close.</sub></td>
  </tr>
  <tr>
    <td width="33%"><img src="docs/readme/shots/fort-inside.jpg" alt="Inside the fort"><br><sub>Inside Tidewatch Fort.</sub></td>
    <td width="33%"><img src="docs/readme/shots/bell-inside.jpg" alt="Inside the diving bell"><br><sub>Air inside Wexley's bell.</sub></td>
    <td width="33%"><img src="docs/readme/shots/northward.jpg" alt="The Northward"><br><sub>Aboard the <i>Northward</i>.</sub></td>
  </tr>
</table>

## New blocks and items

Giant clams (reach in for a pearl; they grow another), tube worms, barnacles, sea glass and its pane, the
lightkeeper's signal lamp and the smugglers' contraband crate (their job sites), pearls, black pearls, ambergris, the
**storm glass** (it reads the weather ahead) and the **diving helmet** (breathe under water while you wear it).

---

## Requirements

- Minecraft 26.3, Fabric Loader 0.19.5+, Fabric API
- [Village Friends](https://github.com/radhepa/Village-Friends-Minecraft-Mod) 2.29.0 or newer
- Plays well with [Sea Friends](https://github.com/radhepa/Sea-Friends) (its villages and our sites keep apart, and
  the sea folk know the sites) and the rest of the Village Friends modpack.

## Settings

`config/oceanexpansion.json`: `rarity` (1.0; 2.0 = half as many per side, 0.5 = twice as many) and `rumors`.

## Building

`build.ps1` (or `gradlew build`).

| What | How |
|---|---|
| The sites | `python tools/sites/build.py` |
| Dialogue | `python tools/talk/talk.py` |
| Block and item art | `python tools/art/blocks.py` |

See [DESIGN.md](DESIGN.md).

## License

[MIT](LICENSE). The README art in `docs/readme/` is drawn from in-game screenshots.
