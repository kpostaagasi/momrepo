# Getiri–Hacim Momentum Raporu — Ekip Promptu (v3)

Bu dosya, **v1 promptunun yerini alır.** İki bölümden oluşur:

- **Bölüm A** — doğrudan bir AI asistanına yapıştırılacak prompt. Yalnızca `PROMPT BAŞLANGIÇ` ve `PROMPT BİTİŞ` arasını kopyalayın.
- **Bölüm B** — ekip için kullanım notları, yorumlama kuralları, sürüm geçmişi.

> Bu sürüm, repodaki üretim koduyla (`run.py` + `src/`) denetlenip hizalandı. Bölüm B'deki
> referans koşu **v3 formülüyle** üretilmiştir.

---

# BÖLÜM A — Kopyalanacak prompt

```
════════════════════════ PROMPT BAŞLANGIÇ ════════════════════════
```

Bir fon yönetim ekibi için **getiri ve hacmi birleştiren kesitsel momentum çalışması** hazırlayacaksın. Çıktı iki dosyadır: grafik öncelikli bir PDF rapor ve tam veri matrisini içeren bir Excel çalışma kitabı. Türkçe yaz, profesyonel ve sayısal ol, uzun paragraflardan kaçın — bulgular tabloya girer.

## 1. Temel ilke

> **Yön getiriden gelir. Hacim yalnızca o yöne duyulan güveni ölçeklendirir.**

Bu ilke formülün tamamını belirler: hacim toplamaya değil **çarpmaya** girer ve çarpanı **daima pozitiftir**. Hacim hiçbir koşulda bir sinyalin işaretini çeviremez.

## 2. Veri

Kaynak: Yahoo Finance günlük OHLCV.
`https://query1.finance.yahoo.com/v8/finance/chart/{SEMBOL}?range=3y&interval=1d`
Kullanıcı ajanı başlığı gönder. Başarısız isteklerde **3, 6 ve 9 saniye** bekle, en fazla 3 kez dene.

**Veri filtresi: en az 505 bar.** 252 günlük getiri penceresi 253, 504 günlük hacim tabanı ise 505 bar gerektirir; ikisi de aynı anda bulunmalıdır. 230 bar eşiği **yetersizdir** — 253 ile 505 arasındaki seriler 12 aylık pencerede hesaplanamaz. Son barı veri tarihinden 7 günden eski olan, ya da veri hiç gelmeyen sembolleri evrenden düşür ve hangilerinin neden düştüğünü raporla.

Beş evren, her biri **kendi içinde** standardize edilir:

| Evren | Kapsam |
|---|---|
| Emtia | 21 vadeli: GC=F, SI=F, PL=F, PA=F, HG=F, BZ=F, NG=F, RB=F, HO=F, ZC=F, ZS=F, ZW=F, ZL=F, ZR=F, ZO=F, KC=F, CC=F, SB=F, CT=F, LE=F, HE=F |
| Tahvil / faiz | ^TNX, ^TYX, ^IRX + IGLT.L, EXHC.DE, 1482.T, XGB.TO, CBON, TLT, IEF |
| Nasdaq 100 | Endeks bileşenleri |
| BIST 100 | Geniş BIST evreninden 60 günlük TL işlem hacmine göre en likit 100 pay |
| BIST 30 | AEFES, AKBNK, ASELS, ASTOR, BIMAS, DSTKF, EKGYO, ENKAI, EREGL, FROTO, GARAN, GUBRF, ISCTR, KCHOL, KRDMD, MGROS, PETKM, PGSUS, SAHOL, SASA, SISE, TAVHL, TCELL, THYAO, TOASO, TRALT, TTKOM, TUPRS, VAKBN, YKBNK |

## 3. Hacim veri kalitesi

Sürekli vadeli kontrat serilerinde Yahoo hacmi güvenilmezdir. Son 120 bar üzerinde kalite testi:

- NaN olmayan gözlem ≥ 60 **ve** kapsama oranı ≥ %60
- medyan hacim > 0
- 90. yüzdelik / medyan ≤ 5,0
- medyanın %20'sinin altındaki günlerin payı ≤ %35

