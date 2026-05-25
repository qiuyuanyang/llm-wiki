#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
vector_store.py — SQLite-based vector storage for wiki pages.

Uses SQLite with a simple vector column (stored as JSON blob).
Supports cosine similarity search via raw SQL.

No external vector database required — everything lives in a single
SQLite file alongside the wiki.
"""

import json
import math
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import WikiConfig


class VectorStore:
    """SQLite-backed vector store with cosine similarity search."""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.db_path = config.vector_db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_path TEXT NOT NULL UNIQUE,
                page_type TEXT NOT NULL,
                title TEXT,
                content_hash TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vectors_page_path
            ON vectors(page_path)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vectors_page_type
            ON vectors(page_type)
        """)
        conn.commit()
        conn.close()

    def upsert_vector(self, page_path: str, page_type: str, title: str,
                      content_hash: str, vector: List[float]):
        """Insert or update a page's vector embedding."""
        conn = self._get_conn()
        now = datetime.now().isoformat()
        vector_json = json.dumps(vector)

        existing = conn.execute(
            "SELECT id FROM vectors WHERE page_path = ?", (page_path,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE vectors
                SET vector_json = ?, content_hash = ?, title = ?,
                    page_type = ?, updated_at = ?
                WHERE page_path = ?
            """, (vector_json, content_hash, title, page_type, now, page_path))
        else:
            conn.execute("""
                INSERT INTO vectors (page_path, page_type, title, content_hash,
                                     vector_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (page_path, page_type, title, content_hash, vector_json, now, now))

        conn.commit()
        conn.close()

    def delete_vector(self, page_path: str) -> bool:
        """Remove a page's vector embedding. Returns True if a row was deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM vectors WHERE page_path = ?", (page_path,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def search(self, query_vector: List[float], top_k: int = 10,
               page_type: Optional[str] = None) -> List[Dict]:
        """Cosine similarity search. Returns ranked results with scores."""
        conn = self._get_conn()

        if page_type:
            rows = conn.execute(
                "SELECT page_path, page_type, title, vector_json FROM vectors WHERE page_type = ?",
                (page_type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT page_path, page_type, title, vector_json FROM vectors"
            ).fetchall()

        conn.close()

        scored = []
        for row in rows:
            stored = json.loads(row["vector_json"])
            score = self._cosine_similarity(query_vector, stored)
            scored.append({
                "page_path": row["page_path"],
                "page_type": row["page_type"],
                "title": row["title"],
                "score": score,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def search_all(self, query_vector: List[float], top_k: int = 10) -> List[Dict]:
        """Search across all page types."""
        return self.search(query_vector, top_k)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def count(self) -> int:
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
        conn.close()
        return count

    def get_stats(self) -> Dict:
        conn = self._get_conn()
        stats = {"total": 0, "by_type": {}}
        row = conn.execute("SELECT COUNT(*) as cnt FROM vectors").fetchone()
        stats["total"] = row["cnt"]

        rows = conn.execute(
            "SELECT page_type, COUNT(*) as cnt FROM vectors GROUP BY page_type"
        ).fetchall()
        for r in rows:
            stats["by_type"][r["page_type"]] = r["cnt"]

        conn.close()
        return stats
