#!/usr/bin/env python3
"""Render a preview image of a note PDF: the cover and the first content pages side by side.

Usage:
    python3 preview.py note.pdf -o preview.png [--pages 1,3,4] [--dpi 70]

Default pages: the cover, the first content page (page 3 when there is a table of contents)
and the page after it. Uses pdftoppm (poppler) when installed, otherwise PyMuPDF; prints a
clear message and exits with code 2 when neither is available.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def page_count(pdf: Path) -> int:
    try:
        import fitz  # PyMuPDF
        with fitz.open(pdf) as doc:
            return doc.page_count
    except ImportError:
        pass
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    return 0


def render_pages(pdf: Path, pages, dpi: int, tmp: Path):
    """Return a list of PIL images, one per requested page."""
    from PIL import Image
    images = []
    if shutil.which("pdftoppm"):
        for n in pages:
            stem = tmp / f"p{n}"
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(n), "-l", str(n),
                            "-singlefile", str(pdf), str(stem)], capture_output=True)
            if Path(f"{stem}.png").exists():  # pages beyond the end are simply skipped
                images.append(Image.open(f"{stem}.png").convert("RGB"))
        return images
    try:
        import fitz
    except ImportError:
        return None
    with fitz.open(pdf) as doc:
        for n in pages:
            pix = doc[n - 1].get_pixmap(dpi=dpi)
            images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return images


def compose(images, out: Path, max_width: int = 1800):
    from PIL import Image, ImageDraw, ImageFilter
    w, h = images[0].size
    pad, gap = 40, 30
    canvas = Image.new("RGB", (pad * 2 + w * len(images) + gap * (len(images) - 1), pad * 2 + h), "#e8e4da")
    for i, im in enumerate(images):
        x, y = pad + i * (w + gap), pad
        shadow = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle([12, 12, w + 12, h + 12], fill=(0, 0, 0, 55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas.paste(shadow, (x - 6, y - 2), shadow)
        canvas.paste(im, (x, y))
    canvas.thumbnail((max_width, max_width))
    canvas.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser(description="Preview image of a note PDF")
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", help="PNG path (default: <pdf>-preview.png next to the PDF)")
    ap.add_argument("--pages", help="Comma-separated page numbers (default: cover + first content pages)")
    ap.add_argument("--dpi", type=int, default=70)
    a = ap.parse_args()

    pdf = Path(a.pdf)
    out = Path(a.output) if a.output else pdf.with_name(pdf.stem + "-preview.png")
    total = page_count(pdf)
    if a.pages:
        pages = [int(p) for p in a.pages.split(",") if p.strip()]
    else:
        pages = [1, 3, 4] if (total >= 4 or not total) else list(range(1, total + 1))[:3]
    if total:
        pages = [p for p in pages if 1 <= p <= total] or [1]

    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit("Preview needs Pillow: pip install pillow")
    with tempfile.TemporaryDirectory() as tmp:
        images = render_pages(pdf, pages, a.dpi, Path(tmp))
        if not images:
            print("No PDF rasterizer found (install poppler for pdftoppm, or pip install pymupdf).",
                  file=sys.stderr)
            sys.exit(2)
        compose(images, out)
    print(f"Preview: {out} (pages {', '.join(map(str, pages))} of {total or '?'})")


if __name__ == "__main__":
    main()
