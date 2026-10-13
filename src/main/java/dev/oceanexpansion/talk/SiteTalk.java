package dev.oceanexpansion.talk;

import java.io.Reader;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import com.google.gson.Gson;
import dev.oceanexpansion.OceanExpansion;
import dev.oceanexpansion.resident.Residents;
import dev.oceanexpansion.resident.Role;
import dev.oceanexpansion.worldgen.Sites;
import dev.villagefriends.FriendshipLevels;
import dev.villagefriends.ResidentRoutines;
import dev.villagefriends.VillageFriends;
import dev.villagefriends.homestead.Homesteads;
import dev.villagefriends.talk.Talk;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimplePreparableReloadListener;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.profiling.ProfilerFiller;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.core.component.DataComponents;

/**
 * What the sea-site residents say, in Village Friends' own conversation window. Village Friends sends every line a
 * homestead dweller speaks through {@code TalkWorld.line}; {@code TalkWorldMixin} hands ours here. Lines come from
 * {@link TalkBank} (data/oceanexpansion/talk/lines.json); the ones said lately are remembered in Village Friends' bond
 * with the player, so they aren't repeated soon.
 */
public final class SiteTalk {
    private SiteTalk() {}

    private static final Gson GSON = new Gson();
    private static final Random RANDOM = new Random();
    private static TalkBank bank = TalkBank.EMPTY;

    public static TalkBank bank() { return bank; }

    public static void register() {
        ResourceLoader.get(PackType.SERVER_DATA).registerReloadListener(OceanExpansion.id("talk"), new SimplePreparableReloadListener<TalkBank>() {
            @Override protected TalkBank prepare(ResourceManager resources, ProfilerFiller profiler) {
                var resource = resources.getResource(OceanExpansion.id("talk/lines.json"));
                if (resource.isEmpty()) return TalkBank.EMPTY;
                try (Reader reader = resource.get().openAsReader()) {
                    return parse(GSON.fromJson(reader, Raw.class));
                } catch (Exception e) {
                    OceanExpansion.LOG.error("Site dialogue rejected; keeping the lines already loaded: {}", e.toString());
                    return bank;
                }
            }
            @Override protected void apply(TalkBank loaded, ResourceManager resources, ProfilerFiller profiler) { bank = loaded; }
        });
    }

    static final class Raw { Map<String, String> parents; Map<String, List<String>> pools; }

    static TalkBank parse(Raw raw) {
        if (raw == null || raw.pools == null) return TalkBank.EMPTY;
        return new TalkBank(raw.pools, raw.parents == null ? Map.of() : raw.parents);
    }

    /** A line for one of our residents on a Village Friends topic, or null (anyone else, or nothing fits). */
    public static String line(Villager v, ServerPlayer p, String topic) {
        var resident = Residents.of(v);
        if (resident == null || resident.kind() == null || !(v.level() instanceof ServerLevel level)) return null;
        Role role = resident.kind();
        if (topic.equals("news") || topic.equals("chat") || topic.equals("adventure")) resident = Residents.rumor(v, level);
        int friendship = FriendshipLevels.level(VillageFriends.state(v, p), VillageFriends.bond(v, p));
        String period = Talk.period(ResidentRoutines.timeOfDay(level));
        ItemStack held = p.getMainHandItem();
        var moment = new TalkBank.Moment(role.talk(), topic, friendship, period, held(held), states(p), resident.knowsRumor(),
                FabricLoader.getInstance().isModLoaded("seafriends"));

        Map<String, String> fill = new HashMap<>();
        var d = Homesteads.dweller(v);
        if (d != null) { fill.put("name", Residents.first(d.name())); fill.put("place", d.place()); }
        fill.put("player", p.getName().getString());
        fill.put("time", TalkBank.timeWord(period));
        if (!held.isEmpty()) fill.put("item", held.getHoverName().getString().toLowerCase(java.util.Locale.ROOT));
        String chief = Residents.neighbor(v, Role.SMUGGLER_BOSS), captain = Residents.neighbor(v, Role.CAPTAIN);
        if (chief != null) fill.put("chief", chief);
        if (captain != null) fill.put("captain", captain);
        if (resident.knowsRumor()) {
            fill.put("rumor_name", Sites.describe(resident.rumor()));
            fill.put("rumor_dir", resident.rumorDir());
            fill.put("rumor_dist", resident.rumorDist());
        }

        var bond = VillageFriends.bond(v, p);
        Set<String> recent = new HashSet<>(bond.recentLines());
        TalkBank.Line line = bank.pick(moment, fill, recent, RANDOM);
        if (line == null) return null;
        VillageFriends.saveBond(v, p, VillageFriends.bond(v, p).line(line.id()));
        return line.text();
    }

