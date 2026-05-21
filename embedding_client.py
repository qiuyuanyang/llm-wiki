#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
embedding_client.py — Client for embedding model API.

Supports OpenAI-compatible embedding endpoints (vLLM, Ollama, etc.).
All configuration comes from config.py (env vars / wiki_config.json).
"""

import os
import json
import time
from typing import List, Optional
from config import WikiConfig


class EmbeddingClient:
    """OpenAI-compatible embedding API client."""

    def __init__(self, config: Optional[WikiConfig] = None):
        self.config = config or WikiConfig()
        self.api_base_url = self.config.embedding.api_base_url.rstrip("/")
        self.model = self.config.embedding.model
        self.api_key = self.config.embedding.api_key or os.getenv("EMBEDDING_API_KEY", "none")
        self.dimension = self.config.embedding.dimension
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise RuntimeError(
                    "openai package required: pip install openai"
                )

            kwargs = {"api_key": self.api_key, "max_retries": 2}
            if self.api_base_url:
                kwargs["base_url"] = self.api_base_url

            # Force NO_PROXY for local addresses
            from urllib.parse import urlparse
            host = urlparse(self.api_base_url).hostname or ""
            _local_prefixes = ("127.", "10.", "192.168.", "172.", "localhost", "::1")
            if any(host == p or host.startswith(p) for p in _local_prefixes):
                existing = os.environ.get("NO_PROXY", "")
                if host not in existing:
                    os.environ["NO_PROXY"] = f"{existing},{host},localhost,127.0.0.1".lstrip(",")
                    os.environ["no_proxy"] = os.environ["NO_PROXY"]

            self._client = openai.OpenAI(**kwargs)
        return self._client

    def embed(self, texts: List[str], show_progress: bool = False) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Handles batching: API typically limits to ~2048 inputs per call.
        """
        if not texts:
            return []

        client = self._get_client()
        all_embeddings = []
        batch_size = 32  # conservative batch size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if show_progress:
                print(f"  Embedding batch {i // batch_size + 1} "
                      f"({len(batch)} texts)...")

            resp = client.embeddings.create(
                model=self.model,
                input=batch,
            )

            for emb in resp.data:
                all_embeddings.append(emb.embedding)

        return all_embeddings

    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed([text])[0]

    def health_check(self) -> bool:
        """Check if embedding service is reachable."""
        try:
            self.embed(["health check"])
            return True
        except Exception:
            return False
