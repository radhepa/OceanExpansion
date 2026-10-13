package dev.oceanexpansion.resident;

import java.util.Set;
import java.util.stream.Collectors;

import com.google.common.collect.ImmutableSet;
import dev.oceanexpansion.OceanExpansion;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.fabricmc.fabric.api.object.builder.v1.world.poi.PoiHelper;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.npc.villager.VillagerProfession;
import net.minecraft.world.item.trading.TradeSet;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The two professions of the sea sites. The lightkeeper (job site: the signal lamp) buys fish and sells lamps, glass,
 * spyglasses, a storm glass and Sea Charts to the other sites; the smuggler (job site: a contraband crate) deals in
 * spices, silk, pearls, nautilus shells and, for the trusted, a trident or a heart of the sea. Trades live in
 * data/oceanexpansion/villager_trade.
 */
public final class Jobs {
    private Jobs() {}

    public static void register() {
        profession("lightkeeper", dev.oceanexpansion.block.OceanBlocks.SIGNAL_LAMP, SoundEvents.VILLAGER_WORK_CARTOGRAPHER);
        profession("smuggler", dev.oceanexpansion.block.OceanBlocks.CONTRABAND_CRATE, SoundEvents.VILLAGER_WORK_FISHERMAN);
    }

    private static void profession(String id, Block site, SoundEvent work) {
        ResourceKey<PoiType> poi = ResourceKey.create(Registries.POINT_OF_INTEREST_TYPE, OceanExpansion.id(id));
        Set<BlockState> states = site.getStateDefinition().getPossibleStates().stream().collect(Collectors.toSet());
        PoiHelper.register(OceanExpansion.id(id), 1, 1, states);
        var trades = new Int2ObjectOpenHashMap<ResourceKey<TradeSet>>();
        for (int level = 1; level <= 5; level++) trades.put(level, ResourceKey.create(Registries.TRADE_SET, OceanExpansion.id(id + "/level_" + level)));
        Registry.register(BuiltInRegistries.VILLAGER_PROFESSION, ResourceKey.create(Registries.VILLAGER_PROFESSION, OceanExpansion.id(id)),
                new VillagerProfession(Component.translatable("entity.oceanexpansion.villager." + id), holder -> holder.is(poi), holder -> holder.is(poi),
                        ImmutableSet.of(), ImmutableSet.of(), work, trades));
    }
}
