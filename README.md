# PM Doc Pipeline

**Curated Doc-as-Code pipeline for Product Managers.**

Stage the documents that matter, convert them to clean Markdown, and let VS Code Copilot search your knowledge base. Everything runs locally — no GPUs, no cloud AI, no data leaves your machine.

---

## Philosophy: You Curate, Pipeline Formats

This is **not** a data warehouse. It's a focused knowledge base.

- **You pick** the 10-50 documents that matter right now (a PRD, a sprint deck, key meeting notes)
- **Pipeline converts** them to clean, searchable Markdown with metadata
- **Copilot searches** a tight, high-signal set it can actually reason about

Remote sources (Confluence, GitHub) produce **metadata catalogs** — searchable indexes with links back to the source of truth — not full content copies that go stale.

---

## Quick Start

```bash
# 1. Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# 2. Stage some documents
pm-pipeline add ~/docs/sprint-deck.pptx
pm-pipeline add ~/docs/prd-v2.docx
pm-pipeline add ~/docs/meeting-notes.pdf

# 3. Run
pm-pipeline run

# 4. Open output/ in VS Code → Copilot can now search everything
```

---

## Architecture

```
  You stage files ──→  pm-pipeline add <file>
                              │
       ┌──────────────────────▼──────────────────────┐
       │          STAGE 1: DATA HARVESTER            │
       │  Staged local files + remote catalogs       │
       └──────────────────────┬──────────────────────┘
                              │ raw/
       ┌──────────────────────▼──────────────────────┐
       │       STAGE 2: UNIVERSAL TRANSLATOR         │
       │  PDF · DOCX · PPTX · HTML → Markdown        │
       └──────────────────────┬──────────────────────┘
                              │ processed/
       ┌──────────────────────▼──────────────────────┐
       │           STAGE 3: THE ENGINE               │
       │  Git diffs · Ticket mapping · Decisions      │
       └──────────────────────┬──────────────────────┘
                              │
       ┌──────────────────────▼──────────────────────┐
       │          STAGE 4: THE PUBLISHER             │
       │  Flat workspace + PROJECT_CONTEXT.md         │
       └──────────────────────┬──────────────────────┘
                              │
                              ▼
                     output/
                       PROJECT_CONTEXT.md   ← Copilot reads this first
                       DECISION_LOG.md
                       CHANGELOG.md
                       docs/                ← Your processed documents
                       catalogs/            ← Confluence/GitHub indexes
```

---

## CLI Commands

| Command | What It Does |
|---|---|
| `pm-pipeline add <file> [file...]` | Stage document(s) for processing |
| `pm-pipeline remove <file>` | Remove a document from staging |
| `pm-pipeline list` | Show all staged files |
| `pm-pipeline run` | Run all 4 pipeline stages |
| `pm-pipeline run -s translate -s publish` | Run specific stages |
| `pm-pipeline status` | Show file counts and pipeline state |
| `pm-pipeline init` | Create project directories |

### Typical daily workflow

```bash
# Morning: stage today's documents
pm-pipeline add ~/Downloads/standup-notes.docx
pm-pipeline add ~/Downloads/q3-roadmap.pptx

# Process
pm-pipeline run

# Open VS Code, ask Copilot:
#   "What decisions were made about the auth feature?"
#   "Summarize the Q3 roadmap"
#   "What tickets are referenced in today's standup notes?"
```

---

## How Each Stage Works

### Stage 1: Data Harvester

**Local files** — Only files you explicitly `pm-pipeline add` get processed. No auto-discovery, no watch-everything.

**Confluence** (optional) — Produces a **metadata catalog**: a searchable Markdown table with page titles, labels, authors, dates, and links back to Confluence. Only pages you "pin" by ID get full content downloaded.

**GitHub** (optional) — Produces a **catalog** of issues/PRs. Only label-matched items get full body + comments.

**Webex** (optional) — Downloads transcripts for specific meeting IDs you provide.

### Stage 2: Universal Translator

Converts every raw file to Markdown with YAML frontmatter:

