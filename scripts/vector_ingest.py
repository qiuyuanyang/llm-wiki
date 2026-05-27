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


def ingest_file(config: WikiConfig, file_path: Path,
                embedding_client: EmbeddingClient = None) -> bool:
    """Ingest a raw source file from raw/sources/ into wiki + vector store.

    Reads the raw file, optionally adds frontmatter, copies to wiki/sources/,
    then generates embedding and stores the vector.
    """
    content = file_path.read_text(encoding="utf-8")
    if not content.strip():
        return False

    # Determine destination in wiki/sources/
    dest_name = file_path.name
    if not dest_name.endswith('.md'):
        dest_name = file_path.stem.replace(' ', '-').replace('_', '-').lower() + '.md'
    dest = config.wiki_dir / 'sources' / dest_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if already has frontmatter
    if not content.startswith('---'):
        # Add minimal frontmatter
        title = file_path.stem.replace('-', ' ').replace('_', ' ').title()
        from datetime import datetime
        fm = f"---\ntitle: {title}\ntype: source\nupdated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nsource: {file_path.name}\n---\n\n"
        content = fm + content

    # Copy to wiki/sources
    dest.write_text(content, encoding='utf-8')

    # Generate embedding and store
    if embedding_client is None:
        embedding_client = EmbeddingClient(config)

    store = VectorStore(config)
    text_content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    if not text_content:
        return False

    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
    page_path = str(dest.relative_to(config.root))
    page_type = 'source'
    title = _title_from_path(dest)

    vector = embedding_client.embed_single(text_content)
    store.upsert_vector(page_path, page_type, title, content_hash, vector)
    return True


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


def _collect_all_page_paths(config: WikiConfig) -> set:
    """Collect all valid wiki page paths (relative to config.root)."""
    pages = list(config.wiki_dir.rglob("*.md"))
    pages += list(config.diagnoses_dir.glob("*.md")) if config.diagnoses_dir.exists() else []
    pages = [p for p in pages if p.name not in ("index.md", "log.md", "dashboard.md")]
    return {str(p.relative_to(config.root)) for p in pages}


def _clean_orphan_vectors(config: WikiConfig, show_progress: bool = True) -> List[str]:
    """Remove vector entries whose wiki files no longer exist on disk.
    Returns list of removed page_paths."""
    import sqlite3
    disk_paths = _collect_all_page_paths(config)
    conn = sqlite3.connect(str(config.vector_db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, page_path FROM vectors").fetchall()
    orphaned = []
    for row in rows:
        if row["page_path"] not in disk_paths:
            conn.execute("DELETE FROM vectors WHERE id = ?", (row["id"],))
            orphaned.append(row["page_path"])
    conn.commit()
    conn.close()
    if show_progress and orphaned:
        print(f"  🗑️  清理了 {len(orphaned)} 个孤儿向量条目:")
        for p in orphaned:
            print(f"      - {p}")
    return orphaned


def ingest_all(config: WikiConfig, embedding_client: EmbeddingClient,
               show_progress: bool = True) -> Dict:
    """Generate embeddings for all wiki pages, then clean up orphaned vectors."""
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


def schedule_orphan_cleanup(config: WikiConfig, embedding_client: EmbeddingClient,
                            show_progress: bool = True) -> None:
    """Async orphan cleanup in a background thread — does not block the caller."""
    import threading

    def _worker():
        if show_progress:
            print("\n🧹 [后台] 开始扫描孤儿向量条目...")
        orphaned = _clean_orphan_vectors(config, show_progress)
        if show_progress:
            if orphaned:
                print(f"🧹 [后台] 清理了 {len(orphaned)} 个孤儿条目")
            else:
                print("🧹 [后台] 向量库干净，无需清理")

    t = threading.Thread(target=_worker, daemon=True, name="orphan-cleanup")
    t.start()


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
