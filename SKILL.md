---
name: notlas
description: Turn a course lecture transcript (Udemy or any video course; pasted text or a .vtt/.srt/.txt file) into a structured Turkish study note, saved as Markdown + PDF in the user's indexed notes repository (courses/). Use when the user shares a lecture transcript and asks to make notes from it ("ders notu çıkar", "notlaştır", "bu dersi not al", "turn this transcript into notes"), asks to process transcripts in the transcripts/ folder, or invokes /notlas (alone, it replies with a fill-in template). Not for general PDF creation or summarizing other documents.
---

# Notlas

Turn lecture transcripts into study notes that serve two readers: the user (PDF) and AI coding agents the user will later point at the notes as a knowledge source (Markdown). Notes are written **in Turkish**; these instructions are in English.

Scripts live in the `scripts/` folder next to this `SKILL.md`. Below, `<skill>` means that folder's parent (the directory containing this file). Use its absolute path, because the working directory is usually somewhere else; inside the Notlas project folder `<skill>` is simply `.`. Run the scripts with `python3` (never `python3 -I`: isolated mode hides user-installed packages and PDF rendering fails).

## 1. Locate the notes repository

Decide the repository root (`<root>`) first, because later steps read from it:

1. The user named a path → use it.
2. The working folder contains `CLAUDE.md` and `courses/` (the Notlas project folder) → `<root>` is that `courses/`.
3. A folder on the user's computer is connected:
   - with a shell on that computer → run every script there, `<root>` = `courses/` inside the folder the user chose.
   - with file transfer only → work on a local copy. **Before saving**, copy **every** `<root>/*/course.json` from the computer into the same relative paths of the local copy (they are small). Afterwards copy back the new note's `.md` and `.pdf` plus the saved course's `INDEX.md` and `course.json`, and the root `README.md`. All of these are needed: without the course's `course.json` its index would list only the new lecture, and without the other courses' `course.json` files the root `README.md` would list only one course. If you could not fetch them, do not copy back `INDEX.md`, `course.json` or `README.md`; copy only the `.md` and `.pdf`, and tell the user to run `save_note.py --reindex` on the computer.
4. None of the above (plain cloud chat) → `<root>` = `./courses/`; at the end send the user the note's `.md` and `.pdf`. Mention that indexes only cover this session's notes unless they attach their existing `course.json`.

Then list existing courses:

```bash
python3 <skill>/scripts/save_note.py --list-courses --root <root>
```

Each line reads `folder | course name | N ders | son: Bölüm X - … / Ders Y - …` (the last saved lecture). If the lecture belongs to a listed course, use that course's name **exactly** as listed in the `course:` field. Different spellings create a second course folder.

## 2. Gather the inputs

The user should never have to remember a format. Collect what you can, offer what you can infer, and ask for the rest **once**.

| Input | Required | Notes |
|---|---|---|
| Transcript | Yes | Pasted text, an attached file, or a file in the Notlas `transcripts/` folder |
| Course name | Yes | Must match an existing course exactly, or be confirmed as new |
| Section number + title | Yes | `Bölüm 5 - App Router Temelleri`; decides the folder and prevents collisions |
| Lecture number + title | Yes | `Ders 23 - Server Components`; Udemy numbers lectures across the whole course |
| Course description | Only for a new course, optional | Context for terminology; pass it with `--course-description` on the first save; never copy it into the note |

**Where values come from**, in this order:
1. The user's message, in any form ("Kurs: …", "5. bölüm 23. ders", "Next.js kursunun sonraki dersi").
2. The transcript file name, when it follows `<course-key>_<section-no>-<lecture-no>.<ext>` (e.g. `nextjs_05-23.vtt`). Match `<course-key>` against the course folders and names from step 1.
3. The course overview from step 1: for the next lecture of a course, propose the same section as its last lecture and lecture number + 1.
4. The transcript itself: propose a lecture title from its main topic when the user gave none.

Then pick exactly one of these:

**A. No transcript and no details** (e.g. the user typed only `/notlas`): reply with this fill-in template and wait. Fill in the course list from step 1 (or write "Henüz kurs yok."), and do nothing else in this turn:

```
Kurs: <aşağıdakilerden biri ya da yeni kursun adı>
Bölüm: <numara> - <bölüm adı>
Ders: <numara> - <ders adı>
Kurs açıklaması: <yalnızca yeni kurs için, isteğe bağlı>

<transkripti buraya yapıştır ya da transcripts/ klasöründeki dosyanın adını yaz>
```

Mevcut kurslar:
- <course name> (son: Bölüm X - … / Ders Y - …)

Add one line: "Dosyayı `kurs_bölüm-ders.vtt` adıyla transcripts/ klasörüne koyarsan bilgileri dosya adından alırım."

