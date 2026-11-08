# Changelog

## Unreleased

### Fixed

- **Cover layout with long texts.** Long course, section or lecture names no longer run off the cover: the course / section / date row is a fixed three-column row whose cells wrap, the date stays on one line, long lecture titles get a smaller cover font, and the cover block is vertically centred.
- **Long inline code** (identifiers in margin notes, table cells and body text) wraps inside its column instead of leaving the page; short identifiers are not split.

### Added

- **Automatic preview.** After each save Claude renders the cover and first content pages into one image (`scripts/preview.py`), checks it, and shows it together with the PDF without being asked. In Claude Code on macOS the PDF is also opened directly.

## v0.1.0 — 2026-11-08

First public release of **Notlas** (*not + atlas*), a Claude skill that turns course lecture transcripts into structured Turkish study notes, saved as an academic-style PDF for reading and as Markdown in an indexed repository that AI agents can use as a knowledge source.

### Highlights

- **Transcript → study note.** Claude re-teaches the lecture instead of summarizing it: a summary, descriptive topic sections, runnable code blocks, a concept table, pitfalls and review questions. Notes are written in Turkish; technical terms keep their original English in parentheses, and code, commands and identifiers are never translated.
- **Academic PDF theme.** Tufte-style handout layout: ivory paper, EB Garamond, a cover page, a table of contents with page numbers, callouts as margin notes, booktabs tables and syntax-highlighted code. Fonts are embedded with full Turkish character coverage.
- **Agent-ready notes repository.** Notes are stored as `courses/<course>/notes/<NN-section>/<NNN-lecture>.md` with a matching `pdf/` tree. Each course gets an `INDEX.md` (summary, topics and concepts for every lecture) and a machine-readable `course.json`; a root `README.md` lists all courses. Point an agent at a course's `INDEX.md` and it can find and open the right lecture.
- **No format to remember.** `/notlas` on its own replies with a fill-in template that lists your courses and the last lecture saved in each. Paste a transcript without details and Claude asks once, proposing the most likely course and the next lecture number. A transcript file named like `nextjs_05-23.vtt` supplies course, section and lecture by itself.

### Safety checks in `save_note.py`

- Rejects notes whose fixed section headings (`## Özet`, `## Önemli Kavramlar`, …) are misspelled or missing.
- Refuses a new course name that looks like an existing course, unless confirmed with `--new-course`.
- Never silently replaces a different lecture stored at the same path (`--overwrite` to force).
- Indexes are rebuilt from `course.json` plus every note on disk, so saving into a partial copy never shrinks an index; `--reindex --prune` cleans up after moving or deleting lectures.
- PDF engine failures never block saving: the note and indexes are written and the warning explains why the PDF is missing.

### Tools

- `scripts/save_note.py`: validate, store, render and index notes (`--list-courses`, `--reindex`, `--prune`, `--no-pdf`).
- `scripts/build_pdf.py`: Markdown → PDF with WeasyPrint, falling back to an installed Chrome, Chromium, Edge or Brave.
- `scripts/clean_transcript.py`: VTT/SRT/timestamped transcript → clean paragraphs (drops cue numbers and repeated caption lines, keeps spoken numbers).

### Installation

- **Claude app:** download `notlas.zip` from this release and upload it under **Customize → Skills → + → Create skill → Upload a skill**. Code execution and file creation must be enabled under Settings → Capabilities. To save notes into a folder on your computer, connect the project folder to the chat with **+ → Add folder** in the desktop app.
- **Claude Code:** clone or link the repository into `~/.claude/skills/notlas`, or open the cloned folder directly (its `CLAUDE.md` describes the workflow).

### Requirements

Python 3.9+ with `markdown`, `pygments` and `weasyprint`. In the Claude app these are installed automatically when needed. On macOS, WeasyPrint also needs `pango` (`brew install pango`); without it the PDF falls back to Google Chrome if installed.

### Known limitations

- Videos are not processed: notes come from the transcript text only, so a lecture without captions cannot be converted.
- Notes are derived from course content, so the copyright stays with the instructors. Keep your `courses/` repository private (it is git-ignored by default).
- `/notlas` as a slash command is confirmed in Claude Code; in other clients, mention the skill by name if the command does not appear.

### Upgrading from pre-release builds

- Folder and file names are now English: the notes root `ders-notlari/` (later `lecture-notes/`) is `courses/`, each course's `notlar/` is `notes/`, and `kurs.json` is `course.json`. Rename existing folders and files, then run `python3 scripts/save_note.py --reindex --root courses` to rebuild the indexes.
- Front matter now uses `course` / `section` / `lecture`; notes written with the old `kurs` / `bolum` / `ders` keys are still read.
- Replace any previously uploaded `udemy-ders-notu` or older `notlas` skill with this release's `notlas.zip`.
