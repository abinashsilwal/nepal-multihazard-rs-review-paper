# data

DOIs, titles, years, screening decisions and scores. There are no abstracts and no raw
Scopus or Web of Science records here.

- `screening_decisions.csv`: one row per screened record, with the decision (Include,
  Maybe or Exclude), exclusion reason and provisional tags
- `priority_ranking.csv`: the 256 in-scope papers with their priority score, the six
  sub-scores and an `in_core_100` flag
- `synthesis_core_100.csv`: the 100 papers in the core set

`screening_decisions.csv` was saved before one record was found to be a non-article
document type, so it has 484 rows while the paper reports 483 screened. It also predates
the full-text reading that settled the hazard tag of 9 records. The counts in the main
README are the ones used in the paper.
