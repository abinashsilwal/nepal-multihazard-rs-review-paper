#!/usr/bin/env python3
"""
merge_dedupe.py  (v2 - Scopus + Web of Science)

Pools and de-duplicates the Scopus + Web of Science exports for the review
"Remote sensing and geospatial approaches for multi-hazard monitoring in Nepal".

Each database export is mapped to a common schema (Scopus is read as a native
CSV; the Web of Science "Excel" export is saved with a .csv extension but is
actually an .xls/OLE2 file, so it's read with pandas.read_excel). Records are
tagged with source database, hazard search stream, and document type (WoS
leaves 'Document Type' blank in this export, so type is inferred from the file
name instead: *_Article -> Article, *_Review -> Review).

De-duplication runs across both databases using whichever key is available,
in order: DOI, then title+year, then the native id (Scopus EID / WoS UT). That
lets the same paper found in both databases be merged on a shared DOI or title
even though their native ids differ, and keeps a record of the overlap.

Outputs: master_records.csv, master_articles.csv, reference_nonarticle.csv,
duplicates_removed.csv, audit_log.txt (PRISMA stage counts).

To add another database later, append an entry to DB_SOURCES with its folder,
a file->stream map, and a column-mapping function, then re-run.

Run from this folder; its parent should hold the search-result folders.
"""
import os, re, sys, datetime
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))   # this Review_Workflow folder
PROJECT = os.path.dirname(ROOT)                      # parent (holds the search folders)
OUT_DIR = ROOT

# Common schema columns we keep
KEEP = ["Authors","Title","Year","Source title","Document Type","DOI","Link",
        "Cited by","Abstract","Author Keywords","Index Keywords"]

# ---- file -> (hazard stream, filename doc type) ----
STREAM_MAP = {
 "01_Main_MultiHazard_Search_Article": ("Main","Article"),
 "01_Main_MultiHazard_Search_Review":  ("Main","Review"),
 "02_Flood_Search_Article":            ("Flood","Article"),
 "02_Flood_Search_Review":             ("Flood","Review"),
 "03_Landslide_Search_Article":        ("Landslide","Article"),
 "03_Landslide_Search_Review":         ("Landslide","Review"),
 "04_GLOF_Search_Article":             ("GLOF","Article"),
 "05_Drought_Search_Article":          ("Drought","Article"),
}

def stream_doctype(fname):
    base = os.path.splitext(os.path.basename(fname))[0]
    return STREAM_MAP.get(base, ("Unknown","Article"))

# ---------- column mappers ----------
def map_scopus(df):
    # Scopus already uses our schema names; add native id from EID.
    out = pd.DataFrame()
    for c in KEEP:
        out[c] = df[c] if c in df.columns else ""
    out["_nativeid"] = df["EID"] if "EID" in df.columns else ""
    return out

_STOP={"a","an","and","as","at","but","by","for","from","in","of","on","or","the","to","vs","via","with"}
def smart_title(s):
    """Title-case an ALL-CAPS WoS journal name the way Scopus styles it
    (lowercase interior conjunctions/prepositions)."""
    if not isinstance(s,str) or not s.isupper():
        return s
    words=s.split()
    out=[]
    for i,w in enumerate(words):
        lw=w.lower()
        out.append(lw if (i>0 and lw in _STOP) else lw.capitalize())
    return " ".join(out)

def map_wos(df):
    out = pd.DataFrame()
    out["Authors"]        = df.get("Authors","")
    out["Title"]          = df.get("Article Title","")
    out["Year"]           = df.get("Publication Year","")
    src                   = df.get("Source Title","")
    # WoS source titles are ALL CAPS; normalize to Scopus-style title case
    out["Source title"]   = src.fillna("").map(smart_title)
    out["Document Type"]  = df.get("Document Type","")        # blank in this export
    out["DOI"]            = df.get("DOI","")
    out["Link"]           = df.get("DOI Link","")
    out["Cited by"]       = df.get("Times Cited, All Databases","")
    out["Abstract"]       = df.get("Abstract","")
    out["Author Keywords"]= df.get("Author Keywords","")
    out["Index Keywords"] = df.get("Keywords Plus","")
    out["_nativeid"]      = df.get("UT (Unique WOS ID)","")
    return out

