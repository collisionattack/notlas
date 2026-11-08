#!/usr/bin/env python3
"""VTT / SRT / zaman damgalı transkripti düz, okunur metne çevirir.

Kullanım: python3 clean_transcript.py girdi.vtt > temiz.txt
"""
import re
import sys
from pathlib import Path

TIMING = re.compile(r"^\s*(\d{1,2}:)?\d{1,2}:\d{2}([.,]\d{1,3})?\s*-->\s*")
INLINE_TS = re.compile(r"^\s*\[?(\d{1,2}:)?\d{1,2}:\d{2}\]?\s*")
TAGS = re.compile(r"<[^>]+>")


def clean(text: str) -> str:
    lines, prev = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "Kind:", "Language:")):
            continue
        if line.isdigit() or TIMING.match(line):
            continue
        line = TAGS.sub("", INLINE_TS.sub("", line)).strip()
        if not line or line == prev:  # tekrar eden altyazı satırlarını at
            continue
        lines.append(line)
        prev = line

    # Satırları birleştirip cümle sonlarında paragraflara böl
    joined = " ".join(lines)
    joined = re.sub(r"\s+", " ", joined)
    sentences = re.split(r"(?<=[.!?])\s+", joined)
    paras, buf = [], []
    for s in sentences:
        buf.append(s)
        if len(" ".join(buf)) > 600:
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))
    return "\n\n".join(paras)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Kullanım: clean_transcript.py <dosya>")
    print(clean(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")))
