package dev.oceanexpansion.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Only there so the haunt mark ticks. */
public class HauntBlockEntity extends BlockEntity {
    public HauntBlockEntity(BlockPos pos, BlockState state) { super(OceanBlocks.HAUNT_ENTITY, pos, state); }
}
