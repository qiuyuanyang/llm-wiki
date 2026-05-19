# LLM Wiki — Maintenance Manual

---

## Directory Structure

```
llm-wiki/                        ← Obsidian Vault root (open this directory)
├── LLM.md                       ← LLM Agent operating instructions (core — do not modify casually)
├── wiki_config.json             ← Active model configuration
├── wiki.sh                      ← Unified CLI entry point for all operations
│
├── wiki/                        ← LLM writes, you read
│   ├── index.md                 ← Content index (auto-updated on every ingest)
│   ├── log.md                   ← Operation log (append-only)
│   ├── overview.md              ← Global knowledge synthesis
│   ├── dashboard.md             ← Dataview dynamic dashboard
│   ├── entities/                ← People / organisations / products
│   ├── concepts/                ← Terms / theories / methods
│   ├── sources/                 ← Per-source summary pages (1 : 1 with raw/)
│   ├── queries/                 ← Archived high-value Q&A
│   └── comparisons/             ← Comparative analysis tables
│
├── raw/                         ← You place files; LLM reads (read-only — do not modify)
│   ├── sources/                 ← Source materials (placing files here triggers ingest)
│   ├── assets/                  ← Image attachments
│   └── clips/                   ← Obsidian Web Clipper output
│
├── templates/                   ← Obsidian Templater templates
└── scripts/                     ← Automation scripts
    ├── wiki_watcher.py          ← Daemon (watches raw/ and auto-processes new files)
    ├── ingest.sh                ← Manual ingest helper
    ├── stats.sh                 ← Statistics and health checks
    └── search.sh                ← Local full-text search
```

---

## First-Time Setup

**1. Open the project root as an Obsidian Vault** (not the `wiki/` subdirectory)

```
Obsidian → Open Vault → select llm-wiki/
```

`.obsidian/` is pre-configured: attachments → `raw/assets/`, templates → `templates/`, graph colours set.

**2. Install Obsidian plugins** (Settings → Community plugins)

| Plugin        | Purpose                          | Priority    |
|---------------|----------------------------------|-------------|
| **Dataview**  | Dynamic tables in `dashboard.md` | Required    |
| **Templater** | Quickly create conformant pages  | Required    |
| Obsidian Git  | Automatic backup                 | Recommended |

---

## Three Operating Modes

### Mode A: Manual (full control — best for important materials)

```bash
bash scripts/ingest.sh ~/Downloads/paper.pdf
# → Prints a prompt to copy-paste to your LLM Agent
```

### Mode B: Foreground (visible real-time processing logs)

```bash
./wiki.sh start
# Drop a file into raw/sources/ → auto-processed, terminal shows findings summary
```

### Mode C: Background daemon (fully automatic — recommended for daily use)

```bash
./wiki.sh daemon    # Start in background
./wiki.sh status    # Check status
./wiki.sh stop      # Stop daemon
```

Install dependencies (required for Mode B / C only):

```bash
pip install anthropic openai watchdog rich pdfplumber
```

---

## Core Operations

### INGEST — Process new source material

Tell your LLM Agent: `Please process raw/sources/xxx.md`

The LLM will: read → report 3–5 key findings → create summary page → update entity/concept pages → update `index.md` and `log.md`

### QUERY — Ask a question

Ask the LLM Agent directly. It will read `index.md` to find relevant pages, synthesise an answer, and ask whether to archive it to `wiki/queries/`.

### LINT — Health check

```bash
./wiki.sh lint
# Then tell your LLM Agent: "Please run a LINT health check"
```

---

## Model Configuration

Model configuration is stored in `wiki_config.json` and switched via `./wiki.sh model` — no code changes needed.

### Switch commands

```bash
./wiki.sh model                               # Show current model
./wiki.sh model anthropic,claude-opus-4-6    # Anthropic official
./wiki.sh model anthropic,claude-sonnet-4-6  # Faster and more cost-effective
./wiki.sh model local,Qwen3.6-35B-A3B-FP8   # Local Ollama / vLLM
./wiki.sh model dashscope,qwen-max           # Alibaba Cloud DashScope
./wiki.sh model openai,gpt-4o               # OpenAI
```

### Built-in Providers

| Provider    | API Endpoint                  | Credential env var      |
|-------------|-------------------------------|-------------------------|
| `anthropic` | Anthropic official            | `ANTHROPIC_API_KEY`     |
| `local`     | `http://localhost:11434/v1`   | None (Ollama default)   |
| `dashscope` | DashScope compatible endpoint | `DASHSCOPE_API_KEY`     |
| `openai`    | OpenAI official               | `OPENAI_API_KEY`        |

### Adding a custom provider

Edit `wiki_config.json`, add an entry under `providers`:

```json
"minimax": {
  "base_url": "https://api.minimax.chat/v1",
  "api_key_env": "MINIMAX_API_KEY"
}
```

Then `./wiki.sh model minimax,abab7-chat-preview` takes effect immediately.

---

## Link Conventions

The Vault root is the project root. Internal links must include the `wiki/` prefix:

```
Correct: [[wiki/entities/geoffrey-hinton|Geoffrey Hinton]]
Correct: [[wiki/concepts/attention-mechanism]]
Wrong:   [[entities/geoffrey-hinton]]
```

---

## Periodic Maintenance

| Frequency          | Action                                                              |
|--------------------|---------------------------------------------------------------------|
| Every new source   | `./wiki.sh ingest <file>` → paste prompt to LLM Agent             |
| Weekly             | `./wiki.sh lint` → ask LLM Agent to fix reported issues            |
| Monthly            | `./wiki.sh hotspot` → generate knowledge hotspot analysis           |

---

## Quick Reference

```bash
./wiki.sh ingest <file|URL>   # Import source material
./wiki.sh model [SPEC]        # View / switch model
./wiki.sh stats               # Wiki statistics
./wiki.sh lint                # Health check
./wiki.sh search "keyword"    # Search wiki
./wiki.sh hotspot             # Hotspot analysis
```
