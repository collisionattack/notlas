#!/usr/bin/env python3
"""Ders notu Markdown dosyasını shadcn/ui görünümlü, kapaklı ve içindekilerli bir PDF'e çevirir.

Kullanım:
    python3 build_pdf.py not.md [-o cikti.pdf] [-t tema] [--no-toc] [--html]

Markdown dosyası isteğe bağlı bir YAML ön bloğuyla başlayabilir:
    ---
    kurs: "Kurs Adı"
    bolum: "Bölüm 3 - ..."
    ders: "Ders 12 - ..."
    ---

Uyarı kutuları: '> ⚠️ ...' (Dikkat), '> 💡 ...' (İpucu / 'Ek not:'), '> ℹ️ ...' (Not).
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
import unicodedata
from pathlib import Path

try:
    import markdown
    from pygments.formatters import HtmlFormatter
except ImportError:
    sys.exit("Eksik paket: pip install markdown pygments weasyprint")

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
THEMES_DIR = ASSETS / "themes"
VARSAYILAN_TEMA = "akademik"
FONTS_DIR = ASSETS / "fonts"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

ICONS = {
    "warning": '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#92400e" stroke-width="2" '
               'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2 20h20L12 3z"/>'
               '<path d="M12 10v4"/><path d="M12 17.5v.01"/></svg>',
    "tip": '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#075985" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 21h4"/>'
           '<path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/></svg>',
    "note": '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#71717a" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
            '<path d="M12 11v5"/><path d="M12 7.5v.01"/></svg>',
}
MARKERS = [("⚠", "warning", "Dikkat"), ("💡", "tip", "İpucu"), ("ℹ", "note", "Not"),
           ("📝", "note", "Not"), ("✅", "tip", "İyi uygulama")]


def slugify(value, separator="-"):
    value = unicodedata.normalize("NFKD", value.translate(TR_MAP)).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(rf"[{separator}\s]+", separator, value)


def split_front_matter(text: str):
    meta = {}
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[slugify(k.strip()).replace("-", "_")] = v.strip().strip('"').strip("'")
        text = text[m.end():]
    return meta, text


def fence_languages(md_text: str):
    langs, inside = [], False
    for line in md_text.splitlines():
        m = re.match(r"^\s*(```|~~~)\s*([\w+#.-]*)", line)
        if m:
            if not inside:
                langs.append(m.group(2) or "")
            inside = not inside
    return langs


def wrap_code_blocks(body: str, langs):
    blocks = re.findall(r'<div class="codehilite">', body)
    use_titles = len(blocks) == len(langs)
    it = iter(langs)

    def repl(m):
        lang = next(it, "") if use_titles else ""
        title = f'<div class="code-title">{html.escape(lang)}</div>' if lang else ""
        return f'<div class="code-block">{title}{m.group(0)}'

    body = re.sub(r'<div class="codehilite">.*?</pre>\s*</div>',
                  lambda m: repl(m) + "</div>", body, flags=re.S)
    return body


def build_alerts(body: str) -> str:
    def convert(m):
        inner = m.group(1)
        paras = re.findall(r"<p>(.*?)</p>", inner, re.S)
        if not paras or not any(_marker(p) for p in paras):
            return m.group(0)
        out, plain = [], []
        for p in paras:
            mk = _marker(p)
            if mk:
                if plain:
                    out.append("<blockquote>" + "".join(f"<p>{x}</p>" for x in plain) + "</blockquote>")
                    plain = []
                kind, title, text = mk
                out.append(f'<div class="alert {kind}">{ICONS[kind]}<div class="body">'
                           f'<div class="alert-title">{title}</div>'
                           f'<div class="alert-desc"><p>{text}</p></div></div></div>')
            elif out and out[-1].startswith('<div class="alert'):
                # Uyarının devam paragrafı
                out[-1] = out[-1].replace("</div></div></div>", f"<p>{p}</p></div></div></div>", 1)
            else:
                plain.append(p)
        if plain:
            out.append("<blockquote>" + "".join(f"<p>{x}</p>" for x in plain) + "</blockquote>")
        return "".join(out)

    return re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", convert, body, flags=re.S)


def _marker(p: str):
    s = p.lstrip()
    for sym, kind, title in MARKERS:
        if s.startswith(sym):
            text = s[len(sym):].lstrip("️").strip()
            # "Ek not:" / "<strong>Başlık:</strong>" gibi kısa önekleri başlık yap
            tm = re.match(r"^(?:<strong>)?([^<:]{2,30}):(?:</strong>)?\s*(.*)$", text, re.S)
            if tm:
                title, text = tm.group(1).strip(), tm.group(2)
            return kind, title, text
    return None


def render_html(md_text: str, meta: dict, toc: bool, tema: str = VARSAYILAN_TEMA) -> str:
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "codehilite"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "codehilite"},
            "toc": {"toc_depth": "1-2", "permalink": False, "slugify": slugify},
        },
    )
    body = md.convert(md_text)
    body = wrap_code_blocks(body, fence_languages(md_text))
    body = build_alerts(body)

    first_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    ders = meta.get("ders") or (re.sub("<[^>]+>", "", first_h1.group(1)) if first_h1 else "Ders Notu")
    kurs = meta.get("kurs", "")
    bolum = meta.get("bolum", "")
    bugun = dt.date.today()
    tarih = f"{bugun.day} {AYLAR[bugun.month - 1]} {bugun.year}"
    e = html.escape

    # "Ders 18 - List Comprehension" → numara "18", başlık "List Comprehension"
    nm = re.match(r"^\s*(?:Ders|Lecture|Bölüm)?\s*(\d+)\s*[-–—:.]\s*(.+)$", ders, re.I)
    ders_no, ders_baslik = (nm.group(1), nm.group(2)) if nm else ("", ders)
    bm = re.match(r"^\s*(?:Bölüm|Section)?\s*(\d+)\s*[-–—:.]\s*(.+)$", bolum, re.I)
    bolum_no, bolum_baslik = (bm.group(1), bm.group(2)) if bm else ("", bolum)

    meta_cells = "".join(
        f'<div><span class="k">{k}</span><span class="v">{e(v)}</span></div>'
        for k, v in [("Kurs", kurs), ("Bölüm", bolum), ("Tarih", tarih)] if v)
    cover = (
        '<section class="cover"><div class="cover-art"></div>'
        f'<div class="cover-top"><span class="badge">Ders Notu</span>'
        f'<span class="cover-date">{tarih}</span></div>'
        '<div class="cover-main">'
        + (f'<div class="cover-num"><span class="lbl">Ders</span>{e(ders_no)}</div>' if ders_no else "")
        + (f'<div class="eyebrow">{e(kurs)}</div>' if kurs else "")
        + f'<h1 class="title">{e(ders_baslik)}</h1>'
        + (f'<div class="desc">{"<b>Bölüm " + e(bolum_no) + "</b> · " if bolum_no else ""}{e(bolum_baslik)}</div>'
           if bolum else "")
        + '</div><div class="separator"></div>'
        + f'<div class="meta">{meta_cells}</div>'
        + '<div class="foot">Ders transkriptinden derlenmiştir · Kişisel kullanım içindir</div>'
        '<span class="s-ders">' + e(ders) + '</span></section>'
    )

    YAN = {"ozet", "onemli-kavramlar", "dikkat-edilmesi-gerekenler", "tekrar-sorulari"}
    konular = [re.sub("<[^>]+>", "", t) for i, t in re.findall(r'<h2 id="([^"]*)">(.*?)</h2>', body, re.S)
               if i not in YAN]
    if konular:
        lis = "".join(f'<li><span>{n:02d}</span>{e(k)}</li>' for n, k in enumerate(konular[:12], 1))
        cover = cover.replace('</div><div class="separator">',
                              '</div><div class="cover-topics"><div class="ct-head">cat konular.txt</div>'
                              f'<ol>{lis}</ol></div><div class="separator">', 1)

    toc_html = ""
    if toc and body.count("<h2") + body.count("<h1") >= 4:
        toc_list = re.sub(r'^\s*<div class="toc">\s*|\s*</div>\s*$', "", md.toc)
        toc_html = ('<section class="toc"><div class="card"><h2>İçindekiler</h2>'
                    '<p class="sub">Bu notta yer alan başlıklar</p>'
                    f'<div class="toc-list">{toc_list}</div>'
                    '</div></section>')

    css = theme_css(tema)
    pm = re.search(r"pygments:\s*([\w-]+)", css)
    pyg_css = HtmlFormatter(style=pm.group(1) if pm else "github-dark").get_style_defs(".codehilite")
    return (
        f'<!doctype html><html lang="tr" class="tema-{e(tema)}"><head><meta charset="utf-8">'
        f"<title>{e(ders)}</title><style>{font_faces()}\n{pyg_css}\n"
        f".codehilite{{background:transparent!important}}\n{css}"
        "</style></head><body>"
        f'{cover}{toc_html}<main class="content">{body}</main></body></html>'
    )


FAMILIES = {"inter": "Inter", "eb-garamond": "EB Garamond",
            "jetbrains-mono": "JetBrains Mono"}

def font_faces() -> str:
    """assets/fonts içindeki <aile>-<ağırlık>-<stil>.woff2 dosyalarından @font-face üretir.
    Her dosya Latin + Latin Extended (Türkçe) karakterleri birlikte içerir."""
    rules = []
    for f in sorted(FONTS_DIR.glob("*.woff2")):
        m = re.match(r"^(.+?)-(\d{3})-(normal|italic)$", f.stem)
        if not m or m.group(1) not in FAMILIES:
            continue
        fam, w, st = m.groups()
        rules.append(f'@font-face{{font-family:"{FAMILIES[fam]}";font-weight:{w};font-style:{st};'
                     f'src:url("{f.as_uri()}");}}')
    return "\n".join(rules)


def theme_css(tema: str) -> str:
    path = THEMES_DIR / f"{tema}.css"
    if not path.exists():
        mevcut = ", ".join(sorted(p.stem for p in THEMES_DIR.glob("*.css")))
        sys.exit(f"Tema bulunamadı: {tema}. Mevcut temalar: {mevcut}")
    css = path.read_text(encoding="utf-8")
    if "uses: base" in css:
        css = (THEMES_DIR / "_base.css").read_text(encoding="utf-8") + "\n" + css
    return css


def pdf_weasyprint(html_str: str, out: Path) -> bool:
    try:
        from weasyprint import HTML
    except Exception:
        return False
    HTML(string=html_str, base_url=str(ASSETS)).write_pdf(str(out))
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
           f"--print-to-pdf={out.resolve()}", Path(tmp).as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    return out.exists()


def main():
    ap = argparse.ArgumentParser(description="Ders notu Markdown → PDF")
    ap.add_argument("markdown_file")
    ap.add_argument("-o", "--output")
    ap.add_argument("-t", "--tema", default=VARSAYILAN_TEMA,
                    help="Tema (assets/themes/*.css); varsayılan: akademik")
    ap.add_argument("--no-toc", action="store_true", help="İçindekiler sayfası ekleme")
    ap.add_argument("--html", action="store_true", help="Ara HTML dosyasını da kaydet")
    a = ap.parse_args()

    src = Path(a.markdown_file)
    out = Path(a.output) if a.output else src.with_suffix(".pdf")
    meta, md_text = split_front_matter(src.read_text(encoding="utf-8"))
    html_str = render_html(md_text, meta, toc=not a.no_toc, tema=a.tema)

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
