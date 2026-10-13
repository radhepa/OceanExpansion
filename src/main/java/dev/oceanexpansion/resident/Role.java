package dev.oceanexpansion.resident;

import java.util.Collection;
import java.util.List;

import dev.villagefriends.routine.Routine.Block;

/**
 * Who lives at a site: the lightkeeper, the Tidewatch garrison (wardens and their captain) and the smugglers of the
 * Brine Brotherhood (and their chief). A site's template tags each of them ({@code oceanexpansion.resident.<id>});
 * this gives the role its job, its talk, its words for what it is doing, and its day. Pure.
 */
public enum Role {
    LIGHTKEEPER("lightkeeper", "lightkeeper", "oceanexpansion:lightkeeper", 3, 14),
    WARDEN_KNIGHT("warden_knight", "warden", "villagefriends:knight", 2, 20),
    WARDEN_ARCHER("warden_archer", "warden", "villagefriends:archer", 2, 20),
    CAPTAIN("captain", "captain", "villagefriends:knight", 4, 20),
    SMUGGLER("smuggler", "smuggler", "oceanexpansion:smuggler", 2, 16),
    SMUGGLER_BOSS("smuggler_boss", "chief", "oceanexpansion:smuggler", 4, 16);

    public static final String TAG = "oceanexpansion.resident.";
    public static final String DWELLER_PREFIX = "oceanexpansion_";

    private final String id, talk, profession;
    private final int level, tether;

    Role(String id, String talk, String profession, int level, int tether) {
        this.id = id; this.talk = talk; this.profession = profession; this.level = level; this.tether = tether;
    }

    public String id() { return this.id; }
    /** Which lines they speak (data/oceanexpansion/talk): lightkeeper, warden, captain, smuggler or chief. */
    public String talk() { return this.talk; }
    public String profession() { return this.profession; }
    public int level() { return this.level; }
    /** How far they stray from the middle of their site before heading back. */
    public int tether() { return this.tether; }
    /** The role Village Friends keeps in their dweller record. */
    public String dwellerRole() { return DWELLER_PREFIX + this.talk; }
    public boolean guard() { return this == WARDEN_KNIGHT || this == WARDEN_ARCHER || this == CAPTAIN; }
    public boolean smuggler() { return this == SMUGGLER || this == SMUGGLER_BOSS; }
    /** The site a role lives at when the structure can't be found (a resident spawned by hand). */
    public String site() { return this.guard() ? "fort" : this.smuggler() ? "smugglers" : "lighthouse"; }

    public static Role byId(String id) {
        for (Role r : values()) if (r.id.equals(id)) return r;
        return null;
    }

    /** The role an entity's tags give it, or null. */
    public static Role fromTags(Collection<String> tags) {
        for (String tag : tags) if (tag.startsWith(TAG)) { Role r = byId(tag.substring(TAG.length())); if (r != null) return r; }
        return null;
    }

    public static boolean ours(String dwellerRole) { return dwellerRole != null && dwellerRole.startsWith(DWELLER_PREFIX); }

    /** The personality that fits the life (Village Friends personalities). */
    public String personality(long seed) {
        List<String> options = switch (this) {
            case LIGHTKEEPER -> List.of("meticulous", "steadfast", "imaginative", "curious");
            case WARDEN_KNIGHT, WARDEN_ARCHER -> List.of("protective", "steadfast", "pragmatic", "adventurous");
            case CAPTAIN -> List.of("steadfast", "protective");
            case SMUGGLER -> List.of("adventurous", "pragmatic", "warmhearted", "curious");
            case SMUGGLER_BOSS -> List.of("pragmatic", "meticulous");
        };
        return options.get((int) Math.floorMod(mix(seed), (long) options.size()));
    }

    /** Their nameplate: "Keeper Ansel of Gull Point Light", "Captain Mira of Fort Saltmere", "Nell of the Brine". */
    public String label(String name, String place) {
        return switch (this) {
            case LIGHTKEEPER -> "Keeper " + name + " of " + place;
            case WARDEN_KNIGHT, WARDEN_ARCHER -> "Warden " + name + " of " + place;
            case CAPTAIN -> "Captain " + name + " of " + place;
            case SMUGGLER -> name;
            case SMUGGLER_BOSS -> name + ", Chief of " + place;
        };
    }

