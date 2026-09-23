"""Kullanım: python send.py preview | team   (ortam değişkenleri: SMTP_USER, SMTP_PASS, MAIL_TO, MAIL_CC)"""
import os, sys, glob, smtplib, datetime as dt
from email.message import EmailMessage
mode=sys.argv[1]; OUT=os.environ.get("OUT_DIR","out")
pdf=sorted(glob.glob(f"{OUT}/Momentum_Calismasi_*.pdf"))[-1]; xlsx=pdf[:-4]+".xlsx"
date=dt.date.fromisoformat(os.path.basename(pdf)[19:29])
if (dt.date.today()-date).days>6: sys.exit(f"Rapor bayat ({date}); gönderilmedi.")
body=open(f"{OUT}/summary.txt").read()
user=os.environ["SMTP_USER"]; m=EmailMessage(); m["From"]=user
subj=f"Getiri–Hacim Momentum Çalışması · {date:%d.%m.%Y}"
if mode=="preview":
    m["To"]=user; m["Subject"]="[ONAY BEKLİYOR] "+subj
    link=f"{os.environ.get('GITHUB_SERVER_URL','')}/{os.environ.get('GITHUB_REPOSITORY','')}/actions/workflows/send.yml"
    body=f"Ekibe göndermek için: {link} → Run workflow.\nGöndermezsen ekibe hiçbir şey gitmez.\n\n"+body
else:
    m["To"]=os.environ["MAIL_TO"]
    if os.environ.get("MAIL_CC"): m["Cc"]=os.environ["MAIL_CC"]
    m["Subject"]=subj
    body=("Merhaba,\n\n"
          "Bu haftanın getiri–hacim momentum çalışmasını ekte paylaşıyorum. Öne çıkan başlıklar aşağıda:\n\n"
          +body+
          "\n\nSorularınız ve yorumlarınız için bana ulaşabilirsiniz.\n\n"
          "Saygılarımla,\nKamil Postaagasi")
m.set_content(body)
for f,t in [(pdf,("application","pdf")),(xlsx,("application","vnd.openxmlformats-officedocument.spreadsheetml.sheet"))]:
    m.add_attachment(open(f,"rb").read(),maintype=t[0],subtype=t[1],filename=os.path.basename(f))
with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
    s.login(user,os.environ["SMTP_PASS"]); s.send_message(m)
print("Gönderildi:",mode,m["Subject"])  # alıcılar loglara basılmaz
