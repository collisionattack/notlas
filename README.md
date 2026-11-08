# Notlas

**Turn course lecture transcripts into study notes you can read, and your AI agents can use.**

Notlas (*not* "note" + *atlas*) is a [Claude](https://claude.ai) skill. Give it the transcript of a Udemy (or any video course) lecture and it writes a structured study note, saved as an academic-style PDF for you and as Markdown in an indexed repository your coding agents can search.

![Sample note: cover, first page and a page with margin notes](docs/preview.png)

<sub>Full sample: [docs/sample.pdf](docs/sample.pdf)</sub>

## Features

- **Re-teaches, doesn't summarize.** Each note has a summary, topic sections, runnable code, a concept table, pitfalls and review questions. Notes are written in Turkish; technical terms keep their English original, and code is never translated.
- **Agent-ready repository.** Every course gets an `INDEX.md` listing each lecture's summary, topics and concepts, so an agent can find the right note and open only that file.
- **Academic PDF.** Tufte-style layout with a cover, table of contents, margin notes and highlighted code, with embedded fonts that cover all Turkish characters.
- **Nothing to remember.** `/notlas` alone returns a fill-in template; a bare transcript gets one round of questions with sensible defaults.
- **Safe by default.** Misspelled sections, near-duplicate course names and saves that would replace a different lecture are refused. Each save ends with a preview image of the result.

## Quick start

**Claude app (desktop)**

1. Download `notlas.zip` from the [latest release](https://github.com/mrttyyldrm/notlas/releases/latest) and upload it under **Customize → Skills → + → Create skill → Upload a skill**. Make sure code execution is enabled in **Settings → Capabilities**.
2. Clone this repository, then in a new chat attach the folder with **+ → Add folder**.
3. Type `/notlas` and follow the template.

**Claude Code**

```bash
git clone https://github.com/mrttyyldrm/notlas ~/notlas
ln -s ~/notlas ~/.claude/skills/notlas
cd ~/notlas && claude
```

## Usage

Pick whichever is easiest:

| You do | Notlas does |
|---|---|
| Type `/notlas` | Replies with a template listing your courses and the last lecture of each |
| Paste a transcript | Asks once for the missing course / section / lecture, proposing the next lecture |
| Save `nextjs_05-23.vtt` in `transcripts/` and say *notlaştır* ("make notes") | Reads course, section and lecture from the file name |

Or give everything at once:

```
Kurs: Docker ve Kubernetes                        # course
Bölüm 2 - Depolama / Ders 7 - Docker Volume'ları  # section / lecture
<transcript>
Bunu notlaştır.                                   # "turn this into notes"
```

## Output

```
courses/                              (git-ignored, stays on your machine)
├── README.md                         all courses
└── <course>/
    ├── INDEX.md                      every lecture: summary, topics, concepts, links
    ├── course.json                   the same, machine-readable
    ├── notes/<NN-section>/<NNN-lecture>.md
    └── pdf/<NN-section>/<NNN-lecture>.pdf
```

To use a course as a knowledge source in another project, add a line like this to that project's `CLAUDE.md`:

```markdown
For Next.js questions, check my course notes first: ~/notlas/courses/<course>/INDEX.md
```

## Requirements

Python 3.9+ with `markdown`, `pygments`, `weasyprint` and `pillow`. In the Claude app these are installed automatically when needed. For local use:

```bash
pip3 install markdown pygments weasyprint pillow
brew install pango poppler      # macOS: PDF rendering and previews
```

| Problem | Fix |
|---|---|
| "PDF not created" | Install `pango` (macOS) or Google Chrome; the Markdown note is saved either way |
| No preview image | Install `poppler` or `pip3 install pymupdf` |
| Notes land in an old folder | Re-upload the latest `notlas.zip`; older versions used other folder names |

## Development

| Command | Purpose |
|---|---|
| `scripts/save_note.py NOTE.md --root courses` | Validate, store, render and index a note |
| `scripts/save_note.py --list-courses` / `--reindex [--prune]` | Inspect or rebuild the indexes |
| `scripts/build_pdf.py NOTE.md -o out.pdf` | Render a single PDF |
| `scripts/preview.py out.pdf -o preview.png` | Cover and first pages as one image |
| `scripts/clean_transcript.py lecture.vtt` | VTT/SRT → plain paragraphs |

The PDF theme lives in `assets/themes/academic.css`; Claude's instructions are in `SKILL.md` and `CLAUDE.md`. See [CHANGELOG.md](CHANGELOG.md) for release notes. Issues and pull requests are welcome.

## License

Code is released under the [MIT License](LICENSE). Bundled fonts (EB Garamond, Inter, JetBrains Mono) are under the SIL Open Font License; see `assets/fonts/`.

Notes you create are derived from course material, so the copyright stays with the instructors: keep them private. Notlas is not affiliated with Udemy or Anthropic.
