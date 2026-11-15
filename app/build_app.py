"""JamVibe demo: write real pipeline data into app/index.html (between the generated-data markers) and make the publish copy.

Usage: python3 app/build_app.py [path/to/archive.zip]   (run friends.py first)
       python3 app/build_app.py --copy-only             (after editing index.html: refresh artifact.html only)
Only the block between the markers is replaced, so hand edits to CONFIG/TEXT and app code are kept.
Real dataset user IDs are never written into the app; people are keyed by their invented first name.
"""
import base64, csv, io, json, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
ZIP = next((a for a in sys.argv[1:] if not a.startswith("--")), str(Path.home() / "archive (1).zip"))
APP = HERE / "index.html"
PUBLISH = HERE / "artifact.html"  # same app without the <html>/<head> wrapper, for the claude.ai artifact
GROUP_KEYS = [("pop", "pop"), ("hiphop", "hip hop"), ("kpop", "k-pop")]  # (key, expected top genre), in friend_groups.json order
OTHER_SHARE_CAP = 0.5  # shortcut: caps plays outside a person's top 50 so simulated months stay about named artists
BEGIN, END = "/* <generated-data> do not edit by hand: python3 app/build_app.py rewrites this block */", "/* </generated-data> */"


FONTS = [("Bricolage", "bricolage-grotesque-display.woff2", "600 800"),   # (CSS family, file in app/fonts, weight range)
         ("Instrument Sans", "instrument-sans.woff2", "400 700")]
FONT_BEGIN, FONT_END = "/* <embedded-fonts> written by app/build_app.py from app/fonts (SIL OFL) */", "/* </embedded-fonts> */"


def embed_fonts(html):
    """Inline the woff2 files as data: URIs so the app needs no font requests (works offline)."""
    if FONT_BEGIN not in html:
        return html
    faces = "\n".join(
        f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-style: normal; font-display: swap; '
        f'src: url(data:font/woff2;base64,{base64.b64encode((HERE / "fonts" / f).read_bytes()).decode()}) format("woff2"); }}'
        for fam, f, w in FONTS)
    return re.sub(re.escape(FONT_BEGIN) + ".*?" + re.escape(FONT_END), lambda _: f"{FONT_BEGIN}\n{faces}\n{FONT_END}", html, flags=re.S)


def write_publish_copy(html):
    """<title> through </head> plus the body, without the document wrapper the artifact host adds."""
    head = re.search(r"(<title>.*?)</head>", html, re.S).group(1)
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    PUBLISH.write_text(head + body)


def main():
    if "--copy-only" in sys.argv:  # after editing CONFIG/TEXT in index.html: refresh fonts + artifact.html without re-reading the zip
        html = embed_fonts(APP.read_text())
        APP.write_text(html)
        write_publish_copy(html)
        print(f"wrote {APP.name} (fonts) and {PUBLISH.name}")
        return
    fg = json.loads((ROOT / "friend_groups.json").read_text())
    assert len(fg["groups"]) == len(GROUP_KEYS), "expected 3 groups in friend_groups.json; rerun friends.py"
    genre_of = {r["artist_name"]: r["genre"] for r in csv.DictReader(open(ROOT / "artist_genres.csv", encoding="utf-8"))
                if r["genre"] != "other"}

    uid = json.loads((ROOT / "private" / "user_ids.json").read_text())  # key -> real dataset ID, local only
    key_of, groups = {}, {}
    for (gkey, expect), g in zip(GROUP_KEYS, fg["groups"]):
        assert g["genre_mix"][0][0] == expect, f"group order changed: {gkey} leads with {g['genre_mix'][0][0]}"
        groups[gkey] = []
        for m in g["members"]:
            k = m["key"]
            assert k not in key_of.values(), f"duplicate first name {k}"
            key_of[uid[k]] = k
            groups[gkey].append(k)

    top50 = {k: [] for k in key_of.values()}
    scrobbles = {}
    with zipfile.ZipFile(ZIP) as z:
        with z.open("archive/users.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                if r["user_id"] in key_of:
                    scrobbles[key_of[r["user_id"]]] = int(r["total_scrobbles"] or 0)
        print(f"Reading top-50 artists for {len(key_of)} people (streams ~1.4 GB)...", flush=True)
        with z.open("archive/user_top_artists.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                if r["user_id"] in key_of:
                    top50[key_of[r["user_id"]]].append([r["artist_name"], int(r["playcount"] or 0)])

    people = {}
    for k, arts in top50.items():
        arts.sort(key=lambda a: -a[1])
        assert arts, f"no artists for {k}"
        named = sum(p for _, p in arts)
        total = max(scrobbles.get(k, 0), named)
        people[k] = {"top50": arts, "allTimePlays": total,
                     "otherShare": round(min(OTHER_SHARE_CAP, 1 - named / total), 3)}
    artists = {a for p in people.values() for a, _ in p["top50"]}
    data = {"source": "Last.fm public dataset (anonymous listeners); genres from MusicBrainz",
            "people": people, "groups": groups,
            "genres": {a: genre_of[a] for a in sorted(artists) if a in genre_of}}

    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")  # can't close the <script>
    block = f"{BEGIN}\nconst DATA = {js};\n{END}"
    html = APP.read_text()
    assert html.count(BEGIN) == 1 and html.count(END) == 1, "generated-data markers missing in index.html"
    html = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda _: block, html, flags=re.S)
    html = embed_fonts(html)
    APP.write_text(html)

    write_publish_copy(html)
    print(f"wrote {APP.name} and {PUBLISH.name}: {len(people)} people, {len(data['genres'])} artists with a genre")


if __name__ == "__main__":
    main()