Testi geçemeyenlere **ETF hacmi vekil bağla**: altın→GLD, gümüş→SLV, platin→PPLT, paladyum→PALL.

Birleştirirken tarihleri **güne yuvarla** (`normalize()`). Vadeli ve ETF serilerinin zaman damgaları farklı saatlerde gelir; ham tarih üzerinden merge **hata vermeden** boş sonuç üretir.

**Getiri serileri (^TNX, ^TYX, ^IRX) hacimsizdir** ve vekil bağlanmaz. Bunlar fiyat değil faiz oranı serisidir (ör. ^TNX ≈ 4,2); doğrudan oran olarak alınırsa hem yanlış işaretli hem de ölçek olarak anlamsız olur. Fiyat-eşdeğer getiriye çevir:

```
ret_k = −D × Δy_k / 100          D = 8,5 (10Y) · 17,0 (30Y) · 0,25 (3A)
```

yani faiz 100 baz puan arttıysa 8,5 yıllık D ile ≈ −%8,5 getiri. Böylece bu üç isim tahvil ETF'leriyle **aynı yönde** okunur. Hacim kolonları boş kalır, MOM hesaplanmaz, kadran "Hacimsiz" olur — ancak getiri kolonları anlamlı ve doludur.

## 4. Likidite kapısı

Fiyat taban veya tavanda kilitliyken hacim "ilgi" ölçüsü olmaktan çıkar: işlem yokluğu ilgisizlik değil, **karşı tarafın bulunmamasıdır**.

```
kilit_günü = (açılış = yüksek = düşük = kapanış)  VE  (|günlük değişim| ≥ %4)
kapı       = son 10 günde kilit ≥ 3 gün  VEYA  (5g ort. hacim / 60g ort. hacim) < 0,25
```

Kapıya takılan enstrümanda **hacim bileşeni ve MOM hesaplanmaz**; ayrı kategoride ("Likidite kilidi") raporlanır.

**%4 eşiği zorunlu.** Yalnızca "OHLC düz" koşulu kullanılırsa yanlış pozitif üretir: PL=F ve PA=F'de Yahoo gün içi aralık yerine uzlaşma fiyatı yayınlar — OHLC düz gelir ama fiyat değişimi %0,3 ve hacim sıfırdır. Bu veri artefaktıdır, likidite kilidi değil.

**Kapı, 505-bar filtresinden önce değerlendirilmelidir.** Kapı testi yalnızca son 10 barı ve 60 günlük hacmi gerektirir; 12 aylık getiriye ihtiyacı yoktur. Filtre önce çalışırsa, likiditesi bitmiş bir isim (ör. 412 barla DSTKF) sessizce evrenden düşer ve raporlanması gereken en önemli olay kaybolur. Kapıya takılan satır sıralamaya girmez, `MOM` boş kalır.

## 5. Hesaplama

Pencereler: **k ∈ {21, 63, 126, 252}** işlem günü → 1a / 3a / 6a / 12a.

**5.1 Getiri ve hacim oranı**
```
ret_k      = P_t / P_(t−k) − 1
volratio_k = (son k günün ort. hacmi) / (son 504 günün ort. hacmi)
```
Taban **504 gündür, 252 değil**. 252 kullanılırsa 12 aylık pencerede oran herkes için tam 1,00 olur, ln(1)=0 çıkar ve o pencere tamamen sinyalsiz kalır.

**5.2 Normalizasyon — sıra tabanlı normal skor (van der Waerden)**
```
z = Φ⁻¹( (sıra − 3/8) / (n + 1/4) )
```
Hem `ret_k` hem `ln(volratio_k)` için, her evren kendi içinde.

Z-skor kullanma. Basit getiri aşağıda −%100 ile sınırlı, yukarıda sınırsızdır; sağa çarpıktır. Jarque-Bera testi 8 pencere/evren kombinasyonunun 7'sinde normalliği reddeder (Nasdaq 12a: çarpıklık +3,57, basıklık +18,13). Sıra dönüşümü tasarım gereği normaldir (çarpıklık 0,00 · basıklık −0,18, her zaman), uç değerlere bağışıktır ve **winsorize gerektirmez**.

