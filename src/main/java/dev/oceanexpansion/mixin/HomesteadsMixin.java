package dev.oceanexpansion.mixin;

import dev.oceanexpansion.resident.Residents;
import dev.villagefriends.homestead.Homesteads;
import dev.villagefriends.routine.Routine;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.npc.villager.Villager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Village Friends asks its homestead hooks about every dweller's day; for sea-site residents Ocean Expansion answers
 * (their plan, what they're doing, where they go, the "Lives at" line). Everyone else is left to Village Friends.
 */
@Mixin(Homesteads.class)
public abstract class HomesteadsMixin {
    @Inject(method = "plan", at = @At("HEAD"), cancellable = true)
    private static void oceanexpansion$plan(Villager v, Routine.Plan plan, int time, CallbackInfoReturnable<Routine.Plan> cir) {
        Routine.Plan ours = Residents.plan(v, plan, time);
        if (ours != null) cir.setReturnValue(ours);
    }

    @Inject(method = "doing", at = @At("HEAD"), cancellable = true)
    private static void oceanexpansion$doing(Villager v, Routine.Plan plan, CallbackInfoReturnable<String> cir) {
        if (Residents.ours(v)) cir.setReturnValue(Residents.doing(v, plan));
    }

    @Inject(method = "steer", at = @At("HEAD"), cancellable = true)
    private static void oceanexpansion$steer(Villager v, ServerLevel level, Routine.Plan plan, CallbackInfoReturnable<Boolean> cir) {
        if (Residents.ours(v)) cir.setReturnValue(Residents.steer(v, level, plan));
    }

    @Inject(method = "about", at = @At("HEAD"), cancellable = true)
    private static void oceanexpansion$about(Villager v, CallbackInfoReturnable<String> cir) {
        String about = Residents.about(v);
        if (about != null) cir.setReturnValue(about);
    }
}
