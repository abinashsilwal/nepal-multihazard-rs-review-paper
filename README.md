# Multi-hazard remote sensing in Nepal — systematic review pipeline

Reproducible search, screening, and prioritisation workflow for the review:

> **Remote sensing and geospatial approaches for multi-hazard monitoring in Nepal:
> documented capabilities, operational gaps, and lessons for mountain regions.**

This repository contains the **code, methods records, and derived (DOI-keyed) data**
needed to reproduce the corpus and the synthesis core. It does **not** contain the raw
Scopus or Web of Science exports, which may not be redistributed under those databases'
licences (see *Data availability* below).

---

## What this pipeline does

Two bibliographic databases (Scopus + Web of Science, 2016–2025) were searched with five
Boolean queries, then pooled, de-duplicated, screened, and prioritised to a 100-article
in-depth synthesis core:

| Stage | n |
|------|---|
| Records identified (567 Scopus + 795 WoS) | 1,362 |
| Duplicates removed (DOI / title+year) | −855 |
| Unique records | 507 |
| Non-article types removed | −24 |
| Articles screened | 483 |
| Excluded at screening (manual) | −228 |
| Added via citation snowballing | +1 |
| **In scope** | **256** |
| **In-depth synthesis core** (stratified by hazard) | **100** |

Screening exclusions: 160 not a Nepal study area, 52 off-topic, 16 not remote-sensing-based.
One further article, identified through citation snowballing (to catch studies framed around
sub-national place names such as Khumbu or Langtang rather than "Nepal"), was added on the
same basis.
Core composition: Landslide 39, Multi-hazard 23, GLOF 16, Flood 15, Drought 7.

## Repository layout

```
scripts/      reproducible screening and ranking pipeline (Python)
  merge_dedupe.py        pool both databases, de-duplicate (DOI → title+year → native id)
  classify_screen.py     rule-based relevance scoring + auto-tagging
  finalize_screening.py  combine auto + manual screening decisions
  rank_priority.py       weighted priority score + stratified core selection
data/         derived data only (DOI + title + decisions + scores; NO abstracts)
  screening_decisions.csv   per-article include/exclude + provisional tags
  priority_ranking.csv      priority score, sub-scores, in-core flag
  synthesis_core_100.csv    the 100-article core
docs/         methods records (PRISMA log, screening report, prioritisation method, audit log, queries)
```

## Reproducing the corpus

The raw database exports are not redistributed. To regenerate the corpus with your own
institutional access:

1. In **Scopus** and **Web of Science Core Collection**, run the five queries in
   `docs/search_queries.docx` (TITLE-ABS-KEY / Topic field), limited to 2016–2025.
2. Export each result set and place the files in
   `Scopus Search (2016-2025)/` and `Web of Science Search (2016-2025)/`
   using the file names referenced in `scripts/merge_dedupe.py`.
3. Run the pipeline:

   ```bash
   pip install -r requirements.txt
   python scripts/merge_dedupe.py
   python scripts/classify_screen.py
   python scripts/finalize_screening.py
   python scripts/rank_priority.py
   ```

Re-running on the same exports reproduces the identical unique corpus, screening
decisions, and 100-article core. The `data/` files let you verify decisions and scores
by DOI without the licensed raw records.

## Data availability & licensing

- **Raw Scopus / Web of Science records are NOT included** and must not be redistributed
  under those databases' terms. Only derived, DOI-keyed metadata and decisions are shared.
- **Code** is released under the MIT Licence (`LICENSE`).
- **Documents and derived data** (`docs/`, `data/`) are released under CC-BY-4.0.

## Citation

See `CITATION.cff`. On publication, this repository will be archived to Zenodo and the DOI
added here.

## Author

Abinash Silwal — University of Kansas — geospatial.abinash@gmail.com
       
---

## Archived release (for the paper's Data Availability statement)

To make this repository citable, create a versioned release and archive it on Zenodo:

1. Push this folder to a public GitHub repository.
2. In Zenodo, enable the repository under *Settings → GitHub*, then publish a GitHub
   **release** (e.g. `v1.0`). Zenodo mints a DOI automatically.
3. Add the DOI to the manuscript's *Data availability* statement and to `CITATION.cff`.

Placeholder to replace once minted:

> Silwal, A. (2026). *Multi-hazard remote sensing in Nepal — review pipeline* (v1.0)
> \[Data set]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

Also included: `data/Reliability_double_coding.xlsx`, the implementation-evidence
double-coding sheet used to check inter-rater reliability of the matrix (Supplementary Material).
