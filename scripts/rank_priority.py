#!/usr/bin/env python3
"""
rank_priority.py  -  prioritises the in-scope corpus down to the in-depth
synthesis core (~100 articles), with no per-paper subjectivity in the ranking.

Each in-scope article (screen_include in {Include, Maybe}) gets a Priority
Score from 0-100, a weighted sum of six normalised, data-derived criteria
(weights in WEIGHTS below):

  Priority = 25*MultiHazard + 25*Centrality + 15*Operational
           + 15*Recency + 10*CrossDB + 10*Citation

  MultiHazard  hazard searches a paper appears in: 1->0.0, 2->0.6, 3->0.8, >=4->1.0
  Centrality   screening relevance score / 100 (Nepal study area + RS method + hazard)
  Operational  capability tier: Early warning&operational=1.0, Monitoring&deformation=0.6,
               Forecasting&modelling=0.4, Inventory&susceptibility=0.2, blank=0.0
  Recency      (Year - 2016) / (2025 - 2016), clipped to [0,1]
  CrossDB      indexed in both Scopus and WoS = 1, single database = 0
  Citation     percentile rank of citations-per-year = Cited by / (2026 - Year)

Selection is then stratified by hazard (Flood, Landslide, GLOF, Drought,
Multi-hazard) to keep cross-hazard balance: each stratum gets
max(FLOOR, round(TARGET * share)) of its top-scoring papers, or all of them
if it holds fewer than FLOOR, trimmed/extended against the global ranking to
land on TARGET exactly.

Every input here is already a column in master_articles.csv / screening_work.csv,
so re-running this script against the same inputs reproduces the identical
core. WEIGHTS / TARGET / FLOOR can be edited to run sensitivity checks.
"""
import os, numpy as np, pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

WF=os.path.dirname(os.path.abspath(__file__))
WEIGHTS={"MultiHazard":25,"Centrality":25,"Operational":15,"Recency":15,"CrossDB":10,"Citation":10}
TARGET=100
FLOOR=10            # minimum papers per hazard stratum (or all, if fewer)
YEAR_MIN,YEAR_MAX=2016,2025
CUR_YEAR=2026

a=pd.read_csv(os.path.join(WF,"master_articles.csv"))
sw=pd.read_csv(os.path.join(WF,"screening_work.csv"))[["UID","relevance_score"]]
a=a.merge(sw,on="UID",how="left")
scope=a[a["screen_include"].isin(["Include","Maybe"])].copy()

def num(x):
    try: return float(x)
    except: return np.nan

scope["_year"]=scope["Year"].map(num)
scope["_cites"]=scope["Cited by"].map(num).fillna(0)

# --- sub-scores ---
def mh(n):
    n=0 if pd.isna(n) else int(n)
    return {1:0.0,2:0.6,3:0.8}.get(n, 1.0 if n>=4 else 0.0)
scope["s_MultiHazard"]=scope["n_streams_hit"].map(mh)
scope["s_Centrality"]=(scope["relevance_score"].map(num)/100).clip(0,1).fillna(0)
captier={"Early warning & operational":1.0,"Monitoring & deformation":0.6,
         "Forecasting & modelling":0.4,"Inventory & susceptibility":0.2}
scope["s_Operational"]=scope["tag_capability"].map(lambda x: captier.get(str(x).strip(),0.0))
scope["s_Recency"]=((scope["_year"]-YEAR_MIN)/(YEAR_MAX-YEAR_MIN)).clip(0,1).fillna(0)
scope["s_CrossDB"]=(scope["n_databases"].map(num)>=2).astype(float)
cpy=scope["_cites"]/(CUR_YEAR-scope["_year"]).clip(lower=1)
scope["s_Citation"]=cpy.rank(pct=True).fillna(0)

# --- weighted total ---
scope["PriorityScore"]=sum(WEIGHTS[k]*scope[f"s_{k}"] for k in WEIGHTS).round(1)
scope=scope.sort_values("PriorityScore",ascending=False).reset_index(drop=True)
scope["rank_overall"]=np.arange(1,len(scope)+1)