# ---- database sources: (label, folder, reader, mapper) ----
DB_SOURCES = [
 ("Scopus", os.path.join(PROJECT,"Scopus Search (2016-2025)"),
   lambda p: pd.read_csv(p, dtype=str, encoding="utf-8-sig"), map_scopus),
 ("WoS",    os.path.join(PROJECT,"Web of Science Search (2016-2025)"),
   lambda p: pd.read_excel(p, dtype=str), map_wos),
]

LOG=[]
def log(m=""):
    print(m); LOG.append(m)

def norm_doi(x):
    if not isinstance(x,str): return ""
    x=x.strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/","",x).strip()

def norm_title(x):
    if not isinstance(x,str): return ""
    x=re.sub(r"[^a-z0-9 ]+"," ",x.lower())
    return re.sub(r"\s+"," ",x).strip()

def main():
    frames=[]
    for label, folder, reader, mapper in DB_SOURCES:
        log(f"--- {label}  ({folder.split(os.sep)[-1]}) ---")
        if not os.path.isdir(folder):
            log(f"  (folder not found -> skipped)"); continue
        for base,(stream,dtype) in STREAM_MAP.items():
            # find a file whose stem == base (any extension)
            hit=None
            for fn in os.listdir(folder):
                if os.path.splitext(fn)[0]==base:
                    hit=os.path.join(folder,fn); break
            if not hit:
                continue
            try:
                raw=reader(hit)
            except Exception as e:
                log(f"  ERROR reading {os.path.basename(hit)}: {e}"); continue
            m=mapper(raw)
            m["_database"]=label; m["_stream"]=stream; m["_filedoctype"]=dtype
            m["_source_file"]=f"{label}/{os.path.basename(hit)}"
            log(f"  {os.path.basename(hit):42s} {len(m):4d}  [{stream}/{dtype}]")
            frames.append(m)
    if not frames: sys.exit("No input files found.")

    raw=pd.concat(frames,ignore_index=True).reset_index(drop=True)
    n_raw=len(raw)
    log("")
    log(f"TOTAL RECORDS IDENTIFIED: {n_raw}")
    log(f"  by database: {raw['_database'].value_counts().to_dict()}")
    log(f"  by stream:   {raw['_stream'].value_counts().to_dict()}")

    raw["_doi_n"]=raw["DOI"].map(norm_doi)
    raw["_title_n"]=raw["Title"].map(norm_title)
    raw["_year"]=raw["Year"].fillna("").astype(str).str.strip()
    raw["_nid"]=raw["_nativeid"].fillna("").astype(str).str.strip()

    # ---- robust cross-database dedupe (DOI -> Title+Year -> native id) ----
    groups={}            # key string -> gid
    next_gid=0
    gid_of=[]
    removed=[]           # (idx, reason)
    for i,row in raw.iterrows():
        cand=[]
        if row["_doi_n"]:                 cand.append(("DOI", "DOI:"+row["_doi_n"]))
        if row["_title_n"]:               cand.append(("TITLE+YEAR","TIT:"+row["_title_n"]+"|"+row["_year"]))
        if row["_nid"]:                   cand.append(("NATIVE_ID","NID:"+row["_nid"]))
        found=None; reason=None
        for rsn,k in cand:
            if k in groups: found=groups[k]; reason=rsn; break
        if found is None:
            gid=next_gid; next_gid+=1
            for _,k in cand: groups[k]=gid
            gid_of.append(gid)
        else:
            for _,k in cand: groups.setdefault(k,found)
            gid_of.append(found); removed.append((i,reason))
    raw["_gid"]=gid_of
    removed_idx={i for i,_ in removed}
    raw["_kept"]=~raw.index.isin(removed_idx)

    # aggregate provenance per group
    g_streams=raw.groupby("_gid")["_stream"].apply(lambda s:", ".join(sorted(set(s))))
    g_dbs    =raw.groupby("_gid")["_database"].apply(lambda s:", ".join(sorted(set(s))))
    g_nstream=raw.groupby("_gid")["_stream"].apply(lambda s:len(set(s)))
    g_ndb    =raw.groupby("_gid")["_database"].apply(lambda s:len(set(s)))

    uni=raw[raw["_kept"]].copy()
    uni["streams_all"]=uni["_gid"].map(g_streams)
    uni["databases_all"]=uni["_gid"].map(g_dbs)
    uni["n_streams_hit"]=uni["_gid"].map(g_nstream)
    uni["n_databases"]=uni["_gid"].map(g_ndb)

    n_uni=len(uni); n_dup=n_raw-n_uni
    log("")
    log("DE-DUPLICATION (robust, cross-database: DOI -> Title+Year -> native id)")
    rc={}
    for _,r in removed: rc[r]=rc.get(r,0)+1
    log(f"  duplicates removed: {n_dup}")
    for k,v in rc.items(): log(f"     - matched on {k}: {v}")
    log(f"  UNIQUE RECORDS REMAINING: {n_uni}")
    overlap=(uni["n_databases"]>=2).sum()
    log(f"  found in BOTH databases (Scopus & WoS): {overlap}")
    log(f"  Scopus-only: {(uni['databases_all']=='Scopus').sum()}   "
        f"WoS-only: {(uni['databases_all']=='WoS').sum()}")
    log(f"  multi-stream (>=2 hazard searches): {(uni['n_streams_hit']>=2).sum()}")

    # document class: real Document Type if present else filename doc type
    def doc_class(r):
        dt=str(r["Document Type"]).strip()
        return dt if dt and dt.lower()!="nan" else r["_filedoctype"]
    uni["doc_class"]=uni.apply(doc_class,axis=1)

    # screening + tagging columns
    for c in ["screen_include","exclude_reason","tag_hazard","tag_sensor_platform",
              "tag_method","tag_capability","tag_maturity","notes"]:
        uni[c]=""

    uni=uni.rename(columns={"_gid":"UID"})
    front=["UID","Authors","Title","Year","Source title","doc_class","databases_all",
           "n_databases","streams_all","n_streams_hit","DOI","Link","Cited by",
           "screen_include","exclude_reason","tag_hazard","tag_sensor_platform",
           "tag_method","tag_capability","tag_maturity","notes",
           "Abstract","Author Keywords","Index Keywords"]
    front=[c for c in front if c in uni.columns]
    master=uni[front]
    master.to_csv(os.path.join(OUT_DIR,"master_records.csv"),index=False)

    is_art=master["doc_class"].fillna("").str.strip().str.lower().eq("article")
    primary=master[is_art].copy(); reference=master[~is_art].copy()
    primary.to_csv(os.path.join(OUT_DIR,"master_articles.csv"),index=False)
    reference.to_csv(os.path.join(OUT_DIR,"reference_nonarticle.csv"),index=False)
    log("")
    log("DOCUMENT-TYPE SPLIT (synthesis = Articles only)")
    log(f"  PRIMARY synthesis set (Article): {len(primary)}")
    log(f"  REFERENCE set (Review/other): {len(reference)}")
    for dt,c in master["doc_class"].fillna("(blank)").value_counts().items():
        log(f"     - {dt}: {c}")

    dup_df=raw.loc[[i for i,_ in removed],
                   ["Title","Year","DOI","_database","_stream","_source_file","_gid"]].copy()
    dup_df["matched_on"]=[r for _,r in removed]
    dup_df.to_csv(os.path.join(OUT_DIR,"duplicates_removed.csv"),index=False)

    stamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    head=["="*70,"AUDIT LOG  -  merge_dedupe.py (Scopus + Web of Science)",
          f"Run: {stamp}",
          "Review: Remote sensing & geospatial approaches for multi-hazard",
          "        monitoring in Nepal","="*70,""]
    with open(os.path.join(OUT_DIR,"audit_log.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(head+LOG)+"\n")
    log(""); log("OUTPUTS WRITTEN: master_records.csv, master_articles.csv, "
                  "reference_nonarticle.csv, duplicates_removed.csv, audit_log.txt")
    print("audit_log.txt written")

if __name__=="__main__":
    main()
