"""Make two "friend groups" of real (anonymous) US users from two random k-means taste clusters.

Usage: python3 friends.py [path/to/archive.zip]   (run genres.py first)
Writes friend_groups.json.
"""
import csv, io, json, math, random, sys, zipfile
from collections import Counter
from pathlib import Path

ZIP = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "archive (1).zip")
HERE = Path(__file__).parent
PRIVATE = HERE / "private"  # git-ignored: holds the real dataset user IDs of the picked friends
K, SEED = 9, 42
COUNTRY = "United States"
MIN_LABELED = 0.6        # share of a user's top-artist plays that must fall on a genre-labeled artist
GROUP_SIZES = (4, 8)     # each friend group gets a random size in this range
EXTRA_GENRE, EXTRA_SIZE = "k-pop", 5  # third group for the app: the cluster that leans hardest into this genre
SILHOUETTE_SAMPLE = 1000  # shortcut: silhouette estimated on 1,000 users (exact is O(n^2)); fine for a demo score

FAKE_NAMES = ["Maya Ortiz", "Jordan Lee", "Priya Shah", "Marcus Bell", "Sofia Reyes", "Ethan Brooks", "Ava Kim",
              "Noah Grant", "Leila Haddad", "Caleb Ward", "Zoe Park", "Diego Morales", "Hannah Cole", "Isaac Fox",
              "Nina Patel", "Owen Hart", "Ruby Chen", "Tyler Nash", "Grace Diaz", "Eli Turner", "Chloe Adams",
              "Jamal Price", "Lucy Moreno", "Ben Carter"]


def sq_norm(v):
    return sum(x * x for x in v.values())


def dist2_c(u, c, c_norm):
    """Squared distance between sparse user u and dense centroid c (c_norm = |c|^2)."""
    return c_norm + sum(x * x - 2 * x * c[g] for g, x in u.items())


def dist_uu(u, v):
    s = sum((x - v.get(g, 0.0)) ** 2 for g, x in u.items()) + sum(y * y for g, y in v.items() if g not in u)
    return math.sqrt(s)


def kmeans(vecs, k, rng, iters=50):
    genres = sorted({g for v in vecs for g in v})
    dense = lambda v: {g: v.get(g, 0.0) for g in genres}
    cents = [dense(rng.choice(vecs))]
    while len(cents) < k:  # k-means++ init: favor points far from existing centers
        norms = [sq_norm(c) for c in cents]
        d = [min(dist2_c(v, c, n) for c, n in zip(cents, norms)) for v in vecs]
        cents.append(dense(rng.choices(vecs, weights=d)[0]))
    for _ in range(iters):
        norms = [sq_norm(c) for c in cents]
        labels = [min(range(k), key=lambda j: dist2_c(v, cents[j], norms[j])) for v in vecs]
        sums, counts = [Counter() for _ in range(k)], Counter(labels)
        for v, l in zip(vecs, labels):
            sums[l].update(v)
        new = [{g: sums[j][g] / counts[j] for g in genres} if counts[j] else cents[j] for j in range(k)]
        if new == cents:
            break
        cents = new
    norms = [sq_norm(c) for c in cents]
    inertia = sum(dist2_c(v, cents[l], norms[l]) for v, l in zip(vecs, labels))
    return cents, labels, inertia


def silhouette(vecs, labels, k, rng, sample):
    """Mean silhouette over a random sample of points, each compared against all points."""
    total = 0.0
    idx = rng.sample(range(len(vecs)), min(sample, len(vecs)))
    for i in idx:
        sums, counts = [0.0] * k, [0] * k
        for j, v in enumerate(vecs):
            if j != i:
                sums[labels[j]] += dist_uu(vecs[i], v)
                counts[labels[j]] += 1
        own = labels[i]
        if counts[own] == 0:
            continue  # singleton cluster: silhouette is 0 by convention
        a = sums[own] / counts[own]
        b = min(sums[j] / counts[j] for j in range(k) if j != own and counts[j])
        total += (b - a) / max(a, b) if max(a, b) else 0.0
    return total / len(idx)


def load_users():
    genre_of = {r["artist_name"]: r["genre"] for r in csv.DictReader(open(HERE / "artist_genres.csv", encoding="utf-8"))
                if r["genre"] != "other"}
    with zipfile.ZipFile(ZIP) as z:
        with z.open("archive/users.csv") as f:
            wanted = {r["user_id"] for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""))
                      if r["country"] == COUNTRY}
        users = []  # (user_id, share_vector, top5_artists)
        cur, total, labeled, top5, done = None, 0, Counter(), [], set()

        def finish():
            if cur not in wanted or total == 0:
                return
            lab = sum(labeled.values())
            if lab / total >= MIN_LABELED:
                users.append((cur, {g: p / lab for g, p in labeled.items()}, top5))

        with z.open("archive/user_top_artists.csv") as f:
            for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                uid = row["user_id"]
                if uid != cur:
                    finish()
                    assert uid not in done, f"file not grouped by user (user {uid} seen twice)"
                    done.add(cur)
                    cur, total, labeled, top5 = uid, 0, Counter(), []
                if uid not in wanted:
                    continue
                p = int(row["playcount"] or 0)
                total += p
                if row["artist_name"] in genre_of:
                    labeled[genre_of[row["artist_name"]]] += p
                if len(top5) < 5:
                    top5.append([row["artist_name"], p, genre_of.get(row["artist_name"], "other")])
            finish()
    return users, len(wanted)