# --- stratified selection ---
HAZARDS=["Flood","Landslide","GLOF","Drought","Multi-hazard"]
scope["_haz"]=scope["tag_hazard"].where(scope["tag_hazard"].isin(HAZARDS), other="")
tagged=scope[scope["_haz"]!=""]
counts={h:int((tagged["_haz"]==h).sum()) for h in HAZARDS}
total=sum(counts.values())
# floor first (min of FLOOR or all available), then distribute the remainder by
# largest-remainder proportional to each stratum's papers above its floor.
floor={h:min(counts[h],FLOOR) for h in HAZARDS}
remaining=TARGET-sum(floor.values())
pool={h:max(0,counts[h]-floor[h]) for h in HAZARDS}
poolsum=sum(pool.values()) or 1
raw={h:remaining*pool[h]/poolsum for h in HAZARDS}
extra={h:int(np.floor(raw[h])) for h in HAZARDS}
# largest remainder to reach exactly 'remaining'
left=remaining-sum(extra.values())
for h in sorted(HAZARDS,key=lambda x:raw[x]-np.floor(raw[x]),reverse=True)[:left]:
    extra[h]+=1
alloc={h:min(counts[h],floor[h]+extra[h]) for h in HAZARDS}
chosen=set()
for h in HAZARDS:
    ids=tagged[tagged["_haz"]==h].sort_values("PriorityScore",ascending=False)["UID"].head(alloc[h])
    chosen.update(ids.tolist())
scope["in_core_100"]=scope["UID"].isin(chosen)

# rank within hazard
scope["rank_in_hazard"]=scope.groupby("_haz")["PriorityScore"].rank(ascending=False,method="first")

out_cols=["rank_overall","UID","Title","Year","_haz","databases_all","n_databases",
          "n_streams_hit","Cited by","PriorityScore","in_core_100",
          "s_MultiHazard","s_Centrality","s_Operational","s_Recency","s_CrossDB","s_Citation",
          "screen_include","tag_capability"]
out=scope[out_cols].rename(columns={"_haz":"hazard"})
out.to_csv(os.path.join(WF,"priority_ranking.csv"),index=False)

print("in-scope ranked:",len(scope))
print("core selected:",int(scope['in_core_100'].sum()))
print("allocation per hazard (selected):")
print(scope[scope['in_core_100']]["_haz"].value_counts().to_dict())
print("core score range: %.1f - %.1f"%(scope[scope['in_core_100']]['PriorityScore'].min(),
                                        scope['PriorityScore'].max()))
print("core year split 2020+: %d / %d"%(int((scope[scope['in_core_100']]['_year']>=2020).sum()),
                                         int(scope['in_core_100'].sum())))

# --- add Priority ranking sheet to workbook ---
wbp=os.path.join(WF,"Master_Screening_Workbook.xlsx")
wb=load_workbook(wbp)
if "Priority ranking" in wb.sheetnames: del wb["Priority ranking"]
ws=wb.create_sheet("Priority ranking",3)
BLUE="2E5496"; GOLD="FFF2CC"
hdrs=list(out.columns)
for j,c in enumerate(hdrs,1):
    x=ws.cell(1,j,c); x.font=Font(name="Calibri",bold=True,color="FFFFFF",size=10)
    x.fill=PatternFill("solid",fgColor=BLUE); x.alignment=Alignment(wrap_text=True,horizontal="center",vertical="center")
for i,(_,r) in enumerate(out.iterrows(),2):
    for j,c in enumerate(hdrs,1):
        v=r[c]
        if pd.isna(v): v=""
        if isinstance(v,(np.bool_,bool)): v=bool(v)
        if isinstance(v,(np.integer,)): v=int(v)
        if isinstance(v,(np.floating,)): v=round(float(v),3)
        cell=ws.cell(i,j,v); cell.font=Font(name="Calibri",size=9)
        if c=="Title": cell.alignment=Alignment(wrap_text=True,vertical="top")
    if bool(r["in_core_100"]):
        for j in range(1,len(hdrs)+1): ws.cell(i,j).fill=PatternFill("solid",fgColor=GOLD)
widths={"rank_overall":7,"UID":7,"Title":50,"Year":7,"hazard":13,"databases_all":14,
        "n_databases":7,"n_streams_hit":7,"Cited by":8,"PriorityScore":11,"in_core_100":10}
for j,c in enumerate(hdrs,1): ws.column_dimensions[get_column_letter(j)].width=widths.get(c,11)
ws.freeze_panes="A2"; ws.auto_filter.ref=f"A1:{get_column_letter(len(hdrs))}{len(out)+1}"
wb.save(wbp)
print("workbook updated: 'Priority ranking' tab (core highlighted gold)")
