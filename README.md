# LLM Wiki — Infrastructure Knowledge Base

A personal knowledge base for IT operations & infrastructure, built on the pattern established by Andrej Karpathy's [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

An LLM Agent automatically ingests raw source materials, maintains a structured wiki with vector embeddings, and answers questions by synthesizing knowledge across pages.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Workflows](#workflows)
- [New Features](#new-features)
- [Model Configuration](#model-configuration)
- [Environment Variables](#environment-variables)
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

# Generate vector embeddings (requires embedding model running)
./wiki.sh embed

# Ask a question
./wiki.sh query "What is the IP of web-server-01?"
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
├── config.py                  # Centralised config (env vars + JSON)
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
│   ├── infrastructure/        # Servers, switches, firewalls, databases, services
│   ├── sources/               # Per-source summary pages (1 : 1 with raw/)
│   ├── queries/               # Archived high-value Q&A
│   ├── comparisons/           # Comparative analyses
│   └── topology.html          # Interactive D3 topology graph (generated)
│
├── raw/                       # Source materials (read-only — never modified by LLM)
│   ├── sources/               # Drop files here to trigger ingest
│   ├── assets/                # Images and attachments
│   └── clips/                 # Obsidian Web Clipper output
│
├── diagnoses/                 # Fault diagnosis knowledge base
│
├── templates/                 # Obsidian Templater templates
│   ├── infrastructure-template.md  # NEW: Infrastructure component template
│   └── ...
│
├── scripts/                   # Automation tools
│   ├── wiki_watcher.py        # Daemon process (watches raw/ and auto-ingests)
│   ├── vector_ingest.py       # NEW: Generate vector embeddings for wiki pages
│   ├── query_engine.py        # NEW: Intelligent Q&A (vector search + LLM)
│   ├── graph_viz.py           # NEW: D3 topology graph generator
│   ├── diagnosis_engine.py    # NEW: Fault diagnosis knowledge engine
│   ├── ingest.sh              # Manual ingest helper
│   ├── stats.sh               # Statistics and health checks
│   └── search.sh              # Local full-text search
│
├── vector_store.py            # SQLite-backed vector storage
├── embedding_client.py        # OpenAI-compatible embedding API client
└── config.py                  # Centralised configuration (env vars / JSON)
```

---

## Workflows

| Action  | You do                                           | LLM does                                                    |
|---------|--------------------------------------------------|-------------------------------------------------------------|
| Ingest  | `./wiki.sh ingest <file>` or tell the LLM Agent | Reads, distils, updates 10-15 pages                         |
| Query   | Ask the LLM Agent a question                     | Reads index → dives into relevant pages → synthesises answer; optionally archives |
| Lint    | `./wiki.sh lint` → paste report to LLM Agent    | Checks for contradictions, orphaned pages, broken links, stale content |

---

## New Features

### 🔍 Vector Search & Intelligent Q&A

Semantic search powered by embedding models (e.g. Qwen3-Embedding-8B). Find relevant pages by meaning, not just keywords.

```bash
# Generate embeddings for all wiki pages
./wiki.sh embed

# Ask a question — vector search + LLM synthesis
./wiki.sh query "How to configure MySQL master-slave replication?"

# Vector search only (no LLM)
./wiki.sh search-v "firewall rules"
```

### 📊 Infrastructure Topology Graph

Interactive D3 force-directed graph showing dependencies between infrastructure components.

```bash
./wiki.sh graph
# Opens wiki/topology.html in browser
```

### 🔧 Fault Diagnosis Engine

Extract and search problem → cause → solution triples from your documentation.

```bash
# Scan sources for diagnosis triples
./wiki.sh diagnose scan

# Search for a specific issue
./wiki.sh diagnose search "MySQL replication lag"

# List all diagnoses
./wiki.sh diagnose list

# Show statistics
./wiki.sh diagnose stats
```

### 🌐 Web UI

Browse, search, and query the wiki through a web browser.

```bash
./wiki.sh web              # Start web UI on port 5000
./wiki.sh web --port 8080  # Custom port
```

Features:
- 📊 Dashboard with statistics
- 🔍 Semantic search
- 🤖 Intelligent Q&A
- 🔧 Fault diagnosis browser
- 📊 Interactive topology graph

### 🏗️ Infrastructure Entity Support

New page type for servers, switches, firewalls, databases, services, storage, and monitors. Each component gets its own page with dependencies, IP addresses, and configuration summaries.

Template: `templates/infrastructure-template.md`

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

## Environment Variables

All model endpoints and API keys are configured via environment variables — **no secrets are hard-coded**.

### Embedding Model

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_API_BASE_URL` | `http://localhost:8000/v1` | OpenAI-compatible embedding endpoint |
| `EMBEDDING_MODEL` | `Alibaba-NLP/Qwen3-Embedding-0.6B` | Embedding model name |
| `EMBEDDING_API_KEY` | (none) | API key for embedding service |
| `EMBEDDING_DIM` | `1024` | Embedding vector dimension |

### LLM Model

| Variable | Default | Description |
|---|---|---|
| `LLM_API_BASE_URL` | `http://localhost:8000/v1` | OpenAI-compatible LLM endpoint |
| `LLM_MODEL` | `Qwen/Qwen3-32B` | LLM model for INGEST/QUERY/LINT |
| `LLM_API_KEY` | (none) | API key for LLM service |

### Other

| Variable | Default | Description |
|---|---|---|
| `WIKI_ROOT` | `.` (current directory) | Path to wiki root |

You can also configure embedding and LLM settings in `wiki_config.json`:

```json
{
  "embedding": {
    "api_base_url": "http://localhost:8000/v1",
    "model": "Alibaba-NLP/Qwen3-Embedding-0.6B",
    "dimension": 1024
  },
  "llm": {
    "api_base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen3-32B"
  }
}
```

Environment variables take precedence over `wiki_config.json`.

---

## Scripts Reference

```bash
./wiki.sh daemon             # Start background daemon (fully automatic mode)
./wiki.sh start              # Start foreground watcher (real-time logs visible)
./wiki.sh stop               # Stop background daemon
./wiki.sh status             # Show running status and active model
./wiki.sh hotspot            # Generate hotspot analysis immediately
./wiki.sh ingest <file|URL>  # Manually import a source into raw/sources/
./wiki.sh stats              # Show wiki statistics
./wiki.sh lint               # Run health check
./wiki.sh search <keyword>   # Full-text search across wiki
./wiki.sh model [SPEC]       # View or switch the active model

# New commands
./wiki.sh embed              # Generate embeddings for all wiki pages
./wiki.sh reindex            # Full reindex: clear vectors and regenerate
./wiki.sh query <question>   # Intelligent Q&A (vector search + LLM)
./wiki.sh search-v <keyword> # Vector search only (no LLM)
./wiki.sh graph              # Generate topology graph (HTML)
./wiki.sh diagnose <cmd>     # Diagnosis engine (scan/search/list/stats)
./wiki.sh web [--port PORT]   # Start web UI (default port 5000)
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
