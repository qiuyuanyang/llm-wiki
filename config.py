#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
config.py — Centralised configuration for LLM Wiki.

All model endpoints, API keys, and operational settings are loaded from
environment variables or wiki_config.json.  No secrets are hard-coded.

Environment variables (all optional — sensible defaults are provided):
    EMBEDDING_API_BASE_URL   — OpenAI-compatible embedding endpoint
                               (default: http://localhost:8000/v1)
    EMBEDDING_MODEL          — embedding model name
                               (default: Alibaba-NLP/Qwen3-Embedding-0.6B)
    EMBEDDING_API_KEY        — API key for embedding service (if required)
    EMBEDDING_DIM            — embedding vector dimension
                               (default: 1024)
    LLM_API_BASE_URL         — OpenAI-compatible LLM endpoint
                               (default: http://localhost:8000/v1)
    LLM_MODEL                — LLM model name for INGEST/QUERY/LINT
                               (default: Qwen/Qwen3-32B)
    LLM_API_KEY              — API key for LLM service (if required)
    WIKI_ROOT                — path to wiki root (default: current directory)
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    api_base_url: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_API_BASE_URL", "http://localhost:8000/v1")
    )
    model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-8B")
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("EMBEDDING_API_KEY")
    )
    dimension: int = field(
        default_factory=lambda: int(os.getenv("EMBEDDING_DIM", "4096"))
    )


@dataclass
class LLMConfig:
    """LLM model configuration for INGEST / QUERY / LINT."""
    api_base_url: str = field(
        default_factory=lambda: os.getenv("LLM_API_BASE_URL", "http://localhost:8000/v1")
    )
    model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "Qwen3.6-35B-A3B-FP8")
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("LLM_API_KEY")
    )


@dataclass
class WikiConfig:
    """Top-level wiki configuration."""
    root: Path = field(
        default_factory=lambda: Path(os.getenv("WIKI_ROOT", ".")).resolve()
    )
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    def __post_init__(self):
        # Override with wiki_config.json if it exists and has relevant fields
        json_path = self.root / "wiki_config.json"
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                # Merge embedding config from json if present
                emb = data.get("embedding", {})
                if emb:
                    if "api_base_url" in emb:
                        self.embedding.api_base_url = emb["api_base_url"]
                    if "model" in emb:
                        self.embedding.model = emb["model"]
                    if "api_key" in emb:
                        self.embedding.api_key = emb["api_key"]
                    if "dimension" in emb:
                        self.embedding.dimension = int(emb["dimension"])
                # Merge LLM config from json if present
                llm = data.get("llm", {})
                if llm:
                    if "api_base_url" in llm:
                        self.llm.api_base_url = llm["api_base_url"]
                    if "model" in llm:
                        self.llm.model = llm["model"]
                    if "api_key" in llm:
                        self.llm.api_key = llm["api_key"]
            except (json.JSONDecodeError, KeyError, ValueError):
                pass  # Fall back to env vars / defaults

    @property
    def wiki_root(self) -> Path:
        """Alias for root — used by legacy scripts."""
        return self.root

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

    @property
    def raw_dir(self) -> Path:
        return self.root / "raw" / "sources"

    @property
    def diagnoses_dir(self) -> Path:
        return self.root / "diagnoses"

    @property
    def infrastructure_dir(self) -> Path:
        return self.root / "wiki" / "infrastructure"

    @property
    def index_md(self) -> Path:
        return self.wiki_dir / "index.md"

    @property
    def log_md(self) -> Path:
        return self.wiki_dir / "log.md"

    @property
    def overview_md(self) -> Path:
        return self.wiki_dir / "overview.md"

    @property
    def state_file(self) -> Path:
        return self.root / ".wiki_watcher_state.json"

    @property
    def pid_file(self) -> Path:
        return self.root / ".wiki_watcher.pid"

    @property
    def vector_db_path(self) -> Path:
        return self.root / ".wiki_vectors.db"

    def ensure_dirs(self):
        """Create required directories if they don't exist."""
        for d in [self.wiki_dir, self.raw_dir, self.diagnoses_dir,
                  self.infrastructure_dir,
                  self.wiki_dir / "entities", self.wiki_dir / "concepts",
                  self.wiki_dir / "sources", self.wiki_dir / "queries",
                  self.wiki_dir / "comparisons"]:
            d.mkdir(parents=True, exist_ok=True)
