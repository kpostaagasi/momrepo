"""PDF: grafik öncelikli, 7 sayfa. Detay tablolar Excel'de."""
import os, pickle, pandas as pd, numpy as np, io
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.colors import TwoSlopeNorm
from matplotlib.ticker import LogLocator, FuncFormatter, NullFormatter
from matplotlib.lines import Line2D
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
_F=os.path.join(os.path.dirname(matplotlib.__file__),"mpl-data","fonts","ttf")  # DejaVu Türkçe karakterler için zorunlu
pdfmetrics.registerFont(TTFont("DV",os.path.join(_F,"DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DVB",os.path.join(_F,"DejaVuSans-Bold.ttf")))
registerFontFamily("DV",normal="DV",bold="DVB")
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":6})
r=pickle.load(open("res.pkl","rb")); U=r["U"]; DATE=r["DATE"]; DS=DATE.strftime("%d.%m.%Y")
RAW=pickle.load(open("raw.pkl","rb"))["data"]
NAVY=colors.HexColor("#12314F"); GOLD=colors.HexColor("#B8862B")
A=pd.concat(U.values()).sort_values("MOM",ascending=False,na_position="last")
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
def tbl(data,widths):
    rows=[[Paragraph(str(x),TH) for x in data[0]]]+[[Paragraph(str(x),TC) for x in row] for row in data[1:]]
    t=Table(rows,colWidths=widths,repeatRows=1)
    st=[("BACKGROUND",(0,0),(-1,0),NAVY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),1.2),("BOTTOMPADDING",(0,0),(-1,-1),1.2),
        ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),("LINEBELOW",(0,0),(-1,0),0.8,GOLD)]
    st+=[("BACKGROUND",(0,i),(-1,i),colors.HexColor("#F2F4F7")) for i in range(2,len(rows),2)]
    t.setStyle(TableStyle(st)); return t
pct=lambda x:"—" if pd.isna(x) else f"{x*100:+.1f}%"
f2=lambda x:"—" if pd.isna(x) else f"{x:+.2f}"
def lastf(x): return f"{x:,.2f}" if x<10000 else f"{x:,.0f}"
def hum(v):
    if pd.isna(v): return "—"
    for d,s in [(1e9,"B"),(1e6,"M"),(1e3,"K")]:
        if v>=d: return f"{v/d:.1f}{s}"
    return f"{v:.0f}"
QS={"Q1 · Teyitli yükseliş":"Q1 Teyitli yük.","Q2 · Teyitsiz yükseliş":"Q2 Teyitsiz yük.","Q3 · Teyitli düşüş":"Q3 Teyitli düş.","Q4 · İlgisiz düşüş":"Q4 İlgisiz düş.","Likidite kilidi":"Likidite kilidi","Hacimsiz":"Hacimsiz"}
QC={"Q1":"#2e7d32","Q2":"#9e9d24","Q3":"#c62828","Q4":"#ef6c00","Li":"#555555","Ha":"#555555"}
def name(row): return row.Enstrüman+(" *" if row.Olay else "")+(" †" if isinstance(row.Not,str) and row.Not.startswith("Vekil") else "")
def img(fig,w):
    b=io.BytesIO(); fig.savefig(b,format="png",dpi=200,bbox_inches="tight"); plt.close(fig); b.seek(0)
    iw,ih=fig.get_size_inches(); return Image(b,width=w,height=w*ih/iw)
W=182*mm
SMA=[(50,"#1f77b4"),(100,"#ff7f0e"),(200,"#7b1fa2")]
PX={"GC=F":"GLD","SI=F":"SLV","PL=F":"PPLT","PA=F":"PALL"}

def ohlc(s,note):
    df=RAW[s]; df=df[df.index<=DATE].copy()
    for c in ("open","high","low"): df[c]=df[c].fillna(df.close)
    if isinstance(note,str) and note.startswith("Vekil") and PX.get(s) in RAW:  # panel hacmi de skordaki vekil hacmi
        pv=RAW[PX[s]].volume; df["volume"]=pv.reindex(df.index).values
    return df
