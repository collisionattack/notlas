# Notlas

*not + atlas*: Udemy (veya herhangi bir video kurs) ders transkriptlerini Türkçe, yapılandırılmış ders notlarına dönüştüren bir **Claude skill**'i. Notlar kalıcı bir **not deposuna** hem Markdown hem PDF olarak kaydedilir. Markdown dosyaları, geliştirme yaparken agent'lara bilgi kaynağı olarak verilmek üzere tasarlanmıştır.

## Nasıl çalışır

1. Sen transkripti, kurs adını, açıklamasını ve ders/bölüm bilgisini verirsin.
2. Claude dersi yeniden anlatan bir Markdown not yazar (özet, konular, kod, kavram tablosu, uyarılar, tekrar soruları).
3. `save_note.py` notu depoya yerleştirir, akademik temalı PDF'i üretir ve kurs dizinini günceller.

## Not deposu yapısı

```
ders-notlari/
├── README.md                           # Tüm kurslar
└── <kurs-slug>/
    ├── INDEX.md                        # Her ders: özet, konular, kavramlar, dosya yolları
    ├── kurs.json                       # Aynı bilgi, makinece okunur
    ├── notlar/<NN-bolum>/<NNN-ders>.md # Agent'ların okuyacağı kaynak
    └── pdf/<NN-bolum>/<NNN-ders>.pdf   # Okunabilir kopya
```

Bir agent'a kursu bilgi kaynağı olarak vermek için `<kurs-slug>/INDEX.md` dosyasını göstermen yeterli. Agent dizinden ilgili dersi bulur ve yalnızca o Markdown dosyasını açar. Örnek depo için `examples/ders-notlari/` klasörüne bak.

## Proje klasörü olarak kullanım

Depoyu klonlayıp Claude Code veya Claude masaüstü uygulamasında bu klasörü aç. `CLAUDE.md` iş akışını tanımlar:

```
notlas/
├── CLAUDE.md          # Claude'a çalışma talimatları
├── SKILL.md           # Not formatı ve yazım kuralları
├── transkriptler/     # Ham transkriptleri buraya bırak (git dışı)
└── ders-notlari/      # Kalıcı not deposu (git dışı)
```

## Kurulum

**Claude uygulaması:** Bu klasörü ZIP olarak sıkıştır (veya Releases'teki `notlas.zip`'i indir). **Customize → Skills → + → Create skill → Upload a skill** yoluyla yükle. Settings → Capabilities altında kod çalıştırma ve dosya oluşturma açık olmalı.

**Claude Code:**
```bash
git clone https://github.com/<kullanici>/notlas ~/.claude/skills/notlas
```

## Kullanım

> Kurs: Docker ve Kubernetes
> Açıklama: ...
> Ders: Bölüm 2 / Ders 7 - Docker Volume'ları
> Transkript: (metni yapıştır veya .vtt/.txt dosyasını ekle)
>
> Bunu ders notu yap.

ya da `/notlas` yaz.

## Betikler

```bash
pip install weasyprint markdown pygments
python3 scripts/clean_transcript.py ders.vtt > ders.txt                 # VTT/SRT → düz metin
python3 scripts/save_note.py not.md --kok ders-notlari \
        --kurs-aciklama "..."                                           # depoya kaydet (MD + PDF + dizin)
python3 scripts/build_pdf.py not.md -o not.pdf                          # yalnızca PDF
```

## Dosyalar

```
CLAUDE.md                   # Proje klasörü iş akışı
SKILL.md                    # Claude'a talimatlar: not formatı, yazım kuralları, kayıt akışı
scripts/clean_transcript.py # Zaman damgası ve tekrar eden satırları temizler
scripts/save_note.py        # Not deposuna kaydeder, INDEX.md / kurs.json / README.md üretir
scripts/build_pdf.py        # Markdown → PDF (WeasyPrint, yoksa headless Chrome)
assets/themes/akademik.css  # Tufte tarzı tema: fildişi kâğıt, EB Garamond, kenar notları
assets/fonts/               # EB Garamond, Inter, JetBrains Mono (OFL, Türkçe karakterli)
examples/                   # Örnek transkript, notlar ve örnek not deposu
```

## Not

Kişisel kullanım içindir. Üretilen notlar kursun içeriğinden türetildiği için telif hakkı eğitmene aittir; paylaşmayın.
