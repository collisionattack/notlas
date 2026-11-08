# Notlas — project instructions

This folder is both the **source of the Notlas skill** and the user's **personal lecture-notes repository**.

## Making lecture notes

When the user shares a lecture transcript (pasted, attached, or dropped into `transkriptler/`), follow `SKILL.md` in this folder. In this project:

- The repository root is always `ders-notlari/` (pass `--root ders-notlari`).
- Read transcripts from `transkriptler/` and write cleaned text and note drafts there too. Never write drafts into `ders-notlari/`.
- Run the scripts from this folder: `python3 scripts/save_note.py transkriptler/<note>.md --root ders-notlari`.

## Folders

| Folder | Contents | In git |
|---|---|---|
| `ders-notlari/` | Notes repository: `<course>/INDEX.md`, `kurs.json`, `notlar/` (MD), `pdf/` | No (personal, derived from copyrighted courses) |
| `transkriptler/` | Raw transcripts and note drafts | No |
| `SKILL.md`, `scripts/`, `assets/` | Skill source | Yes |
| `examples/` | Sample notes and a sample repository | Yes |

## Using the notes as a knowledge source

To give another project's agent a course as reference, point it at `ders-notlari/<course-slug>/INDEX.md`. The index lists every lecture's summary, topics and concepts with links to the Markdown notes. PDFs are for humans.

## Developing the skill

- PDF theme: `assets/themes/akademik.css`. After changing it, re-render the examples and look at them:
  `python3 scripts/save_note.py examples/ornek_*.md --root examples/ders-notlari --new-course`
- Package the skill for upload to Claude, excluding personal data and git:
  ```bash
  cd .. && zip -qr notlas.zip notlas -x 'notlas/.git/*' 'notlas/ders-notlari/*' 'notlas/transkriptler/*' '*/__pycache__/*'
  ```
