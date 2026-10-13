package dev.oceanexpansion;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

/**
 * {@code config/oceanexpansion.json}. Written with the defaults the first time the game starts.
 *
 * <ul>
 *   <li>{@code rarity} (default 1.0, 0.25 to 4): how spread out the sea sites are. 2.0 means half as many along each side
 *       (a quarter as many in all), 0.5 twice as many along each side. Only chunks generated afterwards change.</li>
 *   <li>{@code rumors} (default true): residents tell you about the nearest other sea site.</li>
 * </ul>
 */
public record OceanConfig(double rarity, boolean rumors) {
    public static final OceanConfig DEFAULT = new OceanConfig(1.0, true);
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static OceanConfig current;

    public static OceanConfig get() {
        if (current == null) current = load(FabricLoader.getInstance().getConfigDir().resolve("oceanexpansion.json"));
        return current;
    }

    static OceanConfig load(Path path) {
        OceanConfig config = DEFAULT;
        if (Files.isRegularFile(path)) {
            try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
                Raw raw = GSON.fromJson(reader, Raw.class);
                if (raw != null) config = new OceanConfig(clamp(raw.rarity == null ? 1.0 : raw.rarity),
                        raw.rumors == null || raw.rumors);
            } catch (IOException | RuntimeException e) {
                OceanExpansion.LOG.warn("Couldn't read {}, using the defaults: {}", path, e.toString());
            }
        } else {
            try {
                Files.createDirectories(path.getParent());
                try (Writer writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
                    Raw raw = new Raw();
                    raw.rarity = DEFAULT.rarity;
                    raw.rumors = DEFAULT.rumors;
                    GSON.toJson(raw, writer);
                }
            } catch (IOException e) {
                OceanExpansion.LOG.warn("Couldn't write {}: {}", path, e.toString());
            }
        }
        return config;
    }

    /** A structure set's spacing and separation stretched by {@code rarity}; spacing always stays above separation. */
    public static int[] scaled(int spacing, int separation, double rarity) {
        int s = Math.max(4, (int) Math.round(spacing * rarity));
        int sep = Math.max(1, Math.min(s - 2, (int) Math.round(separation * rarity)));
        return new int[]{s, sep};
    }

    public static double clamp(double rarity) {
        return Double.isFinite(rarity) ? Math.max(0.25, Math.min(4.0, rarity)) : 1.0;
    }

    private static final class Raw {
        Double rarity;
        Boolean rumors;
    }
}
