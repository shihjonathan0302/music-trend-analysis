# Project Plan — Music Hit & Trend Analysis

A portfolio project demonstrating product-analyst judgment: framing business
questions, building a real data pipeline, modeling what drives a track's
popularity, and translating findings into product recommendations.

**Target completion:** 2026-08-20 · **Started:** 2026-07-24

---

## Data sources (public, no API required)

| Role | Dataset (Kaggle) | Notes |
|---|---|---|
| Primary | `maharshipandya/-spotify-tracks-dataset` | 114k rows, audio features + popularity + per-track genre |
| Secondary | `yamaerenay/spotify-dataset-19212020-600k-tracks` | 586k rows, audio features + release year, **no genre** |

The two datasets are **not joined**: their popularity scores are proprietary
snapshots taken years apart and are not comparable. They share the same audio
feature vocabulary and are integrated at the narrative level, not the row level.

---

## Timeline overview

| Week | Dates | Phase | Deliverable |
|---|---|---|---|
| 1 | Jul 24 – Jul 30 | Data pipeline & schema | Clean data + queryable SQLite database |
| 2 | Jul 31 – Aug 6 | SQL-first analysis | Four business-question analyses |
| 3 | Aug 7 – Aug 13 | Modeling | Explainable popularity model + limitations |
| 4 | Aug 14 – Aug 20 | Output & write-up | Tableau exports, README, case study |

---

## Phase 1 — Data ingestion & schema (Week 1)

- [x] Set up reproducible environment (`.venv` + `requirements.txt`)
- [x] Explore raw data — `notebooks/01_explore.ipynb`
  - [x] Primary: shape, duplicate tracks across genres, missing/impossible values
  - [x] Secondary: release-date parsing, per-decade sample sizes
- [x] Clean the primary dataset → tidy `data/processed/` tables (`notebooks/02_clean_primary.ipynb`)
- [ ] Clean the secondary dataset (deferred; trend module)
- [x] Design normalized SQLite schema (`sql/schema.sql`)
- [x] Load cleaned data into SQLite; verify row counts and foreign-key integrity (`notebooks/03_load_db.ipynb`)

## Phase 2 — Analysis, SQL-first (Week 2)

Each framed as a question a streaming-company hiring manager would ask.

- [ ] **What drives popularity?** Which audio features correlate most with the
      popularity score, overall and by genre.
- [ ] **Is there a "hit formula"?** Do popular tracks cluster into a narrower
      band of audio features than unpopular ones? Implications for playlisting.
- [ ] **Trend over time** (historical dataset). How have tempo, energy, loudness,
      acousticness shifted by decade? Is "songs got louder/more energetic" true?
- [ ] **Genre consistency.** Which genres show the most/least internal variance
      in audio features — musically consistent vs. diverse.

## Phase 3 — Modeling (Week 3)

- [ ] Binarize a "hit" label at a reasonable popularity percentile
- [ ] Explainable model (logistic regression primary; shallow tree as a check)
- [ ] Report feature importance → translate to product/playlisting implications
- [ ] **Limitations section** (as important as the model): proprietary/opaque
      popularity metric, correlation vs. causation, survivorship bias, the ~10%
      of tracks with popularity = 0
- [ ] *Stretch:* k-means clustering of tracks by audio features

## Phase 4 — Output & write-up (Week 4)

- [ ] Export aggregated tables/views for Tableau (features-vs-popularity,
      decade-trend, genre-comparison)
- [ ] Build Tableau Public dashboard (done manually outside this repo)
- [ ] README: problem statement, data sources + attribution, methodology,
      an explicit "where AI accelerated me vs. where I applied judgment" section,
      reproduction steps, links
- [ ] 600–900 word case study: (1) business problem, (2) method + AI vs. judgment,
      (3) findings + honest limitations, (4) what I'd do next with real engagement data

---

## Scope-cut priority (if the timeline slips)

Cut from the top down; never cut the README, case study, or limitations.

1. Drop k-means clustering (stretch goal)
2. Drop the tree-model cross-check (keep logistic regression only)
3. Simplify genre analysis (top ~20 genres instead of all 114)
4. Drop the historical/decade-trend module (self-contained; does not affect the core)

---

## Environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Raw CSVs are not committed (see `.gitignore`); download them from the Kaggle
links above into `data/raw/`.

---

## Progress log

- **2026-07-24** — Environment set up; raw-data exploration notebook complete for
  both datasets. Decision: keep datasets separate (no row-level join); treat the
  historical dataset as an optional, last-to-cut trend module.
- **2026-07-24** — Primary dataset cleaned into 4 tidy tables; normalized SQLite
  schema built and loaded into `db/spotify.db` (89,539 tracks, 114 genres, 29,779
  artists, 0 FK violations). Caught a data gotcha: a literal `"N/A"` artist
  placeholder collided with pandas' default NA tokens on CSV round-trip.