**5.3 Hacim çarpanı — daima pozitif**
```
m(z) = (1 − B) + 2B · Φ(z)          B = 0,50  →  m ∈ [0,506 ; 1,494]
```
Parantezler önemlidir: önce `1 − B`, sonra `2B·Φ(z)` toplanır. Yazım hatası olarak `1 − (B + 2B·Φ(z))` okunursa m ∈ [−0,5 ; 0,5] çıkar ve "daima pozitif" ilkesi kendi kendini çürütür.

z sıra tabanlı normal skor olduğu için Φ(z) **tam olarak yüzdelik sırayı** verir ve [0,1] aralığında düzgün dağılır. Sonuçları:

| Özellik | Değer |
|---|---|
| m > 0 her zaman | işaret tuzağı yapısal olarak yok |
| E[m] | **tam 1,000** — kesitsel seviye kaymaz |
| m(medyan hacim) | 1,00 — ortalama hacimli isim getirisini olduğu gibi taşır |
| en yüksek/en düşük oran | 3,0x (sınırlı) |

`exp(z/2)` kullanma: oran 12,2x'e çıkar, üst uç sınırsızdır ve E[m] = e^(1/8) = 1,133 olduğu için her skoru sistematik %13 şişirir.

**5.4 Momentum**
```
MOM_k = z(ret_k) × m(z_hacim_k)
MOM   = 0,40·MOM_1a + 0,30·MOM_3a + 0,20·MOM_6a + 0,10·MOM_12a
```
**Tek metrik.** MOM_ADJ gibi ikinci bir sıralama ölçütü yok — çarpan pozitif olduğu için gerek kalmadı.

Ayrıca raporlanacak yardımcı büyüklükler: `ZRET` ve `ZVOL` (aynı ağırlıklarla bileşik normal skorlar), kadran ataması için.

**5.5 Kadranlar** (bileşik ZRET ve ZVOL işaretine göre)

| Kadran | Getiri | Hacim | Çarpan | Sonuç |
|---|---|---|---|---|
| Q1 · Teyitli yükseliş | + | + | ~1,5 | büyük pozitif |
| Q2 · Teyitsiz yükseliş | + | − | ~0,5 | küçük pozitif |
| Q3 · Teyitli düşüş | − | + | ~1,5 | büyük negatif |
| Q4 · İlgisiz düşüş | − | − | ~0,5 | küçük negatif |
| Likidite kilidi | — | — | — | skorlanmaz |
| Hacimsiz | +/− | yok | — | yalnızca getiri |

## 6. PDF rapor

**Kural: önce grafik, sonra tablo, yazı minimum.**

**Sayfa 1 — Yöntem + Özet**
1. Yöntem tablosu: getiri · hacim oranı · getiri normalizasyonu · hacim normalizasyonu · likidite kapısı · hacim çarpanı · momentum · bileşik. Formüller açık yazılır.
2. Özet paragrafı: tüm evrenlerde en yüksek 5 MOM, genel Q1 payı, çarpan aralığı ve ortalaması, kapı sayısı, işaret uyuşmazlığı
3. Evren tablosu: evren, adet, öne çıkan üç (skorla), en zayıf, Q1 payı, Q3 payı
4. "Öne çıkanlar": evren liderleri ve dikkat çeken kadran değişimleri, 4–5 cümle
5. Kadran tanımları: tek satır dipnot

**Her evren için bir sayfa**, bu sırayla:
1. Yan yana iki grafik — kadran saçılımı ve bileşik MOM yatay çubuk
2. Altında pencere bazlı MOM ısı haritası
3. En altta tablo: en iyi 8 + en kötü 5 (enstrüman, son, 1a/3a/6a/12a getiri, z(getiri), z(hacim), MOM, **m (1a)**, kadran)
4. Kadran dağılımı: tek satır dipnot

**Likidite kapısı sayfası** — kapıya takılan enstrümanlar: evren, son, 1a, 3a, kilit gün sayısı, 5g/60g hacim oranı, durum açıklaması.

**Son sayfa** — evrenler arası karşılaştırma, tüm evrenlerde en yüksek 15 MOM, veri notları ve kısıtlar, sorumluluk reddi.

