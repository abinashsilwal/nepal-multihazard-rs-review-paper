#!/usr/bin/env python3
"""
classify_screen.py  -  stage-one screening pass, rule-based and reproducible.

For each primary article it derives, from the title, abstract and keywords,
a provisional hazard/sensor/method/capability/maturity tagging, plus a
relevance score (0-100) and a provisional decision (Include / Maybe / Exclude)
with a confidence band and short reason.

The corpus is already pre-filtered (every record contains Nepal + a hazard + an
RS term), so scoring rewards centrality - terms appearing in the title or
keywords, Nepal place names, a concrete RS method - and penalises peripheral
mentions (global/regional scope, Nepal absent from the title, no real method).
This is only a first pass: borderline records (Maybe, or Low confidence) are
the set that then gets read by eye and adjudicated in finalize_screening.py.

Output: screening_work.csv (all columns, for review).
"""
import os, re, pandas as pd
WF=os.path.dirname(os.path.abspath(__file__))
a=pd.read_csv(os.path.join(WF,"master_articles.csv"))

def txt(r,*cols):
    return " ".join(str(r[c]) for c in cols if c in r and pd.notna(r[c])).lower()

NEPAL_PLACES=["kathmandu","gorkha","langtang","everest","sagarmatha","khumbu","imja",
 "tsho rolpa","koshi","kosi","gandaki","karnali","pokhara","annapurna","manaslu",
 "dhaulagiri","mustang","rasuwa","sindhupalchok","melamchi","seti","bagmati","rolwaling",
 "dudh koshi","tama koshi","barun","kanchenjunga","mahabharat","chure","churia","siwalik",
 "terai","mahakali","trishuli","budhi gandaki","marsyangdi","nepalese","nepali"]

HAZ={
 "Flood":["flood","inundation","fluvial","riverine","flash flood","overflow","waterlogg"],
 "Landslide":["landslide","slope failure","debris flow","rockfall","rock fall","mass movement",
              "slope instability","mass wasting","slope stability","coseismic landslide","earth flow"],
 "GLOF":["glof","glacial lake","glacier","glacial lake outburst","moraine","supraglacial",
         "proglacial","ice-dammed","ice dammed","cryosphere","glacial retreat","glacial hazard"],
 "Drought":["drought","vegetation stress","water stress","dry spell","evapotranspiration",
            "meteorological drought","agricultural drought","spei","spi index"],
}
SENS={
 "SAR/InSAR":["insar","\bsar\b","sentinel-1","sentinel 1","interferometr","palsar","alos",
              "dinsar","ps-insar","psinsar","radar","coherence","backscatter"],
 "Optical":["landsat","sentinel-2","sentinel 2","modis","optical","planetscope","\bspot\b",
            "aster","worldview","rapideye","multispectral","google earth","planet imagery"],
 "DEM":["\bdem\b","srtm","digital elevation","aster gdem","alos world 3d","\bdsm\b","\bdtm\b",
        "topographic","terrain model"],
 "Thermal/NDVI":["ndvi","thermal","land surface temperature","\blst\b","\bevi\b","vegetation index",
                 "ndwi","ndsi"],
 "UAV":["uav","drone","unmanned aerial","structure from motion","\bsfm\b","photogrammetr"],
}
METH={
 "Susceptibility mapping":["susceptibility","frequency ratio","weights of evidence","analytic hierarchy",
                           "\bahp\b","information value","hazard zonation","hazard mapping"],
 "Change detection":["change detection","multi-temporal","multitemporal","time series","time-series","temporal change"],
 "Deformation/InSAR":["deformation","displacement","subsidence","surface velocity","ground motion","creep"],
 "ML/DL":["machine learning","deep learning","random forest","neural network","support vector",
          "\bsvm\b","\bcnn\b","xgboost","gradient boosting","ensemble model","convolutional"],
 "Hydrologic/hydraulic modelling":["hydrolog","hydraulic","hec-ras","hec ras","hydrodynamic",
          "rainfall-runoff","inundation model","flood model","dam break","dam-break","glof model"],
 "Inventory/mapping":["inventory","delineation","detection","mapping","classification","extraction"],
}
EWS=["early warning","\bews\b","real-time","real time","operational","monitoring system",
     "decision support","forecast system","warning system"]
FORECAST=["forecast","prediction","predict","simulation","scenario","projection","modelling","modeling"]
MONITOR=["monitoring","time series","time-series","deformation","displacement","change detection"]
PILOT=["prototype","pilot","demonstrat","proof of concept","testbed","field test"]
SCOPE_NEG=["global","worldwide","pan-asia","south asia","whole hindu kush","entire hindu kush",
           "across asia","high mountain asia","third pole"]