def main():
    rng = random.Random(SEED)
    print(f"Building genre profiles for {COUNTRY} users (streams ~1.4 GB)...", flush=True)
    users, n_country = load_users()
    vecs = [u[1] for u in users]
    print(f"{COUNTRY} users: {n_country:,}; with >= {MIN_LABELED:.0%} labeled plays: {len(users):,}. k-means (k={K})...", flush=True)
    cents, labels, inertia = kmeans(vecs, K, rng)
    sizes = Counter(labels)
    print(f"Silhouette on {SILHOUETTE_SAMPLE:,} users...", flush=True)
    sil = silhouette(vecs, labels, K, rng, SILHOUETTE_SAMPLE)

    eligible = [j for j in range(K) if sizes[j] >= GROUP_SIZES[1]]
    chosen = rng.sample(eligible, 2)  # two random clusters, not the most distant pair
    names = rng.sample(FAKE_NAMES, 2 * GROUP_SIZES[1])

    groups = []
    for j in chosen:
        members = [i for i, l in enumerate(labels) if l == j]
        picks = rng.sample(members, rng.randint(*GROUP_SIZES))
        groups.append({
            "cluster": j,
            "cluster_size": sizes[j],
            "genre_mix": sorted(((g, round(s, 3)) for g, s in cents[j].items() if s >= 0.01), key=lambda x: -x[1]),
            "members": [{
                "name": names.pop(),
                "user_id": users[i][0],
                "country": COUNTRY,
                "genres": sorted(((g, round(s, 3)) for g, s in vecs[i].items()), key=lambda x: -x[1])[:5],
                "top_artists": users[i][2],
            } for i in picks],
        })

    # Extra group for the app: drawn after the two random groups so those stay identical across runs.
    used = {m["name"] for g in groups for m in g["members"]}
    extra = max((j for j in eligible if j not in chosen), key=lambda j: cents[j].get(EXTRA_GENRE, 0))
    spare = [n for n in FAKE_NAMES if n not in used]
    rng.shuffle(spare)
    members = [i for i, l in enumerate(labels) if l == extra]
    groups.append({
        "cluster": extra,
        "cluster_size": sizes[extra],
        "genre_mix": sorted(((g, round(s, 3)) for g, s in cents[extra].items() if s >= 0.01), key=lambda x: -x[1]),
        "members": [{"name": spare.pop(), "user_id": users[i][0], "country": COUNTRY,
                     "genres": sorted(((g, round(s, 3)) for g, s in vecs[i].items()), key=lambda x: -x[1])[:5],
                     "top_artists": users[i][2]} for i in rng.sample(members, EXTRA_SIZE)],
    })
    chosen.append(extra)

    clusters = [{"cluster": j, "size": sizes[j],
                 "top_genres": sorted(((g, round(s, 3)) for g, s in cents[j].items()), key=lambda x: -x[1])[:3]}
                for j in sorted(range(K), key=lambda j: -sizes[j])]
    out = {"country": COUNTRY, "country_users": n_country, "sample_users": len(users), "k": K,
           "scores": {"inertia": round(inertia, 2), "inertia_per_user": round(inertia / len(users), 4),
                      "silhouette": round(sil, 3), "silhouette_sample": SILHOUETTE_SAMPLE},
           "clusters": clusters, "groups": groups}
    # Real dataset user IDs stay local (private/ is git-ignored); shared files use the invented first name as the key.
    ids = {}
    for g in groups:
        for m in g["members"]:
            m["key"] = m["name"].split()[0].lower()
            assert m["key"] not in ids, f"duplicate first name {m['key']}"
            ids[m["key"]] = m.pop("user_id")
    PRIVATE.mkdir(exist_ok=True)
    (PRIVATE / "user_ids.json").write_text(json.dumps(ids, indent=1))
    (HERE / "friend_groups.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    print(f"\nScores (k={K}): inertia {inertia:,.1f} ({inertia / len(users):.4f} per user), silhouette {sil:.3f}")
    for c in clusters:
        mark = "  <- picked" if c["cluster"] in chosen else ""
        print(f"  cluster {c['cluster']}: {c['size']:>5,} users  {c['top_genres']}{mark}")
    for n, g in enumerate(groups, 1):
        print(f"\nFriend group {n} (cluster {g['cluster']}, {len(g['members'])} people): {g['genre_mix'][:4]}")
        for m in g["members"]:
            print(f"  {m['name']:<14} {[a[0] for a in m['top_artists']]}")


if __name__ == "__main__":
    toy = [{"rock": 1.0}, {"rock": 0.9, "pop": 0.1}, {"pop": 1.0}, {"pop": 0.95, "rock": 0.05}]
    _, lab, _ = kmeans(toy, 2, random.Random(0))
    assert lab[0] == lab[1] != lab[2] == lab[3], lab
    assert silhouette(toy, lab, 2, random.Random(0), 4) > 0.8
    main()
