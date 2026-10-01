import pickle, numpy as np, pandas as pd, datetime as dt
from statistics import NormalDist
ND=NormalDist()
R=pickle.load(open("raw.pkl","rb")); D=R["data"]
TODAY=pd.Timestamp(dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date())
MINBARS=505; K={"1a":21,"3a":63,"6a":126,"12a":252}; W={"1a":.4,"3a":.3,"6a":.2,"12a":.1}
BASE=504; STALE_DAYS=7; VOL_BAND=0.50
LOCK_MINPCT=0.04; LOCK_WIN=10; LOCK_MINDAYS=3; VOL_DRAIN=0.25
PROXY={"GC=F":"GLD","SI=F":"SLV","PL=F":"PPLT","PA=F":"PALL"}
NOVOL={"^TNX":8.5,"^TYX":17.0,"^IRX":0.25}   # getiri serileri: fiyat-eşdeğer getiri için süre (duration)
NAMES={"GC=F":"Altın","SI=F":"Gümüş","PL=F":"Platin","PA=F":"Paladyum","HG=F":"Bakır","BZ=F":"Brent","NG=F":"Doğalgaz","RB=F":"Benzin RBOB","HO=F":"Isınma yağı","ZC=F":"Mısır","ZS=F":"Soya","ZW=F":"Buğday","ZL=F":"Soya yağı","ZR=F":"Pirinç","ZO=F":"Yulaf","KC=F":"Kahve","CC=F":"Kakao","SB=F":"Şeker","CT=F":"Pamuk","LE=F":"Canlı sığır","HE=F":"Domuz",
"^TNX":"ABD 10Y getiri","^TYX":"ABD 30Y getiri","^IRX":"ABD 3A bono","IGLT.L":"İngiltere Gilt ETF","EXHC.DE":"Almanya Bund ETF","1482.T":"Japonya JGB ETF (hedge)","XGB.TO":"Kanada devlet ETF","CBON":"Çin devlet ETF","TLT":"ABD 20Y+ ETF","IEF":"ABD 7-10Y ETF"}
dropped=[]; log={}
clean={}
for s,df in D.items():
    if df is None: dropped.append((s,"veri gelmedi")); continue
    df=df[df.index<TODAY]
    clean[s]=df
DATE=max(v.index[-1] for v in clean.values())
def usable(s):
    df=clean.get(s)
    if df is None: return False
    if len(df)<MINBARS: dropped.append((s,f"{len(df)} bar < {MINBARS}")); return False
    if (DATE-df.index[-1]).days>STALE_DAYS: dropped.append((s,f"son bar {df.index[-1].date()}")); return False
    return True
def qtest(v):
    v=v.iloc[-120:]; nn=v.notna().sum(); cov=nn/len(v); med=v.median()
    if nn<60 or cov<.6: return False,f"kapsama {cov:.0%}"
    if not med>0: return False,"medyan hacim 0"
    p90=v.quantile(.9)/med; low=(v<.2*med).mean()
    if p90>5: return False,f"p90/medyan {p90:.1f}"
    if low>.35: return False,f"düşük gün payı {low:.0%}"
    return True,f"p90/med {p90:.1f}, düşük %{low*100:.0f}"
def vdw(x):
    """van der Waerden sıra skoru: Φ⁻¹((sıra−3/8)/(n+1/4)). Tasarım gereği normal, winsorize gerekmez."""
    x=x.astype(float); m=x.notna(); out=x*np.nan
    n=int(m.sum())
    if n<3: return out
    r=x[m].rank()
    out[m]=[ND.inv_cdf((v-.375)/(n+.25)) for v in r]
    return out
def mult(z):
    """Hacim çarpanı m(z)=(1−B)+2B·Φ(z), B=0,50 → [0,506;1,494], E[m]=1,000, daima pozitif."""
    return pd.Series([(1-VOL_BAND)+2*VOL_BAND*ND.cdf(v) for v in z.fillna(0)],index=z.index)
