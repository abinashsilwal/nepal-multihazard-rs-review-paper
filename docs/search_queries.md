# Search queries

Searched on 14 June 2026, publication years 2016-2025.

Scopus: each query inside `TITLE-ABS-KEY( ... )`.
Web of Science Core Collection: the same terms in the Topic (TS) field.

Exports are named by stream and document type, for example `02_Flood_Search_Article`
and `01_Main_MultiHazard_Search_Review` (see `scripts/merge_dedupe.py`).

**1. Main (multi-hazard)**

```
("remote sensing" OR satellite OR "earth observation" OR geospatial OR GIS)
AND (flood* OR landslide* OR "glacial lake outburst flood" OR GLOF OR drought* OR "multi-hazard")
AND Nepal
```

**2. Flood**

```
("remote sensing" OR satellite OR GIS OR "earth observation")
AND (flood* OR inundation)
AND Nepal
```

**3. Landslide**

```
("remote sensing" OR satellite OR GIS OR DEM OR InSAR)
AND (landslide* OR "slope failure")
AND Nepal
```

**4. GLOF**

```
("remote sensing" OR satellite OR GIS OR DEM)
AND ("glacial lake outburst flood" OR GLOF OR glacier*)
AND Nepal
```

**5. Drought**

```
("remote sensing" OR satellite OR GIS OR NDVI)
AND (drought* OR "vegetation stress")
AND Nepal
```
