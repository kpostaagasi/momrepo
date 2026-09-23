"""Haftalık momentum raporu: veri → hesap → Excel → PDF → e-posta özeti."""
import os, sys, subprocess, shutil, pickle, pandas as pd
OUT=os.environ.setdefault("OUT_DIR","out"); os.makedirs(OUT,exist_ok=True); os.makedirs("state",exist_ok=True)
for f in ["fetch","compute","xl","pdf"]:
    print(f"== {f}"); subprocess.run([sys.executable,f"src/{f}.py"],check=True)
r=pickle.load(open("res.pkl","rb")); U=r["U"]; D=r["DATE"].strftime("%d.%m.%Y")
A=pd.concat(U.values()).sort_values("MOMADJ",ascending=False)
L=[f"Veri tarihi: {D}","","1) Evren liderleri (düzeltilmiş momentum, MOMADJ – ilk 3)"]
for k,t in U.items():
    L.append(f"  {k}: "+", ".join(f"{a} {b:+.2f}" for a,b in zip(t.Enstrüman.head(3),t.MOMADJ.head(3)))+f"  | teyitli yükseliş (Q1) %{t.Kadran.str.startswith('Q1').mean()*100:.0f}, teyitli düşüş (Q3) %{t.Kadran.str.startswith('Q3').mean()*100:.0f}")
ev=A[A.Olay]
if len(ev): L+=["","2) Olay işaretliler (1 aylık getiri ≥ %30, 12 aylık < 0; haber akışı kontrol edilmeli): "+", ".join(f"{a} ({b})" for a,b in zip(ev.Enstrüman,ev.Evren))]
P=r["prev"]
if P:
    L+=["",f"3) Önceki çalışmaya göre değişim ({P['tarih']}): Q1 payı %{P['q1'][0]*100:.0f} → %{P['q1'][1]*100:.0f}; kadran değiştiren {len(P['changes'])} satır; ilk beşten düşen: "+(", ".join(f"{n} ({e})" for e,n in P["out5"]) or "yok")]
L+=["","Ayrıntılı analiz ekteki PDF raporda, tüm veri matrisi Excel dosyasındadır."]
open(f"{OUT}/summary.txt","w").write("\n".join(L))
shutil.move("state/last_new.csv","state/last.csv")
print("Özet yazıldı:",f"{OUT}/summary.txt")  # içerik loglara basılmaz (public repo)
