-- =============================================================================
-- Normalized SQLite schema — primary dataset (Spotify Tracks)
-- =============================================================================
-- The raw file mixes three things in one flat table: track metadata, the
-- genres a track belongs to (many-to-many), and its artists (many-to-many).
-- We split them into dimension + bridge tables so each fact is stored once.
--
--   tracks 1─1 audio_features
--   tracks *─* genres   (via track_genres)
--   tracks *─* artists  (via track_artists)
--
-- Re-runnable: dropping in reverse-dependency order lets this script rebuild
-- the database from scratch.
-- =============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS track_artists;
DROP TABLE IF EXISTS track_genres;
DROP TABLE IF EXISTS audio_features;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS tracks;

-- One row per unique track. popularity is Spotify's proprietary 0-100 score
-- (NOT play count) — a caveat carried through to the modeling limitations.
CREATE TABLE tracks (
    track_id     TEXT    PRIMARY KEY,
    track_name   TEXT    NOT NULL,
    album_name   TEXT,
    popularity   INTEGER NOT NULL CHECK (popularity BETWEEN 0 AND 100),
    duration_ms  INTEGER NOT NULL,
    explicit     INTEGER NOT NULL CHECK (explicit IN (0, 1))
);

-- 1:1 with tracks. Audio-feature ranges noted inline for shared expectations.
CREATE TABLE audio_features (
    track_id          TEXT    PRIMARY KEY,
    danceability      REAL,                 -- 0..1
    energy            REAL,                 -- 0..1
    key               INTEGER,              -- 0..11 pitch class
    loudness          REAL,                 -- dB, roughly -60..0
    mode              INTEGER,              -- 0 = minor, 1 = major
    speechiness       REAL,                 -- 0..1
    acousticness      REAL,                 -- 0..1
    instrumentalness  REAL,                 -- 0..1
    liveness          REAL,                 -- 0..1
    valence           REAL,                 -- 0..1 (musical positivity)
    tempo             REAL,                 -- BPM (> 0 after cleaning)
    time_signature    INTEGER,              -- beats per bar
    FOREIGN KEY (track_id) REFERENCES tracks (track_id)
);

-- Genre dimension: 114 genre strings stored once, keyed by a surrogate integer.
CREATE TABLE genres (
    genre_id    INTEGER PRIMARY KEY,
    genre_name  TEXT    NOT NULL UNIQUE
);

-- Bridge: many-to-many between tracks and genres.
CREATE TABLE track_genres (
    track_id  TEXT    NOT NULL,
    genre_id  INTEGER NOT NULL,
    PRIMARY KEY (track_id, genre_id),
    FOREIGN KEY (track_id) REFERENCES tracks (track_id),
    FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
);

-- Artist dimension: unique artist name keyed by a surrogate integer.
CREATE TABLE artists (
    artist_id    INTEGER PRIMARY KEY,
    artist_name  TEXT    NOT NULL UNIQUE
);

-- Bridge: many-to-many between tracks and artists. position 0 = primary artist.
CREATE TABLE track_artists (
    track_id   TEXT    NOT NULL,
    artist_id  INTEGER NOT NULL,
    position   INTEGER NOT NULL,
    PRIMARY KEY (track_id, artist_id),
    FOREIGN KEY (track_id)  REFERENCES tracks (track_id),
    FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
);

-- Indexes serve the Phase 2 analysis queries, not built speculatively.
CREATE INDEX idx_track_genres_genre   ON track_genres (genre_id);
CREATE INDEX idx_tracks_popularity    ON tracks (popularity);
CREATE INDEX idx_track_artists_artist ON track_artists (artist_id);
