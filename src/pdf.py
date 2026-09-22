import os, pickle, pandas as pd, numpy as np, io
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("DV","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV",normal="DV",bold="DVB")
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":7})
r=pickle.load(open("res.pkl","rb")); U=r["U"]; DATE=r["DATE"]; DS=DATE.strftime("%d.%m.%Y")
NAVY=colors.HexColor("#12314F"); GOLD=colors.HexColor("#B8862B")
A=pd.concat(U.values()).sort_values("MOMADJ",ascending=False)
K=["1a","3a","6a","12a"]
H1=ParagraphStyle("h1",fontName="DVB",fontSize=13,textColor=NAVY,spaceAfter=3,leading=16)
H2=ParagraphStyle("h2",fontName="DVB",fontSize=9,textColor=NAVY,spaceBefore=5,spaceAfter=2)
B=ParagraphStyle("b",fontName="DV",fontSize=7.4,leading=9.6)
S=ParagraphStyle("s",fontName="DV",fontSize=6.2,leading=7.8,textColor=colors.HexColor("#444444"))
TC=ParagraphStyle("tc",fontName="DV",fontSize=6.3,leading=7.6)
TH=ParagraphStyle("th",fontName="DVB",fontSize=6.3,leading=7.6,textColor=colors.white)
def band(c,d):
    w,h=A4; c.saveState()
    c.setFillColor(NAVY); c.rect(0,h-16*mm,w,16*mm,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont("DVB",11); c.drawString(14*mm,h-10*mm,"Getiri–Hacim Momentum Çalışması")
    c.setFont("DV",7.5); c.drawRightString(w-14*mm,h-10*mm,f"Veri tarihi: {DS}  |  Kaynak: Yahoo Finance")
    c.setStrokeColor(GOLD); c.setLineWidth(1.6); c.line(0,h-16.8*mm,w,h-16.8*mm)
    c.setFont("DV",6.5); c.setFillColor(colors.grey)
    c.drawString(14*mm,8*mm,"Yatırım tavsiyesi değildir."); c.drawRightString(w-14*mm,8*mm,f"Sayfa {d.page}")
    c.restoreState()
def tbl(data,widths,num_from=1,zebra=True,left_cols=(0,)):
    rows=[[Paragraph(str(x),TH) for x in data[0]]]+[[Paragraph(str(x),TC) for x in row] for row in data[1:]]
    t=Table(rows,colWidths=widths,repeatRows=1)
    st=[("BACKGROUND",(0,0),(-1,0),NAVY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),1.2),("BOTTOMPADDING",(0,0),(-1,-1),1.2),
        ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),("LINEBELOW",(0,0),(-1,0),0.8,GOLD)]
    if zebra: st+= [("BACKGROUND",(0,i),(-1,i),colors.HexColor("#F2F4F7")) for i in range(2,len(rows),2)]
    t.setStyle(TableStyle(st)); return t
pct=lambda x:"—" if pd.isna(x) else f"{x*100:+.1f}%"
f2=lambda x:"—" if pd.isna(x) else f"{x:+.2f}"
def lastf(x): return f"{x:,.2f}" if x<10000 else f"{x:,.0f}"
QS={"Q1 · Teyitli yükseliş":"Q1 Teyitli yük.","Q2 · Teyitsiz yükseliş":"Q2 Teyitsiz yük.","Q3 · Teyitli düşüş":"Q3 Teyitli düş.","Q4 · İlgisiz düşüş":"Q4 İlgisiz düş.","Hacimsiz":"Hacimsiz"}
def name(row): return row.Enstrüman+(" *" if row.Olay else "")+(" †" if isinstance(row.Not,str) and row.Not.startswith("Vekil") else "")
def img(fig,w):
    b=io.BytesIO(); fig.savefig(b,format="png",dpi=200,bbox_inches="tight"); plt.close(fig); b.seek(0)
    iw,ih=fig.get_size_inches(); return Image(b,width=w,height=w*ih/iw)
