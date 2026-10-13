package dev.oceanexpansion.talk;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Everything the sea-site residents can say (data/oceanexpansion/talk/lines.json, compiled by tools/talk/talk.py), and
 * how a line is chosen. Pure: {@link DelveTalk} supplies the moment (who, which topic, what is known) and keeps
 * track of what was said lately.
 *
 * <p>Pools are named {@code <role>.<topic>[.<detail>]}. A role with a parent (the chief's is the smuggler, the
 * captain's the warden) also draws on its parent's pools.
 */
public final class TalkBank {
    /** A chosen line: its id (pool#index, remembered so it isn't repeated soon) and its filled-in text. */
    public record Line(String id, String text) {}

    /** What the moment looks like to the speaker. */
    public record Moment(String role, String topic, int friendship, String period, String held, Collection<String> states,
                         boolean rumor, boolean sea) {}

    private static final Pattern PLACEHOLDER = Pattern.compile("\\{([a-z_]+)}");
    public static final TalkBank EMPTY = new TalkBank(Map.of(), Map.of());

    private final Map<String, List<String>> pools;
    private final Map<String, String> parents;

    public TalkBank(Map<String, List<String>> pools, Map<String, String> parents) {
        this.pools = Map.copyOf(pools);
        this.parents = Map.copyOf(parents);
    }

    public int size() { return this.pools.values().stream().mapToInt(List::size).sum(); }

    /** The lines of {@code role.pool} followed by those of its parent role's pool, and so on up the line. */
    public List<String> lines(String role, String pool) {
        List<String> out = new ArrayList<>();
        for (String r = role; r != null && out.size() < 10_000; r = this.parents.get(r)) {
            List<String> own = this.pools.get(r + "." + pool);
            if (own != null) out.addAll(own);
        }
        return out;
    }

    /** Which pools a moment draws from, and how likely each is (only pools that have lines). */
    public Map<String, Integer> pools(Moment m) {
        var w = new LinkedHashMap<String, Integer>();
        switch (m.topic()) {
            case "greet" -> {
                w.put("greet", 6);
                w.put(m.friendship() >= 3 ? "greet.friend" : "greet.stranger", 4);
                String time = greetingTime(m.period());
                if (time != null) w.put("greet." + time, 3);
                if (!m.held().isEmpty()) w.put("held." + m.held(), 2);
                for (String s : m.states()) w.put("player." + s, 3);
            }
            case "chat" -> {
                w.put("chat", 8);
                if (m.friendship() <= 1) w.put("chat.new", 3);
                if (m.friendship() >= 6) w.put("chat.close", 4);
                w.put("past", m.friendship() >= 3 ? 3 : 2);
                if (m.period().equals("night") || m.period().equals("late")) w.put("night", 3);
                if (!m.held().isEmpty()) w.put("held." + m.held(), 2);
                for (String s : m.states()) w.put("player." + s, 2);
                if (m.rumor()) w.put("rumor", 2);
                if (m.sea()) w.put("seafolk", 1);
            }
            case "work" -> w.put("work", 8);
            case "news" -> {
                w.put("news", 5);
                if (m.rumor()) w.put("rumor", 8); else w.put("rumor.none", 3);
                if (m.sea()) w.put("seafolk", 3);
            }
            case "adventure" -> {
                w.put("adventure", 8);
                if (m.rumor()) w.put("rumor", 3);
            }
            case "joke", "heart" -> w.put(m.topic(), 8);
            default -> w.put("chat", 1);
        }
        w.keySet().removeIf(pool -> this.lines(m.role(), pool).isEmpty());
        return w;
    }

    /**
     * A line for the moment that wasn't said lately and whose placeholders can all be filled, or null if nothing
     * fits. {@code recent} holds ids of lines said lately.
     */
    public Line pick(Moment m, Map<String, String> fill, Collection<String> recent, Random random) {
        var weights = new LinkedHashMap<>(this.pools(m));
        while (!weights.isEmpty()) {
            int total = weights.values().stream().mapToInt(Integer::intValue).sum();
            int roll = random.nextInt(total);
            String pool = null;
            for (var e : weights.entrySet()) { roll -= e.getValue(); if (roll < 0) { pool = e.getKey(); break; } }
            Line line = this.from(m.role(), pool, fill, recent, random);
            if (line != null) return line;
            weights.remove(pool);
        }
        return null;
    }

    /** A line from one pool: one not said lately if possible, else any that can be filled. */
    public Line from(String role, String pool, Map<String, String> fill, Collection<String> recent, Random random) {
        List<String> lines = this.lines(role, pool);
        if (lines.isEmpty()) return null;
        int start = random.nextInt(lines.size());
        Line fallback = null;
        for (int n = 0; n < lines.size(); n++) {
            int i = (start + n) % lines.size();
            String text = fill(lines.get(i), fill);
            if (text == null) continue;
            String id = "oe:" + role + "." + pool + "#" + i;
            if (!recent.contains(id)) return new Line(id, text);
            if (fallback == null) fallback = new Line(id, text);
        }
        return fallback;
    }

    /** The line with its placeholders filled, or null if one has no value now. */
    public static String fill(String line, Map<String, String> fill) {
        Matcher m = PLACEHOLDER.matcher(line);
        StringBuilder out = new StringBuilder();
        while (m.find()) {
            String value = fill.get(m.group(1));
            if (value == null || value.isEmpty()) return null;
            m.appendReplacement(out, Matcher.quoteReplacement(value));
        }
        m.appendTail(out);
        return out.toString();
    }

    /** Which greeting a time of day calls for ("morning", "evening", "night"), or null at midday. */
    public static String greetingTime(String period) {
        return switch (period) {
            case "dawn", "morning" -> "morning";
            case "evening" -> "evening";
            case "night", "late" -> "night";
            default -> null;
        };
    }

    /** The {time} placeholder: morning, afternoon, evening or night. */
    public static String timeWord(String period) {
        return switch (period) {
            case "dawn", "morning" -> "morning";
            case "noon", "afternoon" -> "afternoon";
            case "evening" -> "evening";
            default -> "night";
        };
    }

    /** All pool names (for checks). */
    public List<String> poolNames() { return new ArrayList<>(this.pools.keySet()); }
}