**Grafik şartnamesi**

| Grafik | Özellik |
|---|---|
| Kadran saçılımı | x = ZRET, y = ZVOL, renk = MOM (RdYlGn, sıfır merkezli norm), Q1 ve Q3 bölgeleri hafif gölgeli, eksenler sıfırda çizgili, en uç 12 nokta etiketli, kadran isimleri köşelerde. y ekseni etiketi çarpan aralığını belirtir |
| Bileşik MOM çubuk | Yatay, en iyi/en kötü 10, pozitif yeşil negatif kırmızı, uçlarda değer etiketi, x ekseni etiketinde formül. **Skorlanmayan satırlar (likidite kilidi, hacimsiz) grafiğe girmez** — çubuk çizemeyen boş etiketli satır olarak görünürler |
| Isı haritası | Satır = en iyi 9 + en kötü 9, sütun = 4 pencere, hücrede sayı, simetrik renk ölçeği |

**Biçim:** A4 dikey, DejaVu Sans (Türkçe karakterler için zorunlu), lacivert `#12314F` üst bant, altın `#B8862B` ayraç, tablo gövdesi 6,1–6,7 punto, üstbilgide veri tarihi, altbilgide sayfa numarası ve "Yatırım tavsiyesi değildir".

## 7. Excel çalışma kitabı

7 sekme: `Yöntem` · `Emtia` · `Tahvil` · `Nasdaq 100` · `BIST 100` · `BIST 30` · `TUMU`

`Yöntem` sekmesi: tüm adımlar, ağırlıklar, çarpan formülü ve özellikleri, kadran tanımları, likidite kapısı eşikleri, hacim vekilleri, çarpan ölçümleri (min/max/ortalama/medyan), işaret uyuşmazlığı ve "BIST 30, BIST 100'ün alt kümesidir; skorlar evren içinde hesaplandığı için aynı hissenin iki sekmedeki skoru farklıdır" notu.

Veri sekmeleri 33 kolon: Enstrüman · Evren · Son · Getiri 1a/3a/6a/12a · Ort hacim 1a/3a/6a/12a · Hacim oranı 1a/3a/6a/12a · z getiri 1a/3a/6a/12a · z hacim 1a/3a/6a/12a · MOM 1a/3a/6a/12a · z getiri bileşik · z hacim bileşik · MOM bileşik · Çarpan 1a · Çarpan 3a · Kadran.

Biçim: getiriler `0.0%`, hacimler `#,##0`, skorlar `0.00`. Başlık satırı lacivert dolgu + beyaz kalın, `freeze_panes="D2"`, tüm aralıkta otomatik filtre (kolon sayısı sabit yazılmaz), MOM azalan sıralı.

## 8. Dosya adlandırma

Veri tarihini serinin **son barından türet**, sabit kodlama.
`Momentum_Calismasi_v3_YYYY-AA-GG.pdf` ve `.xlsx`. Rapor üstbilgisinde ve Excel Yöntem sekmesinde aynı tarih.

## 9. Teslimden önce kontrol et

- Son bar tarihi beklenen işlem günü mü
- Her evrende `zvol_12a` standart sapması ≈ 1,0 mu — **0 ise hacim tabanı yanlışlıkla 252 güne ayarlanmıştır**
- Çarpan aralığı [0,506 ; 1,494], **ortalaması 1,000** mu — değilse Φ dönüşümü yanlış
- Vekil bağlanan enstrümanlarda hacim kolonları dolu mu — boşsa tarih yuvarlama atlanmıştır
- Likidite kapısı emtiada yanlış pozitif üretiyor mu — üretiyorsa %4 eşiği eksiktir
- **Likidite kilidi sayfası boş değil mi** — hiç kapı yoksa hesap çalışmıyor demektir, önce OHLC'nin gerçekten geldiğini doğrula
- MOM işareti z(getiri) işaretiyle uyuşmayan isim sayısı ≤ %3 mü (bileşik toplamdan kaynaklanır, normaldir)
- Tablolarda sayılar satır içinde bölünüyor mu
- Grafiklerde boş etiketli satır var mı — skorlanmayan satırlar sızmış olabilir
- 1 aylık getirisi aşırı yüksek **ve** 12 aylık getirisi negatif olan isimleri ayrıca işaretle — bunlar momentum değil tek seferlik olay taşır
- Türkçe karakterler PDF'te doğru görünüyor mu

