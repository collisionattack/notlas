---
name: notlas
description: Turn a course lecture transcript (Udemy or any video course; pasted text or a .vtt/.srt/.txt file) into a structured Turkish study note, saved as Markdown + PDF in the user's indexed notes repository (ders-notlari/). Use when the user shares a lecture transcript and asks to make notes from it ("ders notu çıkar", "notlaştır", "bu dersi not al", "turn this transcript into notes"), asks to process transcripts in the transkriptler/ folder, or types /notlas. Not for general PDF creation or summarizing other documents.
---

# Notlas

Turn lecture transcripts into study notes that serve two readers: the user (PDF) and AI coding agents the user will later point at the notes as a knowledge source (Markdown). Notes are written **in Turkish**; these instructions are in English.

Scripts live in this skill's `scripts/` folder. Run them with `python3` (never `python3 -I`: isolated mode hides user-installed packages and PDF rendering fails).

## 1. Locate the notes repository

Decide the repository root (`<root>`) first, because later steps read from it:

1. The user named a path → use it.
2. The working folder contains `CLAUDE.md` and `ders-notlari/` (the Notlas project folder) → `<root>` is that `ders-notlari/`.
3. A folder on the user's computer is connected:
   - with a shell on that computer → run every script there, `<root>` = `ders-notlari/` inside the folder the user chose.
   - with file transfer only → work on a local copy. **Before saving**, copy the course's existing `kurs.json` (and the root `README.md`) from the computer into the same relative paths of the local copy; afterwards copy back every file the script reports as written plus `INDEX.md`, `kurs.json` and `README.md`. Without the old `kurs.json`, the index would list only the new lecture. If you could not fetch it, run `save_note.py --reindex` on the full repository later, or tell the user.
4. None of the above (plain cloud chat) → `<root>` = `./ders-notlari/`; at the end send the user the note's `.md` and `.pdf`. Mention that indexes only cover this session's notes unless they attach their existing `kurs.json`.

Then list existing courses:

```bash
python3 scripts/save_note.py --list-courses --root <root>
```

If the lecture belongs to a listed course, use that course's name **exactly** as listed in the `kurs:` field. Different spellings create a second course folder.

## 2. Gather the inputs

| Input | Required | Notes |
|---|---|---|
| Transcript | Yes | Pasted text, an attached file, or a file in the Notlas `transkriptler/` folder |
| Course name | Yes | Reuse the existing name from step 1 when the course already exists |
| Section and lecture (title + number) | Strongly recommended | Format `Bölüm 3 - Title`, `Ders 14 - Title`; numbers decide file order and prevent collisions |
| Course description | No | Context for terminology; pass it to the script on the course's first save, never copy it into the note |

If there is no transcript, ask for it. For anything else that is missing, make a sensible assumption and continue, except in the cases listed in "Ask only when" below.

If the transcript is VTT/SRT or has timestamps, clean it first. Write intermediate files to a scratch location (Notlas project: `transkriptler/`; otherwise a temp folder), never into `<root>`:

```bash
python3 scripts/clean_transcript.py <input> > <scratch>/temiz.txt
```

**One transcript containing several lectures.** Split it on clear boundaries: the instructor closing a lecture ("bir sonraki derste…", "in the next lecture…"), a new welcome or intro, lecture titles, or a jump in timestamps back to 00:00. Write one note file per lecture.

**Ask only when** (one short question, then proceed without further questions):
- lecture boundaries in a combined transcript are genuinely unclear, or
- the course name nearly matches an existing course and you cannot tell whether it is the same course.

When the user is not present (scheduled/unattended run), do not ask: pick the most likely option, and state the choice in your final message.

## 3. Write the note (Markdown)

The Markdown file is the **source of truth**: agents read it, and the PDF is rendered from it. It must be self-contained, searchable and consistently structured.

### Language and terminology
- Write in **Turkish**, translating if the lecture is in English.
- On a technical term's first use, give the original in parentheses: `bağımlılık enjeksiyonu (dependency injection)`.
- Never translate code, commands, identifiers, API names, package names, file paths or error messages. Agents search for these verbatim.

### Content rules
- **Re-teach the lecture; don't summarize it.** Drop filler ("şimdi şuraya tıklayalım", greetings, repetition, "see you next time"). Keep every concept, step, example, command, number and warning the instructor gives.
- **Length target:** roughly 25–40 % of the cleaned transcript's word count. Hands-on coding lectures may run longer because of code; short conceptual lectures may be shorter. If the draft is close to the transcript's length, you are transcribing, not re-teaching.
- **Long transcripts** (≈ 8,000+ words): first outline the lecture's topics, then write the note one `##` section at a time, so later topics are not compressed.
- **No outside facts.** Do not add information the instructor did not give. If a brief explanation genuinely helps understanding, mark it as `> 💡 Ek not: ...`.
- **Code:** reconstruct code the instructor writes as complete, runnable code blocks with a language tag (```tsx, ```bash …). Transcripts often miss code that was typed but not spoken (imports, types, closing braces). You may complete such parts when they follow unambiguously from context, and mark each completed line with a trailing comment `// tamamlandı` (or `# tamamlandı`). If the missing part is not obvious, write `// ... (transkriptte yok)` instead of inventing it.

