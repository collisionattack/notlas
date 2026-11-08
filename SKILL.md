---
name: notlas
description: Notlas — Udemy (veya benzeri) bir kurs dersinin transkriptini, kurs adı ve açıklamasıyla birlikte Türkçe, yapılandırılmış bir ders notuna dönüştürür; notu kalıcı bir not deposuna Markdown + PDF olarak kaydeder ve kurs dizinini (INDEX.md) günceller. Kullanıcı bir ders transkripti verip "ders notu çıkar", "notlaştır", "PDF yap" dediğinde ya da /notlas yazdığında kullan.
---

# Notlas — Ders Notu Derleyici

Kullanıcının verdiği ders transkriptini, ileride hem kendisinin hem de geliştirme yaparken kullanacağı agent'ların bilgi kaynağı olarak okuyabileceği bir **ders notuna** dönüştür ve not deposuna kaydet.

## 1. Girdileri topla

Beklenen girdiler (sohbete yapıştırılmış metin ya da ekli .txt/.vtt/.srt dosyası olabilir):

| Girdi | Zorunlu | Not |
|---|---|---|
| Kurs adı | Evet | Klasör adı buradan türetilir; aynı kurs için her seferinde aynı adı kullan |
| Kurs açıklaması | Hayır | `--kurs-aciklama` ile kurs dizinine yazılır; nota kopyalama |
| Bölüm ve ders adı/numarası | Hayır | "Bölüm 3 - Ad", "Ders 14 - Ad" biçiminde; numaralar dosya sırasını belirler |
| Transkript | Evet | Bir veya birden fazla ders olabilir |

Transkript yoksa iste. Diğer eksikler için soru sorma; makul bir varsayım yap ve devam et.

Kurs daha önce kaydedildiyse (`<kök>/<kurs-slug>/kurs.json` varsa) kurs adını oradaki haliyle aynen kullan ki notlar aynı klasöre düşsün.

Transkript VTT/SRT ise önce temizle:
`python3 scripts/clean_transcript.py <girdi> > temiz.txt`

## 2. Notu yaz (Markdown)

Markdown dosyası **asıl kaynaktır**: agent'lar bunu okuyacak, PDF ondan üretilecek. Bu yüzden içerik kendi başına anlaşılır, aranabilir ve tutarlı yapıda olmalı.

