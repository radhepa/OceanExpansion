package dev.oceanexpansion.block;

import dev.oceanexpansion.item.OceanItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * A giant clam on the sea floor. One with a pearl gives it up to a hand that reaches in (one time in ten a black
 * pearl); under water it grows a new one in time.
 */
public class GiantClamBlock extends WaterFacingBlock {
    public static final BooleanProperty PEARL = BooleanProperty.create("pearl");

    public GiantClamBlock(Properties properties) {
        super(properties, Block.box(1, 0, 2, 15, 8, 14));
        this.registerDefaultState(this.defaultBlockState().setValue(PEARL, true));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(PEARL);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!state.getValue(PEARL)) return InteractionResult.PASS;
        if (level instanceof ServerLevel server) {
            ItemStack pearl = new ItemStack(server.getRandom().nextInt(10) == 0 ? OceanItems.BLACK_PEARL : OceanItems.PEARL);
            if (!player.getInventory().add(pearl)) Block.popResource(server, pos.above(), pearl);
            server.setBlock(pos, state.setValue(PEARL, false), 3);
            server.playSound(null, pos, SoundEvents.SHULKER_CLOSE, SoundSource.BLOCKS, .8F, 1.4F);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected boolean isRandomlyTicking(BlockState state) { return !state.getValue(PEARL) && state.getValue(WATERLOGGED); }

    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (random.nextInt(12) == 0) level.setBlock(pos, state.setValue(PEARL, true), 3);
    }
}