Raporu teslim ederken önceki koşuya göre **değişenleri** kısaca özetle: kadran değiştiren enstrümanlar, ilk beşten düşenler, Q1 payındaki kayma, likidite kapısına yeni takılanlar.

```
════════════════════════ PROMPT BİTİŞ ════════════════════════
```

---

# BÖLÜM B — Ekip notları

## Ne sıklıkta

Haftalık, cuma kapanışı sonrası. Kesitsel skorlar aynı gün ve aynı evren içinde anlamlıdır; farklı tarihlerin skorları doğrudan karşılaştırılamaz. **Kadran değişimleri** karşılaştırılabilir ve asıl izlenmesi gereken budur.

## Yorumlama kuralları

1. **Tek metrik MOM.** Eski MOM_ADJ ayrımı kaldırıldı. Bir çıktı hâlâ iki metrik gösteriyorsa eski sürümdür.
2. **Q2 bir uyarıdır.** Getiri güçlü ama hacim zayıfsa ralli katılımla teyit edilmemiştir. 21 Ağustos koşusunda altın Q2'ydi; 15 Eylül'de Q4'e, 25 Eylül'de Q3'e düştü ve fiyat bu sürede %7 geriledi.
3. **Q3 pozisyon azaltma sinyalidir**, sadece zayıflık değil — hacimli satış dağıtım anlamına gelir.
4. **Likidite kilidi kategorisi okunmadan geçilmez.** Buradaki isimler skorlanmadıkları için sıralamalarda görünmez, ama genellikle en önemli olaylardır. 25 Eylül 2026 koşusunda BIST 100'de 13, BIST 30'da DSTKF.
5. **Tek seferlik olaylara dikatt.** 1 aylık getirisi +%100 civarında, 12 aylık getirisi negatif olan bir isim momentum değil olay taşır. 15 Eylül 2025 koşusunda MARTI bu profille 1. sıradaydı (MOM_ADJ +6,73); on gün sonra taban kilidine girdi ve −%52 geldi.
6. **Evrenler arası skor kıyaslaması yapmayın.** BIST 100'de +2,00 ile Emtia'da +2,00 aynı şey değildir.
7. **Likidite kilidi artık sessizce düşmez.** 505-bar filtresi kapıdan sonra çalışır; DSTKF gibi kısa seriler kapı sayfasında raporlanır. Yine de bir isim kaybolursa ilk bakılacak yer filtre sırasıdır.

## Ayarlanabilir parametreler

| Parametre | Varsayılan | Alternatif |
|---|---|---|
| `VOL_BAND` (B) | 0,50 → m ∈ [0,506 ; 1,494], oran 3,0x | 0,25 → daha zayıf hacim etkisi; 0,80 → oran 9,0x, daha güçlü ayırma ama daha oynak |
| Pencere ağırlıkları | 0,40 / 0,30 / 0,20 / 0,10 | Eşit, ya da uzun vadeye kaydırma 0,15/0,25/0,30/0,30 |
| Hacim tabanı | 504 gün | 378 gün — daha duyarlı, daha gürültülü |
| Kapı: kilit eşiği | ≥3 gün / 10 gün | ≥2 daha hassas |
| Kapı: hacim eşiği | 5g/60g < 0,25 | 0,15 daha dar |

**B parametresinin etkisi** (ayırma gücü = [(Q1−Q2)+(Q4−Q3)] / std):

| B | Oran | BIST 100 | Nasdaq 100 |
|---|---|---|---|
| 0,00 | 1,0x | 0,039 | 0,551 |
| 0,25 | 1,7x | 0,363 | 0,902 |
| **0,50** | **3,0x** | **0,665** | **1,199** |
| 0,80 | 9,0x | 0,985 | 1,485 |

Optimum nokta backtest olmadan belirlenemez. Parametre değiştiren biri, değiştirdiğini **rapor içinde** belirtmeli; aksi halde iki koşu karşılaştırılamaz.

