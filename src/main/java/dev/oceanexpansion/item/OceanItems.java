package dev.oceanexpansion.item;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import dev.oceanexpansion.OceanExpansion;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;

/**
 * The sites' items: pearls (the grotto's clams, the smugglers' trade), black pearls (the deep vents), ambergris (the
 * whale fall), the storm glass (the lightkeeper's) and Wexley's diving helmet, which lets you breathe under water
 * while you wear it.
 */
public final class OceanItems {
    private OceanItems() {}

    public static final List<Item> ITEMS = new ArrayList<>();

    public static final ResourceKey<EquipmentAsset> DIVING_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, OceanExpansion.id("diving_helmet"));
    public static final ArmorMaterial DIVING = new ArmorMaterial(30, Map.of(ArmorType.HELMET, 2), 9, SoundEvents.ARMOR_EQUIP_TURTLE,
            0F, 0F, ItemTags.REPAIRS_COPPER_ARMOR, DIVING_ASSET);

    public static final Item PEARL = register("pearl", Item::new, new Item.Properties());
    public static final Item BLACK_PEARL = register("black_pearl", Item::new, new Item.Properties().rarity(Rarity.RARE));
    public static final Item AMBERGRIS = register("ambergris", Item::new, new Item.Properties().rarity(Rarity.UNCOMMON));
    public static final Item STORM_GLASS = register("storm_glass", StormGlassItem::new, new Item.Properties().stacksTo(1));
    public static final Item DIVING_HELMET = register("diving_helmet", Item::new,
            new Item.Properties().humanoidArmor(DIVING, ArmorType.HELMET).rarity(Rarity.UNCOMMON));

    private static Item register(String id, Function<Item.Properties, Item> factory, Item.Properties props) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OceanExpansion.id(id));
        Item item = Registry.register(BuiltInRegistries.ITEM, key, factory.apply(props.setId(key)));
        ITEMS.add(item);
        return item;
    }

    public static void register() {}

    /** Once a second: a diver whose head is under water in the helmet breathes; the helmet wears a little. */
    public static void tick(MinecraftServer server) {
        if (server.getTickCount() % 20 != 0) return;
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            var head = p.getItemBySlot(EquipmentSlot.HEAD);
            if (!head.is(DIVING_HELMET) || !p.isEyeInFluid(FluidTags.WATER)) continue;
            p.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 60, 0, true, false, true));
            if (server.getTickCount() % 600 == 0 && !p.isCreative()) head.hurtAndBreak(1, p, EquipmentSlot.HEAD);
        }
    }
}
