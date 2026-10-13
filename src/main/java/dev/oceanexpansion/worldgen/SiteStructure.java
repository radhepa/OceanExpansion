package dev.oceanexpansion.worldgen;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.QuartPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/**
 * A sea site: a few block templates laid out around a centre (written by tools/sites/build.py), the whole layout
 * turned at random.
 *
 * <p>Before it is built it samples the sea floor around the chunk: the water at the centre must be as deep as the
 * site wants, the floor no rougher than its {@code flatness} out to its {@code radius}, and all of it under water.
 * Each piece is then set at its height: {@code rigid} pieces from the site's reference (the floor at the centre
 * for a {@code seabed} site, sea level for a {@code surface} site), {@code floor} pieces on the floor under their
 * own centre, {@code surface} pieces from sea level. A piece with a footing has its bottom layer carried down to
 * the floor (see {@link SitePiece}).
 */
public class SiteStructure extends Structure {
    public record Depth(int min, int max) {
        public static final Codec<Depth> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.intRange(0, 200).fieldOf("min").forGetter(Depth::min),
                Codec.intRange(0, 200).fieldOf("max").forGetter(Depth::max)).apply(i, Depth::new));
    }

    public record Spot(Identifier template, int x, int z, int y, int turn, String mode, boolean footing, boolean soft,
                       Optional<BlockState> footingBlock) {
        public static final Codec<Spot> CODEC = RecordCodecBuilder.create(i -> i.group(
                Identifier.CODEC.fieldOf("template").forGetter(Spot::template),
                Codec.INT.fieldOf("x").forGetter(Spot::x), Codec.INT.fieldOf("z").forGetter(Spot::z),
                Codec.INT.optionalFieldOf("y", 0).forGetter(Spot::y),
                Codec.intRange(0, 3).optionalFieldOf("turn", 0).forGetter(Spot::turn),
                Codec.STRING.optionalFieldOf("mode", "rigid").forGetter(Spot::mode),
                Codec.BOOL.optionalFieldOf("footing", false).forGetter(Spot::footing),
                Codec.BOOL.optionalFieldOf("soft", true).forGetter(Spot::soft),
                BlockState.CODEC.optionalFieldOf("footing_block").forGetter(Spot::footingBlock)).apply(i, Spot::new));
    }

    public record Layout(int weight, List<Spot> pieces, List<List<List<Integer>>> paths) {
        public static final Codec<Layout> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.intRange(1, 1000).optionalFieldOf("weight", 1).forGetter(Layout::weight),
                Spot.CODEC.listOf().fieldOf("pieces").forGetter(Layout::pieces),
                Codec.INT.listOf().listOf().listOf().optionalFieldOf("paths", List.of()).forGetter(Layout::paths)).apply(i, Layout::new));
    }

    public record PathStyle(List<BlockState> blocks, Optional<BlockState> light, int every, int width) {
        public static final Codec<PathStyle> CODEC = RecordCodecBuilder.create(i -> i.group(
                BlockState.CODEC.listOf().fieldOf("blocks").forGetter(PathStyle::blocks),
                BlockState.CODEC.optionalFieldOf("light").forGetter(PathStyle::light),
                Codec.intRange(2, 64).optionalFieldOf("every", 7).forGetter(PathStyle::every),
                Codec.intRange(1, 4).optionalFieldOf("width", 2).forGetter(PathStyle::width)).apply(i, PathStyle::new));
    }

    public static final MapCodec<SiteStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            settingsCodec(i),
            Codec.STRING.fieldOf("anchor").forGetter(s -> s.anchor),
            Depth.CODEC.fieldOf("depth").forGetter(s -> s.depth),
            Codec.intRange(0, 64).optionalFieldOf("flatness", 8).forGetter(s -> s.flatness),
            Codec.intRange(4, 96).optionalFieldOf("radius", 16).forGetter(s -> s.radius),
            Layout.CODEC.listOf().fieldOf("layouts").forGetter(s -> s.layouts),
            PathStyle.CODEC.optionalFieldOf("path").forGetter(s -> s.path),
            Codec.floatRange(0F, 1F).optionalFieldOf("chance", 1F).forGetter(s -> s.chance)
    ).apply(i, SiteStructure::new));
    public static final StructureType<SiteStructure> TYPE = () -> CODEC;

    private final String anchor;
    private final Depth depth;
    private final int flatness, radius;
    private final List<Layout> layouts;
    private final Optional<PathStyle> path;
    private final float chance;

    public SiteStructure(StructureSettings settings, String anchor, Depth depth, int flatness, int radius,
                         List<Layout> layouts, Optional<PathStyle> path, float chance) {
        super(settings);
        this.anchor = anchor;
        this.depth = depth;
        this.flatness = flatness;
        this.radius = radius;
        this.layouts = layouts;
        this.path = path;
        this.chance = chance;
    }

    @Override public StructureType<?> type() { return TYPE; }

    public Depth depth() { return this.depth; }
    public String anchor() { return this.anchor; }

    /** The top solid block of the sea floor (or of the land) at (x, z). */
    static int floor(GenerationContext c, int x, int z) {
        return c.chunkGenerator().getFirstOccupiedHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, c.heightAccessor(), c.randomState());
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        if (this.chance < 1F && context.random().nextFloat() >= this.chance) return Optional.empty();
        // The chunk the placement offers may sit on a coast or a rough floor: try a few spots round it.
        for (int[] offset : SPOTS) {
            Optional<GenerationStub> stub = this.at(context, context.chunkPos().getMiddleBlockX() + offset[0], context.chunkPos().getMiddleBlockZ() + offset[1]);
            if (stub.isPresent()) return stub;
        }
        return Optional.empty();
    }

    /** Where to look for a good spot, from the middle of the offered chunk outward. */
    static final int[][] SPOTS = {{0, 0}, {24, 0}, {-24, 0}, {0, 24}, {0, -24}, {20, 20}, {-20, -20}, {20, -20}, {-20, 20}};

    private Optional<GenerationStub> at(GenerationContext context, int cx, int cz) {
        int sea = context.chunkGenerator().getSeaLevel();
        int centre = floor(context, cx, cz);
        int water = sea - 1 - centre;
        if (water < this.depth.min() || water > this.depth.max()) return Optional.empty();
        int lo = centre, hi = centre;
        for (int ring : new int[]{this.radius / 2, this.radius}) {
            for (int k = 0; k < 8; k++) {
                double a = k * Math.PI / 4;
                int f = floor(context, cx + (int) Math.round(Math.cos(a) * ring), cz + (int) Math.round(Math.sin(a) * ring));
                if (f >= sea - 2) return Optional.empty();
                lo = Math.min(lo, f);
                hi = Math.max(hi, f);
            }
        }
        if (hi - lo > this.flatness) return Optional.empty();
        var biome = context.biomeResolver().getNoiseBiome(QuartPos.fromBlock(cx), QuartPos.fromBlock(centre + 1), QuartPos.fromBlock(cz));
        if (!context.validBiome().test(biome)) return Optional.empty();

        RandomSource random = context.random();
        Layout layout = pick(this.layouts, random);
        int turn = random.nextInt(4);
        int reference = this.anchor.equals("surface") ? sea : centre + 1;
        List<StructurePiece> pieces = new ArrayList<>();
        for (Spot spot : layout.pieces()) {
            StructureTemplate template = context.structureTemplateManager().getOrCreate(spot.template());
            var size = template.getSize();
            int[] at = rotate(spot.x(), spot.z(), turn);
            int x = cx + at[0], z = cz + at[1];
            int pieceTurn = (spot.turn() + turn) & 3;
            int y = switch (spot.mode()) {
                case "floor" -> floorUnder(context, x, z, size.getX(), size.getZ(), pieceTurn) + 1 + spot.y();
                case "surface" -> sea + spot.y();
                default -> reference + spot.y();
            };
            BlockPos pivot = new BlockPos(size.getX() / 2, 0, size.getZ() / 2);
            BlockPos origin = new BlockPos(x - pivot.getX(), y, z - pivot.getZ());
            pieces.add(new SitePiece(context.structureTemplateManager(), spot.template(), origin, ROTATIONS[pieceTurn], pivot,
                    spot.soft(), spot.footing(), spot.footingBlock().orElse(null)));
        }
        if (this.path.isPresent() && !layout.paths().isEmpty()) {
            List<int[]> points = new ArrayList<>();
            List<Integer> ends = new ArrayList<>();
            for (List<List<Integer>> line : layout.paths()) {
                for (List<Integer> p : line) {
                    int[] r = rotate(p.get(0), p.get(1), turn);
                    points.add(new int[]{cx + r[0], cz + r[1]});
                }
                ends.add(points.size());
            }
            pieces.add(new PathPiece(points, ends, this.path.get(), lo - 2, sea));
        }
        BlockPos at = new BlockPos(cx, centre + 1, cz);
        return Optional.of(new GenerationStub(at, (StructurePiecesBuilder builder) -> pieces.forEach(builder::addPiece)));
    }

    static final Rotation[] ROTATIONS = {Rotation.NONE, Rotation.CLOCKWISE_90, Rotation.CLOCKWISE_180, Rotation.COUNTERCLOCKWISE_90};

    /** (dx, dz) turned clockwise (seen from above) by quarter turns, as a template rotates about its pivot. */
    public static int[] rotate(int dx, int dz, int turn) {
        for (int k = 0; k < (turn & 3); k++) { int t = dx; dx = -dz; dz = t; }
        return new int[]{dx, dz};
    }

    /** The middle of the floor heights under a piece's centre and the four corners of its footprint. */
    private static int floorUnder(GenerationContext c, int x, int z, int sx, int sz, int turn) {
        int hx = (turn & 1) == 0 ? sx / 2 : sz / 2, hz = (turn & 1) == 0 ? sz / 2 : sx / 2;
        int[] h = {floor(c, x, z), floor(c, x - hx, z - hz), floor(c, x + hx, z - hz), floor(c, x - hx, z + hz), floor(c, x + hx, z + hz)};
        Arrays.sort(h);
        return h[2];
    }

    private static Layout pick(List<Layout> layouts, RandomSource random) {
        int total = layouts.stream().mapToInt(Layout::weight).sum();
        int roll = random.nextInt(total);
        for (Layout l : layouts) { roll -= l.weight(); if (roll < 0) return l; }
        return layouts.getFirst();
    }
}