def hits(t,terms):
    out=[]
    for k in terms:
        pat=k if k.startswith("\\b") or "\\b" in k else re.escape(k)
        if re.search(pat,t): out.append(k)
    return out

def cat_hits(t,d):
    return [c for c,terms in d.items() if hits(t,terms)]

rows=[]
for _,r in a.iterrows():
    title=str(r.get("Title","")).lower()
    kw=txt(r,"Author Keywords","Index Keywords")
    full=txt(r,"Title","Abstract","Author Keywords","Index Keywords")
    tk=title+" "+kw
    has_abs=pd.notna(r.get("Abstract")) and len(str(r.get("Abstract")).strip())>20

    hz=cat_hits(full,HAZ); sn=cat_hits(full,SENS); mt=cat_hits(full,METH)
    # hazard tag
    if len(hz)>=2: hztag="Multi-hazard"
    elif len(hz)==1: hztag=hz[0]
    else: hztag=""
    sntag="Multi-source" if len(sn)>=3 else "; ".join(sn)
    mttag="; ".join([m for m in mt if m!="Inventory/mapping"][:3]) or ("Inventory/mapping" if mt else "")
    # capability (priority: EWS > monitoring/deformation > forecasting > inventory)
    if hits(full,EWS): cap="Early warning & operational"
    elif "Deformation/InSAR" in mt or "Change detection" in mt or hits(full,MONITOR): cap="Monitoring & deformation"
    elif hits(full,FORECAST) or "Hydrologic/hydraulic modelling" in mt: cap="Forecasting & modelling"
    elif "Susceptibility mapping" in mt or "Inventory/mapping" in mt: cap="Inventory & susceptibility"
    else: cap=""
    # maturity
    if hits(full,EWS): mat="Operational"
    elif hits(full,PILOT): mat="Pilot"
    else: mat="Research-only"

    # relevance signals
    nepal_place=bool(hits(full,NEPAL_PLACES)) or "nepal" in title
    nepal_in_title="nepal" in title or bool(hits(title,NEPAL_PLACES))
    rs_central=bool(hits(tk,sum(SENS.values(),[]))) or "remote sensing" in tk or "satellite" in tk or "gis" in tk
    haz_central=bool(cat_hits(tk,HAZ))
    method_present=bool(mt)
    scope_neg=bool(hits(full,SCOPE_NEG)) and not nepal_in_title

    score=0
    score+=25 if nepal_in_title else (12 if nepal_place else 0)
    score+=25 if haz_central else (10 if hz else 0)
    score+=25 if rs_central else (10 if sn else 0)
    score+=15 if method_present else 0
    score+=10 if (sn and hz) else 0
    if scope_neg: score-=20
    if not has_abs: score-=10
    score=max(0,min(100,score))

    # decision
    reasons=[]
    if not hz: reasons.append("no clear hazard")
    if not sn and not rs_central: reasons.append("no concrete RS method")
    if not nepal_place: reasons.append("Nepal not as study area")
    if scope_neg: reasons.append("global/regional scope")
    if not has_abs: reasons.append("no abstract")

    if score>=70 and hz and (sn or rs_central) and nepal_place:
        dec,conf="Include","High"
    elif score>=55:
        dec,conf=("Include","Medium")
    elif score>=40:
        dec,conf=("Maybe","Low")
    else:
        dec,conf=("Maybe","Low") if (hz and (sn or rs_central)) else ("Exclude","Low")

    rows.append({"UID":r["UID"],"Year":r.get("Year"),"Title":r.get("Title"),
        "databases_all":r.get("databases_all"),"streams_all":r.get("streams_all"),
        "n_streams_hit":r.get("n_streams_hit"),
        "relevance_score":score,"screen_auto":dec,"auto_confidence":conf,
        "auto_reason":"; ".join(reasons),
        "tag_hazard":hztag,"tag_sensor_platform":sntag,"tag_method":mttag,
        "tag_capability":cap,"tag_maturity":mat,
        "has_abstract":has_abs})
out=pd.DataFrame(rows)
out.to_csv(os.path.join(WF,"screening_work.csv"),index=False)
print("decisions:",out["screen_auto"].value_counts().to_dict())
print("confidence:",out["auto_confidence"].value_counts().to_dict())
print("hazard tags:",out["tag_hazard"].value_counts().to_dict())
print("capability:",out["tag_capability"].value_counts(dropna=False).to_dict())
print("maturity:",out["tag_maturity"].value_counts().to_dict())
print("need eye-review (Maybe or Low conf or Exclude):",
      ((out["screen_auto"]!="Include")|(out["auto_confidence"]=="Low")).sum())