**B. Transcript present, but course, section or lecture missing or uncertain**: ask **one** round of questions covering everything that is missing, with your inferences as the default choices:
- If an interactive question tool is available, use it: course as options (existing courses first; the most likely one first; plus "Yeni kurs"), and section/lecture as a proposed value (e.g. "Bölüm 5 - App Router Temelleri / Ders 24 - <önerilen başlık>") with an option to correct it.
- Otherwise send one short message listing the proposed values; the user answers "evet" or corrects them.
- If the course is new, include an optional "Kurs açıklaması" field in the same round, not as a separate question.
- Also include, in the same round, anything else that is genuinely unclear: lecture boundaries in a combined transcript, or a course name that nearly matches an existing one.
- Write user-facing questions in Turkish.

**C. Everything known** (from the message, the file name, or an unambiguous "next lecture" of an existing course): don't ask; proceed. In the final message, name any value you inferred.

Never ask more than one round. If the answer still leaves something open, choose the most likely value and say so in the final message. When the user is not present (scheduled or unattended run), don't ask at all: use the inferences and state them.

If the transcript is VTT/SRT or has timestamps, clean it first. Write intermediate files to a scratch location (Notlas project: `transcripts/`; otherwise a temp folder), never into `<root>`:

```bash
python3 <skill>/scripts/clean_transcript.py <input> > <scratch>/temiz.txt
```

**One transcript containing several lectures.** Split it on clear boundaries: the instructor closing a lecture ("bir sonraki derste…", "in the next lecture…"), a new welcome or intro, lecture titles, or a jump in timestamps back to 00:00. Write one note file per lecture, and number them consecutively.

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
course: "Course Name"
section: "Bölüm 3 - Section Title"
lecture: "Ders 12 - Lecture Title"
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
python3 <skill>/scripts/save_note.py <scratch>/note.md --root <root> [--course-description "..."]
```

Pass `--course-description` on a course's first save (or when it changes).

The script validates the note, places it at `<root>/<course-slug>/notes/<NN-section>/<NNN-lecture>.md`, renders `pdf/…/<NNN-lecture>.pdf`, and rebuilds the course `INDEX.md`, `course.json` and the root `README.md`. Indexes are rebuilt from `course.json` plus every note on disk, so re-saving never drops other lectures.

**If the script stops with an error, fix the cause rather than reaching for the bypass flag:**

| Error | What to do |
|---|---|
| note structure (heading misspelled/missing) | Fix the note's headings, then save again. `--skip-checks` is only for notes the user deliberately structured differently. |
| course does not exist yet, but similar courses do | Same course → copy the listed name into `course:` exactly. Truly different course → re-run with `--new-course`. |
| path already holds a different lecture / no `section:` | Add the correct `section:` (preferred). Use `--overwrite` only when you are deliberately replacing the same lecture. |

Re-saving a lecture with the same section and title updates it in place; this is expected.

**Moving or deleting a lecture** (e.g. its section was wrong): save it with the corrected `section:`. The script warns that the same lecture also exists in the old section folder. Delete the old `.md` and its `.pdf` (ask the user first if you cannot delete files), then run `--reindex --prune` for that course. Without `--prune`, the index keeps listing the old copy.

Other commands: `--reindex --root <root> [--course <slug>]` rebuilds indexes from the files on disk. Add `--prune` to drop entries whose note file no longer exists; only use it on the complete repository, never on a partial copy. `--no-pdf` saves Markdown only.

PDF rendering uses WeasyPrint, with a fallback to installed Chrome/Edge. On macOS, WeasyPrint needs `brew install pango`; without it the script falls back to Chrome automatically. If every engine fails, the script prints a `WARNING ... PDF not created (...)` line but still saves the Markdown and updates the indexes. Tell the user the PDF is missing and quote the reason.

## 5. Preview, check and show the result

Always show the result without being asked; the user should never have to request a preview.

1. **Render a preview image** of each saved PDF (cover and the first content pages side by side). Write it to the scratch location (Notlas project: `transcripts/`), never into `<root>`:
   ```bash
   python3 <skill>/scripts/preview.py <root>/<course>/pdf/<section>/<lecture>.pdf -o <scratch>/<lecture>-preview.png
   ```
   If it exits with code 2 (no rasterizer available), skip the image and run `pdftotext <pdf> - | head -40` instead to confirm the Turkish characters (ç ğ ı İ ö ş ü) come through.
2. **Look at the preview yourself** before showing it: text running off the page or overlapping, missing Turkish characters, broken code blocks or tables. If something is wrong, fix the note and save it again, then re-render the preview.
3. **Show it in the final reply**, using what the environment offers:
   - In a chat app with a tool for sending or presenting files to the user: send the preview PNG (it displays inline) and the PDF itself (so it opens in the viewer). For several lectures, send every PDF and the preview of the first one.
   - In Claude Code: print the absolute paths of the PDF and the preview, since the desktop app makes them clickable. On macOS, also open the PDF with `open "<pdf>"`, unless the user said not to.
   - If no preview could be made, still send or open the PDF.
4. **Reply in one or two sentences:** which lecture was saved, where, and the course's lecture count. Do not paste the note's content into the chat. If you made an assumption (course name, lecture split, missing section number), say so in one line.