## Bilinen sınırlar

- **Uluslararası 10 yıllık getiriler** günlük seri olarak ücretsiz kaynaklardan çekilemiyor. İngiltere, Almanya, Japonya, Kanada ve Çin tahvil ETF'leriyle temsil ediliyor ve **ETF fiyatı getiriyle ters yönlüdür**. Türkiye için likit ETF vekili yok. Çözüm: TCMB EVDS + FRED API anahtarları veya Bloomberg'den GT{PARA}10Y CSV export'u.
- **BIST 100 evreni** resmi bileşen listesi değil, likidite ile proxy'leniyor. BIST 30 ise resmi listedir ve çeyrek revizyonlarla (Oca/Nis/Tem/Eki) elle güncellenir — 01.10.2026'da TRMET giriyor, DSTKF çıkıyor.
- **Risk düzeltmesi yok.** %70 oynaklıktaki bir isimde +%20 ile %25 oynaklıktaki bir isimde +%20 aynı sinyal sayılıyor. Getiriyi `oynaklık × √k` ile bölmek sıradaki doğal adım.
- **İşaret uyuşmazlığı ~%2.** Pencere başına çarpım her pencerede işareti korur, ama bileşik skor dört pencerenin ağırlıklı toplamı olduğu için bileşik MOM'un işareti bileşik ZRET'ten farklı çıkabilir. Yalnızca ZRET ≈ 0 olduğunda görülür ve ekonomik anlamı vardır: düşüşler teyitli, yükselişler teyitsiz. Kesin garanti isteniyorsa çarpan bileşik düzeyde uygulanır (`MOM = ZRET × m(ZVOL)`), ama pencere içi getiri-hacim eşleşmesi kaybolur.
- Bu **kesitsel** bir çalışmadır, zaman serisi backtest'i değildir.

## Sürüm geçmişi

| Sürüm | Değişiklik | Gerekçe |
|---|---|---|
| v1 | Basit getiri → winsorize → z-skor; MOM = z×z; sıralama MOM_ADJ = z × e^(z/2) | İlk kurulum |
| v2 | Sıra → normal skor (van der Waerden); winsorize kaldırıldı; likidite kapısı eklendi | JB testi 8 kombinasyonun 7'sinde normalliği reddetti; DSTKF taban kilidinde "ilgisiz düşüş" olarak sınıflanıyordu |
| **v3** | **Hacim çarpanı m(z) = (1−B) + 2B·Φ(z), daima pozitif; MOM_ADJ kaldırıldı; kapı 505-bar filtresinden önce çalışıyor** | **Hacim yön taşımamalı; işaret tuzağı yapısal olarak çözüldü, tek metriğe indi** |

## Doğrulama — 25 Eylül 2026 referans koşusu (v3)

**Evren büyüklükleri:** Emtia 21 · Tahvil 10 · Nasdaq 100 96 · BIST 100 100 · BIST 30 30 · toplam 257

**Tüm evrenlerde en yüksek 5 MOM:**

| # | Enstrüman | Evren | MOM | z(getiri) | m (1a) | Kadran |
|---|---|---|---|---|---|---|
| 1 | ENERY | BIST 100 | +2,46 | +1,95 | 1,35 | Q1 |
| 2 | TUPRS | BIST 30 | +2,27 | +2,00 | 1,15 | Q1 |
| 3 | Çin devlet ETF | Tahvil / faiz | +2,19 | +1,55 | 1,41 | Q1 |
| 4 | TUPRS | BIST 100 | +2,05 | +1,83 | 1,12 | Q1 |
| 5 | TKFEN | BIST 100 | +2,04 | +2,28 | **0,91** | **Q2** |

**Evren liderleri ve en zayıfları:**

| Evren | En iyi | En zayıf |
|---|---|---|
| Emtia | Yulaf +1,18 | Domuz −1,97 |
| Tahvil / faiz | Çin devlet ETF +2,19 | ABD 30Y getiri −1,55 |
| Nasdaq 100 | META +1,90 | INTU −2,09 |
| BIST 100 | ENERY +2,46 | DAPGM −2,01 |
| BIST 30 | TUPRS +2,27 | SASA −1,76 |

