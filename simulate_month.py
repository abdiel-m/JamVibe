"""Simulate one month of plays for each friend in friend_groups.json, from their real lifetime habits.

Everyone starts at 0 on day 1. Plays are drawn from each user's real top-50 artist play shares, plus an
"other artists" share for listening outside their top 50 (from total_scrobbles).
Usage: python3 simulate_month.py [path/to/archive.zip]   (run friends.py first)
Writes demo_data.json (friend_groups.json + the simulated month).
"""
import calendar, csv, io, json, math, random, sys, zipfile
from collections import Counter
from datetime import date
from pathlib import Path

ZIP = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "archive (1).zip")
HERE = Path(__file__).parent
YEAR, MONTH, SEED = 2026, 10, 7
MEDIAN_PLAYS, SPREAD, MIN_PLAYS, MAX_PLAYS = 1000, 0.35, 400, 2200  # ~20-50 plays/day for active users
WEEKEND_BOOST = 1.25
OTHER = "Other artists"


def month_total(rng):
    return max(MIN_PLAYS, min(MAX_PLAYS, round(rng.lognormvariate(math.log(MEDIAN_PLAYS), SPREAD))))


def simulate(rng, artists, other_share, days):
    """artists: [(name, lifetime_plays)]. Returns (total, Counter name->plays, daily list)."""
    total = month_total(rng)
    life = sum(p for _, p in artists)
    names = [n for n, _ in artists] + [OTHER]
    weights = [p / life * (1 - other_share) for _, p in artists] + [other_share]
    plays = Counter(rng.choices(names, weights, k=total))
    day_w = [WEEKEND_BOOST if date(YEAR, MONTH, d).weekday() >= 5 else 1.0 for d in range(1, days + 1)]
    daily = [0] * days
    for d in rng.choices(range(days), day_w, k=total):
        daily[d] += 1
    return total, plays, daily


def main():
    rng = random.Random(SEED)
    data = json.loads((HERE / "friend_groups.json").read_text())
    genre_of = {r["artist_name"]: r["genre"] for r in csv.DictReader(open(HERE / "artist_genres.csv", encoding="utf-8"))}
    uid = json.loads((HERE / "private" / "user_ids.json").read_text())  # key -> real dataset ID, local only
    ids = {uid[m["key"]] for g in data["groups"] for m in g["members"]}
    top50 = {i: [] for i in ids}
    scrobbles = {}
    with zipfile.ZipFile(ZIP) as z:
        with z.open("archive/users.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                if r["user_id"] in ids:
                    scrobbles[r["user_id"]] = int(r["total_scrobbles"] or 0)
        print(f"Reading top-50 artists for {len(ids)} friends (streams ~1.4 GB)...", flush=True)
        with z.open("archive/user_top_artists.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                if r["user_id"] in ids:
                    top50[r["user_id"]].append((r["artist_name"], int(r["playcount"] or 0)))

    days = calendar.monthrange(YEAR, MONTH)[1]
    for g in data["groups"]:
        group_genres = Counter()
        for m in g["members"]:
            u = uid[m["key"]]
            arts = top50[u]
            life = sum(p for _, p in arts)
            other_share = max(0.0, 1 - life / scrobbles[u]) if scrobbles.get(u) else 0.0
            total, plays, daily = simulate(rng, arts, other_share, days)
            genres = Counter()
            for name, p in plays.items():
                gname = genre_of.get(name, "other") if name != OTHER else "other"
                if gname != "other":
                    genres[gname] += p
            group_genres.update(genres)
            lab = sum(genres.values()) or 1
            cum, run = [], 0
            for d in daily:
                run += d
                cum.append(run)
            m.update({
                "month_total": total,
                "month_cumulative": cum,
                "month_other_share": round(other_share, 3),
                "top_artists": [[n, p, genre_of.get(n, "other")] for n, p in plays.most_common() if n != OTHER][:5],
                "genres": [(gname, round(p / lab, 3)) for gname, p in genres.most_common(5)],
            })
            assert cum[-1] == total and sum(plays.values()) == total
        lab = sum(group_genres.values()) or 1
        g["month_mix"] = [(gname, round(p / lab, 3)) for gname, p in group_genres.most_common() if p / lab >= 0.01]
        g["members"].sort(key=lambda m: -m["month_total"])
        g["month_total"] = sum(m["month_total"] for m in g["members"])

    data["month"] = {"year": YEAR, "month": MONTH, "label": f"{calendar.month_name[MONTH]} {YEAR}", "days": days,
                     "simulated": True, "median_plays": MEDIAN_PLAYS}
    (HERE / "demo_data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    for n, g in enumerate(data["groups"], 1):
        print(f"\nGroup {n}: {g['month_total']:,} plays in {data['month']['label']}  mix {g['month_mix'][:3]}")
        for m in g["members"]:
            print(f"  {m['name']:<14} {m['month_total']:>5,} plays  other {m['month_other_share']:.0%}  top: {[a[0] for a in m['top_artists'][:3]]}")


if __name__ == "__main__":
    r = random.Random(0)
    t, p, d = simulate(r, [("A", 300), ("B", 100)], 0.5, 31)
    assert sum(d) == t == sum(p.values()) and MIN_PLAYS <= t <= MAX_PLAYS
    assert abs(p["Other artists"] / t - 0.5) < 0.1 and p["A"] > p["B"]
    main()
