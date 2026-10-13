package dev.oceanexpansion.resident;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.oceanexpansion.OceanExpansion;
import dev.oceanexpansion.OceanConfig;
import dev.oceanexpansion.worldgen.Sites;
import dev.villagefriends.ResidentNames;
import dev.villagefriends.ResidentProfile;
import dev.villagefriends.ResidentRoutines;
import dev.villagefriends.VillageFriends;
import dev.villagefriends.homestead.Dwelling;
import dev.villagefriends.homestead.Homesteads;
import dev.villagefriends.routine.Routine;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.entity.npc.villager.VillagerProfession;
import net.minecraft.world.entity.npc.villager.VillagerType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;

/**
 * The people of the lived-in sites, as Village Friends residents. The site's template tags each of them with a
 * {@link Role}; the first time one loads it becomes who they are: a Village Friends "dweller" (no village, their own
 * day and dialogue) with a name, the site's name, a personality that fits, the right job and level, gear, and the
 * middle of their site, which they don't stray far from. Hooks: {@code HomesteadsMixin} (their day) and
 * {@code TalkWorldMixin} (their lines, {@link dev.oceanexpansion.talk.SiteTalk}).
 */
public final class Residents {
    private Residents() {}

    /** What a site resident keeps: their role, their site, their post (where they stand watch) and the rumour they know. */
    public record Resident(String role, String site, int postX, int postY, int postZ, String rumor, String rumorDir, String rumorDist) {
        public static final Codec<Resident> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.fieldOf("role").forGetter(Resident::role), Codec.STRING.fieldOf("site").forGetter(Resident::site),
                Codec.INT.fieldOf("post_x").forGetter(Resident::postX), Codec.INT.fieldOf("post_y").forGetter(Resident::postY),
                Codec.INT.fieldOf("post_z").forGetter(Resident::postZ),
                Codec.STRING.optionalFieldOf("rumor", "").forGetter(Resident::rumor),
                Codec.STRING.optionalFieldOf("rumor_dir", "").forGetter(Resident::rumorDir),
                Codec.STRING.optionalFieldOf("rumor_dist", "").forGetter(Resident::rumorDist)
        ).apply(i, Resident::new));
        public Role kind() { return Role.byId(this.role); }
        public BlockPos post() { return new BlockPos(this.postX, this.postY, this.postZ); }
        public boolean knowsRumor() { return !this.rumor.isEmpty() && !this.rumor.equals("none"); }
        Resident withRumor(String rumor, String dir, String dist) { return new Resident(role, site, postX, postY, postZ, rumor, dir, dist); }
    }

    public static final AttachmentType<Resident> RESIDENT = AttachmentRegistry.create(OceanExpansion.id("resident"), b -> b.persistent(Resident.CODEC));
    /** Rumours worked out per site (dwelling id), shared by everyone who lives there. */
    private static final Map<String, Resident> RUMORS = new HashMap<>();
    private static final Map<UUID, Villager> LOADED = new HashMap<>();

    public static void register() { java.util.Objects.requireNonNull(RESIDENT); }

    public static Resident of(Villager v) { return VillageFriends.target(v).getAttached(RESIDENT); }
    public static boolean ours(Villager v) { return VillageFriends.target(v).hasAttached(RESIDENT); }

    // -- settling in ---------------------------------------------------------------------------------

    /** First load of a tagged site resident: who they are and where they live. Does nothing for anyone else. */
    public static void settle(Villager v) {
        if (!(v.level() instanceof ServerLevel level)) return;
        if (ours(v)) { LOADED.put(v.getUUID(), v); return; }
        Role role = Role.fromTags(v.entityTags());
        if (role == null) return;
        BlockPos pos = v.blockPosition();
        StructureStart start = level.structureManager().getStructureWithPieceAt(pos, Sites.ALL);
        String site = role.site();
        BlockPos middle = pos;
        String dwelling = "site:" + (pos.getX() >> 4) + ":" + (pos.getZ() >> 4);
        if (start.isValid()) {
            var key = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(start.getStructure());
            if (key != null) site = key.getPath();
            var core = start.getPieces().getFirst().getBoundingBox().getCenter();
            middle = new BlockPos(core.getX(), pos.getY(), core.getZ());
            dwelling = "site:" + start.getChunkPos().x() + ":" + start.getChunkPos().z();
        }
        long seed = level.getSeed() ^ (long) dwelling.hashCode() * 0x9E3779B97F4A7C15L;
        String place = Places.name(site, seed);
        var profile = VillageFriends.profile(v);
        String recipe = profile.look();
        VillageFriends.target(v).setAttached(VillageFriends.PROFILE,
                ResidentProfile.withPersonality(profile, role.personality(seed ^ v.getUUID().getLeastSignificantBits()), recipe));
        String name = ResidentNames.name(v.getUUID(), recipe);
        VillageFriends.target(v).setAttached(Homesteads.DWELLER,
                new Dwelling.Dweller(role.dwellerRole(), name, place, dwelling, middle.getX(), middle.getY(), middle.getZ()));
        job(v, level, role);
        v.setVillagerData(v.getVillagerData().withType(level.registryAccess(), VillagerType.byBiome(level.getBiome(pos))));
        v.setCustomName(Component.literal(role.label(name, place)));
        v.setCustomNameVisible(true);
        VillageFriends.target(v).setAttached(RESIDENT, new Resident(role.id(), site, pos.getX(), pos.getY(), pos.getZ(), "", "", ""));
        gear(v, role);
        LOADED.put(v.getUUID(), v);
        VillageFriends.ensureIdentity(v);
    }

    /** The job and level the role asks for (level 2 and up never loses its job). */
    private static void job(Villager v, ServerLevel level, Role role) {
        ResourceKey<VillagerProfession> key = ResourceKey.create(Registries.VILLAGER_PROFESSION, Identifier.parse(role.profession()));
        var profession = level.registryAccess().lookupOrThrow(Registries.VILLAGER_PROFESSION).get(key);
        if (profession.isEmpty()) return;
        int lvl = Math.max(role.level(), v.getVillagerData().level());
        v.setVillagerData(v.getVillagerData().withProfession(profession.get()).withLevel(lvl));
        v.setVillagerXp(Math.max(v.getVillagerXp(), 10 * lvl));
    }

    /** The lightkeeper carries a spyglass. Never dropped. */
    static void gear(Villager v, Role role) {
        if (role == Role.LIGHTKEEPER) put(v, EquipmentSlot.MAINHAND, Items.SPYGLASS);
    }

    private static void put(Villager v, EquipmentSlot slot, net.minecraft.world.item.Item item) {
        if (!v.getItemBySlot(slot).isEmpty()) return;
        v.setItemSlot(slot, new ItemStack(item));
        v.setDropChance(slot, 0F);
    }

    public static void unloaded(Villager v) { LOADED.remove(v.getUUID()); }

    public static void clear() { LOADED.clear(); RUMORS.clear(); }

    /** Every few seconds: gear that was put down (trading shows the offer in hand, then clears it) goes back on. */
    public static void tick(MinecraftServer server) {
        if (server.getTickCount() % 100 != 0) return;
        List<Villager> gone = new ArrayList<>();
        for (Villager v : LOADED.values()) {
            if (v.isRemoved()) { gone.add(v); continue; }
            Resident r = of(v);
            if (r == null || r.kind() == null || v.getTradingPlayer() != null || v.isSleeping()) continue;
            gear(v, r.kind());
        }
        for (Villager v : gone) LOADED.remove(v.getUUID());
    }

    // -- their day ------------------------------------------------------------------------------------

    /** Their day down here (see {@link Role#adjust}); null for anyone not ours. */
    public static Routine.Plan plan(Villager v, Routine.Plan plan, int time) {
        Resident r = of(v);
        if (r == null || r.kind() == null) return null;
        boolean watch = Math.floorMod(v.getUUID().hashCode(), 2) == 0;
        Routine.Block block = r.kind().adjust(plan.block(), plan.scheduled(), time, watch);
        return block == plan.block() ? plan : new Routine.Plan(block, plan.scheduled(), plan.weather(), plan.day());
    }

    public static String doing(Villager v, Routine.Plan plan) {
        Resident r = of(v);
        return r == null || r.kind() == null ? null : r.kind().doing(plan.block());
    }

    public static String about(Villager v) {
        Resident r = of(v);
        var d = Homesteads.dweller(v);
        return r == null || r.kind() == null || d == null ? null : r.kind().about(d.place());
    }

    /**
     * Keeps a resident near the middle of their site (past their role's tether they turn back for their bed), and
     * puts a warden on watch at their post. True when it told them where to go.
     */
    public static boolean steer(Villager v, ServerLevel level, Routine.Plan plan) {
        Resident r = of(v);
        var d = Homesteads.dweller(v);
        if (r == null || r.kind() == null || d == null) return false;
        if (plan.block() == Routine.Block.NIGHT_WATCH && r.kind().guard()) {
            BlockPos post = r.post();
            if (v.blockPosition().distSqr(post) > 2) ResidentRoutines.walk(v, post, .45F, 1);
            else v.getLookControl().setLookAt(post.getX() * 2.0 - d.x(), post.getY() + 1.5, post.getZ() * 2.0 - d.z());
            return true;
        }
        if (plan.block().sleep) return false;
        int tether = r.kind().tether();
        if (d.away(v.getX(), v.getZ()) <= (long) tether * tether && Math.abs(v.getY() - d.y()) < 10) return false;
        BlockPos middle = new BlockPos(d.x(), d.y(), d.z());
        BlockPos bed = v.getBrain().getMemory(MemoryModuleType.HOME).filter(h -> h.dimension() == level.dimension()).map(GlobalPos::pos)
                .filter(h -> h.distSqr(middle) < 40 * 40).orElse(r.post());
        ResidentRoutines.walk(v, bed, .55F, 3);
        return true;
    }

    // -- rumours --------------------------------------------------------------------------------------

    /**
     * The nearest site of another kind, worked out the first time anyone in this site is asked (and kept): where it
     * lies and roughly how far. "none" when there's nothing within a few thousand blocks, or rumours are off.
     */
    public static Resident rumor(Villager v, ServerLevel level) {
        Resident r = of(v);
        if (r == null || !r.rumor().isEmpty()) return r;
        var d = Homesteads.dweller(v);
        String dwelling = d == null ? v.getUUID().toString() : d.dwelling();
        Resident known = RUMORS.get(dwelling);
        Resident next;
        if (known != null) next = r.withRumor(known.rumor(), known.rumorDir(), known.rumorDist());
        else {
            next = r.withRumor("none", "", "");
            if (OceanConfig.get().rumors()) {
                var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
                List<Holder<Structure>> others = new ArrayList<>();
                for (String key : Sites.KEYS) if (!key.equals(r.site())) registry.get(Sites.key(key)).ifPresent(others::add);
                Pair<BlockPos, Holder<Structure>> found = others.isEmpty() ? null : level.getChunkSource().getGenerator()
                        .findNearestMapStructure(level, HolderSet.direct(others), v.blockPosition(), 3, false);
                if (found != null) {
                    String kind = found.getSecond().unwrapKey().map(k -> k.identifier().getPath()).orElse("none");
                    double dx = found.getFirst().getX() - v.getX(), dz = found.getFirst().getZ() - v.getZ();
                    next = r.withRumor(kind, Places.direction(dx, dz), Places.distance(Math.sqrt(dx * dx + dz * dz)));
                }
            }
            RUMORS.put(dwelling, next);
        }
        VillageFriends.target(v).setAttached(RESIDENT, next);
        return next;
    }

    /** First name of the resident with this role who lives in the same site (and is near), or null. */
    public static String neighbor(Villager v, Role role) {
        var d = Homesteads.dweller(v);
        if (d == null) return null;
        for (Villager o : v.level().getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(48), o -> o != v && o.isAlive())) {
            Resident r = of(o);
            var od = Homesteads.dweller(o);
            if (r != null && r.kind() == role && od != null && od.dwelling().equals(d.dwelling())) return first(od.name());
        }
        return null;
    }

    public static String first(String name) {
        int space = name.indexOf(' ');
        return space > 0 ? name.substring(0, space) : name;
    }
}
