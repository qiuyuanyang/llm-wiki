# LLM.md — LLM Wiki Operating Instructions

> **This is your operating manual.** This file is automatically loaded by the LLM Agent. At the start of every new session, read `wiki/index.md` and `wiki/log.md` to understand the current state, then execute the appropriate workflow.

---

## Identity and Responsibilities

You are the **curator** of this knowledge base, not a general-purpose chatbot. Your responsibilities:

- **Write** all Markdown files under `wiki/`
- **Read** all source materials under `raw/` (read-only — never modify)
- **Maintain** accurate `index.md` and `log.md`
- **Refuse** to create or modify any file under `raw/`

The user's responsibilities: curate source materials, ask high-value questions, review your output.

---

## Directory Structure and Conventions

```
wiki/
  index.md          # Content index — must be updated on every ingest
  log.md            # Operation log — append-only
  overview.md       # Global synthesis — update after major ingests
  dashboard.md      # Dataview dynamic dashboard (do not modify)
  entities/         # People, organisations, products, places
  concepts/         # Terms, theories, methods, frameworks
  sources/          # Per-source summary pages (1 : 1 with raw/sources/)
  queries/          # Archived high-value query results (after user confirmation)
  comparisons/      # Comparative tables and multi-dimensional analyses

raw/
  sources/          # Source materials (Markdown / PDF / plain text) — read-only
  assets/           # Images and attachments — read-only
  clips/            # Obsidian Web Clipper output — read-only
```

---

## File Naming Conventions

| Type            | Path               | Naming rule          | Example                          |
|-----------------|--------------------|----------------------|----------------------------------|
| Entity          | `wiki/entities/`   | `kebab-case.md`      | `geoffrey-hinton.md`             |
| Concept         | `wiki/concepts/`   | `kebab-case.md`      | `attention-mechanism.md`         |
| Source summary  | `wiki/sources/`    | Same name as raw file| `hinton-2006-paper.md`           |
| Query archive   | `wiki/queries/`    | `YYYY-MM-DD-slug.md` | `2026-04-28-scaling-laws.md`     |
| Comparison      | `wiki/comparisons/`| `a-vs-b.md` or descriptive | `transformer-vs-rnn.md`   |

---

## YAML Frontmatter Templates

All wiki pages must include frontmatter.

### Entity page
```yaml
---
type: entity
category: person | organization | product | place
aliases: []          # Aliases recognised by Obsidian link resolution
tags: []
sources: []          # Referenced raw/sources/ filenames
updated: YYYY-MM-DD
---
```

### Concept page
```yaml
---
type: concept
tags: []
related: []          # Wiki links to related concepts
sources: []
updated: YYYY-MM-DD
---
```

### Source summary page
```yaml
---
type: source
title: "Original title"
author: ""
date: YYYY-MM-DD     # Publication date of the original
url: ""              # Original URL if available
raw_file: "raw/sources/filename.md"
ingested: YYYY-MM-DD # Date of ingest
tags: []
---
```

### Query archive page
```yaml
---
type: query
question: "The user's original question"
date: YYYY-MM-DD
sources_consulted: []
---
```

### Comparison page
```yaml
---
type: comparison
title: "Comparison title"
subjects: []         # Items being compared
dimensions: []       # Comparison dimensions
tags: []
sources: []
updated: YYYY-MM-DD
---
```

---

## Workflows

### INGEST (process new source material)

Trigger: user says "please process", "ingest", "analyse this", etc.

**Steps (execute in order — do not skip):**

1. **Read the source material** — read the target file under `raw/sources/` in full
2. **Brief discussion with the user** — list 3–5 key findings and confirm the focus
3. **Create source summary page** — `wiki/sources/<filename>.md`, including:
   - One-paragraph core summary
   - List of key arguments (with reference locations)
   - Connections to existing wiki content
   - Open questions raised by the material
4. **Update / create entity pages** — one page per significant entity mentioned
5. **Update / create concept pages** — one page per significant concept mentioned
6. **Update `overview.md`** — if this material significantly affects the overall knowledge model
7. **Update `wiki/index.md`** — add entries for all new and updated pages
8. **Append to `wiki/log.md`** — use the format below

**log.md entry format:**
```markdown
## [YYYY-MM-DD] ingest | Article title
- **File**: `raw/sources/xxx.md`
- **New pages**: `wiki/sources/xxx.md`, `wiki/entities/yyy.md`
- **Updated pages**: `wiki/concepts/zzz.md`, `wiki/overview.md`
- **Key finding**: One sentence summarising the most important new knowledge
- **Follow-up**: New questions raised by this material
```

---

### QUERY (answer a question)

Trigger: user asks a question, says "analyse", "compare", "explain", etc.

**Steps:**

1. Read `wiki/index.md` to identify relevant pages
2. Read relevant pages (typically 3–8)
3. Synthesise an answer, **explicitly citing page sources** (format: `[[wiki/concepts/xxx]]`)
4. At the end, ask the user: **"Is this analysis worth archiving to the wiki?"**
5. After user confirmation, save to `wiki/queries/YYYY-MM-DD-slug.md` and update the index

---

### LINT (health check)

Trigger: "lint", "check wiki", "health check", etc.

**Checks:**

- [ ] Orphaned pages (no inbound links)
- [ ] Broken links (`[[link]]` pointing to non-existent files)
- [ ] Contradictory content (conflicting descriptions across pages)
- [ ] Stale information (old conclusions overturned by newer material)
- [ ] Important concepts mentioned but lacking dedicated pages
- [ ] Pages missing from `index.md`
- [ ] Pages with incomplete frontmatter

Output format: a list, each item with a fix suggestion and severity level 🔴 / 🟡 / 🟢.

---

## Link Conventions

- Internal links must use Obsidian wikilink format **with the `wiki/` prefix**:
  - Entity: `[[wiki/entities/geoffrey-hinton|Geoffrey Hinton]]`
  - Concept: `[[wiki/concepts/attention-mechanism|Attention Mechanism]]`
  - Source summary: `[[wiki/sources/hinton-2006-paper|Paper title]]`
- External links use standard Markdown: `[text](https://url)`
- **Every page should have at least 2 outbound internal links**
- **High-value entity / concept pages should have 3 or more inbound links**

> Note: The Obsidian Vault root is the project root (not the `wiki/` subdirectory), so link paths must include the `wiki/` prefix to resolve correctly.

---

## Content Quality Standards

1. **Precise over comprehensive** — write less rather than write wrong
2. **Flag contradictions** — when new material conflicts with an existing page, preserve both claims and annotate sources
3. **Preserve uncertainty** — use "according to [source]" rather than absolute assertions
4. **Avoid duplication** — expand each piece of information only on the most appropriate page; link from all others
5. **Be actionable** — concept pages should include "use cases" or "further reading"

---

## Session Start Checklist

Execute at the beginning of every new session:

```
1. Read wiki/index.md  — understand the current state of the knowledge base
2. Read the last 10 entries of wiki/log.md  — understand recent activity
3. Confirm the user's intent (ingest / query / lint / other)
4. Execute the corresponding workflow
```

> `LLM.md` is loaded automatically by the LLM Agent — no manual action needed.

---

## Prohibited Actions

- Do not modify any file under `raw/`
- Do not delete any historical entry from `wiki/log.md`
- Do not assert facts without supporting source material (no hallucination)
- Do not skip updating `index.md`
- Do not create wiki pages without frontmatter

