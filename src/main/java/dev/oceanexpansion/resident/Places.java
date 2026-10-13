package dev.oceanexpansion.resident;

import java.util.List;

/** The names of the lived-in sites: the same for everyone who lives there, different from site to site. Pure. */
public final class Places {
    private Places() {}

    static final List<String> LIGHTS = List.of("Gull Point Light", "Saltmarrow Light", "Widow's Rock Light", "Brineholm Light",
            "Old Crake Light", "Seawatch Light", "Cormorant Light", "Lantern Skerry", "Mistmouth Light", "Greywater Light",
            "Kittiwake Light", "Stormhollow Light", "Farhaven Light", "Lowtide Light");
    static final List<String> FORTS = List.of("Fort Saltmere", "Fort Brinewall", "Tidewatch Keep", "Fort Grayreef", "Fort Shoalgate",
            "Fort Wavebreak", "Fort Kelpmoor", "Seaward Hold", "Fort Coralstone", "Fort Gullcrag", "Fort Deepmarch", "Fort Sternwall");
    static final List<String> ROCKS = List.of("the Brine", "Cutpurse Stack", "Gallows Rock", "the Hollow Tooth", "Black Gull Stack",
            "Quiet Rock", "the Sly Needle", "Rumrunner's Rest", "the Cracked Bell", "Saltlick Stack", "the Grinning Rock",
            "Lantern-Out Rock");

    /** The name of a site of this kind ("lighthouse", "fort", "smugglers"), picked by its seed. */
    public static String name(String site, long seed) {
        List<String> names = switch (site) {
            case "fort" -> FORTS;
            case "smugglers" -> ROCKS;
            default -> LIGHTS;
        };
        return names.get((int) Math.floorMod(Role.mix(seed), (long) names.size()));
    }

    /** "north-east", "south"... from (dx, dz), x east and z south. */
    public static String direction(double dx, double dz) {
        String[] names = {"east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"};
        double angle = Math.toDegrees(Math.atan2(dz, dx));
        int i = (int) Math.floorMod(Math.round(angle / 45.0), 8L);
        return names[i];
    }

    /** How far, as a sailor would put it. */
    public static String distance(double blocks) {
        if (blocks < 200) return "a short row";
        if (blocks < 500) return "a fair sail";
        if (blocks < 1000) return "half a day's sail";
        if (blocks < 1800) return "a long day's sail";
        return "further than most boats go";
    }
}
