# Derived data (DOI-keyed)

These files contain **derived metadata and review decisions only** — DOI, title, year,
hazard, screening decision, and priority scores. They contain **no abstracts and no raw
Scopus/Web of Science records**, so they are safe to share under CC-BY-4.0 while respecting
the databases' licensing terms.

| File | One row per | Key fields |
|------|-------------|-----------|
| `screening_decisions.csv` | screened article (484) | DOI, title, year, `screen_include`, `exclude_reason`, `screen_confidence`, provisional tags |
| `priority_ranking.csv` | in-scope article (256) | DOI, hazard, `PriorityScore`, six sub-scores, `in_core_100` |
| `synthesis_core_100.csv` | core article (100) | DOI, title, year, hazard, `PriorityScore` |

Note on counts: `screening_decisions.csv` reflects the screening pass before 9 records
with an unresolved hazard tag were settled by full-text reading, and before one article
was reclassified as a non-article document type — both resolved during manuscript
preparation. The published PRISMA flow (483 screened, 256 in scope, 100-article core) is
the authoritative count; see the root `README.md` and `docs/Methods_PRISMA_Log.docx`.

To rebuild these (and the full corpus) from your own database access, see the root
`README.md` → *Reproducing the corpus*.
