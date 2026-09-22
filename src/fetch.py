import time, requests, pandas as pd, pickle, re, io
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
def get(sym):
    for _ in range(3):
        try:
            r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=3y&interval=1d",headers=UA,timeout=20)
            j=r.json()["chart"]["result"][0]
            q=j["indicators"]["quote"][0]
            df=pd.DataFrame({"close":q["close"],"volume":q["volume"]},index=pd.to_datetime(j["timestamp"],unit="s",utc=True).tz_convert(j["meta"]["exchangeTimezoneName"]).tz_localize(None).normalize())
            adj=j["indicators"].get("adjclose")
            if adj: df["close"]=adj[0]["adjclose"]
            df=df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
            return sym,df
        except Exception as e:
            err=e; time.sleep(3*(_+1))
    return sym,None
COM="GC=F SI=F PL=F PA=F HG=F BZ=F NG=F RB=F HO=F ZC=F ZS=F ZW=F ZL=F ZR=F ZO=F KC=F CC=F SB=F CT=F LE=F HE=F".split()
BOND="^TNX ^TYX ^IRX IGLT.L EXHC.DE 1482.T XGB.TO CBON TLT IEF".split()
PROXY="GLD SLV PPLT PALL".split()
B30="AEFES AKBNK ASELS ASTOR BIMAS DSTKF EKGYO ENKAI EREGL FROTO GARAN GUBRF ISCTR KCHOL KRDMD MGROS PETKM PGSUS SAHOL SASA SISE TAVHL TCELL THYAO TOASO TRALT TTKOM TUPRS VAKBN YKBNK".split()
BROAD=B30+"""AGHOL AKSA AKSEN ALARK ALFAS ALTNY ANSGR ARCLK BERA BINHO BRSAN BRYAT BSOKE BTCIM CANTE CCOLA CIMSA CLEBI CWENE DOAS DOHOL ECILC EFORC EGEEN ENERY ENJSA EUPWR EUREN GENIL GESAN GLRMK GRSEL GRTHO GSRAY HALKB HEKTS IEYHO ISMEN IZENR KARSN KCAER KONTR KONYA KOZAA KTLEV KUYAS LMKDC MAVI MIATK MPARK OBAMS ODINE OTKAR OYAKC PASEU PATEK PSGYO QUAGR RALYH REEDR RYGYO SKBNK SMRTG SOKM TABGD TKFEN TMSN TSKB TTRAK TUKAS TUREX TURSG ULKER VAKKO VESBE VESTL YEOTK ZOREN ESEN AKFYE AKCNS ALBRK ANHYT ASUZU AYDEM BAGFS BIOEN BJKAS BOBET BUCIM CEMTS DEVA DOCO ECZYT ENSRI ERBOS FENER GEDZA GOKNR GOZDE HLGYO INDES ISGYO ISDMR JANTS KAREL KARTN KLSER KMPUR KORDS KZBGY LOGO MAGEN MOBTL NTHOL OZKGY PAPIL PENTA PETUN PNLSN QUAGR SARKY SELEC SNGYO TATEN TBORG TRGYO TKNSA TSPOR ULUUN VERUS YYLGD ZRGYO AHGAZ AKFGY BASGZ BIENY CVKMD DAPGM DMRGD EKSUN EBEBK FORTE GARFA HTTBT INVES IPEKE ISGSY KBORU KLKIM KRVGD LIDER MARBL MEGMT PGSUS REEDR SDTTR TARKM TERA TUCLK YIGIT""".split()
BROAD=list(dict.fromkeys(BROAD))
import os
try:
    ndx=[r["symbol"].replace(".","-").replace("/","-") for r in requests.get("https://api.nasdaq.com/api/quote/list-type/nasdaq100",headers=UA).json()["data"]["data"]["rows"]]
    assert len(ndx)>=90
    open("state/ndx.txt","w").write("\n".join(ndx))
except Exception as e:
    print("Nasdaq listesi alınamadı, state/ndx.txt kullanılıyor:",e)
    ndx=open("state/ndx.txt").read().split()
print("NDX",len(ndx))
syms=COM+BOND+PROXY+ndx+[s+".IS" for s in BROAD]
with ThreadPoolExecutor(6) as ex: data=dict(ex.map(get,syms))
pickle.dump({"data":data,"COM":COM,"BOND":BOND,"B30":B30,"BROAD":BROAD,"NDX":ndx},open("raw.pkl","wb"))
print("fail",[k for k,v in data.items() if v is None]); print("n",sum(v is not None for v in data.values()))
fails=[k for k,v in data.items() if v is None]
if len(fails)>0.10*len(syms): raise SystemExit(f"Çok fazla sembol başarısız ({len(fails)}/{len(syms)}); rapor üretilmedi.")
