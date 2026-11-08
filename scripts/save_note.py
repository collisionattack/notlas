#!/usr/bin/env python3
"""Bir ders notunu (Markdown) not deposuna kaydeder, PDF'ini üretir ve dizinleri günceller.

Kullanım:
    python3 save_note.py not.md [--kok ders-notlari] [--kurs-aciklama "..."] [--pdf-yok]

Oluşan yapı (agent'lar Markdown'ı, insanlar PDF'i okur):

    ders-notlari/
    ├── README.md                       # Tüm kurslar
    └── <kurs-slug>/
        ├── INDEX.md                    # Kurs dizini: ders → özet, kavramlar, dosya yolu
        ├── kurs.json                   # Makinece okunur kurs ve ders listesi
        ├── notlar/<NN-bolum>/<NN-ders>.md
        └── pdf/<NN-bolum>/<NN-ders>.pdf
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pdf  # noqa: E402

YAN = {"Özet", "Önemli Kavramlar", "Dikkat Edilmesi Gerekenler", "Tekrar Soruları"}


def slug(text: str, max_len: int = 60) -> str:
    s = build_pdf.slugify(text or "")
    return s[:max_len].rstrip("-") or "adsiz"


def numara_ve_ad(text: str, onek: str):
    m = re.match(rf"^\s*(?:{onek})?\s*(\d+)\s*[-–—:.]\s*(.+)$", text or "", re.I)
    return (int(m.group(1)), m.group(2).strip()) if m else (None, (text or "").strip())


def ozet_cikar(md: str) -> str:
    m = re.search(r"^##\s+Özet\s*\n+(.+?)(?:\n\s*\n|\n#)", md, re.S | re.M)
    if not m:
        return ""
    t = re.sub(r"[`*_]", "", " ".join(m.group(1).split()))
    return t if len(t) <= 260 else t[:257].rsplit(" ", 1)[0] + "…"


def kavramlar_cikar(md: str):
    m = re.search(r"^##\s+Önemli Kavramlar\s*\n(.*?)(?=^#{1,2}\s|\Z)", md, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("-: ") and cells[0] != "Kavram":
            out.append(re.sub(r"[`*_]", "", cells[0]))
    return out


def basliklar_cikar(md: str):
    return [h.strip() for h in re.findall(r"^##\s+(.+)$", md, re.M) if h.strip() not in YAN]


def kaydet(not_yolu: Path, kok: Path, kurs_aciklama: str = "", pdf: bool = True, tema: str = "akademik"):
    metin = not_yolu.read_text(encoding="utf-8")
    meta, govde = build_pdf.split_front_matter(metin)
    kurs = meta.get("kurs") or sys.exit("Notun YAML ön bloğunda 'kurs' alanı zorunlu.")
    b_no, b_ad = numara_ve_ad(meta.get("bolum", ""), "Bölüm|Section")
    first_h1 = re.search(r"^#\s+(.+)$", govde, re.M)
    d_no, d_ad = numara_ve_ad(meta.get("ders") or (first_h1.group(1) if first_h1 else not_yolu.stem), "Ders|Lecture")

    kurs_dir = kok / slug(kurs)
    bolum_dir = f"{b_no:02d}-{slug(b_ad)}" if b_no is not None else (slug(b_ad) if b_ad else "genel")
    ders_dosya = f"{d_no:03d}-{slug(d_ad)}" if d_no is not None else slug(d_ad)

    md_hedef = kurs_dir / "notlar" / bolum_dir / f"{ders_dosya}.md"
    pdf_hedef = kurs_dir / "pdf" / bolum_dir / f"{ders_dosya}.pdf"
    md_hedef.parent.mkdir(parents=True, exist_ok=True)
    md_hedef.write_text(metin if metin.endswith("\n") else metin + "\n", encoding="utf-8")

    if pdf:
        pdf_hedef.parent.mkdir(parents=True, exist_ok=True)
        html_str = build_pdf.render_html(govde, meta, toc=True, tema=tema)
        if not (build_pdf.pdf_weasyprint(html_str, pdf_hedef) or build_pdf.pdf_chrome(html_str, pdf_hedef)):
            print("UYARI: PDF motoru bulunamadı, yalnızca Markdown kaydedildi.", file=sys.stderr)

    # kurs.json güncelle
    kj = kurs_dir / "kurs.json"
    veri = json.loads(kj.read_text(encoding="utf-8")) if kj.exists() else {"kurs": kurs, "aciklama": "", "dersler": []}
    veri["kurs"] = kurs
    if kurs_aciklama:
        veri["aciklama"] = kurs_aciklama
    kayit = {
        "bolum_no": b_no, "bolum": b_ad, "ders_no": d_no, "ders": d_ad,
        "ozet": ozet_cikar(govde), "konular": basliklar_cikar(govde), "kavramlar": kavramlar_cikar(govde),
        "md": md_hedef.relative_to(kurs_dir).as_posix(),
        "pdf": pdf_hedef.relative_to(kurs_dir).as_posix() if pdf_hedef.exists() else None,
        "guncelleme": dt.date.today().isoformat(),
    }
    veri["dersler"] = [d for d in veri["dersler"] if d["md"] != kayit["md"]] + [kayit]
    veri["dersler"].sort(key=lambda d: (d["bolum_no"] if d["bolum_no"] is not None else 9999,
                                        d["ders_no"] if d["ders_no"] is not None else 9999, d["ders"]))
    kj.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    yaz_kurs_index(kurs_dir, veri)
    yaz_kok_readme(kok)
    return md_hedef, pdf_hedef if pdf_hedef.exists() else None


def yaz_kurs_index(kurs_dir: Path, veri: dict):
    s = [f"# {veri['kurs']} — Ders Notları", ""]
    if veri.get("aciklama"):
        s += [f"> {veri['aciklama']}", ""]
    s += ["Bu klasör, kursun ders notlarını bilgi kaynağı olarak tutar. Agent'lar için kaynak "
          "Markdown dosyalarıdır (`notlar/`); `pdf/` aynı içeriğin okunabilir kopyasıdır. "
          "Bir konuyu ararken önce aşağıdaki kavram ve konu listelerine bakın, sonra ilgili notu açın.", "",
          f"Toplam {len(veri['dersler'])} ders · Makinece okunur liste: `kurs.json`", ""]
    son_bolum = object()
    for d in veri["dersler"]:
        bolum_baslik = (f"Bölüm {d['bolum_no']} · {d['bolum']}" if d["bolum_no"] is not None
                        else (d["bolum"] or "Genel"))
        if bolum_baslik != son_bolum:
            s += [f"## {bolum_baslik}", ""]
            son_bolum = bolum_baslik
        no = f"{d['ders_no']} · " if d["ders_no"] is not None else ""
        s.append(f"### {no}{d['ders']}")
        s.append("")
        if d["ozet"]:
            s += [d["ozet"], ""]
        if d["konular"]:
            s.append("- **Konular:** " + "; ".join(d["konular"]))
        if d["kavramlar"]:
            s.append("- **Kavramlar:** " + ", ".join(d["kavramlar"]))
        dosyalar = f"[Markdown]({d['md']})" + (f" · [PDF]({d['pdf']})" if d.get("pdf") else "")
        s += [f"- **Dosya:** {dosyalar}", ""]
    (kurs_dir / "INDEX.md").write_text("\n".join(s), encoding="utf-8")


def yaz_kok_readme(kok: Path):
    satirlar = ["# Ders Notları", "",
                "Kişisel kurs notları deposu. Her kurs kendi klasöründedir; kursun `INDEX.md` dosyası "
                "derslerin özetini, konularını ve kavramlarını listeler.", "",
                "| Kurs | Ders sayısı | Dizin |", "|---|---|---|"]
    for kj in sorted(kok.glob("*/kurs.json")):
        v = json.loads(kj.read_text(encoding="utf-8"))
        satirlar.append(f"| {v['kurs']} | {len(v['dersler'])} | [{kj.parent.name}/INDEX.md]({kj.parent.name}/INDEX.md) |")
    (kok / "README.md").write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Ders notunu not deposuna kaydet (MD + PDF)")
    ap.add_argument("not_dosyasi", nargs="+")
    ap.add_argument("--kok", default="ders-notlari", help="Not deposunun kök klasörü (varsayılan: ./ders-notlari)")
    ap.add_argument("--kurs-aciklama", default="", help="Kurs açıklaması (INDEX.md ve kurs.json'a yazılır)")
    ap.add_argument("--pdf-yok", action="store_true", help="Yalnızca Markdown kaydet")
    a = ap.parse_args()
    kok = Path(a.kok)
    for n in a.not_dosyasi:
        md, pdf = kaydet(Path(n), kok, a.kurs_aciklama, pdf=not a.pdf_yok)
        print(f"Kaydedildi: {md}" + (f"\n            {pdf}" if pdf else ""))
    print(f"Dizin güncellendi: {kok / 'README.md'}")


if __name__ == "__main__":
    main()
