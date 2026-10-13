package dev.oceanexpansion.block;

import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.TransparentBlock;

/** Frosted sea glass and its pane (vanilla glass behaviour, our look). */
public final class SeaGlassBlocks {
    private SeaGlassBlocks() {}

    public static final class Glass extends TransparentBlock {
        public Glass(Properties properties) { super(properties); }
    }

    public static final class Pane extends IronBarsBlock {
        public Pane(Properties properties) { super(properties); }
    }
}
