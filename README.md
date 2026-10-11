# Multi-hazard remote sensing in Nepal: review pipeline

Scripts and derived data for the literature search and screening behind the review
"Remote sensing and geospatial approaches for multi-hazard monitoring in Nepal:
documented capabilities, operational gaps, and lessons for mountain regions"
(Silwal et al., under review).

The raw Scopus and Web of Science exports are not included, because those databases do
not allow them to be redistributed. Everything else needed to follow the screening and
ranking is here.

## Record counts

Scopus and Web of Science, 2016-2025, five queries (see `docs/search_queries.md`).

| Step | Records |
|---|---|
| Identified (567 Scopus, 795 Web of Science) | 1,362 |
| Duplicates removed | 855 |
| Unique records | 507 |
| Non-article document types removed | 24 |
| Screened | 483 |
| Excluded at screening | 228 |
| Added by citation snowballing | 1 |
| In scope | 256 |
| Core set for the detailed synthesis | 100 |

Exclusions: 160 not a Nepal study area, 52 off-topic, 16 not based on remote sensing.
The core set has 39 landslide, 23 multi-hazard, 16 GLOF, 15 flood and 7 drought papers.

## Folders

```
scripts/   the four Python scripts
data/      screening decisions, priority scores and the 100-paper core (no abstracts)
docs/      the search queries
```

The scripts, in the order they are run:

- `merge_dedupe.py` pools the two databases and removes duplicates
- `classify_screen.py` gives each article a first keyword score and provisional tags
- `finalize_screening.py` combines that score with the decisions made by reading the borderline records
- `rank_priority.py` scores the in-scope articles and picks the core set

## Running it

You need your own Scopus and Web of Science access. Run the queries, export the results
and put them in two folders next to `scripts/`, named `Scopus Search (2016-2025)` and
`Web of Science Search (2016-2025)`. The expected file names are listed at the top of
`merge_dedupe.py`. Then:

```
pip install -r requirements.txt
python scripts/merge_dedupe.py
python scripts/classify_screen.py
python scripts/finalize_screening.py
python scripts/rank_priority.py
```

Intermediate files are written to `scripts/`. They contain abstracts, so they are
listed in `.gitignore`.

## Data and licence

The files in `data/` hold DOIs, titles, years, decisions and scores only. The code is
under the MIT licence (`LICENSE`); the data and docs are under CC BY 4.0.

## Contact

Abinash Silwal, University of Kansas, geospatial.abinash@gmail.com
