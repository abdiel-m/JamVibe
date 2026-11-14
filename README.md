# JamVibe

A project for **Startup Launch Weekend x AI Hackathon 2026**.

A music friend-group app: leaderboards for any artist, compatibility between friends, a monthly race where everyone starts at zero, challenges, and a monthly recap with share cards.

This repo holds a working **demo** built on real, anonymous listening data.

## Try the demo

Open `app/index.html` in any browser. It's one self-contained file: no server, no login, no network requests, and it works offline.

The demo viewer is **Grace**, in the *Mostly Pop* group. Join a third group with the code **ROOMIES**.

## What's real and what's simulated

- **Real:** each person's all-time top-50 artists and play counts, from a public Last.fm dataset of anonymous listeners. Used for all-time leaderboards, compatibility, Group Sound and group vs. group.
- **Simulated:** anything monthly (this month, last month, the race, alerts, challenges). The dataset has no dates, so monthly plays are generated from each person's real play shares. These screens are labeled "Simulated month · example numbers".
- **Invented:** the names. No real user IDs appear in the app.

## Editing the app

In `app/index.html`, everything editable is in the **EDIT HERE: CONFIG + TEXT** block at the top of the script: the app name, people and avatar colors, group names and join codes, starting challenges, award wording, simulation settings, and every sentence shown in the app.

Don't edit the **generated-data** block by hand. The pipeline rewrites it.

After editing, refresh the copy used for publishing:

```
python3 app/build_app.py --copy-only
```

## Data pipeline

The scripts expect the dataset zip at `~/archive (1).zip`, or a path given as the first argument. The zip is not in this repo: it's 2.4 GB.

| Step | Script | Output |
|---|---|---|
| 1. Genres for the 300 most-played artists (MusicBrainz, 1 request/sec, cached) | `genres.py` | `artist_genres.csv`, `genre_cache.json` |
| 2. US taste clusters (k-means, k=9) and three friend groups | `friends.py` | `friend_groups.json` |
| 3. Real top-50 artists written into the app | `app/build_app.py` | `app/index.html`, `app/artifact.html` |

Python 3 standard library only. No packages to install.

## Credits and licenses

- Listening data: a public Last.fm dataset of anonymous listeners.
- Genre data: [MusicBrainz](https://musicbrainz.org), licensed CC BY-NC-SA 3.0 (attribution, non-commercial). Replace it before any commercial use.

## Team

- [@abdiel-m](https://github.com/abdiel-m)
- [@drewsswrlddd](https://github.com/drewsswrlddd)
