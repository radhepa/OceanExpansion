package dev.oceanexpansion.worldgen;

import java.util.List;
import java.util.Optional;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.oceanexpansion.OceanConfig;
import net.minecraft.core.Holder;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.LegacyRandomSource;
import net.minecraft.world.level.levelgen.WorldgenRandom;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadType;

/**
 * Vanilla's random spread with two changes. Its grid is stretched by the player's {@code rarity} setting
 * ({@link OceanConfig}): 2.0 makes sites half as common along each side, 0.5 twice as common. And it keeps
 * clear of other structure sets: {@code avoid} lists sets by id with how many chunks to keep from anywhere they
 * could stand (villages, ocean monuments, Village Friends homesteads, the Sea Friends' villages...). A
 * set that isn't loaded (a mod that isn't installed) is skipped. It is still a random spread, so /locate and
 * exploration maps find sites.
 */
public class SpreadPlacement extends RandomSpreadStructurePlacement {
    public record Avoid(ResourceKey<StructureSet> set, int chunks) {
        public static final Codec<Avoid> CODEC = RecordCodecBuilder.create(i -> i.group(
                ResourceKey.codec(Registries.STRUCTURE_SET).fieldOf("set").forGetter(Avoid::set),
                Codec.intRange(1, 16).fieldOf("chunks").forGetter(Avoid::chunks)).apply(i, Avoid::new));
    }

    public static final MapCodec<SpreadPlacement> CODEC = RecordCodecBuilder.<SpreadPlacement>mapCodec(i -> placementCodec(i).and(i.group(
            Codec.intRange(0, 4096).fieldOf("spacing").forGetter(p -> p.baseSpacing),
            Codec.intRange(0, 4096).fieldOf("separation").forGetter(p -> p.baseSeparation),
            RandomSpreadType.CODEC.optionalFieldOf("spread_type", RandomSpreadType.LINEAR).forGetter(SpreadPlacement::spreadType),
            Avoid.CODEC.listOf().optionalFieldOf("avoid", List.of()).forGetter(p -> p.avoid)
    )).apply(i, SpreadPlacement::new)).validate(p -> p.baseSpacing <= p.baseSeparation
            ? DataResult.error(() -> "Spacing has to be larger than separation")
            : DataResult.success(p));

    private final int baseSpacing, baseSeparation, spacing, separation;
    private final List<Avoid> avoid;

    public SpreadPlacement(Vec3i locateOffset, FrequencyReductionMethod frequencyReductionMethod, float frequency, int salt,
                          Optional<ExclusionZone> exclusionZone, int spacing, int separation, RandomSpreadType spreadType, List<Avoid> avoid) {
        super(locateOffset, frequencyReductionMethod, frequency, salt, exclusionZone, spacing, separation, spreadType);
        this.baseSpacing = spacing;
        this.baseSeparation = separation;
        int[] scaled = OceanConfig.scaled(spacing, separation, OceanConfig.get().rarity());
        this.spacing = scaled[0];
        this.separation = scaled[1];
        this.avoid = List.copyOf(avoid);
    }

    @Override public int spacing() { return this.spacing; }
    @Override public int separation() { return this.separation; }

    @Override
    public ChunkPos getPotentialStructureChunk(long seed, int sourceX, int sourceZ) {
        int gridX = Math.floorDiv(sourceX, this.spacing), gridZ = Math.floorDiv(sourceZ, this.spacing);
        WorldgenRandom random = new WorldgenRandom(new LegacyRandomSource(0L));
        random.setLargeFeatureWithSalt(seed, gridX, gridZ, this.salt());
        int limit = this.spacing - this.separation;
        int spreadX = this.spreadType().evaluate(random, limit), spreadZ = this.spreadType().evaluate(random, limit);
        return new ChunkPos(gridX * this.spacing + spreadX, gridZ * this.spacing + spreadZ);
    }

    /**
     * Set while this placement asks other sets where they could stand. Sets that keep clear of each other (Reef Towns
     * and Prism Courts, Sea Friends and Ocean Expansion) would otherwise ask each other back forever: the inner ask
     * only looks at the grid.
     */
    private static final ThreadLocal<Boolean> ASKING = ThreadLocal.withInitial(() -> false);

    @Override
    protected boolean isPlacementChunk(ChunkGeneratorStructureState state, int x, int z) {
        ChunkPos chunk = this.getPotentialStructureChunk(state.getLevelSeed(), x, z);
        if (chunk.x() != x || chunk.z() != z) return false;
        if (ASKING.get()) return true;
        ASKING.set(true);
        try {
            for (Avoid a : this.avoid) {
                for (Holder<StructureSet> set : state.possibleStructureSets()) {
                    if (set.is(a.set()) && state.hasStructureChunkInRange(set, x, z, a.chunks())) return false;
                }
            }
            return true;
        } finally {
            ASKING.set(false);
        }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    @Override
    public MapCodec<RandomSpreadStructurePlacement> codec() {
        return (MapCodec) CODEC;
    }
}
