#!/usr/bin/env python3
"""Save lecture notes (Markdown) into the notes repository, render their PDFs and rebuild the indexes.

Usage:
    python3 save_note.py NOTE.md [NOTE2.md ...] --root courses [--course-description "..."]
    python3 save_note.py --list-courses --root courses
    python3 save_note.py --reindex --root courses [--course <course-slug>] [--prune]

Repository layout (agents read the Markdown, humans read the PDFs):

    <root>/
    ├── README.md                         # all courses
    └── <course-slug>/
        ├── INDEX.md                      # lecture → summary, topics, concepts, file paths
        ├── course.json                   # same data, machine-readable
        ├── notes/<NN-section>/<NNN-lecture>.md
        └── pdf/<NN-section>/<NNN-lecture>.pdf

Safety checks (each can be bypassed with the flag shown in its error message):
  * required sections/headings are present and spelled exactly        (--skip-checks)
  * a NEW course name that looks like an existing course is refused    (--new-course)
  * a different lecture already stored at the same path is not replaced (--overwrite)

Indexes are rebuilt from course.json PLUS every note found under notes/, so an index is never
shrunk by saving into a partial copy of the repository: entries whose files are not present
locally are kept as long as they are listed in course.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pdf  # noqa: E402

REQUIRED = ["Özet"]
CANONICAL = ["Özet", "Önemli Kavramlar", "Dikkat Edilmesi Gerekenler", "Tekrar Soruları"]
# Common misspellings → canonical heading (the PDF theme and the index depend on exact names)
VARIANTS = {
    r"(ders\s+)?özet(i)?\s*:?|summary|tl;?dr": "Özet",
    r"(önemli\s+|temel\s+|anahtar\s+)?kavramlar\s*:?|key\s+concepts|concepts|glossary|terimler": "Önemli Kavramlar",
    r"dikkat(\s+edilmesi\s+gerekenler)?\s*:?|uyarılar|tuzaklar|pitfalls|gotchas|caveats": "Dikkat Edilmesi Gerekenler",
    r"(tekrar|gözden\s+geçirme|alıştırma)\s+soruları\s*:?|review\s+questions|sorular": "Tekrar Soruları",
}


# ---------------------------------------------------------------- parsing helpers
def slug(text: str, max_len: int = 60) -> str:
    s = build_pdf.slugify(text or "")
    return s[:max_len].rstrip("-") or "adsiz"


def number_and_title(text: str, prefix: str):
    m = re.match(rf"^\s*(?:{prefix})?\s*(\d+)\s*[-–—:.]\s*(.+)$", text or "", re.I)
    return (int(m.group(1)), m.group(2).strip()) if m else (None, (text or "").strip())


def h2_headings(md: str):
    out, in_code = [], False
    for line in md.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_code = not in_code
        elif not in_code:
            m = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
            if m:
                out.append(m.group(1).strip())
    return out


def section_body(md: str, heading: str) -> str:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^#{{1,2}}\s|\Z)", md, re.S | re.M)
    return m.group(1) if m else ""


def extract_summary(md: str) -> str:
    body = section_body(md, "Özet").strip()
    first_para = re.split(r"\n\s*\n", body, maxsplit=1)[0] if body else ""
    t = re.sub(r"[`*_]", "", " ".join(first_para.split()))
    return t if len(t) <= 260 else t[:257].rsplit(" ", 1)[0] + "…"


def extract_concepts(md: str):
    rows = [ln.strip() for ln in section_body(md, "Önemli Kavramlar").splitlines() if ln.strip().startswith("|")]
    is_sep = [bool(re.fullmatch(r"\|?(\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*\|?", r)) for r in rows]
    out = []
    for i, row in enumerate(rows):
        if is_sep[i] or (i + 1 < len(rows) and is_sep[i + 1]):  # separator, or the header above it
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) >= 2 and cells[0]:
            out.append(re.sub(r"[`*_]", "", cells[0]))
    return out


def extract_topics(md: str):
    return [h for h in h2_headings(md) if h not in CANONICAL]


def validate(md: str, path: Path):
    """Return a list of problems with the note's structure (empty list = OK)."""
    problems = []
    if not re.search(r"^#\s+\S", md, re.M):
        problems.append("missing the '# <Lecture title>' heading")
    heads = h2_headings(md)
    for h in heads:
        if h in CANONICAL:
            continue
        for pat, canon in VARIANTS.items():
            if re.fullmatch(pat, h, re.I):
                problems.append(f"heading '## {h}' must be spelled exactly '## {canon}'")
    for req in REQUIRED:
        if req not in heads:
            problems.append(f"missing required section '## {req}'")
    if "Önemli Kavramlar" in heads and not extract_concepts(md):
        problems.append("'## Önemli Kavramlar' must contain a '| Kavram | Açıklama |' table")
    return [f"{path.name}: {p}" for p in problems]


