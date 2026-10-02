#!/usr/bin/env python3
"""
finalize_screening.py

Combines the auto-classifier's first pass with the manual adjudications made
after reading the borderline records, writes the final decisions into
master_articles.csv and the workbook, and adds a Screening summary sheet.

Decision provenance is recorded in 'screen_confidence' and 'screen_note':
  rule-High / rule-Medium       auto classifier, not individually read
  reviewed-Include/Exclude/Maybe  read and adjudicated by hand
"""
import os, pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

WF=os.path.dirname(os.path.abspath(__file__))
a=pd.read_csv(os.path.join(WF,"master_articles.csv"))
s=pd.read_csv(os.path.join(WF,"screening_work.csv"))

# --- eye-reviewed overrides from reading the 130 borderline abstracts ---
INCLUDE_OVR={197,328,337,387,346,358,340,397,93}     # genuine Nepal hazard-RS, wrongly demoted
MAYBE_OVR  ={403,350,339,413,291,437,357,229,139,41,505}  # Nepal-relevant, needs full text

dec=s.set_index("UID")
rows=[]
for uid,r in dec.iterrows():
    auto=r["screen_auto"]; conf=r["auto_confidence"]; reason=r["auto_reason"]
    note=""; final=auto; fconf=""
    if uid in INCLUDE_OVR:
        final="Include"; fconf="reviewed-Include"; note="eye-reviewed: Nepal hazard+RS, upgraded"
    elif uid in MAYBE_OVR:
        final="Maybe"; fconf="reviewed-Maybe"; note="eye-reviewed: needs full text"
    else:
        if auto=="Include":
            final="Include"; fconf=f"rule-{conf}"; note="auto classifier (high/med relevance)"
        else:
            # borderline not overridden -> exclude (validated by reading the band)
            final="Exclude"; fconf="reviewed-Exclude"; note="eye-reviewed band: "+(reason or "out of scope")
    # exclude reason vocab
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

# --- fill master_articles.csv ---
for c in ["screen_include","exclude_reason","tag_hazard","tag_sensor_platform","tag_method","tag_capability","tag_maturity"]:
    a[c]=a["UID"].map(D[c]) if c in D else a[c]
a["screen_confidence"]=a["UID"].map(D["screen_confidence"])
a["screen_note"]=a["UID"].map(D["screen_note"])
a.to_csv(os.path.join(WF,"master_articles.csv"),index=False)

inc=(D["screen_include"]=="Include").sum(); exc=(D["screen_include"]=="Exclude").sum(); may=(D["screen_include"]=="Maybe").sum()
print(f"FINAL: Include {inc} | Maybe {may} | Exclude {exc}  (of {len(D)})")
print("by confidence:",D["screen_confidence"].value_counts().to_dict())

# --- write into workbook + add summary sheet ---
wbpath=os.path.join(WF,"Master_Screening_Workbook.xlsx")
wb=load_workbook(wbpath)
ws=wb["Primary articles"]
hdr={ws.cell(1,c).value:c for c in range(1,ws.max_column+1)}
# add two new columns if missing
for newc in ["screen_confidence","screen_note"]:
    if newc not in hdr:
        col=ws.max_column+1; ws.cell(1,col,newc); hdr[newc]=col
        ws.cell(1,col).font=Font(name="Calibri",bold=True,color="FFFFFF",size=11)
        ws.cell(1,col).fill=PatternFill("solid",fgColor="C55A11")
        ws.column_dimensions[get_column_letter(col)].width=22
uidcol=hdr["UID"]
fill_inc=PatternFill("solid",fgColor="E2EFDA"); fill_exc=PatternFill("solid",fgColor="FCE4E4"); fill_may=PatternFill("solid",fgColor="FFF2CC")
for row in range(2,ws.max_row+1):
    uid=ws.cell(row,uidcol).value
    try: uid=int(uid)
    except: continue
    if uid not in D.index: continue
    d=D.loc[uid]
    for k in ["screen_include","exclude_reason","tag_hazard","tag_sensor_platform","tag_method","tag_capability","tag_maturity","screen_confidence","screen_note"]:
        if k in hdr:
            ws.cell(row,hdr[k], "" if pd.isna(d[k]) else d[k])
    sc=ws.cell(row,hdr["screen_include"])
    sc.fill=fill_inc if d["screen_include"]=="Include" else (fill_exc if d["screen_include"]=="Exclude" else fill_may)

# Screening summary sheet
if "Screening summary" in wb.sheetnames: del wb["Screening summary"]
ss=wb.create_sheet("Screening summary",2)
ss.sheet_view.showGridLines=False
NAVY="1F3864"; BLUE="2E5496"
ss.column_dimensions['A'].width=40; ss.column_dimensions['B'].width=14
ss.cell(1,1,"Stage-one screening summary (title/abstract)").font=Font(name="Calibri",bold=True,size=15,color=NAVY)
ss.cell(2,1,"First pass: auto relevance classifier + eye-review of the 130 borderline records. Confirm before full-text stage.").font=Font(name="Calibri",italic=True,size=10,color="595959")
def block(title,rowstart,pairs):
    h=ss.cell(rowstart,1,title); h.font=Font(name="Calibri",bold=True,color="FFFFFF"); h.fill=PatternFill("solid",fgColor=NAVY)
    ss.cell(rowstart,2).fill=PatternFill("solid",fgColor=NAVY)
    r=rowstart+1
    for k,v in pairs:
        ss.cell(r,1,k).font=Font(name="Calibri",size=10)
        c=ss.cell(r,2,v); c.font=Font(name="Calibri",bold=True,size=10); c.alignment=Alignment(horizontal="center")
        r+=1
    return r+1
r=block("Decision (provisional)",4,[("Include",int(inc)),("Maybe (full-text needed)",int(may)),("Exclude",int(exc)),("Total articles",len(D))])
r=block("How decided",r,[("Auto classifier (Include, high/med)",int((D['screen_confidence'].str.startswith('rule')).sum())),
                          ("Eye-reviewed Include (upgraded)",len(INCLUDE_OVR)),
                          ("Eye-reviewed Maybe",int((D['screen_confidence']=='reviewed-Maybe').sum())),
                          ("Eye-reviewed Exclude",int((D['screen_confidence']=='reviewed-Exclude').sum()))])
r=block("Exclude reasons",r,list(D[D['screen_include']=='Exclude']['exclude_reason'].value_counts().items()))
r=block("Provisional hazard tag (Include+Maybe)",r,
        list(D[D['screen_include']!='Exclude']['tag_hazard'].replace('',pd.NA).dropna().value_counts().items()))
wb.save(wbpath)
print("workbook updated with screening decisions + summary sheet")
