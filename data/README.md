# data

DOIs, titles, years, screening decisions and scores. There are no abstracts and no raw
Scopus or Web of Science records here.

- `screening_decisions.csv`: one row for each of the 483 screened records, plus one row
  (UID 507) for the article added by citation snowballing, so 484 rows in all. It gives the
  decision (Include or Exclude), the exclusion reason, how the decision was reached, and the
  hazard and capability codes of the included records.
- `priority_ranking.csv`: the 255 in-scope records found through the database searches,
  with their priority score, the six sub-scores and an `in_core_100` flag. The snowballed
  article was added by hand and is not scored.
- `synthesis_core_100.csv`: the 100 papers in the core set.

The 256 included records are 113 landslide, 69 multi-hazard, 34 GLOF and glacier, 33 flood
and 7 drought papers. A capability code is given for 231 of them, which is the set shown in
Figure 3 of the paper. Records without a code are left blank.

`screen_confidence` shows how a decision was reached. `rule-High` and `rule-Medium` mean the
keyword score was high or medium and the decision was confirmed by reading the record;
`reviewed-Include` and `reviewed-Exclude` mean the record was borderline and was settled by
reading the abstract or full text. The snowballed article is marked `added-by-snowballing`.

Capability codes and the names used in the paper:

| Code | Name in the paper |
|---|---|
| Inventory & susceptibility | Inventory and susceptibility mapping |
| Monitoring & deformation | Monitoring and change detection |
| Forecasting & modelling | Forecasting and modeling |
| Early warning & operational | Early warning and decision support |

The implementation-evidence levels in Table 1 of the paper were coded by hand and are not
listed in these files.