# ---------------------------------------------------------------- course index
def load_course(course_dir: Path, name: str = "") -> dict:
    kj = course_dir / "course.json"
    if kj.exists():
        return json.loads(kj.read_text(encoding="utf-8"))
    return {"course": name, "description": "", "lectures": []}


def lecture_entry(md_path: Path, course_dir: Path, previous: dict | None = None) -> dict:
    text = md_path.read_text(encoding="utf-8")
    meta, body = build_pdf.split_front_matter(text)
    s_no, s_title = number_and_title(meta.get("section", ""), "Bölüm|Section")
    first_h1 = re.search(r"^#\s+(.+)$", body, re.M)
    l_no, l_title = number_and_title(meta.get("lecture") or (first_h1.group(1) if first_h1 else md_path.stem),
                                     "Ders|Lecture")
    rel_md = md_path.relative_to(course_dir).as_posix()
    rel_pdf = "pdf/" + rel_md[len("notes/"):-3] + ".pdf"
    has_pdf = (course_dir / rel_pdf).exists() or bool(previous and previous.get("pdf"))
    return {
        "section_no": s_no, "section": s_title, "lecture_no": l_no, "lecture": l_title,
        "summary": extract_summary(body), "topics": extract_topics(body), "concepts": extract_concepts(body),
        "md": rel_md, "pdf": rel_pdf if has_pdf else None,
        "updated": dt.datetime.fromtimestamp(md_path.stat().st_mtime).date().isoformat(),
    }


