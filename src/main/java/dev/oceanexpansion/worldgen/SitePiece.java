package dev.oceanexpansion.worldgen;

import dev.oceanexpansion.OceanExpansion;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

/**
 * One template of a site, turned about its middle. Templates keep their own waterlogging (the build writes it).
 * A {@code soft} piece's natural blocks only replace solid ground ({@link NaturalProcessor}). A piece with a
 * {@code footing} carries every block of its bottom layer straight down until it meets the sea floor, so an islet
 * or a fort stands on the bottom and a hanging chain reaches what is below it.
 */
public class SitePiece extends TemplateStructurePiece {
    public static final StructurePieceType TYPE = SitePiece::new;
    /** How far a footing may reach down. */
    static final int FOOTING_DEPTH = 64;

    private final BlockPos pivot;
    private final boolean soft, footing;
    /** What a footing is built of; null to carry each bottom block itself down (lights are never carried). */
    private final @org.jspecify.annotations.Nullable BlockState footingBlock;

    public SitePiece(StructureTemplateManager templates, Identifier template, BlockPos origin, Rotation rotation, BlockPos pivot,
                     boolean soft, boolean footing, @org.jspecify.annotations.Nullable BlockState footingBlock) {
        super(TYPE, 0, templates, template, template.toString(), settings(rotation, pivot, soft), origin);
        this.pivot = pivot;
        this.soft = soft;
        this.footing = footing;
        this.footingBlock = footingBlock;
    }

    public SitePiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(TYPE, tag, context.structureTemplateManager(), id -> settings(
                Rotation.valueOf(tag.getStringOr("Rot", "NONE")),
                new BlockPos(tag.getIntOr("PX", 0), 0, tag.getIntOr("PZ", 0)), tag.getBooleanOr("Soft", true)));
        this.pivot = new BlockPos(tag.getIntOr("PX", 0), 0, tag.getIntOr("PZ", 0));
        this.soft = tag.getBooleanOr("Soft", true);
        this.footing = tag.getBooleanOr("Footing", false);
        this.footingBlock = tag.read("FootingBlock", BlockState.CODEC).orElse(null);
    }

    private static StructurePlaceSettings settings(Rotation rotation, BlockPos pivot, boolean soft) {
        StructurePlaceSettings s = new StructurePlaceSettings().setRotation(rotation).setRotationPivot(pivot)
                .setLiquidSettings(LiquidSettings.IGNORE_WATERLOGGING).setFinalizeEntities(true);
        if (soft) s.addProcessor(NaturalProcessor.INSTANCE);
        s.addProcessor(DRY_ABOVE_SEA);
        return s;
    }

    /**
     * A template's water never stands above the sea: a tower that rises out of the waves is dry up there (its water
     * cells are air, nothing in them is waterlogged) instead of pouring down its sides.
     */
    static final net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor DRY_ABOVE_SEA =
            new net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor() {
        @Override
        public net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo processBlock(
                net.minecraft.world.level.LevelReader level, BlockPos target, BlockPos reference, BlockPos relative,
                net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo info, StructurePlaceSettings settings) {
            if (info.pos().getY() < level.getSeaLevel()) return info;
            BlockState state = info.state();
            if (state.getBlock() == Blocks.WATER)
                return new net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo(info.pos(), Blocks.AIR.defaultBlockState(), null);
            if (state.hasProperty(BlockStateProperties.WATERLOGGED) && state.getValue(BlockStateProperties.WATERLOGGED))
                return new net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo(info.pos(),
                        state.setValue(BlockStateProperties.WATERLOGGED, false), info.nbt());
            return info;
        }

        @Override
        public com.mojang.serialization.MapCodec<? extends net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor> codec() {
            return NaturalProcessor.CODEC;   // never written out: the piece adds it again when it loads
        }
    };

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        super.addAdditionalSaveData(context, tag);
        tag.putString("Rot", this.placeSettings.getRotation().name());
        tag.putInt("PX", this.pivot.getX());
        tag.putInt("PZ", this.pivot.getZ());
        tag.putBoolean("Soft", this.soft);
        tag.putBoolean("Footing", this.footing);
        if (this.footingBlock != null) tag.store("FootingBlock", BlockState.CODEC, this.footingBlock);
    }

    @Override
    protected void handleDataMarker(String marker, BlockPos pos, ServerLevelAccessor level, RandomSource random, BoundingBox box) {}

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                            BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
        super.postProcess(level, structures, generator, random, chunkBox, chunkPos, pivot);
        if (!this.footing) return;
        BoundingBox box = this.boundingBox;
        int y0 = box.minY();
        BlockPos.MutableBlockPos at = new BlockPos.MutableBlockPos();
        for (int x = Math.max(box.minX(), chunkBox.minX()); x <= Math.min(box.maxX(), chunkBox.maxX()); x++) {
            for (int z = Math.max(box.minZ(), chunkBox.minZ()); z <= Math.min(box.maxZ(), chunkBox.maxZ()); z++) {
                BlockState top = level.getBlockState(at.set(x, y0, z));
                if (top.isAir() || top.getBlock() == Blocks.WATER || top.hasBlockEntity() || top.canBeReplaced()) continue;
                if (this.footingBlock != null) top = this.footingBlock;
                else if (top.getLightEmission() > 0) continue;
                for (int y = y0 - 1; y >= Math.max(level.getMinY(), y0 - FOOTING_DEPTH); y--) {
                    BlockState below = level.getBlockState(at.set(x, y, z));
                    if (!open(below)) break;
                    BlockState put = top;
                    if (put.hasProperty(BlockStateProperties.WATERLOGGED))
                        put = put.setValue(BlockStateProperties.WATERLOGGED, below.getFluidState().is(FluidTags.WATER));
                    level.setBlock(at, put, 2);
                }
            }
        }
    }

    /** What a footing may fill: open water or air, sea plants, bubbles. */
    static boolean open(BlockState s) {
        return s.isAir() || s.getBlock() == Blocks.WATER || s.getBlock() == Blocks.BUBBLE_COLUMN || s.getBlock() == Blocks.SEAGRASS
                || s.getBlock() == Blocks.TALL_SEAGRASS || s.getBlock() == Blocks.KELP || s.getBlock() == Blocks.KELP_PLANT
                || (s.canBeReplaced() && !s.getFluidState().is(FluidTags.LAVA));
    }

    /** The template this piece places (namespace:path). */
    public String templateId() { return this.templateName; }
}
