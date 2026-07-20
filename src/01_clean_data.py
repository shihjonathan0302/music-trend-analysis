"""
Phase 1a — Clean the two raw Kaggle datasets and write tidy CSVs to data/processed/.

Datasets:
  1. data/raw/spotify_tracks.csv       — maharshipandya/-spotify-tracks-dataset (114k tracks,
                                          audio features + popularity + a single `track_genre` label)
  2. data/raw/tracks_1921_2020.csv     — yamaerenay/spotify-dataset-19212020-600k-tracks
                                          (audio features + release_date, NO genre column)

Schema overlap / divergence (this drives the DB design in schema.sql):
  * Audio feature columns are identical in name & scale across both datasets
    (danceability, energy, key, loudness, mode, speechiness, acousticness,
    instrumentalness, liveness, valence, tempo, time_signature).
  * Genre exists ONLY in the primary dataset, and as a flat label per row.
    The same track_id appears once PER genre playlist it was sampled from, so
    "one row = one track" is FALSE in the raw file — we split that into a
    tracks table + a track_genres bridge instead of silently deduping.
  * Release year exists ONLY in the historical dataset (release_date, sometimes
    just a year). The two datasets share some track_ids but we deliberately do
    NOT join them row-by-row: popularity was snapshotted years apart, so a join
    would mix incomparable popularity scores. They stay separate fact tables.
  * Historical `artists` column is a stringified Python list; primary uses
    semicolon-separated names. Both are exploded into a track_artists bridge.
"""

import ast
import pathlib

import pandas as pd

RAW = pathlib.Path("data/raw")
OUT = pathlib.Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

AUDIO_COLS = [
    "danceability", "energy", "key", "loudness", "mode", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
    "time_signature",
]


def clean_primary() -> None:
    df = pd.read_csv(RAW / "spotify_tracks.csv", index_col=0)

    # Basic hygiene: a handful of rows have null artists/track_name; they are
    # unusable for the artist dimension and <0.01% of rows, so drop them.
    df = df.dropna(subset=["track_id", "artists", "track_name"])

    # Range sanity checks (drop rather than clip — out-of-range values here
    # indicate corrupt rows, not measurement noise).
    df = df[df["popularity"].between(0, 100)]
    df = df[df["tempo"] > 0]                      # tempo == 0 is a known extraction failure
    df = df[df["duration_ms"].between(30_000, 1_800_000)]  # <30s or >30min: skits/audiobooks

    # One track can appear under several genre playlists → bridge table.
    track_genres = df[["track_id", "track_genre"]].drop_duplicates()
    track_genres.to_csv(OUT / "track_genres.csv", index=False)

    # Deduplicate to one row per track. Audio features are identical across the
    # duplicate rows; popularity can differ by a point or two between playlist
    # snapshots, so keep the max (the track's best observed popularity).
    dedup = (
        df.sort_values("popularity", ascending=False)
          .drop_duplicates(subset="track_id", keep="first")
    )

    tracks = dedup[["track_id", "track_name", "album_name", "popularity",
                    "duration_ms", "explicit"]]
    tracks.to_csv(OUT / "tracks.csv", index=False)

    dedup[["track_id"] + AUDIO_COLS].to_csv(OUT / "audio_features.csv", index=False)

    # Explode "A;B;C" artist strings into (track_id, artist_name, position).
    artists = (
        dedup[["track_id", "artists"]]
        .assign(artist_name=lambda d: d["artists"].str.split(";"))
        .explode("artist_name")
    )
    artists["artist_name"] = artists["artist_name"].str.strip()
    artists["position"] = artists.groupby("track_id").cumcount()
    artists[["track_id", "artist_name", "position"]].to_csv(
        OUT / "track_artists.csv", index=False
    )

    print(f"primary: {len(df):,} rows -> {len(tracks):,} unique tracks, "
          f"{track_genres['track_genre'].nunique()} genres")


def clean_historical() -> None:
    df = pd.read_csv(RAW / "tracks_1921_2020.csv")
    df = df.dropna(subset=["id", "name"])
    df = df[df["tempo"] > 0]
    df = df[df["duration_ms"].between(30_000, 1_800_000)]

    # release_date is 'YYYY', 'YYYY-MM' or 'YYYY-MM-DD'; we only need the year.
    df["release_year"] = df["release_date"].str.slice(0, 4).astype(int)
    df = df[df["release_year"].between(1921, 2020)]
    df["decade"] = (df["release_year"] // 10) * 10

    # Artist names arrive as a stringified list, e.g. "['Uli', 'Bob']".
    df["artist_names"] = df["artists"].map(
        lambda s: "; ".join(ast.literal_eval(s)) if isinstance(s, str) else ""
    )

    cols = (["id", "name", "artist_names", "popularity", "duration_ms",
             "explicit", "release_year", "decade"] + AUDIO_COLS)
    df[cols].rename(columns={"id": "track_id", "name": "track_name"}).to_csv(
        OUT / "historical_tracks.csv", index=False
    )
    print(f"historical: {len(df):,} tracks, years "
          f"{df['release_year'].min()}–{df['release_year'].max()}")


if __name__ == "__main__":
    clean_primary()
    clean_historical()
