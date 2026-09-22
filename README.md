# Getiri–Hacim Momentum Raporu · haftalık otomasyon

Her pazartesi 09:00 (TR) cuma kapanışıyla PDF + Excel üretir, önce **yalnızca sana** önizleme gönderir. Ekibe gönderim, sen onaylayana kadar yapılmaz.

## Akış
1. `build.yml` (cron) → `run.py` → `out/` şifrelenip artifact olarak yüklenir → önizleme maili `[ONAY BEKLİYOR]` → `state/last.csv.enc` (şifreli) commit
2. Önizlemeyi kontrol et → Actions → **Momentum - ekibe gönder (onay)** → Run workflow
3. `send.yml` son başarılı üretimin artifact'ını indirip çözer ve ekibe yollar (6 günden eski rapor gönderilmez)

## Gizlilik (public repo)
- Kod açık; rapor içeriği açık değildir. Artifact ve karşılaştırma tabanı `ARTIFACT_PASS` ile AES-256 şifrelenir, düz `state/last.csv` commit'lenmez.
- Rapor özeti ve alıcı adresleri Actions loglarına yazılmaz.
- Workflow'lar yalnızca zamanlayıcı ve `workflow_dispatch` ile çalışır; fork/PR'lar secret'lara erişemez. Çalıştırma yetkisi yalnızca yazma izni olanlardadır.
- Artifact'ı elle çözmek için:
  `openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in momentum-rapor.tar.gz.enc | tar -xzf -`

## Kurulum
1. Bu klasörü bir GitHub reposuna push et (public olabilir).
2. Gmail: 2 adımlı doğrulama açık olmalı → Google Hesabı → Uygulama şifreleri → 16 haneli şifre al.
3. Repo → Settings → Secrets and variables → Actions:
   - `SMTP_USER` gönderen Gmail adresi
   - `SMTP_PASS` uygulama şifresi
   - `MAIL_TO` ekip adresleri, virgülle
   - `MAIL_CC` (opsiyonel)
   - `ARTIFACT_PASS` rapor/artifact şifreleme parolası (uzun, rastgele; ör. `openssl rand -base64 32`)
4. Settings → Actions → General → Workflow permissions: **Read and write**.
5. Actions → Momentum - haftalık üretim → Run workflow ile ilk testi yap.

## Bakım
- BIST 30 listesi `src/fetch.py` içinde (`B30`); çeyrek revizyonlarında güncelle (Oca/Nis/Tem/Eki).
- BIST 100 geniş evreni `BROAD`; yeni halka arzlar eklenmeli.
- Nasdaq 100 listesi her koşuda api.nasdaq.com'dan çekilir; başarısızsa `state/ndx.txt` kullanılır.
- Semboller %10'dan fazla başarısızsa ya da son bar 4 günden eskiyse iş durur, mail gitmez.
- Parametre değişikliği (ağırlık, taban, winsorize) yapılırsa commit mesajına ve rapora yazılmalı; aksi halde haftalar karşılaştırılamaz.
