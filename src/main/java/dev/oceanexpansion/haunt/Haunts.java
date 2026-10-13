package dev.oceanexpansion.haunt;

import java.util.Optional;

import dev.oceanexpansion.block.HauntBlock;
import dev.oceanexpansion.block.HauntBlock.Kind;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The guardians of the abandoned sites. A site's template marks where they wait with an invisible haunt block;
 * the first time a survival (or adventure) player comes within {@link #RANGE} blocks the mark is gone and they rise:
 * <ul>
 *   <li>{@code drowned_crew}: three drowned of a lost crew, one with a trident.</li>
 *   <li>{@code drowned_captain}: the Golden Heron's captain (a drowned in a gold helmet with a trident, twice a
 *       drowned's health) and two of her crew.</li>
 *   <li>{@code guardians}: three guardians, still keeping the Old Tide's temple.</li>
 *   <li>{@code frozen_crew}: three strays in the Northward's frozen coats.</li>
 *   <li>{@code deep_lurkers}: two of Not-So-Vanilla Mobs' anglers when that mod is installed, else two guardians.</li>
 * </ul>
 * They don't despawn: they are the site's, until someone deals with them.
 */
public final class Haunts {
    private Haunts() {}

    public static final int RANGE = 14;

    public static void tick(ServerLevel level, BlockPos pos, BlockState state) {
        if (Math.floorMod(level.getGameTime() + pos.asLong(), 10) != 0) return;
        Player p = level.getNearestPlayer(pos.getX() + .5, pos.getY() + .5, pos.getZ() + .5, RANGE,
                e -> !e.isSpectator() && !(e instanceof Player pl && pl.isCreative()));
        if (p == null) return;
        Kind kind = state.getValue(HauntBlock.KIND);
        level.setBlock(pos, state.getValue(HauntBlock.WATERLOGGED) ? Blocks.WATER.defaultBlockState() : Blocks.AIR.defaultBlockState(), 3);
        rise(level, pos, kind);
        if (p instanceof ServerPlayer sp) sp.sendOverlayMessage(Component.translatable("haunt.oceanexpansion." + kind.getSerializedName()));
    }

    /** Puts a haunt's guardians at {@code pos}; returns how many rose. */
    public static int rise(ServerLevel level, BlockPos pos, Kind kind) {
        int risen = 0;
        switch (kind) {
            case DROWNED_CREW -> {
                for (int i = 0; i < 3; i++) {
                    Mob m = EntityTypes.DROWNED.create(level, EntitySpawnReason.STRUCTURE);
                    if (spawn(level, m, pos, i)) {
                        risen++;
                        if (i == 0) equip(m, EquipmentSlot.MAINHAND, new ItemStack(Items.TRIDENT), .08F);
                        if (i == 1) equip(m, EquipmentSlot.MAINHAND, new ItemStack(Items.FISHING_ROD), .1F);
                    }
                }
                bubbles(level, pos, SoundEvents.DROWNED_AMBIENT_WATER);
            }
            case DROWNED_CAPTAIN -> {
                Mob captain = EntityTypes.DROWNED.create(level, EntitySpawnReason.STRUCTURE);
                if (captain != null) {
                    captain.setCustomName(Component.translatable("entity.oceanexpansion.drowned_captain"));
                    if (spawn(level, captain, pos, 0)) {
                        risen++;
                        equip(captain, EquipmentSlot.HEAD, new ItemStack(Items.GOLDEN_HELMET), .15F);
                        equip(captain, EquipmentSlot.CHEST, new ItemStack(Items.CHAINMAIL_CHESTPLATE), .1F);
                        equip(captain, EquipmentSlot.MAINHAND, new ItemStack(Items.TRIDENT), .25F);
                        equip(captain, EquipmentSlot.OFFHAND, new ItemStack(Items.NAUTILUS_SHELL), 1F);
                        toughen(captain, 40, 1.15);
                    }
                }
                for (int i = 1; i < 3; i++) {
                    Mob m = EntityTypes.DROWNED.create(level, EntitySpawnReason.STRUCTURE);
                    if (spawn(level, m, pos, i)) risen++;
                }
                bubbles(level, pos, SoundEvents.DROWNED_AMBIENT_WATER);
            }
            case GUARDIANS -> {
                for (int i = 0; i < 3; i++) {
                    Mob m = EntityTypes.GUARDIAN.create(level, EntitySpawnReason.STRUCTURE);
                    if (spawn(level, m, pos, i)) risen++;
                }
                level.playSound(null, pos, SoundEvents.GUARDIAN_AMBIENT, SoundSource.HOSTILE, 1.4F, .8F);
            }
            case FROZEN_CREW -> {
                for (int i = 0; i < 3; i++) {
                    Mob m = EntityTypes.STRAY.create(level, EntitySpawnReason.STRUCTURE);
                    if (m != null) m.setCustomName(i == 0 ? Component.translatable("entity.oceanexpansion.frozen_sailor") : null);
                    if (spawn(level, m, pos, i)) {
                        risen++;
                        equip(m, EquipmentSlot.HEAD, new ItemStack(Items.LEATHER_HELMET), .1F);
                        if (i == 0) equip(m, EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD), .1F);
                        if (m instanceof AbstractSkeleton s) s.reassessWeaponGoal();
                    }
                }
                level.playSound(null, pos, SoundEvents.STRAY_AMBIENT, SoundSource.HOSTILE, 1.4F, .6F);
                level.sendParticles(ParticleTypes.SNOWFLAKE, pos.getX() + .5, pos.getY() + 1, pos.getZ() + .5, 40, 1, 1, 1, .02);
            }
            case DEEP_LURKERS -> {
                for (int i = 0; i < 2; i++) {
                    Mob m = modded(level, "nsvmobs:angler").orElseGet(() -> EntityTypes.GUARDIAN.create(level, EntitySpawnReason.STRUCTURE));
                    if (spawn(level, m, pos, i)) risen++;
                }
                bubbles(level, pos, SoundEvents.GUARDIAN_AMBIENT);
            }
        }
        return risen;
    }

    private static void bubbles(ServerLevel level, BlockPos pos, net.minecraft.sounds.SoundEvent sound) {
        level.playSound(null, pos, sound, SoundSource.HOSTILE, 1.2F, .7F);
        level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, pos.getX() + .5, pos.getY() + .5, pos.getZ() + .5, 40, 1, .5, 1, .1);
    }

    /** Another mod's mob by id, when that mod is installed. */
    static Optional<Mob> modded(ServerLevel level, String id) {
        return BuiltInRegistries.ENTITY_TYPE.getOptional(Identifier.parse(id))
                .map(type -> type.create(level, EntitySpawnReason.STRUCTURE))
                .filter(e -> e instanceof Mob).map(e -> (Mob) e);
    }

    private static void toughen(Mob m, double health, double scale) {
        var h = m.getAttribute(Attributes.MAX_HEALTH);
        if (h != null) { h.setBaseValue(health); m.setHealth((float) health); }
        var s = m.getAttribute(Attributes.SCALE);
        if (s != null) s.setBaseValue(scale);
    }

    private static boolean spawn(ServerLevel level, Mob m, BlockPos pos, int index) {
        if (m == null) return false;
        int[][] offsets = {{0, 0}, {1, 1}, {-1, 1}, {1, -1}, {-1, -1}};
        int[] o = offsets[index % offsets.length];
        m.snapTo(pos.getX() + .5 + o[0], pos.getY(), pos.getZ() + .5 + o[1], level.getRandom().nextFloat() * 360F, 0F);
        if (!level.noCollision(m)) m.snapTo(pos.getX() + .5, pos.getY(), pos.getZ() + .5, m.getYRot(), 0F);
        m.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.STRUCTURE, null);
        m.setPersistenceRequired();
        return level.addFreshEntity(m);
    }

    private static void equip(Mob m, EquipmentSlot slot, ItemStack stack, float dropChance) {
        m.setItemSlot(slot, stack);
        m.setDropChance(slot, dropChance);
    }
}