| Input | Library | Output |
|---|---|---|
| PDF | pdfplumber (layout-aware) or PyMuPDF (fast) | Markdown with page breaks |
| DOCX | python-docx | Markdown preserving headings, lists, tables |
| PPTX | python-pptx | Markdown with slide-by-slide structure |
| HTML | markdownify | Clean Markdown (handles Confluence format) |
| JSON | built-in | Structured Markdown (GitHub issues/PRs) |
| VTT | built-in | Readable transcript with speaker labels |

### Stage 3: The Engine

All rule-based, deterministic, no AI:

- **Change Tracking** — GitPython diffs `processed/` against last commit
- **Ticket Extraction** — Regex patterns find JIRA-123, #456, etc.
- **Decision Detection** — Keyword matching ("decided", "approved", "action item") + context extraction
- **Changelog** — Groups changes by source, date, or ticket

### Stage 4: The Publisher

- Copies processed docs into flat `output/docs/`
- Writes `DECISION_LOG.md` and `CHANGELOG.md` at top level
- Generates `PROJECT_CONTEXT.md` — **the single file that ties everything together**

---

## PROJECT_CONTEXT.md — Why It Matters

`PROJECT_CONTEXT.md` is the file Copilot finds first. It contains:

- **Document inventory** — every processed file with title and source
- **All decisions** — extracted inline with context and ticket refs
- **Ticket references** — every ticket number found across all documents
- **Recent changes** — what changed in the latest pipeline run

When you open this file in VS Code, Copilot has a complete map of your knowledge base in one context window.

---

## Remote Sources: Catalogs, Not Copies

For a large enterprise, copying Confluence spaces locally is wrong — it creates stale duplicates and overwhelms Copilot.

Instead, the pipeline produces **catalogs**:

```markdown
## Space: PM

| Title              | Labels        | Last Modified | Author    | Link          |
|--------------------|---------------|---------------|-----------|---------------|
| Q3 Roadmap         | roadmap       | 2024-03-15    | Jane Doe  | [Open](url)   |
| Auth Feature PRD   | prd, specs    | 2024-03-10    | John Doe  | [Open](url)   |
```

Copilot can search this table to answer "where is the doc about X?" and give you the link. The source of truth stays in Confluence.

For the few pages you **need** locally (e.g., the active PRD), use `pinned_page_ids` in the config.

---

## Configuration

All settings live in `config/pipeline.yaml`. For remote sources, credentials go in `.env`:

```bash
cp config/.env.example .env
# Edit .env with your tokens
```

Key config sections:

| Section | What to edit |
|---|---|
| `sources.confluence.spaces` | Space keys + label filters for the catalog |
| `sources.confluence.pinned_page_ids` | Specific pages to download fully |
| `sources.github.repos` | Repos + label filters |
| `sources.webex.meeting_ids` | Specific meetings to transcribe |
| `engine.ticket_patterns` | Regex for your ticket system (JIRA, GitHub, etc.) |
| `engine.decision_keywords` | Words that signal decisions |

---

## Library Stack

All offline, CPU-only, actively maintained:

| Category | Library | Why |
|---|---|---|
| PDF parsing | pdfplumber | Best layout-aware extraction; handles tables |
| PDF (fast mode) | PyMuPDF | 10-50x faster for simple text; configurable |
| Word parsing | python-docx | De facto standard; headings, tables, styles |
| PowerPoint | python-pptx | Only serious .pptx library; slides, shapes, tables |
| HTML → Markdown | markdownify | Clean, configurable; handles Confluence HTML |
| Confluence API | atlassian-python-api | Most complete Atlassian client; Cloud + Server |
| GitHub API | PyGithub | Mature; issues, PRs, labels, comments |
| Webex API | webexpythonsdk | Official community SDK; transcripts, messages |
| Config | PyYAML + pydantic | YAML parsing + optional schema validation |
| Git operations | GitPython | Change detection via diffs; no C deps |
| CLI | Click | Clean composable commands; Pallets project |

---

## Security & Privacy

- All document parsing runs locally (pdfplumber, python-docx, python-pptx, markdownify)
- Zero AI/LLM calls — all analysis is regex + keyword matching
- API credentials stay in `.env` (gitignored)
- Remote source raw data is gitignored
- The only network calls are to APIs you explicitly enable

---

## License

MIT