def rebuild_course(course_dir: Path, description: str = "", name: str = "", prune: bool = False) -> dict:
    """Merge course.json with every note on disk; disk wins for files that exist locally.

    prune=True drops entries whose Markdown file is missing locally. Use it only on a complete
    repository (never on a partial copy), e.g. after deleting or moving a lecture.
    """
    data = load_course(course_dir, name)
    if name:
        data["course"] = name
    if description:
        data["description"] = description
    by_md = {d["md"]: d for d in data.get("lectures", [])
             if not prune or (course_dir / d["md"]).exists()}
    for md in sorted((course_dir / "notes").glob("**/*.md")):
        rel = md.relative_to(course_dir).as_posix()
        by_md[rel] = lecture_entry(md, course_dir, by_md.get(rel))
        if not data.get("course"):
            data["course"] = build_pdf.split_front_matter(md.read_text(encoding="utf-8"))[0].get("course", "")
    big = 9999
    data["lectures"] = sorted(by_md.values(), key=lambda d: (
        d["section_no"] if d["section_no"] is not None else big,
        d["lecture_no"] if d["lecture_no"] is not None else big, d["md"]))
    (course_dir / "course.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_course_index(course_dir, data)
    return data


def write_course_index(course_dir: Path, data: dict):
    s = [f"# {data['course']} — Ders Notları", ""]
    if data.get("description"):
        s += [f"> {data['description']}", ""]
    s += ["Bu klasör, kursun ders notlarını bilgi kaynağı olarak tutar. Agent'lar için kaynak "
          "Markdown dosyalarıdır (`notes/`); `pdf/` aynı içeriğin okunabilir kopyasıdır. "
          "Bir konuyu ararken önce aşağıdaki kavram ve konu listelerine bakın, sonra ilgili notu açın.", "",
          f"Toplam {len(data['lectures'])} ders · Makinece okunur liste: `course.json`", ""]
    last = object()
    for d in data["lectures"]:
        sec = (f"Bölüm {d['section_no']} · {d['section']}" if d["section_no"] is not None else (d["section"] or "Genel"))
        if sec != last:
            s += [f"## {sec}", ""]
            last = sec
        no = f"{d['lecture_no']} · " if d["lecture_no"] is not None else ""
        s += [f"### {no}{d['lecture']}", ""]
        if d.get("summary"):
            s += [d["summary"], ""]
        if d.get("topics"):
            s.append("- **Konular:** " + "; ".join(d["topics"]))
        if d.get("concepts"):
            s.append("- **Kavramlar:** " + ", ".join(d["concepts"]))
        files = f"[Markdown]({d['md']})" + (f" · [PDF]({d['pdf']})" if d.get("pdf") else "")
        s += [f"- **Dosya:** {files}", ""]
    (course_dir / "INDEX.md").write_text("\n".join(s), encoding="utf-8")


def write_root_readme(root: Path):
    lines = ["# Ders Notları", "",
             "Kişisel kurs notları deposu. Her kurs kendi klasöründedir; kursun `INDEX.md` dosyası "
             "derslerin özetini, konularını ve kavramlarını listeler.", "",
             "| Kurs | Ders sayısı | Dizin |", "|---|---|---|"]
    for kj in sorted(root.glob("*/course.json")):
        v = json.loads(kj.read_text(encoding="utf-8"))
        lines.append(f"| {v['course']} | {len(v['lectures'])} | [{kj.parent.name}/INDEX.md]({kj.parent.name}/INDEX.md) |")
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_courses(root: Path):
    return [(kj.parent.name, json.loads(kj.read_text(encoding="utf-8"))["course"])
            for kj in sorted(root.glob("*/course.json"))]


def label(no, title, word, empty="-"):
    """'Bölüm 5 - Title' / 'Ders 23 - Title' (or just the title when there is no number)."""
    return f"{word} {no} - {title}" if no is not None else (title or empty)


def course_overview(root: Path):
    """One line per course: folder, name, lecture count, and the last (highest-numbered) lecture."""
    lines = []
    for kj in sorted(root.glob("*/course.json")):
        v = json.loads(kj.read_text(encoding="utf-8"))
        lectures = v.get("lectures", [])
        line = f"{kj.parent.name} | {v['course']} | {len(lectures)} ders"
        if lectures:
            last = lectures[-1]  # course.json is kept sorted by section and lecture number
            line += (f" | son: {label(last['section_no'], last['section'], 'Bölüm', 'Genel')} / "
                     f"{label(last['lecture_no'], last['lecture'], 'Ders')}")
        lines.append(line)
    return lines


STOPWORDS = {"ve", "ile", "icin", "kurs", "kursu", "egitimi", "the", "and", "for", "with", "course",
             "complete", "guide", "a", "to", "z", "sifirdan", "ileri", "seviye", "web", "full", "stack",
             "gelistirme", "programlama", "temelleri", "bootcamp", "masterclass", "uygulamali", "pratik",
             "development", "developer", "programming", "fundamentals", "beginners", "advanced"}


def similar_courses(root: Path, name: str):
    target = slug(name)
    out = []
    for s, title in list_courses(root):
        ratio = difflib.SequenceMatcher(None, target, s).ratio()
        shared = {w for w in (set(target.split("-")) & set(s.split("-"))) - STOPWORDS if len(w) >= 3}
        if ratio >= 0.6 or target.startswith(s) or s.startswith(target) or shared:
            out.append((s, title, round(ratio, 2)))
    return sorted(out, key=lambda x: -x[2])


# ---------------------------------------------------------------- save
def save(note: Path, root: Path, description: str = "", pdf: bool = True,
         new_course: bool = False, overwrite: bool = False, skip_checks: bool = False):
    text = note.read_text(encoding="utf-8")
    meta, body = build_pdf.split_front_matter(text)
    course = meta.get("course")
    if not course:
        sys.exit(f"ERROR {note.name}: front matter must contain 'course:'.")
    if not skip_checks:
        problems = validate(body, note)
        if problems:
            sys.exit("ERROR note structure:\n  - " + "\n  - ".join(problems) +
                     "\nFix the note (preferred) or pass --skip-checks.")

    course_dir = root / slug(course)
    if not course_dir.exists() and not new_course:
        sims = similar_courses(root, course)
        if sims:
            lst = "\n".join(f"  - {t}  (folder: {s})" for s, t, _ in sims)
            sys.exit(f"ERROR: course '{course}' does not exist yet, but similar courses do:\n{lst}\n"
                     "If it is the same course, set 'course:' to that exact name. "
                     "If it really is a new course, re-run with --new-course.")

    s_no, s_title = number_and_title(meta.get("section", ""), "Bölüm|Section")
    first_h1 = re.search(r"^#\s+(.+)$", body, re.M)
    l_no, l_title = number_and_title(meta.get("lecture") or (first_h1.group(1) if first_h1 else note.stem),
                                     "Ders|Lecture")
    sec_dir = f"{s_no:02d}-{slug(s_title)}" if s_no is not None else (slug(s_title) if s_title else "genel")
    file_stem = f"{l_no:03d}-{slug(l_title)}" if l_no is not None else slug(l_title)
    md_target = course_dir / "notes" / sec_dir / f"{file_stem}.md"
    pdf_target = course_dir / "pdf" / sec_dir / f"{file_stem}.pdf"

    if md_target.exists() and not overwrite and md_target.resolve() != note.resolve():
        old_meta, old_body = build_pdf.split_front_matter(md_target.read_text(encoding="utf-8"))
        old_h1 = re.search(r"^#\s+(.+)$", old_body, re.M)
        _, old_title = number_and_title(old_meta.get("lecture") or (old_h1.group(1) if old_h1 else ""), "Ders|Lecture")
        if slug(old_title) != slug(l_title) or old_meta.get("section", "") != meta.get("section", ""):
            sys.exit(f"ERROR: {md_target} already holds a different lecture ('{old_title}').\n"
                     "Add/fix 'section:' so the lectures land in different section folders, "
                     "or pass --overwrite to replace it.")
        if s_no is None and not s_title:
            sys.exit(f"ERROR: {md_target} already exists and this note has no 'section:', so it is unclear whether "
                     "it is an update of the same lecture or a same-named lecture from another section.\n"
                     "Add 'section:' (preferred), or pass --overwrite if it is an update of the same lecture.")

    md_target.parent.mkdir(parents=True, exist_ok=True)
    if md_target.resolve() != note.resolve():
        md_target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")

    pdf_ok = False
    if pdf:
        try:
            pdf_target.parent.mkdir(parents=True, exist_ok=True)
            html_str = build_pdf.render_html(body, meta, toc=True)
            engine, err = build_pdf.render_pdf(html_str, pdf_target)
            pdf_ok = bool(engine)
            if not pdf_ok:
                print(f"WARNING {note.name}: PDF not created ({err}). The Markdown note and the indexes "
                      "were still saved; install WeasyPrint (+ brew install pango on macOS) or Chrome "
                      "and save again to add the PDF.", file=sys.stderr)
        except Exception as exc:  # e.g. a theme/HTML problem; the note itself must still be indexed
            print(f"WARNING {note.name}: PDF not created ({type(exc).__name__}: {exc}).", file=sys.stderr)

    data = rebuild_course(course_dir, description, course)
    write_root_readme(root)

    # Same lecture file name in another section folder → probably moved; old copy is still listed.
    twins = [p for p in (course_dir / "notes").glob(f"*/{file_stem}.md") if p.resolve() != md_target.resolve()]
    if twins:
        lst = "\n".join(f"  - {p}" for p in twins)
        print(f"WARNING {note.name}: the same lecture also exists in another section folder:\n{lst}\n"
              "If the lecture was moved, delete the old .md (and its .pdf under pdf/), then run "
              f"--reindex --prune --root {root} --course {course_dir.name}.", file=sys.stderr)
    return md_target, (pdf_target if pdf_ok else None), len(data["lectures"])


def main():
    ap = argparse.ArgumentParser(description="Save lecture notes into the notes repository (MD + PDF + indexes)")
    ap.add_argument("notes", nargs="*", help="Note Markdown file(s) to save")
    ap.add_argument("--root", default="courses", help="Notes repository root (default: ./courses)")
    ap.add_argument("--course-description", dest="desc", default="",
                    help="Course description (stored in INDEX.md and course.json)")
    ap.add_argument("--no-pdf", dest="no_pdf", action="store_true", help="Save Markdown only")
    ap.add_argument("--new-course", action="store_true", help="Confirm that a course name is genuinely new")
    ap.add_argument("--overwrite", action="store_true", help="Replace a different lecture stored at the same path")
    ap.add_argument("--skip-checks", action="store_true", help="Skip note-structure validation")
    ap.add_argument("--list-courses", action="store_true",
                    help="List courses as 'folder | name | N ders | son: <last section> / <last lecture>' and exit")
    ap.add_argument("--reindex", action="store_true", help="Rebuild indexes from course.json + notes on disk")
    ap.add_argument("--prune", action="store_true",
                    help="With --reindex: drop index entries whose note file no longer exists "
                         "(only on the complete repository, never on a partial copy)")
    ap.add_argument("--course", help="With --reindex: only this course folder")
    a = ap.parse_args()
    root = Path(a.root)

    if a.list_courses:
        lines = course_overview(root)
        print("\n".join(lines) if lines else f"No courses yet in {root}/")
        return
    if a.reindex:
        dirs = [root / a.course] if a.course else [p.parent for p in root.glob("*/course.json")] + \
            [p for p in root.iterdir() if p.is_dir() and (p / "notes").is_dir() and not (p / "course.json").exists()]
        for d in sorted(set(dirs)):
            n = len(rebuild_course(d, a.desc if a.course else "", prune=a.prune)["lectures"])
            print(f"Reindexed {d.name}: {n} lectures")
        write_root_readme(root)
        return
    if not a.notes:
        ap.error("give at least one note file, or use --list-courses / --reindex")

    for n in a.notes:
        md, pdf, total = save(Path(n), root, a.desc, pdf=not a.no_pdf,
                              new_course=a.new_course, overwrite=a.overwrite, skip_checks=a.skip_checks)
        print(f"Saved: {md}" + (f"\n       {pdf}" if pdf else "") + f"\n       course now has {total} lectures")
    print(f"Indexes updated: {root / 'README.md'}")


if __name__ == "__main__":
    main()
