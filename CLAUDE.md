# Notlas — project instructions

This folder is both the **source of the Notlas skill** and the user's **personal lecture-notes repository**.

## Making lecture notes

When the user shares a lecture transcript (pasted, attached, or dropped into `transcripts/`), follow `SKILL.md` in this folder. In this project:

- The repository root is always `lecture-notes/` (pass `--root lecture-notes`).
- Read transcripts from `transcripts/` and write cleaned text and note drafts there too. Never write drafts into `lecture-notes/`.
- Run the scripts from this folder: `python3 scripts/save_note.py transcripts/<note>.md --root lecture-notes`.

## Folders

| Folder | Contents | In git |
|---|---|---|
| `lecture-notes/` | Notes repository: `<course>/INDEX.md`, `course.json`, `notes/` (MD), `pdf/` | No (personal, derived from copyrighted courses) |
| `transcripts/` | Raw transcripts and note drafts | No |
| `SKILL.md`, `scripts/`, `assets/` | Skill source | Yes |
| `docs/` | README preview image | Yes |

## Using the notes as a knowledge source

To give another project's agent a course as reference, point it at `lecture-notes/<course-slug>/INDEX.md`. The index lists every lecture's summary, topics and concepts with links to the Markdown notes. PDFs are for humans.

## Developing the skill

- PDF theme: `assets/themes/academic.css`. After changing it, render an existing note (or a short test note written to `transcripts/`) outside the repository and look at the pages:
  `python3 scripts/build_pdf.py lecture-notes/<course>/notes/<section>/<lecture>.md -o transcripts/theme-test.pdf`
  Check a note with code blocks, tables, margin notes and Turkish characters. If the theme changed, re-render all PDFs with `save_note.py` (it rewrites them in place).
- Package the skill for upload to Claude, excluding personal data, git and the README image:
  ```bash
  cd .. && zip -qr notlas.zip notlas -x 'notlas/.git/*' 'notlas/lecture-notes/*' 'notlas/transcripts/*' 'notlas/docs/*' 'notlas/_to_delete/*' '*/__pycache__/*'
  ```