def gate(df,v):
    """Likidite kapısı. %4 eşiği zorunlu: PL=F/PA=F'de Yahoo gün içi aralık yerine uzlaşma fiyatı yayınlar, OHLC düz gelir ama gerçekte likidite yoktur."""
    w=df.iloc[-LOCK_WIN:]
    chg=(w.close-w.close.shift(1)).abs()/w.close.shift(1)
    days=int(((w.open==w.high)&(w.high==w.low)&(w.low==w.close)&(chg>=LOCK_MINPCT)).sum())
    b=v.iloc[-60:].mean(); a=v.iloc[-5:].mean()
    vr=a/b if b>0 else np.nan
    drained=bool(pd.notna(vr) and vr<VOL_DRAIN)
    why=[]
    if days>=LOCK_MINDAYS: why.append(f"{days} kilitli gün / son {LOCK_WIN}")
    if drained: why.append(f"5g/60g hacim {vr:.2f} < {VOL_DRAIN}")
    return (days>=LOCK_MINDAYS) or drained, days, vr, " · ".join(why)
def build(name,syms,label=lambda s:s):
    rows=[]
    for s in syms:
        if s not in clean or len(clean[s])<LOCK_WIN+1:
            if s in clean: dropped.append((s,f"{len(clean[s])} bar < {LOCK_WIN+1}"))
            else: dropped.append((s,"veri gelmedi"))
            continue
        df=clean[s].copy(); c=df.close; v=df.volume.astype(float).where(df.volume>0)
        note=""
        if s in NOVOL:
            v=None; note="Hacimsiz (getiri serisi)"
        elif name=="Emtia":
            ok,msg=qtest(v)
            if not ok:
                if s in PROXY and PROXY[s] in clean:
                    pv=clean[PROXY[s]].volume.astype(float); pv.index=pv.index.normalize()
                    v=pv.where(pv>0).reindex(df.index.normalize()); v.index=df.index
                    note=f"Vekil hacim: {PROXY[s]} ({msg})"
                else: v=None; note=f"Hacimsiz: kalite testi geçemedi, vekil yok ({msg})"
            else: note=""
            log[s]=(ok,msg,note)
        # Kapı önce değerlendirilir: kilitli enstrüman 505 bar şartına takılsa bile ayrı raporlanmalı (kapı sayfası yalnızca 1a/3a ve 60g hacim ister).
        r={"Enstrüman":label(s),"Sembol":s,"Evren":name,"Son":c.iloc[-1],"Not":note}
        r["Kilit"],r["KilitGün"],r["VolDrain"],r["GateNeden"]=False,0,np.nan,""
        if v is not None and {"open","high","low"}<=set(df.columns) and len(df)>=LOCK_WIN+1:
            hit,days,vr,why=gate(df,v)
            r["Kilit"],r["KilitGün"],r["VolDrain"],r["GateNeden"]=hit,days,vr,why
        if not r["Kilit"] and not usable(s): continue
        for k,n in K.items():
            if s in NOVOL:
                r[f"ret_{k}"]=-NOVOL[s]*(c.iloc[-1]-c.iloc[-1-n])/100
            else: r[f"ret_{k}"]=c.iloc[-1]/c.iloc[-1-n]-1 if len(df)>n else np.nan
            if v is None: r[f"vol_{k}"]=np.nan; r[f"vr_{k}"]=np.nan
            else:
                a=v.iloc[-n:].mean(); b=v.iloc[-BASE:].mean()
                r[f"vol_{k}"]=a; r[f"vr_{k}"]=a/b if b>0 else np.nan
        rows.append(r)
    t=pd.DataFrame(rows)
    for k in K:
        t[f"zr_{k}"]=vdw(t[f"ret_{k}"])
        lv=np.log(t[f"vr_{k}"].where(t[f"vr_{k}"]>0))
        t[f"zv_{k}"]=vdw(lv)
        t[f"m_{k}"]=mult(t[f"zv_{k}"])
        t[f"mom_{k}"]=t[f"zr_{k}"]*t[f"m_{k}"]
    for o,p in [("ZRET","zr"),("ZVOL","zv"),("MOM","mom")]:
        t[o]=sum(W[k]*t[f"{p}_{k}"] for k in K)
    G=t.Kilit
    t.loc[G,["ZVOL","MOM"]+[f"{p}_{k}" for p in ("zv","m","mom") for k in K]]=np.nan
    def q(r):
        if r.Kilit: return "Likidite kilidi"
        if pd.isna(r.ZVOL): return "Hacimsiz"
        return {(1,1):"Q1 · Teyitli yükseliş",(1,0):"Q2 · Teyitsiz yükseliş",(0,1):"Q3 · Teyitli düşüş",(0,0):"Q4 · İlgisiz düşüş"}[(int(r.ZRET>=0),int(r.ZVOL>=0))]
    t["Kadran"]=t.apply(q,axis=1)
    t["Olay"]=(t.ret_1a>=.30)&(t.ret_12a<0)
    return t.sort_values("MOM",ascending=False,na_position="last").reset_index(drop=True)