def topbot(t,n):
    n=min(n,len(t)//2); return pd.concat([t.head(n),t.tail(n)])
def charts(t):
    fig,(a1,a2)=plt.subplots(1,2,figsize=(7.6,3.4),gridspec_kw={"width_ratios":[1.15,1]})
    d=t[t.ZVOL.notna()]
    lim=max(abs(d.MOM).max(),0.1)
    a1.axhspan(0,9,xmin=0.5,xmax=1,color="#2e7d32",alpha=.0)
    xm=max(abs(d.ZRET).max(),0.5)*1.35; ym=max(abs(d.ZVOL).max(),0.5)*1.15
    a1.fill_between([0,xm],0,ym,color="#2e7d32",alpha=.07); a1.fill_between([-xm,0],0,ym,color="#c62828",alpha=.07)
    sc=a1.scatter(d.ZRET,d.ZVOL,c=d.MOM,cmap="RdYlGn",norm=TwoSlopeNorm(0,-lim,lim),s=22,edgecolor="#333",linewidth=.3)
    a1.axhline(0,color="#555",ls="--",lw=.7); a1.axvline(0,color="#555",ls="--",lw=.7)
    a1.set_xlim(-xm,xm); a1.set_ylim(-ym,ym)
    ext=d.assign(e=np.hypot(d.ZRET,d.ZVOL)).nlargest(min(12,len(d)),"e")
    for _,rr in ext.iterrows(): a1.annotate(rr.Enstrüman,(rr.ZRET,rr.ZVOL),fontsize=5.6,xytext=(3,2),textcoords="offset points")
    for (x,y,s,ha,va) in [(xm,ym,"Q1 Teyitli yükseliş","right","top"),(xm,-ym,"Q2 Teyitsiz yükseliş","right","bottom"),(-xm,ym,"Q3 Teyitli düşüş","left","top"),(-xm,-ym,"Q4 İlgisiz düşüş","left","bottom")]:
        a1.text(x*.97,y*.97,s,ha=ha,va=va,fontsize=6,color="#12314F",fontweight="bold")
    a1.set_xlabel("ZRET (bileşik getiri z)"); a1.set_ylabel("ZVOL (bileşik hacim z)"); a1.set_title("Kadran saçılımı (renk = MOM)",fontsize=8)
    cb=fig.colorbar(sc,ax=a1,fraction=.04,pad=.01); cb.ax.tick_params(labelsize=5.5)
    b=topbot(t,10).iloc[::-1]
    cols=["#2e7d32" if v>=0 else "#c62828" for v in b.MOMADJ]
    a2.barh(range(len(b)),b.MOMADJ,color=cols,height=.7)
    a2.set_yticks(range(len(b))); a2.set_yticklabels(b.Enstrüman,fontsize=5.8); a2.axvline(0,color="#555",lw=.6)
    m=abs(b.MOMADJ).max()
    for i,v in enumerate(b.MOMADJ): a2.text(v+(0.02*m if v>=0 else -0.02*m),i,f"{v:+.2f}",va="center",ha="left" if v>=0 else "right",fontsize=5.4)
    a2.set_xlim(-m*1.3,m*1.3); a2.set_title(f"Bileşik MOMADJ · en iyi / en kötü {len(b)//2}",fontsize=8)
    for a in (a1,a2): a.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    h=topbot(t,9); M=h[[f"mom_{k}" for k in K]].values.astype(float)
    fig2,ax=plt.subplots(figsize=(7.6,0.2*len(h)+0.75))
    v=np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1
    im=ax.imshow(np.ma.masked_invalid(M),cmap="RdYlGn",norm=TwoSlopeNorm(0,-v,v),aspect="auto")
    ax.set_facecolor("#e0e0e0")
    for i in range(M.shape[0]):
        for j in range(4): ax.text(j,i,"—" if np.isnan(M[i,j]) else f"{M[i,j]:+.2f}",ha="center",va="center",fontsize=5.8)
    ax.set_xticks(range(4)); ax.set_xticklabels(["MOM 1a","MOM 3a","MOM 6a","MOM 12a"]); ax.set_yticks(range(len(h))); ax.set_yticklabels(h.Enstrüman,fontsize=5.8)
    n=len(h)//2; ax.axhline(n-.5,color="#12314F",lw=1.2)
    ax.set_title(f"Pencere bazlı MOM · üst {n} / alt {n} (MOMADJ sırası)",fontsize=8)
    fig2.colorbar(im,ax=ax,fraction=.025,pad=.01).ax.tick_params(labelsize=5.5); fig2.tight_layout()
    return fig,fig2
W=182*mm
R0=pickle.load(open("raw.pkl","rb"))
DROPMAP={"Emtia":R0["COM"],"Tahvil / faiz":R0["BOND"],"Nasdaq 100":R0["NDX"],"BIST 30":[x+".IS" for x in R0["B30"]]}
def ttable(t):
    sub=t if len(t)<=13 else pd.concat([t.head(8),t.tail(5)])
    hdr=["#","Enstrüman","Son","1a","3a","6a","12a","z(getiri)","z(hacim)","MOM","MOMADJ","Kadran"]
    rows=[hdr]
    for i,rr in sub.iterrows():
        rows.append([i+1,name(rr),lastf(rr.Son)]+[pct(rr[f"ret_{k}"]) for k in K]+[f2(rr.ZRET),f2(rr.ZVOL),f2(rr.MOM),f2(rr.MOMADJ),QS[rr.Kadran]])
    wd=[7*mm,34*mm,17*mm,13*mm,13*mm,13*mm,14*mm,13.5*mm,13.5*mm,12.5*mm,14*mm,23*mm]
    tb=tbl(rows,wd)
    if len(t)>13: tb.setStyle(TableStyle([("LINEBELOW",(0,8),(-1,8),1,GOLD)]))
    return tb
story=[]
# ---- sayfa 1
story.append(Paragraph("Yöntem ve Özet",H1))
meth=[["Adım","Formül / kural"],
["Getiri","ret_k = P_t / P_(t−k) − 1 · k = 21/63/126/252. Getiri serilerinde: −D·Δy/100 (D: 10Y 8.5, 30Y 17, 3A 0.25)"],
["Hacim oranı","volratio_k = ort(hacim, son k) / ort(hacim, son 504) · sıfır hacim NaN"],
["Getiri z-skoru","z_ret_k = kesitsel_z(winsorize(ret_k, %2, %98)), ±3 kırpma"],
["Hacim standardizasyonu","z_vol_k = kesitsel_z(winsorize(ln volratio_k, %2, %98)), ±3 kırpma"],
["MOM","MOM_k = z_ret_k × z_vol_k"],
["Bileşik","0.40·1a + 0.30·3a + 0.20·6a + 0.10·12a (MOM, MOMADJ, ZRET, ZVOL)"],
["MOMADJ","MOMADJ_k = z_ret_k × exp(clip(z_vol_k, ±2)/2) · çarpan 0.37x–2.72x · sıralama bununla"]]
story.append(tbl(meth,[32*mm,150*mm]))
nq4=int(((A.MOM>0)&(A.ZRET<0)).sum()); nm=int(A.MOM.notna().sum()); q1=(A.Kadran.str.startswith("Q1")).sum()
t5=", ".join(f"{rr.Enstrüman} ({rr.Evren}, {rr.MOMADJ:+.2f})" for _,rr in A.head(5).iterrows())
story.append(Spacer(1,4))
story.append(Paragraph(f"<b>Özet.</b> {sum(len(t) for t in U.values())} satır, 5 evren. En yüksek 5 MOMADJ: {t5}. Tüm evrenlerde Q1 payı %{q1/len(A)*100:.0f} ({q1}/{len(A)}); hacimli satırların %{nq4/nm*100:.0f}'inde ({nq4}/{nm}) getiri negatifken ham MOM pozitif, bu yüzden sıralama MOMADJ ile.",B))
story.append(Paragraph("Evren özeti",H2))
rows=[["Evren","Adet","Öne çıkan üç (MOMADJ)","En zayıf","Q1","Q3"]]
for k,t in U.items():
    rows.append([k,len(t),", ".join(f"{a} {b:+.2f}" for a,b in zip(t.Enstrüman.head(3),t.MOMADJ.head(3))),f"{t.Enstrüman.iloc[-1]} {t.MOMADJ.iloc[-1]:+.2f}",f"%{t.Kadran.str.startswith('Q1').mean()*100:.0f}",f"%{t.Kadran.str.startswith('Q3').mean()*100:.0f}"])
story.append(tbl(rows,[24*mm,11*mm,79*mm,40*mm,14*mm,14*mm]))
def hline(k,t):
    q3=t.Kadran.str.startswith("Q3").mean(); top=t.iloc[0]; bot=t.iloc[-1]
    x=f"{k}: lider {top.Enstrüman} ({top.MOMADJ:+.2f}, {QS[top.Kadran]})"
    if top.Olay: x+=f", ancak olay işaretli (1a %{top.ret_1a*100:+.0f}, 12a %{top.ret_12a*100:+.0f})"
    q2=t.head(5); q2=q2[q2.Kadran.str.startswith("Q2")]
    if len(q2): x+=f"; ilk beşte hacim teyidi olmayan: {', '.join(q2.Enstrüman)}"
    x+=f"; en zayıf {bot.Enstrüman} ({bot.MOMADJ:+.2f})"
    if q3>=.35: x+=f"; payların %{q3*100:.0f}'i Q3'te, hacimli satış belirgin"
    if len(t)<15: x+="; küçük evren, skorlar gürültülü"
    return x+"."
hl=[hline(k,t) for k,t in U.items()]
story.append(Paragraph(" ".join(hl),B))
P=r["prev"]
story.append(Paragraph("Önceki koşuya göre",H2))
if P:
    ch=P["changes"]
    txt=f"Taban {P['tarih']}. Q1 payı %{P['q1'][0]*100:.0f} → %{P['q1'][1]*100:.0f}. Kadran değiştiren {len(ch)} satır"
    if ch: txt+=": "+", ".join(f"{n} ({e}) {QS[a][:2]}→{QS[b][:2]}" for e,n,a,b in ch[:30])+(" …" if len(ch)>30 else "")
    txt+=". İlk beşten düşenler: "+(", ".join(f"{n} ({e})" for e,n in P["out5"]) or "yok")+"."
    story.append(Paragraph(txt,B))
else:
    story.append(Paragraph("Önceki koşu kaydı yok; karşılaştırma bir sonraki koşuda başlar.",B))
story.append(Spacer(1,4))
story.append(Paragraph("Q1 teyitli yükseliş (+/+) · Q2 teyitsiz yükseliş (+/−) · Q3 teyitli düşüş (−/+) · Q4 ilgisiz düşüş (−/−), ham MOM burada pozitif çıkar ve yanıltır · * olay işareti (1a ≥ %30, 12a < 0) · † vekil ETF hacmi.",S))
story.append(PageBreak())
for k,t in U.items():
    story.append(Paragraph(f"{k} · {len(t)} enstrüman",H1))
    f1,f2_=charts(t); story.append(img(f1,W)); story.append(img(f2_,W*0.92 if len(t)>=18 else W*0.8))
    story.append(Spacer(1,3)); story.append(ttable(t))
    vc=t.Kadran.map(QS).value_counts()
    dr=[x.replace(".IS","") for x,_ in r["dropped"] if x in DROPMAP.get(k,[])]
    vk=t[t.Not.fillna("").str.startswith("Vekil")].Enstrüman.tolist(); hs=t[t.Kadran=="Hacimsiz"].Enstrüman.tolist()
    extra="".join([f" · Vekil hacim: {', '.join(vk)}" if vk else "", f" · Hacimsiz: {', '.join(hs)}" if hs else "", f" · Düşen (<505 bar / veri yok): {', '.join(dr)}" if dr else "", " · Likidite proxy evreni, resmi liste değil." if k=="BIST 100" else ""])
    story.append(Spacer(1,2)); story.append(Paragraph("Kadran dağılımı: "+" · ".join(f"{a} {b}" for a,b in vc.items())+extra,S))
    story.append(PageBreak())
# son sayfa
story.append(Paragraph("Evrenler arası karşılaştırma",H1))
rows=[["Evren","Adet","Medyan 1a","Medyan 12a","Q1","Q2","Q3","Q4","Hacimsiz","Lider (MOMADJ)"]]
for k,t in U.items():
    c=t.Kadran.str[:2].value_counts()
    rows.append([k,len(t),pct(t.ret_1a.median()),pct(t.ret_12a.median())]+[f"%{c.get(q,0)/len(t)*100:.0f}" for q in ["Q1","Q2","Q3","Q4","Ha"]]+[f"{t.Enstrüman.iloc[0]} {t.MOMADJ.iloc[0]:+.2f}"])
story.append(tbl(rows,[26*mm,12*mm,17*mm,17*mm,12*mm,12*mm,12*mm,12*mm,15*mm,47*mm]))
story.append(Paragraph("Tüm evrenlerde en yüksek 15 MOMADJ",H2))
rows=[["#","Enstrüman","Evren","1a","12a","ZRET","ZVOL","MOM","MOMADJ","Kadran"]]
for i,(_,rr) in enumerate(A.head(15).iterrows(),1):
    rows.append([i,name(rr),rr.Evren,pct(rr.ret_1a),pct(rr.ret_12a),f2(rr.ZRET),f2(rr.ZVOL),f2(rr.MOM),f2(rr.MOMADJ),QS[rr.Kadran]])
story.append(tbl(rows,[7*mm,32*mm,24*mm,15*mm,15*mm,14*mm,14*mm,14*mm,16*mm,31*mm]))
story.append(Paragraph("Skorlar kendi evreni içinde standardizedir; bu liste yalnızca tarama amaçlıdır, evrenler arası büyüklük kıyası yapılmaz. BIST 30 payları BIST 100 içinde de yer alır ve farklı skor taşır.",S))
story.append(Paragraph("Veri notları ve kısıtlar",H2))
notes=[f"Veri tarihi {DS}: bugünün kısmi barları atıldı. Minimum 505 bar. Düşenler: "+", ".join(f"{s.replace('.IS','')} ({w})" for s,w in r["dropped"])+".",
"Getiri serileri (^TNX, ^TYX, ^IRX) −D·Δy ile fiyat-eşdeğer getiriye çevrildi; hacimsiz, vekil bağlanmadı. Uluslararası tahviller ETF ile temsil ediliyor; Türkiye için likit vekil yok (EVDS/FRED/Bloomberg gerekli).",
f"Tahvil evreni {len(U['Tahvil / faiz'])} enstrüman: winsorize bu büyüklükte zayıf kalır, ±3 kırpma uygulandı; skorlar gürültülüdür.",
f"BIST 100 resmi liste değil, {r['nbroad']} paylık evrenden likidite ile seçildi. BIST 30 listesi src/fetch.py içinde; çeyrek revizyonlarında (Oca/Nis/Tem/Eki) güncellenmeli.",
"Sürekli vadeli seriler spot kotasyondan farklıdır. Kesitsel çalışmadır, backtest değildir.",
"Kesitsel z-skorlar tarihler arasında doğrudan karşılaştırılmaz; haftalık izleme kadran değişimleri üzerinden yapılır."]
for n in notes: story.append(Paragraph("• "+n,B))
story.append(Spacer(1,8))
story.append(Paragraph("<b>Sorumluluk reddi.</b> Bu rapor yalnızca bilgilendirme amaçlıdır; yatırım tavsiyesi, alım-satım önerisi veya teklif niteliği taşımaz. Veriler ücretsiz kaynaklardan alınmıştır, doğruluğu garanti edilmez. Karar öncesi veriler birincil kaynaklardan teyit edilmelidir.",S))
out=os.environ.get("OUT_DIR","out")+f"/Momentum_Calismasi_{DATE.strftime('%Y-%m-%d')}.pdf"
SimpleDocTemplate(out,pagesize=A4,leftMargin=14*mm,rightMargin=14*mm,topMargin=21*mm,bottomMargin=14*mm,title="Momentum Çalışması").build(story,onFirstPage=band,onLaterPages=band)
print(out)
