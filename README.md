# LLM Wiki

A personal knowledge base built on the pattern established by Andrej Karpathy's [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

An LLM Agent automatically ingests raw source materials, maintains a structured wiki, and answers questions by synthesizing knowledge across pages.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Workflows](#workflows)
- [Model Configuration](#model-configuration)
- [Scripts Reference](#scripts-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

```bash
# 1. Clone the repo and open the project root as an Obsidian Vault (not wiki/)
# 2. Place raw source materials into raw/sources/
# 3. Start the watcher daemon (auto-processes new files)
./wiki.sh daemon

# Or ingest a single file manually
./wiki.sh ingest ~/Downloads/paper.pdf
```

Install Python dependencies (required for daemon / foreground modes):

```bash
pip install anthropic openai watchdog rich pdfplumber
```

Full usage details are in [`tips.md`](tips.md).

---

## Directory Structure

```
.
├── LICENSE                    # MIT License
├── README.md                  # This file
├── wiki_config.json           # Model configuration (provider / model selection)
├── wiki.sh                    # Unified CLI entry point
├── tips.md                    # Full maintenance manual
├── LLM.md                     # LLM Agent operating instructions (auto-loaded)
│
├── wiki/                      # LLM-generated content (treat as read-only)
│   ├── index.md               # Content index — updated on every ingest
│   ├── log.md                 # Operation log (append-only)
│   ├── overview.md            # Global knowledge synthesis
│   ├── dashboard.md           # Dataview dynamic dashboard
│   ├── entities/              # People, organisations, products
│   ├── concepts/              # Terms, theories, methods
│   ├── sources/               # Per-source summary pages (1 : 1 with raw/)
│   ├── queries/               # Archived high-value Q&A
│   └── comparisons/           # Comparative analyses
│
├── raw/                       # Source materials (read-only — never modified by LLM)
│   ├── sources/               # Drop files here to trigger ingest
│   ├── assets/                # Images and attachments
│   └── clips/                 # Obsidian Web Clipper output
│
├── templates/                 # Obsidian Templater templates
└── scripts/                   # Automation tools
    ├── wiki_watcher.py        # Daemon process (watches raw/ and auto-ingests)
    ├── ingest.sh              # Manual ingest helper
    ├── stats.sh               # Statistics and health checks
    └── search.sh              # Local full-text search
```

---

## Workflows

| Action  | You do                                           | LLM does                                                    |
|---------|--------------------------------------------------|-------------------------------------------------------------|
| Ingest  | `./wiki.sh ingest <file>` or tell the LLM Agent | Reads, distils, updates 10-15 pages                         |
| Query   | Ask the LLM Agent a question                     | Reads index → dives into relevant pages → synthesises answer; optionally archives |
| Lint    | `./wiki.sh lint` → paste report to LLM Agent    | Checks for contradictions, orphaned pages, broken links, stale content |

---

## Model Configuration

Switch the active model at any time — no code changes needed:

```bash
./wiki.sh model local,Qwen3.6-35B-A3B-FP8     # Local Ollama / vLLM
./wiki.sh model dashscope,qwen-max             # Alibaba Cloud DashScope
./wiki.sh model anthropic,claude-sonnet-4-6   # Anthropic (default)
./wiki.sh model openai,gpt-4o                 # OpenAI

# Start daemon and set model in one command
./wiki.sh daemon model local,Qwen3.6-35B-A3B-FP8
```

Configuration is persisted in `wiki_config.json`. Add a custom provider by editing the `providers` object:

```json
"minimax": {
  "base_url": "https://api.minimax.chat/v1",
  "api_key_env": "MINIMAX_API_KEY"
}
```

### Built-in Providers

| Provider    | API Endpoint                  | Credential env var      |
|-------------|-------------------------------|-------------------------|
| `anthropic` | Anthropic official            | `ANTHROPIC_API_KEY`     |
| `local`     | `http://localhost:11434/v1`   | None (Ollama default)   |
| `dashscope` | DashScope compatible endpoint | `DASHSCOPE_API_KEY`     |
| `openai`    | OpenAI official               | `OPENAI_API_KEY`        |

---

## Scripts Reference

```bash
./wiki.sh daemon             # Start background daemon (fully automatic)
./wiki.sh start              # Start foreground watcher (real-time logs)
./wiki.sh stop               # Stop background daemon
./wiki.sh status             # Show running status and active model
./wiki.sh hotspot            # Generate hotspot analysis immediately
./wiki.sh ingest <file|URL>  # Manually import a source into raw/sources/
./wiki.sh stats              # Show wiki statistics
./wiki.sh lint               # Run health check
./wiki.sh search <keyword>   # Full-text search across wiki
./wiki.sh model [SPEC]       # View or switch the active model
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Follow the existing code style and keep shell scripts POSIX-compatible where possible.
3. Submit a pull request with a clear description of the change.

Bug reports and feature requests are welcome via GitHub Issues.

---

## License

This project is released under the [MIT License](LICENSE).
