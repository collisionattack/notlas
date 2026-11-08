#!/usr/bin/env python3
"""Render a lecture-note Markdown file to a PDF with cover page and table of contents.

Usage:
    python3 build_pdf.py note.md [-o out.pdf] [-t theme] [--no-toc] [--html]

The Markdown file may start with a YAML front-matter block:
    ---
    course: "Course name"
    section: "Bölüm 3 - Section name"
    lecture: "Ders 12 - Lecture name"
    ---

Callouts: '> ⚠️ ...' (Dikkat), '> 💡 ...' (İpucu; '> 💡 Ek not: ...' sets the title), '> ℹ️ ...' (Not).
PDF engine: WeasyPrint (preferred), otherwise headless Chrome / Chromium / Edge.
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
    sys.exit("Missing package: pip install markdown pygments weasyprint")

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
THEMES_DIR = ASSETS / "themes"
DEFAULT_THEME = "academic"
FONTS_DIR = ASSETS / "fonts"
TR_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
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


LEGACY_KEYS = {"kurs": "course", "bolum": "section", "ders": "lecture"}


def _yaml_scalar(v: str) -> str:
    """Parse a simple YAML scalar: strips only the outer matching quotes, keeps inner ones."""
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def split_front_matter(text: str):
    meta = {}
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                meta[slugify(k.strip()).replace("-", "_")] = _yaml_scalar(v)
        text = text[m.end():]
    for old, new in LEGACY_KEYS.items():  # notes written before the English rename
        if old in meta and new not in meta:
            meta[new] = meta.pop(old)
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
                # follow-up paragraph of the same callout
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
            # a short prefix such as "Ek not:" or "<strong>Title:</strong>" becomes the callout title
            tm = re.match(r"^(?:<strong>)?([^<:]{2,30}):(?:</strong>)?\s*(.*)$", text, re.S)
            if tm:
                title, text = tm.group(1).strip(), tm.group(2)
            return kind, title, text
    return None


def render_html(md_text: str, meta: dict, toc: bool, theme: str = DEFAULT_THEME) -> str:
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
    lecture = meta.get("lecture") or (re.sub("<[^>]+>", "", first_h1.group(1)) if first_h1 else "Ders Notu")
    course = meta.get("course", "")
    section = meta.get("section", "")
    today = dt.date.today()
    date_str = f"{today.day} {TR_MONTHS[today.month - 1]} {today.year}"
    e = html.escape

    # "Ders 18 - List Comprehension" → number "18", title "List Comprehension"
    nm = re.match(r"^\s*(?:Ders|Lecture|Bölüm)?\s*(\d+)\s*[-–—:.]\s*(.+)$", lecture, re.I)
    lecture_no, lecture_title = (nm.group(1), nm.group(2)) if nm else ("", lecture)
    bm = re.match(r"^\s*(?:Bölüm|Section)?\s*(\d+)\s*[-–—:.]\s*(.+)$", section, re.I)
    section_no, section_title = (bm.group(1), bm.group(2)) if bm else ("", section)

    # smaller cover title for long lecture names, so the cover never spills onto a second page
    title_size = " xlong" if len(lecture_title) > 80 else (" long" if len(lecture_title) > 45 else "")

    meta_cells = "".join(
        f'<div><span class="k">{k}</span><span class="v">{e(v)}</span></div>'
        for k, v in [("Kurs", course), ("Bölüm", section), ("Tarih", date_str)] if v)
    cover = (
        '<section class="cover"><div class="cover-art"></div>'
        f'<div class="cover-top"><span class="badge">Ders Notu</span>'
        f'<span class="cover-date">{date_str}</span></div>'
        '<div class="cover-center"><div class="cover-main">'
        + (f'<div class="cover-num"><span class="lbl">Ders</span>{e(lecture_no)}</div>' if lecture_no else "")
        + (f'<div class="eyebrow">{e(course)}</div>' if course else "")
        + f'<h1 class="title{title_size}">{e(lecture_title)}</h1>'
        + (f'<div class="desc">{"<b>Bölüm " + e(section_no) + "</b> · " if section_no else ""}{e(section_title)}</div>'
           if section else "")
        + '</div><div class="separator"></div>'
        + f'<div class="meta">{meta_cells}</div></div>'
        + '<div class="foot">Ders transkriptinden derlenmiştir · Kişisel kullanım içindir</div>'
        '<span class="s-lecture">' + e(lecture) + '</span>'
        '<span class="s-course">' + e(course) + '</span></section>'
    )

    toc_html = ""
    if toc and body.count("<h2") + body.count("<h1") >= 4:
        toc_list = re.sub(r'^\s*<div class="toc">\s*|\s*</div>\s*$', "", md.toc)
        toc_html = ('<section class="toc"><div class="card"><h2>İçindekiler</h2>'
                    '<p class="sub">Bu notta yer alan başlıklar</p>'
                    f'<div class="toc-list">{toc_list}</div>'
                    '</div></section>')

    css = theme_css(theme)
    pm = re.search(r"pygments:\s*([\w-]+)", css)
    pyg_css = HtmlFormatter(style=pm.group(1) if pm else "github-dark").get_style_defs(".codehilite")
    return (
        f'<!doctype html><html lang="tr" class="theme-{e(theme)}"><head><meta charset="utf-8">'
        f"<title>{e(lecture)}</title><style>{font_faces()}\n{pyg_css}\n"
        f".codehilite{{background:transparent!important}}\n{css}"
        "</style></head><body>"
        f'{cover}{toc_html}<main class="content">{body}</main></body></html>'
    )


FAMILIES = {"inter": "Inter", "eb-garamond": "EB Garamond",
            "jetbrains-mono": "JetBrains Mono"}

def font_faces() -> str:
    """Build @font-face rules from assets/fonts/<family>-<weight>-<style>.woff2.
    Each file contains Latin and Latin Extended (incl. Turkish) glyphs."""
    rules = []
    for f in sorted(FONTS_DIR.glob("*.woff2")):
        m = re.match(r"^(.+?)-(\d{3})-(normal|italic)$", f.stem)
        if not m or m.group(1) not in FAMILIES:
            continue
        fam, w, st = m.groups()
        rules.append(f'@font-face{{font-family:"{FAMILIES[fam]}";font-weight:{w};font-style:{st};'
                     f'src:url("{f.as_uri()}");}}')
    return "\n".join(rules)


def theme_css(theme: str) -> str:
    path = THEMES_DIR / f"{theme}.css"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in THEMES_DIR.glob("*.css")))
        sys.exit(f"Theme not found: {theme}. Available: {available}")
    css = path.read_text(encoding="utf-8")
    if "uses: base" in css:
        css = (THEMES_DIR / "_base.css").read_text(encoding="utf-8") + "\n" + css
    return css


def pdf_weasyprint(html_str: str, out: Path) -> bool:
    try:
        from weasyprint import HTML
    except Exception as exc:  # package missing, or system library (pango) missing
        print(f"WeasyPrint unavailable ({type(exc).__name__}: {exc}).", file=sys.stderr)
        return False
    HTML(string=html_str, base_url=str(ASSETS)).write_pdf(str(out))
    return True


def pdf_chrome(html_str: str, out: Path) -> bool:
    candidates = [shutil.which(n) for n in
               ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]]
    candidates += [  # on macOS and Windows, browsers are usually not on PATH
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    exe = next((a for a in candidates if a and Path(a).exists()), None)
    if not exe:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        tmp = f.name
    cmd = [exe, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
           f"--print-to-pdf={out.resolve()}", Path(tmp).as_uri()]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return out.exists()


def render_pdf(html_str: str, out: Path):
    """Try every PDF engine in turn. Never raises; returns (engine_name, None) or (None, error_text)."""
    errors = []
    for name, fn in (("WeasyPrint", pdf_weasyprint), ("Chrome", pdf_chrome)):
        try:
            if fn(html_str, out):
                return name, None
            errors.append(f"{name}: not available")
        except Exception as exc:  # rendering failed (e.g. missing pango at render time, Chrome timeout)
            errors.append(f"{name}: {type(exc).__name__}: {str(exc).strip()[:200]}")
    return None, "; ".join(errors)


def main():
    ap = argparse.ArgumentParser(description="Lecture note Markdown → PDF")
    ap.add_argument("markdown_file")
    ap.add_argument("-o", "--output")
    ap.add_argument("-t", "--theme", default=DEFAULT_THEME,
                    help="Theme name (assets/themes/*.css); default: academic")
    ap.add_argument("--no-toc", action="store_true", help="Skip the table-of-contents page")
    ap.add_argument("--html", action="store_true", help="Also save the intermediate HTML")
    a = ap.parse_args()

    src = Path(a.markdown_file)
    out = Path(a.output) if a.output else src.with_suffix(".pdf")
    meta, md_text = split_front_matter(src.read_text(encoding="utf-8"))
    html_str = render_html(md_text, meta, toc=not a.no_toc, theme=a.theme)

    if a.html:
        out.with_suffix(".html").write_text(html_str, encoding="utf-8")

    engine, err = render_pdf(html_str, out)
    if not engine:
        sys.exit(f"PDF not created ({err}). Install WeasyPrint (pip install weasyprint; "
                 "on macOS also brew install pango) or Google Chrome.")
    print(f"PDF created ({engine}): {out}")


if __name__ == "__main__":
    main()
