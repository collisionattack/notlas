# udemy-ders-notu

Udemy (veya herhangi bir video kurs) ders transkriptlerini Türkçe, yapılandırılmış ders notlarına dönüştüren ve PDF olarak kaydeden bir **Claude skill**'i.

Sen transkripti, kurs adını ve açıklamasını verirsin; Claude dersi yeniden anlatan bir not yazar ve kapaklı, içindekilerli bir PDF + düzenlenebilir Markdown dosyası üretir.

## Kurulum

**Claude.ai / Claude uygulaması:** Bu klasörü ZIP olarak sıkıştır (ya da Releases'teki `udemy-ders-notu.zip`'i indir) ve Claude ayarlarındaki *Skills* bölümünden yükle.

**Claude Code:**
```bash
git clone https://github.com/<kullanici>/udemy-ders-notu ~/.claude/skills/udemy-ders-notu
```

## Kullanım

Yeni bir sohbette:

> Kurs: Docker ve Kubernetes
> Açıklama: ...
> Ders: Bölüm 2 / Ders 7 - Docker Volume'ları
> Transkript: (metni yapıştır veya .vtt/.txt dosyasını ekle)
>
> Bunu ders notu yap.

ya da `/udemy-ders-notu` yaz.

## Yapı

```
SKILL.md                    # Claude'a talimatlar: not formatı, yazım kuralları, akış
scripts/clean_transcript.py # VTT/SRT → düz metin (zaman damgası ve tekrarları temizler)
scripts/build_pdf.py        # Markdown → PDF (WeasyPrint, yoksa headless Chrome)
assets/style.css            # PDF teması: shadcn/ui (zinc) görünümü, A4, kapak, içindekiler
assets/fonts/               # Inter + Geist Mono (OFL lisanslı, Türkçe karakter destekli)
examples/                   # Örnek transkript, not ve PDF
```

Betikler tek başına da çalışır:
```bash
pip install weasyprint markdown pygments
python3 scripts/clean_transcript.py ders.vtt > ders.txt
python3 scripts/build_pdf.py not.md -o not.pdf
```

## Not

Kişisel kullanım içindir. Üretilen notlar kursun içeriğinden türetildiği için telif hakkı eğitmene aittir; paylaşmayın.
