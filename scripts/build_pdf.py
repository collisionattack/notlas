#!/usr/bin/env python3
"""Ders notu Markdown dosyasını kapaklı, içindekilerli bir PDF'e çevirir.

Kullanım:
    python3 build_pdf.py not.md [-o cikti.pdf] [--no-toc] [--html]

Markdown dosyası isteğe bağlı bir YAML ön bloğuyla başlayabilir:
    ---
    kurs: "Kurs Adı"
    bolum: "Bölüm 3 - ..."
    ders: "Ders 12 - ..."
    ---
PDF motoru: WeasyPrint (tercih edilen), yoksa headless Chrome/Chromium.
"""
import argparse
import datetime as dt
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import markdown
    from pygments.formatters import HtmlFormatter
except ImportError:
    sys.exit("Eksik paket: pip install markdown pygments weasyprint")

HERE = Path(__file__).resolve().parent
CSS_PATH = HERE.parent / "assets" / "style.css"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def split_front_matter(text: str):
    meta = {}
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"').strip("'")
        text = text[m.end():]
    return meta, text


def render_html(md_text: str, meta: dict, toc: bool) -> str:
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "codehilite"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "codehilite"},
            "toc": {"toc_depth": "1-2", "permalink": False},
        },
    )
    body = md.convert(md_text)

    first_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    ders = meta.get("ders") or (re.sub("<[^>]+>", "", first_h1.group(1)) if first_h1 else "Ders Notu")
    kurs = meta.get("kurs", "")
    bolum = meta.get("bolum", "")
    bugun = dt.date.today()
    tarih = f"{bugun.day} {AYLAR[bugun.month - 1]} {bugun.year}"

    e = html.escape
    cover = (
        '<section class="cover">'
        + (f'<div class="kurs">{e(kurs)}</div>' if kurs else "")
        + (f'<div class="bolum">{e(bolum)}</div>' if bolum else "")
        + f'<div class="ders">{e(ders)}</div>'
        + f'<div class="tarih">Ders notu · {tarih}</div></section>'
    )
    toc_html = ""
    # Birden fazla başlık varsa içindekiler ekle
    if toc and body.count("<h2") + body.count("<h1") >= 4:
        toc_html = f'<section class="toc"><h2>İçindekiler</h2>{md.toc}</section>'

    pyg_css = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
    css = CSS_PATH.read_text(encoding="utf-8")
    return (
        '<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        f"<title>{e(ders)}</title><style>{css}\n{pyg_css}\n"
        ".codehilite{background:#f7f8fa}</style></head><body>"
        f'{cover}{toc_html}<main class="content">{body}</main></body></html>'
    )


def pdf_weasyprint(html_str: str, out: Path) -> bool:
    try:
        from weasyprint import HTML
    except Exception:
        return False
    HTML(string=html_str, base_url=str(HERE)).write_pdf(str(out))
    return True


def pdf_chrome(html_str: str, out: Path) -> bool:
    exe = next((shutil.which(n) for n in
                ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]
                if shutil.which(n)), None)
    if not exe:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        tmp = f.name
    cmd = [exe, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
           f"--print-to-pdf={out}", f"file://{tmp}"]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    return out.exists()


def main():
    ap = argparse.ArgumentParser(description="Ders notu Markdown → PDF")
    ap.add_argument("markdown_file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--no-toc", action="store_true", help="İçindekiler sayfası ekleme")
    ap.add_argument("--html", action="store_true", help="Ara HTML dosyasını da kaydet")
    a = ap.parse_args()

    src = Path(a.markdown_file)
    out = Path(a.output) if a.output else src.with_suffix(".pdf")
    meta, md_text = split_front_matter(src.read_text(encoding="utf-8"))
    html_str = render_html(md_text, meta, toc=not a.no_toc)

    if a.html:
        out.with_suffix(".html").write_text(html_str, encoding="utf-8")

    if pdf_weasyprint(html_str, out):
        engine = "WeasyPrint"
    elif pdf_chrome(html_str, out):
        engine = "Chrome"
    else:
        sys.exit("PDF motoru bulunamadı: `pip install weasyprint` kurun veya Chrome yükleyin.")
    print(f"PDF oluşturuldu ({engine}): {out}")


if __name__ == "__main__":
    main()
