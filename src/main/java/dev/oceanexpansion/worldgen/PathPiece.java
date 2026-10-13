package dev.oceanexpansion.worldgen;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;

/**
 * Paths laid on the sea floor between buildings: the floor's top block (sand, gravel, dirt, stone...) is swapped for a
 * path block, with a light now and then at the edge. Only natural floor is touched, never a building.
 */
public class PathPiece extends StructurePiece {
    public static final StructurePieceType TYPE = PathPiece::new;

    private final List<int[]> points;
    private final List<Integer> ends;
    private final SiteStructure.PathStyle style;

    public PathPiece(List<int[]> points, List<Integer> ends, SiteStructure.PathStyle style, int minY, int maxY) {
        super(TYPE, 0, box(points, style.width(), minY, maxY));
        this.points = points;
        this.ends = ends;
        this.style = style;
    }

    public PathPiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(TYPE, tag);
        int[] xs = tag.getIntArray("X").orElse(new int[0]), zs = tag.getIntArray("Z").orElse(new int[0]);
        this.points = new ArrayList<>();
        for (int i = 0; i < xs.length; i++) this.points.add(new int[]{xs[i], zs[i]});
        this.ends = new ArrayList<>();
        for (int e : tag.getIntArray("Ends").orElse(new int[0])) this.ends.add(e);
        this.style = tag.read("Style", SiteStructure.PathStyle.CODEC).orElse(
                new SiteStructure.PathStyle(List.of(Blocks.GRAVEL.defaultBlockState()), Optional.empty(), 7, 2));
    }

    private static BoundingBox box(List<int[]> points, int width, int minY, int maxY) {
        int x0 = Integer.MAX_VALUE, z0 = Integer.MAX_VALUE, x1 = Integer.MIN_VALUE, z1 = Integer.MIN_VALUE;
        for (int[] p : points) { x0 = Math.min(x0, p[0]); z0 = Math.min(z0, p[1]); x1 = Math.max(x1, p[0]); z1 = Math.max(z1, p[1]); }
        return new BoundingBox(x0 - width - 1, minY, z0 - width - 1, x1 + width + 1, maxY, z1 + width + 1);
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        tag.putIntArray("X", this.points.stream().mapToInt(p -> p[0]).toArray());
        tag.putIntArray("Z", this.points.stream().mapToInt(p -> p[1]).toArray());
        tag.putIntArray("Ends", this.ends.stream().mapToInt(Integer::intValue).toArray());
        tag.store("Style", SiteStructure.PathStyle.CODEC, this.style);
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                            BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
        int start = 0, step = 0;
        int half = this.style.width() / 2;
        for (int end : this.ends) {
            for (int i = start; i + 1 < end; i++) {
                int[] a = this.points.get(i), b = this.points.get(i + 1);
                int n = Math.max(1, (int) Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) * 2));
                for (int k = 0; k <= n; k++, step++) {
                    double t = k / (double) n;
                    int x = (int) Math.round(a[0] + (b[0] - a[0]) * t), z = (int) Math.round(a[1] + (b[1] - a[1]) * t);
                    for (int dx = -half; dx <= this.style.width() - 1 - half; dx++)
                        for (int dz = -half; dz <= this.style.width() - 1 - half; dz++) this.pave(level, chunkBox, x + dx, z + dz);
                    if (this.style.light().isPresent() && step % (this.style.every() * 2) == 0)
                        this.light(level, chunkBox, x + half + 1, z, this.style.light().get());
                }
            }
            start = end;
        }
    }

    private void pave(WorldGenLevel level, BoundingBox chunkBox, int x, int z) {
        if (!chunkBox.isInside(x, chunkBox.minY(), z)) return;
        int y = level.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z) - 1;
        BlockPos pos = new BlockPos(x, y, z);
        if (!natural(level.getBlockState(pos)) || !level.getFluidState(pos.above()).isSource()) return;
        List<BlockState> blocks = this.style.blocks();
        level.setBlock(pos, blocks.get(Math.floorMod(x * 31 + z * 17 + (x ^ z), blocks.size())), 2);
    }

    private void light(WorldGenLevel level, BoundingBox chunkBox, int x, int z, BlockState light) {
        if (!chunkBox.isInside(x, chunkBox.minY(), z)) return;
        int y = level.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z);
        BlockPos pos = new BlockPos(x, y, z);
        if (!natural(level.getBlockState(pos.below())) || level.getBlockState(pos).getBlock() != Blocks.WATER) return;
        if (light.canSurvive(level, pos)) {
            BlockState put = light.hasProperty(BlockStateProperties.WATERLOGGED) ? light.setValue(BlockStateProperties.WATERLOGGED, true) : light;
            level.setBlock(light.isSolidRender() ? pos.below() : pos, put, 2);
        }
    }

    /** The sea floor's own top blocks. */
    static boolean natural(BlockState s) {
        return s.is(BlockTags.SAND) || s.is(BlockTags.DIRT) || s.is(Blocks.GRAVEL) || s.is(Blocks.CLAY) || s.is(Blocks.STONE)
                || s.is(Blocks.ANDESITE) || s.is(Blocks.DIORITE) || s.is(Blocks.GRANITE) || s.is(Blocks.TUFF) || s.is(Blocks.DEEPSLATE)
                || s.is(Blocks.MUD) || s.is(Blocks.SANDSTONE) || s.is(Blocks.MAGMA_BLOCK) || s.is(Blocks.PACKED_ICE);
    }
}
