package dev.oceanexpansion.worldgen;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo;

/**
 * Natural blocks in a site (the sand a wreck is bedded in, the stone lining a sea cave...) only replace solid ground:
 * where the world is water or air they are left out, so a wreck sinks into the sea floor instead of floating in a
 * box of sand. Built blocks, water and air are not touched. The list is tools/sites/kit.py's NATURAL.
 */
public final class NaturalProcessor implements StructureProcessor {
    public static final List<String> SOFT = List.of(
            "stone", "deepslate", "tuff", "andesite", "diorite", "granite", "calcite", "amethyst_block", "budding_amethyst",
            "smooth_basalt", "basalt", "dripstone_block", "moss_block", "dirt", "coarse_dirt", "rooted_dirt", "gravel", "clay",
            "mud", "magma_block", "obsidian", "blackstone", "coal_ore", "iron_ore", "copper_ore", "gold_ore", "redstone_ore",
            "lapis_ore", "diamond_ore", "emerald_ore", "deepslate_coal_ore", "deepslate_iron_ore", "deepslate_copper_ore",
            "deepslate_gold_ore", "deepslate_redstone_ore", "deepslate_lapis_ore", "deepslate_diamond_ore", "deepslate_emerald_ore",
            "raw_iron_block", "raw_copper_block", "raw_gold_block", "sand", "red_sand", "sandstone", "packed_ice", "snow_block",
            "podzol", "grass_block");
    public static final NaturalProcessor INSTANCE = new NaturalProcessor();
    public static final MapCodec<NaturalProcessor> CODEC = MapCodec.unit(INSTANCE);

    private Set<Block> blocks;

    private Set<Block> blocks() {
        if (this.blocks == null) this.blocks = SOFT.stream().map(id -> BuiltInRegistries.BLOCK.getValue(Identifier.withDefaultNamespace(id)))
                .collect(Collectors.toUnmodifiableSet());
        return this.blocks;
    }

    @Override
    public StructureBlockInfo processBlock(LevelReader level, BlockPos targetPosition, BlockPos referencePos, BlockPos templateRelativePos,
                                           StructureBlockInfo processed, StructurePlaceSettings settings) {
        if (!this.blocks().contains(processed.state().getBlock())) return processed;
        return solid(level.getBlockState(processed.pos())) ? processed : null;
    }

    /** Ground a natural block may replace: anything but air, fluids and soft plants. */
    static boolean solid(BlockState state) {
        return !state.isAir() && state.getFluidState().isEmpty() && !state.canBeReplaced();
    }

    @Override
    public MapCodec<? extends StructureProcessor> codec() {
        return CODEC;
    }
}