    /**
     * Their day at sea: no tavern, bell or market. The lightkeeper tends the lamp from dusk to midnight and through
     * storms; the captain and half the wardens keep the wall until midnight; smugglers do their business at night
     * and sleep late.
     */
    public Block adjust(Block block, Block scheduled, int time, boolean watch) {
        int t = Math.floorMod(time, 24000);
        boolean evening = t >= 12500 && t < 18000;   // 18:30 to midnight in Village Friends' clock (0 = 06:00)
        boolean night = t >= 12500 || t < 500;
        switch (this) {
            case LIGHTKEEPER -> {
                if (evening || block == Block.STORM || block == Block.SHELTER) return Block.NIGHT_WATCH;
            }
            case CAPTAIN -> { if (evening) return Block.NIGHT_WATCH; }
            case WARDEN_KNIGHT, WARDEN_ARCHER -> { if (evening && watch) return Block.NIGHT_WATCH; }
            case SMUGGLER, SMUGGLER_BOSS -> {
                if (evening || (night && t < 20000)) return Block.NIGHT_WATCH;
                if (t < 3500 && block.sleep) return Block.SLEEP;
            }
        }
        Block b = switch (block) {
            case SHELTER, STORM, SNOWED_IN, RAIN_WALK, SNOW_PLAY -> scheduled == null || scheduled == block ? Block.WORK : scheduled;
            default -> block;
        };
        return switch (b) {
            case LUNCH, LUNCH_TAVERN -> Block.LUNCH_HOME;
            case SUPPER_TAVERN -> Block.SUPPER;
            case TAVERN, PERFORM -> Block.EVENING;
            case SOCIAL, MARKET, LESSONS, PARTY, PLAY, PRAYER -> Block.HOBBY;
            case NIGHT_WATCH -> Block.SLEEP;
            case DEFEND -> Block.WORK;
            case SHELTER, STORM, SNOWED_IN, RAIN_WALK, SNOW_PLAY -> Block.WORK;
            default -> b;
        };
    }

    /** What they're doing, as their conversation window shows it; null to keep Village Friends' own words. */
    public String doing(Block block) {
        return switch (this) {
            case LIGHTKEEPER -> switch (block) {
                case WORK -> "Polishing the great lens"; case HOBBY -> "Mending nets"; case EVENING -> "Writing the Lamp Log";
                case NIGHT_WATCH -> "Keeping the light"; case LUNCH_HOME, SUPPER, BREAKFAST -> "Eating fish stew"; default -> null; };
            case WARDEN_KNIGHT, WARDEN_ARCHER -> switch (block) {
                case WORK -> "Drilling in the yard"; case HOBBY -> "Scraping salt off their kit"; case EVENING -> "Off watch";
                case NIGHT_WATCH -> "Walking the sea wall"; case LUNCH_HOME, SUPPER, BREAKFAST -> "At mess"; default -> null; };
            case CAPTAIN -> switch (block) {
                case WORK -> "Inspecting the fort"; case HOBBY -> "Reading the Tide Log"; case EVENING -> "Writing the Tide Log";
                case NIGHT_WATCH -> "Watching the water from the keep"; case LUNCH_HOME, SUPPER, BREAKFAST -> "At mess"; default -> null; };
            case SMUGGLER -> switch (block) {
                case WORK -> "Shifting crates"; case HOBBY -> "Playing dice"; case EVENING -> "Watching for sails";
                case NIGHT_WATCH -> "Running cargo"; case LUNCH_HOME, SUPPER, BREAKFAST -> "Eating ship's biscuit"; default -> null; };
            case SMUGGLER_BOSS -> switch (block) {
                case WORK -> "Going over the ledger"; case HOBBY -> "Counting coin"; case EVENING -> "Planning a run";
                case NIGHT_WATCH -> "Giving orders on the dock"; case LUNCH_HOME, SUPPER, BREAKFAST -> "Dining alone"; default -> null; };
        };
    }

    /** "Lives at" line for their About page. */
    public String about(String place) {
        return switch (this) {
            case LIGHTKEEPER -> "\nKeeps: " + place + " (a lighthouse on a rock at sea)";
            case WARDEN_KNIGHT, WARDEN_ARCHER, CAPTAIN -> "\nPosted at: " + place + " (a Tidewatch sea fort)";
            case SMUGGLER, SMUGGLER_BOSS -> "\nLives at: " + place + " (no one is supposed to know)";
        };
    }

    static long mix(long seed) {
        long z = seed * 0x9E3779B97F4A7C15L;
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        return z ^ (z >>> 31);
    }
}
