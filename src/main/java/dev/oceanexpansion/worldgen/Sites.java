package dev.oceanexpansion.worldgen;

import java.util.List;

import dev.oceanexpansion.OceanExpansion;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.levelgen.structure.Structure;

/** The ten sites (data/oceanexpansion/worldgen, written by tools/sites/build.py) and the worldgen types they use. */
public final class Sites {
    private Sites() {}

    /** Every site, in the order the docs list them. */
    public static final List<String> KEYS = List.of("lighthouse", "fort", "galleon", "whale", "temple", "grotto", "bell", "smugglers",
            "iceberg", "vents");
    public static final TagKey<Structure> ALL = TagKey.create(Registries.STRUCTURE, OceanExpansion.id("sites"));
    public static final TagKey<Structure> INHABITED = TagKey.create(Registries.STRUCTURE, OceanExpansion.id("inhabited"));

    public static ResourceKey<Structure> key(String site) {
        return ResourceKey.create(Registries.STRUCTURE, OceanExpansion.id(site));
    }

    /** What residents call a site when they tell you about it (with its article). */
    public static String describe(String site) {
        return switch (site) {
            case "lighthouse" -> "a lighthouse on a rock, with a keeper still in it";
            case "fort" -> "a Tidewatch sea fort";
            case "galleon" -> "the wreck of a great galleon, the Golden Heron by the talk";
            case "whale" -> "the bones of a whale as long as a street";
            case "temple" -> "a drowned temple of the Old Tide";
            case "grotto" -> "a sea cave full of giant clams, the pearl divers' grotto";
            case "bell" -> "old Wexley's diving barge, and his bell under it";
            case "smugglers" -> "a hollow sea stack where the Brine Brotherhood hides";
            case "iceberg" -> "an iceberg with a ship frozen into it";
            case "vents" -> "the deep vents where the sea floor smokes and glows";
            default -> "something strange";
        };
    }

    public static void register() {
        Registry.register(BuiltInRegistries.STRUCTURE_TYPE, OceanExpansion.id("site"), SiteStructure.TYPE);
        Registry.register(BuiltInRegistries.STRUCTURE_PLACEMENT, OceanExpansion.id("spread"), SpreadPlacement.CODEC);
        Registry.register(BuiltInRegistries.STRUCTURE_PROCESSOR, OceanExpansion.id("natural"), NaturalProcessor.CODEC);
        Registry.register(BuiltInRegistries.STRUCTURE_PIECE, OceanExpansion.id("site"), SitePiece.TYPE);
        Registry.register(BuiltInRegistries.STRUCTURE_PIECE, OceanExpansion.id("path"), PathPiece.TYPE);
    }
}
