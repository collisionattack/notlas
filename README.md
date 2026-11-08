# Notlas

*not + atlas* — a Claude skill that turns course lecture transcripts (Udemy or any video course) into structured study notes. Each note is saved twice: as an academic-style **PDF** for reading and as **Markdown** in an indexed notes repository that AI agents can use as a knowledge source.

Notes are written in Turkish; technical terms keep their original English in parentheses, and code, commands and identifiers are never translated.

## How it works

1. You give Claude a transcript plus the course name and section/lecture titles (and optionally the course description).
2. Claude re-teaches the lecture as a Markdown note: summary, topic sections, runnable code, a concept table, pitfalls and review questions.
3. `scripts/save_note.py` validates the note, stores it in the repository, renders the PDF and rebuilds the indexes.

## Notes repository

```
ders-notlari/
├── README.md                             # all courses
└── <course-slug>/
    ├── INDEX.md                          # per lecture: summary, topics, concepts, file links
    ├── kurs.json                         # same data, machine-readable
    ├── notlar/<NN-section>/<NNN-lecture>.md   # source for agents
    └── pdf/<NN-section>/<NNN-lecture>.pdf     # readable copy
```

To use a course as a knowledge source in another project, point the agent at the course's `INDEX.md`. It finds the relevant lecture there and opens only that Markdown file. See `examples/ders-notlari/` for a filled-in sample.

## Using it as a project folder

Clone the repo and open the folder in Claude Code or the Claude desktop app. `CLAUDE.md` describes the workflow:

```
notlas/
├── CLAUDE.md        # workflow instructions for Claude
├── SKILL.md         # note format and writing rules
├── transkriptler/   # drop raw transcripts here (git-ignored)
└── ders-notlari/    # your notes repository (git-ignored)
```

## Installing the skill

**Claude app:** zip this folder without `.git/`, `ders-notlari/` and `transkriptler/` (or download `notlas.zip` from Releases), then go to **Customize → Skills → + → Create skill → Upload a skill**. Code execution and file creation must be enabled under Settings → Capabilities.

**Claude Code:**
```bash
git clone https://github.com/<user>/notlas ~/.claude/skills/notlas
```

## Usage

> Kurs: Docker ve Kubernetes
> Bölüm 2 - Depolama / Ders 7 - Docker Volume'ları
> *(paste the transcript or attach the .vtt/.txt file)*
>
> Bunu ders notu yap.

or type `/notlas`.

## Scripts

```bash
pip install weasyprint markdown pygments
python3 scripts/clean_transcript.py lecture.vtt > lecture.txt          # VTT/SRT → plain text
python3 scripts/save_note.py note.md --root ders-notlari \
        --course-description "..."                                    # save: MD + PDF + indexes
python3 scripts/save_note.py --list-courses --root ders-notlari       # existing courses
python3 scripts/save_note.py --reindex --root ders-notlari            # rebuild indexes from disk
python3 scripts/build_pdf.py note.md -o note.pdf                      # PDF only
```

`save_note.py` refuses misspelled section headings, course names that look like an existing course, and saves that would replace a different lecture. Each check names the flag that overrides it.

PDF rendering uses WeasyPrint and falls back to an installed Chrome/Edge (on macOS, WeasyPrint needs `brew install pango`).

## Files

```
SKILL.md                    # instructions for Claude
CLAUDE.md                   # project-folder workflow
scripts/clean_transcript.py # strips timestamps and repeated caption lines
scripts/save_note.py        # validates and stores notes, builds INDEX.md / kurs.json / README.md
scripts/build_pdf.py        # Markdown → PDF
assets/themes/akademik.css  # Tufte-style theme: ivory paper, EB Garamond, margin notes
assets/fonts/               # EB Garamond, Inter, JetBrains Mono (SIL OFL, full Turkish coverage)
examples/                   # sample transcript, notes and a sample repository
```

## Note

For personal use. Notes are derived from course content, so the copyright stays with the instructors. Don't publish your notes repository.
