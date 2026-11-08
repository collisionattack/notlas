---
name: udemy-ders-notu
description: Udemy (veya benzeri) bir kurs dersinin transkriptini, kurs adı ve açıklamasıyla birlikte Türkçe, yapılandırılmış bir ders notuna dönüştürür ve PDF + Markdown olarak kaydeder. Kullanıcı bir ders transkripti verip "ders notu çıkar", "notlaştır", "PDF yap" dediğinde ya da /udemy-ders-notu yazdığında kullan.
---

# Udemy Ders Notu

Kullanıcının verdiği ders transkriptini, ileride tekrar okunabilecek, kendi başına anlaşılır bir **ders notuna** dönüştür ve PDF olarak kaydet.

## 1. Girdileri topla

Beklenen girdiler (sohbete yapıştırılmış metin ya da ekli .txt/.vtt/.srt dosyası olabilir):

| Girdi | Zorunlu | Not |
|---|---|---|
| Kurs adı | Evet | |
| Kurs açıklaması | Hayır | Bağlam için kullan, nota kopyalama |
| Bölüm adı / ders adı | Hayır | Yoksa transkriptten kısa bir başlık türet |
| Transkript | Evet | Bir veya birden fazla ders olabilir |

Transkript yoksa iste. Diğer eksikler için soru sorma; makul bir varsayım yap ve devam et.

Transkript VTT/SRT ise önce temizle:
`python3 scripts/clean_transcript.py <girdi> > temiz.txt`

## 2. Notu yaz (Markdown)

Notu **Türkçe** yaz. Kaynak İngilizce ise çevir; teknik terimin ilk geçtiği yerde orijinalini parantez içinde ver: "bağımlılık enjeksiyonu (dependency injection)". Kod, komut, sınıf/fonksiyon adları çevrilmez.

Temel ilke: **transkripti özetleme, dersi yeniden anlat.** Konuşma dilindeki tekrarları, "şimdi şuraya tıklayalım", "bir sonraki derste görüşürüz" gibi dolgu cümlelerini at; anlatılan her kavramı, adımı, örneği ve uyarıyı koru. Eğitmen kod yazıyorsa kodu kod bloğu olarak yeniden kur. Transkriptte olmayan bilgi ekleme; kısa bir açıklama gerçekten anlamaya yardım ediyorsa `> 💡 Ek not:` olarak işaretle.

Dosya şu yapıyla başlamalı (en üstteki YAML bloğu kapak sayfasını oluşturur):

```markdown
---
kurs: "Kurs Adı"
bolum: "Bölüm 3 - Bölüm Adı"
ders: "Ders 12 - Ders Adı"
---

# Ders Adı

## Özet
2-4 cümle: bu derste ne öğreniliyor, neden önemli.

## <Konu başlığı 1>
Açıklayıcı paragraflar, gerektiğinde madde işaretleri, tablolar, kod blokları.

### <Alt başlık>
...

## Önemli Kavramlar
| Kavram | Açıklama |
|---|---|

## Dikkat Edilmesi Gerekenler
> ⚠️ Eğitmenin vurguladığı hatalar, tuzaklar, ipuçları.

## Tekrar Soruları
1. ... (3-5 soru; cevapları notun içinde bulunabilir olmalı)
```

Kurallar:
- Başlıkları transkriptteki konu akışına göre kendin belirle; şablondaki "Konu başlığı" yer tutucudur.
- Derste karşılığı olmayan bölümü (ör. hiç uyarı yoksa "Dikkat Edilmesi Gerekenler") atla.
- Kod bloklarına dil etiketi ver (```python, ```bash ...).
- Birden fazla ders verildiyse her dersi `#` başlığıyla ayrı yaz; YAML'daki `ders` alanını boş bırak veya bölüm adını kullan.

## 3. PDF'e çevir ve kaydet

Dosya adı: `<kurs-kisa-adi>_<ders-no>_<ders-adi>.md` (Türkçe karakterleri ve boşlukları sadeleştir).

```bash
pip install --break-system-packages -q weasyprint markdown pygments 2>/dev/null
python3 scripts/build_pdf.py not.md            # not.pdf üretir
python3 scripts/build_pdf.py not.md -o cikti.pdf
```

Betik WeasyPrint yoksa headless Chrome'a geçer. İkisi de yoksa hatayı kullanıcıya bildir ve en azından Markdown dosyasını teslim et.

PDF'i üretip ilk sayfaları bir kez görüntüleyerek kontrol et (Türkçe karakterler, kod blokları, tablo taşması). Sonra **hem .pdf hem .md dosyasını** kullanıcıya teslim et. Kullanıcı bilgisayarındaki belirli bir klasörü bağladıysa dosyaları oraya da yaz.

Yanıtta notun içeriğini sohbete tekrar yazma; tek cümleyle neyin üretildiğini söyle.
