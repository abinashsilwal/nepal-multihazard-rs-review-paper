#!/usr/bin/env python3
"""
Rank the in-scope articles and pick the 100-paper core for the detailed synthesis.

Articles with screen_include Include or Maybe get a priority score from 0 to 100:

  25*MultiHazard + 25*Centrality + 15*Operational + 15*Recency + 10*CrossDB + 10*Citation

  MultiHazard  number of hazard searches the paper turned up in: 1 -> 0.0, 2 -> 0.6,
               3 -> 0.8, 4 or more -> 1.0
  Centrality   relevance score from classify_screen.py divided by 100
  Operational  highest capability: early warning and operational 1.0, monitoring and
               deformation 0.6, forecasting and modelling 0.4, inventory and
               susceptibility 0.2, none 0
  Recency      (year - 2016) / (2025 - 2016), limited to 0-1
  CrossDB      1 if indexed in both Scopus and Web of Science, otherwise 0
  Citation     percentile of citations per year (cited by / (2026 - year))

The core is picked by hazard (Flood, Landslide, GLOF, Drought, Multi-hazard) so that no
hazard is left out. Each hazard gets at least FLOOR papers, or all of its papers if it
has fewer. The remaining places up to TARGET are shared out in proportion to the number
of papers each hazard has above its floor, and the top-scoring papers of each hazard are
taken. WEIGHTS, TARGET and FLOOR can be changed to test how sensitive the core is.

Reads master_articles.csv and screening_work.csv, writes priority_ranking.csv.
"""
import os, numpy as np, pandas as pd

WF=os.path.dirname(os.path.abspath(__file__))
WEIGHTS={"MultiHazard":25,"Centrality":25,"Operational":15,"Recency":15,"CrossDB":10,"Citation":10}
TARGET=100
FLOOR=10            # minimum papers per hazard (or all, if fewer)
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

# sub-scores
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

# weighted total
scope["PriorityScore"]=sum(WEIGHTS[k]*scope[f"s_{k}"] for k in WEIGHTS).round(1)
scope=scope.sort_values("PriorityScore",ascending=False).reset_index(drop=True)
scope["rank_overall"]=np.arange(1,len(scope)+1)

# pick the core hazard by hazard
HAZARDS=["Flood","Landslide","GLOF","Drought","Multi-hazard"]
scope["_haz"]=scope["tag_hazard"].where(scope["tag_hazard"].isin(HAZARDS), other="")
tagged=scope[scope["_haz"]!=""]
counts={h:int((tagged["_haz"]==h).sum()) for h in HAZARDS}
# floor first, then share out the rest by largest remainder
floor={h:min(counts[h],FLOOR) for h in HAZARDS}
remaining=TARGET-sum(floor.values())
pool={h:max(0,counts[h]-floor[h]) for h in HAZARDS}
poolsum=sum(pool.values()) or 1
raw={h:remaining*pool[h]/poolsum for h in HAZARDS}
extra={h:int(np.floor(raw[h])) for h in HAZARDS}
left=remaining-sum(extra.values())
for h in sorted(HAZARDS,key=lambda x:raw[x]-np.floor(raw[x]),reverse=True)[:left]:
    extra[h]+=1
alloc={h:min(counts[h],floor[h]+extra[h]) for h in HAZARDS}
chosen=set()
for h in HAZARDS:
    ids=tagged[tagged["_haz"]==h].sort_values("PriorityScore",ascending=False)["UID"].head(alloc[h])
    chosen.update(ids.tolist())
scope["in_core_100"]=scope["UID"].isin(chosen)

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
