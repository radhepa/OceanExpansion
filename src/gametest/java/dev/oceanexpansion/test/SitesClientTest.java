package dev.oceanexpansion.test;

import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Function;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.mojang.datafixers.util.Pair;
import dev.oceanexpansion.OceanExpansion;
import dev.oceanexpansion.block.OceanBlocks;
import dev.oceanexpansion.block.HauntBlock;
import dev.oceanexpansion.resident.Residents;
import dev.oceanexpansion.talk.SiteTalk;
import dev.oceanexpansion.worldgen.Sites;
import dev.villagefriends.TalkWorld;
import dev.villagefriends.homestead.Homesteads;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * The sea sites in a real, generated world: each of the ten found the way /locate finds it, its pieces and height
 * checked (under the sea, or rising above it), its residents (named, settled, talking from our own lines, trading,
 * knowing a rumour), its chests' loot tables, its guardians woken by a survival player, how far it stands from the
 * Sea Friends' villages and the ocean monuments, screenshots (with night vision), and a block dump for the cutaway.
 *   gradlew runClientGameTest -PoceanTests=Lighthouse,Galleon,... [-PtestHeap=2g] [-PcompatMods=<instance mods>]
 * Seed: -Doceanexpansion.seed (default "ocean expansion").
 */
@SuppressWarnings("UnstableApiUsage")
public class SitesClientTest implements FabricClientGameTest {
    static final Path OUT = Path.of("sites");
    static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private final Map<String, Object> report = new LinkedHashMap<>();

    static void check(boolean ok, String what) { if (!ok) throw new AssertionError(what); }

    static boolean wanted(String scene) {
        String only = System.getProperty("oceanexpansion.tests");
        return only == null || only.isBlank() || List.of(only.toLowerCase(Locale.ROOT).split(",")).contains(scene.toLowerCase(Locale.ROOT));
    }

    static <T> T onServer(TestSingleplayerContext w, Function<ServerLevel, T> fn) {
        return w.getServer().computeOnServer(s -> fn.apply(s.overworld()));
    }

    static ServerPlayer player(TestSingleplayerContext w) { return w.getConnection().getServerPlayer(); }

    static void shoot(ClientGameTestContext ctx, String name) {
        ctx.runOnClient(client -> client.gui.toastManager().clear());
        ctx.takeScreenshot(name);
    }

    static void settle(ClientGameTestContext ctx, TestSingleplayerContext w) {
        try { w.getConnection().waitForChunksRender(); } catch (AssertionError slow) { ctx.waitTicks(40); }
    }

    @Override
    public void runTest(ClientGameTestContext ctx) {
        if (Sites.KEYS.stream().noneMatch(SitesClientTest::wanted) && !wanted("census")) return;
        JsonObject catalog = catalog();
        ctx.getInput().resizeWindow(1280, 800);
        ctx.runOnClient(client -> {
            client.options.guiScale().set(2);
            client.options.renderDistance().set(5);
            client.options.gamma().set(1.0);
            client.resizeGui();
        });
        String seed = System.getProperty("oceanexpansion.seed", "ocean expansion");
        try (TestSingleplayerContext w = ctx.worldBuilder().adjustSettings(ui -> {
            var normal = ui.getSettings().worldgenLoadContext().lookupOrThrow(Registries.WORLD_PRESET).getOrThrow(WorldPresets.NORMAL);
            ui.setWorldType(new WorldCreationUiState.WorldTypeEntry(normal));
            ui.setGenerateStructures(true);
            ui.setSeed(seed);
        }).create()) {
            settle(ctx, w);
            for (String cmd : List.of("gamemode creative @a", "gamerule advance_time false", "gamerule advance_weather false",
                    "gamerule spawn_mobs false", "time set 6000", "weather clear", "difficulty normal",
                    "effect give @a minecraft:night_vision infinite 0 true", "effect give @a minecraft:conduit_power infinite 0 true")) {
                w.getServer().runCommand(cmd);
            }
            ctx.runOnClient(client -> { if (!client.gui.hud.isHidden()) client.gui.hud.toggle(); });
            fly(w);
            report.put("seed", seed);
            report.put("mods", FabricLoader.getInstance().getAllMods().stream().map(m -> m.getMetadata().getId()).filter(id -> !id.startsWith("fabric")
                    && !id.equals("java") && !id.equals("minecraft") && !id.equals("mixinextras")).sorted().toList());
            int n = 1;
            for (String key : Sites.KEYS) {
                if (!wanted(key)) continue;
                visit(ctx, w, key, catalog.getAsJsonObject(key), n++);
            }
            if (wanted("census")) census(w);
        } finally {
            try {
                Files.createDirectories(OUT);
                Files.writeString(OUT.resolve("report.json"), GSON.toJson(report), StandardCharsets.UTF_8);
            } catch (IOException e) { OceanExpansion.LOG.warn("couldn't write the test report", e); }
        }
    }

