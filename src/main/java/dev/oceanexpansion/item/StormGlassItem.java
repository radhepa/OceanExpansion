package dev.oceanexpansion.item;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/**
 * A lightkeeper's storm glass: its crystals cloud before weather turns. Use it to read the sky: how long the fair
 * spell has left, or how long the rain or the storm will last.
 */
public class StormGlassItem extends Item {
    public StormGlassItem(Properties properties) { super(properties); }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
            sp.sendOverlayMessage(Component.translatable(reading(server)));
            server.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, .6F, 1.2F);
            player.getCooldowns().addCooldown(player.getItemInHand(hand), 40);
        }
        return InteractionResult.SUCCESS;
    }

    /** The glass's reading, as a translation key. */
    static String reading(ServerLevel level) {
        var w = level.getWeatherData();
        String base = "item.oceanexpansion.storm_glass.";
        if (w.isThundering()) return base + (w.getThunderTime() > 6000 ? "storm_long" : "storm_short");
        if (w.isRaining()) {
            if (w.getThunderTime() < w.getRainTime() && w.getThunderTime() < 3000) return base + "storm_coming";
            return base + (w.getRainTime() > 6000 ? "rain_long" : "rain_short");
        }
        if (w.getClearWeatherTime() > 0) return base + "fair_long";
        int until = w.getRainTime();
        if (until < 2400) return base + "rain_soon";
        if (until < 12000) return base + "rain_today";
        return base + "fair_long";
    }
}
