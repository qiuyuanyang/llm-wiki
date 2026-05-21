#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
vector_ingest.py — Generate embeddings for wiki pages and store in vector store.

Called automatically after each INGEST to keep the vector index up-to-date.
"""

import hashlib
import re
import sys
from pathlib import Path
from typing import List, Dict

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig
from vector_store import VectorStore
from embedding_client import EmbeddingClient


def _extract_text_content(file_path: Path) -> str:
    """Extract readable text from a wiki markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1")

    # Strip YAML frontmatter
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    # Strip markdown links but keep text
    content = re.sub(r'\[\[([^\]|]+)(\|[^\]]+)?\]\]', r'\1', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    # Strip headers to plain text
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    return content.strip()


def _page_type_from_path(file_path: Path, wiki_root: Path) -> str:
    """Infer page type from file path."""
    rel = str(file_path.relative_to(wiki_root))
    if rel.startswith("wiki/entities/"):
        return "entity"
    if rel.startswith("wiki/concepts/"):
        return "concept"
    if rel.startswith("wiki/sources/"):
        return "source"
    if rel.startswith("wiki/infrastructure/"):
        return "infrastructure"
    if rel.startswith("wiki/queries/"):
        return "query"
    if rel.startswith("wiki/comparisons/"):
        return "comparison"
    if rel.startswith("diagnoses/"):
        return "diagnosis"
    return "page"


def _title_from_path(file_path: Path) -> str:
    """Extract title from file path."""
    return file_path.stem.replace("-", " ").replace("_", " ").title()


def ingest_page(file_path: Path, config: WikiConfig,
                embedding_client: EmbeddingClient) -> bool:
    """Generate embedding for a single wiki page and store it."""
    store = VectorStore(config)
    content = _extract_text_content(file_path)
    if not content:
        return False

    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
    page_path = str(file_path.relative_to(config.root))
    page_type = _page_type_from_path(file_path, config.root)
    title = _title_from_path(file_path)

    vector = embedding_client.embed_single(content)
    store.upsert_vector(page_path, page_type, title, content_hash, vector)
    return True


def ingest_all(config: WikiConfig, embedding_client: EmbeddingClient,
               show_progress: bool = True) -> Dict:
    """Generate embeddings for all wiki pages."""
    store = VectorStore(config)
    pages = list(config.wiki_dir.rglob("*.md"))
    pages += list(config.diagnoses_dir.glob("*.md")) if config.diagnoses_dir.exists() else []

    # Filter out index, log, dashboard
    pages = [p for p in pages if p.name not in ("index.md", "log.md", "dashboard.md")]

    if show_progress:
        print(f"📊 Found {len(pages)} pages to embed...")

    success = 0
    failed = 0

    for page in pages:
        try:
            if ingest_page(page, config, embedding_client):
                success += 1
            else:
                failed += 1
        except Exception as e:
            if show_progress:
                print(f"  ❌ {page.name}: {e}")
            failed += 1

    stats = store.get_stats()
    if show_progress:
        print(f"\n✅ Embedding complete: {success} success, {failed} failed")
        print(f"   Total vectors in store: {stats['total']}")
        for ptype, count in stats.get("by_type", {}).items():
            print(f"   {ptype}: {count}")

    return {"success": success, "failed": failed, "stats": stats}


def reindex(config: WikiConfig, embedding_client: EmbeddingClient,
            show_progress: bool = True) -> Dict:
    """Full reindex: clear all vectors and regenerate."""
    store = VectorStore(config)
    # Clear existing vectors
    import sqlite3
    conn = sqlite3.connect(str(config.vector_db_path))
    conn.execute("DELETE FROM vectors")
    conn.commit()
    conn.close()

    if show_progress:
        print("🔄 Vector store cleared, reindexing all pages...")

    return ingest_all(config, embedding_client, show_progress)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Wiki vector embedding generator")
    parser.add_argument("--reindex", action="store_true", help="Full reindex: clear and regenerate all vectors")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    config = WikiConfig()
    embedding_client = EmbeddingClient(config)

    if args.reindex:
        result = reindex(config, embedding_client, show_progress=not args.quiet)
    else:
        result = ingest_all(config, embedding_client, show_progress=not args.quiet)

    sys.exit(0 if result["failed"] == 0 else 1)