    static JsonObject catalog() {
        try (var in = SitesClientTest.class.getResourceAsStream("/data/oceanexpansion/oceanexpansion/catalog.json")) {
            check(in != null, "the catalog (tools/sites/build.py) is in the jar");
            return GSON.fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), JsonObject.class);
        } catch (IOException e) { throw new AssertionError(e); }
    }

    static void fly(TestSingleplayerContext w) {
        w.getServer().runCommand("gamemode creative @a");
        onServer(w, level -> {
            ServerPlayer p = player(w);
            p.getAbilities().flying = true;
            p.onUpdateAbilities();
            return null;
        });
    }

    // -- finding a site -------------------------------------------------------------------------------

    record Site(String key, BlockPos found, StructureStart start, Map<String, List<BoundingBox>> pieces) {
        BoundingBox core() { return this.start.getPieces().getFirst().getBoundingBox(); }
        BoundingBox all() { return this.start.getBoundingBox(); }
    }

    static String template(StructurePiece piece) {
        return piece instanceof dev.oceanexpansion.worldgen.SitePiece p ? Identifier.parse(p.templateId()).getPath() : piece.getClass().getSimpleName();
    }

    static Site find(TestSingleplayerContext w, String key) {
        Pair<BlockPos, Holder<Structure>> found = onServer(w, level -> {
            var holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getOrThrow(Sites.key(key));
            return level.getChunkSource().getGenerator().findNearestMapStructure(level, HolderSet.direct(holder), BlockPos.ZERO, 100, false);
        });
        check(found != null, "a " + key + " generates in the world");
        BlockPos at = found.getFirst();
        Site site = onServer(w, level -> {
            ChunkAccess chunk = level.getChunk(at.getX() >> 4, at.getZ() >> 4, ChunkStatus.STRUCTURE_STARTS, true);
            for (var e : chunk.getAllStarts().entrySet()) {
                var id = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(e.getKey());
                if (id == null || !id.equals(OceanExpansion.id(key)) || !e.getValue().isValid()) continue;
                Map<String, List<BoundingBox>> pieces = new LinkedHashMap<>();
                for (StructurePiece piece : e.getValue().getPieces())
                    pieces.computeIfAbsent(template(piece), k -> new ArrayList<>()).add(piece.getBoundingBox());
                return new Site(key, at, e.getValue(), pieces);
            }
            return null;
        });
        check(site != null, "the " + key + "'s start at " + at);
        OceanExpansion.LOG.info("[sites test] {} at {}: {} pieces {}", key, at, site.start().getPieces().size(), site.pieces().keySet());
        return site;
    }

    // -- one site -------------------------------------------------------------------------------------

    void visit(ClientGameTestContext ctx, TestSingleplayerContext w, String key, JsonObject info, int n) {
        Site site = find(w, key);
        Map<String, Object> facts = new LinkedHashMap<>();
        report.put(key, facts);
        facts.put("found", List.of(site.found().getX(), site.found().getY(), site.found().getZ()));
        facts.put("pieces", site.pieces().keySet());
        BoundingBox core = site.core();
        var pieceNames = info.getAsJsonArray("pieces").asList().stream().map(e -> e.getAsString()).toList();
        for (String p : site.pieces().keySet()) check(pieceNames.contains(p), key + " is built from its own pieces: " + p);
        int sea = onServer(w, level -> level.getSeaLevel());
        boolean surface = info.get("anchor").getAsString().equals("surface");
        // a surface site reaches above the waves; a seabed site stays under them
        if (surface) check(site.all().maxY() >= sea, key + " rises above the sea: " + site.all());
        else check(core.minY() < sea - 3, key + " lies under the sea: " + core);

        facts.put("core", List.of(core.minX(), core.minY(), core.minZ(), core.maxX(), core.maxY(), core.maxZ()));

        // get there and let it load (residents load with their chunks); first a wide look from outside
        Vec3 target = onServer(w, level -> floorNear(level, core));
        BoundingBox all = site.all();
        Vec3 middle = new Vec3((all.minX() + all.maxX()) / 2.0, (all.minY() + all.maxY()) / 2.0, (all.minZ() + all.maxZ()) / 2.0);
        double reach = Math.max(all.maxX() - all.minX(), all.maxZ() - all.minZ()) * 0.62 + 6;
        Vec3 outside = middle.add(reach, surface ? Math.max(6, (all.maxY() - all.minY()) * 0.35) : (all.maxY() - all.minY()) * 0.3, reach * 0.55);
        if (!surface) outside = new Vec3(outside.x, Math.min(outside.y, sea - 2), outside.z);
        look(ctx, w, outside, middle, 80);
        shoot(ctx, String.format("site-%02d-%s-0-outside", n, key));
        // (the chunks are loaded now) how deep the sea is just outside the site
        BlockPos beside = BlockPos.containing(middle.x + reach * 0.8, 0, middle.z);
        facts.put("water_beside", onServer(w, level -> sea - level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.OCEAN_FLOOR,
                beside.getX(), beside.getZ())));
        look(ctx, w, target.add(0, 1.6, 0), target.add(3, 0, 3), 30);
        Vec3 eye = onServer(w, level -> roomView(level, core, target));
        look(ctx, w, eye, target, 30);
        shoot(ctx, String.format("site-%02d-%s-1", n, key));
        Vec3 eye2 = onServer(w, level -> roomView(level, core, target.add((core.maxX() - core.minX()) / 4.0, 0, -(core.maxZ() - core.minZ()) / 4.0)));
        look(ctx, w, eye2, target, 15);
        shoot(ctx, String.format("site-%02d-%s-2", n, key));

        // loot: every chest/barrel/pot of the site that is loaded rolls one of our tables
        Map<String, Integer> loot = onServer(w, level -> loot(level, site.all()));
        facts.put("loot", loot);
        check(!loot.isEmpty(), key + " has containers with our loot: " + loot);
        for (String table : loot.keySet()) check(table.startsWith("oceanexpansion:chests/" + key + "/") || table.startsWith("oceanexpansion:chests/"),
                key + " loot table " + table);

        if (info.get("inhabited").getAsBoolean()) residents(ctx, w, site, info, facts);
        else haunts(ctx, w, site, info, facts);
        compat(w, site, facts);
        dump(w, site);
    }

    void residents(ClientGameTestContext ctx, TestSingleplayerContext w, Site site, JsonObject info, Map<String, Object> facts) {
        int expected = info.getAsJsonArray("residents").size();
        ctx.waitTicks(40);
        List<String> found = onServer(w, level -> {
            List<String> out = new ArrayList<>();
            for (Villager v : level.getEntitiesOfClass(Villager.class, AABB.of(site.all()).inflate(8))) {
                var r = Residents.of(v);
                var d = Homesteads.dweller(v);
                check(r != null && d != null && d.role().startsWith("oceanexpansion_"), "every villager in a " + site.key() + " is settled as a site resident: "
                        + v.getName().getString());
                check(v.hasCustomName(), "a resident has a nameplate: " + v.getName().getString());
                out.add(r.role() + ":" + BuiltInRegistries.VILLAGER_PROFESSION.getKey(v.getVillagerData().profession().value()) + ":" + v.getCustomName().getString());
            }
            return out;
        });
        facts.put("residents", found);
        check(found.size() >= expected, site.key() + " has its " + expected + " residents: " + found);
        // they talk from our own lines, know a rumour, and miners trade
        List<String> said = onServer(w, level -> {
            List<String> out = new ArrayList<>();
            ServerPlayer p = player(w);
            for (Villager v : level.getEntitiesOfClass(Villager.class, AABB.of(site.all()).inflate(8))) {
                String greet = TalkWorld.line(v, p, "greet");
                String news = TalkWorld.line(v, p, "news");
                check(greet != null && !greet.contains("{"), "a resident greets from our lines: " + greet);
                check(news != null, "and has news");
                var r = Residents.rumor(v, level);
                check(r != null && !r.rumor().isEmpty(), "a rumour was looked for");
                out.add(v.getCustomName().getString() + ": " + greet + " | " + news + " | rumour " + r.rumor() + " " + r.rumorDir() + " " + r.rumorDist());
                if (r.role().equals("lightkeeper") || r.role().startsWith("smuggler")) {
                    check(!v.getOffers().isEmpty(), "a " + r.role() + " has trades");
                    check(SiteTalk.line(v, p, "work") != null, "and talks about work");
                }
            }
            return out;
        });
        facts.put("talk", said);
        // up close with one of them
        Vec3 face = onServer(w, level -> level.getEntitiesOfClass(Villager.class, AABB.of(site.all()).inflate(8)).getFirst().getEyePosition());
        look(ctx, w, onServer(w, level -> roomView(level, site.core(), face)), face, 20);
        shoot(ctx, "site-" + site.key() + "-resident");
    }

    void haunts(ClientGameTestContext ctx, TestSingleplayerContext w, Site site, JsonObject info, Map<String, Object> facts) {
        if (info.getAsJsonArray("haunts").isEmpty()) return;
        BlockPos mark = onServer(w, level -> {
            BoundingBox all = site.all();
            for (BlockPos pos : BlockPos.betweenClosed(all.minX(), all.minY(), all.minZ(), all.maxX(), all.maxY(), all.maxZ()))
                if (level.isLoaded(pos) && level.getBlockState(pos).is(OceanBlocks.HAUNT)) return pos.immutable();
            return null;
        });
        if (mark == null) { facts.put("haunt", "not in the loaded pieces"); return; }
        String kind = onServer(w, level -> level.getBlockState(mark).getValue(HauntBlock.KIND).getSerializedName());
        // a survival player walks up to it
        w.getServer().runCommand(String.format(Locale.ROOT, "tp @a %d %d %d", mark.getX() + 8, mark.getY() + 1, mark.getZ()));
        w.getServer().runCommand("gamemode survival @a");
        ctx.waitTicks(40);
        int risen = onServer(w, level -> level.getEntitiesOfClass(Mob.class, new AABB(mark).inflate(8), m -> m instanceof Enemy && m.isAlive()).size());
        boolean gone = onServer(w, level -> !level.getBlockState(mark).is(OceanBlocks.HAUNT));
        facts.put("haunt", kind + " at " + mark.toShortString() + ": " + risen + " risen");
        check(gone && risen >= 1, "the " + kind + " guardians rise when a player comes near (" + risen + ")");
        Vec3 at = onServer(w, level -> {
            var up = level.getEntitiesOfClass(Mob.class, new AABB(mark).inflate(10), m -> m instanceof Enemy && m.isAlive());
            Vec3 sum = Vec3.ZERO;
            for (Mob m : up) sum = sum.add(m.getEyePosition());
            return up.isEmpty() ? Vec3.atCenterOf(mark) : sum.scale(1.0 / up.size());
        });
        w.getServer().runCommand("gamemode creative @a");
        fly(w);
        w.getServer().runOnServer(s -> {    // hold them still for the picture
            for (Mob m : s.overworld().getEntitiesOfClass(Mob.class, new AABB(mark).inflate(12), m -> m instanceof Enemy)) m.setNoAi(true);
        });
        look(ctx, w, onServer(w, level -> nearView(level, at)), at, 10);
        shoot(ctx, "site-" + site.key() + "-guardians");
        w.getServer().runOnServer(s -> {
            for (Mob m : s.overworld().getEntitiesOfClass(Mob.class, new AABB(mark).inflate(24), m -> m instanceof Enemy)) m.discard();
        });
    }

    /** How far the site stands from the Sea Friends' villages and the ocean monuments. */
    void compat(TestSingleplayerContext w, Site site, Map<String, Object> facts) {
        for (String[] other : new String[][]{{"seafriends", "villages", "5"}, {"minecraft", "ocean_monument", "4"}}) {
            if (!other[0].equals("minecraft") && !FabricLoader.getInstance().isModLoaded(other[0])) continue;
            TagKey<Structure> tag = TagKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath(other[0], other[1]));
            BlockPos near = onServer(w, level -> level.findNearestMapStructure(tag, site.found(), 6, false));
            if (near == null) { facts.put(other[1], "none near"); continue; }
            int chunks = Math.max(Math.abs((near.getX() >> 4) - (site.found().getX() >> 4)), Math.abs((near.getZ() >> 4) - (site.found().getZ() >> 4)));
            facts.put(other[1], chunks + " chunks away");
            check(chunks >= Integer.parseInt(other[2]) - 1, site.key() + " keeps clear of " + other[1] + ": " + chunks + " chunks");
        }
    }

    // -- how rare they are ---------------------------------------------------------------------------------

    /**
     * Every placement cell of the sites' structure set in a 9 x 9 block of cells round the origin (about 4,300
     * blocks square): how many cells grew a site, and of which kind.
     */
    void census(TestSingleplayerContext w) {
        Map<String, Object> out = onServer(w, level -> {
            var set = level.registryAccess().lookupOrThrow(Registries.STRUCTURE_SET)
                    .getOrThrow(net.minecraft.resources.ResourceKey.create(Registries.STRUCTURE_SET, OceanExpansion.id("sites"))).value();
            var placement = (dev.oceanexpansion.worldgen.SpreadPlacement) set.placement();
            int spacing = placement.spacing(), cells = 0, found = 0;
            Map<String, Integer> kinds = new LinkedHashMap<>();
            for (int gx = -4; gx <= 4; gx++) for (int gz = -4; gz <= 4; gz++) {
                cells++;
                var chunk = placement.getPotentialStructureChunk(level.getSeed(), gx * spacing, gz * spacing);
                ChunkAccess c = level.getChunk(chunk.x(), chunk.z(), ChunkStatus.STRUCTURE_STARTS, true);
                for (var e : c.getAllStarts().entrySet()) {
                    var id = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(e.getKey());
                    if (id == null || !id.getNamespace().equals(OceanExpansion.MOD_ID) || !e.getValue().isValid()) continue;
                    found++;
                    kinds.merge(id.getPath(), 1, Integer::sum);
                }
            }
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("cells", cells);
            m.put("cell_blocks", spacing * 16);
            m.put("sites", found);
            m.put("kinds", kinds);
            m.put("blocks_per_site", found == 0 ? -1 : (int) Math.round(Math.sqrt((double) cells * spacing * 16 * spacing * 16 / found)));
            return m;
        });
        report.put("census", out);
        OceanExpansion.LOG.info("[sites test] census {}", out);
        check((int) out.get("sites") > 0, "sites generate: " + out);
    }

    // -- looking ----------------------------------------------------------------------------------------

    /** A spot a few blocks from `at` with a clear view of it. */
    static Vec3 nearView(ServerLevel level, Vec3 at) {
        for (double d : new double[]{4.5, 3.5, 6, 2.5}) for (double h : new double[]{1.2, .4, 2.2}) for (int a = 0; a < 360; a += 30) {
            double r = Math.toRadians(a);
            Vec3 eye = at.add(Math.cos(r) * d, h, Math.sin(r) * d);
            BlockPos cell = BlockPos.containing(eye);
            if (!level.getBlockState(cell).getCollisionShape(level, cell).isEmpty()) continue;
            var hit = level.clip(new ClipContext(eye, at, ClipContext.Block.VISUAL, ClipContext.Fluid.NONE, CollisionContext.empty()));
            if (hit.getType() == HitResult.Type.MISS || hit.getLocation().distanceTo(at) < 1.2) return eye;
        }
        return at.add(3, 1, 3);
    }

    static void look(ClientGameTestContext ctx, TestSingleplayerContext w, Vec3 eye, Vec3 at, int ticks) {
        double dx = at.x - eye.x, dy = at.y - eye.y, dz = at.z - eye.z;
        float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
        float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)));
        w.getServer().runCommand(String.format(Locale.ROOT, "tp @a %.2f %.2f %.2f %.1f %.1f", eye.x, eye.y - 1.62, eye.z, yaw, pitch));
        ctx.waitTicks(ticks);
        settle(ctx, w);
        ctx.waitTicks(10);
    }

    /** Standing height in the middle of the core piece: the first floor with two blocks of air above it. */
    static Vec3 floorNear(ServerLevel level, BoundingBox core) {
        int cx = (core.minX() + core.maxX()) / 2, cz = (core.minZ() + core.maxZ()) / 2;
        level.getChunk(cx >> 4, cz >> 4);
        for (int r = 0; r <= 6; r++) for (int dx = -r; dx <= r; dx++) for (int dz = -r; dz <= r; dz++) {
            if (Math.max(Math.abs(dx), Math.abs(dz)) != r) continue;
            for (int y = core.minY() + 1; y < core.maxY(); y++) {
                BlockPos p = new BlockPos(cx + dx, y, cz + dz);
                if (stand(level, p)) return Vec3.atBottomCenterOf(p);
            }
        }
        return new Vec3(cx + .5, core.minY() + 2, cz + .5);
    }

    static boolean stand(ServerLevel level, BlockPos p) {
        return level.getBlockState(p).getCollisionShape(level, p).isEmpty() && level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()
                && !level.getBlockState(p.below()).getCollisionShape(level, p.below()).isEmpty();
    }

    /** The open spot in the core piece with the longest clear view of `at` (a camera inside the room). */
    static Vec3 roomView(ServerLevel level, BoundingBox core, Vec3 at) {
        Vec3 best = at.add(0, 2, 0);
        double bestScore = -1;
        for (int x = core.minX() + 1; x < core.maxX(); x += 2) for (int z = core.minZ() + 1; z < core.maxZ(); z += 2)
            for (int y = core.minY() + 1; y < core.maxY(); y += 2) {
                BlockPos cell = new BlockPos(x, y, z);
                BlockState s = level.getBlockState(cell);
                if (!s.getCollisionShape(level, cell).isEmpty()) continue;
                Vec3 eye = Vec3.atCenterOf(cell);
                double d = eye.distanceTo(at);
                if (d < 4 || d > 22) continue;
                var hit = level.clip(new ClipContext(eye, at, ClipContext.Block.VISUAL, ClipContext.Fluid.NONE, CollisionContext.empty()));
                if (hit.getType() != HitResult.Type.MISS && hit.getLocation().distanceTo(at) > 1.2) continue;
                double score = d + (eye.y > at.y + 1 ? 2 : 0);
                if (score > bestScore) { bestScore = score; best = eye; }
            }
        return best;
    }

    static Map<String, Integer> loot(ServerLevel level, BoundingBox all) {
        Map<String, Integer> out = new LinkedHashMap<>();
        for (int cx = all.minX() >> 4; cx <= all.maxX() >> 4; cx++) for (int cz = all.minZ() >> 4; cz <= all.maxZ() >> 4; cz++) {
            if (!level.hasChunk(cx, cz)) continue;
            for (var be : level.getChunk(cx, cz).getBlockEntities().values()) {
                if (!(be instanceof RandomizableContainerBlockEntity c) || c.getLootTable() == null) continue;
                if (!all.isInside(be.getBlockPos())) continue;
                out.merge(c.getLootTable().identifier().toString(), 1, Integer::sum);
            }
        }
        for (Entity e : level.getEntitiesOfClass(Entity.class, AABB.of(all))) {
            if (e instanceof net.minecraft.world.entity.vehicle.minecart.MinecartChest cart && cart.getContainerLootTable() != null)
                out.merge(cart.getContainerLootTable().identifier() + " (cart)", 1, Integer::sum);
        }
        return out;
    }

    /** Plain rock the cutaway leaves out. */
    static final java.util.Set<String> ROCK = java.util.Set.of("minecraft:stone", "minecraft:deepslate", "minecraft:tuff", "minecraft:granite",
            "minecraft:diorite", "minecraft:andesite", "minecraft:dirt", "minecraft:gravel", "minecraft:bedrock", "minecraft:cave_air", "minecraft:air",
            "minecraft:water", "minecraft:sand", "minecraft:clay");

    /** Every block of the site's pieces but plain rock and air (for tools/sites/cutaway.py). */
    static void dump(TestSingleplayerContext w, Site site) {
        Map<String, Object> blocks = onServer(w, level -> {
            Map<String, Object> out = new LinkedHashMap<>();
            BoundingBox all = site.all();
            out.put("origin", List.of(all.minX(), all.minY(), all.minZ()));
            List<Object> cells = new ArrayList<>();
            java.util.Set<Long> seen = new java.util.HashSet<>();
            for (StructurePiece piece : site.start().getPieces()) {
                BoundingBox b = piece.getBoundingBox();
                for (BlockPos p : BlockPos.betweenClosed(b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ())) {
                    if (!level.isLoaded(p) || !seen.add(p.asLong())) continue;
                    BlockState s = level.getBlockState(p);
                    if (ROCK.contains(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString())) continue;
                    cells.add(List.of(p.getX() - all.minX(), p.getY() - all.minY(), p.getZ() - all.minZ(),
                            s.toString().replace("Block{", "").replace("}", "")));
                }
            }
            out.put("cells", cells);
            return out;
        });
        try {
            Files.createDirectories(OUT);
            Files.writeString(OUT.resolve(site.key() + ".json"), new Gson().toJson(blocks), StandardCharsets.UTF_8);
        } catch (IOException e) { OceanExpansion.LOG.warn("couldn't dump {}", site.key(), e); }
    }
}