nm=lambda s:NAMES.get(s,s.replace(".IS",""))
U={}
U["Emtia"]=build("Emtia",R["COM"],nm)
U["Tahvil / faiz"]=build("Tahvil / faiz",R["BOND"],nm)
U["Nasdaq 100"]=build("Nasdaq 100",R["NDX"])
# BIST 100: likidite
liq={}
for s in [x+".IS" for x in R["BROAD"]]:
    df=clean.get(s)
    if df is None or len(df)<MINBARS or (DATE-df.index[-1]).days>STALE_DAYS: continue
    liq[s]=(df.close*df.volume).iloc[-60:].mean()
b100=sorted(liq,key=liq.get,reverse=True)[:100]
U["BIST 100"]=build("BIST 100",b100,nm)
U["BIST 30"]=build("BIST 30",[x+".IS" for x in R["B30"]],nm)
dropped=list(dict.fromkeys(dropped))
import os
if (TODAY-DATE).days>4: raise SystemExit(f"Veri bayat: son bar {DATE.date()}")
A0=pd.concat(U.values())
prev=None
if os.path.exists("state/last.csv"):
    P=pd.read_csv("state/last.csv"); P["key"]=P.Evren+"|"+P.Enstrüman
    C=A0.assign(key=A0.Evren+"|"+A0.Enstrüman)
    m=C.merge(P[["key","Kadran","Sıra","Tarih"]],on="key",how="inner",suffixes=("","_p"))
    ch=m[m.Kadran!=m.Kadran_p]
    C["Sıra"]=C.groupby("Evren").MOM.rank(ascending=False,method="min")
    out5=P[(P.Sıra<=5)].merge(C[["key","Sıra"]],on="key",how="left",suffixes=("_p",""))
    out5=out5[~(out5.Sıra<=5)]
    q1=lambda d:d.Kadran.str.startswith("Q1").mean()
    prev={"tarih":str(P.Tarih.iloc[0]),"changes":ch[["Evren","Enstrüman","Kadran_p","Kadran"]].values.tolist(),
          "out5":out5[["Evren","Enstrüman"]].values.tolist(),"q1":(q1(P),q1(A0))}
    newgate=C[C.Kilit & ~C.key.isin(P.key[P.Kadran=="Likidite kilidi"])][["Evren","Enstrüman"]].values.tolist()
else: newgate=[]
os.makedirs("state",exist_ok=True)
pickle.dump({"U":U,"DATE":DATE,"dropped":dropped,"log":log,"nbroad":len(liq),"prev":prev,"newgate":newgate},open("res.pkl","wb"))
S=A0.copy(); S["Sıra"]=S.groupby("Evren").MOM.rank(ascending=False,method="min"); S["Tarih"]=str(DATE.date())
S[["Tarih","Evren","Enstrüman","Kadran","MOM","Sıra"]].to_csv("state/last_new.csv",index=False)
print("DATE",DATE.date(),{k:len(t) for k,t in U.items()})
