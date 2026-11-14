"""Top-N artists by total plays -> primary MusicBrainz genre; everything else is "other".

Usage: python3 genres.py [path/to/archive.zip]
Writes artist_genres.csv; caches MusicBrainz responses in genre_cache.json.
"""
import csv, io, json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ZIP = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "archive (1).zip")
TOP_N = 300
HERE = Path(__file__).parent
CACHE = HERE / "genre_cache.json"
OUT = HERE / "artist_genres.csv"
UA = "lastfm-genre-demo/0.1 (educational project)"
# shortcut: name search can't tell same-name artists apart; these were checked by hand. Add here if a match looks wrong.
GENRE_OVERRIDES = {"Loona": "k-pop"}  # search finds the Dutch singer; Last.fm's "Loona" is the k-pop group


def artist_totals():
    plays = Counter()
    mbids = defaultdict(Counter)  # name -> mbid votes; names are the key since mbid is sometimes blank
    with zipfile.ZipFile(ZIP) as z, z.open("archive/user_top_artists.csv") as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
            name = row["artist_name"]
            plays[name] += int(row["playcount"] or 0)
            if row["mbid"]:
                mbids[name][row["mbid"]] += 1
    return plays, mbids


def primary_genre(mb_json):
    genres = (mb_json or {}).get("genres") or []
    if not genres:
        return None
    return max(genres, key=lambda g: (g["count"], -len(g["name"])))["name"]


def fetch(mbid):
    return get(f"https://musicbrainz.org/ws/2/artist/{mbid}?inc=genres&fmt=json")


def search(name):
    """MusicBrainz artist search; returns the result list (cached by caller)."""
    q = urllib.parse.quote(f'artist:"{name}" OR alias:"{name}"')
    res = get(f"https://musicbrainz.org/ws/2/artist/?query={q}&limit=5&fmt=json")
    return (res or {}).get("artists", [])


def norm(s):
    """Compare names ignoring case, accents and hyphen style (MusicBrainz writes 'blink‐182' with U+2010)."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[‐-―−]", "-", s).casefold()


def best_match(name, results):
    """First (highest-ranked) result whose name or an alias equals ours."""
    want = norm(name)
    for a in results:
        names = [a.get("name", "")] + [al.get("name", "") for al in a.get("aliases") or []]
        if want in (norm(n) for n in names):
            return a["id"]
    return None


def get(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # cached as "not found" so it is never re-fetched
            if e.code == 503:
                time.sleep(5 * 2 ** attempt)  # 5s..160s; MusicBrainz 503s under load can last a minute+
                continue
            raise
    raise RuntimeError(f"MusicBrainz kept returning 503 for {url}")


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    print("Summing plays per artist (streams ~1.4 GB)...", flush=True)
    plays, mbids = artist_totals()
    top = plays.most_common(TOP_N)

    fetched = 0
    for name, _ in top:
        mbid = mbids[name].most_common(1)[0][0] if mbids[name] else None
        if not mbid or mbid in cache:
            continue
        cache[mbid] = fetch(mbid)
        fetched += 1
        CACHE.write_text(json.dumps(cache))  # save after every call so an interrupt loses nothing
        time.sleep(1.1)  # MusicBrainz limit: 1 request/second
        if fetched % 25 == 0:
            print(f"  fetched {fetched}", flush=True)

    def call(key, fn):
        nonlocal fetched
        if key not in cache:
            cache[key] = fn()
            fetched += 1
            CACHE.write_text(json.dumps(cache))
            time.sleep(1.1)  # MusicBrainz limit: 1 request/second
        return cache[key]

    # Second pass: artists still without a genre (no mbid in the dataset, or an mbid with no genres) get a name search.
    rows, by_search, unresolved = [], [], []
    for name, p in top:
        mbid = mbids[name].most_common(1)[0][0] if mbids[name] else ""
        genre = GENRE_OVERRIDES.get(name) or (primary_genre(cache.get(mbid)) if mbid else None)
        if genre is None:
            found = best_match(name, call(f"search:{name}", lambda: search(name)))
            if found:
                g2 = primary_genre(call(found, lambda: fetch(found)))
                if g2:
                    mbid, genre = found, g2
                    by_search.append(f"{name} -> {genre}")
            if genre is None:
                unresolved.append(name)
        rows.append((name, mbid, p, genre or "other"))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["artist_name", "mbid", "plays", "genre"])
        w.writerows(rows)

    total = sum(plays.values())
    top_plays = sum(p for _, p in top)
    print(f"\nUnique artists: {len(plays):,}   total plays: {total:,}")
    print(f"Top {TOP_N} plays: {top_plays:,} = {top_plays / total:.1%} of all plays")
    labeled = sum(p for (_, _, p, g) in rows if g != "other")
    print(f"Top {TOP_N} with a genre: {labeled / total:.1%} of all plays   fetched this run: {fetched}")
    print(f"Found by name search ({len(by_search)}): {by_search}")
    print(f"Still no genre ({len(unresolved)}): {unresolved}")
    print("Genre counts among top artists:", Counter(r[3] for r in rows).most_common(15))


if __name__ == "__main__":
    assert primary_genre({"genres": [{"name": "rock", "count": 3}, {"name": "pop", "count": 5}]}) == "pop"
    assert primary_genre({"genres": []}) is None and primary_genre(None) is None
    _r = [{"id": "x", "score": 100, "name": "Travis Scott", "aliases": [{"name": "Travi$ Scott"}]},
          {"id": "y", "score": 95, "name": "Drake"}]
    assert best_match("travi$ scott", _r) == "x" and best_match("Drake", _r) == "y" and best_match("Oasis", _r) is None
    assert best_match("JAY-Z", [{"id": "j", "score": 100, "name": "JAŸ‐Z"}]) == "j"
    main()