Notu **Türkçe** yaz. Kaynak İngilizce ise çevir; teknik terimin ilk geçtiği yerde orijinalini parantez içinde ver: "bağımlılık enjeksiyonu (dependency injection)". Kod, komut, sınıf/fonksiyon adları, API ve paket adları çevrilmez (agent'lar bunlarla arama yapar).

Temel ilke: **transkripti özetleme, dersi yeniden anlat.** Konuşma dilindeki tekrarları, "şimdi şuraya tıklayalım", "bir sonraki derste görüşürüz" gibi dolgu cümlelerini at; anlatılan her kavramı, adımı, örneği, komutu ve uyarıyı koru. Eğitmen kod yazıyorsa kodu çalışır haliyle kod bloğu olarak yeniden kur. Transkriptte olmayan bilgi ekleme; kısa bir açıklama gerçekten anlamaya yardım ediyorsa `> 💡 Ek not:` olarak işaretle.

Dosya şu yapıyla başlamalı (YAML bloğu kapağı ve depo konumunu belirler):

```markdown
---
kurs: "Kurs Adı"
bolum: "Bölüm 3 - Bölüm Adı"
ders: "Ders 12 - Ders Adı"
---

# Ders Adı

## Özet
2-4 cümle: bu derste ne öğreniliyor, neden önemli. (Kurs dizinine otomatik aktarılır.)

## <Konu başlığı 1>
Açıklayıcı paragraflar, gerektiğinde madde işaretleri, tablolar, kod blokları.

### <Alt başlık>
...

## Önemli Kavramlar
| Kavram | Açıklama |
|---|---|
(İlk sütun kurs dizinine "Kavramlar" olarak aktarılır; terimleri arama yapılabilir biçimde yaz.)

## Dikkat Edilmesi Gerekenler
> ⚠️ Eğitmenin vurguladığı hatalar, tuzaklar.

## Tekrar Soruları
1. ... (3-5 soru; cevapları notun içinde bulunabilir olmalı)
```

Kurallar:
- `##` başlıklarını transkriptteki konu akışına göre kendin belirle; bunlar dizinde "Konular" olarak listelenir, o yüzden açıklayıcı olsunlar ("Giriş" yerine "Docker Volume Türleri").
- Derste karşılığı olmayan bölümü (ör. hiç uyarı yoksa "Dikkat Edilmesi Gerekenler") atla.
- Kod bloklarına dil etiketi ver (```python, ```bash ...).
- Birden fazla ders verildiyse her ders için **ayrı bir .md dosyası** yaz; her biri kendi YAML bloğuyla.
- Uyarı işaretleri: `> ⚠️ ...` (Dikkat), `> 💡 ...` (İpucu; `> 💡 Ek not: ...` başlığı "Ek not" yapar), `> ℹ️ ...` (Not). Her uyarıyı ayrı bir satırda, aralarında boş satır bırakarak yaz. PDF'te metin içindeki uyarılar kenar notu olarak basılır; "Dikkat Edilmesi Gerekenler" altındakiler metinde kalır.

## 3. Not deposuna kaydet (MD + PDF)

```bash
pip install -q weasyprint markdown pygments 2>/dev/null \
  || pip install --break-system-packages -q weasyprint markdown pygments 2>/dev/null \
  || pip3 install --user -q weasyprint markdown pygments
python3 scripts/save_note.py not.md --kok <kök-klasör> [--kurs-aciklama "..."]
# birden fazla ders: python3 scripts/save_note.py ders14.md ders15.md --kok <kök>
```

`--kurs-aciklama`'yı kursun ilk kaydında (veya açıklama değiştiğinde) ver; sonraki kayıtlarda gerekmez.

Betik şu yapıyı oluşturur veya günceller:

```
<kök>/                                  (varsayılan: ders-notlari/)
├── README.md                           # Tüm kurslar ve ders sayıları
└── <kurs-slug>/
    ├── INDEX.md                        # Ders → özet, konular, kavramlar, dosya yolları
    ├── kurs.json                       # Aynı bilginin makinece okunur hali
    ├── notlar/<NN-bolum>/<NNN-ders>.md # Agent'ların okuyacağı kaynak
    └── pdf/<NN-bolum>/<NNN-ders>.pdf   # Akademik temalı, okunabilir kopya
```

Aynı ders yeniden kaydedilirse dosyaların üzerine yazılır ve dizindeki kaydı güncellenir.

Betikleri `python3 -I` ile çalıştırma: izole mod kullanıcı klasörüne kurulan paketleri (`pip install --user`) görmez ve PDF üretilemez. macOS'ta WeasyPrint sistem kütüphanesi ister (`brew install pango`); kurulu değilse betik otomatik olarak yüklü Chrome/Edge'e geçer.

**Kök klasör nerede olmalı:**
- Kullanıcı bir yol söylediyse onu kullan.
- Notlas proje klasöründe çalışılıyorsa (klasörde `CLAUDE.md` ve `ders-notlari/` varsa) kök her zaman o `ders-notlari/` klasörüdür.
- Claude Code'da veya kullanıcının bilgisayarında bir klasör bağlıysa: kullanıcının belirttiği not deposu; belirtmediyse çalışma dizininde `ders-notlari/`. Kullanıcının bilgisayarına yalnızca uzaktan dosya erişimi varsa, depoyu çalışma alanında üret ve değişen dosyaları (not .md, .pdf, INDEX.md, kurs.json, README.md) aynı göreli yollarla o klasöre yaz.
- Hiçbiri yoksa (bulut sohbeti): çalışma dizininde `ders-notlari/` oluştur, sonra kullanıcıya not .md ve .pdf dosyasını, ayrıca tüm depoyu tek parça indirebilmesi için `ders-notlari.zip`'i gönder.

PDF'in ilk sayfalarını bir kez görüntüleyerek kontrol et (Türkçe karakterler, kod blokları, tablolar). PDF motoru (WeasyPrint/Chrome) yoksa betik yalnızca Markdown'ı kaydeder; bunu kullanıcıya söyle.

Yanıtta notun içeriğini sohbete tekrar yazma; tek cümleyle neyin nereye kaydedildiğini söyle.
