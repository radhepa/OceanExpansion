package dev.oceanexpansion.block;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

import dev.oceanexpansion.OceanExpansion;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

/** The sites' blocks: the clam, the vent worms, barnacles, sea glass, the two job sites and the haunt mark. */
public final class OceanBlocks {
    private OceanBlocks() {}

    /** Every block item, in creative-tab order. */
    public static final List<Item> ITEMS = new ArrayList<>();

    public static final GiantClamBlock GIANT_CLAM = register("giant_clam", GiantClamBlock::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_PINK).strength(1.5F).sound(SoundType.BONE_BLOCK).noOcclusion(), true);
    public static final TubeWormsBlock TUBE_WORMS = register("tube_worms", TubeWormsBlock::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_RED).noCollision().instabreak().sound(SoundType.WET_GRASS).noOcclusion()
            .pushReaction(PushReaction.POPPED), true);
    public static final BarnaclesBlock BARNACLES = register("barnacles", BarnaclesBlock::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.STONE).noCollision().strength(0.4F).sound(SoundType.CORAL_BLOCK).noOcclusion()
            .pushReaction(PushReaction.POPPED), true);
    public static final SeaGlassBlocks.Glass SEA_GLASS = register("sea_glass", SeaGlassBlocks.Glass::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_CYAN).strength(0.3F).sound(SoundType.GLASS).noOcclusion(), true);
    public static final SeaGlassBlocks.Pane SEA_GLASS_PANE = register("sea_glass_pane", SeaGlassBlocks.Pane::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_CYAN).strength(0.3F).sound(SoundType.GLASS).noOcclusion(), true);
    public static final WaterFacingBlock SIGNAL_LAMP = register("signal_lamp", p -> new WaterFacingBlock(p, Block.box(3, 0, 3, 13, 15, 13)),
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(2.0F).sound(SoundType.COPPER).noOcclusion()
                    .lightLevel(s -> 15), true);
    public static final WaterFacingBlock CONTRABAND_CRATE = register("contraband_crate", p -> new WaterFacingBlock(p, Block.box(1, 0, 1, 15, 14, 15)),
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.0F).sound(SoundType.WOOD).ignitedByLava(), true);
    public static final HauntBlock HAUNT = register("haunt", HauntBlock::new, BlockBehaviour.Properties.of()
            .noCollision().noOcclusion().noLootTable().strength(-1.0F, 3600000.0F).replaceable().noTerrainParticles()
            .pushReaction(PushReaction.POPPED), false);

    public static final BlockEntityType<HauntBlockEntity> HAUNT_ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            OceanExpansion.id("haunt"), new BlockEntityType<>(HauntBlockEntity::new, Set.of(HAUNT)));

    private static <B extends Block> B register(String id, Function<BlockBehaviour.Properties, B> factory, BlockBehaviour.Properties props, boolean item) {
        ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OceanExpansion.id(id));
        B block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(props.setId(key)));
        if (item) {
            ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OceanExpansion.id(id));
            ITEMS.add(Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix())));
        }
        return block;
    }

    public static void register() {}
}
