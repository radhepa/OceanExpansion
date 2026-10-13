package dev.oceanexpansion;

import dev.oceanexpansion.block.OceanBlocks;
import dev.oceanexpansion.item.OceanItems;
import dev.oceanexpansion.resident.Jobs;
import dev.oceanexpansion.resident.Residents;
import dev.oceanexpansion.talk.SiteTalk;
import dev.oceanexpansion.worldgen.Sites;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.npc.villager.Villager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Ocean Expansion: ten rare places to find at sea, for the Village Friends modpack. See DESIGN.md.
 */
public final class OceanExpansion implements ModInitializer {
    public static final String MOD_ID = "oceanexpansion";
    public static final Logger LOG = LoggerFactory.getLogger("Ocean Expansion");

    public static Identifier id(String path) { return Identifier.fromNamespaceAndPath(MOD_ID, path); }

    @Override
    public void onInitialize() {
        OceanConfig.get();
        Sites.register();
        OceanBlocks.register();
        OceanItems.register();
        Jobs.register();
        Residents.register();
        SiteTalk.register();

        // Settle our residents before Village Friends looks at a newly loaded villager, so it never tries to put
        // them in a village.
        Identifier early = id("before_village_friends");
        ServerEntityEvents.ENTITY_LOAD.addPhaseOrdering(early, Event.DEFAULT_PHASE);
        ServerEntityEvents.ENTITY_LOAD.register(early, (entity, level) -> { if (entity instanceof Villager v) Residents.settle(v); });
        ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> { if (entity instanceof Villager v) Residents.unloaded(v); });
        ServerTickEvents.END_SERVER_TICK.register(Residents::tick);
        ServerTickEvents.END_SERVER_TICK.register(OceanItems::tick);
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> Residents.clear());

        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("functional_blocks")))
                .register(out -> { out.accept(OceanBlocks.SIGNAL_LAMP); out.accept(OceanBlocks.CONTRABAND_CRATE); });
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("natural_blocks")))
                .register(out -> { out.accept(OceanBlocks.GIANT_CLAM); out.accept(OceanBlocks.TUBE_WORMS); out.accept(OceanBlocks.BARNACLES); });
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("colored_blocks")))
                .register(out -> { out.accept(OceanBlocks.SEA_GLASS); out.accept(OceanBlocks.SEA_GLASS_PANE); });
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("ingredients")))
                .register(out -> { out.accept(OceanItems.PEARL); out.accept(OceanItems.BLACK_PEARL); out.accept(OceanItems.AMBERGRIS); });
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("tools_and_utilities")))
                .register(out -> out.accept(OceanItems.STORM_GLASS));
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace("combat")))
                .register(out -> out.accept(OceanItems.DIVING_HELMET));
        LOG.info("Ocean Expansion ready (rarity {})", OceanConfig.get().rarity());
    }
}