def panel(fig,spec,i,rr):
    df=ohlc(rr.Sembol,rr.Not); n=len(df); x=np.arange(n)
    gs=GridSpecFromSubplotSpec(2,1,subplot_spec=spec,height_ratios=[4,1],hspace=0.04)
    ax=fig.add_subplot(gs[0]); av=fig.add_subplot(gs[1],sharex=ax)
    o,h,l,c=(df[k].values for k in ("open","high","low","close")); up=c>=o
    col=np.where(up,"#2e7d32","#c62828")
    ax.vlines(x,l,h,color=col,lw=.35)
    ax.bar(x,np.maximum(np.abs(c-o),c*1e-4),bottom=np.minimum(o,c),width=.8,color=col,linewidth=0)
    for w,cl in SMA: ax.plot(x,df.close.rolling(w).mean().values,color=cl,lw=.6)
    ax.axhline(c[-1],color="#12314F",lw=.5,ls="--")
    if np.nanmax(h)/np.nanmin(l)>3:  # fiyat aralığı 3 katı aşarsa log; etiketler düz sayı (3×10² değil)
        ax.set_yscale("log"); ax.yaxis.set_major_locator(LogLocator(base=10,subs=(1,2,5)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:,.0f}" if v>=10 else f"{v:g}")); ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(-2,n+1); ax.tick_params(labelbottom=False,labelsize=5,length=2)
    ax.set_title(f"{i}. {rr.Enstrüman} · {rr.Evren} · {lastf(rr.Son)}",loc="left",fontsize=6.6,fontweight="bold",pad=9)
    ax.text(0,1.01,f"1a {pct(rr.ret_1a)} · 3a {pct(rr.ret_3a)} · 12a {pct(rr.ret_12a)}",transform=ax.transAxes,fontsize=5.4,va="bottom",color="#333")
    q=rr.Kadran[:2]
    ax.text(1,1.01,f"MOM {f2(rr.MOM)} · m {rr.m_1a:.2f} · {q}",transform=ax.transAxes,ha="right",va="bottom",fontsize=5.4,color="white",fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25",fc=QC[q],ec="none"))
    v=df.volume.values.astype(float); av.bar(x,np.nan_to_num(v),width=.8,color=col,linewidth=0,alpha=.7)
    av.set_yticks([]); av.tick_params(labelsize=5,length=2)
    av.text(.99,.92,f"son gün hacim {hum(v[-1])}",transform=av.transAxes,ha="right",va="top",fontsize=5)
    m=df.index.month; tk=[j for j in range(1,n) if m[j]!=m[j-1] and m[j] in (1,7)]
    av.set_xticks(tk); av.set_xticklabels([df.index[j].strftime("%m/%y") for j in tk])
    for a in (ax,av): a.spines[["top","right"]].set_visible(False)
def ohlcpage(title,t,foot):
    t=t[t.MOM.notna()].head(10)
    fig=plt.figure(figsize=(7.6,7.9)); gs=GridSpec(5,2,figure=fig,hspace=.62,wspace=.16)
    for i,(_,rr) in enumerate(t.iterrows()): panel(fig,gs[i//2,i%2],i+1,rr)
    h=[Line2D([],[],color=cl,lw=1,label=f"SMA {w}") for w,cl in SMA]+[Line2D([],[],color="#12314F",lw=1,ls="--",label="son kapanış")]
    fig.legend(handles=h,loc="lower center",ncol=4,frameon=False,fontsize=6,bbox_to_anchor=(.5,-.01))
    story.append(Paragraph(title,H1)); story.append(img(fig,W))
    if foot: story.append(Paragraph(foot,S))
    story.append(PageBreak())
def qdist(t): return "Kadran dağılımı: "+" · ".join(f"{a} {b}" for a,b in t.Kadran.map(QS).value_counts().items())

story=[]
# ---- Sayfa 1: Yöntem + Özet
story.append(Paragraph("Yöntem ve Özet",H1))
meth=[["Adım","Formül / kural"],
["Getiri ve hacim","ret_k = P_t / P_(t−k) − 1 · volratio_k = ort(hacim, son k) / ort(hacim, son 504) · k = 21/63/126/252 (1a/3a/6a/12a)"],
["Normalizasyon","Sıra tabanlı normal skor (van der Waerden): z = Φ⁻¹((sıra − 3/8)/(n + 1/4)), ret_k ve ln(volratio_k) için, evren içinde"],
["Hacim çarpanı","m(z) = (1 − B) + 2B·Φ(z), B = 0,50 → m ∈ [0,506 ; 1,494], daima pozitif, E[m] = 1,000"],
["Momentum","MOM_k = z(ret_k) × m(z_hacim_k) · MOM = 0,40·1a + 0,30·3a + 0,20·6a + 0,10·12a"],
["Likidite kapısı","kilit = (O=H=L=C) ve |değişim| ≥ %4 · kapı = son 10 günde ≥ 3 kilit VEYA 5g/60g hacim < 0,25 → MOM hesaplanmaz"]]
story.append(tbl(meth,[30*mm,152*mm]))
q1=(A.Kadran.str.startswith("Q1")).sum()
t5=", ".join(f"{rr.Enstrüman} ({rr.Evren}, {rr.MOM:+.2f})" for _,rr in A.drop_duplicates("Sembol").head(5).iterrows())
story.append(Spacer(1,4))
story.append(Paragraph(f"<b>Özet.</b> {len(A)} satır, 5 evren. Birleşik sıralamada en yüksek 5 MOM: {t5}. Tüm evrenlerde Q1 (teyitli yükseliş) payı %{q1/len(A)*100:.0f} ({q1}/{len(A)}).",B))
story.append(Paragraph("Evren özeti",H2))
rows=[["Evren","Adet","Öne çıkan üç (MOM)","En zayıf","Q1","Q3","Medyan 1a"]]
for k,t in U.items():
    w=t[t.MOM.notna()].iloc[-1]  # likidite kilidi satırları skorlanmaz; en zayıf skorlanan isim
    rows.append([k,len(t),", ".join(f"{a} {b:+.2f}" for a,b in zip(t.Enstrüman.head(3),t.MOM.head(3))),f"{w.Enstrüman} {w.MOM:+.2f}",
                 f"%{t.Kadran.str.startswith('Q1').mean()*100:.0f}",f"%{t.Kadran.str.startswith('Q3').mean()*100:.0f}",pct(t.ret_1a.median())])
story.append(tbl(rows,[24*mm,10*mm,74*mm,36*mm,11*mm,11*mm,16*mm]))
story.append(Paragraph("Öne çıkanlar",H2))
hl=["Evren liderleri: "+"; ".join(f"{k} {t.iloc[0].Enstrüman} ({t.iloc[0].MOM:+.2f}, {QS[t.iloc[0].Kadran]})" for k,t in U.items())+"."]
q2=A.drop_duplicates("Sembol").head(10); q2=q2[q2.Kadran.str.startswith("Q2")]
if len(q2): hl.append("İlk 10'da hacim teyidi olmayan (Q2, uyarı): "+", ".join(f"{a} ({b})" for a,b in zip(q2.Enstrüman,q2.Evren))+".")
G=A[A.Kilit]
hl.append(f"Likidite kapısına takılan {len(G)} enstrüman"+(": "+", ".join(f"{a} ({b})" for a,b in zip(G.Enstrüman,G.Evren)) if len(G) else "")+" — skorlanmadı, sayfa 7'de.")
ev=A[A.Olay].drop_duplicates("Sembol")
if len(ev): hl.append("Olay işaretli (1a ≥ %30, 12a < 0; momentum değil tek seferlik olay olabilir): "+", ".join(f"{a} ({pct(b)} / {pct(c)})" for a,b,c in zip(ev.Enstrüman,ev.ret_1a,ev.ret_12a))+".")
hl.append("Tahvil evreni için OHLC sayfası yok: uluslararası bacaklar ETF vekilleriyle temsil edildiği için mum grafiği getiriyi değil ters yönlü fiyatı gösterir. Tahvil özet tablosunda, kadran haritasında ve Excel'de yer alır.")
for x in hl: story.append(Paragraph("• "+x,B))
story.append(Spacer(1,4))
story.append(Paragraph("Tüm veri matrisi (33 kolon), pencere bazlı skorlar, yöntem gerekçeleri ve düşen semboller Excel çalışma kitabındadır. * olay işareti · † vekil ETF hacmi.",S))
story.append(PageBreak())
# ---- Sayfa 2: birleşik liderler (BIST 30 ⊂ BIST 100: aynı sembolün yüksek skorlu kaydı; tahvil hariç)
L=A[(A.Evren!="Tahvil / faiz")&A.MOM.notna()].drop_duplicates("Sembol")
ohlcpage("Momentum liderleri · tüm evrenler",L,"Birleşik sıralama; aynı sembol birden çok evrendeyse yüksek skorlu kayıt tutulur. Likidite kapısındaki ve hacimsiz isimler listeye giremez. Tahvil evreni hariç (ETF fiyatı getiriyle ters yönlüdür).")
# ---- Sayfa 3–6: evren bazlı
for k in ["Emtia","Nasdaq 100","BIST 100","BIST 30"]:
    ohlcpage(f"{k} · en yüksek MOM 10",U[k],qdist(U[k]))
# ---- Sayfa 7: kadran haritası + likidite kapısı
story.append(Paragraph("Kadran haritası ve likidite kapısı",H1))
fig,axs=plt.subplots(3,2,figsize=(7.6,7.0)); NORM=TwoSlopeNorm(0,-2.5,2.5)
for a,(k,t) in zip(axs.flat,U.items()):
    d=t[t.ZVOL.notna()]
    xm=max(abs(d.ZRET).max(),.5)*1.3; ym=max(abs(d.ZVOL).max(),.5)*1.2
    a.fill_between([0,xm],0,ym,color="#2e7d32",alpha=.07); a.fill_between([-xm,0],0,ym,color="#c62828",alpha=.07)
    a.scatter(d.ZRET,d.ZVOL,c=d.MOM,cmap="RdYlGn",norm=NORM,s=12,edgecolor="#333",linewidth=.25)
    a.axhline(0,color="#555",ls="--",lw=.6); a.axvline(0,color="#555",ls="--",lw=.6)
    for _,rr in d.assign(e=np.hypot(d.ZRET,d.ZVOL)).nlargest(min(6,len(d)),"e").iterrows():
        a.annotate(rr.Enstrüman,(rr.ZRET,rr.ZVOL),fontsize=5,xytext=(2,2),textcoords="offset points")
    a.set_xlim(-xm,xm); a.set_ylim(-ym,ym); a.set_title(f"{k} · {len(d)} skorlu",fontsize=7,loc="left")
    a.set_xlabel("ZRET",fontsize=5.5); a.set_ylabel("ZVOL",fontsize=5.5); a.spines[["top","right"]].set_visible(False)
lg=axs.flat[5]; lg.axis("off")
for j,(q,s) in enumerate([("Q1","Teyitli yükseliş · + / + · m ≈ 1,5"),("Q2","Teyitsiz yükseliş · + / − · m ≈ 0,5 · uyarı"),("Q3","Teyitli düşüş · − / + · m ≈ 1,5 · dağıtım"),("Q4","İlgisiz düşüş · − / − · m ≈ 0,5")]):
    lg.text(.02,.92-j*.13,q,color="white",fontweight="bold",fontsize=6.5,bbox=dict(boxstyle="round,pad=.25",fc=QC[q],ec="none"),transform=lg.transAxes)
    lg.text(.14,.92-j*.13,s,fontsize=6.2,transform=lg.transAxes,va="baseline")
lg.text(.02,.36,"x = ZRET (bileşik getiri skoru), y = ZVOL (bileşik hacim skoru).\nGölgeli: teyitli bölgeler. Kapı ve hacimsiz satırlar haritada yok.",fontsize=5.6,transform=lg.transAxes,va="top")
cax=lg.inset_axes([.05,.06,.9,.07]); cb=fig.colorbar(plt.cm.ScalarMappable(NORM,"RdYlGn"),cax=cax,orientation="horizontal")
cb.ax.tick_params(labelsize=5.5); cb.set_label("MOM (renk skalası, tüm evrenlerde ortak)",fontsize=5.6)
fig.tight_layout(); story.append(img(fig,W*0.93))
story.append(Paragraph("Likidite kapısına takılanlar",H2))
if len(G)==0: story.append(Paragraph("Bu koşuda kapıya takılan enstrüman yok — kapı hiç tetiklenmiyorsa OHLC verisinin geldiği doğrulanmalı.",S))
else:
    rows=[["Enstrüman","Evren","Son","1a","3a","Kilit gün","5g/60g hacim","Durum"]]
    for _,rr in G.sort_values(["Evren","Enstrüman"]).iterrows():
        rows.append([name(rr),rr.Evren,lastf(rr.Son),pct(rr.ret_1a),pct(rr.ret_3a),int(rr.KilitGün),"—" if pd.isna(rr.VolDrain) else f"{rr.VolDrain:.2f}",rr.GateNeden or "—"])
    story.append(tbl(rows,[26*mm,20*mm,16*mm,14*mm,14*mm,13*mm,18*mm,61*mm]))
story.append(Spacer(1,6))
story.append(Paragraph("<b>Sorumluluk reddi.</b> Bu rapor yalnızca bilgilendirme amaçlıdır; yatırım tavsiyesi, alım-satım önerisi veya teklif niteliği taşımaz. Veriler ücretsiz kaynaklardan alınmıştır, doğruluğu garanti edilmez. Skorlar kendi evreni içinde hesaplanır; evrenler arası kıyas yapılmaz.",S))
out=os.environ.get("OUT_DIR","out")+f"/Momentum_Calismasi_v3_{DATE.strftime('%Y-%m-%d')}.pdf"
SimpleDocTemplate(out,pagesize=A4,leftMargin=14*mm,rightMargin=14*mm,topMargin=21*mm,bottomMargin=14*mm,title="Momentum Çalışması").build(story,onFirstPage=band,onLaterPages=band)
print(out)