### Required structure

Use exactly this skeleton. The four Turkish headings below are **fixed strings**: the script that builds the index and the PDF theme match them literally, and the script rejects notes that misspell them. Do not write `## Ders Özeti`, `## Özet:` or `## Kavramlar`.

````markdown
---
kurs: "Course Name"
bolum: "Bölüm 3 - Section Title"
ders: "Ders 12 - Lecture Title"
---

# Lecture Title

## Özet
2–4 sentences: what the lecture teaches and why it matters. (Copied into the course index.)

## <Descriptive topic heading>
Explanatory paragraphs; bullets, tables and code blocks where they help.

### <Subheading>
...

## Önemli Kavramlar
| Kavram | Açıklama |
|---|---|
| Term (original term) | One-line definition |

## Dikkat Edilmesi Gerekenler
> ⚠️ Mistakes, pitfalls and gotchas the instructor stressed.

## Tekrar Soruları
1. 3–5 questions whose answers are in the note.
````

Rules:
- `# Lecture Title` and `## Özet` are mandatory. Omit `Önemli Kavramlar`, `Dikkat Edilmesi Gerekenler` or `Tekrar Soruları` only if the lecture truly has nothing for them; if present, `Önemli Kavramlar` must be a table.
- Topic headings (`##`) become the "Konular" list in the course index, so make them descriptive (`Docker Volume Türleri`, not `Giriş` or `Devam`).
- Front-matter values: wrap them in double quotes. If a value itself contains a double quote, either escape it (`\"`) or wrap the value in single quotes instead.
- Callouts, each in its own blockquote with a blank line between them: `> ⚠️ ...` (Dikkat), `> 💡 ...` (İpucu; `> 💡 Ek not: ...` makes the title "Ek not"), `> ℹ️ ...` (Not). In the PDF, callouts inside the body become margin notes; those under `Dikkat Edilmesi Gerekenler` stay in the text column.

## 4. Save to the repository (MD + PDF + indexes)

Install dependencies if needed (the first command that works is enough):

```bash
pip install -q weasyprint markdown pygments 2>/dev/null \
  || pip install --break-system-packages -q weasyprint markdown pygments 2>/dev/null \
  || pip3 install --user -q weasyprint markdown pygments
```

Save (several notes can be passed at once):

```bash
python3 scripts/save_note.py <scratch>/note.md --root <root> [--course-description "..."]
```

Pass `--course-description` on a course's first save (or when it changes).

The script validates the note, places it at `<root>/<course-slug>/notlar/<NN-section>/<NNN-lecture>.md`, renders `pdf/…/<NNN-lecture>.pdf`, and rebuilds the course `INDEX.md`, `kurs.json` and the root `README.md`. Indexes are rebuilt from `kurs.json` plus every note on disk, so re-saving never drops other lectures.

**If the script stops with an error, fix the cause rather than reaching for the bypass flag:**

| Error | What to do |
|---|---|
| note structure (heading misspelled/missing) | Fix the note's headings, then save again. `--skip-checks` is only for notes the user deliberately structured differently. |
| course does not exist yet, but similar courses do | Same course → copy the listed name into `kurs:` exactly. Truly different course → re-run with `--new-course`. |
| path already holds a different lecture / no `bolum:` | Add the correct `bolum:` (preferred). Use `--overwrite` only when you are deliberately replacing the same lecture. |

Re-saving a lecture with the same section and title updates it in place; this is expected.

Other commands: `--reindex --root <root> [--course <slug>]` rebuilds indexes from the files on disk, and `--no-pdf` saves Markdown only.

PDF rendering uses WeasyPrint, with a fallback to installed Chrome/Edge. On macOS, WeasyPrint needs `brew install pango`; without it the script falls back to Chrome automatically. If no engine is available, the Markdown is still saved: tell the user the PDF is missing and why.

## 5. Check and report

Check the PDF once with whatever is available:
- If you can render pages to images (e.g. `pdftoppm -r 60 -f 1 -l 3 file.pdf out`), look at the cover and the first content pages: Turkish characters, code blocks, tables, margin notes.
- Otherwise run `pdftotext file.pdf - | head -40` and confirm the Turkish characters (ç ğ ı İ ö ş ü) come through.
- If neither tool exists, skip the check.

Then reply in one or two sentences: which lecture was saved, where, and the course's lecture count. Do not paste the note's content into the chat. If you made an assumption (course name, lecture split, missing section number), say so in one line.
