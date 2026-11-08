# Notlas — çalışma talimatları

Bu klasör hem **Notlas skill'inin kaynak kodu** hem de kullanıcının **kişisel ders notu deposu**dur.

## Ders notu oluşturma

Kullanıcı bir ders transkripti verdiğinde (sohbete yapıştırarak veya `transkriptler/` klasörüne koyarak), bu klasördeki `SKILL.md` talimatlarını izle:

1. Transkript `transkriptler/` içindeyse oradan oku; VTT/SRT ise `scripts/clean_transcript.py` ile temizle.
2. Notu `SKILL.md`'deki formatta yaz. Geçici dosyayı `transkriptler/` altına koyabilirsin.
3. Şu komutla kaydet. Kök klasör her zaman `ders-notlari/` olmalı:
   ```bash
   python3 scripts/save_note.py <not>.md --kok ders-notlari [--kurs-aciklama "..."]
   ```
4. Kaydettikten sonra üretilen PDF'i bir kez görsel olarak kontrol et.

## Klasörler

| Klasör | İçerik | Git |
|---|---|---|
| `ders-notlari/` | Kalıcı not deposu: `<kurs>/INDEX.md`, `kurs.json`, `notlar/` (MD), `pdf/` | Hayır (kişisel, telifli içerikten türetilmiş) |
| `transkriptler/` | Gelen ham transkriptler ve geçici not taslakları | Hayır |
| `scripts/`, `assets/`, `SKILL.md` | Skill kaynak kodu | Evet |
| `examples/` | Örnek notlar ve örnek depo | Evet |

## Agent'lara bilgi kaynağı olarak verme

Başka bir projede bir kursu kaynak olarak kullanmak için agent'a `ders-notlari/<kurs-slug>/INDEX.md` dosyasını göster. Agent ilgili dersi dizinden bulur ve `notlar/` altındaki Markdown dosyasını okur. PDF'ler insanlar içindir.

## Skill'i geliştirme

- PDF teması: `assets/themes/akademik.css`. Değişiklikten sonra `examples/` altındaki notları `save_note.py --kok examples/ders-notlari` ile yeniden üretip görsel kontrol yap.
- Skill paketini Claude'a yüklemek için klasörü ZIP'le; `ders-notlari/`, `transkriptler/` ve `.git/` hariç tutulmalı:
  ```bash
  cd .. && zip -qr notlas.zip notlas -x 'notlas/.git/*' 'notlas/ders-notlari/*' 'notlas/transkriptler/*' '*/__pycache__/*'
  ```
