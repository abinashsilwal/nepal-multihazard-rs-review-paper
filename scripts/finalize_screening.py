#!/usr/bin/env python3
"""
Combine the keyword score from classify_screen.py with the decisions made by reading
the borderline records, and write screening_decisions.csv and master_articles.csv.

screen_confidence shows where each decision came from:
  rule-High, rule-Medium            automatic score, record not read individually
  reviewed-Include/Exclude/Maybe    read and decided by hand
"""
import os, pandas as pd

WF=os.path.dirname(os.path.abspath(__file__))
a=pd.read_csv(os.path.join(WF,"master_articles.csv"))
s=pd.read_csv(os.path.join(WF,"screening_work.csv"))

# manual decisions after reading the 130 borderline abstracts
INCLUDE_OVR={197,328,337,387,346,358,340,397,93}     # Nepal hazard + remote sensing, scored too low
MAYBE_OVR  ={403,350,339,413,291,437,357,229,139,41,505}  # relevant to Nepal, need the full text

dec=s.set_index("UID")
rows=[]
for uid,r in dec.iterrows():
    auto=r["screen_auto"]; conf=r["auto_confidence"]; reason=r["auto_reason"]
    note=""; final=auto; fconf=""
    if uid in INCLUDE_OVR:
        final="Include"; fconf="reviewed-Include"; note="reviewed by hand: upgraded to Include"
    elif uid in MAYBE_OVR:
        final="Maybe"; fconf="reviewed-Maybe"; note="reviewed by hand: needs full text"
    else:
        if auto=="Include":
            final="Include"; fconf=f"rule-{conf}"; note="automatic score"
        else:
            # borderline and not overridden: excluded after reading
            final="Exclude"; fconf="reviewed-Exclude"; note="reviewed by hand: "+(reason or "out of scope")
    # exclusion reason
    er=""
    if final=="Exclude":
        rl=(reason or "")
        if "Nepal not as study area" in rl or "global/regional scope" in rl: er="Not Nepal"
        elif "no clear hazard" in rl: er="No hazard focus"
        elif "no concrete RS method" in rl: er="Not RS/geospatial"
        else: er="Off-topic"
    rows.append({"UID":uid,"screen_include":final,"screen_confidence":fconf,
        "exclude_reason":er,"screen_note":note,
        "tag_hazard":r["tag_hazard"],"tag_sensor_platform":r["tag_sensor_platform"],
        "tag_method":r["tag_method"],"tag_capability":r["tag_capability"],
        "tag_maturity":r["tag_maturity"]})
D=pd.DataFrame(rows).set_index("UID")
D.to_csv(os.path.join(WF,"screening_decisions.csv"))

# add the decisions to master_articles.csv
for c in ["screen_include","exclude_reason","tag_hazard","tag_sensor_platform","tag_method","tag_capability","tag_maturity"]:
    a[c]=a["UID"].map(D[c]) if c in D else a[c]
a["screen_confidence"]=a["UID"].map(D["screen_confidence"])
a["screen_note"]=a["UID"].map(D["screen_note"])
a.to_csv(os.path.join(WF,"master_articles.csv"),index=False)

inc=(D["screen_include"]=="Include").sum(); exc=(D["screen_include"]=="Exclude").sum(); may=(D["screen_include"]=="Maybe").sum()
print(f"FINAL: Include {inc} | Maybe {may} | Exclude {exc}  (of {len(D)})")
print("by confidence:",D["screen_confidence"].value_counts().to_dict())
