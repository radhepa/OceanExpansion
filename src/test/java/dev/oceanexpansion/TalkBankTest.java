package dev.oceanexpansion;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import dev.oceanexpansion.talk.TalkBank;
import org.junit.jupiter.api.Test;

/** The compiled dialogue (data/oceanexpansion/talk/lines.json) and how a line is picked. */
class TalkBankTest {
    private static final List<String> ROLES = List.of("lightkeeper", "warden", "captain", "smuggler", "chief");
    private static final List<String> TOPICS = List.of("greet", "chat", "work", "news", "adventure", "joke", "heart");

    static TalkBank bank() throws Exception {
        Path path = Path.of("src/main/resources/data/oceanexpansion/talk/lines.json");
        try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            Map<String, Object> raw = new Gson().fromJson(r, new TypeToken<Map<String, Object>>() {}.getType());
            @SuppressWarnings("unchecked") Map<String, List<String>> pools = (Map<String, List<String>>) raw.get("pools");
            @SuppressWarnings("unchecked") Map<String, String> parents = (Map<String, String>) raw.get("parents");
            return new TalkBank(pools, parents);
        }
    }

    private static Map<String, String> fill(boolean rumor) {
        var fill = new java.util.HashMap<>(Map.of("name", "Ansel", "player", "Alex", "place", "Gull Point Light", "time", "evening",
                "chief", "Nell", "captain", "Mira", "item", "trident"));
        if (rumor) fill.putAll(Map.of("rumor_name", "a drowned temple of the Old Tide", "rumor_dir", "north-east", "rumor_dist", "a fair sail"));
        return fill;
    }

    @Test
    void everyRoleHasSomethingToSayOnEveryTopic() throws Exception {
        TalkBank bank = bank();
        assertTrue(bank.size() > 800, "the bank is loaded: " + bank.size());
        Random random = new Random(1);
        for (String role : ROLES) for (String topic : TOPICS) for (int friendship : new int[]{0, 4, 7}) {
            var m = new TalkBank.Moment(role, topic, friendship, "morning", "pickaxe", Set.of("hurt"), true, true);
            var line = bank.pick(m, fill(true), Set.of(), random);
            assertNotNull(line, role + " on " + topic + " at friendship " + friendship);
            assertFalse(line.text().contains("{"), "filled: " + line.text());
        }
    }

    @Test
    void childRolesFallBackToTheirParents() throws Exception {
        TalkBank bank = bank();
        assertFalse(bank.lines("chief", "rumor.none").isEmpty(), "the chief borrows the smugglers' rumor.none");
        assertFalse(bank.lines("captain", "joke").isEmpty(), "the captain borrows the wardens' jokes");
    }

    @Test
    void rumoursNeedARumour() throws Exception {
        TalkBank bank = bank();
        var m = new TalkBank.Moment("smuggler", "news", 3, "noon", "", Set.of(), false, false);
        assertFalse(bank.pools(m).containsKey("rumor"));
        assertTrue(bank.pools(m).containsKey("rumor.none"));
        assertNull(TalkBank.fill("Out {rumor_dir} there's {rumor_name}.", fill(false)), "a rumour line can't be said without one");
        assertEquals("Out north-east there's a drowned temple of the Old Tide.",
                TalkBank.fill("Out {rumor_dir} there's {rumor_name}.", fill(true)));
    }

    @Test
    void recentLinesAreNotRepeated() throws Exception {
        TalkBank bank = bank();
        Random random = new Random(5);
        Set<String> said = new HashSet<>();
        var m = new TalkBank.Moment("lightkeeper", "joke", 2, "noon", "", Set.of(), false, false);
        int pool = bank.lines("lightkeeper", "joke").size();
        for (int i = 0; i < pool; i++) {
            var line = bank.pick(m, fill(false), said, random);
            assertNotNull(line);
            assertTrue(said.add(line.id()), "line " + line.id() + " came round again before the pool was used up");
        }
    }

    @Test
    void timesOfDay() {
        assertEquals("morning", TalkBank.greetingTime("dawn"));
        assertNull(TalkBank.greetingTime("noon"));
        assertEquals("night", TalkBank.timeWord("late"));
        assertEquals("afternoon", TalkBank.timeWord("noon"));
    }
}