**Likidite kapısı:** BIST 100'de 13 isim (KTLEV, TERA, PASEU, SELEC, ODINE, IEYHO, MIATK, LIDER, KUYAS, RALYH, MAGEN, GRTHO, BSOKE), BIST 30'da 1 isim (DSTKF, 7 kilitli gün, 5g/60g hacim 0,00).

**Kadran dağılımı:**

| Evren | Q1 | Q2 | Q3 | Q4 | Kapı | Hacimsiz |
|---|---|---|---|---|---|---|
| Emtia | 5 | 6 | 3 | 5 | 0 | 2 |
| Tahvil / faiz | 2 | 2 | 1 | 2 | 0 | 3 |
| Nasdaq 100 | 22 | 26 | 27 | 21 | 0 | 0 |
| BIST 100 | 22 | 34 | 20 | 11 | 13 | 0 |
| BIST 30 | 4 | 10 | 11 | 4 | 1 | 0 |

**Kontrol noktaları:**
- Çarpan: min 0,506 · max 1,494 · **ortalama 1,005** · medyan 1,000 (tasarım gereği 1,000'e çok yakın)
- `zvol_12a` standart sapması 0,92 – 0,99 (≈1,0)
- Emtiada likidite kapısına takılan **0** isim (PL=F ve PA=F yanlış pozitif vermedi)
- MOM/ZRET işaret uyuşmazlığı **%2,1** (5/243) — sınırın altında
- Genel Q1 payı %21
- **TKFEN vakası formülün doğru çalıştığının testidir:** getiri z-skoru +2,28 ile evrenin en yükseği, ama çarpan 0,91 olduğu için skoru 2,04'e iniyor ve Q2'de kalıyor. Eski formülde (z×z) bu isim daha da düşük, negatif MOM alıyordu.

**Önceki koşuya (18.09.2026) göre:** Q1 payı %23 → %21 · 60 satır kadran değiştirdi · ilk beşten düşenler: Kakao, Benzin RBOB, LITE, MU, MRVL, SELEC, DMRGD · kapıya yeni takılan: DSTKF · olay işaretli: META (1a +%30,6 / 12a −%0,8).

## Kod dosyaları

| Dosya | İşlev |
|---|---|
| `run.py` | Orkestrasyon: fetch → compute → xl → pdf, ardından `out/summary.txt` ve `state/last.csv` güncellemesi |
| `src/fetch.py` | Evren tanımları (`COM`, `BOND`, `B30`, `BROAD`) + Yahoo veri çekme → `raw.pkl` |
| `src/compute.py` | Hacim kalite testi, ETF vekil bağlama, sıra normalizasyonu, hacim çarpanı (`VOL_BAND`), likidite kapısı, kadran ataması, önceki koşu karşılaştırması → `res.pkl` |
| `src/xl.py` | Excel üretimi (7 sekme, 33 kolon) |
| `src/pdf.py` | Grafikler, PDF üretimi |
| `send.py` | Ekip maili (`preview` = yalnızca sana, `team` = ekibe) |
| `.github/workflows/` | `build.yml` (üretim) · `send.yml` (onaylı gönderim) |

Yeni tarihle çalıştırmak için: `rm -f raw.pkl res.pkl` → `python3 run.py`. Tam koşu: `python3 send.py preview`.

**Çıktı dosyaları** `out/` altına yazılır: `Momentum_Calismasi_v3_YYYY-AA-GG.pdf`, `.xlsx`, `summary.txt`.

**Karşılaştırma tabanı** `state/last.csv` (git'e düşmez) ve şifreli `state/last.csv.enc` (commit'lenir) — sonraki koşunun kadran değişimlerini hesaplamak için gereklidir.

**Tekrarlanabilirlik notu:** Yahoo'nun sürekli vadeli serileri geriye dönük düzeltilebiliyor. Farklı bir tarihte çekilen 3 yıllık seri, aynı geçmiş günler için birebir aynı olmayabilir. Tam tekrarlanabilirlik gerekiyorsa `raw.pkl` dosyasını rapor çıktılarıyla birlikte arşivleyin.