    /** What kind of thing the player holds, as our lines know it ("" for nothing they'd remark on). */
    static String held(ItemStack s) {
        if (s.isEmpty()) return "";
        if (s.is(Items.TRIDENT)) return "trident";
        if (s.is(Items.FISHING_ROD)) return "fishing_rod";
        if (s.is(Items.NAUTILUS_SHELL) || s.is(Items.HEART_OF_THE_SEA)) return "shell";
        if (s.is(dev.oceanexpansion.item.OceanItems.PEARL) || s.is(dev.oceanexpansion.item.OceanItems.BLACK_PEARL)) return "pearl";
        if (s.is(Items.COD) || s.is(Items.SALMON) || s.is(Items.TROPICAL_FISH) || s.is(Items.PUFFERFISH) || s.is(Items.COOKED_COD)
                || s.is(Items.COOKED_SALMON)) return "fish";
        if (s.is(ItemTags.BOATS)) return "boat";
        if (s.is(Items.SPYGLASS)) return "spyglass";
        if (s.is(ItemTags.PICKAXES)) return "pickaxe";
        if (s.is(ItemTags.SWORDS)) return "sword";
        if (s.is(ItemTags.AXES)) return "axe";
        if (s.is(ItemTags.SHOVELS)) return "shovel";
        if (s.is(Items.BOW) || s.is(Items.CROSSBOW)) return "bow";
        if (s.is(Items.SHIELD)) return "shield";
        if (s.is(Items.TORCH) || s.is(Items.SOUL_TORCH) || s.is(Items.COPPER_TORCH) || s.is(Items.LANTERN) || s.is(Items.SOUL_LANTERN)) return "torch";
        if (s.is(Items.DIAMOND) || s.is(Items.DIAMOND_ORE) || s.is(Items.DEEPSLATE_DIAMOND_ORE) || s.is(Items.DIAMOND_BLOCK)) return "diamond";
        if (s.is(Items.GOLD_INGOT) || s.is(Items.RAW_GOLD) || s.is(Items.GOLD_NUGGET) || s.is(Items.GOLD_BLOCK)) return "gold";
        if (s.is(Items.EMERALD) || s.is(Items.EMERALD_BLOCK)) return "emerald";
        if (s.is(Items.RAW_IRON) || s.is(Items.RAW_COPPER) || s.is(Items.IRON_INGOT) || s.is(Items.COPPER_INGOT) || s.is(Items.COAL)
                || s.is(Items.REDSTONE) || s.is(Items.LAPIS_LAZULI) || s.is(ItemTags.IRON_ORES) || s.is(ItemTags.COAL_ORES)
                || s.is(ItemTags.COPPER_ORES)) return "ore";
        if (s.is(Items.MAP) || s.is(Items.FILLED_MAP)) return "map";
        if (s.is(Items.COMPASS) || s.is(Items.RECOVERY_COMPASS)) return "compass";
        if (s.is(Items.BOOK) || s.is(Items.WRITABLE_BOOK) || s.is(Items.WRITTEN_BOOK) || s.is(Items.ENCHANTED_BOOK)) return "book";
        if (s.is(Items.TNT)) return "tnt";
        if (s.is(Items.POTION) || s.is(Items.SPLASH_POTION) || s.is(Items.LINGERING_POTION)) return "potion";
        if (s.is(Items.BUCKET) || s.is(Items.WATER_BUCKET) || s.is(Items.LAVA_BUCKET)) return "bucket";
        if (s.is(net.minecraft.tags.BlockItemTags.SMALL_FLOWERS.item())) return "flower";
        if (s.has(DataComponents.FOOD)) return "food";
        return "";
    }

    /** How the player looks: hurt, hungry, unarmored, in diamond, in leather, on fire, with a worn tool. */
    static Set<String> states(ServerPlayer p) {
        var states = new HashSet<String>();
        if (p.getHealth() < p.getMaxHealth() * .5F) states.add("hurt");
        if (p.getFoodData().getFoodLevel() <= 8) states.add("hungry");
        if (p.isOnFire()) states.add("fire");
        if (p.getMainHandItem().isDamaged() && p.getMainHandItem().getDamageValue() > p.getMainHandItem().getMaxDamage() * 3 / 4) states.add("damaged");
        var chest = p.getItemBySlot(EquipmentSlot.CHEST);
        if (chest.is(Items.DIAMOND_CHESTPLATE) || chest.is(Items.NETHERITE_CHESTPLATE)) states.add("diamond");
        else if (chest.is(Items.LEATHER_CHESTPLATE)) states.add("leather");
        else if (chest.isEmpty() && p.getItemBySlot(EquipmentSlot.HEAD).isEmpty() && p.getItemBySlot(EquipmentSlot.LEGS).isEmpty()) states.add("unarmored");
        return states;
    }
}
